"""Ordering statistics for a metric whose best value is not zero.

Every one-sided statistic in :mod:`fmeval.analysis` -- monotonicity, the adjacent-severity
AUC, the sensitivity and saturation thresholds, the rank correlation -- assumes damage
moves the value in one direction. That assumption fails for the spread-to-skill ratio,
which is calibrated at one and wrong on both sides of it: an ensemble that hedges reads
high, one that is overconfident reads low, and both are worse than the middle.

The repository adapts rather than the metric. ``spread_skill`` reports the raw ratio, as
the forecasting literature does, and declares ``target=1.0``; the analysis orders by
distance from that target. What is *reported* stays the ratio -- a reader still sees 0.4
and knows the ensemble is too narrow -- while what is *ranked* is how far from calibrated
it is.

Without this, a perfectly behaved calibration axis would arrive in the report card flagged on
three criteria at once, and the flag would say the metric is broken when the analysis is.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from fmeval.analysis import add_damage, normalisation, summarise_axes
from tests.conftest import make_frame


def _frame(values: list[float], *, metric: str = "spread_skill",
           target: float | None = 1.0) -> pd.DataFrame:
    """One ``spread_inflate`` axis whose levels take ``values``, level 0 first, in six frames.

    ``target_value`` is set when the metric declares a target, as the pipeline writes it.
    """
    df = make_frame(metric=metric, field="density", n_frames=6, reference=values[0],
                    axes={"spread_inflate": values[1:]})
    if target is not None:
        df["target_value"] = target
    return df


def _row(df: pd.DataFrame, axis: str = "spread_inflate") -> pd.Series:
    out = summarise_axes(df)
    return out[out["degradation"] == axis].iloc[0]


def test_a_ratio_falling_away_from_its_target_is_ranked_as_worsening():
    """Overconfidence: the ratio falls from 1.0 toward 0.2 as damage rises.

    Ranked by raw value this is a perfectly *decreasing* axis and would score rho = -1
    against a statistic expecting a rise. Ranked by distance from the target it is what
    it actually is: monotonically worsening.
    """
    df = _frame([1.0, 0.8, 0.55, 0.35, 0.2])
    row = _row(df)
    assert row["rho"] == pytest.approx(1.0)
    assert row["monotone_fraction"] == pytest.approx(1.0)


def test_a_ratio_rising_away_from_its_target_is_also_ranked_as_worsening():
    """Hedging: the same axis in the other direction must score the same way.

    This is the half a sign convention cannot express. Whatever single direction were
    declared, one of these two tests would fail.
    """
    df = _frame([1.0, 1.4, 2.0, 3.1, 4.5])
    row = _row(df)
    assert row["rho"] == pytest.approx(1.0)
    assert row["monotone_fraction"] == pytest.approx(1.0)


def test_the_reported_value_is_still_the_raw_ratio():
    """The orientation is internal to the ranking; the number a reader sees is unchanged."""
    df = _frame([1.0, 0.8, 0.55, 0.35, 0.2])
    out = summarise_axes(df)
    row = out[out["degradation"] == "spread_inflate"].iloc[0]
    # Whatever summary columns carry the metric's own value, none of them may have been
    # replaced by a distance: the clean value is the ratio 1.0, not 0.0.
    assert row["value_clean"] == pytest.approx(1.0)


def test_a_metric_without_a_target_is_untouched():
    """The ordinary error case, with no target, is ranked by the raw value."""
    df = _frame([0.0, 0.2, 0.5, 0.9, 1.6], metric="crps", target=None)
    row = _row(df)
    assert row["rho"] == pytest.approx(1.0)
    assert row["monotone_fraction"] == pytest.approx(1.0)


def test_a_non_monotone_excursion_is_still_caught():
    """The transform must not launder a genuinely disordered axis into a clean one.

    Here the ratio jumps past the target and back, so its distance from the target is not
    monotone either, and the statistics must say so.
    """
    df = _frame([1.0, 0.5, 1.05, 0.4, 1.0])
    row = _row(df)
    assert row["rho"] < 0.9
    assert row["monotone_fraction"] < 1.0


def test_a_value_at_or_below_zero_does_not_break_the_ranking():
    """A collapsed ensemble reads exactly zero, which a log-ratio cannot take.

    Zero is a real, reachable value of this metric -- the ensemble has no spread at all --
    so it must be ranked as the worst point on the axis rather than dropped or turned
    into a NaN that silently shrinks the sample.
    """
    df = _frame([1.0, 0.6, 0.3, 0.1, 0.0])
    row = _row(df)
    assert np.isfinite(row["rho"])
    assert row["rho"] == pytest.approx(1.0)


def test_response_statistics_run_on_the_distance_from_the_target():
    """Onset and resolution are read on |log(value / target)|, the scale the ordering runs on."""
    df = _frame([1.0, 1.2, 1.5, 2.0, 3.0])
    row = summarise_axes(add_damage(df, normalisation(df)), norm=normalisation(df),
                         n_bootstrap=0).iloc[0]
    assert row["elasticity"] > 0, "the distance from calibration rises along the ladder"
    assert row["response_shape"] != "" and np.isfinite(row["severity_resolution"])
