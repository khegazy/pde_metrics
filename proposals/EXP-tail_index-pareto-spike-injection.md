---
type: "EXP"
kind: "degradation"
related: ["metrics/tail_index", "metrics/increment_flatness", "docs/ideas/distributional/tail_index_estimators.md"]
seen_in: "agent's own"
doi: "none"
found_by: "tail_index, 2026-10-30"
---

# EXP: Inject sparse spikes with power-law amplitudes of a known exponent

## What the experiment is

My own idea. A degradation that adds to a fixed, small fraction of cells (drawn per frame from
the seeded generator) a spike whose amplitude is drawn from a Pareto distribution with
P(A > a) = (a / a_0)^-alpha, with a_0 a fixed multiple of the field's fluctuation rms and a random
sign. The severity is the exponent alpha, decreasing (a smaller alpha is a heavier tail), or the
fraction of cells at fixed alpha.

## What it tests

It changes the tail of the one-cell increments in a controlled and known way: a spike of
amplitude A makes increments of size A on both sides, so once the spikes dominate the largest
increments the increments' tail is a power law with exponent alpha, and the Hill estimate at
k = ceil(sqrt(n)) has a known target, 1/alpha (Boucheron & Thomas 2015, Electron. J. Stat. 9(2),
Sect. 1). No current degradation has a known answer for a tail estimate: `additive_noise` moves
the tail toward a Gaussian, whose index is zero, but where the reference sits relative to that
depends on the field.

## Metrics it would test

`tail_index` (a known target), `increment_flatness` (flatness grows without bound as alpha falls
toward 4, where the fourth moment stops existing), `increment_w1` and the planned tail-exceedance
and peaks-over-threshold tier of the idea page.

## Why it is helpful

It is the only kind of experiment in which a tail estimator's number can be checked against a
known value on real data rather than on an iid synthetic sample, and it models a real failure:
a surrogate that produces rare spurious spikes.

## Cost and requirements

A new degradation bundle, `stochastic` family, about thirty lines of code; no data, no licence.
It must not be calibrated (it draws at random) and must declare which properties it preserves
(none of single_point_statistics, amplitude spectrum or shape).

## References

- Boucheron, S. & Thomas, M. (2015). Tail index estimation, concentration and adaptivity.
  *Electronic Journal of Statistics* 9(2), 2751-2792. doi:10.1214/15-EJS1088.
