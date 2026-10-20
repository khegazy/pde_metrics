"""Tests for palinstrophy.

The registry-wide contract lives in ``tests/test_metric_contract.py``, with the dependence
on grid spacing that makes the ctx necessary. What is tested here is the closed-form value
for a single Fourier mode and the k^2 weighting that distinguishes this from enstrophy.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import cosine_mode, make_ctx

from ..enstrophy.metric import enstrophy
from .metric import palinstrophy


def test_worked_example_from_the_card():
    """A unit-amplitude mode-1 wave on an 8x8 unit grid gives (2 pi / L)^2 / 4.

    The x-derivative of ``cos(kx)`` is ``-k sin(kx)``, whose mean square is ``k^2 / 2``; the
    y-derivative is zero. Palinstrophy is half of that, so ``k^2 / 4`` with
    ``k = 2 pi / 8 = 0.785398``, giving 0.154213.

    The same field has enstrophy ``0.5 * <cos^2> = 0.25``, and the ratio of the two is
    ``k^2 / 2`` -- the k^2 weighting, in one number.
    """
    shape = (8, 8)
    field = cosine_mode(shape, mode=1)
    k = 2.0 * np.pi / shape[0]

    assert palinstrophy(field, ctx=make_ctx(shape)) == pytest.approx(k**2 / 4.0)
    assert enstrophy(field) == pytest.approx(0.25)


@pytest.mark.parametrize("mode", [1, 2, 3])
def test_it_weights_a_mode_by_k_squared_where_enstrophy_does_not(mode: int):
    """Palinstrophy rises as the square of the wavenumber; enstrophy does not move at all.

    This is the entire difference between the two diagnostics, and it is why palinstrophy
    responds to smoothing far more strongly.
    """
    shape = (16, 16)
    field = cosine_mode(shape, mode=mode)
    k = 2.0 * np.pi * mode / shape[0]

    assert palinstrophy(field, ctx=make_ctx(shape)) == pytest.approx(k**2 / 4.0)
    assert enstrophy(field) == pytest.approx(0.25)


def test_a_constant_field_has_no_palinstrophy():
    """A uniform vorticity field has zero gradient everywhere, so the value is exactly 0."""
    constant = np.full((1, 8, 8), 4.2)
    assert palinstrophy(constant, ctx=make_ctx((8, 8))) == pytest.approx(0.0, abs=1e-20)
