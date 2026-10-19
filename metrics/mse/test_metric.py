"""Tests specific to mean squared error.

The contract every metric must satisfy -- zero on identical fields, symmetry, the
pointwise map reducing to the scalar -- is checked over the whole registry in
``tests/test_metric_contract.py`` and is not repeated here. So are the properties MSE
shares with MAE: the two-lobed error map of a displaced feature, the blindness to where an
error sits, and the quadratic response to a small displacement that makes MSE tolerant of
small shifts and severe about larger ones.

What is tested here is the behaviour the card claims: the worked example printed in the
card's Intuition section. Keeping it in a test is what stops the prose drifting away from
the code.
"""

from __future__ import annotations

from tests.conftest import SQUARE_HALF_AMPLITUDE, SQUARE_REFERENCE, SQUARE_SHIFTED

from .metric import mse


def test_worked_example_from_the_card():
    """The two numbers quoted in the card's Intuition section.

    Four of sixteen cells differ by one when the feature moves, so the mean squared error
    is 4/16. Four cells differ by a half when the amplitude is halved, so it is 4*0.25/16.

    The ratio is the claim the card makes about what MSE prioritises. This is the double
    penalty in its smallest form: the displaced candidate has the feature's shape and
    amplitude exactly right and is punished four times as hard as one that keeps the
    position and gets the amplitude badly wrong.
    """
    assert mse(SQUARE_REFERENCE, SQUARE_SHIFTED) == 0.25
    assert mse(SQUARE_REFERENCE, SQUARE_HALF_AMPLITUDE) == 0.0625
