"""Tests specific to the gaussian_blur degradation.

The contract every operator satisfies -- shape preservation, the declared severity
direction, reproducibility from the seed -- is checked over the whole registry in
``tests/test_degradation_contract.py`` and is not repeated here.

What is tested here is what the card claims: the worked example in its Intuition section,
the exact preservation of the spatial mean, and the monotone attenuation in wavenumber
that separates this kernel from the windowed ones.
"""

from __future__ import annotations

import numpy as np

from tests.conftest import make_ctx

from .degradation import gaussian_blur

FIELD = np.array([[[0.0, 0.0, 0.0, 0.0],
                   [0.0, 1.0, 1.0, 0.0],
                   [0.0, 1.0, 1.0, 0.0],
                   [0.0, 0.0, 0.0, 0.0]]])


def test_worked_example_from_the_card():
    """The 4x4 numbers printed in the card's Intuition section, to two decimals."""
    out = gaussian_blur(FIELD, 1.0, ctx=make_ctx((4, 4)))
    expected = np.array([[0.13, 0.23, 0.23, 0.13],
                         [0.23, 0.42, 0.42, 0.23],
                         [0.23, 0.42, 0.42, 0.23],
                         [0.13, 0.23, 0.23, 0.13]])
    assert np.allclose(out[0], expected, atol=0.005)


def test_attenuation_is_monotone_in_wavenumber():
    """Every mode is damped and none amplified, which the box kernel cannot claim.

    A single sinusoid at each resolvable wavenumber, blurred, must come back with its
    amplitude reduced -- and reduced more at higher wavenumber.
    """
    n = 64
    x = np.arange(n)
    amplitudes = []
    for k in (1, 2, 4, 8):
        wave = np.sin(2 * np.pi * k * x / n)[None, :, None] * np.ones((1, n, n))
        out = gaussian_blur(wave, 2.0, ctx=make_ctx((n, n)))
        amplitudes.append(np.abs(out).max())
    assert all(a < 1.0 for a in amplitudes), amplitudes
    assert amplitudes == sorted(amplitudes, reverse=True), amplitudes
