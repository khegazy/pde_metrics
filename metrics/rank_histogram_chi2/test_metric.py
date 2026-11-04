"""Rank-histogram chi-square: the arithmetic on a hand-checkable case, and its null value.

The statistic is a function of the histogram ``rank_histogram`` computes, so the tests pin
the formula (against a hand count and against SciPy's Pearson statistic) and the one
property that makes it a test statistic: with independent, exchangeable draws its mean is the
number of degrees of freedom, whatever the number of cells.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from degradations._shared.ensemble import scale_spread
from metrics.rank_histogram.metric import rank_histogram, rank_histogram_curve
from metrics.rank_histogram_chi2.metric import rank_histogram_chi2
from tests.conftest import exchangeable_ensemble, make_ctx

#: Two members and six cells against a zero reference, arranged so the reference takes
#: rank 0 at three cells, rank 1 at one and rank 2 at two.
WORKED_REFERENCE = np.zeros((1, 6))
WORKED_MEMBERS = np.array([
    [1.0, 1.0, 1.0, -1.0, -1.0, -1.0],
    [2.0, 2.0, 2.0, 1.0, -2.0, -2.0],
]).reshape(2, 1, 6)


def test_worked_example_from_the_card():
    """Counts 3, 1, 2 in three bins; the flat expectation is 6 / 3 = 2 per bin.

    T = (3-2)^2/2 + (1-2)^2/2 + (2-2)^2/2 = 0.5 + 0.5 + 0 = 1.0. The reliability index of the
    same histogram is |1/2 - 1/3| + |1/6 - 1/3| + 0 = 1/3.
    """
    assert rank_histogram_chi2(WORKED_REFERENCE, WORKED_MEMBERS) == pytest.approx(1.0)
    assert rank_histogram(WORKED_REFERENCE, WORKED_MEMBERS) == pytest.approx(1.0 / 3.0)


def test_equals_pearsons_statistic_on_the_counts():
    """The fraction form n K sum (f - 1/K)^2 is Pearson's statistic on the counts."""
    reference, members = exchangeable_ensemble(0, (2, 12, 10), 5)
    ctx = make_ctx(reference, field="velocity", label="test")
    _, fractions = rank_histogram_curve(reference, members, ctx=make_ctx(
        reference, field="velocity", label="test"))
    counts = np.rint(fractions * reference.size)
    assert counts.sum() == reference.size
    assert rank_histogram_chi2(reference, members, ctx=ctx) == pytest.approx(
        stats.chisquare(counts).statistic, rel=1e-12)


def test_null_mean_is_the_degrees_of_freedom():
    """Independent cells of a calibrated ensemble: T follows chi-square with N degrees of freedom.

    One draw has a standard deviation of sqrt(2N) = 4 at N = 8, so the assertion is on the
    mean of 200 draws (standard error about 0.28), with a band of more than three standard
    errors that still separates a correct 8 from a statistic off by a quarter.
    """
    values = [rank_histogram_chi2(*exchangeable_ensemble(seed, (1, 32, 32), 8))
              for seed in range(200)]
    assert 7.0 < np.mean(values) < 9.0, np.mean(values)


def test_grows_with_the_number_of_draws_at_a_fixed_shape():
    """The same miscalibration on four times the cells gives about four times the statistic,
    while the reliability index stays put: the difference between a test statistic and a
    descriptive one."""
    small = exchangeable_ensemble(1, (1, 32, 32), 8)
    large = exchangeable_ensemble(1, (1, 64, 64), 8)
    narrow_small = (small[0], scale_spread(small[1], 0.3))
    narrow_large = (large[0], scale_spread(large[1], 0.3))
    ratio = rank_histogram_chi2(*narrow_large) / rank_histogram_chi2(*narrow_small)
    assert 3.0 < ratio < 5.0, ratio
    assert rank_histogram(*narrow_large) == pytest.approx(rank_histogram(*narrow_small), rel=0.2)


def test_is_at_its_bound_when_every_draw_lands_in_one_bin():
    """All n draws in one of K bins gives n (K - 1) = n N."""
    reference = np.zeros((1, 8, 8))
    members = np.ones((4, 1, 8, 8))
    assert rank_histogram_chi2(reference, members) == pytest.approx(64 * 4)
