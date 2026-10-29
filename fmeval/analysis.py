"""Turn the tidy result frame into the reported criteria.

This module computes numbers only. The separate :func:`flag` pass compares them against
configured reference thresholds, so the two can never be confused and re-flagging with
different thresholds needs no recomputation. **Nothing here labels a metric accepted or
rejected** -- the flags exist to draw attention to a row, and the panel decision is the
team's.

Two rules that keep the numbers honest:

**Rank correlation is computed within one ladder axis, never across.** ``gaussian_blur
sigma=2`` and ``translate_x=4`` have no order relative to each other, and neither do
``gaussian_blur`` and ``median_blur`` even though both belong to the ``smoothing``
family. The unit is the ladder entry. Where one number per metric is wanted, the minimum
across axes is reported -- the honest worst case.

**The IN-4 field is excluded from every rank correlation**, by its ``ordinal=False``
declaration. It is a separate probe, not a severity level.
"""

from __future__ import annotations

import logging
import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field as dc_field
from itertools import pairwise

import numpy as np
import pandas as pd
from scipy.stats import false_discovery_control, mannwhitneyu, spearmanr

from . import stats
from .context import derive_rng

log = logging.getLogger(__name__)

#: Label of the default anchor, the field's spatial mean (the climatological reference
#: forecast, judgements/001). Its median value defines D = 1 unless a run sets another
#: ``analysis.anchor``.
MEAN_FIELD_LABEL: str = "mean_field"

#: Label of the large-random-translation probe: the right statistics in the wrong place. It was
#: the anchor of every run recorded before ``anchor_label`` existed, so :func:`run_labels`
#: falls back to it for those.
UNCORRELATED_LABEL: str = "uncorrelated"

#: Ladder labels that are probes or reference measurements, not monotone axes.
PROBE_LABELS: frozenset[str] = frozenset({"gaussian_impostor", MEAN_FIELD_LABEL,
                                          UNCORRELATED_LABEL})

#: The unit every per-metric statistic is computed over. A list, not a tuple: pandas reads a
#: tuple passed to ``groupby`` as one key.
GROUP_KEYS: list[str] = ["dataset", "metric", "field"]

#: What identifies one result row: one metric evaluation of one variant of one frame. Every
#: statistic reads a row as one point on one trace, and pairs a frame's levels with that frame's
#: clean value by ``frame_index`` within a :data:`GROUP_KEYS` group, so a second row under the
#: same key -- another trajectory's frame of the same index included -- would be merged into it
#: silently; :func:`normalisation` refuses that.
ROW_KEYS: list[str] = [*GROUP_KEYS, "frame_index", "variant_label"]

#: The ladder entry the profile's displacement elasticity is read from: a sub-pixel shift, the
#: smallest displacement the ladder applies and the regime of the double penalty.
DISPLACEMENT_AXIS: str = "translate_subpixel"

#: Moving-block bootstrap of the rank-correlation interval: resamples, and block length in
#: frames. The metric trace is autocorrelated in time, so an independent bootstrap would give
#: absurdly tight intervals.
N_BOOTSTRAP: int = 200
BLOCK_LENGTH: int = 10

#: The per-(metric, field) profile columns :func:`report_card` adds, in display order.
PROFILE_COLUMNS: tuple[str, ...] = ("selectivity", "most_sensitive_axis", "least_sensitive_axis",
                                    "blind_axes", "elasticity_displacement")

#: Fraction of the clean-to-anchor span at which a metric counts as having
#: departed from clean. Fixed once here and never tuned per metric.
SENSITIVITY_FRACTION: float = 0.10

#: Fraction of the clean-to-anchor span at which a metric counts as saturated.
SATURATION_FRACTION: float = 0.90

#: Fraction of the clean-to-anchor span at which the half-damage severity is read. Fixed
#: once here, like the two fractions above.
HALF_DAMAGE_FRACTION: float = 0.5

#: How many of an axis's mildest usable levels the elasticity is fitted over. The slope over a
#: whole ladder that saturates understates the small-damage exponent: on the pinned run
#: comparison_1790639359, MSE on vorticity under translate_subpixel has a slope of 1.76 over all
#: six levels and 1.99 over the first three, and the second is the double-penalty exponent.
ELASTICITY_LEVELS: int = 3

#: The negligibility margin on the damage scale. A degradation on which the metric's largest
#: damage is provably below it is listed as one the metric does not respond to. Half the
#: detection fraction, so "detected" and "blind" can never both hold. A repository convention,
#: fixed once and never per metric; the analogue followed is the smallest effect size of interest
#: of equivalence testing (Lakens 2017, Soc. Psychol. Personal. Sci. 8(4):355-362).
BLINDNESS_MARGIN: float = SENSITIVITY_FRACTION / 2

#: Confidence of the upper bound on the largest damage (the bootstrap quantile it is read at).
BLINDNESS_CONFIDENCE: float = 0.90

#: False-discovery level below which an axis is listed as one the metric does not respond to.
FDR_LEVEL: float = 0.10

#: Per-axis columns added by :func:`_response_statistics`, in output order.
RESPONSE_COLUMNS: tuple[str, ...] = (
    "cliffs_delta_min", "elasticity", "elasticity_x", "response_shape",
    "severity_10", "severity_50", "severity_resolution", "field_change_max",
    "damage_per_change", "blindness_block_length", "damage_max_ucb", "blindness_q",
)
_TEXT_COLUMNS = frozenset({"elasticity_x", "response_shape"})

#: Relative size below which a quantity counts as round-off rather than signal, measured
#: against the largest value in the same group.
#:
#: Two things use it. The damage score needs its clean-to-anchor span to be a real span, and a
#: metric invariant to the operator the anchor is built from has no span at all -- under an
#: anchor built by translation, that is most of the position-tolerant family this project
#: exists to develop. The rank correlation needs the values
#: it is ranking to differ by more than the last few bits, and ``np.roll`` changes the
#: summation order inside ``np.mean`` even when it cannot change the quantity
#: (:func:`_is_round_off`). Both are round-off presented as measurement.
#:
#: 1e-9 rather than something nearer the float64 epsilon: accumulated round-off over a 256^2
#: reduction is several orders of magnitude above 2.2e-16, while the mildest severity level that
#: does real work on this data moves the value by 1e-4 of its range. Nothing measured falls in the
#: gap between.
DEGENERATE_SPAN: float = 1e-9


# --- normalisation --------------------------------------------------------------------


def run_labels(meta: Mapping, config: Mapping | None = None) -> tuple[str, frozenset[str]]:
    """The anchor label and the probe labels a run declared, with the defaults for older runs.

    ``evaluate.py`` records both in ``run_meta.json``: the anchor is ``analysis.anchor`` from the
    configuration, the probes every ladder entry whose operator is declared ``ordinal=False``.
    A folder written before that falls back to the resolved configuration, then to
    :data:`UNCORRELATED_LABEL` (the anchor every such run used) and :data:`PROBE_LABELS`, so it
    keeps rendering as it did.
    """
    configured = ((config or {}).get("analysis") or {}).get("anchor")
    anchor = meta.get("anchor_label") or configured or UNCORRELATED_LABEL
    recorded = meta.get("probe_labels")
    return str(anchor), (frozenset(recorded) if recorded is not None else PROBE_LABELS)


def normalisation(df: pd.DataFrame, *, anchor_label: str = MEAN_FIELD_LABEL,
                  probe_labels: frozenset[str] = PROBE_LABELS) -> pd.DataFrame:
    """Anchors that put every metric on one dimensionless scale.

    Raw mean squared error and a raw transport distance are not comparable, so a *damage
    score* is defined per (dataset, metric, field):

        D = (v - clean) / (anchor - clean)

    ``clean`` is the median value on the reference severity level. ``anchor`` is the median value
    on the ladder entry ``anchor_label`` (``analysis.anchor``). By default that is ``mean_field``,
    the field's spatial mean: the climatological reference forecast against which skill scores
    are conventionally measured (Murphy 1988, Mon. Wea. Rev. 116(12), 2417-2424). D = 1 then
    means "as far from the truth as the field's own mean", which is what makes the score readable
    across metrics with different units. For the mean squared error the anchor is exactly the
    reference's spatial variance.

    A ratio to the clean value is not usable here: mean squared error on the reference severity
    level is exactly zero. Per-figure min-max scaling is not usable either, because the figure would
    change whenever a severity level is added.

    Returns:
        One row per (dataset, metric, field) with ``value_clean``, ``value_anchor``,
        ``span``, ``anchor_source`` and ``degenerate``.

    Raises:
        ValueError: If two rows share a :data:`ROW_KEYS` key, which no statistic here can read.
    """
    keys = [k for k in ROW_KEYS if k in df.columns]
    repeated = df.duplicated(keys, keep=False)
    if repeated.any():
        raise ValueError(
            f"{int(repeated.sum())} result rows share a key of {ROW_KEYS} with another row, "
            f"e.g. {df.loc[repeated, keys].head(2).to_dict('records')}. "
            "Every statistic reads one row as one point of one trace and pairs frames by "
            "frame_index within a dataset; concatenate runs under distinct dataset names, or "
            "analyse them separately."
        )
    rows = []
    for key, g in df.groupby(GROUP_KEYS, observed=True):
        clean = float(g.loc[g["level"] == 0, "value"].median())    # NaN with no reference rows
        high, source = _anchor(g, anchor_label, probe_labels)
        span = high - clean
        # The scale is the LARGEST value anywhere in the group, not the median. The median is
        # defeated in exactly the case this guard exists for: a metric invariant to the
        # operator the anchor is built from returns round-off on the anchor, on the impostor
        # and on every severity level of that operator, so more than half the rows can be
        # round-off and the median collapses to round-off with them -- the guard then compares
        # noise against noise and passes, and the impostor reads as "worse than the anchor"
        # for a metric that cannot separate any of them.
        scale = float(np.nanmax(np.abs(g["value"].to_numpy()))) or 1.0
        rows.append(
            {
                **dict(zip(GROUP_KEYS, key, strict=True)),
                "value_clean": clean,
                "value_anchor": high,
                "span": span,
                "anchor_source": source,
                "degenerate": not np.isfinite(span) or abs(span) < DEGENERATE_SPAN * scale,
            }
        )
    return pd.DataFrame(rows)


