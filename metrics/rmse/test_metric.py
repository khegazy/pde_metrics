"""Tests specific to root mean squared error.

The registry-wide contract is checked in ``tests/test_metric_contract.py``. What is
tested here is what the card claims: the worked example in its Intuition section, which is
the square root of mean squared error's, and the consequence of that square root for the
declared reduction.
"""

from __future__ import annotations

import numpy as np

from tests.conftest import SQUARE_HALF_AMPLITUDE, SQUARE_REFERENCE, SQUARE_SHIFTED

from ..mse.metric import mse
from .metric import rmse, rmse_map


def test_worked_example_from_the_card():
    """Four of sixteen cells wrong by one gives sqrt(4/16) = 0.5; by a half, 0.25.

    These are exactly the square roots of MSE's worked example, 0.25 and 0.0625: the card's
    claim that the two orderings can never disagree, since a square root is monotone and the
    two differ in scale, never in order. A one-cell shift costs twice a halved amplitude
    here, against four times for MSE: taking the square root pulls the quadratic penalty
    back to a linear-looking ratio on these fields, which is why RMSE reads like MAE while
    ordering like MSE.
    """
    assert rmse(SQUARE_REFERENCE, SQUARE_SHIFTED) == 0.5
    assert rmse(SQUARE_REFERENCE, SQUARE_HALF_AMPLITUDE) == 0.25


def test_the_map_does_not_average_to_the_metric():
    """The reduction is sqrt_mean, and this test is why it must be declared.

    The stored per-cell map is the squared error. Averaging it gives MSE, not RMSE, so a
    consumer that assumed every map averages to its metric would be silently wrong here.
    """
    mean_of_map = rmse_map(SQUARE_REFERENCE, SQUARE_SHIFTED).mean()
    assert mean_of_map == mse(SQUARE_REFERENCE, SQUARE_SHIFTED)
    assert mean_of_map != rmse(SQUARE_REFERENCE, SQUARE_SHIFTED)
    assert np.sqrt(mean_of_map) == rmse(SQUARE_REFERENCE, SQUARE_SHIFTED)
