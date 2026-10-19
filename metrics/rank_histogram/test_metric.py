"""Rank histogram reliability index: is the ensemble the right shape?

The scalar reported here is a summary of a histogram, so the tests fall into two groups:
those that pin the arithmetic on a hand-checkable case, and those that check the summary
responds the way the histogram's shape is known to respond -- rising for an ensemble that
is too narrow, too wide, or off-centre, and near zero only when the truth is genuinely
exchangeable with the members.

The calibrated-null test draws independent fields with a fixed seed, so it is
deterministic in practice, but its threshold is loose enough that it tests the metric
rather than the seed. Every test passes the context the pipeline would build for a density
field, whose generator breaks ties.
"""

from __future__ import annotations

import numpy as np
import pytest

from degradations._shared.ensemble import scale_spread
from metrics.ensemble_mean_rmse.metric import ensemble_mean_rmse
from metrics.rank_histogram.metric import rank_histogram, reliability_index
from tests.conftest import exchangeable_ensemble, make_ctx

# --- the summary statistic itself ----------------------------------------------------


def test_reliability_index_is_zero_for_a_flat_histogram():
    counts = np.full(5, 20)
    assert reliability_index(counts) == pytest.approx(0.0)


def test_reliability_index_is_maximal_when_one_bin_takes_everything():
    """All mass in one bin of N+1 gives 2N/(N+1), the largest value attainable."""
    for n_bins in (3, 5, 9):
        counts = np.zeros(n_bins, dtype=int)
        counts[0] = 100
        n_members = n_bins - 1
        assert reliability_index(counts) == pytest.approx(
            2 * n_members / (n_members + 1)
        )


def test_reliability_index_worked_example():
    """Four bins holding 40, 20, 20, 20 of 100 draws.

    Frequencies are 0.4, 0.2, 0.2, 0.2 against a uniform 0.25, so the absolute
    deviations are 0.15, 0.05, 0.05, 0.05 and the index is 0.30.
    """
    assert reliability_index(np.array([40, 20, 20, 20])) == pytest.approx(0.30)


# --- the metric on hand-checkable ensembles ------------------------------------------


def test_worked_example_from_the_card():
    """Three members and four cells, arranged so the reference takes each rank once.

    One draw in each of the four bins is exactly uniform, so the index is zero.
    """
    reference = np.array([0.0, 0.0, 0.0, 0.0]).reshape(1, 4)
    members = np.array(
        [
            [1.0, -1.0, -1.0, -1.0],   # ref below all three  -> rank 0
            [2.0, 1.0, -2.0, -2.0],    # ref above one        -> rank 1
            [3.0, 2.0, 1.0, -3.0],     # ref above two        -> rank 2
        ]
    ).reshape(3, 1, 4)                  # ref above all three  -> rank 3
    ctx = make_ctx(reference, field="density", label="test")
    assert rank_histogram(reference, members, ctx=ctx) == pytest.approx(0.0)


def test_a_reference_below_every_member_fills_the_first_bin():
    """Maximal bias: every draw lands in one bin, so the index is at its bound."""
    reference = np.zeros((1, 8, 8))
    members = np.ones((4, 1, 8, 8))
    ctx = make_ctx(reference, field="density", label="test")
    assert rank_histogram(reference, members, ctx=ctx) == pytest.approx(2 * 4 / 5)


def test_a_reference_above_every_member_fills_the_last_bin():
    reference = np.full((1, 8, 8), 10.0)
    members = np.zeros((4, 1, 8, 8))
    ctx = make_ctx(reference, field="density", label="test")
    assert rank_histogram(reference, members, ctx=ctx) == pytest.approx(2 * 4 / 5)


# --- calibration behaviour -----------------------------------------------------------


def test_is_near_zero_for_an_exchangeable_ensemble():
    """The calibrated null: truth drawn from the same process as the members.

    With 64 cells per bin on average the sampling floor is around 0.1, so the assertion
    is loose in absolute terms but far below what any miscalibration below produces.
    """
    reference, members = exchangeable_ensemble(0, (1, 48, 48), 8)
    ctx = make_ctx(reference, field="density", label="test")
    assert rank_histogram(reference, members, ctx=ctx) < 0.12


def test_underdispersion_raises_the_index():
    """Too-narrow members push the truth to the tails: a U-shaped histogram."""
    reference, members = exchangeable_ensemble(1, (1, 48, 48), 8)
    narrow = scale_spread(members, 0.2)
    ctx = make_ctx(reference, field="density", label="test")
    assert rank_histogram(reference, narrow, ctx=ctx) > 0.5


