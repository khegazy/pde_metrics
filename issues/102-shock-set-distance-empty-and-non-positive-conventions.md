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
3. **A non-positive pressure is flagged as shocked.** The test is written
   `max(p-, p+) >= R min(p-, p+)`, which holds whenever the smaller neighbour is zero or
   negative: the pressure ratio across it is unbounded. A non-positive pressure is not a
   thermodynamic state, so the alternative, not flagging it, would let a prediction that
   breaks positivity score as if smooth there.

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
