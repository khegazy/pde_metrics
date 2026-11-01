"""Tests for ``tail_exceedance``: the worked example, ties, the constant cases, the choice of
order statistic, the non-monotone response to blur, and the invariances the card states.

The contract tests in ``tests/test_metric_contract.py`` already check one finite float, the
target value on identical fields, shape rejection, dtype stability, the declared non-monotonicity
on the synthetic blur ladder, a fixed curve coordinate and the same number from the cached curve,
so none of that is repeated here.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from .metric import tail_exceedance, tail_exceedance_curve

#: The card's reference: a sawtooth down the rows, constant along each row (tail_index's example).
SAWTOOTH = np.array([[[0.0, 0.0, 0.0, 0.0],
                      [3.0, 3.0, 3.0, 3.0],
                      [2.0, 2.0, 2.0, 2.0],
                      [1.0, 1.0, 1.0, 1.0]]])
#: The card's first candidate: the sawtooth with its first jump cut from 3 to 2 in two columns.
CUT = np.array([[[0.0, 0.0, 0.0, 0.0],
                 [3.0, 3.0, 2.0, 2.0],
                 [2.0, 2.0, 2.0, 2.0],
                 [1.0, 1.0, 1.0, 1.0]]])


def test_worked_example_matches_the_card():
    """Cutting two of the four big jumps scores 2/4 = 0.5; tripling the field scores 16/4 = 4.

    By hand. Down each column of the sawtooth the values are 0, 3, 2, 1 and wrap back to 0, so the
    step sizes are 3, 1, 1, 1; over the four columns that is four steps of 3 and twelve of 1.
    n = 16 cells, so k = ceil(sqrt(16)) = 4 and the threshold is the fourth-largest step, 3. The
    reference has 4 steps of at least 3. Along each row the sawtooth is constant, so that
    direction's threshold is 0 and it is left out.

    The cut candidate goes 0, 2, 2, 1 down two columns, steps 2, 0, 1, 1, and keeps the sawtooth
    in the other two, so 2 of its steps reach 3: 2/4 = 0.5. The tripled candidate has steps 9 and
    3, all sixteen at least 3: 16/4 = 4.
    """
    assert tail_exceedance(SAWTOOTH, CUT) == 0.5
    assert tail_exceedance(SAWTOOTH, 3.0 * SAWTOOTH) == 4.0


def test_ties_at_the_threshold_are_all_events():
    """A reference whose steps are all 1 has 16 events at its threshold 1, and so has the sawtooth.

    By hand. Rows alternating 0 and 1 have every step down a column of size 1, so the
    fourth-largest is 1 and all sixteen steps are at least 1: the reference count is 16, not
    k = 4. Every step of the sawtooth is 1 or 3, so all sixteen reach 1 too: 16/16 = 1.
    """
    alternating = np.array([[[0.0, 0.0, 0.0, 0.0],
                             [1.0, 1.0, 1.0, 1.0],
                             [0.0, 0.0, 0.0, 0.0],
                             [1.0, 1.0, 1.0, 1.0]]])
    assert tail_exceedance(alternating, SAWTOOTH) == 1.0


def test_a_constant_candidate_scores_zero_and_a_constant_reference_nan():
    """A constant candidate has no step at all, so no event: 0/4 = 0. A constant reference has a
    threshold of 0 on every axis, so no event is defined and the value is NaN."""
    assert tail_exceedance(SAWTOOTH, np.full_like(SAWTOOTH, 2.0)) == 0.0
    assert np.isnan(tail_exceedance(np.full_like(SAWTOOTH, 2.0), SAWTOOTH))


def test_a_non_finite_field_is_refused():
    """A NaN compares false with every threshold, so it would silently lower a count."""
    x = np.random.default_rng(2).standard_normal((2, 16, 8))
    for bad in (np.nan, np.inf):
        y = x.copy()
        y[0, 3, 3] = bad
        with pytest.raises(ValueError, match="finite"):
            tail_exceedance(x, y)
        with pytest.raises(ValueError, match="finite"):
            tail_exceedance(y, x)


def test_an_independent_twin_scores_one_at_the_smallest_order():
    """At theta = 0.1 on 1024 cells (k = 2) an independent draw scores 1 on average, not 1.5.

    A periodic random walk with centred steps has exactly those steps (rolled by one) as its
    one-cell increments; centred steps sum to zero, so they are exchangeable rather than strictly
    independent, a dependence of order 1/n. Reference and candidate are drawn independently. For the
    k-th largest of n, F(X_(k)) is Beta(n - k + 1, k), so a new value reaches it with probability
    k / (n + 1) and the expected frequency bias is n / (n + 1) = 0.999. Had the threshold been
    the (k + 1)-th largest with a strict inequality, it would be n (k + 1) / ((n + 1) k) = 1.499.
    Mean over 400 seeds: 1.015 with a standard error of 0.052 (measured); the alternative convention
    measures 1.5625 on the same seeds (adversarial review, .agent/adversary/checks.out), so the
    bound 0.2 separates the two.
    """
    def walk(rng: np.random.Generator) -> np.ndarray:
        steps = rng.standard_normal(1024)
        return np.cumsum(steps - steps.mean())[None]

    values = []
    for seed in range(400):
        rng = np.random.default_rng(seed)
        thetas, curve = tail_exceedance_curve(walk(rng), walk(rng))
        values.append(curve[list(thetas).index(0.1)])
    assert abs(np.mean(values) - 1.0) < 0.2


def test_blur_can_raise_the_value_before_it_lowers_it():
    """One spike spread by a blur puts several cells above a low threshold, then none.

    A 16-cell spike of height 8 on noise of rms 0.01 (seed 0): the reference's fourth-largest step
    is a noise step, so a blurred spike's several moderate steps all exceed it until the blur is
    wide enough to flatten the spike. Measured: 1, 1, 2, 3, 3.5, 0 at sigma 0, 0.5, 1, 2, 4, 8;
    with n = 16 and k = 4 these are candidate counts of 4, 4, 8, 12, 14 and 0 over the reference's
    4. This is why the decorator declares ``monotone_under_smoothing=False``; the sequence is
    pinned so the documented numbers cannot drift from the field the test builds.
    """
    x = 0.01 * np.random.default_rng(0).standard_normal((1, 16))
    x[0, 0] += 8.0
    values = [tail_exceedance(x, x if s == 0 else gaussian_filter(x, (0, s), mode="wrap"))
              for s in (0, 0.5, 1, 2, 4, 8)]
    assert values == [1.0, 1.0, 2.0, 3.0, 3.5, 0.0], values


def test_scaling_both_fields_and_moving_the_candidate_change_nothing():
    """Scaling both fields by one constant scales every step and every threshold alike; an integer
    shift of the candidate moves its steps without changing their sizes."""
    rng = np.random.default_rng(5)
    reference, candidate = rng.standard_normal((2, 2, 16, 8))
    value = tail_exceedance(reference, candidate)
    assert tail_exceedance(7.0 * reference, 7.0 * candidate) == value
    assert tail_exceedance(reference, np.roll(candidate, (3, 2), axis=(1, 2))) == value
