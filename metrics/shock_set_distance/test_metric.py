"""Tests for the shock detector and the distance between shock sets.

The registry-wide contract (zero on identical fields, symmetry, one finite float, the
doubling of the value with the grid spacing) lives in ``tests/test_metric_contract.py``.
These test what is specific to this bundle: the detector's threshold, what it flags and what
it leaves alone, the conventions for empty sets, and the exact Sod solution.
"""

from __future__ import annotations

import numpy as np
import pytest

from fmeval.data.analytic import SodShockTube
from tests.conftest import make_ctx

from .metric import shock_mask, shock_set_distance, surface_distances

#: A pressure step on eight cells, high on the left as in Sod's tube.
STEP = np.array([[1.0, 1.0, 1.0, 1.0, 0.1, 0.1, 0.1, 0.1]])
#: The same step two cells further right.
STEP_SHIFTED = np.array([[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1, 0.1]])


def _score(reference: np.ndarray, candidate: np.ndarray, spacing: float = 1.0) -> float:
    return shock_set_distance(reference, candidate,
                              ctx=make_ctx(reference.shape[1:], spacing=spacing))


def test_worked_example_matches_the_card():
    """The example in the card's Intuition section: a step moved two cells.

    The jump between cells 3 and 4 is a pressure ratio of 10, above the Mach 1.3 ratio 1.805,
    so cells 3 and 4 are flagged, each having the jump between its two neighbours; in the
    candidate, cells 5 and 6. Distances, in cells: 3 -> 5 is 2, 4 -> 5 is 1, 5 -> 4 is 1,
    6 -> 4 is 2. The average of the four is 6/4 = 1.5.
    """
    assert np.flatnonzero(shock_mask(STEP[0])).tolist() == [3, 4]
    assert np.flatnonzero(shock_mask(STEP_SHIFTED[0])).tolist() == [5, 6]
    assert _score(STEP, STEP_SHIFTED) == pytest.approx(1.5)


def test_a_one_cell_shift_overlaps_the_two_flagged_cells():
    """Moved one cell, the flagged pairs {3, 4} and {4, 5} share cell 4.

    Distances: 3 -> 4 is 1, 4 -> 4 is 0, 4 -> 4 is 0, 5 -> 4 is 1; the average is 2/4 = 0.5.
    A step moved by s >= 1 cells scores s - 1/2 cells, because each flagged pair's nearer cell
    is s - 1 away and its farther cell s away.
    """
    shifted = np.array([[1.0, 1.0, 1.0, 1.0, 1.0, 0.1, 0.1, 0.1]])
    assert _score(STEP, shifted) == pytest.approx(0.5)


def test_the_threshold_is_the_pressure_ratio_of_a_mach_1_3_shock():
    """Schaal & Springel (2015), MNRAS 446, 3992, Eq. (2) at gamma = 1.4 and M = 1.3:
    2 * 1.4 * 1.69 / 2.4 - 0.4 / 2.4 = 1.971667 - 0.166667 = 1.805. A step of ratio 1.80
    is not a shock and one of 1.81 is."""
    assert not shock_mask(np.array([1.80, 1.80, 1.0, 1.0])).any()
    assert shock_mask(np.array([1.81, 1.81, 1.0, 1.0])).tolist() == [False, True, True, False]


def test_the_walls_are_not_wrapped():
    """A smooth fall from 1 to 0.1 over 16 cells changes by 10^(2/15) = 1.36 across any cell's
    two neighbours, below 1.805, so nothing is flagged. Wrapped, the ends would meet as a jump
    of 10 and cells 0 and 15 would be flagged."""
    assert not shock_mask(np.geomspace(1.0, 0.1, 16)).any()


def test_a_non_positive_pressure_is_flagged():
    """The ratio across a zero or negative pressure is unbounded, so the cell beside it is a
    shock (the convention in the card and issues/102)."""
    assert shock_mask(np.array([1.0, 1.0, 0.0, 1.0, 1.0])).tolist() == [
        False, True, False, True, False]
    assert shock_mask(np.array([1.0, 1.0, -0.5, 1.0, 1.0])).tolist() == [
        False, True, False, True, False]


def test_empty_sets_score_zero_together_and_the_diagonal_alone():
    """No shock in either field is agreement, 0. A shock in one field only is the worst value,
    the diagonal of the domain: 8 cells of spacing 0.5 give 8 * 0.5 = 4."""
    flat = np.full((1, 8), 0.55)
    assert _score(flat, flat + 0.1, spacing=0.5) == 0.0
    assert _score(STEP, flat, spacing=0.5) == pytest.approx(4.0)
    assert _score(flat, STEP, spacing=0.5) == pytest.approx(4.0)


def test_surface_distances_are_euclidean_at_the_grid_spacing():
    """One point at (0, 0), one at (3, 4) in cells: 5 cells apart on a unit grid, and
    sqrt((3 * 2)^2 + 4^2) = sqrt(52) on a grid twice as wide along x."""
    a, b = np.zeros((6, 6), dtype=bool), np.zeros((6, 6), dtype=bool)
    a[0, 0], b[3, 4] = True, True
    assert surface_distances(a, b, (1.0, 1.0))[0].tolist() == pytest.approx([5.0])
    assert surface_distances(a, b, (2.0, 1.0))[1].tolist() == pytest.approx([np.sqrt(52.0)])
    with pytest.raises(ValueError, match="non-empty"):
        surface_distances(a, np.zeros_like(b), (1.0, 1.0))


def test_on_the_exact_sod_solution_it_finds_the_shock_and_tracks_its_speed():
    """The exact Sod solution at t = 0.1 and t = 0.11 on 2048 cells.

    Only the shock is flagged, as the two cells straddling x = 0.5 + S_R t: the contact
    carries no pressure jump and the rarefaction is smooth. S_R is the reader's exact shock
    speed, 1.75216, which ``tests/test_analytic_datasets.py`` checks against the published
    value (``docs/datasets/sod_shock_tube.md``). Between the two times the shock moves
    S_R * 0.01 = 0.0175, 35.9 cells, so the score is (s - 1/2) cells for the integer number s
    of cells the jump moved, within one cell of S_R * 0.01 - dx/2.
    """
    tube = SodShockTube(n_frames=2, t_start=0.1, t_end=0.11)
    early, late = tube.solution(0.1)["pressure"], tube.solution(0.11)["pressure"]
    dx, speed = tube.grid.spacing[0], tube.speeds["shock"]
    flagged = np.flatnonzero(shock_mask(early[0]))
    assert flagged.size == 2 and flagged[1] == flagged[0] + 1
    assert abs((flagged[0] + 1) * dx - (0.5 + speed * 0.1)) <= dx
    score = _score(early, late, spacing=dx)
    assert abs(score - (speed * 0.01 - 0.5 * dx)) <= dx
