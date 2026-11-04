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

from fmeval.analysis import (
    FDR_LEVEL,
    FURTHEST_FROM_TARGET,
    GROUP_KEYS,
    _oriented,
    add_damage,
    normalisation,
    report_card,
    summarise_axes,
)
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
    """Onset and resolution are read on the distance from the target, the scale the ordering
    runs on."""
    df = _frame([1.0, 1.2, 1.5, 2.0, 3.0])
    row = summarise_axes(add_damage(df, normalisation(df)), norm=normalisation(df),
                         n_bootstrap=0).iloc[0]
    assert row["elasticity"] > 0, "the distance from calibration rises along the ladder"
    assert row["response_shape"] != "" and np.isfinite(row["severity_resolution"])


# --- reading a target metric: direction, damage, blindness and zeros --------------------------


def test_direction_records_which_way_the_raw_value_moved():
    """The ordering reads the distance from the target on both sides alike, so `direction` is free
    to say which way the reported value went: a ratio that falls reads -1, one that rises +1,
    and both are equally well ordered."""
    falls = _row(_frame([1.0, 0.8, 0.55, 0.35, 0.2]))
    rises = _row(_frame([1.0, 1.4, 2.0, 3.1, 4.5]))
    assert (falls["direction"], rises["direction"]) == (-1, 1)
    assert falls["rho"] == pytest.approx(1.0) and rises["rho"] == pytest.approx(1.0)


def test_distance_from_the_target_is_symmetric_bounded_and_ordered_as_the_log_ratio():
    """q(v) = |v - t| / (v + t) = tanh(|ln(v / t)| / 2): half and twice the target are equally
    far, zero and infinity are furthest, and the order is that of |ln(v / t)|."""
    v = pd.Series([0.5, 2.0, 0.0, np.inf, 1.0, 0.1, 3.0, np.nan])
    q = _oriented(v, 1, 1.0).to_numpy()
    assert q[0] == pytest.approx(q[1]) == pytest.approx(1 / 3)
    assert q[2] == q[3] == FURTHEST_FROM_TARGET and q[4] == 0.0 and np.isnan(q[7])
    finite = v.iloc[[0, 4, 5, 6]].to_numpy()
    assert np.array_equal(np.argsort(q[[0, 4, 5, 6]]), np.argsort(np.abs(np.log(finite))))
    assert np.allclose(q[[0, 4, 5, 6]], np.tanh(np.abs(np.log(finite)) / 2))


def test_damage_is_zero_at_the_target_and_positive_on_both_sides_of_it():
    """The anchor sits on the collapsed side (an ensemble replaced by its mean has no spread), and
    inflation must still read positive damage, equal to the deflation that is as far off."""
    df = make_frame(metric="spread_skill", reference=1.0, n_frames=6,
                    axes={"spread_inflate": [2.0, 4.0], "spread_deflate": [0.5, 0.25],
                          "mean_field": [0.0]})
    df["target_value"] = 1.0
    norm = normalisation(df)
    assert norm.iloc[0]["span"] == pytest.approx(FURTHEST_FROM_TARGET)
    damage = add_damage(df, norm).groupby(["degradation", "level"])["damage"].median()
    assert damage[("identity", 0)] == 0.0
    assert damage[("mean_field", 1)] == pytest.approx(1.0)
    for level in (1, 2):
        assert damage[("spread_inflate", level)] > 0
        assert damage[("spread_inflate", level)] == pytest.approx(
            damage[("spread_deflate", level)])
    assert damage[("spread_inflate", 2)] > damage[("spread_inflate", 1)]


def test_an_axis_on_which_the_value_stays_on_the_target_is_listed_blind():
    """A translation leaves an extreme-increment frequency ratio at exactly 1, its target, so its
    damage is provably zero; the blur that removes the extremes is not."""
    df = make_frame(metric="tail_exceedance", reference=1.0, n_frames=20,
                    axes={"translate_x": [1.0, 1.0, 1.0], "gaussian_blur": [0.6, 0.3, 0.1],
                          "mean_field": [0.0]})
    df["target_value"] = 1.0
    norm = normalisation(df)
    axes = summarise_axes(add_damage(df, norm), norm=norm, n_bootstrap=50)
    by_axis = axes.set_index("degradation")
    assert by_axis.loc["translate_x", "damage_max_ucb"] == pytest.approx(0.0)
    assert by_axis.loc["translate_x", "blindness_q"] < FDR_LEVEL
    assert by_axis.loc["gaussian_blur", "blindness_q"] == pytest.approx(1.0)
    card = report_card(axes, pd.DataFrame(columns=GROUP_KEYS), norm)
    assert card.iloc[0]["blind_axes"] == "translate_x"


def test_a_frame_that_reaches_zero_and_stays_there_is_ordered():
    """(0.3, 0, 0, 0): a blur removes every extreme increment by the second strength. Zero is the
    furthest point from the target, so the frame has a rank correlation (not NaN) and is in
    order; the tie at the furthest point is not a step backwards."""
    row = _row(_frame([1.0, 0.3, 0.0, 0.0, 0.0]))
    assert np.isfinite(row["rho"]) and row["rho"] > 0
    assert row["monotone_fraction"] == pytest.approx(1.0)


def test_a_tie_short_of_the_furthest_point_is_still_out_of_order():
    """Only the furthest point excuses a tie: a ratio stuck at 0.5 over two strengths is not
    ordered."""
    row = _row(_frame([1.0, 0.8, 0.5, 0.5, 0.2]))
    assert row["monotone_fraction"] == pytest.approx(0.0)


def test_a_target_that_is_not_positive_is_refused():
    """The distance from the target is a ratio, so a zero or negative target has no scale."""
    df = _frame([1.0, 0.8, 0.5, 0.3, 0.2])
    df["target_value"] = 0.0
    with pytest.raises(ValueError, match="positive target"):
        normalisation(df)
