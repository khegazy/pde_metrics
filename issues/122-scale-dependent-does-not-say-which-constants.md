# The schema's `scale_dependent` does not say whether the constant may be negative

**Category:** documentation
**Priority:** low
**Status:** open, needs an owner decision.

## Context

`fmeval/cards/schema.py` defines `scale_dependent` as "whether the value changes when both fields
are multiplied by the same constant", with no sign. A metric that reads a ratio of positive
quantities (`shock_set_distance`, `shock_mask_overlap`) is unchanged by a positive constant, which
is a change of units, but not by a negative one, which empties both shock masks. Both bundles
declare `false` with a comment restricting it to positive constants.

Found by the adversarial review of `shock_mask_overlap` (finding 018, 2026-10-31).

## The choice to be made

Whether the field means a change of units (a positive constant) or any constant. The first matches
how both bundles use it; the second would make both declarations wrong.
