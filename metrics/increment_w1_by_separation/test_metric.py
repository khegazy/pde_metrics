"""Tests for the increment-W1 curve over separations and the number registered for it.

The registry-wide contract -- zero on identical fields, one finite float, dtype stability,
monotonicity under blur, a curve with one value per fixed coordinate, zero curve on identical
fields, the same number from the cached curve -- lives in ``tests/test_metric_contract.py``.
What is tested here is the worked example printed in the card, the identity with
``increment_w1`` at one cell, and the two closed-form properties the card states.

Every expected value is derived in the docstring beside it rather than copied from a run.
"""

from __future__ import annotations

import numpy as np
import pytest

from metrics.increment_w1.metric import increment_w1
from tests.conftest import alternating_field, step_field

from .metric import increment_w1_by_separation, increment_w1_curve, mean_absolute_increment


def test_worked_example_from_the_card():
    """The 4x4 pair in the card's Intuition section: a curve of 0.25 and 0.25, and a number of 1.

    The separations are 1 and 2 cells (up to half of 4). Down each column the reference reads
    0, 1, 1, 1 and the candidate 0, 1, 0, 1. At one cell the reference's increments are
    +1, 0, 0, -1 and the candidate's +1, -1, +1, -1, so the x-axis distance is 0.5 (the
    worked example of ``increment_w1``). At two cells the reference's are +1, 0, -1, 0 and
    the candidate's are all 0: sorted, eight of the sixteen pairs differ by 1, so the x-axis
    distance is again 0.5. Across each row both fields are constant, so the y axis contributes
    0 at both separations, and the curve averages the axes: 0.25 at each separation.

    The reference's mean absolute increment is 0.5 along x at both separations and 0 along y,
    0.25 averaged. Each separation's ratio is then 0.25 / 0.25 = 1, and their mean is 1.
    """
    separations, curve = increment_w1_curve(step_field(), alternating_field())
    assert separations.tolist() == [1, 2]
    assert curve == pytest.approx([0.25, 0.25])
    assert mean_absolute_increment(step_field(), separations) == pytest.approx([0.25, 0.25])
    assert increment_w1_by_separation(step_field(), alternating_field()) == pytest.approx(1.0)


def test_the_one_cell_value_is_increment_w1_itself():
    """At one cell the curve is ``increment_w1``, exactly: the same function computes both."""
    rng = np.random.default_rng(4)
    reference, candidate = rng.standard_normal((2, 2, 32, 16))
    separations, curve = increment_w1_curve(reference, candidate)
    assert separations[0] == 1
    assert curve[0] == increment_w1(reference, candidate)


@pytest.mark.parametrize("factor", [0.5, 2.0, 3.0])
def test_a_scaled_candidate_scores_the_size_of_its_scale_error(factor: float):
    """A candidate ``c`` times the reference scores ``|c - 1|`` at every separation.

    Sorting commutes with multiplication by a positive constant, so each sorted increment
    ``d`` is paired with ``c d`` and the distance is the mean of ``|c - 1| |d|``: exactly
    ``|c - 1|`` times the reference's mean absolute increment, which the normalisation divides
    out. The registered number is therefore ``|c - 1|``, whatever the field.
    """
    reference = np.random.default_rng(5).standard_normal((1, 32, 16))
    assert increment_w1_by_separation(reference, factor * reference) == pytest.approx(
        abs(factor - 1.0), rel=1e-12)


def test_a_separation_with_no_reference_increments_is_zero_or_infinite():
    """Where the reference has no increments at all, a candidate with none adds 0 and one with
    any adds an infinite term: nothing in the reference sets a scale for a departure there."""
    flat = np.zeros((1, 4, 4))
    assert increment_w1_by_separation(flat, flat) == 0.0
    assert increment_w1_by_separation(flat, alternating_field()) == np.inf
