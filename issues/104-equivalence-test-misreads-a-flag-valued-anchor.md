# The blindness test reads a metric whose anchor is a flag value as blind to axes it follows

**Category:** method
**Priority:** unset
**Status:** open, needs a decision on how such a metric's damage is scaled.

## Context

The analysis lists an axis under `blind_axes` when the upper confidence bound of the metric's
largest damage on it lies below `BLINDNESS_MARGIN`, 0.05 on the damage scale
(`fmeval/analysis.py`: `SENSITIVITY_FRACTION / 2`, an equivalence test in the sense of Lakens
2017, Soc. Psychol. Personal. Sci. 8(4):355-362). Damage is the metric's departure from the
clean value as a fraction of its value on the anchor, the field's spatial mean
(`judgements/001`).

A metric that scores "no feature present" with a fixed worst-case value has that value as its
anchor, because the spatial mean contains no feature. `shock_set_distance` scores a field with
no shock at the domain's diagonal (the convention of `issues/102`), so its damage is the
distance between shock sets as a fraction of the domain's length. Any real displacement of a
shock is a small fraction of that, and lands under the margin.

Found by the agent that built `shock_set_distance` (2026-10-31, PR #22); the numbers below were
re-read from its evidence before this issue was filed.

## Evidence

`metrics/shock_set_distance/_generated/fingerprint.json` on branch `metric/shock_set_distance`
(run `shock_set_distance_1793350452`, `sod_shock_tube`, 10 frames, at `d9dcb84`, clean tree):

| axis | rho | largest damage | listed in `blind_axes` |
|---|---|---|---|
| `translate_x` | 1.0 | 0.00757 | yes |
| `translate_subpixel` | 0.986 | 0.00171 | yes |

The anchor value is 1.0, the length of the unit tube. Under `translate_x` the metric's values are
exactly (s − ½) cells for a shift of s cells, so it follows the axis perfectly, yet the profile
reports it as blind to it. The same will happen to any metric whose value without a feature is a
worst-case convention: shock-mask overlap, an eddy census, a pair-correlation function of
features.

## Options

1. A metric declares a natural scale for its damage (here one cell, or the shock's own width)
   that replaces the anchor for the blindness test only.
2. A metric declares its no-feature flag value, and an anchor equal to it excludes the metric
   from the blindness test, which then reports "not applicable" rather than "blind".
3. Leave the test as it is and document that `blind_axes` is unreliable for flag-valued metrics.

Which one changes what "blind" means for a family of metrics, so it is a person's decision
(or a judgement, under `AGENTS.md` §1, after researching how equivalence margins are set when the
reference scale is a convention).

## Related

- `issues/102` (the empty-set conventions of `shock_set_distance`, on its branch)
- `judgements/001-damage-anchor-is-the-spatial-mean.md`
