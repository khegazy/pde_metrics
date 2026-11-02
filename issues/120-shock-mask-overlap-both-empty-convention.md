# The score `shock_mask_overlap` gives two empty shock sets is a convention

**Category:** method
**Priority:** unset
**Status:** open. The metric is built with the convention labelled; what would replace it is
open.

## Context

`shock_mask_overlap` detects the shocked cells of each pressure field with the detector of
`shock_set_distance` and reports the Dice coefficient of the two sets,
`2 |A n B| / (|A| + |B|)` (Taha and Hanbury 2015, *BMC Med. Imaging* 15, 29, Eq. 6). When
exactly one set is empty the formula gives 0 and needs no convention. When both are empty it is
0/0, and the metric must still return one finite number. It returns **1**: both fields agree
that there is no shock.

No source fixes this value for this use. Maier-Hein et al. (2024, *Nature Methods* 21, 195-212,
Suppl. Note 2.3) recommend setting an undefined metric value to the worst possible value, which
for the Dice coefficient is 0; I found no rule there specific to an empty reference together with
an empty prediction (the arXiv HTML copy 2206.01653v8 was read through a fetch tool; its Suppl.
Note 2.4, on empty references in object detection, was cut off in the copy read). Scoring 0 would
charge a smooth prediction of a smooth reference as heavily as a missed shock, which is why the
metric does not. The convention matches the first convention of `shock_set_distance`, which
scores two empty sets as a perfect 0 (issue 102).

Where it matters: every frame or region in which the reference holds no shock. On
`sod_shock_tube` every frame of the reference has a shock, so no evidence row uses the
convention; on a shocklet dataset (issue 002) a model that smooths every shocklet away would
score 1 on the frames with none and 0 on the others.

## The choice to be made

1. **1 (now).** Agreement on "no shock" is perfect agreement.
2. **0, the worst value**, following Maier-Hein et al. (2024). Every smooth-on-smooth frame then
   scores as a total failure.
3. **NaN**, leaving the frame out of the analysis. This keeps the Dice coefficient a measure of
   overlap only, but the repository's contract tests require a finite number on every synthetic
   input, and a frame without a shock would vanish from the rank statistics.
4. **Report detection separately**: NaN as in 3, plus a second number counting the frames with
   a missed or invented shock, as issue 102 suggests for the distance.

Options 2 to 4 change the registered number of every row where both sets are empty, so the
choice is a decision for a person; it should be made together with issue 102, so the two shock
metrics treat an empty set alike.

## Related

Written with `shock_mask_overlap`, 2026-10-31. Issue 102 records the empty-set and
non-positive-pressure conventions of `shock_set_distance`, whose detector this metric imports.
