"""Tests for the H^-1 metric.

The contract tests every metric must satisfy -- symmetry, zero on identical fields, the
pointwise map reducing to the scalar, float32/float64 agreement -- live in
``tests/test_metric_contract.py`` and run over the whole registry. What is tested here is
what only this metric claims: the worked example printed in the card, the ``1 / k`` scaling
that is the entire point of a negative-order norm, the proportionality to domain size, and
the blindness to a constant offset that the homogeneous seminorm implies.

Every expected value in this file is derived in closed form in the docstring beside it, not
copied from a run.
"""

from __future__ import annotations

import numpy as np
import pytest

from fmeval.context import FieldContext
from fmeval.data.base import GridSpec

from ..rmse.metric import rmse
from .metric import h_minus_one


def _ctx(shape: tuple[int, ...], spacing: float = 1.0) -> FieldContext:
    """A minimal context; this metric uses only the grid's spacing and shape."""
    return FieldContext(
        field="density",
        grid=GridSpec(
            shape=shape,
            spacing=(spacing,) * len(shape),
            periodic=(True,) * len(shape),
        ),
        frame_index=0,
        time=0.0,
        fluctuation_rms=1.0,
        rng=np.random.default_rng(0),
    )


def _cosine_mode(shape: tuple[int, int], mode: int, spacing: float = 1.0) -> np.ndarray:
    """``cos(2 pi m x / L)``, constant along y, as a single-channel ``(1, *shape)`` field.

    x is the first *spatial* axis, per the canonical trailing-axes layout.
    """
    x = np.arange(shape[0]) * spacing
    length = shape[0] * spacing
    profile = np.cos(2.0 * np.pi * mode * x / length)
    return np.broadcast_to(profile[:, None], shape).copy()[np.newaxis, ...]


def test_worked_example_from_the_card():
    """The 4x4 example in the card's Intuition section.

    The error field is one cosine along x at mode m = 1 on a 4x4 grid of unit spacing, so
    the domain length is L = 4 and the only excited wavevectors are the conjugate pair
    m = +/-1 with |k| = 2 pi / L = pi / 2.

    A unit-amplitude cosine has Fourier coefficients 1/2 at each of that pair, so with the
    root-mean-square normalisation this metric uses, the sum of |coefficient|^2 is
    2 * (1/2)^2 = 1/2 -- which is the mean square of a cosine, as it must be. Dividing that
    sum by |k|^2 and taking the root gives

        (1 / sqrt(2)) * (L / 2 pi) = (1 / sqrt(2)) * (2 / pi) = sqrt(2) / pi = 0.450158...

    The same error scores 1 / sqrt(2) = 0.707107 under rmse; the ratio is the factor
    1 / |k| that this metric applies and rmse does not.
    """
    reference = np.zeros((1, 4, 4))
    candidate = _cosine_mode((4, 4), mode=1)

    assert h_minus_one(reference, candidate, ctx=_ctx((4, 4))) == pytest.approx(
        np.sqrt(2.0) / np.pi
    )
    assert rmse(reference, candidate) == pytest.approx(1.0 / np.sqrt(2.0))


def test_the_nyquist_mode_is_the_other_half_of_the_worked_example():
    """Mode 2 on the same 4x4 grid: the card contrasts it with mode 1.

    Mode 2 is the Nyquist mode of a 4-point axis, so it is self-conjugate and carries a
    single coefficient of magnitude 1 rather than a conjugate pair of 1/2. Its mean square
    is therefore 1 rather than 1/2, and |k| = 2 pi * 2 / 4 = pi, giving 1 / pi = 0.318310.

    Per unit of rms error that is (1/pi) / 1 against mode 1's (sqrt(2)/pi) / (1/sqrt(2)) =
    2/pi -- a factor of exactly two for a doubling of the wavenumber.
    """
    reference = np.zeros((1, 4, 4))
    candidate = _cosine_mode((4, 4), mode=2)

    assert h_minus_one(reference, candidate, ctx=_ctx((4, 4))) == pytest.approx(
        1.0 / np.pi
    )
    assert rmse(reference, candidate) == pytest.approx(1.0)


@pytest.mark.parametrize("mode", [1, 2, 3])
def test_error_at_mode_m_falls_as_one_over_m(mode: int):
    """A single mode of fixed amplitude scores L / (2 pi m) times its rms.

    This is the defining property: the same amount of error costs less the smaller the
    scale it sits on, which is what makes the norm weaker than L2. An 8-point axis keeps
    every mode tested here below Nyquist, so each is an ordinary conjugate pair.
    """
    shape = (8, 8)
    reference = np.zeros((1, *shape))
    candidate = _cosine_mode(shape, mode=mode)

    expected = (1.0 / np.sqrt(2.0)) * shape[0] / (2.0 * np.pi * mode)
    assert h_minus_one(reference, candidate, ctx=_ctx(shape)) == pytest.approx(expected)


def test_value_scales_with_the_physical_domain_size():
    """Doubling the cell spacing doubles the value: the norm carries a length.

    Same field, same mode index, twice the spacing means twice the domain and half the
    wavenumber, so 1 / |k| doubles. This is why the metric must read the *analysis* grid's
    spacing rather than assuming unit cells.
    """
    shape = (8, 8)
    reference = np.zeros((1, *shape))
    candidate = _cosine_mode(shape, mode=1)

    unit = h_minus_one(reference, candidate, ctx=_ctx(shape, spacing=1.0))
    doubled = h_minus_one(reference, candidate, ctx=_ctx(shape, spacing=2.0))
    assert doubled == pytest.approx(2.0 * unit)


def test_a_constant_offset_is_invisible():
    """A uniform bias lies entirely in k = 0, which the homogeneous seminorm excludes.

    This is the metric's sharpest blind spot and it is exact, not approximate: a
    prediction offset by any constant scores zero. Stated in the card's Limitations.
    """
    shape = (8, 8)
    reference = _cosine_mode(shape, mode=1)
    candidate = reference + 17.0

    assert h_minus_one(reference, candidate, ctx=_ctx(shape)) == pytest.approx(0.0)
    assert rmse(reference, candidate) == pytest.approx(17.0)


def test_displacement_costs_less_than_it_does_under_rmse():
    """Shifting a field by one cell: H^-1 pays a smaller fraction of the unrelated level.

    Both metrics are anchored against the same pair of fields, so comparing each shifted
    value to that metric's own value for an unrelated field removes the units and leaves
    the property the repository cares about -- tolerance of displacement.
    """
    shape = (16, 16)
    ctx = _ctx(shape)
    reference = _cosine_mode(shape, mode=1) + 0.3 * _cosine_mode(shape, mode=5)
    shifted = np.roll(reference, 1, axis=1)
    unrelated = np.roll(reference, shape[0] // 2, axis=1)

    h_fraction = h_minus_one(reference, shifted, ctx=ctx) / h_minus_one(
        reference, unrelated, ctx=ctx
    )
    rmse_fraction = rmse(reference, shifted) / rmse(reference, unrelated)
    assert h_fraction < rmse_fraction
