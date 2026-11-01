# `shock_set_distance`'s card miscounts a half-cell shift and misreads the high-pass filters

**Category:** documentation
**Priority:** low — no number is wrong; two readings of the numbers are
**Status:** open.

## Context

Two readings on `metrics/shock_set_distance/card.md` disagree with what the shared detector
`shock_mask` does, as measured by the agent that built `shock_mask_overlap` (findings 006 and 017,
2026-10-31) and confirmed independently by that bundle's adversarial reviewer.

1. **The half-cell shift.** The card says a half-cell sub-pixel shift "places the step on a cell
   centre, which flags three cells instead of two and scores a third of a cell". The score is right
   and the cell count is not: the shifted field flags one cell. With the reference's two cells
   {1382, 1383} against the candidate's {1383}, the average symmetric distance is
   (1 + 0 + 0) / 3 = 1/3 cell; three flagged cells would give 1/5.
2. **The high-pass filters.** The card reads the high-pass results as the shock being removed. The
   filters keep the jump (0.20 of 0.203 on Sod) but raise the pre-shock plateau to 0.24 to 0.51, so
   the pressure ratio across the intact shock falls to 1.84, 1.80 or 1.40 against the detector's
   threshold of 1.805. A uniform offset of 0.2 does the same (ratio 1.68). The detector is erased by
   any operator that raises the pressure level without removing the jump.

## Evidence

`results/shock_mask_overlap_1793494245` (Sod, 10 frames): the half-cell shift gives a Dice
coefficient of 2/3 in every frame, which with a two-cell reference means one flagged candidate cell.
The off-run scripts `halfcell.py` and `check_crit.py` are kept in that agent's log archive.

## What would settle it

Correct both readings on the card, by its owner. The second also bears on any future degradation
that adds a bias to a Sod field.
