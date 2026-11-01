---
type: "MTR"
kind: "variant of tail_exceedance"
related: ["metrics/tail_exceedance", "metrics/increment_flatness", "docs/ideas/distributional/tail_index_estimators.md"]
seen_in: "agent's own"
doi: "none"
found_by: "tail_exceedance, 2026-10-31"
---

# MTR: Tail exceedance at a fixed multiple of the reference's increment rms

## What it measures

The same frequency bias as `tail_exceedance`, the prediction's count of extreme one-cell
increments over the reference's, but with the extreme level fixed at a multiple of the reference's
own increment rms (for example three) rather than at the reference's square-root-of-n-th largest
increment. It is the form the idea page gave as its example.

## Definition

For each channel and axis, $\sigma_\delta$ is the rms of the reference's one-cell increments, and
the event is $\lvert\delta\rvert \ge c\,\sigma_\delta$ with $c$ fixed once. The frequency bias is
the candidate's count over the reference's (WWRP/WCRP JWGFVR, "Forecast verification: methods,
issues and FAQ", section "Frequency bias (bias score)", which numbers no equations), and the curve
runs over $c$. The level $c$ in rms units is my own suggestion, not from a source.

## Relation to existing work

`tail_exceedance` (built) fixes the level as a percentile of the reference, so the reference's
event rate is the same on every field (`judgements/005`). This variant lets the rate vary with the
shape of the reference's distribution: measured on `kinet_re5e4` frames 2000, 6000 and 10000, the
reference's rate at $c = 3$ is 0.0145 to 0.0315 across fields and frames, against 0.0027 for a
Gaussian. Its curve over $c$ would therefore show how much heavier than Gaussian the reference's
increments are, which the percentile form hides by construction.

## How it could be tested

The same ladder axes as `tail_exceedance`: `additive_noise` raises it, `gaussian_blur`, `box_blur`
and `median_blur` lower it. A threshold in rms units saturates later under blur than the
$\sqrt{n}$-th percentile does when $c$ is small, which `issues/118` is about.

## Why it is helpful

It reads directly as "how many increments beyond three standard deviations", the language the
turbulence literature uses for increment distributions normalised by their rms, and its reference
rate itself is an intermittency diagnostic.

## References

- WWRP/WCRP Joint Working Group on Forecast Verification Research. Forecast verification:
  methods, issues and FAQ. <https://jwgfvr.github.io/forecastverification>
