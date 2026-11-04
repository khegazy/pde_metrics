"""Tests specific to PDEBench's normalised root mean squared error.

The registry-wide contract is checked in ``tests/test_metric_contract.py``. What is tested here
is what the card claims: the worked example in its Intuition section, that the denominator is
the raw RMS of the reference with no mean removed, the mean over channels, the asymmetry, the
failure of the triangle inequality, and the zero reference.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import SQUARE_REFERENCE, SQUARE_SHIFTED, synthetic_field

from ..rmse.metric import rmse
from ..vrmse.metric import vrmse
from .metric import nrmse


def test_worked_example_from_the_card():
    """The table in the card's Intuition section.

    The moved square has RMSE sqrt(4/16) = 0.5 and the reference's RMS is also
    sqrt(4/16) = 0.5, so nRMSE is 1. On a background of 1000, the RMSE is still 0.5 but the
    reference's RMS is sqrt(1000^2 + 2 * 1000 * 4/16 + 4/16) = sqrt(1000500.25) = 1000.2501, so
    nRMSE falls to 0.5 / 1000.2501 = 4.9988e-4. ``vrmse`` divides by the fluctuation and stays at
    sqrt(0.25 / (3/15 + 1e-7)) = 1.1180 on both.
    """
    background = 1000.0
    assert nrmse(SQUARE_REFERENCE, SQUARE_SHIFTED) == 1.0
    assert nrmse(SQUARE_REFERENCE + background, SQUARE_SHIFTED + background) == pytest.approx(
        0.5 / np.sqrt(1000500.25), rel=1e-12)
    assert rmse(SQUARE_REFERENCE + background, SQUARE_SHIFTED + background) == pytest.approx(
        0.5, rel=1e-12)
    for offset in (0.0, background):
        assert vrmse(SQUARE_REFERENCE + offset, SQUARE_SHIFTED + offset) == pytest.approx(
            np.sqrt(0.25 / (0.2 + 1e-7)), rel=1e-12)


def test_scaling_both_fields_leaves_it_unchanged():
    """Error and denominator scale together, with no constant added to break it."""
    reference = synthetic_field((16, 8), 2, seed=1)
    candidate = synthetic_field((16, 8), 2, seed=2)
    plain = nrmse(reference, candidate)
    for factor in (1e-6, 1e3):
        assert nrmse(reference * factor, candidate * factor) == pytest.approx(plain, rel=1e-12)


def test_channels_are_normalised_separately_and_then_averaged():
    """PDEBench's reduction: one ratio per channel, then their mean.

    The first channel is the moved square, nRMSE 1; the second is a copy of the reference
    scaled by 100 and predicted exactly, nRMSE 0. The mean is 0.5. Pooling the channels would
    divide one RMSE by the RMS of both, which the large second channel dominates.
    """
    reference = np.concatenate([SQUARE_REFERENCE, 100.0 * SQUARE_REFERENCE])
    candidate = np.concatenate([SQUARE_SHIFTED, 100.0 * SQUARE_REFERENCE])
    assert nrmse(reference, candidate) == 0.5


def test_it_is_not_symmetric():
    """The reference sets the scale: halving its amplitude halves the denominator."""
    damped = SQUARE_REFERENCE * 0.5
    assert nrmse(SQUARE_REFERENCE, damped) == 0.5
    assert nrmse(damped, SQUARE_REFERENCE) == 1.0


def test_it_breaks_the_triangle_inequality():
    """Each term is divided by its own first argument's scale, so the inequality can fail.

    With f the square, g twice it and h three times it, d(f, h) = 1 / 0.5 = 2 while
    d(f, g) + d(g, h) = 0.5 / 0.5 + 0.5 / 1 = 1.5.
    """
    f, g, h = SQUARE_REFERENCE, 2.0 * SQUARE_REFERENCE, 3.0 * SQUARE_REFERENCE
    assert nrmse(f, h) == 2.0
    assert nrmse(f, g) + nrmse(g, h) == 1.5


def test_a_reference_channel_of_zeros_has_no_scale():
    """PDEBench's division has no value there; NaN rather than an infinity."""
    reference = np.concatenate([SQUARE_REFERENCE, np.zeros((1, 4, 4))])
    assert np.isnan(nrmse(reference, reference + 0.1))


def test_mismatched_shapes_are_refused_even_when_they_broadcast():
    with pytest.raises(ValueError, match="matching shapes"):
        nrmse(np.ones((1, 4, 2)), np.zeros((2, 4, 2)))
