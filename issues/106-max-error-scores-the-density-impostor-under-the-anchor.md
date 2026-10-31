# The maximum error scores the density impostor near the anchor; one gap is unexplained

**Category:** method
**Priority:** unset — it changes only how one trap test is read, for one metric on one field
**Status:** open. The cause of a value near 1 is measured; why the harness's median sits below
the per-frame medians is not.

## Context

`max_error` (pull request 25) reports the largest absolute difference between prediction and
reference. Its damage scale runs from the reference (0) to the field's spatial mean (1,
`judgements/001`), so damage 1 is the reference's own largest deviation from its mean. The
Gaussian impostor (a random field with the reference's energy spectrum) is the trap a
phase-blind metric falls into; a metric that sees phase should score it at a damage well above
the levels a mild degradation reaches.

Found by the agent that built `max_error` (2026-10-31); the cause was measured in that bundle's
adversarial review (2026-10-30) and re-run by the agent.

## Evidence

`metrics/max_error/_generated/fingerprint.json` on branch `metric/max_error`, run
`max_error_1793355020` (`kinet_re5e4`, start 2000, reduction 50, 161 frames, clean tree at
`e4da8d3`):

| field | impostor damage | large-translation probe damage | anchor value (largest deviation from the mean) |
|---|---|---|---|
| density | 0.955 | 0.959 | 0.0386 |
| velocity | 1.597 | 1.612 | 0.0937 |
| vorticity | 1.197 | 1.281 | 0.0169 |

On density both the impostor and the moved copy of the reference score near the anchor, where on
velocity and vorticity they score well above it.

## The measured cause

- **Where the extreme sits.** Density's largest departure from its mean is one negative minimum,
  5.46 to 6.51 standard deviations deep on frames 3000, 5000 and 8000. It sits on the strongest
  vortex core: on frames 2500, 5000, 8000 and 10000, |vorticity| there is 5.24σ to 7.59σ, against
  field maxima of 5.47σ to 7.63σ. That a density minimum sits on a vortex core follows from low
  pressure there; this is reasoning from where it sits, not a cited result.
- **What that does to the trap test.** A field unrelated to the reference that lacks this minimum
  differs from the reference there by about the reference's own largest deviation, which is the
  anchor. Over 300 impostor seeds per frame the median damage is 1.015 to 1.024 (10 to 90% about
  0.77 to 1.23); over 300 large shifts it is 1.042 to 1.053.
- **The earlier conjecture is contradicted.** This issue first attributed the result to density's
  energy sitting in a few large-scale modes. By the reviewer's argument, not a measurement, that
  mechanism would give a damage near 4/π ≈ 1.27, the expected largest difference between two
  copies of one wave with a random phase difference, not values near 1.

## What is still open

Why the harness's median over 161 frames, 0.955, sits below the per-frame medians near 1.02 from
300 seeds each. Measuring the harness's own single impostor draw per frame against the 300-seed
distribution of that frame would show whether the harness's seed falls low by chance or something
in the pipeline differs from the stand-alone draw. No number in the bundle depends on the answer.

## Related

- `judgements/001-damage-anchor-is-the-spatial-mean.md`
- `issues/031` (no ladder level reaches the anchor), which reads the same scale