def test_overdispersion_raises_the_index():
    """Too-wide members trap the truth in the middle: a dome-shaped histogram."""
    reference, members = exchangeable_ensemble(2, (1, 48, 48), 8)
    wide = scale_spread(members, 5.0)
    ctx = make_ctx(reference, field="density", label="test")
    assert rank_histogram(reference, wide, ctx=ctx) > 0.3


def test_detects_miscalibration_that_the_ensemble_mean_cannot_see():
    """The reason this metric is on the panel beside ensemble_mean_rmse.

    Scaling the members about their own mean leaves the ensemble mean untouched, so a
    mean-based score is unchanged, while the rank histogram registers it immediately.
    """
    reference, members = exchangeable_ensemble(4, (1, 48, 48), 8)
    narrow = scale_spread(members, 0.2)

    assert ensemble_mean_rmse(reference, narrow) == pytest.approx(
        ensemble_mean_rmse(reference, members), rel=1e-12
    )
    narrow_index = rank_histogram(reference, narrow,
                                  ctx=make_ctx(reference, field="density", label="test"))
    calibrated_index = rank_histogram(reference, members,
                                      ctx=make_ctx(reference, field="density", label="test"))
    assert narrow_index > 4 * calibrated_index


# --- ties, determinism and shape handling --------------------------------------------


def test_ties_are_broken_at_random_so_a_discrete_calibrated_forecast_stays_flat():
    """A collapsed ensemble equal to the reference is all ties, spread evenly over the ranks.

    Randomising among tied ranks is the standard treatment (Hamill 2001): it keeps the
    histogram uniform for a genuinely calibrated but discretised forecast, where always
    taking the lowest rank -- or any one fixed rank -- would put every draw in a single bin
    and score the bound 2N/(N+1) = 1.6. With 1024 cells in five bins the random draw's
    sampling floor is about 0.05.
    """
    reference = np.zeros((1, 32, 32))
    members = np.zeros((4, 1, 32, 32))
    ctx = make_ctx(reference, field="density", label="test")
    assert rank_histogram(reference, members, ctx=ctx) < 0.15


def test_tie_breaking_is_deterministic_for_a_given_seed():
    """The same seed reproduces the tie assignment; a different seed draws a new one.

    Members drawn from {-1, 0, 1} against a zero reference tie at most cells, so the seeded
    branch decides most ranks and two seeds give different histograms.
    """
    reference = np.zeros((1, 16, 16))
    members = np.random.default_rng(5).integers(-1, 2, (6, 1, 16, 16)).astype(float)

    def score(seed: int) -> float:
        ctx = make_ctx(reference, field="density", seed=seed, label="test")
        return rank_histogram(reference, members, ctx=ctx)

    assert score(11) == score(11)
    assert score(11) != score(12)


def test_without_a_context_ties_take_the_midpoint_rank():
    """The ctx is optional; without one, a tie takes the middle of the ranks it spans.

    Four members and four cells against a zero reference:

    * all four members tie: ranks 0..4, midpoint 4 // 2 = 2;
    * members -1, -1, 1, 1: no tie, rank 2;
    * members -1, 0, 0, 1: one below and two tied, rank 1 + 2 // 2 = 2;
    * members all -1: rank 4.

    Three draws in bin 2 and one in bin 4 of five give frequencies 0, 0, 0.75, 0, 0.25
    against a uniform 0.2, so the index is 0.2 + 0.2 + 0.55 + 0.2 + 0.05 = 1.2. Counting
    only members strictly below would give ranks 0, 2, 1, 4 and an index of 0.4.
    """
    reference = np.zeros((1, 4))
    members = np.array([
        [0.0, -1.0, -1.0, -1.0],
        [0.0, -1.0, 0.0, -1.0],
        [0.0, 1.0, 0.0, -1.0],
        [0.0, 1.0, 1.0, -1.0],
    ]).reshape(4, 1, 4)
    assert rank_histogram(reference, members) == pytest.approx(1.2)


def test_needs_at_least_two_members():
    with pytest.raises(ValueError, match="two"):
        rank_histogram(np.zeros((1, 4, 4)), np.zeros((1, 1, 4, 4)),
                       ctx=make_ctx((4, 4), field="density", label="test"))
