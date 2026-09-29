"""Tests for ``coarsen_bandlimited``.

The registry-wide contract (shape and dtype preserved, passthrough, declared direction,
seed reproducibility) lives in ``tests/test_degradation_contract.py``. What is tested here is
what makes this operator the companion of ``coarsen`` rather than just another smoothing:
it keeps the same block means, it adds nothing above the coarse band, and it therefore does
not create the edges ``issues/039`` is about.
"""

from __future__ import annotations

import numpy as np
import pytest

from degradations.coarsen.degradation import coarsen
from fmeval.remap import block_average

from .degradation import coarsen_bandlimited

#: Non-square, as the contract tests require, and divisible by every factor used here.
SHAPE = (32, 16)


def _random(seed: int = 0, channels: int = 2) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal((channels, *SHAPE))


@pytest.mark.parametrize("factor", [2, 4, 8])
def test_block_means_are_those_coarsen_keeps(factor: int):
    """Both operators discard the same information: their block means agree exactly.

    That is what makes the pair a controlled comparison. Any difference between a metric's
    response to the two is a response to how each block is filled in, not to how much
    resolution was lost.
    """
    x = _random()
    band = coarsen_bandlimited(x, factor, ctx=None)
    stair = coarsen(x, factor, ctx=None)

    np.testing.assert_allclose(block_average(band, factor), block_average(x, factor), atol=1e-12)
    np.testing.assert_allclose(block_average(band, factor), block_average(stair, factor),
                               atol=1e-12)


@pytest.mark.parametrize("factor", [2, 4, 8])
def test_nothing_is_added_above_the_coarse_band(factor: int):
    """Along each axis, no mode above the coarse grid's Nyquist wavenumber survives.

    ``coarsen``'s staircase fails this badly: its jumps put energy at every wavenumber up to
    the fine grid's limit, which is what a derivative-based metric then measures.
    """
    x = _random()
    kx = np.abs(np.fft.fftfreq(SHAPE[0]) * SHAPE[0])[:, None]
    ky = np.abs(np.fft.fftfreq(SHAPE[1]) * SHAPE[1])[None, :]
    outside = (kx > SHAPE[0] / (2 * factor)) | (ky > SHAPE[1] / (2 * factor))

    def fraction_outside(y: np.ndarray) -> float:
        power = np.abs(np.fft.fftn(y, axes=(1, 2))) ** 2
        return float(power[:, outside].sum() / power.sum())

    assert fraction_outside(coarsen_bandlimited(x, factor, ctx=None)) < 1e-25
    assert fraction_outside(coarsen(x, factor, ctx=None)) > 1e-3


def test_a_field_the_coarse_grid_can_represent_is_returned_unchanged():
    """A wave well inside the coarse band is exactly recoverable from its block means.

    A mode-1 cosine along x on 32 cells, coarsened by 4 to 8 cells, is far below the coarse
    Nyquist of 4, so the band-limited field with its block means is the wave itself. The
    staircase is not: it reports the same block means with a step in every block.
    """
    x = np.broadcast_to(np.cos(2 * np.pi * np.arange(32) / 32)[:, None], SHAPE)[None].copy()

    np.testing.assert_allclose(coarsen_bandlimited(x, 4, ctx=None), x, atol=1e-12)
    assert not np.allclose(coarsen(x, 4, ctx=None), x, atol=1e-3)


def test_worked_example_from_the_card():
    """One row of eight cells, coarsened by two, beside what ``coarsen`` gives.

    The row (0, 1, 1, 1, 1, 0, 0, 0) has pair means (0.5, 1, 0.5, 0). ``coarsen`` repeats
    them, a step of 0.5 at two block edges. The band-limited reconstruction keeps the same
    pair means but ramps between them: (0.2929, 0.7071, 1, 1, 0.7071, 0.2929, 0, 0), where
    0.2929 + 0.7071 = 1, so each pair still averages 0.5.
    """
    row = np.array([0, 1, 1, 1, 1, 0, 0, 0], dtype=float)
    x = np.tile(row[:, None], (1, 4))[None]

    band = coarsen_bandlimited(x, 2, ctx=None)[0, :, 0]
    stair = coarsen(x, 2, ctx=None)[0, :, 0]

    np.testing.assert_allclose(stair, [0.5, 0.5, 1, 1, 0.5, 0.5, 0, 0])
    a = (2 - np.sqrt(2)) / 2      # 0.2929
    np.testing.assert_allclose(band, [a, 1 - a, 1, 1, 1 - a, a, 0, 0], atol=1e-12)


@pytest.mark.parametrize(("factor", "low", "high"), [(2, 0.17, 0.19), (4, 0.20, 0.22),
                                                     (8, 0.21, 0.23)])
def test_a_step_rings_where_coarsen_steps(factor: int, low: float, high: float):
    """The limitation the card states: a sharp front overshoots rather than steps.

    A unit step on 64 cells (two edges, on a periodic domain) comes back overshooting by 18%,
    21% and 23% of the step at factors 2, 4 and 8 -- more than the classic 9% Gibbs
    overshoot, because inverting the box average boosts the modes nearest the cut.
    ``coarsen`` stays within the original range. On a shocked flow a derivative-based
    metric would therefore see ringing here in place of the staircase there.
    """
    row = (np.arange(64) >= 32).astype(float)
    x = np.tile(row[:, None], (1, 8))[None]

    band = coarsen_bandlimited(x, factor, ctx=None)
    stair = coarsen(x, factor, ctx=None)

    assert low < band.max() - 1.0 < high
    assert stair.max() <= 1.0 and stair.min() >= 0.0


def test_the_spatial_mean_is_preserved_exactly():
    """The zero mode passes through the inversion with gain one."""
    x = _random() + 3.0
    np.testing.assert_allclose(coarsen_bandlimited(x, 4, ctx=None).mean(axis=(1, 2)),
                               x.mean(axis=(1, 2)), atol=1e-12)


def test_a_factor_of_one_is_the_identity():
    x = _random()
    assert coarsen_bandlimited(x, 1, ctx=None) is x
