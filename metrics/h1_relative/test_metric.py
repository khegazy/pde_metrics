"""Tests for the neural-operator relative H^1 error.

The registry-wide contract lives in ``tests/test_metric_contract.py``. What is tested here is
what only this bundle claims: the worked example of the card, computed by hand; the centred
difference, which cannot see a grid-scale checkerboard; the zeroth-order term, which sees a
uniform offset that ``h1_seminorm`` does not; and the sum over channels. The unit-length
domain, ``h = 1 / N``, is pinned by the worked example's stencil factor.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import cosine_mode, make_ctx

from ..h1_seminorm.metric import h1_seminorm
from ..rmse.metric import rmse
from .metric import EPSILON, h1_relative

# One cosine along x on a 4 x 4 grid, constant along y: columns 1, 0, -1, 0.
REFERENCE = np.tile(np.array([1.0, 0.0, -1.0, 0.0])[:, None], (1, 4))[None]
# The reference moved one cell along x: columns 0, 1, 0, -1.
SHIFTED = np.roll(REFERENCE, 1, axis=1)
# Half a checkerboard along x added to the reference: the error is 0.5, -0.5, 0.5, -0.5.
CHECKER = REFERENCE + 0.5 * np.tile(np.array([1.0, -1.0, 1.0, -1.0])[:, None], (1, 4))[None]


def test_worked_example_from_the_card():
    """Both numbers of the card's example, worked out by hand.

    With h = 1/4 the centred difference is ``(f[i+1] - f[i-1]) * 2``. The reference's squares
    sum to 2 per row, 8 over the grid; its x-differences are 0, -4, 0, 4, squares 32 per row,
    128 over the grid; its y-differences are zero. So its squared H^1 norm is 136.

    Shifted: the error is -1, 1, 1, -1 per row (16 over the grid) with differences 4, 4, -4,
    -4 (256 over the grid), 272 in all, and the value is sqrt(272 / 136) = sqrt(2) = 1.41421,
    which is also its relative L2 error, sqrt(16 / 8): a single mode is weighted alike by both.

    Checkerboard: the error's squares sum to 4 and its centred differences are all zero, so
    the value is sqrt(4 / 136) = 0.171499, against a relative L2 error of sqrt(4 / 8) =
    0.707107. The centred difference cannot see the grid-scale mode, and the reference's
    gradient inflates the denominator.
    """
    assert h1_relative(REFERENCE, SHIFTED) == pytest.approx(
        np.sqrt(272.0) / (np.sqrt(136.0) + EPSILON), rel=1e-14)
    assert h1_relative(REFERENCE, SHIFTED) == pytest.approx(1.414214, abs=5e-7)
    assert h1_relative(REFERENCE, CHECKER) == pytest.approx(
        np.sqrt(4.0) / (np.sqrt(136.0) + EPSILON), rel=1e-14)
    assert h1_relative(REFERENCE, CHECKER) == pytest.approx(0.171499, abs=5e-7)


def test_a_prediction_of_zero_scores_one_per_channel():
    """The relative norm of the reference against itself is one, less the 1e-8."""
    reference = cosine_mode((8, 8), mode=2)
    k_h = 8 * np.sin(np.pi / 2)            # the centred difference's eigenvalue, h = 1/8
    expected = 1.0 / (1.0 + EPSILON / np.sqrt(np.sum(reference**2) * (1 + k_h**2)))
    assert h1_relative(reference, np.zeros_like(reference)) == pytest.approx(expected, rel=1e-12)


def test_a_uniform_offset_counts_through_the_zeroth_order_term():
    """Inhomogeneous: an offset has no gradient but is charged by the value term.

    ``h1_seminorm`` returns zero for the same pair; this returns the offset's L2 norm over the
    reference's H^1 norm, 3 * 4 = 12 over sqrt(136).
    """
    offset = REFERENCE + 3.0
    assert h1_relative(REFERENCE, offset) == pytest.approx(
        12.0 / (np.sqrt(136.0) + EPSILON), rel=1e-14)
    assert h1_seminorm(REFERENCE, offset, ctx=make_ctx((4, 4))) == pytest.approx(0.0, abs=1e-12)


def test_channels_are_summed():
    """``reduction="sum"``: two identical channels score twice one."""
    one = h1_relative(REFERENCE, SHIFTED)
    two = h1_relative(np.concatenate([REFERENCE] * 2), np.concatenate([SHIFTED] * 2))
    assert two == pytest.approx(2.0 * one, rel=1e-14)


def test_it_is_not_symmetric():
    """The reference's norm is the denominator, so swapping the fields changes the value."""
    other = 2.0 * REFERENCE
    assert h1_relative(REFERENCE, other) == pytest.approx(1.0, rel=1e-6)
    assert h1_relative(other, REFERENCE) == pytest.approx(0.5, rel=1e-6)


def test_it_reads_the_relative_l2_error_when_the_error_has_the_reference_shape():
    """Scaling the reference by 1.3 gives 0.3 in every norm, which rmse confirms on L2."""
    reference = cosine_mode((8, 8), mode=1)
    candidate = 1.3 * reference
    assert h1_relative(reference, candidate) == pytest.approx(0.3, rel=1e-6)
    assert rmse(reference, candidate) / rmse(reference, 0.0 * reference) == pytest.approx(0.3)
