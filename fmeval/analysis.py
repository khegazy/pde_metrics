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
from itertools import pairwise

import numpy as np
import pandas as pd
from scipy.stats import false_discovery_control, mannwhitneyu, spearmanr

from . import stats
from .context import derive_rng

log = logging.getLogger(__name__)

#: Ladder labels that are probes or reference measurements, not monotone axes.
PROBE_LABELS: frozenset[str] = frozenset({"gaussian_impostor", "uncorrelated"})

#: Label of the measured anchor: the value a metric gives two statistically identical but
#: positionally unrelated fields. Defines D = 1.
UNCORRELATED_LABEL: str = "uncorrelated"

#: Fraction of the clean-to-uncorrelated range at which a metric counts as having
#: departed from clean. Fixed once here and never tuned per metric.
SENSITIVITY_FRACTION: float = 0.10

#: Fraction of the uncorrelated limit at which a metric counts as saturated.
SATURATION_FRACTION: float = 0.90

#: Fraction of the clean-to-unrelated span at which the half-damage severity is read. Fixed
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
#: Two things use it. The damage score needs its ``clean``-to-``uncorrelated`` span to be a
#: real span, and a metric invariant to the operator the anchor is built from has no span at
#: all -- most of the position-tolerant family this project exists to develop is invariant to
#: translation, which is how the anchor is constructed. The rank correlation needs the values
#: it is ranking to differ by more than the last few bits, and ``np.roll`` changes the
#: summation order inside ``np.mean`` even when it cannot change the quantity, which was
#: enough to produce a reported ``rho`` of 0.707 on an axis whose values spanned a relative
#: 1.6e-16. Both are round-off presented as measurement.
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
    :data:`UNCORRELATED_LABEL` and :data:`PROBE_LABELS`, so it keeps rendering as it did.
    """
    configured = ((config or {}).get("analysis") or {}).get("anchor")
    anchor = meta.get("anchor_label") or configured or UNCORRELATED_LABEL
    recorded = meta.get("probe_labels")
    return str(anchor), (frozenset(recorded) if recorded is not None else PROBE_LABELS)


def normalisation(df: pd.DataFrame, *, uncorrelated_label: str = UNCORRELATED_LABEL,
                  probe_labels: frozenset[str] = PROBE_LABELS) -> pd.DataFrame:
    """Anchors that put every metric on one dimensionless scale.

    Raw mean squared error and a raw transport distance are not comparable, so a *damage
    score* is defined per (dataset, metric, field):

        D = (v - clean) / (uncorrelated - clean)

    ``clean`` is the median value on the reference severity level. ``uncorrelated`` is *measured*,
    not inferred: the ``uncorrelated`` ladder entry applies several large random
    translations, which preserve every statistic exactly while destroying alignment, and
    the metric is evaluated against those. D = 1 then means "as different as two unrelated
    fields", which is what makes the score readable across metrics with different units.

    Scavenging the largest configured translation severity level instead would understate the anchor
    badly: on the real data a 16-cell displacement only reaches about 0.6 of the true
    uncorrelated value, so every damage score would be inflated by roughly 1.6x.

    A ratio to the clean value is not usable here: mean squared error on the reference severity
    level is exactly zero. Per-figure min-max scaling is not usable either, because the figure would
    change whenever a severity level is added.

    Returns:
        One row per (dataset, metric, field) with ``value_clean``, ``value_uncorrelated``,
        ``span``, ``anchor_source`` and ``degenerate``.
    """
    rows = []
    for (dataset, metric, field), g in df.groupby(
        ["dataset", "metric", "field"], observed=True
    ):
        clean = float(g.loc[g["level"] == 0, "value"].median()) if (g["level"] == 0).any() \
            else float("nan")
        high, source = _uncorrelated_anchor(g, uncorrelated_label, probe_labels)
        span = high - clean
        # The scale is the LARGEST value anywhere in the group, not the median. The median is
        # defeated in exactly the case this guard exists for: a metric invariant to the
        # operator the anchor is built from returns round-off on the anchor, on the impostor
        # and on every translation severity level, so more than half the rows are round-off and the
        # median collapses to round-off with them -- the guard then compares noise against
        # noise and passes. Measured with a spectral metric of the BD-1 shape on the real
        # trajectory: the anchor was 1.5e-16 against a genuine blur response of 3.5e-1, and
        # the impostor was reported at damage 1.17, which reads as "worse than two unrelated
        # fields" for a metric that cannot separate any of them.
        scale = float(np.nanmax(np.abs(g["value"].to_numpy()))) or 1.0
        rows.append(
            {
                "dataset": dataset,
                "metric": metric,
                "field": field,
                "value_clean": clean,
                "value_uncorrelated": high,
                "span": span,
                "anchor_source": source,
                "degenerate": not np.isfinite(span) or abs(span) < DEGENERATE_SPAN * scale,
            }
        )
    return pd.DataFrame(rows)


def _uncorrelated_anchor(g: pd.DataFrame, preferred: str,
                         probe_labels: frozenset[str] = PROBE_LABELS) -> tuple[float, str]:
    """Estimate the value two statistically identical but unaligned fields would give."""
    if preferred and (g["degradation"] == preferred).any():
        sub = g[g["degradation"] == preferred]
        return float(sub["value"].median()), preferred

    # Fall back to the largest configured translation. This UNDERSTATES the anchor --
    # 16 cells reaches only ~0.6 of the true value on this data -- so the source is
    # recorded and the report says so.
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
    keys = ["dataset", "metric", "field"]
    out = df.merge(norm[[*keys, "value_clean", "span", "degenerate"]], on=keys, how="left")
    with np.errstate(invalid="ignore", divide="ignore"):
        out["damage"] = (out["value"] - out["value_clean"]) / out["span"]
    out.loc[out["degenerate"], "damage"] = np.nan
    return out.drop(columns=["value_clean", "span", "degenerate"])


def _declared_target(g: pd.DataFrame) -> float | None:
    """The value a calibrated prediction attains, when the metric declares one.

    ``None`` for the ordinary case, where the metric is an error and zero is best.
    """
    if "target_value" not in g.columns:
        return None
    values = g["target_value"].dropna().unique()
    if len(values) == 0:
        return None
    target = float(values[0])
    return target if np.isfinite(target) and target > 0 else None


def _target_distance(values: pd.Series, target: float) -> pd.Series:
    """How far each value sits from ``target``, on a scale where the ratio is symmetric.

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
    v = values.to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.abs(np.log(v / target))
    return pd.Series(np.where(v > 0, out, np.inf), index=values.index)