def _anchor(g: pd.DataFrame, preferred: str,
            probe_labels: frozenset[str] = PROBE_LABELS) -> tuple[float, str]:
    """The anchor value of one group and where it came from."""
    if preferred and (g["degradation"] == preferred).any():
        sub = g[g["degradation"] == preferred]
        return float(sub["value"].median()), preferred

    # A run without its anchor entry falls back to the largest configured translation. That is
    # a different reference, not an estimate of the anchor, so the source is recorded and the
    # report says so.
    for label in ("translate_x", "translate_subpixel", "translate_y"):
        sub = g[g["degradation"] == label]
        if not sub.empty:
            top = sub.loc[sub["level"] == sub["level"].max()]
            return float(top["value"].median()), f"{label}@max"

    # Otherwise fall back to the worst severity level of any ordinal axis, and say so.
    ordinal = g[~g["degradation"].isin(probe_labels)]
    if ordinal.empty:
        return float("nan"), "none"
    worst = ordinal.loc[ordinal["value"].abs().idxmax()]
    return float(worst["value"]), f"{worst['degradation']}@max"


def add_damage(df: pd.DataFrame, norm: pd.DataFrame) -> pd.DataFrame:
    """Attach the dimensionless damage score ``D`` to every row."""
    out = df.merge(norm[[*GROUP_KEYS, "value_clean", "span", "degenerate"]], on=GROUP_KEYS,
                   how="left")
    with np.errstate(invalid="ignore", divide="ignore"):
        out["damage"] = (out["value"] - out["value_clean"]) / out["span"]
    out.loc[out["degenerate"], "damage"] = np.nan
    return out.drop(columns=["value_clean", "span", "degenerate"])


def _oriented(values: pd.Series, sign: int, target: float | None) -> pd.Series:
    """``values`` on the scale every ordering statistic runs on, where larger is always worse.

    For an ordinary metric that is ``sign * values``, with ``sign`` from
    :func:`response_direction`. A metric calibrated at an interior ``target`` is not monotone in
    damage -- it is wrong above the target and equally wrong below it -- so it is ordered by how
    far each value sits from ``target``, on a scale where the ratio is symmetric.

    A ratio lives on a multiplicative scale: half the calibrated spread and twice it are
    equally wrong, and a difference from the target would call the second one four times
    worse than the first. The log ratio makes them equal, which is the whole reason the
    spread-to-skill literature reads this quantity multiplicatively.

    Zero and negative values are real and reachable -- an ensemble collapsed onto its
    mean has exactly no spread -- and a log cannot take them. They are the furthest thing
    from calibrated there is, so they map to positive infinity rather than to NaN: a NaN
    would drop the severity level from the rank correlation and quietly shrink the axis
    it is meant to be the worst point of.
    """
    if target is None:
        return sign * values
    v = values.to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.abs(np.log(v / target))
    return pd.Series(np.where(v > 0, out, np.inf), index=values.index)


def response_direction(df: pd.DataFrame) -> dict[tuple, int]:
    """Which way each metric moves under each degradation: ``+1`` away from clean upward, ``-1``.

    The only place a direction comes from. The ordering statistics read a degradation's trace as
    a *departure from clean* in a fixed direction (:func:`summarise_axes`), so a metric that falls
    steadily under blur and one that rises steadily under noise both read as following their
    degradation; which way a metric moves carries no weight.

    One sign per (dataset, metric, field, degradation): the sign of the median over frames of
    ``v(L) - v(0)``, the departure at level ``L`` from the clean value of the same frame. One
    sign per row, never one per point: choosing the sign point by point (ranking the absolute
    departure) lets a response that scatters to both sides of clean, more widely at each level,
    read as a perfect trend. A two-field error metric is exactly zero on the clean field, so its
    sign is ``+1`` and its statistics are those of its raw values.

    ``L`` is the harshest usable level (not flagged ``severity_degenerate``) whose median
    departure is finite and more than round-off against the metric's largest value: round-off
    carries no direction, so ``L`` is the harshest level that moved the metric at all. A
    translation-invariant quantity under a sub-pixel shift is the case that needs it: it moves at
    fractional distances and is back on its clean value to round-off at whole cells, the harshest
    levels (``increment_flatness`` on density, comparison_1790639359); a sign defaulted at ``+1``
    there would decide the sign of its ``rho`` by convention.

    Returns:
        ``{(dataset, metric, field, degradation): +1 or -1}``. A row with no such level, every
        median departure round-off, has no direction and no key; its callers default to ``+1``,
        and the round-off guard of the ordering statistics withholds it.
    """
    clean = dict(list(df[df["level"] == 0].groupby(GROUP_KEYS, observed=True)))
    ladder = df[(df["level"] > 0) & ~_degenerate_severities(df)]
    scales = df["value"].abs().groupby([df[k] for k in GROUP_KEYS], observed=True).max()
    out: dict[tuple, int] = {}
    for (*key, axis), g in ladder.groupby([*GROUP_KEYS, "degradation"], observed=True):
        key = tuple(key)
        if key not in clean:
            continue
        by_frame = clean[key].groupby("frame_index", observed=True)["value"].median()
        departure = (g["value"] - g["frame_index"].map(by_frame)).to_numpy(float)
        for level in sorted(g["level"].unique(), reverse=True):
            at_level = departure[(g["level"] == level).to_numpy()]
            if not np.isfinite(at_level).any():
                continue
            median = float(np.nanmedian(at_level))
            if abs(median) > DEGENERATE_SPAN * float(scales.loc[key]):
                out[(*key, axis)] = 1 if median > 0 else -1
                break
    return out


def _relative_change(rows: pd.DataFrame) -> pd.Series:
    """Each row's departure from the clean value of its frame, over that clean value's size.

    ``(v - v(0)) / |v(0)|`` per (dataset, metric, field, frame): "the value moved 30% from its
    clean value". NaN where the clean value is round-off against the largest value in the frame,
    which is every row of a two-field error metric, whose clean value is exactly zero; its damage
    is the relative reading there. ``rows`` must hold the clean (level 0) rows of every frame it
    holds.
    """
    keys = [rows[k] for k in (*GROUP_KEYS, "frame_index")]
    clean = rows["value"].where(rows["level"] == 0).groupby(keys, observed=True).transform("median")
    scale = rows["value"].abs().groupby(keys, observed=True).transform("max")
    with np.errstate(divide="ignore", invalid="ignore"):
        relative = (rows["value"] - clean) / clean.abs()
    return relative.where(clean.abs() > DEGENERATE_SPAN * scale)


# --- per-axis criteria ------------------------------------------------------------------


