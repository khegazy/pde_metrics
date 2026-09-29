"""Tests for the increment-PDF 1-Wasserstein metric.

The registry-wide contract -- symmetry, zero on identical fields, dtype stability,
monotonicity under blur -- lives in ``tests/test_metric_contract.py``. What is tested here
is the worked example printed in the card and the two invariances that are the whole reason
this metric is in the repository: it does not see where structure is, and it does not see a
constant offset.

Every expected value is derived in the docstring beside it rather than copied from a run.
"""

from __future__ import annotations

import numpy as np
import pytest

from .metric import axis_w1, increment_w1


def _step() -> np.ndarray:
    """Zero on the first row, one on the rest: one jump down each column."""
    out = np.ones((1, 4, 4))
    out[0, 0, :] = 0.0
    return out


def _alternating() -> np.ndarray:
    """Zero and one on alternate rows: a jump at every step down each column."""
    out = np.zeros((1, 4, 4))
    out[0, 1::2, :] = 1.0
    return out


def test_worked_example_from_the_card():
    """The 4x4 pair in the card's Intuition section scores 0.25.

    Down each column the reference increments are ``+1, 0, 0, -1`` and the candidate's are
    ``+1, -1, +1, -1``. Pooled over the four columns, the reference's sorted sample is four
    ``-1``, eight ``0`` and four ``+1``; the candidate's is eight ``-1`` and eight ``+1``.
    Matching them in sorted order leaves the first four and last four pairs equal and the
    middle eight differing by exactly 1, so the x-axis distance is 8/16 = 0.5.

    Across each row both fields are constant, so their y-increments are identically zero,
    the two degenerate distributions coincide, and that axis contributes 0. The reported
    value averages the two axes: (0.5 + 0) / 2 = 0.25.
    """
    assert axis_w1(_step()[0], _alternating()[0], axis=-2) == pytest.approx(0.5)
    assert axis_w1(_step()[0], _alternating()[0], axis=-1) == pytest.approx(0.0)
    assert increment_w1(_step(), _alternating()) == pytest.approx(0.25)


@pytest.mark.parametrize("shift", [1, 3, 7])
def test_a_translated_field_is_at_distance_zero(shift: int):
    """Rolling the field leaves every increment distribution exactly unchanged.

    This is the metric's defining property and the reason it is orthogonal to a pointwise
    norm: it compares the statistics of the increments and never asks where they occurred,
    so a prediction that is right everywhere but in the wrong place costs nothing at all.
    It is also, stated the other way round, the metric's blind spot.
    """
    rng = np.random.default_rng(0)
    field = rng.standard_normal((1, 16, 8))
    for axis in (-2, -1):
        assert increment_w1(field, np.roll(field, shift, axis=axis)) == pytest.approx(0.0)


def test_a_constant_offset_is_invisible():
    """Adding a constant cancels in the difference that defines an increment.

    Shared with ``h_minus_one``, and for the same practical reason worth stating: a
    surrogate that has drifted in its mean while keeping its structure is invisible here.
    """
    rng = np.random.default_rng(1)
    field = rng.standard_normal((1, 16, 8))
    assert increment_w1(field, field + 12.5) == pytest.approx(0.0)


def test_doubling_the_field_costs_the_mean_absolute_increment():
    """A candidate scaled by two scores the mean absolute increment of the reference.

    Sorting commutes with multiplication by a positive constant, so matching quantiles pairs
    each sorted increment ``d`` with ``2d`` and the distance per axis is the mean of
    ``|2d - d| = |d|``. For the step field that is 2/4 = 0.5 along x and 0 along y, giving
    0.25 -- a closed-form value that does not depend on the sort order being guessed right.
    """
    assert increment_w1(_step(), 2.0 * _step()) == pytest.approx(0.25)


def test_a_field_with_wider_increments_is_further_away():
    """Widening the increment distribution increases the distance monotonically.

    Amplifying a field stretches its increment distribution about zero, and the transport
    cost of that stretch grows with the factor. This is the response that makes the metric
    usable at all, as distinct from the invariances above.
    """
    rng = np.random.default_rng(2)
    field = rng.standard_normal((1, 16, 8))
    values = [increment_w1(field, factor * field) for factor in (1.0, 1.5, 2.0, 3.0)]
    assert values == sorted(values)
    assert values[0] == pytest.approx(0.0)