def response_direction(df: pd.DataFrame,
                       norm: pd.DataFrame | None = None) -> dict[tuple, int]:
    """Which way each metric's value moves as damage rises: ``+1`` up, ``-1`` down.

    Three of the ordering statistics below are one-sided -- monotonicity requires a rising
    difference, the Mann-Whitney AUC is taken with ``alternative="greater"``, and the
    threshold levels look for the first median to exceed a target. Applied blind they assume
    every metric is an error measure. A metric where larger means a better match then arrives
    in the report card flagged on three criteria at once while being perfectly well behaved:
    measured on an axis falling cleanly from 1.0 to 0.2, ``rho = -1.0``,
    ``monotone_fraction = 0.0`` and ``separability_auc_min = 0.0``. That shape is not
    hypothetical -- it is any correlation, SSIM or skill score, and PS-2/PS-3 when they
    arrive.

    The direction is taken from the metric's own declaration where the run recorded one, and
    otherwise measured: the ``uncorrelated`` anchor is by construction as bad as a field can
    look, so an anchor below the clean value means larger is better. Measuring is the fallback
    rather than the primary source because the anchor is empty for a metric invariant to the
    translation it is built from -- the case the degeneracy guard above exists for.

    Returns:
        ``{(dataset, metric, field): +1 or -1}``. Missing keys mean ``+1``.
    """
    keys = ["dataset", "metric", "field"]
    out: dict[tuple, int] = {}

    if "higher_is_better" in df.columns:
        declared = df.groupby(keys, observed=True)["higher_is_better"].agg(
            lambda s: bool(s.iloc[0])
        )
        for key, higher in declared.items():
            out[key] = -1 if higher else 1

    anchors = norm if norm is not None else normalisation(df)
    for _, row in anchors.iterrows():
        key = (row["dataset"], row["metric"], row["field"])
        if key in out:
            continue                      # a declaration outranks an inference
        clean, high = row["value_clean"], row["value_uncorrelated"]
        if row["degenerate"] or not (np.isfinite(clean) and np.isfinite(high)):
            continue                      # no usable anchor: leave it at the default
        out[key] = -1 if high < clean else 1
    return out


# --- per-axis criteria ------------------------------------------------------------------


