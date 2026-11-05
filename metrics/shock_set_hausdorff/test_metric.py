"""Tests for the Hausdorff distance between shock sets.

The registry-wide contract (zero on identical fields, symmetry, one finite float, the doubling
of the value with the grid spacing) lives in ``tests/test_metric_contract.py``, and the
detector, the empty-set conventions and the non-finite rule are tested once, in
``metrics/shock_set_distance``. What is tested here is the worked example of the card and the
value on the exact Sod solution.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt

from fmeval.data.analytic import SodShockTube
from metrics.shock_set_distance.metric import shock_mask, shock_set_distance
from tests.conftest import SHOCK_STEP, SHOCK_STEP_MOVED, SHOCK_STEP_SPIKE, make_ctx

from .metric import hausdorff, shock_set_hausdorff


def test_worked_example_from_the_card():
    """The step flags cells {7, 8}; moved two cells, {9, 10}; with the spike, {0, 2, 7, 8}.

    Moved: the nearest-cell distances are 7 -> 9: 2, 8 -> 9: 1, and back 9 -> 8: 1, 10 -> 8: 2,
    so the largest is 2 (Taha & Hanbury 2015, Eq. 48), where the average surface distance is
    6/4 = 1.5. Spike: the true cells match exactly, the spurious cell 0 is 7 from cell 7 and
    cell 2 is 5 from it, so the largest is 7, where the average is 12/6 = 2.
    """
    ctx = make_ctx((16,))
    assert shock_set_hausdorff(SHOCK_STEP, SHOCK_STEP_MOVED, ctx=ctx) == 2.0
    assert shock_set_hausdorff(SHOCK_STEP, SHOCK_STEP_SPIKE, ctx=make_ctx((16,))) == 7.0
    assert shock_set_distance(SHOCK_STEP, SHOCK_STEP_SPIKE, ctx=make_ctx((16,))) == 2.0


def test_it_is_the_largest_difference_of_the_two_distance_maps():
    """For two non-empty sets, max over every cell x of |d(x, A) - d(x, B)| is the Hausdorff
    distance: spatstat's deltametric at p = c = infinity, the form SpatialVx computes. Checked on
    two random sets of a 2-D grid with an anisotropic spacing."""
    rng = np.random.default_rng(4)
    a, b = rng.random((12, 9)) < 0.08, rng.random((12, 9)) < 0.08
    a[0, 0] = b[5, 5] = True
    spacing = (1.0, 2.5)
    d_a = distance_transform_edt(~a, sampling=spacing)
    d_b = distance_transform_edt(~b, sampling=spacing)
    assert hausdorff(a, b, spacing) == pytest.approx(np.abs(d_a - d_b).max(), rel=1e-12)


def test_on_the_exact_sod_solution_a_moved_shock_scores_its_shift():
    """The exact Sod pressure at t = 0.1 and t = 0.11 on 2048 cells: two adjacent cells are
    flagged in each, moved by a whole number s of cells, so each flagged cell's farther partner
    is s cells away and the Hausdorff distance is s cells, half a cell more than the average
    surface distance's s - 1/2."""
    tube = SodShockTube(n_frames=2, t_start=0.1, t_end=0.11)
    early, late = (tube.solution(t)["pressure"] for t in (0.1, 0.11))
    s = int(np.flatnonzero(shock_mask(late[0]))[0] - np.flatnonzero(shock_mask(early[0]))[0])
    dx = tube.grid.spacing[0]
    ctx = make_ctx((2048,), spacing=dx)
    assert shock_set_hausdorff(early, late, ctx=ctx) == pytest.approx(s * dx, rel=1e-12)
    assert shock_set_distance(early, late, ctx=make_ctx((2048,), spacing=dx)) == pytest.approx(
        (s - 0.5) * dx, rel=1e-12)
