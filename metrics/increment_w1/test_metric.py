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

from metrics.increment_flatness.metric import increments
from tests.conftest import alternating_field, make_ctx, oriented_velocity_field, step_field

from .metric import increment_w1, increment_w1_transverse, sample_w1


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
    step, alternating = step_field(), alternating_field()
    for axis, expected in ((-2, 0.5), (-1, 0.0)):
        assert sample_w1(increments(step[0], axis),
                         increments(alternating[0], axis)) == pytest.approx(expected)
    assert increment_w1(step, alternating, ctx=make_ctx(step)) == pytest.approx(0.25)


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
        moved = np.roll(field, shift, axis=axis)
        assert increment_w1(field, moved, ctx=make_ctx(field)) == pytest.approx(0.0)


def test_a_constant_offset_is_invisible():
    """Adding a constant cancels in the difference that defines an increment.

    Shared with ``h_minus_one``, and for the same practical reason worth stating: a
    surrogate that has drifted in its mean while keeping its structure is invisible here.
    """
    rng = np.random.default_rng(1)
    field = rng.standard_normal((1, 16, 8))
    assert increment_w1(field, field + 12.5, ctx=make_ctx(field)) == pytest.approx(0.0)


def test_doubling_the_field_costs_the_mean_absolute_increment():
    """A candidate scaled by two scores the mean absolute increment of the reference.

    Sorting commutes with multiplication by a positive constant, so matching quantiles pairs
    each sorted increment ``d`` with ``2d`` and the distance per axis is the mean of
    ``|2d - d| = |d|``. For the step field that is 2/4 = 0.5 along x and 0 along y, giving
    0.25 -- a closed-form value that does not depend on the sort order being guessed right.
    """
    step = step_field()
    assert increment_w1(step, 2.0 * step, ctx=make_ctx(step)) == pytest.approx(0.25)


def test_a_field_with_wider_increments_is_further_away():
    """Widening the increment distribution increases the distance monotonically.

    Amplifying a field stretches its increment distribution about zero, and the transport
    cost of that stretch grows with the factor. This is the response that makes the metric
    usable at all, as distinct from the invariances above.
    """
    rng = np.random.default_rng(2)
    field = rng.standard_normal((1, 16, 8))
    values = [increment_w1(field, factor * field, ctx=make_ctx(field))
              for factor in (1.0, 1.5, 2.0, 3.0)]
    assert values == sorted(values)
    assert values[0] == pytest.approx(0.0)


def test_velocity_is_scored_on_its_longitudinal_increments_with_the_transverse_beside():
    """``oriented_velocity_field`` against a zero field: 0.0625 longitudinal, 0.125 transverse.

    Against a field with no increments the transport distance of a pair is the mean absolute
    increment of the reference. Longitudinally, u_x along x is a lone step, two non-zero unit
    increments in a column of 16, 0.125, and u_y along y is constant, 0: the number is 0.0625.
    Transversely, u_x along y is constant, 0, and u_y along x is a square wave of period 8, four
    unit increments in 16, 0.25: the companion holds 0.125 at the registered one-cell
    separation. Pooling all four pairs, as before velocity had an orientation, gives 0.09375.
    """
    field, zero = oriented_velocity_field(), np.zeros((2, 16, 8))
    ctx = make_ctx(field, field="velocity")
    assert increment_w1(field, zero, ctx=ctx) == pytest.approx(0.0625)
    separations, transverse = increment_w1_transverse(field, zero, ctx=ctx)
    assert separations.tolist() == [1] and transverse == pytest.approx([0.125])
    assert increment_w1(field, zero, ctx=make_ctx(field, field="density")) == pytest.approx(0.09375)
    assert len(increment_w1_transverse(field[:1], zero[:1], ctx=make_ctx(field[:1]))[0]) == 0
