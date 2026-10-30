"""Tests specific to the maximum absolute error.

The contract every metric satisfies -- zero on identical fields, symmetry, the per-cell map
reducing to the scalar under the declared ``max`` reduction on one and two channels -- is
checked over the whole registry in ``tests/test_metric_contract.py`` and is not repeated here.

What is tested here is what the card claims: the worked example in its Intuition section,
that a single bad cell is reported at full size where the mean dilutes it, when a displaced
jump costs its full height and when it does not, that channels are pooled, and that a shape
mismatch is refused rather than broadcast.
"""

from __future__ import annotations

import numpy as np
import pytest

from metrics.mae.metric import mae
from tests.conftest import SQUARE_HALF_AMPLITUDE, SQUARE_REFERENCE, SQUARE_SHIFTED

from .metric import max_error, max_error_map


def test_worked_example_from_the_card():
    """The numbers quoted in the card's Intuition section.

    Moving the unit square by one cell leaves cells that differ by the full height 1, so the
    maximum error is 1. Halving the square's height leaves four cells that differ by 0.5, so
    it is 0.5. A cell that should be 0 but is 1 (a spike in one corner) is also 1, while the
    mean absolute error charges the same spike 1/16 = 0.0625.
    """
    spike = SQUARE_REFERENCE.copy()
    spike[0, 0, 0] = 1.0
    assert max_error(SQUARE_REFERENCE, SQUARE_SHIFTED) == 1.0
    assert max_error(SQUARE_REFERENCE, SQUARE_HALF_AMPLITUDE) == 0.5
    assert max_error(SQUARE_REFERENCE, spike) == 1.0
    assert mae(SQUARE_REFERENCE, spike) == 0.0625


def test_a_jump_on_a_cell_face_costs_its_full_height_at_every_shift():
    """The double penalty in its extreme form, the first pitfall on the card.

    A plateau of height 1, two cells wide, between constant zeros, with both edges on cell
    faces. Moved by one, two or three cells (never far enough to wrap round the eight-cell
    row), it always leaves a cell where the reference is 1 and the candidate 0, so every shift
    scores the full height 1: the maximum cannot tell a one-cell miss from a larger one.
    """
    reference = np.array([[[0, 0, 1, 1, 0, 0, 0, 0]]], dtype=float)
    for shift in (1, 2, 3):
        assert max_error(reference, np.roll(reference, shift, axis=2)) == 1.0


def test_a_jump_inside_a_cell_costs_half_its_height_at_a_one_cell_shift():
    """The full-height rule needs the jump on a cell face; after averaging onto cells it fails.

    A step from 0 to 1 whose face sits in the middle of the fourth cell, which therefore holds
    the cell average 0.5. Moved by one cell, every cell differs by 0 or 0.5, so the maximum is
    0.5, half the jump. Moved by two cells, the fifth cell is 1 in the reference and 0 in the
    candidate, so the maximum reaches the full height 1.
    """
    reference = np.array([[[0, 0, 0, 0.5, 1, 1, 1, 1]]])
    one_cell = np.array([[[0, 0, 0, 0, 0.5, 1, 1, 1]]])
    two_cells = np.array([[[0, 0, 0, 0, 0, 0.5, 1, 1]]])
    assert max_error(reference, one_cell) == 0.5
    assert max_error(reference, two_cells) == 1.0


def test_channels_are_pooled_into_one_maximum():
    """A two-channel field scores the largest error over both channels, not their average.

    The first channel is wrong by 0.25 in one cell and the second by 0.5 in another, so the
    pooled maximum is 0.5. The mean of the per-channel maxima, PDEBench's reduction, would be
    (0.25 + 0.5) / 2 = 0.375; the card records why this bundle pools instead. The map holds
    0.25 and 0.5 in those two cells, the largest over channels, not a channel sum.
    """
    reference = np.zeros((2, 4, 2))
    candidate = reference.copy()
    candidate[0, 1, 0] = 0.25
    candidate[1, 3, 1] = -0.5
    assert max_error(reference, candidate) == 0.5
    expected_map = np.zeros((4, 2))
    expected_map[1, 0] = 0.25
    expected_map[3, 1] = 0.5
    np.testing.assert_array_equal(max_error_map(reference, candidate), expected_map)


@pytest.mark.parametrize("function", [max_error, max_error_map])
def test_a_shape_mismatch_that_numpy_would_broadcast_is_refused(function):
    """One channel against two would broadcast to a plausible number; it must raise instead.

    The contract test's mismatch (16 by 8 against 16 by 10) cannot broadcast, so it does not
    cover this case.
    """
    with pytest.raises(ValueError, match="matching shapes"):
        function(np.zeros((1, 8, 8)), np.ones((2, 8, 8)))