def summarise_axes(df: pd.DataFrame, *, norm: pd.DataFrame | None = None,
                   block_length: int = BLOCK_LENGTH, n_bootstrap: int = N_BOOTSTRAP,
                   seed: int = 0, probe_labels: frozenset[str] = PROBE_LABELS) -> pd.DataFrame:
    """One row per (dataset, metric, field, ladder axis) with the criteria of group A.

    Args:
        df: The tidy result frame, with or without a ``damage`` column.
        norm: Normalisation anchors. When given, the sensitivity and saturation levels are
            measured against the shared clean-to-anchor span, which makes them
            comparable across axes; without it each axis is measured against its own
            range and the numbers mean different things on different rows.
        block_length: Moving-block bootstrap block length, in frames (see :data:`N_BOOTSTRAP`).
        n_bootstrap: Bootstrap resamples.
        seed: Bootstrap seed.
        probe_labels: Ladder labels that are probes or anchors rather than monotone axes; the
            run's declaration, from :func:`run_labels`.
    """
    rng = np.random.default_rng(seed)
    reference = df[df["level"] == 0]
    references = dict(list(reference.groupby(GROUP_KEYS, observed=True)))
    directions = response_direction(df)
    relative = _relative_change(df)
    # A degenerate span is carried as NaN rather than dropped. Dropping it would make the
    # threshold levels fall back to each axis's own range, and passing it through would make
    # them meaningless in the other direction: a tenth of a round-off span is cleared by any
    # real response, so every family would read "first strength detected: level 1".
    spans = _anchor_by_group(norm, "span")
    # The anchor itself, for a target-valued metric: its onset span must be measured on the same
    # |log(value / target)| scale its ordering statistics run on, not in raw units.
    highs = _anchor_by_group(norm, "value_anchor")
    rows = []

    # Severity levels that resolved to the same experiment as a milder one are not independent
    # points. Scoring a tie would read as agreement in the rank correlation and would compare a
    # distribution against itself in the separability, so they are dropped and counted.
    ladder = df[df["level"] > 0]
    degenerate = _degenerate_severities(ladder)
    ladder = ladder[~degenerate]
    if degenerate.any():
        log.info("excluded %d rows on severity levels that resolved to a milder severity level's "
                 "severity; n_levels below is what was measured, n_levels_configured what was "
                 "asked for", int(degenerate.sum()))

    # What "round-off" means for a metric is set by the largest value it reaches anywhere, not
    # by the axis being ranked (see :func:`_is_round_off`). The scale is taken per frame for the
    # per-frame statistics because a metric's magnitude drifts along a trajectory by many orders
    # -- density's perturbation grows six -- and a whole-trajectory maximum would call early
    # frames round-off.
    magnitude = df.assign(_abs=df["value"].abs())
    frame_scales = magnitude.groupby([*GROUP_KEYS, "frame_index"], observed=True)["_abs"].max()
    group_scales = magnitude.groupby(GROUP_KEYS, observed=True)["_abs"].max()
    largest = _largest_responses(pd.concat([reference, ladder]), GROUP_KEYS, probe_labels)

    for (*key, axis), g in ladder.groupby([*GROUP_KEYS, "degradation"], observed=True):
        key = tuple(key)
        dataset, metric, field = key
        frame_scale = frame_scales.loc[key].to_dict()
        group_scale = float(group_scales.loc[key])
        levels = g["level"].to_numpy()
        values = g["value"].to_numpy()
        is_probe = axis in probe_labels
        # The value a calibrated prediction attains, when the metric declares one; None for the
        # ordinary case, where the metric is an error and zero is best.
        declared = g["target_value"].dropna().unique() if "target_value" in g.columns else []
        first = float(declared[0]) if len(declared) else np.nan
        target = first if np.isfinite(first) and first > 0 else None
        clean_rows = references.get(key, reference.iloc[:0])
        clean = float(clean_rows["value"].median())
        # Every ordering statistic below is computed on the oriented value (:func:`_oriented`),
        # so "rises with damage" holds by construction and the four of them need no direction
        # argument. For an ordinary metric that is the departure from the clean value of the
        # same frame times the degradation's measured sign (:func:`response_direction`): the
        # clean level is not a point of the trend, and a value that crosses its clean value
        # while moving steadily one way still follows the degradation. A target-valued metric
        # keeps its distance from the target. The reported values stay in the metric's own units.
        base = clean_base = 0.0
        if target is None:
            by_frame = clean_rows.groupby("frame_index", observed=True)["value"].median()
            base = g["frame_index"].map(by_frame)
            clean_base = clean_rows["frame_index"].map(by_frame)
        sign = directions.get((*key, axis), 1) if target is None else 1
        oriented = g.assign(value=_oriented(g["value"] - base, sign, target))
        # The clean value on the same scale: zero by construction for an ordinary metric, and
        # near zero for a calibrated prediction.
        oriented_clean = (0.0 if target is None
                          else float(_oriented(pd.Series([clean]), sign, target).iloc[0]))

        record: dict[str, object] = {
            **dict(zip(GROUP_KEYS, key, strict=True)),
            "degradation": axis,
            "degradation_family": g["degradation_family"].iloc[0],
            "is_probe": is_probe,
            "n_levels": int(g["level"].nunique()),
            "n_levels_configured": int(
                df[(df["field"] == field) & (df["degradation"] == axis)]["level"].nunique()
            ),
            "n_frames": int(g["frame_index"].nunique()),
            "value_clean": clean,
            "value_min": float(values.min()),
            "value_max": float(values.max()),
            "cost_s": float(g["wall_time_s"].mean()),
            "direction": sign,
            # Reactivity relative to clean, (v - v(0)) / |v(0)|, at the harshest usable level.
            "relative_change_max": float(relative.loc[g.index[levels == levels.max()]].median()),
        }

        if is_probe or g["level"].nunique() < 2:
            record.update(dict.fromkeys(
                ("rho", "rho_frame_min", "rho_pooled", "rho_ci_lo", "rho_ci_hi",
                 "monotone_fraction", "separability_auc_min", "sensitivity_level",
                 "saturation_level"), np.nan) | _withheld_response())
        else:
            # The span's size: the trace is oriented to rise whichever way the metric moves.
            span = spans.get(key)
            span_size = None if span is None else abs(span)
            rho_by_frame = _per_frame_rho(oriented, frame_scale)
            per_frame = np.fromiter(rho_by_frame.values(), dtype=float, count=len(rho_by_frame))
            lo, hi = _block_bootstrap_rho(rho_by_frame, np.sort(g["frame_index"].unique()), rng,
                                          block_length, n_bootstrap)
            # An all-NaN per-frame correlation is a documented outcome, not a surprise: it is
            # what a metric invariant to this axis produces once the round-off guard has done
            # its job. Suppressed here so it does not read as a numerical accident.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                rho_median = float(np.nanmedian(per_frame)) if len(per_frame) else np.nan
                rho_worst = float(np.nanmin(per_frame)) if len(per_frame) else np.nan
            # When every frame is round-off the axis carries no ordering at all, so the other
            # ordering statistics are withheld with rho.
            axis_round_off = bool(len(per_frame)) and bool(np.isnan(per_frame).all())
            record.update(
                rho=rho_median,
                rho_frame_min=rho_worst,
                rho_pooled=(np.nan if _is_round_off(oriented["value"].to_numpy(), group_scale)
                            else float(spearmanr(levels, oriented["value"].to_numpy()).statistic)),
                rho_ci_lo=lo,
                rho_ci_hi=hi,
                monotone_fraction=(
                    np.nan if axis_round_off else _monotone_fraction(oriented)),
                separability_auc_min=(
                    np.nan if axis_round_off else _min_adjacent_auc(oriented)),
                # Thresholds compare against the clean severity level on whatever scale the
                # ordering statistics run on, so a target-valued metric measures its
                # departure from *calibration* rather than from a raw ratio.
                sensitivity_level=np.nan if axis_round_off else _threshold_level(
                    oriented, oriented_clean, SENSITIVITY_FRACTION, span_size, group_scale),
                saturation_level=np.nan if axis_round_off else _threshold_level(
                    oriented, oriented_clean, SATURATION_FRACTION, span_size, group_scale),
            )
            if target is None:
                response_span = np.nan if span_size is None else span_size
            else:
                high = highs.get(key, np.nan)
                response_span = (
                    float(_oriented(pd.Series([high]), sign, target).iloc[0]) - oriented_clean
                    if np.isfinite(high) else np.nan
                )
            record.update(_response_statistics(
                g, oriented, oriented_clean, target, response_span,
                frame_scale, axis_round_off, record["separability_auc_min"],
                largest.get(key, np.nan), n_bootstrap,
                derive_rng(seed, f"blindness/{dataset}/{metric}/{axis}", 0, str(field)),
                clean_rows.assign(
                    value=_oriented(clean_rows["value"] - clean_base, sign, target)),
            ))
        if "damage" in g.columns:
            damage = g["damage"].to_numpy()
            # All-NaN whenever the anchor is degenerate, which is the documented outcome for a
            # metric that cannot tell the anchor from the reference.
            record["damage_max"] = (
                float(np.nanmax(damage)) if np.isfinite(damage).any() else np.nan
            )
        rows.append(record)

    axes = pd.DataFrame(rows)
    if "blindness_p" in axes.columns:
        # Benjamini & Yekutieli (2001, Ann. Stat. 29(4):1165-1188): valid under arbitrary
        # dependence, which the rows have -- they share frames and fields, and metrics correlate.
        # Adjusted over every row of the run, the several hundred tests the protocol runs at once.
        tested = axes["blindness_p"].notna()
        axes["blindness_q"] = np.nan
        if tested.any():
            axes.loc[tested, "blindness_q"] = false_discovery_control(
                axes.loc[tested, "blindness_p"].to_numpy(float), method="by")
        axes = axes.drop(columns="blindness_p")
    return axes


def _degenerate_severities(rows: pd.DataFrame) -> pd.Series:
    """Which rows sit on a severity level that repeated a milder one or did nothing.

    False throughout for a run that predates the ``severity_degenerate`` column.
    """
    if "severity_degenerate" not in rows.columns:
        return pd.Series(False, index=rows.index)
    return rows["severity_degenerate"].fillna(False).astype(bool)


def _anchor_by_group(norm: pd.DataFrame | None, column: str) -> dict[tuple, float]:
    """``{(dataset, metric, field): norm[column]}``, NaN where the anchor is degenerate."""
    if norm is None:
        return {}
    return {key: (float("nan") if bool(degenerate) else float(value))
            for key, value, degenerate in zip(norm.set_index(GROUP_KEYS).index, norm[column],
                                              norm["degenerate"], strict=True)}


def _paired_medians(g: pd.DataFrame) -> pd.Series:
    """Median over frames of each degradation level's value minus the clean value in the same frame.

    Paired within the frame because a single-field quantity drifts along the trajectory --
    enstrophy decays -- and against the trajectory's median clean value the drift itself would
    read as a response, the same trap as pooling frames for a rank correlation.
    """
    clean = g[g["level"] == 0].groupby("frame_index", observed=True)["value"].median()
    rest = g[g["level"] > 0]
    difference = rest["value"] - rest["frame_index"].map(clean)
    return difference.groupby([rest["degradation"], rest["level"]], observed=True).median()


