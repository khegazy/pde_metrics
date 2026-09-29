"""Tests for palinstrophy.

The registry-wide contract lives in ``tests/test_metric_contract.py``. What is tested here
is the closed-form value for a single Fourier mode, the k^2 weighting that distinguishes
this from enstrophy, and the dependence on grid spacing that makes the ctx necessary.
"""

from __future__ import annotations

import numpy as np
import pytest

from fmeval.context import FieldContext
from fmeval.data.base import GridSpec

from ..enstrophy.metric import enstrophy
from .metric import palinstrophy


def _ctx(shape: tuple[int, ...], spacing: float = 1.0) -> FieldContext:
    return FieldContext(
        field="vorticity",
        grid=GridSpec(shape=shape, spacing=(spacing,) * len(shape),
                      periodic=(True,) * len(shape)),
        frame_index=0, time=0.0, fluctuation_rms=1.0,
        rng=np.random.default_rng(0),
    )


def _wave(shape: tuple[int, int], mode: int, spacing: float = 1.0) -> np.ndarray:
    """``cos(2 pi m x / L)`` along x, constant along y, as ``(1, *shape)``."""
    x = np.arange(shape[0]) * spacing
    length = shape[0] * spacing
    profile = np.cos(2.0 * np.pi * mode * x / length)
    return np.broadcast_to(profile[:, None], shape).copy()[np.newaxis, ...]


def test_worked_example_from_the_card():
    """A unit-amplitude mode-1 wave on an 8x8 unit grid gives (2 pi / L)^2 / 4.

    The x-derivative of ``cos(kx)`` is ``-k sin(kx)``, whose mean square is ``k^2 / 2``; the
    y-derivative is zero. Palinstrophy is half of that, so ``k^2 / 4`` with
    ``k = 2 pi / 8 = 0.785398``, giving 0.154213.

    The same field has enstrophy ``0.5 * <cos^2> = 0.25``, and the ratio of the two is
    ``k^2 / 2`` -- the k^2 weighting, in one number.
    """
    shape = (8, 8)
    field = _wave(shape, mode=1)
    k = 2.0 * np.pi / shape[0]

    assert palinstrophy(field, ctx=_ctx(shape)) == pytest.approx(k**2 / 4.0)
    assert enstrophy(field) == pytest.approx(0.25)


@pytest.mark.parametrize("mode", [1, 2, 3])
def test_it_weights_a_mode_by_k_squared_where_enstrophy_does_not(mode: int):
    """Palinstrophy rises as the square of the wavenumber; enstrophy does not move at all.

    This is the entire difference between the two diagnostics, and it is why palinstrophy
    responds to smoothing far more strongly.
    """
    shape = (16, 16)
    field = _wave(shape, mode=mode)
    k = 2.0 * np.pi * mode / shape[0]

    assert palinstrophy(field, ctx=_ctx(shape)) == pytest.approx(k**2 / 4.0)
    assert enstrophy(field) == pytest.approx(0.25)


def test_value_scales_with_the_inverse_square_of_the_spacing():
    """Doubling the cell size halves every wavenumber, so palinstrophy falls by four.

    This is why the metric must read the analysis grid rather than assume unit cells: on a
    grid coarsened by a factor, using the native spacing would inflate the result by exactly
    the square of that factor.
    """
    shape = (8, 8)
    field = _wave(shape, mode=1)
    unit = palinstrophy(field, ctx=_ctx(shape, spacing=1.0))
    doubled = palinstrophy(field, ctx=_ctx(shape, spacing=2.0))
    assert doubled == pytest.approx(unit / 4.0)


def test_a_constant_field_has_no_palinstrophy():
    """A uniform vorticity field has zero gradient everywhere, so the value is exactly 0."""
    assert palinstrophy(np.full((1, 8, 8), 4.2), ctx=_ctx((8, 8))) == pytest.approx(0.0, abs=1e-20)
