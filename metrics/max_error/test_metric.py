"""Tests specific to the maximum absolute error.

The contract every metric satisfies -- zero on identical fields, symmetry, the per-cell map
reducing to the scalar under the declared ``max`` reduction -- is checked over the whole
registry in ``tests/test_metric_contract.py`` and is not repeated here.

What is tested here is what the card claims: the worked example in its Intuition section,
that a single bad cell is reported at full size where the mean dilutes it, that a displaced
sharp feature costs its full height whatever the displacement, and that channels are pooled.
"""

from __future__ import annotations

import numpy as np

from metrics.mae.metric import mae
from tests.conftest import SQUARE_HALF_AMPLITUDE, SQUARE_REFERENCE, SQUARE_SHIFTED

from .metric import max_error


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


def test_a_displaced_jump_costs_its_full_height_at_any_displacement():
    """The double penalty in its extreme form, the first pitfall on the card.

    The unit square moved by one cell and by two cells leaves, in both cases, a cell where the
    reference is 1 and the candidate 0, so both score the full height 1: the maximum error
    cannot tell a one-cell miss from a larger one once the feature has left its own cells.
    """
    two_cells = np.roll(SQUARE_REFERENCE, 2, axis=2)
    assert max_error(SQUARE_REFERENCE, SQUARE_SHIFTED) == 1.0
    assert max_error(SQUARE_REFERENCE, two_cells) == 1.0


def test_channels_are_pooled_into_one_maximum():
    """A two-channel field scores the largest error over both channels, not their average.

    The first channel is wrong by 0.25 in one cell and the second by 0.5 in another, so the
    pooled maximum is 0.5. The mean of the per-channel maxima, PDEBench's reduction, would be
    (0.25 + 0.5) / 2 = 0.375; the card records why this bundle pools instead.
    """
    reference = np.zeros((2, 4, 2))
    candidate = reference.copy()
    candidate[0, 1, 0] = 0.25
    candidate[1, 3, 1] = -0.5
    assert max_error(reference, candidate) == 0.5