def _largest_responses(rows: pd.DataFrame, keys: list[str],
                       probe_labels: frozenset[str] = PROBE_LABELS) -> dict[tuple, float]:
    """The largest absolute paired departure from clean any ordinal level produces, per group.

    The scale the blindness bound falls back to when the anchor is degenerate
    (issues/037), so that a metric which cannot see the anchor can still be shown not to respond
    to that anchor's operator.
    """
    out: dict[tuple, float] = {}
    for key, g in rows.groupby(keys, observed=True):
        medians = _paired_medians(g[~g["degradation"].isin(probe_labels) | (g["level"] == 0)])
        if len(medians):
            out[key] = float(np.nanmax(np.abs(medians.to_numpy(float))))
    return out


def _withheld_response() -> dict[str, object]:
    """The response columns for a row that has no ordering to describe."""
    return {c: "" if c in _TEXT_COLUMNS else np.nan for c in RESPONSE_COLUMNS}


def _response_x(g: pd.DataFrame, levels: list) -> tuple[np.ndarray, str]:
    """A severity per level that INCREASES with level, and the name of what it is.

    A calibrated operator records the absolute value it resolved to, which can fall with level
    and differs per field: on the pinned run comparison_1790639359 a vorticity low-pass records
    cutoffs 33.3, 17.1, 8.0 and 4.7 under the name "energy removed". A slope against that has the
    wrong sign and the wrong label, so a calibrated axis uses the configured fraction, which rises
    with level and means the same on every field.

    An uncalibrated knob that falls with level is read through its complement ``1 - x`` when its
    values are fractions -- a retained fraction, whose identity is 1 and whose harshest level is 0,
    becomes the fraction removed -- and through its reciprocal otherwise. The reciprocal of a
    retained fraction is infinite at total attenuation, which would drop that level from the onset
    and the slope.
    """
    calibration = g["calibration"].iloc[0] if "calibration" in g.columns else ""
    calibrated = isinstance(calibration, str) and calibration != ""
    column = "severity_nominal" if calibrated and "severity_nominal" in g.columns else "severity"
    x = g.groupby("level", observed=True)[column].median().reindex(levels).to_numpy(float)
    name = f"{column} ({g['severity_name'].iloc[0]})" if "severity_name" in g.columns else column
    if len(x) > 1 and x[-1] < x[0]:
        if np.all((x >= 0) & (x <= 1)):
            return 1.0 - x, f"1 - {name}"
        with np.errstate(divide="ignore"):
            return 1.0 / x, f"1/{name}"
    return x, name


def _response_statistics(g: pd.DataFrame, oriented: pd.DataFrame, oriented_clean: float,
                         target: float | None, span: float, frame_scale: Mapping[int, float],
                         axis_round_off: bool, auc: float, largest_response: float,
                         n_bootstrap: int, rng: np.random.Generator,
                         clean_rows: pd.DataFrame) -> dict[str, object]:
    """How strongly, how early and how precisely one axis moves the metric: the RESPONSE_COLUMNS.

    Everything is read on the oriented scale the ordering statistics use, so a metric where larger
    is better and a target-valued metric are handled as the other statistics handle them; ``span``
    is the clean-to-anchor span on that scale (NaN when the anchor is degenerate).

    * ``cliffs_delta_min`` -- ``2 A - 1`` of the weakest adjacent pair, so 0 is no separation
      (Cliff 1993, *Psychol. Bull.* 114(3):494-509; Vargha & Delaney 2000, *J. Educ. Behav. Stat.*
      25(2):101-132).
    * ``elasticity`` -- the log-log slope of the size of the median response against the severity
      named by ``elasticity_x``, over the mildest :data:`ELASTICITY_LEVELS` levels.
    * ``response_shape`` -- see :func:`fmeval.stats.fit_response_shape`.
    * ``severity_10`` / ``severity_50`` -- the severity at which the median crosses 10% / 50% of
      the span, interpolated between measured levels; the mildest level when it already has.
    * ``severity_resolution`` -- the median over adjacent pairs of the paired-step Fisher bound,
      on values divided by the metric's largest value in the same frame, which removes the drift of
      the flow along the trajectory (six orders on density) from what would otherwise be counted as
      scatter. A target-valued metric is already on a drift-free scale and is not divided.
    * ``field_change_max`` -- the median ``energy_changed`` at the harshest usable level.
    * ``damage_per_change`` -- the median damage at that level over ``field_change_max``: the
      per-degradation response behind ``selectivity``. Both are medians at the same level.
    * ``blindness_block_length``, ``damage_max_ucb``, ``blindness_q`` -- see
      :func:`_blindness_bound`.
      Computed on round-off axes too: a response that is round-off against a finite span is
      exactly a response provably below the margin.

    ``rng`` is derived from the group's own keys, never the generator the rank-correlation
    interval shares across groups, so nothing here can move an existing interval.
    """
    frames = np.sort(g["frame_index"].unique())
    levels = sorted(g["level"].unique())

    def by_frame_and_level(frame: pd.DataFrame, column: str) -> np.ndarray:
        return (frame.pivot_table(index="frame_index", columns="level", values=column,
                                  aggfunc="median", observed=True)
                .reindex(index=frames, columns=levels).to_numpy(float))

    Y = by_frame_and_level(oriented, "value")
    # Read within each frame, against the clean field of the same frame (see _paired_medians).
    clean =clean_rows.groupby("frame_index", observed=True)[
        [c for c in ("value", "damage") if c in clean_rows.columns]].median().reindex(frames)
    paired = Y - clean["value"].to_numpy(float)[:, None]
    Z = Y
    if target is None:
        scale = np.array([frame_scale.get(f, np.nan) for f in frames], dtype=float)
        scale[scale <= 0] = np.nan
        Z = Y / scale[:, None]
    x, x_name = _response_x(g, levels)
    out = _withheld_response()
    out.update(
        cliffs_delta_min=2.0 * auc - 1.0,
        elasticity_x=x_name,
        field_change_max=(
            float(g.loc[g["level"] == levels[-1], "energy_changed"].median())
            if "energy_changed" in g.columns else np.nan
        ),
    )
    # Damage relative to the clean field of the same frame, where a damage scale exists. Not for a
    # target-valued metric: its damage is on the raw ratio and is not oriented.
    damage = None
    if target is None and "damage" in g.columns and "damage" in clean.columns:
        damage = by_frame_and_level(g, "damage") - clean["damage"].to_numpy(float)[:, None]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            harshest = float(np.nanmedian(damage[:, -1]))
        change = out["field_change_max"]
        if np.isfinite(harshest) and np.isfinite(change) and change > 0:
            out["damage_per_change"] = harshest / change
    if damage is not None and n_bootstrap > 0:
        if (not np.isfinite(damage).any() and np.isfinite(largest_response)
                and largest_response > 0):
            damage = paired / largest_response   # the anchor is degenerate: read against the ladder
        if np.isfinite(damage).any():
            out.update(_blindness_bound(damage, Z, n_bootstrap, rng))
    if axis_round_off:
        return out
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        response = np.nanmedian(paired, axis=0)
        resolution = stats.fisher_severity_resolution(x, Z)
        out["severity_resolution"] = (
            float(np.nanmedian(resolution)) if np.isfinite(resolution).any()
            or np.isinf(resolution).any() else np.nan
        )
    # A fall is read by its size, as the two-sided bound is; rho already gives the direction.
    magnitude = -response if np.isfinite(response[-1]) and response[-1] < 0 else response
    out.update(
        elasticity=stats.elasticity(x[:ELASTICITY_LEVELS], magnitude[:ELASTICITY_LEVELS]),
        response_shape=stats.fit_response_shape(x, magnitude)[0],
    )
    if np.isfinite(span):
        # Between measured levels only: a knob's identity is not always 0 (a coarsening factor's
        # is 1), so a crossing before the mildest level is reported as that level.
        out.update(
            severity_10=stats.severity_at(x, response, SENSITIVITY_FRACTION * span),
            severity_50=stats.severity_at(x, response, HALF_DAMAGE_FRACTION * span),
        )
    return out


