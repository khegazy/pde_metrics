"""Tests specific to the per-channel maximum error.

The registry-wide contract is checked in ``tests/test_metric_contract.py``. What is tested here
is what the card claims: the two-channel worked example in its Intuition section, that the value
equals ``max_error`` on one channel, and the bounds that tie it to ``max_error`` on several.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import SQUARE_REFERENCE, SQUARE_SHIFTED, synthetic_field

from ..max_error.metric import max_error
from .metric import max_error_channel_mean


def test_worked_example_from_the_card():
    """Two channels: the square moved one cell in the first, predicted exactly in the second.

    The first channel's largest error is 1 and the second's 0, so their mean is 0.5, where
    ``max_error`` reports the single worst entry over both channels, 1.
    """
    reference = np.concatenate([SQUARE_REFERENCE, SQUARE_REFERENCE])
    candidate = np.concatenate([SQUARE_SHIFTED, SQUARE_REFERENCE])
    assert max_error_channel_mean(reference, candidate) == 0.5
    assert max_error(reference, candidate) == 1.0


def test_the_mean_of_unequal_channel_maxima():
    """The case ``max_error``'s own test sets beside its pooled value of 0.5, on a 4 x 2 grid.

    The first channel is wrong by 0.25 in one cell and the second by 0.5 in another, so the
    mean of the two maxima is (0.25 + 0.5) / 2 = 0.375.
    """
    reference = np.zeros((2, 4, 2))
    candidate = reference.copy()
    candidate[0, 1, 0] = 0.25
    candidate[1, 3, 1] = -0.5
    assert max_error_channel_mean(reference, candidate) == 0.375


def test_it_is_max_error_on_one_channel():
    """On a one-channel field there is nothing to average over: the two bundles agree."""
    reference = synthetic_field((16, 8), 1, seed=1)
    candidate = synthetic_field((16, 8), 1, seed=2)
    assert max_error_channel_mean(reference, candidate) == max_error(reference, candidate)


def test_it_lies_between_max_error_over_c_and_max_error():
    """A mean of C channel maxima is at most their largest, which is ``max_error``, and at
    least that largest over C."""
    reference = synthetic_field((16, 8), 3, seed=1)
    candidate = synthetic_field((16, 8), 3, seed=2)
    candidate[1] = reference[1]
    pooled = max_error(reference, candidate)
    assert pooled / 3 <= max_error_channel_mean(reference, candidate) <= pooled


def test_mismatched_shapes_are_refused_even_when_they_broadcast():
    """One channel against two would broadcast to a plausible number; it raises instead."""
    with pytest.raises(ValueError, match="matching shapes"):
        max_error_channel_mean(np.ones((1, 4, 2)), np.zeros((2, 4, 2)))