def summarise_axes(df: pd.DataFrame, *, norm: pd.DataFrame | None = None,
                   block_length: int = 10, n_bootstrap: int = 200,
                   seed: int = 0, probe_labels: frozenset[str] = PROBE_LABELS) -> pd.DataFrame:
    """One row per (dataset, metric, field, ladder axis) with the criteria of group A.

    Args:
        df: The tidy result frame, with or without a ``damage`` column.
        norm: Normalisation anchors. When given, the sensitivity and saturation levels are
            measured against the shared clean-to-unrelated span, which makes them
            comparable across axes; without it each axis is measured against its own
            range and the numbers mean different things on different rows.
        block_length: Moving-block bootstrap block length, in frames. The metric trace is
            autocorrelated in time, so an independent bootstrap would give absurdly tight
            intervals.
        n_bootstrap: Bootstrap resamples.
        seed: Bootstrap seed.
        probe_labels: Ladder labels that are probes or anchors rather than monotone axes; the
            run's declaration, from :func:`run_labels`.
    """
    rng = np.random.default_rng(seed)
    reference = df[df["level"] == 0]
    directions = response_direction(df, norm)
    # A degenerate span is carried as NaN rather than dropped. Dropping it would make the
    # threshold levels fall back to each axis's own range, and passing it through would make
    # them meaningless in the other direction: a tenth of a 1.6e-16 span is cleared by any
    # real response, so spectrum_l2 on comparison_1789632054 read "first strength detected:
    # level 1" on every family, against an anchor it cannot see.
    spans = (
        {
            key: (float("nan") if bool(degenerate) else float(span))
            for key, span, degenerate in zip(
                norm.set_index(["dataset", "metric", "field"]).index,
                norm["span"], norm["degenerate"], strict=True,
            )
        }
        if norm is not None else {}
    )
    # The anchor itself, for a target-valued metric: its onset span must be measured on the same
    # |log(value / target)| scale its ordering statistics run on, not in raw units.
    highs = (
        {
            key: (float("nan") if bool(degenerate) else float(high))
            for key, high, degenerate in zip(
                norm.set_index(["dataset", "metric", "field"]).index,
                norm["value_uncorrelated"], norm["degenerate"], strict=True,
            )
        }
        if norm is not None else {}
    )
    rows = []

    # Severity levels that resolved to the same experiment as a milder one are not independent
    # points. Scoring a tie would read as agreement in the rank correlation and would compare a
    # distribution against itself in the separability, so they are dropped and counted.
    ladder = df[df["level"] > 0]
    n_dropped = 0
    if "severity_degenerate" in ladder.columns:
        degenerate = ladder["severity_degenerate"].fillna(False).astype(bool)
        n_dropped = int(degenerate.sum())
        ladder = ladder[~degenerate]
        if n_dropped:
            log.info(
                "excluded %d rows on severity levels that resolved to a milder "
                "severity level's severity; "
                "n_levels below is what was measured, n_levels_configured what was asked for",
                n_dropped,
            )

    # What "round-off" means for a metric is set by the largest value it reaches anywhere,
    # not by the axis being ranked. An axis the metric is invariant to returns values that
    # are *all* near zero, so its own largest value is round-off too and a guard scaled to
    # it compares noise against noise. Measured on comparison_1789632054: spectrum_l2 sat
    # at 1e-16 on every translate_x severity level while reaching 0.62 under blur in the
    # same frames, and was reported at rho = -0.1 to 0.1 (translate_subpixel: -0.6 to
    # -0.71). The scale is taken per frame for the per-frame statistics because a metric's
    # magnitude drifts along a trajectory by many orders -- density's perturbation grows
    # six -- and a whole-trajectory maximum would call early frames round-off.
    keys = ["dataset", "metric", "field"]
    magnitude = df.assign(_abs=df["value"].abs())
    frame_scales = magnitude.groupby([*keys, "frame_index"], observed=True)["_abs"].max()
    group_scales = magnitude.groupby(keys, observed=True)["_abs"].max()
    largest = _largest_responses(pd.concat([reference, ladder]), keys, probe_labels)

    for (dataset, metric, field, axis), g in ladder.groupby(
        ["dataset", "metric", "field", "degradation"], observed=True
    ):
        frame_scale = frame_scales.loc[(dataset, metric, field)].to_dict()
        group_scale = float(group_scales.loc[(dataset, metric, field)])
        levels = g["level"].to_numpy()
        values = g["value"].to_numpy()
        is_probe = axis in probe_labels
        # Every ordering statistic below is computed on the value multiplied by this sign, so
        # "rises with damage" holds by construction and the four of them need no direction
        # argument. The reported values stay in the metric's own units.
        sign = directions.get((dataset, metric, field), 1)
        target = _declared_target(g)
        if target is None:
            oriented = g.assign(value=sign * g["value"])
        else:
            # A metric calibrated at an interior point is not monotone in damage: it is
            # wrong above the target and equally wrong below it. Ordering by distance
            # from the target is what makes the one-sided statistics mean what they say.
            oriented = g.assign(value=_target_distance(g["value"], target))
            sign = 1
        clean_rows = reference[
            (reference["dataset"] == dataset)
            & (reference["metric"] == metric)
            & (reference["field"] == field)
        ]
        clean = float(clean_rows["value"].median())
        # The clean value on the same scale the ordering statistics run on. For an
        # ordinary metric that is just the sign applied; for a target-valued one it is
        # the distance from the target, which is near zero for a calibrated prediction.
        oriented_clean = (
            sign * clean if target is None
            else float(_target_distance(pd.Series([clean]), target).iloc[0])
        )

        record: dict[str, object] = {
            "dataset": dataset,
            "metric": metric,
            "field": field,
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
            "higher_is_better": sign < 0,
        }

        if is_probe or g["level"].nunique() < 2:
            record.update(
                rho=np.nan, rho_frame_min=np.nan, rho_pooled=np.nan,
                rho_ci_lo=np.nan, rho_ci_hi=np.nan,
                monotone_fraction=np.nan, separability_auc_min=np.nan,
                sensitivity_level=np.nan, saturation_level=np.nan,
            )
            record.update(_withheld_response())
        else:
            per_frame = _per_frame_rho(oriented, frame_scale)
            lo, hi = _block_bootstrap_rho(oriented, rng, block_length, n_bootstrap,
                                          frame_scale)
            # An all-NaN per-frame correlation is a documented outcome, not a surprise: it is
            # what a metric invariant to this axis produces once the round-off guard has done
            # its job. Suppressed here so it does not read as a numerical accident.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                rho_median = float(np.nanmedian(per_frame)) if len(per_frame) else np.nan
                rho_worst = float(np.nanmin(per_frame)) if len(per_frame) else np.nan
            # When every frame is round-off the axis carries no ordering at all, and the
            # other ordering statistics are withheld with rho. They were not: spectrum_l2 on
            # translate_subpixel, whose values are 1e-12 against a blur response of 0.62,
            # reported a weakest gap of 0.026 -- "reliably ordered backwards" -- from the
            # last bits of a Fourier shift.
            axis_round_off = bool(len(per_frame)) and bool(np.isnan(per_frame).all())
            record.update(
                rho=rho_median,
                rho_frame_min=rho_worst,
                rho_pooled=(
                    np.nan if _is_round_off(values, group_scale)
                    else float(
                        spearmanr(levels, oriented["value"].to_numpy()).statistic
                        if target is not None
                        else sign * spearmanr(levels, values).statistic
                    )
                ),
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
                    oriented, oriented_clean, SENSITIVITY_FRACTION,
                    _signed(spans.get((dataset, metric, field)), sign), group_scale),
                saturation_level=np.nan if axis_round_off else _threshold_level(
                    oriented, oriented_clean, SATURATION_FRACTION,
                    _signed(spans.get((dataset, metric, field)), sign), group_scale),
            )
            key = (dataset, metric, field)
            if target is None:
                response_span = _signed(spans.get(key), sign)
            else:
                high = highs.get(key, np.nan)
                response_span = (
                    float(_target_distance(pd.Series([high]), target).iloc[0]) - oriented_clean
                    if np.isfinite(high) else np.nan
                )
            record.update(_response_statistics(
                g, oriented, oriented_clean, target,
                np.nan if response_span is None else response_span,
                frame_scale, axis_round_off, record["separability_auc_min"],
                largest.get(key, np.nan), n_bootstrap,
                derive_rng(seed, f"blindness/{dataset}/{metric}/{axis}", 0, str(field)),
                clean_rows.assign(value=(sign * clean_rows["value"] if target is None
                                         else _target_distance(clean_rows["value"], target))),
            ))
        if "damage" in g.columns:
            damage = g["damage"].to_numpy()
            # All-NaN whenever the anchor is degenerate, which is the documented outcome for a
            # metric that cannot tell the unrelated field from the reference.
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

    The scale the blindness bound falls back to when the unrelated-field anchor is degenerate
    (issues/037), so that a metric which cannot see the anchor can still be shown not to respond
    to that anchor's operator.
    """
    out: dict[tuple, float] = {}
    for key, g in rows.groupby(keys, observed=True):
        medians = _paired_medians(g[~g["degradation"].isin(probe_labels) | (g["level"] == 0)])
        if len(medians):
            out[key] = float(np.nanmax(np.abs(medians.to_numpy(float))))
    return out


def _signed(span: float | None, sign: int) -> float | None:
    """Orient a shared span, so a threshold on oriented values uses an oriented target."""
    return None if span is None else sign * span


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
    retained fraction is infinite at total attenuation, which dropped that level from the onset
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
    is the clean-to-unrelated span on that scale (NaN when the anchor is degenerate).

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
    # The response is read within each frame, against the clean field of the same frame: a
    # single-field quantity drifts along the trajectory (enstrophy decays), and against the
    # trajectory's median clean value that drift would read as a response.
    clean = clean_rows.groupby("frame_index", observed=True)[
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
        D = damage
        if not np.isfinite(D).any() and np.isfinite(largest_response) and largest_response > 0:
            D = paired / largest_response      # the anchor is degenerate: read against the ladder
        if np.isfinite(D).any():
            out.update(_blindness_bound(D, Z, n_bootstrap, rng))
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
                   frame_scale: Mapping[int, float] | None = None) -> np.ndarray:
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
    """
    frame_scale = frame_scale or {}
    out = []
    for frame, sub in g.groupby("frame_index", observed=True):
        if sub["level"].nunique() < 2:
            continue
        if _is_round_off(sub["value"].to_numpy(), frame_scale.get(frame)):
            out.append(np.nan)
            continue
        out.append(spearmanr(sub["level"], sub["value"]).statistic)
    return np.asarray(out, dtype=float)


