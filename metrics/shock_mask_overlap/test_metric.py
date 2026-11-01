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
    cells. The shock speed is 1.75216 (the reader's ``speeds``), so 2e-5 moves the shock
    3.5e-5, 0.07 of a cell of width 1/2048: the flagged pair stays or moves one cell, giving
    1 or 2 * 1 / 4 = 0.5. Over 0.01 it moves 35.9 cells, and no flagged cell is shared: 0."""
    tube = SodShockTube(n_frames=2, t_start=0.1, t_end=0.11)
    early = tube.solution(0.1)["pressure"]
    assert _score(early, early) == 1.0
    assert _score(early, tube.solution(0.1 + 2e-5)["pressure"]) in (1.0, 0.5)
    assert _score(early, tube.solution(0.11)["pressure"]) == 0.0