def _blindness_bound(D: np.ndarray, Z: np.ndarray, n_bootstrap: int,
                     rng: np.random.Generator) -> dict[str, float]:
    """An upper bound on the largest damage one degradation produces, and how surely it is small.

    A metric that does not respond significantly is not thereby shown to be blind to the
    degradation; that is accepting the null. Equivalence testing reverses the logic (Schuirmann
    1987, J. Pharmacokinet. Biopharm. 15(6):657-680; Lakens 2017): the claim is made only when the
    upper confidence bound of the response lies below a margin fixed in advance.

    Two-sided, as the two one-sided tests of an equivalence test are: a large fall is a response
    as much as a large rise. Frames are resampled in moving blocks, and in each resample the largest
    absolute per-level median damage is taken. ``damage_max_ucb`` is the
    :data:`BLINDNESS_CONFIDENCE` quantile of those, and
    ``blindness_p`` the fraction of resamples in which it reached :data:`BLINDNESS_MARGIN` -- a
    bootstrap tail fraction, not a test p-value -- which :func:`summarise_axes` adjusts across
    the run and drops. On one trajectory the resampling measures variation along it, not between
    realisations (issues/004).

    The block length is estimated on ``Z``, the frame-scaled trace, so the drift of the flow along
    the trajectory is not read as persistence (Politis & White 2004).

    Args:
        D: Frames by levels, damage (or the relative response when the anchor is degenerate).
        Z: Frames by levels, the same values divided by the metric's scale in each frame.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        block = stats.politis_white_block_length(np.nanmedian(Z, axis=1))
        out: dict[str, float] = {"blindness_block_length": block}
        if len(D) < 2 * block:
            return out
        draws = np.array([
            np.nanmax(np.abs(np.nanmedian(D[idx], axis=0)))
            for idx in stats.block_bootstrap(len(D), block, n_bootstrap, rng)
        ])
    draws = draws[np.isfinite(draws)]
    if draws.size:
        out["damage_max_ucb"] = float(np.percentile(draws, 100 * BLINDNESS_CONFIDENCE))
        out["blindness_p"] = float(np.mean(draws >= BLINDNESS_MARGIN))
    return out


def _per_frame_rho(g: pd.DataFrame,
                   frame_scale: Mapping[int, float] | None = None) -> dict[int, float]:
    """Spearman correlation between severity level and value, computed separately in each frame.

    **This is the primary statistic, not the pooled one.** Pooling every (level, value)
    pair across frames conflates the metric's response to severity with any trend in the
    field itself, and on this data that ruins it: the density perturbation grows six orders
    of magnitude along the trajectory, so the worst severity level early is far smaller than the
    mildest severity level late. Measured consequence -- every density axis is perfectly ordered
    inside every frame, yet the pooled correlation reads between 0.10 and 0.91 depending on
    the axis. The pooled value is retained as ``rho_pooled`` for comparison, since a wide
    gap between the two is itself a signal that the field is non-stationary.

    ``frame_scale`` maps each frame to the metric's largest value in that frame across every
    axis; see :func:`_is_round_off` for why the axis alone cannot supply it.

    Returns ``{frame: rho}`` in frame order, for every frame with at least two levels; NaN
    where the frame's values are round-off.
    """
    frame_scale = frame_scale or {}
    out: dict[int, float] = {}
    for frame, sub in g.groupby("frame_index", observed=True):
        if sub["level"].nunique() < 2:
            continue
        out[frame] = (np.nan if _is_round_off(sub["value"].to_numpy(), frame_scale.get(frame))
                      else spearmanr(sub["level"], sub["value"]).statistic)
    return out


def _is_round_off(values: np.ndarray, scale: float | None = None) -> bool:
    """Whether a set of values differs by no more than floating-point noise.

    A rank correlation is defined for any values that are not exactly tied, and float64
    arithmetic almost never ties exactly: ``np.roll`` cannot change a translation-invariant
    quantity, but it does change the summation order inside ``np.mean``, so the severity levels come
    out differing in the last bits and in an arbitrary order. Ranking that gives a number:
    without this test, enstrophy on a translation-only ladder scores ``rho = 0.707`` on
    ``translate_x`` from values spanning a relative 1.6e-16, indistinguishable in the heatmap
    from a genuine correlation.

    ``scale`` is the metric's own magnitude -- its largest value anywhere in the same frame
    or group -- and the test uses whichever of it and the values' largest is bigger.
    Without it an axis the metric is invariant to *and* on which it is zero cannot be
    caught: every value is ~1e-16, so the largest is ~1e-16 and the spread is a large
    fraction of it.
    """
    finite = values[np.isfinite(values)]
    if len(finite) < 2:
        return True
    scale = max(float(np.max(np.abs(finite))), float(scale or 0.0))
    if scale == 0.0:
        return True          # every value is exactly zero: no ordering to measure
    return bool(float(np.ptp(finite)) < DEGENERATE_SPAN * scale)


def _monotone_fraction(g: pd.DataFrame) -> float:
    """Fraction of frames on which the severity level ordering is strictly correct.

    A metric can look fine pooled and be non-monotone within every individual frame, which
    a single correlation hides.
    """
    ok = 0
    frames = g["frame_index"].unique()
    for frame in frames:
        sub = g[g["frame_index"] == frame].sort_values("level")
        if np.all(np.diff(sub["value"].to_numpy()) > 0):
            ok += 1
    return ok / len(frames) if len(frames) else float("nan")


def _min_adjacent_auc(g: pd.DataFrame) -> float:
    """Smallest Mann-Whitney AUC between adjacent severity levels' distributions over time.

    Monotone medians are not enough: if adjacent severity levels overlap, the metric cannot rank two
    models that differ by one severity level. Reported as a descriptive overlap measure only -- no
    p-value, because the trace is autocorrelated and any independence-assuming test would
    be badly anti-conservative.
    """
    levels = sorted(g["level"].unique())
    if len(levels) < 2:
        return float("nan")
    aucs = []
    for a, b in pairwise(levels):
        xa = g.loc[g["level"] == a, "value"].to_numpy()
        xb = g.loc[g["level"] == b, "value"].to_numpy()
        if len(xa) < 2 or len(xb) < 2:
            continue
        u = mannwhitneyu(xb, xa, alternative="greater").statistic
        aucs.append(u / (len(xa) * len(xb)))
    return float(min(aucs)) if aucs else float("nan")


def _threshold_level(g: pd.DataFrame, clean: float, fraction: float,
                     shared_span: float | None = None,
                     scale: float | None = None) -> float:
    """First level whose median reaches ``fraction`` of the way to the anchor.

    Measured against the shared span when one is available, so "fires at severity level 2" means the
    same thing on every axis. Falling back to each axis's own range would make an axis that
    barely damages the field appear just as sensitive as one that destroys it.
    """
    medians = g.groupby("level", observed=True)["value"].median().sort_index()
    if medians.empty:
        return float("nan")
    if _is_round_off(medians.to_numpy(), scale):
        # Not defined when the metric never departs from clean: any target built from a
        # round-off span is cleared by round-off, so the answer would always be level 1.
        return float("nan")
    span = shared_span if shared_span is not None else float(medians.iloc[-1]) - clean
    if not np.isfinite(span) or span == 0:
        return float("nan")
    target = clean + fraction * span
    reached = medians[medians >= target]
    return float(reached.index[0]) if len(reached) else float("nan")


def _block_bootstrap_rho(per_frame: Mapping[int, float], frames: np.ndarray,
                         rng: np.random.Generator, block_length: int,
                         n: int) -> tuple[float, float]:
    """Percentile interval for the per-frame Spearman median, over blocks of frames.

    Blocks of frames, for the reason given at :data:`N_BOOTSTRAP`. The
    resampling is :func:`fmeval.stats.block_bootstrap` over the sorted ``frames``, and what is
    resampled is the per-frame statistic :func:`_per_frame_rho` computed, round-off guard
    included -- so an axis whose ``rho`` is withheld as round-off cannot carry a finite interval.
    """
    if len(frames) < 2 * block_length or n <= 0 or not per_frame:
        return (float("nan"), float("nan"))
    # An all-round-off axis still runs the resampling loop below rather than returning here.
    # The generator is shared across every group in `summarise_axes`, so skipping this
    # group's draws would shift every later group's interval, on axes this guard never touches.
    all_round_off = not np.isfinite(list(per_frame.values())).any()

    draws = []
    for idx in stats.block_bootstrap(len(frames), block_length, n, rng):
        values = [per_frame[f] for f in frames[idx] if f in per_frame]
        if values and not all_round_off:
            # A resample can still land only on withheld frames when some are round-off.
            finite = [v for v in values if np.isfinite(v)]
            draws.append(float(np.median(finite)) if finite else np.nan)
    if not draws or not np.isfinite(draws).any():
        return (float("nan"), float("nan"))
    return (float(np.nanpercentile(draws, 5)), float(np.nanpercentile(draws, 95)))


# --- probes --------------------------------------------------------------------------


def probe_summary(df: pd.DataFrame, norm: pd.DataFrame, *,
                  anchor_label: str = MEAN_FIELD_LABEL,
                  probe_labels: frozenset[str] = PROBE_LABELS) -> pd.DataFrame:
    """One row per (dataset, metric, field) for the non-monotone probes.

    Reports the IN-4 damage score alongside the ladder severity level whose damage is closest, which
    is what makes it interpretable: "the Gaussian field looks as bad as coarsening to 64".

    A group that ran no probe contributes no row. The probes are ordinary ladder entries
    and a custom ladder may omit them -- the ensemble miscalibration ladder does, since a
    phase-scrambled field says nothing about whether an ensemble is honestly dispersed. A row
    carrying only the group keys would make the card generator write a trap-test line with an
    em dash for its score, which a reader cannot distinguish from a trap test that ran and
    could not be scored.

    When the anchor is degenerate the impostor has no damage, so ``gaussian_impostor_relative``
    reports its departure from clean as a fraction of the largest departure any ordinary level
    produced, the probe's departure oriented by its own measured direction
    (:func:`response_direction`), so the number is its size -- the interim number issues/037
    proposes. For a
    phase-blind metric it reads about 1e-15: the fake prediction moves it no more than round-off
    while a blur moves it fully. It is NaN whenever a damage exists, so the two never sit together.
    """
    scored = df if "damage" in df.columns else add_damage(df, norm)
    directions = response_direction(df)
    degenerate = norm.set_index(GROUP_KEYS)["degenerate"].to_dict()
    rows = []
    for key, g in scored.groupby(GROUP_KEYS, observed=True):
        record = dict(zip(GROUP_KEYS, key, strict=True))
        present = sorted(probe_labels & set(g["degradation"].unique()))
        if not present:
            continue
        for label in present:
            sub = g[g["degradation"] == label]
            damage = float(sub["damage"].median())
            record[f"{label}_value"] = float(sub["value"].median())
            record[f"{label}_damage"] = damage
            if label != anchor_label:
                # The anchor's damage is 1 by construction, so the level nearest it says nothing
                # about the anchor and reporting it would add a column with no information.
                record[f"{label}_nearest_level"] = _nearest_level(g, damage, probe_labels)
        if "gaussian_impostor" in present:
            record["gaussian_impostor_relative"] = (
                _relative_response(g, "gaussian_impostor",
                                   directions.get((*key, "gaussian_impostor"), 1), probe_labels)
                if bool(degenerate.get(key, False)) else np.nan
            )
        rows.append(record)
    if not rows:
        # Empty, but still carrying the group keys: every consumer filters this frame by
        # metric or field before reading it, and a frame with no columns at all raises a
        # KeyError on that filter rather than returning nothing.
        return pd.DataFrame(columns=GROUP_KEYS)
    return pd.DataFrame(rows)


def _relative_response(g: pd.DataFrame, label: str, sign: int,
                       probe_labels: frozenset[str]) -> float:
    """A probe's paired departure from clean as a fraction of the largest ordinary-level one."""
    scale = float(np.nanmax(np.abs(g["value"].to_numpy()))) or 1.0
    medians = _paired_medians(g)
    if medians.empty:
        return float("nan")
    degradations = medians.index.get_level_values(0)
    ordinary = medians[~np.isin(degradations.astype(str), list(probe_labels))]
    largest = float(np.nanmax(np.abs(ordinary.to_numpy(float)))) if len(ordinary) else np.nan
    if not np.isfinite(largest) or largest < DEGENERATE_SPAN * scale:
        return float("nan")                    # the ladder itself is round-off: no scale at all
    probe = medians[degradations.astype(str) == label]
    return float(sign * probe.iloc[0] / largest) if len(probe) else float("nan")


