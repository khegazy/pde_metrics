"""The evaluation loop.

I/O costs about 10 ms per frame and a cheap metric costs 0.1 ms, so the loop order is
forced: **read each frame once, build every variant, then fan out over metrics.**

Order of operations within a frame:

1. Read the frame at its native resolution.
2. Remap onto the analysis grid (IN-2), recomputing derived fields there rather than
   averaging them.
3. Measure the reference fluctuation RMS, which sets the scale for relative severities.
4. Apply every ladder severity level.
5. Evaluate every metric against every variant.

Remapping *before* degrading is deliberate. It keeps severity units meaningful: a one-cell
translation means one analysis-grid cell whatever the analysis resolution, rather than
silently becoming half a cell when the grid is halved. It also means derived fields are
recomputed exactly once per frame.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from dataclasses import field as dc_field
from typing import Any

import numpy as np
import pandas as pd

from metrics.registry import MetricSpec

from .calibration import Calibration, calibrate
from .context import COMPANION_KEY, FieldContext, derive_rng, fluctuation_rms
from .data.base import Frame, TimeSelection, Trajectory
from .ladder import SeverityLevel, SeverityLevelApplication, apply_severity_level
from .remap import DEFAULT_METHOD, RemapMethod, coarsen_factor, remap_frame

log = logging.getLogger(__name__)

#: Column order and dtype of the tidy result frame. Frozen: everything downstream --
#: every plot, table and analysis -- is a groupby on this one schema.
RESULT_DTYPES: dict[str, str] = {
    # provenance
    "dataset": "category",
    "dataset_family": "category",
    "complexity_rank": "Int16",
    "param_reynolds": "float64",
    "param_mach": "float64",
    "param_resolution": "Int32",
    "trajectory": "category",
    # position in the trajectory
    "frame_index": "int32",
    "time": "float64",
    # what was measured, on what
    "field": "category",
    "analysis_grid": "int32",
    "remap_op": "category",
    "metric": "category",
    "arity": "category",
    "higher_is_better": "bool",      # the declaration, as provenance; the analysis measures
                                     # its direction instead (analysis.response_direction)
    # how the field was damaged
    "degradation": "category",       # the ladder-entry label: the unit of rank correlation
    "degradation_op": "category",    # the registry name behind it
    "degradation_family": "category",
    "level": "int16",
    "severity": "float64",           # the absolute value actually applied
    "severity_nominal": "float64",   # as written in config; differs for a calibrated operator
    "calibration": "category",
    "severity_degenerate": "bool",   # not a distinct experiment: repeats a milder
                                     # severity level, or resolved to a severity at
                                     # which the operator is a no-op
    "energy_removed": "float64",     # what the severity level MEASURABLY did, as
                                     # opposed to what it asked
    "energy_changed": "float64",     # for: both are fractions of the reference fluctuation
    "severity_name": "category",
    "variant_label": "category",
    # the number
    "value": "float64",
    "seed": "int64",
    "wall_time_s": "float64",
    # probabilistic evaluation; null on rows a deterministic metric produced
    "n_members": "Int16",            # ensemble size actually read, since spread and CRPS
                                     # both depend on it and a run may vary it
    "target_value": "float64",       # the value a calibrated prediction attains, when that
                                     # is not zero: 1 for the spread-to-skill ratio
}


@dataclass(frozen=True)
class DatasetInfo:
    """Provenance and complexity metadata for one dataset, copied onto every row.

    ``family`` and ``rank`` are the warm start for comparing metrics across datasets of
    increasing physical complexity: without a declared ordering there is no axis to plot
    against, and back-filling it later across a dozen configs is tedious.
    """

    name: str
    trajectory: str = ""
    family: str = ""
    rank: int | None = None
    params: Mapping[str, float] = dc_field(default_factory=dict)

    def row(self) -> dict[str, Any]:
        return {
            "dataset": self.name,
            "dataset_family": self.family,
            "complexity_rank": self.rank,
            "param_reynolds": self.params.get("reynolds", np.nan),
            "param_mach": self.params.get("mach", np.nan),
            "param_resolution": self.params.get("resolution"),
            "trajectory": self.trajectory,
        }


@dataclass
class MapRequest:
    """Which pointwise metric maps to keep; also the schema of ``report.error_map``.

    Storing a map for every frame and variant would be gigabytes, so only the named
    combinations are retained -- enough for the figure, not for the whole run. The defaults
    here keep nothing, for callers that do not ask.
    """

    enabled: bool = False
    frames: list[int] = dc_field(default_factory=list)
    """Positions within the *selected* frames; -1 is the last one."""
    axes: list[str] = dc_field(default_factory=list)
    """Ladder-entry labels to keep. Empty means all of them."""
    fields: list[str] = dc_field(default_factory=list)
    """Fields to keep. Empty means all of them."""


@dataclass
class PipelineResult:
    """Everything one evaluation produced."""

    rows: pd.DataFrame
    maps: dict[str, np.ndarray] = dc_field(default_factory=dict)
    """``"<metric>:<field>__<variant>__t<frame>"`` -> pointwise density, for ``error_maps.npz``."""
    companions: pd.DataFrame = dc_field(default_factory=pd.DataFrame)
    """One row per curve coordinate of every result row whose metric has a curve companion: the
    result row's columns, its ``value`` replaced by the curve's, plus ``coordinate``. Empty when no
    metric has one. Written to ``companions.csv``."""
    n_frames: int = 0
    analysis_grid: int = 0
    """Extent of the analysis grid along its first axis, as written to every row."""
    calibration: Calibration | None = None
    io_seconds: float = 0.0
    degrade_seconds: float = 0.0
    metric_seconds: float = 0.0


def _emit(
    spec: MetricSpec,
    field: str,
    frame: Frame,
    severity_level: SeverityLevel,
    applied: SeverityLevelApplication,
    run_columns: dict[str, Any],
    value: Any,
    wall: float,
    n_members: int | None = None,
) -> dict[str, Any]:
    """The result row of one metric evaluation: one number per (frame, field, metric, variant).

    ``run_columns`` are the columns every row of the run shares; column order is fixed later by
    :data:`RESULT_DTYPES`, not here.
    """
    return {
        **run_columns,
        "frame_index": frame.index,
        "time": frame.time,
        "field": field,
        "metric": spec.name,
        "arity": spec.arity,
        "higher_is_better": spec.higher_is_better,
        "degradation": severity_level.label,
        "degradation_op": severity_level.op,
        "degradation_family": severity_level.family,
        "level": severity_level.level,
        "severity": applied.resolved.get(field, severity_level.severity),
        "severity_nominal": severity_level.severity,
        "calibration": severity_level.calibration or "",
        # An operation that did nothing to this field is not an experiment; the reference
        # level does nothing by definition and is not flagged.
        "severity_degenerate": field in applied.unchanged and not severity_level.is_reference,
        "energy_removed": applied.energy_removed.get(field, float("nan")),
        "energy_changed": applied.energy_changed.get(field, float("nan")),
        "severity_name": severity_level.severity_name,
        "variant_label": severity_level.variant_label,
        "wall_time_s": wall,
        "n_members": n_members,
        "target_value": spec.target if spec.target is not None else np.nan,
        "value": float(value),
    }


def map_key(metric: str, field: str, variant: str, frame_index: int) -> str:
    """The ``error_maps.npz`` key of one stored pointwise map. :func:`parse_map_key` inverts it."""
    return f"{metric}:{field}__{variant}__t{frame_index}"


def parse_map_key(key: str) -> tuple[str, str, str, int]:
    """``(metric, field, variant, frame_index)`` of an ``error_maps.npz`` key.

    Parsed from both ends, because a ladder label -- and so a variant -- may itself contain
    ``__``, while metric and canonical field names never contain ``:`` or ``__``.
    """
    metric, rest = key.split(":", 1)
    rest, frame = rest.rsplit("__t", 1)
    field, variant = rest.split("__", 1)
    return metric, field, variant, int(frame)


def run(
    trajectory: Trajectory,
    metrics: Sequence[MetricSpec],
    severity_levels: Sequence[SeverityLevel],
    *,
    fields: Sequence[str],
    selection: TimeSelection | None = None,
    dataset: DatasetInfo,
    seed: int = 0,
    analysis_resolution: int | None = None,
    remap_method: RemapMethod = DEFAULT_METHOD,
    maps: MapRequest | None = None,
    calibration_frames: int = 5,
) -> PipelineResult:
    """Evaluate every metric against every severity level, over the selected frames.

    Args:
        trajectory: Source of frames.
        metrics: Metric specs to evaluate.
        severity_levels: The degradation ladder, including its reference severity level.
        fields: Canonical field names to read. Metrics that do not accept a field skip it.
        selection: Which frames to evaluate. Defaults to all of them.
        dataset: Provenance copied onto every row.
        seed: Run seed; per-severity level generators derive from it deterministically.
        analysis_resolution: IN-2 analysis grid, or None for the native resolution.
        remap_method: ``"block_mean"`` (conservative) or ``"subsample"``.
        maps: Which pointwise maps to retain.
        calibration_frames: How many frames to average the per-field spectral calibration
            over. Measured once and held fixed for the whole run; see :mod:`fmeval.calibration`.

    Returns:
        A :class:`PipelineResult` whose ``rows`` follow :data:`RESULT_DTYPES` exactly.
    """
    selection = selection or TimeSelection()
    maps = maps or MapRequest()
    indices = selection.resolve(len(trajectory))
    if len(indices) == 0:
        raise ValueError("time selection is empty; check dataset.time.start / stop")

    if not trajectory.grid.is_periodic:
        # A metric built on a Fourier transform or a wrap-around difference would read the
        # domain edge as a jump. Not run, rather than run on an extended field: what such a
        # metric means on a bounded domain is a different definition, not a boundary detail.
        # Skipped without rows, as an ensemble metric is on a deterministic dataset.
        periodic_only = [m.name for m in metrics if m.requires_periodic]
        metrics = [m for m in metrics if not m.requires_periodic]
        if not metrics:
            raise ValueError(
                f"every selected metric ({', '.join(periodic_only)}) needs a periodic domain, "
                f"and dataset {dataset.name!r} has boundaries {trajectory.grid.boundary}"
            )
        if periodic_only:
            log.warning("%s need a periodic domain and dataset %r has boundaries %s; no rows "
                        "were produced for them", ", ".join(periodic_only), dataset.name,
                        trajectory.grid.boundary)

    factor = coarsen_factor(trajectory.grid, analysis_resolution)
    grid_size = trajectory.grid.shape[0] // factor
    keep_frames = _map_frames(maps, indices)

    expensive = [m.name for m in metrics if m.cost == "expensive"]
    if expensive and len(indices) > 500:
        log.warning(
            "%d frames x expensive metric(s) %s: consider raising dataset.time.reduction",
            len(indices), expensive,
        )

    calibration = _measure_calibration(
        trajectory, fields, indices, factor, remap_method, calibration_frames
    )

    # A per_unit_time level is a rate times the time since the trajectory's first frame.
    time_origin = float(trajectory.times[0])
    probe = remap_frame(trajectory.frame(int(indices[0]), fields), factor,
                        method=remap_method)
    severity_levels = _runnable_levels(
        severity_levels, probe, fields, seed=seed, calibration=calibration,
        analysis_grid=grid_size, times=trajectory.times[indices], time_origin=time_origin,
    )

    run_columns = {**dataset.row(), "analysis_grid": grid_size, "remap_op": remap_method,
                   "seed": seed}
    rows: list[dict[str, Any]] = []
    curve_rows: list[dict[str, Any]] = []
    stored_maps: dict[str, np.ndarray] = {}
    skipped_ensemble: set[str] = set()
    t_io = t_deg = t_metric = 0.0

    for index in indices:
        t_read = time.perf_counter()
        frame = trajectory.frame(int(index), fields)
        t_io += time.perf_counter() - t_read

        t0 = time.perf_counter()
        frame = remap_frame(frame, factor, method=remap_method)
        available = [f for f in fields if f in frame.fields]
        ref_rms = {name: fluctuation_rms(frame.fields[name]) for name in available}
        variants = {
            severity_level.variant_label: (
                severity_level,
                apply_severity_level(
                    severity_level, frame, available, seed=seed,
                    reference_rms=ref_rms, calibration=calibration, time_origin=time_origin,
                ),
            )
            for severity_level in severity_levels
        }
        t_deg += time.perf_counter() - t0

        for spec in metrics:
            if spec.arity == "ensemble" and not frame.has_members:
                # Nothing to measure. Skipped rather than recorded, because a column of
                # zeros or NaNs is indistinguishable from a metric that ran and found
                # nothing wrong. Reported once per run, below.
                skipped_ensemble.add(spec.name)
                continue
            for field in (f for f in available if spec.accepts(f)):
                reference = frame.fields[field]
                ctx = FieldContext(
                    field=field,
                    grid=frame.grid,
                    frame_index=frame.index,
                    time=frame.time,
                    fluctuation_rms=ref_rms[field],
                    rng=derive_rng(seed, "metric", frame.index, field),
                )
                kwargs = {"ctx": ctx} if spec.takes_ctx else {}
                companion = spec.companion
                # The companion draws from its own generator, so adding one to a metric that
                # draws random numbers cannot move the metric's number. The cache is shared.
                companion_kwargs = ({"ctx": replace(ctx, rng=derive_rng(
                    seed, f"companion/{spec.name}", frame.index, field))}
                    if companion is not None and companion.takes_ctx else {})
                curve = companion is not None and companion.kind == "curve"

                for label, (severity_level, applied) in variants.items():
                    candidate = applied.fields[field]
                    n_members = None
                    if spec.arity == "ensemble":
                        members = (applied.members or frame.members)[field]
                        n_members = int(members.shape[0])
                        args = (reference, members)
                    elif spec.arity == "pairwise":
                        args = (reference, candidate)
                    else:
                        args = (candidate,)
                    t1 = time.perf_counter()
                    if curve:
                        # First, so the metric reads the curve rather than computing it again;
                        # both calls are timed, so the row's cost is the whole evaluation.
                        coordinates, curve_values = companion.fn(
                            *((candidate,) if companion.one_field else args), **companion_kwargs)
                        ctx.cache[COMPANION_KEY] = (coordinates, curve_values)
                    value = spec.fn(*args, **kwargs)
                    wall = time.perf_counter() - t1
                    t_metric += wall
                    row = _emit(spec, field, frame, severity_level, applied, run_columns,
                                value, wall, n_members=n_members)
                    rows.append(row)
                    if curve:
                        curve_rows += [{**row, "coordinate": c, "value": float(v),
                                        "_row": len(rows) - 1}
                                       for c, v in zip(coordinates, curve_values, strict=True)]

                    if (
                        companion is not None and companion.kind == "field"
                        and frame.index in keep_frames
                        and (not maps.axes or severity_level.label in maps.axes)
                        and (not maps.fields or field in maps.fields)
                    ):
                        m = companion.fn(*args, **companion_kwargs)
                        stored_maps[map_key(spec.name, field, label, frame.index)] = (
                            np.asarray(m, dtype=np.float64)
                        )

    if skipped_ensemble:
        log.info(
            "%s need an ensemble and dataset %r provides one realization per frame; "
            "no rows were produced for them",
            ", ".join(sorted(skipped_ensemble)), dataset.name,
        )

    # A metric may accept none of the available fields, which is a legitimate no-op
    # rather than an error -- but pd.DataFrame([]) has no columns to coerce.
    df = _coerce(pd.DataFrame(rows)) if rows else empty_results()
    df = _flag_repeated_levels(df, {level.label for level in severity_levels if level.ordinal})
    companions = pd.DataFrame()
    if curve_rows:
        companions = pd.DataFrame(curve_rows)
        # A repeated level is a property of the experiment, flagged on the result rows above.
        companions["severity_degenerate"] = (
            df["severity_degenerate"].to_numpy()[companions.pop("_row").to_numpy()])
        companions = companions[[*RESULT_DTYPES, "coordinate"]].astype(RESULT_DTYPES)
    return PipelineResult(
        rows=df,
        maps=stored_maps,
        companions=companions,
        n_frames=len(indices),
        analysis_grid=grid_size,
        calibration=calibration,
        io_seconds=t_io,
        degrade_seconds=t_deg,
        metric_seconds=t_metric,
    )


def _flag_repeated_levels(df: pd.DataFrame, ordinal: set[str]) -> pd.DataFrame:
    """Mark severity levels that repeat a milder one as the same experiment, and log them.

    Detected by measurement rather than by declaration: two severity levels whose
    severities resolve to the same quantised operation produce a bitwise identical field,
    hence an exactly equal ``energy_changed``. That is a stronger test than
    asking each operator to describe how it rounds, and it needs no such description -- it
    catches a sharp filter landing twice on the same set of modes, and a windowed kernel landing
    twice on the same odd width, alike. It is applied frame by frame: a ``per_unit_time`` entry's
    levels are distinct experiments at most times and can coincide at one (whole-cell shifts of
    1.0 and 1.4 cells per unit time, both one cell at t = 1), and only that frame's tie is the
    same experiment twice. Only the ``ordinal`` ladder labels are checked: the draws of a probe or
    an anchor are samples, not strengths, and two random draws that happen to coincide in one
    frame are not an ordering to protect.

    Such a severity level is not padding, it is corruption: the rank correlation would
    score the tie as agreement and the adjacent-severity level separability would compare
    a distribution against itself. It is also not a misconfiguration: a field whose energy sits
    in a few wavenumber shells offers only a few distinct cutoffs, however the ladder is written
    (:meth:`fmeval.calibration.Calibration.spectrum_frame` shows the curve).

    Severity levels already marked degenerate because the operator left the field unchanged to
    within round-off (:func:`fmeval.ladder.apply_severity_level`) are logged here too, before the
    merge, so the two reasons stay distinguishable in the log.
    """
    if df.empty:
        return df

    # One row per (field, degradation, frame, level): the experiment, whichever metric scored it.
    keys = ["field", "degradation", "frame_index"]
    ladder = df[(df["level"] > 0) & df["degradation"].isin(ordinal)]
    effects = ladder.drop_duplicates([*keys, "level"])
    # The mildest level with the same energy change in the same frame; NaN never repeats.
    first = effects.groupby([*keys, "energy_changed"], observed=True)["level"].transform("min")
    repeats = effects[effects["level"] > first].assign(first=first)
    repeated = pd.Series(pd.MultiIndex.from_frame(ladder[[*keys, "level"]]).isin(
        pd.MultiIndex.from_frame(repeats[[*keys, "level"]])), index=ladder.index
    ).reindex(df.index, fill_value=False)
    for (field, axis), g in repeats.groupby(["field", "degradation"], observed=True):
        pairs = g.groupby(["level", "first"], observed=True)["frame_index"].nunique()
        log.warning(
            "%s / %s: level(s) %s repeat the experiment of level(s) %s in %s of %d frame(s) "
            "and are excluded there from the acceptance statistics. The field's spectrum cannot "
            "resolve that many distinct severity levels for this operator.",
            field, axis, [int(a) for a, _ in pairs.index], [int(b) for _, b in pairs.index],
            pairs.tolist(), ladder.loc[ladder["field"].eq(field)
                                       & ladder["degradation"].eq(axis), "frame_index"].nunique(),
        )

    flagged = df[(df["level"] > 0) & df["severity_degenerate"]]
    for (field, axis), g in flagged.groupby(["field", "degradation"], observed=True):
        log.warning(
            "%s / %s: level(s) %s resolve to a severity at which the operator leaves the "
            "field unchanged, and are excluded from the acceptance statistics.",
            field, axis, sorted(int(level) for level in g["level"].unique()),
        )
    df = df.copy()
    df["severity_degenerate"] = df["severity_degenerate"] | repeated
    return df


def _map_frames(maps: MapRequest, indices: np.ndarray) -> set[int]:
    """Resolve ``report.error_map.frames`` positions to trajectory frame indices.

    The positions are *within the selected frames*, so what is valid depends on
    ``dataset.time.reduction``, ``start``/``stop`` and the trajectory length, and raising the
    reduction can shrink the selection under a configured position. Negative positions count
    from the end, as elsewhere in numpy, and ``-1`` is the shipped default.

    Raises:
        ValueError: If a position is outside the selection, naming both the setting and the
            selection bounds rather than an index.
    """
    if not (maps.enabled and maps.frames):
        return set()
    n = len(indices)
    out = set()
    for position in maps.frames:
        if not -n <= position < n:
            raise ValueError(
                f"report.error_map.frames contains {position}, which is outside the "
                f"{n} selected frame(s). The positions are counted within the selection, so "
                "they are bounded by dataset.time.reduction, start/stop and max_frames; "
                f"valid values here are {-n} to {n - 1}."
            )
        out.add(int(indices[position]))
    return out


_OPERATOR_DEFECTS = (NameError, AttributeError, ImportError, TypeError)
"""Exception types that mean the operator is broken rather than unsupported here.

