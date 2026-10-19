"""Tests for the H^1 seminorm.

The registry-wide contract lives in ``tests/test_metric_contract.py``, with the scaling
with grid spacing this shares with ``h_minus_one`` and ``palinstrophy``. What is tested here
is the closed-form value for a single mode, the ``k`` scaling that is the mirror image of
``h_minus_one``'s ``1/k``, and the displacement behaviour -- of both seminorms against
rmse -- that is the reason the tracker rates this Low.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import cosine_mode, make_ctx

from ..h_minus_one.metric import h_minus_one
from ..mse.metric import mse
from ..rmse.metric import rmse
from .metric import h1_seminorm


def test_worked_example_from_the_card():
    """A mode-1 error on an 8x8 unit grid scores k / sqrt(2) with k = 2 pi / 8.

    The gradient of ``cos(kx)`` is ``-k sin(kx)``, whose root mean square is ``k / sqrt(2)``.
    That is 0.555360. The same error scores 0.707107 under rmse, so the ratio is exactly k,
    the factor this metric applies.
    """
    shape = (8, 8)
    reference, candidate = np.zeros((1, *shape)), cosine_mode(shape, mode=1)
    k = 2.0 * np.pi / shape[0]

    assert h1_seminorm(reference, candidate, ctx=make_ctx(shape)) == pytest.approx(k / np.sqrt(2.0))
    assert rmse(reference, candidate) == pytest.approx(1.0 / np.sqrt(2.0))

    # The card's second number: three oscillations across the box triple the wavenumber,
    # so the value triples to 3k / sqrt(2) = 1.666081 while rmse stays at 0.707107.
    three = cosine_mode(shape, mode=3)
    assert h1_seminorm(reference, three, ctx=make_ctx(shape)) == pytest.approx(
        3.0 * k / np.sqrt(2.0))
    assert rmse(reference, three) == pytest.approx(1.0 / np.sqrt(2.0))


@pytest.mark.parametrize("mode", [1, 2, 3])
def test_it_is_the_exact_mirror_of_h_minus_one(mode: int):
    """For a single mode the two seminorms multiply to the mean squared error.

    ``h1 = k * rms`` and ``h_minus_one = rms / k``, so their product is ``rms^2 = mse`` for
    any k at all. That identity is the cleanest statement of what the two metrics are: the
    same error weighted by k and by 1/k, on one normalisation.
    """
    shape = (16, 16)
    ctx = make_ctx(shape)
    reference, candidate = np.zeros((1, *shape)), cosine_mode(shape, mode=mode)

    product = (h1_seminorm(reference, candidate, ctx=ctx)
               * h_minus_one(reference, candidate, ctx=ctx))
    assert product == pytest.approx(mse(reference, candidate))


def test_a_constant_offset_is_invisible():
    """A gradient annihilates constants, so a uniform bias costs nothing.

    Shared with h_minus_one, and for a different reason: there the k = 0 mode is excluded
    from the sum, here it is differentiated away. The consequence for a reader is the same.
    """
    shape = (8, 8)
    field = cosine_mode(shape, mode=1)
    assert h1_seminorm(field, field + 9.0, ctx=make_ctx(shape)) == pytest.approx(0.0, abs=1e-12)


def test_displacement_costs_more_than_it_does_under_rmse():
    """The property that makes this the wrong tool for a shifted feature.

    Each metric's value for a one-cell shift is taken as a fraction of its own value for an
    unrelated field, which removes the units and leaves the comparison the repository cares
    about. Where h_minus_one pays a smaller fraction than rmse, this pays a larger one; the
    one assertion pins both halves, so it is also ``h_minus_one``'s displacement test.
    """
    shape = (16, 16)
    ctx = make_ctx(shape)
    reference = cosine_mode(shape, mode=1) + 0.3 * cosine_mode(shape, mode=5)
    shifted = np.roll(reference, 1, axis=1)
    unrelated = np.roll(reference, shape[0] // 2, axis=1)

    h1_fraction = (h1_seminorm(reference, shifted, ctx=ctx)
                   / h1_seminorm(reference, unrelated, ctx=ctx))
    rmse_fraction = rmse(reference, shifted) / rmse(reference, unrelated)
    hm1_fraction = (h_minus_one(reference, shifted, ctx=ctx)
                    / h_minus_one(reference, unrelated, ctx=ctx))
    assert hm1_fraction < rmse_fraction < h1_fraction