def _nearest_level(g: pd.DataFrame, damage: float,
                   probe_labels: frozenset[str] = PROBE_LABELS) -> str:
    """The usable ordinal severity level whose median damage is closest to ``damage``, for
    interpretation, written with its median strength over frames."""
    ordinal = g[(~g["degradation"].isin(probe_labels)) & (g["level"] > 0)
                & ~_degenerate_severities(g)]
    if ordinal.empty or not np.isfinite(damage):
        return ""
    # One strength per level, the median over frames: a per_unit_time level's grows in time.
    levels = ordinal.groupby(["degradation", "level"], observed=True)[["damage", "severity"]]
    medians = levels.median()
    if medians.empty:
        return ""
    label, level = medians["damage"].sub(damage).abs().idxmin()
    return f"{label}={medians.loc[(label, level), 'severity']:g}"


# --- roll-up and flagging ---------------------------------------------------------------


def report_card(axes: pd.DataFrame, probes: pd.DataFrame,
                norm: pd.DataFrame) -> pd.DataFrame:
    """One row per (dataset, metric, field): the criteria gathered for reading.

    Deliberately has no verdict column. It carries the measurements; :func:`flag` adds an
    advisory ``flags`` string, and the decision is made by people.
    """
    ordinal = axes[~axes["is_probe"]]
    if ordinal.empty:
        base = axes[GROUP_KEYS].drop_duplicates()
    else:
        base = (
            ordinal.groupby(GROUP_KEYS, observed=True)
            .agg(
                n_axes=("degradation", "nunique"),
                rho_min=("rho", "min"),
                rho_median=("rho", "median"),
                rho_pooled_min=("rho_pooled", "min"),
                separability_auc_min=("separability_auc_min", "min"),
                monotone_fraction_min=("monotone_fraction", "min"),
                sensitivity_level_median=("sensitivity_level", "median"),
                saturation_level_median=("saturation_level", "median"),
                cost_s=("cost_s", "mean"),
            )
            .reset_index()
        )
        # ``idxmin`` raises on an all-NA group rather than returning NA, and a group is
        # all-NA whenever a metric is exactly invariant to every ordinal operator in the
        # ladder -- a single-field invariant against a translation-only ladder, say. That is a
        # legitimate configuration, so only rows with a defined rho are searched.
        rho_defined = ordinal[ordinal["rho"].notna()]
        if rho_defined.empty:
            base["worst_axis"] = pd.NA
        else:
            worst = rho_defined.loc[
                rho_defined.groupby(GROUP_KEYS, observed=True)["rho"].idxmin()
            ][[*GROUP_KEYS, "degradation"]].rename(columns={"degradation": "worst_axis"})
            base = base.merge(worst, on=GROUP_KEYS, how="left")
        profiles = [dict(zip(GROUP_KEYS, key, strict=True), **_profile(g))
                    for key, g in ordinal.groupby(GROUP_KEYS, observed=True)]
        base = base.merge(pd.DataFrame(profiles), on=GROUP_KEYS, how="left")

    for extra in (probes, norm[[*GROUP_KEYS, "value_clean", "value_anchor", "span",
                                "anchor_source", "degenerate"]]):
        if not extra.empty:
            base = base.merge(extra, on=GROUP_KEYS, how="left")

    if "cost_s" in base.columns and not base.empty:
        base["cost_relative"] = relative_cost(base["cost_s"])
    return base


def relative_cost(cost: pd.Series) -> pd.Series | float:
    """Each cost as a multiple of the cheapest; NaN when the cheapest is zero."""
    cheapest = cost.min()
    return cost / cheapest if cheapest else np.nan


def _profile(axes: pd.DataFrame) -> dict[str, object]:
    """What one metric responds to, across the ordinal degradations of one field.

    The response on each degradation is ``damage_per_change``: the median damage at its harshest
    usable level over the median field change there. Raw damage would describe the ladder rather
    than the metric -- how far the config pushed each degradation -- and every metric would name the
    harshest translation as its most sensitive axis. Per unit of ``energy_changed``, the mean
    squared difference over the reference variance, mean squared error costs the same on every
    degradation and the profile of any other metric is what it charges relative to that one.

    * ``selectivity`` -- one minus the Treves-Rolls sparseness of that profile (Treves & Rolls 1991,
      Network 2(4):371-397): 0 when every degradation costs the same per unit change, approaching
      1 when one degradation carries it all. Depends on which degradations the ladder ran.
    * ``most_sensitive_axis``, ``least_sensitive_axis`` -- the two ends of the profile.
    * ``blind_axes`` -- degradations whose largest damage is provably below
      :data:`BLINDNESS_MARGIN` (``blindness_q`` below :data:`FDR_LEVEL`), ``"; "``-joined.
    * ``elasticity_displacement`` -- the elasticity on ``translate_subpixel``, the double-penalty
      exponent, when the ladder ran it.
    """
    per_unit = pd.Series(dtype=float)
    if "damage_per_change" in axes.columns:
        per_unit = axes["damage_per_change"].set_axis(axes["degradation"])
        per_unit = per_unit[np.isfinite(per_unit)]
    blind = (sorted(axes.loc[axes["blindness_q"] < FDR_LEVEL, "degradation"].astype(str))
             if "blindness_q" in axes.columns else [])
    displacement = (axes.loc[axes["degradation"] == DISPLACEMENT_AXIS, "elasticity"].dropna()
                    if "elasticity" in axes.columns else pd.Series(dtype=float))
    return dict(zip(PROFILE_COLUMNS, (     # in the order of the bullets above
        (1.0 - stats.treves_rolls_sparseness(per_unit.to_numpy())
         if len(per_unit) >= 2 else np.nan),
        per_unit.idxmax() if len(per_unit) else pd.NA,
        per_unit.idxmin() if len(per_unit) else pd.NA,
        BLIND_SEPARATOR.join(blind),
        float(displacement.iloc[0]) if len(displacement) else np.nan,
    ), strict=True))


def per_coordinate(curve: pd.DataFrame) -> pd.DataFrame:
    """Curve-companion rows with each coordinate read as a metric of its own, ``name[coordinate]``.

    The form :func:`summarise_axes`, :func:`per_level_response` and :func:`response_direction` take,
    so a curve gets, coordinate by coordinate, the statistics any metric gets.
    """
    return curve.assign(metric=curve["metric"].astype(str) + "["
                        + curve["coordinate"].map(coordinate_label) + "]")


def coordinate_label(coordinate: object) -> str:
    """A curve coordinate as text, the one spelling every table and label uses.

    A number is written as the shortest decimal that reads back as the same float, without a
    trailing ``.0``: distinct coordinates never share a label, as six significant figures would
    let ``1234567`` and ``1234568`` do, and ``4`` and ``4.0`` -- an integer coordinate as a CSV
    may return it -- stay one coordinate. Anything else is written as it is.
    """
    if isinstance(coordinate, (int, float, np.integer, np.floating)):
        return repr(float(coordinate)).removesuffix(".0")
    return str(coordinate)


