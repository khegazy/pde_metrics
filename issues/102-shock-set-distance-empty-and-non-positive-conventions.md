# The scores `shock_set_distance` gives an empty shock set and a non-positive pressure are conventions

**Category:** method
**Priority:** unset
**Status:** open. The metric is built with three conventions labelled; what would replace them is
open.

## Context

`shock_set_distance` detects the shocked cells of each pressure field with the pressure-jump
criterion of Schaal and Springel (2015, *MNRAS* 446, 3992, Sect. 2.3.2) and reports the average
symmetric surface distance between the two sets (Yeghiazaryan and Voiculescu 2018, *J. Med.
Imaging* 5(1), 015006, Sect. 2.3.2). The distance is undefined when a set is empty, and the
detector's ratio is undefined where the pressure is not positive. The metric must still return
one finite number, so it fixes three values that no source fixes for this use.

1. **Both sets empty: 0.** Both fields agree there is no shock. A segmentation benchmark would
   call the distance undefined and, by the rule below, score it as the worst value; for a shock
   metric that would charge a smooth prediction of a smooth reference as heavily as a missed
   shock, which is why the metric does not.
2. **One set empty: the length of the domain's diagonal.** Maier-Hein et al. (2024, *Nature
   Methods* 21, 195-212, Suppl. Note 2.3) recommend setting an undefined value to the worst
   possible value and name the image diagonal for distance-based metrics. The rule is theirs;
   applying it to a missing shock is this repository's. It makes the value a flag rather than a
   distance: on `sod_shock_tube` every blur that smears the shock beyond the detector's reach
   scores the same diagonal whatever its width.
3. **A cell beside a non-positive pressure is never flagged.** A pressure ratio, and so a Mach
   number, exists only between two positive pressures, so the test
   `max(p-, p+) >= R min(p-, p+)` is applied only where `min(p-, p+) > 0`. The cost is that a
   prediction which breaks positivity away from the shock scores as if smooth there; positivity
   is an admissibility property for a separate check. The alternative, flagging every cell
   beside a non-positive pressure as though the ratio were infinite, was tried and rejected
   because it inverts the ranking: measured on the exact Sod pressure at t = 0.1 (adversarial
   review of 2026-10-31, `.agent/adversary/probe5.py` of the builder's records), an all-zero or
   all-negative candidate then scored 0.280 of the diagonal, a fully flagged field covering the
   true shock, while the exact shock in the right place smeared by a 3-cell Gaussian scored the
   worst value, 1. A third option, returning NaN whenever a field has a non-positive value,
   would fail the repository's contract tests, which run every metric on a signed synthetic
   field and require a finite number.

A field that is NaN or infinite anywhere is not covered by these conventions: the metric returns
NaN, as a pointwise error would.

## What would settle it

A published treatment of empty sets for boundary distances used as a model-selection score
rather than a benchmark aggregate, or a decision for a stated purpose: for example returning
NaN on one empty set and reporting the fraction of frames with a missed or invented shock as a
separate number, which would keep the distance a distance. Either changes the registered
number of every row where a set is empty, so it is a decision for a person.

## Related

Written with the first shock metric, `shock_set_distance`, 2026-10-30. The detector it
contains is the input the shock-mask overlap idea (`docs/ideas/shock_geometry/shock_mask_overlap.md`)
waits on.
