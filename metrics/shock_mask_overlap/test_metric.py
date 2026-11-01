"""Tests for the Dice coefficient of two shock masks.

The registry-wide contract (symmetry, one finite float, shape rejection, float32 agreement,
the declared non-monotone response to blur) lives in ``tests/test_metric_contract.py``, and
the detector's own threshold and wall handling are tested with ``shock_set_distance``. These
test what is specific to this bundle: the Dice coefficient of the flagged cells, its
saturation once a thin shock has moved past its own width, the empty-set convention, the
channel average, and the exact Sod solution.
"""

from __future__ import annotations

import numpy as np
import pytest

from fmeval.data.analytic import SodShockTube
from metrics.shock_set_distance.metric import shock_mask
from tests.conftest import make_ctx

from .metric import REFERENCE_MASKS, shock_mask_overlap

#: A pressure step on eight cells, high on the left as in Sod's tube. Its ratio of 10 exceeds
#: the detector's 1.805, so cells 3 and 4, on either side of the jump, are flagged.
STEP = np.array([[1.0, 1.0, 1.0, 1.0, 0.1, 0.1, 0.1, 0.1]])


def _score(reference: np.ndarray, candidate: np.ndarray) -> float:
    return shock_mask_overlap(reference, candidate, ctx=make_ctx(reference.shape[1:]))


def _shifted(cells: int) -> np.ndarray:
    """The step moved ``cells`` to the right, padded with the high state on the left."""
    return np.concatenate([np.ones((1, cells)), STEP[:, :STEP.shape[1] - cells]], axis=1)


def test_worked_example_matches_the_card():
    """The example in the card's Intuition section: the step moved one cell.

    The reference flags cells 3 and 4, the candidate cells 4 and 5. They share one cell, so
    by Taha & Hanbury (2015), BMC Med. Imaging 15, 29, Eq. (6), Dice = 2 * 1 / (2 + 2) = 0.5.
    """
    assert _score(STEP, _shifted(1)) == pytest.approx(0.5)


def test_a_shock_moved_past_its_width_scores_zero_however_far():
    """Moved two cells, the flagged pairs {3, 4} and {5, 6} share no cell: 2 * 0 / (2 + 2) = 0.
    Moved three cells, {3, 4} and {6, 7}, the score is the same 0, though the miss is half as
    far again. Overlap cannot tell a near miss from a far one (Taha & Hanbury 2015, BMC Med.
    Imaging 15, 29, discussion of small segments)."""
    assert _score(STEP, _shifted(2)) == 0.0
    assert _score(STEP, _shifted(3)) == 0.0


def test_empty_sets_score_one_together_and_zero_alone():
    """No shock in either field is agreement, 1 (the convention of issues/120). A shock in one
    field only shares no cell with the empty set: 2 * 0 / (2 + 0) = 0, from the formula."""
    flat = np.full((1, 8), 0.55)
    assert _score(flat, flat + 0.1) == 1.0
    assert _score(STEP, flat) == 0.0
    assert _score(flat, STEP) == 0.0


def test_channels_are_averaged():
    """Two channels: the step against the step moved one cell, 0.5, and two flat fields, 1.
    The mean is (0.5 + 1) / 2 = 0.75."""
    flat = np.full((1, 8), 0.55)
    reference = np.concatenate([STEP, flat])
    candidate = np.concatenate([_shifted(1), flat])
    assert _score(reference, candidate) == pytest.approx(0.75)