def dominance(curve: pd.DataFrame, probe_labels: frozenset[str] = PROBE_LABELS) -> pd.DataFrame:
    """Whether a curve's ordering of neighbouring strengths can depend on the summary chosen.

    For each frame and each pair of neighbouring usable damaged levels (the clean level is not a
    point of the trend), the harsher level's curve dominates the milder one's when every
    coordinate has moved at least as far from clean, in that coordinate's own measured direction
    (:func:`response_direction`); a difference within round-off of the coordinate's largest value
    in the frame is a tie, as :func:`_is_round_off` reads one, so noise in the last bits cannot
    decide a pair. Any registered number that is
    non-decreasing in every coordinate's oriented departure -- a root-mean-square, a largest
    difference -- then orders the pair the same way; a fitted slope need not. The fraction of frames
    in which the harsher dominates is computed per pair, after the forecast dominance of Ehm et
    al. (2016, J. R. Stat. Soc. B 78(3):505-562), and ``dominance_min`` is the smallest over pairs.
    Coordinates without a measured direction on a degradation (round-off departures) are left out
    of it, since round-off cannot dominate. A frame in which either curve of a pair lacks a finite
    value at one of those coordinates does not enter that pair's fraction: an unknown departure
    neither dominates nor fails to.

    Returns:
        One row per (dataset, metric, field, ordinal degradation) with ``dominance_min`` and
        ``n_coordinates``, the coordinates it was read over.
    """
    directions = response_direction(per_coordinate(curve))
    clean = dict(list(curve[curve["level"] == 0].groupby(GROUP_KEYS, observed=True)))
    scales = {key: g.assign(value=g["value"].abs()).pivot_table(
                  index="frame_index", columns="coordinate", values="value", aggfunc="max")
              for key, g in curve.groupby(GROUP_KEYS, observed=True)}
    ladder = curve[(curve["level"] > 0) & ~curve["degradation"].isin(probe_labels)
                   & ~_degenerate_severities(curve)]
    rows = []
    for (*key, axis), g in ladder.groupby([*GROUP_KEYS, "degradation"], observed=True):
        key = tuple(key)
        if key not in clean or g["level"].nunique() < 2:
            continue
        base = clean[key].pivot_table(index="frame_index", columns="coordinate", values="value",
                                      aggfunc="first")
        signs = {c: directions.get((key[0], f"{key[1]}[{coordinate_label(c)}]", key[2], axis))
                 for c in base.columns}
        coordinates = [c for c, sign in signs.items() if sign is not None]
        levels = sorted(g["level"].unique())
        values = g.pivot_table(index="frame_index", columns=["level", "coordinate"],
                               values="value", aggfunc="first")
        frames = values.index.intersection(base.index)
        cube = (values.reindex(index=frames,
                               columns=pd.MultiIndex.from_product([levels, coordinates]))
                .to_numpy(float).reshape(len(frames), len(levels), len(coordinates))
                - base.reindex(index=frames, columns=coordinates).to_numpy(float)[:, None, :])
        oriented = cube * np.array([signs[c] for c in coordinates], dtype=float)
        complete = np.isfinite(oriented).all(axis=2)
        read = complete[:, 1:] & complete[:, :-1]          # (frame, pair) comparisons made
        tie = DEGENERATE_SPAN * scales[key].reindex(index=frames, columns=coordinates).to_numpy(
            float)[:, None, :]
        dominated = (oriented[:, 1:, :] >= oriented[:, :-1, :] - tie).all(axis=2) & read
        counted = read.sum(axis=0)
        made = counted > 0
        rows.append({**dict(zip(GROUP_KEYS, key, strict=True)), "degradation": axis,
                     "dominance_min": (float((dominated.sum(axis=0)[made] / counted[made]).min())
                                       if coordinates and made.any() else np.nan),
                     "n_coordinates": len(coordinates)})
    return pd.DataFrame(rows, columns=[*GROUP_KEYS, "degradation", "dominance_min",
                                       "n_coordinates"])


@dataclass(frozen=True)
class Analysis:
    """Everything the report and the cards derive from one run."""

    norm: pd.DataFrame
    scored: pd.DataFrame
    """The result rows with ``damage`` attached."""
    axes: pd.DataFrame
    probes: pd.DataFrame
    card: pd.DataFrame
    """Unflagged; :func:`flag` is the report's business, and cards never carry flags."""
    anchor_label: str
    probe_labels: frozenset[str]
    companion_scored: pd.DataFrame = dc_field(default_factory=pd.DataFrame)
    """Curve-companion rows with ``damage`` attached per coordinate and ``metric`` read as
    :func:`per_coordinate` labels it; empty without a curve."""
    companion_axes: pd.DataFrame = dc_field(default_factory=pd.DataFrame)
    """:func:`summarise_axes` on the companion rows, one row per (metric, field, degradation,
    coordinate), with no bootstrap. Never enters :func:`report_card`, :func:`flag`, the
    cross-metric matrices or the false-discovery adjustment of the panel."""
    dominance: pd.DataFrame = dc_field(default_factory=pd.DataFrame)
    """:func:`dominance` per (metric, field, degradation)."""


def analyse(rows: pd.DataFrame, *, companions: pd.DataFrame | None = None,
            meta: Mapping | None = None, config: Mapping | None = None,
            block_length: int = BLOCK_LENGTH, n_bootstrap: int = N_BOOTSTRAP,
            seed: int = 0) -> Analysis:
    """Every statistic of one run, in one call.

    The report driver and the card evidence loader both call this, so a card carries exactly the
    statistics its report shows. ``meta`` and ``config`` are the run's ``run_meta.json`` and
    resolved configuration, from which the anchor and probe labels are read (:func:`run_labels`).
    Called with neither, on rows that come from no run folder, it uses the current defaults:
    :data:`MEAN_FIELD_LABEL` and :data:`PROBE_LABELS`.

    ``companions`` are the run's curve-companion rows. Each coordinate is analysed as a metric of
    its own (:func:`per_coordinate`) by the same functions as the panel, with no bootstrap, into
    tables of their own beside it. Adjacent coordinates of one curve are strongly correlated, so a
    curve of per-coordinate statistics localises the evidence and does not multiply it.
    """
    anchor, probe_labels = (run_labels(meta or {}, config)
                            if meta is not None or config is not None
                            else (MEAN_FIELD_LABEL, PROBE_LABELS))
    norm = normalisation(rows, anchor_label=anchor, probe_labels=probe_labels)
    scored = add_damage(rows, norm)
    axes = summarise_axes(scored, norm=norm, block_length=block_length, n_bootstrap=n_bootstrap,
                          seed=seed, probe_labels=probe_labels)
    probes = probe_summary(scored, norm, anchor_label=anchor, probe_labels=probe_labels)
    extra = {}
    if companions is not None and not companions.empty:
        labelled = per_coordinate(companions)
        curve_norm = normalisation(labelled, anchor_label=anchor, probe_labels=probe_labels)
        curve_scored = add_damage(labelled, curve_norm)
        curve_axes = summarise_axes(curve_scored, norm=curve_norm, n_bootstrap=0, seed=seed,
                                    probe_labels=probe_labels)
        bundle = dict(zip(labelled["metric"], zip(companions["metric"].astype(str),
                                                  companions["coordinate"], strict=True)))
        curve_axes.insert(1, "coordinate", curve_axes["metric"].map(lambda m: bundle[m][1]))
        curve_axes["metric"] = curve_axes["metric"].map(lambda m: bundle[m][0])
        extra = {"companion_scored": curve_scored,
                 "companion_axes": curve_axes,
                 "dominance": dominance(companions, probe_labels)}
    return Analysis(norm=norm, scored=scored, axes=axes, probes=probes,
                    card=report_card(axes, probes, norm), anchor_label=anchor,
                    probe_labels=probe_labels, **extra)


#: How ``blind_axes`` joins its degradations into one cell, so the CSV stays one row per group.
BLIND_SEPARATOR = "; "


def split_blind(value: object) -> list[str]:
    """The degradations a ``blind_axes`` cell lists; empty for a missing or empty cell."""
    if not isinstance(value, str):
        return []      # None, NaN or pd.NA: a group with nothing listed
    return [a for a in value.split(BLIND_SEPARATOR) if a]


def flag(card: pd.DataFrame, thresholds: Mapping[str, float]) -> pd.DataFrame:
    """Add an advisory ``flags`` column naming which reference thresholds were not met.

    Separate from the computation on purpose. An empty ``flags`` means nothing was
    flagged, **not** that the metric is approved; the thresholds are reference values for
    drawing attention, not acceptance criteria.
    """
    out = card.copy()
    # Every check flags a value BELOW its reference.
    checks: list[tuple[str, str, float]] = [
        ("rho_min", "spearman", thresholds.get("spearman", np.nan)),
        ("separability_auc_min", "separability_auc", thresholds.get("separability_auc", np.nan)),
        ("gaussian_impostor_damage", "impostor_damage", thresholds.get("impostor_damage", np.nan)),
    ]
    messages = []
    for _, row in out.iterrows():
        notes = []
        for column, name, limit in checks:
            if column not in out.columns or not np.isfinite(limit):
                continue
            value = row.get(column)
            if value is None or not np.isfinite(value):
                continue
            if value < limit:
                notes.append(f"{name}={value:.2f} < {limit:g}")
        if bool(row.get("degenerate", False)):
            notes.append("no dynamic range")
        messages.append("; ".join(notes))
    out["flags"] = messages
    return out


# --- cross-metric ------------------------------------------------------------------------


def cross_metric_correlation(df: pd.DataFrame, *, field: str | None = None) -> pd.DataFrame:
    """Spearman correlation between metrics across the ladder, for pruning.

    One observation per (axis, level), using the median over time, which is the level at
    which the panel decision is actually made. Using every raw row instead would inflate
    the correlation through shared time trends.

    The reference severity level is excluded. Every pairwise error metric is exactly zero there, so
    keeping it would add a point all metrics share by construction and pull every
    correlation towards +1.
    """
    sub = df if field is None else df[df["field"] == field]
    sub = sub[sub["level"] > 0]
    pivot = (
        sub.groupby(["degradation", "level", "metric"], observed=True)["value"]
        .median()
        .unstack("metric")
        .dropna(how="any")
    )
    if pivot.shape[1] < 2 or len(pivot) < 3:
        return pd.DataFrame()
    rho = pivot.corr(method="spearman")
    rho.index.name = "metric"
    return rho