def _is_round_off(values: np.ndarray, scale: float | None = None) -> bool:
    """Whether a set of values differs by no more than floating-point noise.

    A rank correlation is defined for any values that are not exactly tied, and float64
    arithmetic almost never ties exactly: ``np.roll`` cannot change a translation-invariant
    quantity, but it does change the summation order inside ``np.mean``, so the severity levels come
    out differing in the last bits and in an arbitrary order. Ranking that gives a number.

    Reproduced end to end -- ``evaluate.py metrics=[enstrophy]`` with a translation-only ladder
    reported ``rho_min = 0.707`` on ``translate_x`` from values spanning a relative 1.6e-16,
    printed in the monotonicity heatmap beside genuine correlations and indistinguishable from
    them.

    ``scale`` is the metric's own magnitude -- its largest value anywhere in the same frame
    or group -- and the test uses whichever of it and the values' largest is bigger.
    Without it an axis the metric is invariant to *and* on which it is zero cannot be
    caught: every value is ~1e-16, so the largest is ~1e-16 and the spread is a large
    fraction of it. Measured: spectrum_l2 on ``translate_x`` in comparison_1789632054,
    reported at rho = -0.1 to 0.1 over values twelve orders below its blur response.
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
    """First level whose median reaches ``fraction`` of the way to the unrelated limit.

    Measured against the shared span when one is available, so "fires at severity level 2" means the
    same thing on every axis. Falling back to each axis's own range would make an axis that
    barely damages the field appear just as sensitive as one that destroys it.
    """
    medians = g.groupby("level", observed=True)["value"].median().sort_index()
    if medians.empty:
        return float("nan")
    if _is_round_off(medians.to_numpy(), scale):
        # The level at which a metric "first departs from clean" is not defined when it never
        # departs. Without this the answer is always severity level 1, because any target built from
        # a round-off span is cleared by round-off: measured on enstrophy against a translation-only
        # ladder, both the sensitivity and saturation levels read 1.0 for a quantity translation
        # cannot change at all. Same principle as the rank-correlation guard.
        return float("nan")
    span = shared_span if shared_span is not None else float(medians.iloc[-1]) - clean
    if span is None or not np.isfinite(span) or span == 0:
        return float("nan")
    target = clean + fraction * span
    reached = medians[medians >= target]
    return float(reached.index[0]) if len(reached) else float("nan")


def _block_bootstrap_rho(
    g: pd.DataFrame, rng: np.random.Generator, block_length: int, n: int,
    frame_scale: Mapping[int, float] | None = None,
) -> tuple[float, float]:
    """Percentile interval for the per-frame Spearman median, over blocks of frames.

    Blocks rather than individual frames because the metric trace is autocorrelated;
    resampling frames independently would understate the interval by a large factor.

    The per-frame values are guarded exactly as :func:`_per_frame_rho` guards them. They
    once were not, so an axis whose ``rho`` was correctly withheld as round-off could still
    carry a finite interval around it.
    """
    frame_scale = frame_scale or {}
    frames = np.sort(g["frame_index"].unique())
    if len(frames) < 2 * block_length or n <= 0:
        return (float("nan"), float("nan"))
    block_length = max(1, min(block_length, len(frames) // 2))
    n_blocks = int(np.ceil(len(frames) / block_length))
    starts = np.arange(len(frames) - block_length + 1)
    by_frame = {f: g[g["frame_index"] == f] for f in frames}

    # Resample the PER-FRAME statistic, matching what `rho` reports.
    per_frame = {
        f: (np.nan if _is_round_off(sub["value"].to_numpy(), frame_scale.get(f))
            else spearmanr(sub["level"], sub["value"]).statistic)
        for f, sub in ((f, by_frame[f]) for f in frames)
        if sub["level"].nunique() >= 2
    }
    if not per_frame:
        return (float("nan"), float("nan"))
    # An all-round-off axis still runs the resampling loop below rather than returning here.
    # The generator is shared across every group in `summarise_axes`, so skipping this
    # group's draws would shift every later group's interval -- measured: returning early
    # moved the intervals of mae, h1_seminorm and increment_flatness on axes this guard
    # never touches.
    all_round_off = not np.isfinite(list(per_frame.values())).any()

    draws = []
    for _ in range(n):
        chosen = rng.choice(starts, size=n_blocks)
        picked = np.concatenate([frames[s: s + block_length] for s in chosen])
        values = [per_frame[f] for f in picked if f in per_frame]
        if values and not all_round_off:
            # A resample can still land only on withheld frames when some are round-off.
            finite = [v for v in values if np.isfinite(v)]
            draws.append(float(np.median(finite)) if finite else np.nan)
    if not draws or not np.isfinite(draws).any():
        return (float("nan"), float("nan"))
    return (float(np.nanpercentile(draws, 5)), float(np.nanpercentile(draws, 95)))


# --- probes --------------------------------------------------------------------------


def probe_summary(df: pd.DataFrame, norm: pd.DataFrame, *,
                  uncorrelated_label: str = UNCORRELATED_LABEL,
                  probe_labels: frozenset[str] = PROBE_LABELS) -> pd.DataFrame:
    """One row per (dataset, metric, field) for the non-monotone probes.

    Reports the IN-4 damage score alongside the ladder severity level whose damage is closest, which
    is what makes it interpretable: "the Gaussian field looks as bad as coarsening to 64".

    A group that ran no probe contributes no row. The probes are ordinary ladder entries
    and a custom ladder may omit them -- the ensemble miscalibration ladder does, since a
    phase-scrambled field says nothing about whether an ensemble is honestly dispersed.
    Emitting a row carrying only the group keys made the card generator write a trap-test
    line with an em dash for its score, which a reader cannot distinguish from a trap test
    that ran and could not be scored.

    When the anchor is degenerate the impostor has no damage, so ``gaussian_impostor_relative``
    reports its departure from clean as a fraction of the largest departure any ordinary level
    produced, both in the metric's own direction -- the interim number issues/037 proposes. For a
    phase-blind metric it reads about 1e-15: the fake prediction moves it no more than round-off
    while a blur moves it fully. It is NaN whenever a damage exists, so the two never sit together.
    """
    scored = add_damage(df, norm)
    directions = response_direction(df, norm)
    degenerate = norm.set_index(["dataset", "metric", "field"])["degenerate"].to_dict()
    rows = []
    for (dataset, metric, field), g in scored.groupby(
        ["dataset", "metric", "field"], observed=True
    ):
        record = {"dataset": dataset, "metric": metric, "field": field}
        present = sorted(probe_labels & set(g["degradation"].unique()))
        if not present:
            continue
        for label in present:
            sub = g[g["degradation"] == label]
            damage = float(sub["damage"].median())
            record[f"{label}_value"] = float(sub["value"].median())
            record[f"{label}_damage"] = damage
            if label != uncorrelated_label:
                # The anchor's nearest severity level is the largest translation by construction,
                # so reporting it would add a column that carries no information.
                record[f"{label}_nearest_level"] = _nearest_level(g, damage, exclude=label,
                                                                  probe_labels=probe_labels)
        if "gaussian_impostor" in present:
            key = (dataset, metric, field)
            record["gaussian_impostor_relative"] = (
                _relative_response(g, "gaussian_impostor", directions.get(key, 1), probe_labels)
                if bool(degenerate.get(key, False)) else np.nan
            )
        rows.append(record)
    if not rows:
        # Empty, but still carrying the group keys: every consumer filters this frame by
        # metric or field before reading it, and a frame with no columns at all raises a
        # KeyError on that filter rather than returning nothing.
        return pd.DataFrame(columns=["dataset", "metric", "field"])
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


def _nearest_level(g: pd.DataFrame, damage: float, exclude: str,
                   probe_labels: frozenset[str] = PROBE_LABELS) -> str:
    """The ordinal severity level whose damage is closest to ``damage``, for interpretation."""
    ordinal = g[(~g["degradation"].isin(probe_labels)) & (g["level"] > 0)]
    if ordinal.empty or not np.isfinite(damage):
        return ""
    medians = ordinal.groupby(["degradation", "level", "severity"], observed=True)[
        "damage"
    ].median()
    if medians.empty:
        return ""
    label, _level, severity = medians.sub(damage).abs().idxmin()
    return f"{label}={severity:g}"


# --- roll-up and flagging ---------------------------------------------------------------


def report_card(axes: pd.DataFrame, probes: pd.DataFrame,
                norm: pd.DataFrame) -> pd.DataFrame:
    """One row per (dataset, metric, field): the criteria gathered for reading.

    Deliberately has no verdict column. It carries the measurements; :func:`flag` adds an
    advisory ``flags`` string, and the decision is made by people.
    """
    ordinal = axes[~axes["is_probe"]]
    keys = ["dataset", "metric", "field"]
    if ordinal.empty:
        base = axes[keys].drop_duplicates()
    else:
        base = (
            ordinal.groupby(keys, observed=True)
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
        # legitimate configuration which AGENTS.md explicitly calls correct, and it used to
        # take down the whole report with a pandas message naming nothing in this codebase,
        # after the expensive evaluation had already been paid for.
        rho_defined = ordinal[ordinal["rho"].notna()]
        if rho_defined.empty:
            base["worst_axis"] = pd.NA
        else:
            worst = rho_defined.loc[
                rho_defined.groupby(keys, observed=True)["rho"].idxmin()
            ][[*keys, "degradation"]].rename(columns={"degradation": "worst_axis"})
            base = base.merge(worst, on=keys, how="left")
        profiles = [dict(zip(keys, key, strict=True), **_profile(g))
                    for key, g in ordinal.groupby(keys, observed=True)]
        base = base.merge(pd.DataFrame(profiles), on=keys, how="left")

    for extra in (probes, norm[[*keys, "value_clean", "value_uncorrelated", "span",
                                "anchor_source", "degenerate"]]):
        if not extra.empty:
            base = base.merge(extra, on=keys, how="left")

    if "cost_s" in base.columns and not base.empty:
        baseline = base["cost_s"].min()
        base["cost_relative"] = base["cost_s"] / baseline if baseline else np.nan
    return base


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
    displacement = (axes.loc[axes["degradation"] == "translate_subpixel", "elasticity"].dropna()
                    if "elasticity" in axes.columns else pd.Series(dtype=float))
    return {
        "selectivity": (1.0 - stats.treves_rolls_sparseness(per_unit.to_numpy())
                        if len(per_unit) >= 2 else np.nan),
        "most_sensitive_axis": per_unit.idxmax() if len(per_unit) else pd.NA,
        "least_sensitive_axis": per_unit.idxmin() if len(per_unit) else pd.NA,
        "blind_axes": "; ".join(blind),
        "elasticity_displacement": float(displacement.iloc[0]) if len(displacement) else np.nan,
    }


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
    anchor_label: str = UNCORRELATED_LABEL
    probe_labels: frozenset[str] = PROBE_LABELS


def analyse(rows: pd.DataFrame, *, meta: Mapping | None = None, config: Mapping | None = None,
            block_length: int = 10, n_bootstrap: int = 200, seed: int = 0) -> Analysis:
    """Every statistic of one run, in one call.

    The report driver and the card evidence loader used to repeat this sequence by hand and had
    drifted: the evidence loader skipped :func:`add_damage`, so a card carried none of the damage
    based columns its report showed. ``meta`` and ``config`` are the run's ``run_meta.json`` and
    resolved configuration, from which the anchor and probe labels are read (:func:`run_labels`).
    """
    anchor, probe_labels = run_labels(meta or {}, config)
    norm = normalisation(rows, uncorrelated_label=anchor, probe_labels=probe_labels)
    scored = add_damage(rows, norm)
    axes = summarise_axes(scored, norm=norm, block_length=block_length, n_bootstrap=n_bootstrap,
                          seed=seed, probe_labels=probe_labels)
    probes = probe_summary(rows, norm, uncorrelated_label=anchor, probe_labels=probe_labels)
    return Analysis(norm=norm, scored=scored, axes=axes, probes=probes,
                    card=report_card(axes, probes, norm), anchor_label=anchor,
                    probe_labels=probe_labels)


def flag(card: pd.DataFrame, thresholds: Mapping[str, float]) -> pd.DataFrame:
    """Add an advisory ``flags`` column naming which reference thresholds were not met.

    Separate from the computation on purpose. An empty ``flags`` means nothing was
    flagged, **not** that the metric is approved; the thresholds are reference values for
    drawing attention, not acceptance criteria.
    """
    out = card.copy()
    checks: list[tuple[str, str, float, bool]] = [
        ("rho_min", "spearman", thresholds.get("spearman", np.nan), True),
        ("separability_auc_min", "separability_auc",
         thresholds.get("separability_auc", np.nan), True),
        ("gaussian_impostor_damage", "impostor_damage",
         thresholds.get("impostor_damage", np.nan), True),
    ]
    messages = []
    for _, row in out.iterrows():
        notes = []
        for column, name, limit, below_is_flagged in checks:
            if column not in out.columns or not np.isfinite(limit):
                continue
            value = row.get(column)
            if value is None or not np.isfinite(value):
                continue
            if (value < limit) if below_is_flagged else (value > limit):
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


def damage_by_level(scored: pd.DataFrame, *, field: str | None = None,
                    family: str | None = None,
                    probe_labels: frozenset[str] = PROBE_LABELS) -> pd.DataFrame:
    """Median damage over frames at every strength of every degradation, one column per metric.

    The table issues/035 asks for: two metrics can order every degradation identically and still
    charge very different amounts for the same one, and this is where that shows. The reference
    level, the probes and severity levels that repeat a milder one are excluded; a metric whose
    damage is undefined everywhere (a degenerate anchor, issues/037) has no column.

    Raises:
        KeyError: If ``scored`` has no ``damage`` column.
    """
    if "damage" not in scored.columns:
        raise KeyError("damage_by_level needs the damage column; pass add_damage(df, norm)")
    sub = scored[(scored["level"] > 0) & ~scored["degradation"].isin(probe_labels)]
    if "severity_degenerate" in sub.columns:
        sub = sub[~sub["severity_degenerate"].fillna(False).astype(bool)]
    if field is not None:
        sub = sub[sub["field"] == field]
    if family is not None:
        sub = sub[sub["degradation_family"] == family]
    if sub.empty:
        return pd.DataFrame(columns=list(LEVEL_KEYS))
    wide = (sub.groupby([*LEVEL_KEYS, "metric"], observed=True)["damage"].median()
            .unstack("metric").dropna(axis=1, how="all").reset_index())
    wide.columns = [str(c) for c in wide.columns]
    return wide


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
    out = pd.DataFrame(
        [[stats.lins_ccc(wide[a].to_numpy(float), wide[b].to_numpy(float)) for b in metrics]
         for a in metrics],
        index=pd.Index(metrics, name="metric"), columns=metrics,
    )
    return out


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


def selectivity_profile(axes: pd.DataFrame) -> pd.DataFrame:
    """Rank correlation per metric against every ladder axis: what a metric detects.

    Read across a row rather than down a column. Two metrics with near-identical profiles
    are redundant even when their magnitudes differ, and a profile that is uniform across
    every axis indicates a metric responding to damage in general rather than to a
    specific failure mode.
    """
    ordinal = axes[~axes["is_probe"]]
    if ordinal.empty:
        return pd.DataFrame()
    return (
        ordinal.pivot_table(index=["metric", "field"], columns="degradation",
                            values="rho", observed=True)
        .reset_index()
    )
