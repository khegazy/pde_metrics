"""Tests for this bundle's degradation.

The contract every degradation must satisfy -- shape and dtype preserved, the declared
preservation actually holding -- is checked for the whole registry in
``tests/test_degradation_contract.py``. These test what makes it the climatological anchor.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import make_ctx

from .degradation import mean_field

#: The four-by-four field of the card's worked example: a 2x2 block of ones.
BLOCK = np.zeros((1, 4, 4))
BLOCK[0, 1:3, 1:3] = 1.0


def test_the_worked_example():
    """Four ones among sixteen cells: every cell becomes 0.25."""
    out = mean_field(BLOCK, 0.0, ctx=make_ctx(BLOCK))
    np.testing.assert_array_equal(out, np.full_like(BLOCK, 0.25))


def test_each_channel_keeps_its_own_mean():
    x = np.stack([BLOCK[0], 3.0 + BLOCK[0]])
    out = mean_field(x, 0.0, ctx=make_ctx(x))
    np.testing.assert_array_equal(out[0], np.full((4, 4), 0.25))
    np.testing.assert_array_equal(out[1], np.full((4, 4), 3.25))


def test_its_mean_squared_error_is_the_variance():
    """The closed form the anchor rests on: MSE against the mean is the spatial variance."""
    x = np.random.default_rng(0).standard_normal((1, 32, 16))
    out = mean_field(x, 0.0, ctx=make_ctx(x))
    assert np.mean((x - out) ** 2) == pytest.approx(x.var(), rel=1e-12)
