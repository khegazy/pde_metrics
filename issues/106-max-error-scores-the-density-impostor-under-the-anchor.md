# The maximum error scores the density impostor just under the anchor, unexplained

**Category:** method
**Priority:** unset — it changes only how one trap test is read, for one metric on one field
**Status:** open. Measured, not explained.

## Context

`max_error` (pull request 25) reports the largest absolute difference between prediction and
reference. Its damage scale runs from the reference (0) to the field's spatial mean (1,
`judgements/001`), so damage 1 is the reference's own largest deviation from its mean. The
Gaussian impostor (a random field with the reference's energy spectrum) is the trap a
phase-blind metric falls into; a metric that sees phase should score it at a damage well above
the levels a mild degradation reaches.

Found by the agent that built `max_error` (2026-10-31); re-read from its evidence before this
issue was filed.

## Evidence

`metrics/max_error/_generated/fingerprint.json` on branch `metric/max_error`, run
`max_error_1793355020` (`kinet_re5e4`, start 2000, reduction 50, 161 frames, clean tree at
`e4da8d3`):

| field | impostor damage | large-translation probe damage | anchor value (largest deviation from the mean) |
|---|---|---|---|
| density | 0.955 | 0.959 | 0.0386 |
| velocity | 1.597 | 1.612 | 0.0937 |
| vorticity | 1.197 | 1.281 | 0.0169 |

On density both the impostor and the moved copy of the reference score just under the anchor,
where on velocity and vorticity they score well above it.

## A possible explanation (conjecture, not tested)

Density's fluctuation energy sits mostly in four large-scale modes (`CLAUDE.md`, "What exists":
69% at |k| = √2). A field made of a few large-scale waves of fixed amplitude has a largest
excursion close to that of any other phase arrangement of the same waves, so a phase-randomised
or moved copy differs from the reference by about the reference's own largest excursion from its
mean, which is the anchor. If so, the result is a property of density's spectrum, not of the
metric.

## What would settle it

Measure, frame by frame, the distribution of the impostor's worst-cell error against the anchor's
value on density, and the same on a broadband field; if the ratio sits near 1 only on density,
record that on the card and close this issue. No number in the bundle depends on the answer.

## Related

- `judgements/001-damage-anchor-is-the-spatial-mean.md`
- `issues/031` (no ladder level reaches the anchor), which reads the same scale
