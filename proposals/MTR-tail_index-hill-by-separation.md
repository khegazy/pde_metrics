---
type: "MTR"
kind: "variant of tail_index"
related: ["metrics/tail_index", "metrics/increment_w1_by_separation", "metrics/increment_flatness"]
seen_in: "agent's own"
doi: "none"
found_by: "tail_index, 2026-10-30"
---

# MTR: Hill estimate of the increments at every octave of separation

## What it measures

How the tail of the increment distribution changes with the separation over which the increment
is taken. Intermittency is a statement about that change (issues/036, option 3, argues the same
for flatness): the increment distribution is close to Gaussian at large separations and develops
heavier shoulders at small ones. A single-separation tail estimate cannot express it.

## Definition

My own idea, combining two built pieces. For each octave separation l = 1, 2, 4, ... up to half
the smallest side (the separations `increment_w1_by_separation` uses), take
`increments(channel, axis, separation=l)` from `metrics/increment_flatness`, and compute
`tail_index`'s Equation (2) at k = ceil(sqrt(n)) (Hill estimator in the form of Boucheron & Thomas
2015, Electron. J. Stat. 9(2), Sect. 1; k from Clauset et al. 2009, SIAM Rev. 51(4), Sect. 3.5).
The curve over l is the companion; a registered number would be a convention (for example the
value at l = 1, which is `tail_index` itself, or the slope against log l) and would need an issue
like issues/098.

## Relation to existing work

`tail_index` is this curve at l = 1 only, with a curve over k instead. `increment_flatness` is a
fourth-moment statistic at l = 1. `increment_w1_by_separation` compares whole increment
distributions over the same octaves pairwise. No built or planned metric reads the tail shape as a
function of scale.

## How it could be tested

The smoothing axes (`gaussian_blur`, `box_blur`) change the increments at separations below the
blur width far more than above it, so the curve should depart from the reference's at small l
first; that is a per-coordinate property, so it would be reported in the per-coordinate tables
rather than pre-registered for a registered number.

## Why it is helpful

It turns the tail estimate into a statement about intermittency across scales, which is what the
turbulence literature means by the word, and it reuses two built functions without new numerics.

## References

- Boucheron, S. & Thomas, M. (2015). *Electronic Journal of Statistics* 9(2), 2751-2792.
  doi:10.1214/15-EJS1088.
- Clauset, A., Shalizi, C. R. & Newman, M. E. J. (2009). *SIAM Review* 51(4), 661-703.
  doi:10.1137/070710111.
