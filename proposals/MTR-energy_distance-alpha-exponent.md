---
type: MTR
kind: variant of energy_distance
related: ["energy_distance"]
seen_in: "Székely & Rizzo 2013, J. Stat. Plann. Inference 143(8), 1249-1272"
doi: "10.1016/j.jspi.2013.03.018"
found_by: "energy_distance, 2026-10-30"
---

# MTR: Generalised energy distance with exponent alpha

## What it measures

The energy distance with the distance |x - y| raised to a power alpha in (0, 2), a one-parameter
family that changes how strongly large separations between increments are weighed.

## Definition

E^(alpha)(X, Y) = 2E|X - Y|^alpha - E|X - X'|^alpha - E|Y - Y'|^alpha, which is nonnegative and
zero only for equal distributions for every 0 < alpha < 2, and reduces to a comparison of means
at alpha = 2 (Székely & Rizzo 2013, Proposition 2, Eqs. (5.1)-(5.2)). In kernel terms it is the
maximum mean discrepancy with the fractional-Brownian-motion covariance kernel
k_q(z, z') = (|z|^q + |z'|^q - |z - z'|^q)/2 (Sejdinovic et al. 2013, Ann. Statist. 41(5),
2263-2291, Eq. (4.2)). The registered energy_distance is alpha = 1.

## Relation to existing work

energy_distance fixes alpha = 1. Sejdinovic et al. (2013) report that other members of this
kernel family can give more powerful two-sample tests than alpha = 1 (abstract and their
experimental section; I read the full text but did not check which alpha won on which problem).
On the line, only alpha = 1 has the cumulative-distribution form used for the exact sort-based
evaluation, so another alpha costs O(N^2) pairs or an approximation.

## How it could be tested

The same ladder as energy_distance. The interesting question is whether a larger alpha (closer
to 2) restores sensitivity to the tails the alpha = 1 form suppresses, which the tail-only
degradation in EXP-energy_distance-tail-only-degradation would answer.

## Why it is helpful

It turns the idea page's pitfall ("the kernel and its bandwidth must be fixed once and
declared") into a measured question: alpha is the one free parameter, and a sweep would show
how much the tail weakness depends on it. Any alpha would have to be fixed once, never tuned
per model.

## References

- Székely, G. J. & Rizzo, M. L. (2013). Energy statistics: A class of statistics based on
  distances. J. Stat. Plann. Inference 143(8), 1249-1272. doi:10.1016/j.jspi.2013.03.018.
- Sejdinovic, D., Sriperumbudur, B., Gretton, A. & Fukumizu, K. (2013). Equivalence of
  distance-based and RKHS-based statistics in hypothesis testing. Ann. Statist. 41(5),
  2263-2291. doi:10.1214/13-AOS1140.