def test_a_shock_inside_a_cell_is_marked_as_one_to_three_cells():
    """A jump inside a cell gives that cell an intermediate value, so the detector's ratio of
    1.805 between a cell's two neighbours can mark one, two or three cells, not always two.

    Ratio-10 step, cell 4 averaged with the jump 40% into it: 0.4 * 1 + 0.6 * 0.1 = 0.46.
    Cell 3 sees 1 / 0.46 = 2.17, cell 4 sees 1 / 0.1 = 10, cell 5 sees 0.46 / 0.1 = 4.6: three
    cells. Sod's ratio, 0.303 over 0.1, with the middle cell at 0.175: cell 2 sees
    0.303 / 0.175 = 1.73, cell 3 sees 3.03, cell 4 sees 0.175 / 0.1 = 1.75: one cell. Against
    the reference's sharp pair {3, 4} that single cell scores 2 * 1 / (2 + 1) = 2/3."""
    averaged = np.array([1.0, 1.0, 1.0, 1.0, 0.46, 0.1, 0.1, 0.1])
    assert np.flatnonzero(shock_mask(averaged)).tolist() == [3, 4, 5]
    sharp = np.array([[0.303, 0.303, 0.303, 0.303, 0.1, 0.1, 0.1, 0.1]])
    mixed = np.array([[0.303, 0.303, 0.303, 0.175, 0.1, 0.1, 0.1, 0.1]])
    assert np.flatnonzero(shock_mask(mixed[0])).tolist() == [3]
    assert _score(sharp, mixed) == pytest.approx(2.0 / 3.0)


def test_a_field_without_its_channel_axis_is_rejected():
    """``(8,)`` instead of ``(1, 8)``: read as eight channels of one cell each, no cell could be
    flagged and the step against its one-cell shift would score a perfect 1, not 0.5."""
    with pytest.raises(ValueError, match="grid"):
        shock_mask_overlap(STEP[0], _shifted(1)[0], ctx=make_ctx(STEP.shape[1:]))


def test_a_non_finite_field_scores_nan():
    """A pressure that is NaN or infinite anywhere is not a state the detector can read. Without
    this rule a NaN candidate against a smooth reference would flag nothing and score a
    perfect 1."""
    flat = np.full((1, 8), 0.55)
    broken = flat.copy()
    broken[0, 2] = np.nan
    assert np.isnan(_score(flat, broken))
    assert np.isnan(_score(broken, flat))
    assert np.isnan(_score(STEP, np.where(STEP > 0.5, np.inf, STEP)))


def test_the_reference_masks_are_cached_for_the_frame():
    """The reference's masks are computed once and reused for every candidate of the frame:
    a cached mask is read, not recomputed. A cache holding the step's mask scores a flat
    reference against the step as 1, which only the cached mask can give."""
    ctx = make_ctx(STEP.shape[1:])
    assert shock_mask_overlap(STEP, STEP, ctx=ctx) == 1.0
    assert len(ctx.cache[REFERENCE_MASKS]) == 1
    assert shock_mask_overlap(np.full((1, 8), 0.55), STEP, ctx=ctx) == 1.0


def test_on_the_exact_sod_solution_it_scores_the_moving_shock():
    """The exact Sod solution at t = 0.1 against itself and against t = 0.1 + 2e-5 on 2048
    cells. The shock speed is 1.75216 (the reader's ``speeds``), so at t = 0.1 the shock sits
    at x = 0.5 + 0.175216, 2048 x - 0.5 = 1382.34 cells: between the centres of cells 1382 and
    1383, which are flagged. 2e-5 moves it 3.5e-5, 0.07 of a cell of width 1/2048, to 1382.41,
    still between the same two centres, so the flagged pair is unchanged: 1. Over 0.01 it
    moves 35.9 cells, and no flagged cell is shared: 0."""
    tube = SodShockTube(n_frames=2, t_start=0.1, t_end=0.11)
    early = tube.solution(0.1)["pressure"]
    assert _score(early, early) == 1.0
    assert _score(early, tube.solution(0.1 + 2e-5)["pressure"]) == 1.0
    assert _score(early, tube.solution(0.11)["pressure"]) == 0.0


def test_a_pressure_offset_erases_a_shock_in_the_right_place():
    """The detector reads ratios, so a uniform offset lowers the ratio across an exact shock.
    Sod's post- and pre-shock pressures are 0.30313 and 0.1. With 0.15 added the ratio is
    0.45313 / 0.25 = 1.81, still above 1.805: the same cells, 1. With 0.2 added it is
    0.50313 / 0.3 = 1.68: no shock in the candidate, 0, with the shock exactly in place."""
    tube = SodShockTube(n_frames=2, t_start=0.1, t_end=0.11)
    pressure = tube.solution(0.1)["pressure"]
    assert _score(pressure, pressure + 0.15) == 1.0
    assert _score(pressure, pressure + 0.2) == 0.0
