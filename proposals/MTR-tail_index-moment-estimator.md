---
type: "MTR"
kind: "variant of tail_index"
related: ["metrics/tail_index", "docs/ideas/distributional/tail_index_estimators.md"]
seen_in: "Dekkers, Einmahl & de Haan 1989, Ann. Stat. 17(4), 1833-1855"
doi: "10.1214/aos/1176347397"
found_by: "tail_index, 2026-10-30"
---

# MTR: Moment (Dekkers-Einmahl-de Haan) estimator of the extreme-value index of increments

## What it measures

The extreme-value index gamma of the absolute one-cell increments, like `tail_index`, but with an
estimator that is consistent for every sign of gamma, not only for power-law tails (gamma > 0).
On the kinet fields the far tail of the increments is lighter than a Gaussian's (finding 003 of
the tail_index agent), which suggests gamma <= 0 there, where the Hill estimator has no
guarantee; the moment estimator is the standard generalisation built for exactly that case.

## Definition

With the same order statistics as `tail_index` and M_j = (1/k) sum_{i=1..k} (ln X_(i) - ln
X_(k+1))^j, so that M_1 is the Hill estimator, the moment estimator is
gamma_M = M_1 + 1 - (1/2) (1 - M_1^2 / M_2)^-1. The formula is quoted from memory of the
literature and must be checked against the paper before it is built: the paper's abstract (read
through Crossref) says only that it generalises Hill's estimator to the index of an extreme-value
distribution and is consistent and asymptotically normal; the full text, and so the equation
number, was not read.

## Relation to existing work

`tail_index` registers M_1 at k = ceil(sqrt(n)). This variant reuses the same sort and the same
k and adds one more moment, so it would be a sibling bundle importing `tail_index_curve`'s order
statistics. The peaks-over-threshold tier on the idea page fits a generalised Pareto distribution,
which also covers gamma <= 0 but needs an optimiser; the moment estimator is closed form.

## How it could be tested

`additive_noise`: as the noise dominates, the increments become Gaussian, whose gamma is 0, so the
estimate moves toward the moment estimator's finite-sample value for a Gaussian sample at that
k. A light-tail check (uniform increments, gamma = -1) and a Pareto check (gamma = 1/alpha) would
be the hand-computable unit tests.

## Why it is helpful

It removes the main interpretive limitation of `tail_index` on smooth, well-resolved fields:
there it could report a signed index whose sign says whether the increments' tail is bounded,
exponential-like or power-law, rather than a positive number that is not an index.

## References

- Dekkers, A. L. M., Einmahl, J. H. J. & de Haan, L. (1989). A moment estimator for the index of
  an extreme-value distribution. *The Annals of Statistics* 17(4), 1833-1855.
  doi:10.1214/aos/1176347397 (read: abstract only).
- Boucheron, S. & Thomas, M. (2015). *Electronic Journal of Statistics* 9(2), 2751-2792,
  doi:10.1214/15-EJS1088, Sect. 1: the Hill estimator is consistent exactly when gamma > 0.