:func:`_runnable_levels` drops a severity level it cannot apply, which is right when the
analysis grid is too small for the severity asked of it -- that is one missing experiment,
not a reason to discard the others. It is wrong when the operator itself is defective:
the run would then complete with fewer rows and a warning blaming the analysis grid, and
nothing would make a reader suspect an axis is missing rather than merely quiet.

So a NameError, AttributeError, ImportError or TypeError -- a defect in the code -- stops
the run. Anything else is treated as a limit of this grid and drops the level with a
warning.
"""


def _runnable_levels(
    severity_levels: Sequence[SeverityLevel],
    probe: Frame,
    fields: Sequence[str],
    *,
    seed: int,
    calibration: Calibration,
    analysis_grid: int,
    times: Sequence[float] = (),
    time_origin: float = 0.0,
) -> list[SeverityLevel]:
    """Drop severity levels that cannot run on the analysis grid, before the frame loop starts.

    ``analysis_grid.resolution`` is one of the two documented size knobs, and turning it down
    far enough puts the configured ladder outside what the grid can support: the shipped ladder
    coarsens by up to 16, which cannot run at resolution 8. Checking before the loop names the
    knob, and does so before any frame's I/O has been paid.

    The check is a trial application on one already-remapped frame, so it needs no per-operator
    declaration of what it can support and stays correct as operators are added. Severity
    levels that fail are dropped with a warning naming the knob, and the run proceeds on
    the rest: an unsupported
    severity level is one missing experiment, not a reason to discard the others.

    A ``per_unit_time`` level applies a different strength in every frame, its rate times the
    frame's time since ``time_origin``, so it is tried at each of the selected frames' ``times``:
    a coarsening factor that does not divide the grid at one of them would otherwise stop the run
    inside the frame loop.

    Raises:
        ValueError: If no severity level survives, since there is then nothing to measure.
    """
    keep: list[SeverityLevel] = []
    dropped: list[str] = []
    for severity_level in severity_levels:
        trials = ([replace(probe, time=float(t)) for t in times]
                  if severity_level.per_unit_time and len(times) else [probe])
        try:
            for trial in trials:
                apply_severity_level(severity_level, trial, fields, seed=seed,
                                     calibration=calibration, time_origin=time_origin)
        except _OPERATOR_DEFECTS as exc:
            raise RuntimeError(
                f"the {severity_level.label!r} operator is broken: {type(exc).__name__}: {exc}.\n"
                "This is a defect in the operator rather than a severity the analysis grid "
                "cannot support, so the run stops here rather than quietly measuring one "
                "axis fewer. Fix the operator, or remove it from the ladder with "
                f"degradation.skip=[{severity_level.label}] if that is deliberate."
            ) from exc
        except Exception as exc:  # noqa: BLE001 - the severity itself cannot run here
            log.warning(
                "dropping %s level %d (%s = %g): it cannot run on the %d-cell analysis grid "
                "(%s). Raise analysis_grid.resolution or lower this severity.",
                severity_level.label, severity_level.level,
                severity_level.severity_name, severity_level.severity,
                analysis_grid, exc,
            )
            dropped.append(f"{severity_level.label} level {severity_level.level}")
            continue
        keep.append(severity_level)

    # One line naming the total, because a per-level warning scrolls past in a long run and
    # a reader comparing two runs needs to see that they measured different ladders.
    if dropped:
        log.warning(
            "%d of %d severity levels were dropped and will not appear in the results: %s",
            len(dropped), len(severity_levels), ", ".join(dropped),
        )

    if not keep:
        raise ValueError(
            f"no ladder severity_level can run on the {analysis_grid}-cell analysis grid; every "
            "configured severity was rejected. Raise analysis_grid.resolution."
        )
    return keep


def _measure_calibration(
    trajectory: Trajectory,
    fields: Sequence[str],
    indices: np.ndarray,
    factor: int,
    remap_method: str,
    n_sample: int,
) -> Calibration:
    """Measure each field's spectral properties on the analysis grid, once.

    Sampled evenly across the selected frames rather than from the start, so a trajectory
    whose spectrum evolves is represented rather than characterised by its beginning.
    """
    if n_sample < 1:
        return Calibration()
    chosen = indices[np.unique(np.linspace(0, len(indices) - 1, n_sample).astype(int))]

    frames_by_field: dict[str, list[np.ndarray]] = {f: [] for f in fields}
    for index in chosen:
        frame = remap_frame(trajectory.frame(int(index), fields), factor,
                            method=remap_method)
        for name, array in frame.fields.items():
            frames_by_field[name].append(array)

    result = calibrate(frames_by_field, frame.grid, fields)
    for entry in result.summary():
        log.info(
            "calibration %s: scale %.1f cells (spread %.0f%%), k(50/90/99%%) = %d/%d/%d",
            entry["field"], entry["characteristic_scale"], 100 * entry["scale_spread"],
            entry["k_energy_50"], entry["k_energy_90"], entry["k_energy_99"],
        )
    return result


def _coerce(df: pd.DataFrame) -> pd.DataFrame:
    """Put the frame into the frozen schema: exact columns, exact order, exact dtypes."""
    missing = set(RESULT_DTYPES) - set(df.columns)
    if missing:
        raise ValueError(f"result frame is missing columns: {sorted(missing)}")
    extra = set(df.columns) - set(RESULT_DTYPES)
    if extra:
        raise ValueError(f"result frame has unexpected columns: {sorted(extra)}")
    return df[list(RESULT_DTYPES)].astype(RESULT_DTYPES)


def empty_results() -> pd.DataFrame:
    """An empty frame with the correct schema, for tests and for degenerate runs."""
    return pd.DataFrame({c: pd.Series(dtype=d) for c, d in RESULT_DTYPES.items()})
