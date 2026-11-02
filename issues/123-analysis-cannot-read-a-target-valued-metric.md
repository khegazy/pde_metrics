# The analysis cannot read a metric with a target value: direction, blindness, damage and zeros

**Category:** method
**Priority:** medium — two metrics declare a target, and neither's profile can be read
**Status:** open.

## Context

A metric that declares `target=` (`spread_skill`, and `tail_exceedance` in pull request #31) is
ordered by its distance from the target, `|log(value / target)|` (`fmeval/analysis.py`,
`_oriented`). Four consequences follow, found by the agent that built `tail_exceedance` and its
adversarial reviewer (findings 021, 022, 025 and 026, 2026-10-31):

1. **Direction.** `summarise_axes` sets the reported `direction` to +1 on every axis
   (`sign = ... if target is None else 1`), meaning "moves away from the target". Which way the
   raw value moved is not recorded, so a declaration that a metric falls cannot be checked.
2. **Blindness.** No damage is built for a target metric, so `_blindness_bound` never runs and
   `blind_axes` is always empty, even for an axis on which the value equals the target exactly.
3. **Damage.** The damage columns are the raw `(v - clean) / span`, so with the clean value 1 and the
   mean-field anchor 0 the damage is `1 - v`. Noise that raises `tail_exceedance` to about 195 reads
   as damage of about -194.
4. **Zeros.** `_oriented` maps a value of 0 to `+inf` on purpose, so the worst level is not dropped.
   `_is_round_off` then keeps only finite values and calls a frame with fewer than two of them
   round-off, so a perfectly ordered frame `(0.3, 0, 0, 0)` gets a NaN rank correlation, and
   `_monotone_fraction` counts it out of order because `inf - inf` is NaN.

## Evidence

On `results/tail_exceedance_1793494833`: `gaussian_blur`, `box_blur` and `median_blur` lower the
raw value from 1 to 0 but read direction +1; `translate_x` gives exactly 1.0 at every level and
frame and is not listed blind; the rank correlation of `gaussian_blur`, `box_blur`, `lowpass_ideal`
and `lowpass_butterworth` is withheld on density and velocity, the axes on which the metric responds
most, and the vorticity value of 0.949 is defined in only 39, 43, 9 and 5 of 161 frames.
`spread_skill` shares the code path and can reach 0; its recorded evidence has not been
re-examined.

## Options

1. Record the raw direction beside the oriented one, and build a blindness bound on the oriented
   scale.
2. Map a zero to a large finite value, or exempt infinities from the round-off guard.
3. Define a target metric's damage on the oriented scale.
