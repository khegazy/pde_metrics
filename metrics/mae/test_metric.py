"""Tests specific to mean absolute error.

The contract every metric satisfies -- zero on identical fields, symmetry, the pointwise
map reducing to the scalar -- is checked over the whole registry in
``tests/test_metric_contract.py`` and is not repeated here. So are the properties MAE
shares with MSE: the two-lobed error map of a displaced feature, the blindness to where an
error sits, and the power of the displacement each one responds with.

What is tested here is what the card claims: the worked example in its Intuition section.
"""

from __future__ import annotations

from tests.conftest import SQUARE_HALF_AMPLITUDE, SQUARE_REFERENCE, SQUARE_SHIFTED

from .metric import mae


def test_worked_example_from_the_card():
    """The two numbers quoted in the card's Intuition section.

    Four of sixteen cells differ by one when the feature moves, so the mean absolute
    error is 4/16. Four cells differ by a half when the amplitude is halved, so it is
    4*0.5/16. A one-cell shift therefore costs twice a halved amplitude, where MSE gives
    four times: both metrics prefer the damped candidate to the displaced one, and they
    disagree by how much -- that factor is the whole practical difference between them.
    """
    assert mae(SQUARE_REFERENCE, SQUARE_SHIFTED) == 0.25
    assert mae(SQUARE_REFERENCE, SQUARE_HALF_AMPLITUDE) == 0.125
