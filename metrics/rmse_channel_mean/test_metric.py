"""Tests specific to the per-channel root mean squared error.

The registry-wide contract is checked in ``tests/test_metric_contract.py``. What is tested here
is what the card claims: the two-channel worked example in its Intuition section, that the value
equals ``rmse`` on one channel, and the bounds that tie it to ``rmse`` on several channels.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import SQUARE_REFERENCE, SQUARE_SHIFTED, synthetic_field

from ..rmse.metric import rmse
from .metric import rmse_channel_mean


def test_worked_example_from_the_card():
    """Two channels: the square moved one cell in the first, predicted exactly in the second.

    The first channel's RMSE is sqrt(4/16) = 0.5 and the second's is 0, so their mean is 0.25.
    ``rmse`` pools the 32 entries, four of them wrong by one: sqrt(4/32) = 0.3536.
    """
    reference = np.concatenate([SQUARE_REFERENCE, SQUARE_REFERENCE])
    candidate = np.concatenate([SQUARE_SHIFTED, SQUARE_REFERENCE])
    assert rmse_channel_mean(reference, candidate) == 0.25
    assert rmse(reference, candidate) == pytest.approx(np.sqrt(0.125), rel=1e-15)


def test_it_is_rmse_on_one_channel():
    """On a one-channel field there is nothing to average over: the two bundles agree."""
    reference = synthetic_field((16, 8), 1, seed=1)
    candidate = synthetic_field((16, 8), 1, seed=2)
    assert rmse_channel_mean(reference, candidate) == pytest.approx(
        rmse(reference, candidate), rel=1e-14)


def test_it_lies_between_rmse_over_root_c_and_rmse():
    """A mean of square roots is at most the square root of the mean (Jensen), and at least
    the square root of the sum over C. Equality at the top needs every channel equally wrong;
    at the bottom, all the error in one channel."""
    reference = synthetic_field((16, 8), 3, seed=1)
    candidate = synthetic_field((16, 8), 3, seed=2)
    candidate[1] = reference[1]
    pooled = rmse(reference, candidate)
    value = rmse_channel_mean(reference, candidate)
    assert pooled / np.sqrt(3) <= value <= pooled


def test_mismatched_shapes_are_refused_even_when_they_broadcast():
    """One channel against two would broadcast to a plausible number; it raises instead."""
    with pytest.raises(ValueError, match="matching shapes"):
        rmse_channel_mean(np.ones((1, 4, 2)), np.zeros((2, 4, 2)))
