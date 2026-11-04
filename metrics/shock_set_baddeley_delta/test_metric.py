"""Tests for Baddeley's Delta between shock sets.

The registry-wide contract lives in ``tests/test_metric_contract.py``, and the detector, the
empty-set conventions and the non-finite rule are tested once, in
``metrics/shock_set_distance``. What is tested here is the worked example of the card, the
bound by the Hausdorff distance, and the value of a long one-dimensional shift.
"""

from __future__ import annotations

import numpy as np
import pytest

from metrics.shock_set_hausdorff.metric import hausdorff
from tests.conftest import SHOCK_STEP, SHOCK_STEP_MOVED, SHOCK_STEP_SPIKE, make_ctx

from .metric import baddeley_delta, shock_set_baddeley_delta


def test_worked_example_from_the_card():
    """Every one of the sixteen cells is measured to the nearest flagged cell of each field.

    Moved two cells: the reference's flagged cells are {7, 8}, so its distance map is
    7 6 5 4 3 2 1 0 0 1 2 3 4 5 6 7; the candidate's are {9, 10}, map 9 8 7 6 5 4 3 2 1 0 0 1 2
    3 4 5. They differ by 2 at fourteen cells and by 1 at cells 8 and 9: the mean square is
    (14 * 4 + 2 * 1) / 16 = 58/16, and Delta = sqrt(3.625) = 1.9039.

    Spike: the candidate's flagged cells are {0, 2, 7, 8}, map 0 1 0 1 2 2 1 0 0 1 2 ...; the two
    maps differ by 7, 5, 5, 3, 1 at cells 0 to 4 and agree elsewhere: the mean square is
    (49 + 25 + 25 + 9 + 1) / 16 = 109/16, and Delta = sqrt(6.8125) = 2.6101.
    """
    assert shock_set_baddeley_delta(SHOCK_STEP, SHOCK_STEP_MOVED, ctx=make_ctx((16,))) == (
        pytest.approx(np.sqrt(58 / 16), rel=1e-12))
    assert shock_set_baddeley_delta(SHOCK_STEP, SHOCK_STEP_SPIKE, ctx=make_ctx((16,))) == (
        pytest.approx(np.sqrt(109 / 16), rel=1e-12))


def test_it_never_exceeds_the_hausdorff_distance():
    """|d(x, A) - d(x, B)| <= HD(A, B) at every cell x, so a root mean of it is at most the
    Hausdorff distance; checked on random sets of a 2-D grid with an anisotropic spacing."""
    rng = np.random.default_rng(11)
    for _ in range(20):
        a, b = rng.random((10, 7)) < 0.1, rng.random((10, 7)) < 0.1
        a[0, 0] = b[9, 6] = True
        assert baddeley_delta(a, b, (1.0, 1.5)) <= hausdorff(a, b, (1.0, 1.5)) * (1 + 1e-12)


def test_a_long_shift_scores_nearly_the_shift():
    """Two cells {500, 501} moved by s = 10 on 2048 cells: left of both sets and right of both,
    the maps differ by exactly s; only the s + 2 cells from 500 to 511 differ by less. So Delta
    lies between s * sqrt((2048 - 12) / 2048) and s."""
    a, b = np.zeros(2048, bool), np.zeros(2048, bool)
    a[[500, 501]] = b[[510, 511]] = True
    delta = baddeley_delta(a, b, (1.0,))
    assert 10 * np.sqrt(2036 / 2048) <= delta < 10