#: The columns of :func:`damage_by_level` that are not metrics.
LEVEL_KEYS: tuple[str, ...] = ("field", "degradation", "level", "severity")

#: The degradation families whose per-strength damage a card sets beside the other metrics: the
#: ones where magnitude, not order, is the claim.
DAMAGE_BLOCK_FAMILIES: tuple[str, ...] = ("geometric",)

#: The metrics a card's damage table and figure place beside its own: the pointwise controls
#: every candidate has to be read against.
DAMAGE_BLOCK_CONTROLS: tuple[str, ...] = ("mae", "mse", "rmse", "nrmse")

#: The grouping keys of :func:`per_level_response`, in the order its rows are sorted.
RESPONSE_KEYS: tuple[str, ...] = ("field", "degradation_family", "degradation", "level")

#: Per-row columns :func:`per_level_response` carries through unchanged from the first row of
#: each level, and the value used when a run predates the column.
_RESPONSE_CARRIED: dict[str, object] = {
    "severity": np.nan, "severity_nominal": np.nan, "severity_name": "", "calibration": "",
}


def per_level_response(scored: pd.DataFrame, *, metric: str,
                       probe_labels: frozenset[str] = PROBE_LABELS) -> pd.DataFrame:
    """The response curve of one metric: one row per field, degradation and severity level.

    This is the record a figure draws and the number a reader should be able to download: the
    median, lower and upper quartile over frames of both the damage and the raw value at every
    level, the change relative to the clean value of the same frame (:func:`_relative_change`;
    NaN throughout for a metric whose clean value is zero), with the strength that was applied,
    how much it measurably changed the field, and
    whether the level was a distinct experiment. The reference level and the probes are left
    out; levels flagged ``severity_degenerate`` are **kept and flagged**, unlike in
    :func:`damage_by_level`, because a figure should show a reader that a level was excluded
    rather than silently draw a shorter curve. Over the non-degenerate rows the
    ``damage_median`` column equals the metric's column of :func:`damage_by_level`, and a
    test holds the two together.

    Args:
        scored: Rows with ``damage`` attached, from :func:`add_damage` or :func:`analyse`.
        metric: The metric to record.
        probe_labels: Ladder entries that are probes or anchors rather than ordered axes.

    Returns:
        A frame sorted by :data:`RESPONSE_KEYS`. ``damage_*`` are NaN wherever the field has
        no damage scale; ``value_*`` are always finite where the metric produced a value.

    Raises:
        KeyError: If ``scored`` has no ``damage`` column.
    """
    if "damage" not in scored.columns:
        raise KeyError("per_level_response needs the damage column; pass add_damage(df, norm)")
    rows = scored[scored["metric"].astype(str) == metric]
    sub = rows.assign(relative_change=_relative_change(rows))
    sub = sub[(sub["level"] > 0) & ~sub["degradation"].isin(probe_labels)].copy()
    for column, default in {**_RESPONSE_CARRIED, "energy_changed": np.nan}.items():
        if column not in sub.columns:
            sub[column] = default
    # A level is flagged when no frame of it is a usable experiment. A level usable in some
    # frames (a per_unit_time level is a no-op on the first frame only) is read over those, as
    # summarise_axes reads it.
    flagged = _degenerate_severities(sub)
    level_flagged = flagged.groupby([sub[k] for k in RESPONSE_KEYS], observed=True).transform("all")
    sub = sub[~flagged | level_flagged].assign(severity_degenerate=level_flagged)
    columns = [*RESPONSE_KEYS, *_RESPONSE_CARRIED, "severity_degenerate", "n_frames",
               "damage_median", "damage_q25", "damage_q75",
               "value_median", "value_q25", "value_q75", "relative_change_median",
               "relative_change_q25", "relative_change_q75", "energy_changed_median"]
    if sub.empty:
        return pd.DataFrame(columns=columns)
    out = (
        sub.groupby(list(RESPONSE_KEYS), observed=True)
        .agg(
            # The strength is the median over frames, which differ for a per_unit_time level.
            **{c: (c, "first") for c in _RESPONSE_CARRIED} | {"severity": ("severity", "median")},
            severity_degenerate=("severity_degenerate", "any"),
            n_frames=("frame_index", "nunique"),
            damage_median=("damage", "median"),
            damage_q25=("damage", lambda s: s.quantile(0.25)),
            damage_q75=("damage", lambda s: s.quantile(0.75)),
            value_median=("value", "median"),
            value_q25=("value", lambda s: s.quantile(0.25)),
            value_q75=("value", lambda s: s.quantile(0.75)),
            relative_change_median=("relative_change", "median"),
            relative_change_q25=("relative_change", lambda s: s.quantile(0.25)),
            relative_change_q75=("relative_change", lambda s: s.quantile(0.75)),
            energy_changed_median=("energy_changed", "median"),
        )
        .reset_index()
        .sort_values(list(RESPONSE_KEYS), kind="stable")
        .reset_index(drop=True)
    )
    out["level"] = out["level"].astype(int)
    for column in ("calibration", "severity_name"):
        out[column] = out[column].fillna("").astype(str)
    return out[columns]


def damage_by_level(scored: pd.DataFrame, *, field: str | None = None,
                    family: str | None = None,
                    probe_labels: frozenset[str] = PROBE_LABELS) -> pd.DataFrame:
    """Median damage over frames at every strength of every degradation, one column per metric.

    Two metrics can order every degradation identically and still charge very different amounts
    for the same one; this is where that shows. The reference
    level, the probes and severity levels that repeat a milder one are excluded; a metric whose
    damage is undefined everywhere (a degenerate anchor, issues/037) has no column.

    Raises:
        KeyError: If ``scored`` has no ``damage`` column.
    """
    if "damage" not in scored.columns:
        raise KeyError("damage_by_level needs the damage column; pass add_damage(df, norm)")
    sub = scored[(scored["level"] > 0) & ~scored["degradation"].isin(probe_labels)]
    sub = sub[~_degenerate_severities(sub)]
    if field is not None:
        sub = sub[sub["field"] == field]
    if family is not None:
        sub = sub[sub["degradation_family"] == family]
    if sub.empty:
        return pd.DataFrame(columns=list(LEVEL_KEYS))
    # One row per level, its strength the median over frames: a per_unit_time level's differs.
    keys = [k for k in LEVEL_KEYS if k != "severity"]
    wide = (sub.groupby([*keys, "metric"], observed=True)["damage"].median()
            .unstack("metric").dropna(axis=1, how="all"))
    wide.columns = [str(c) for c in wide.columns]
    wide.insert(0, "severity", sub.groupby(keys, observed=True)["severity"].median())
    return wide.reset_index()[[*LEVEL_KEYS, *wide.columns[1:]]]


def _metric_columns(wide: pd.DataFrame) -> list[str]:
    return [c for c in wide.columns if c not in LEVEL_KEYS]


def concordance_matrix(scored: pd.DataFrame, *, field: str | None = None,
                       probe_labels: frozenset[str] = PROBE_LABELS) -> pd.DataFrame:
    """Lin's concordance between every pair of metrics' damage, over the rows of damage_by_level.

    The redundancy matrix asks whether two metrics order the ladder alike; this asks whether they
    agree in magnitude, penalising departure from the identity line (Lin 1989, Biometrics
    45(1):255-268). On the pinned run comparison_1790639359, MAE and MSE rank-correlate at 0.986
    and have a concordance of 0.699. Pairwise-complete; empty below two metrics or three rows.
    """
    wide = damage_by_level(scored, field=field, probe_labels=probe_labels)
    metrics = _metric_columns(wide)
    if len(metrics) < 2 or len(wide) < 3:
        return pd.DataFrame()
    return pd.DataFrame(
        [[stats.lins_ccc(wide[a].to_numpy(float), wide[b].to_numpy(float)) for b in metrics]
         for a in metrics],
        index=pd.Index(metrics, name="metric"), columns=metrics,
    )


def participation_ratio_of_metrics(scored: pd.DataFrame,
                                   probe_labels: frozenset[str] = PROBE_LABELS) -> float:
    """The effective number of independent directions the metrics' damage responses span.

    (sum lambda)^2 / sum lambda^2 over the eigenvalues of the metric-by-metric covariance of the
    complete rows of damage_by_level (Gao et al. 2017, bioRxiv 214262). The covariance is not
    standardised on purpose: damage already puts every metric on one scale, and standardising
    would give a nearly unresponsive metric's noise the weight of a responsive metric's signal.

    Returns:
        A number between 1 and the metric count, or NaN below two metrics or three complete rows.
    """
    wide = damage_by_level(scored, probe_labels=probe_labels)
    metrics = _metric_columns(wide)
    complete = wide[metrics].dropna()
    if len(metrics) < 2 or len(complete) < 3:
        return float("nan")
    eigenvalues = np.clip(np.linalg.eigvalsh(np.cov(complete.to_numpy(float), rowvar=False)),
                          0.0, None)
    total = float(np.sum(eigenvalues**2))
    return float(np.sum(eigenvalues) ** 2 / total) if total > 0 else float("nan")
