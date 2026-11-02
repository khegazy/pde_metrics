---
type: MTR
kind: variant of persistence_distance
related: ["metrics/persistence_distance", "docs/ideas/topology/minkowski_functionals.md"]
seen_in: "agent's own; Betti numbers from Skraba & Turner 2020, arXiv:2006.16824 v7, Sect. 2 and Theorem 2.3 (interval decomposition)"
doi: "10.48550/arXiv.2006.16824"
found_by: "persistence_distance, 2026-10-31"
---

# MTR: Distance between Betti curves

## What it measures

How the number of connected pieces and loops of the sublevel set differs between the two fields
at each threshold, integrated over thresholds. It forgets which birth is paired with which death
and so cannot be fooled by the pairing, and it is cheap once the diagrams exist: no matching is
solved.

## Definition

With beta_k(t) the number of diagram points (b, d) of dimension k with b <= t < d, the intervals
of the interval decomposition that contain t (Skraba & Turner 2020, arXiv:2006.16824 v7, Sect. 2
and Theorem 2.3; each interval is [b, d) for a closed sublevel filtration, my reading), the
distance my proposal would register is

    B(f, g) = sum_k integral | beta_k^f(t) - beta_k^g(t) | dt

over the union of the two fields' value ranges, in field units times a count. The integral is
exact on the piecewise-constant curves (sum over the sorted breakpoints). The Euler-characteristic
analogue replaces the per-dimension curves by chi(t) = sum_k (-1)^k beta_k(t); that one belongs to
the Minkowski-functionals idea. The choice of the L1 distance over t is mine.

## Relation to existing work

`persistence_distance` exports `betti_curves` and `euler_characteristic_curve`, so this is a
few lines on top of it. The Euler curve is one of the Minkowski functionals
(`docs/ideas/topology/minkowski_functionals.md`), which is planned; the per-dimension Betti
curves are not in the catalog or the ideas. As a curve on a threshold coordinate it would use the
existing curve companion, but the thresholds differ per field, so a fixed coordinate would need
thresholds in units of the reference's fluctuation RMS about its mean.

## How it could be tested

The `persistence_distance` ladder. `additive_noise` raises the number of pieces and loops at every
threshold, so B should follow it; a whole-cell translation on a periodic grid leaves it exactly
unchanged, as for the diagram.

## Why it is helpful

A cheaper and pairing-free summary of the same diagram, with every feature counted, and the link
between the persistence metric and the planned Minkowski functionals.

## References

- Skraba, P. & Turner, K. (2020). Wasserstein stability for persistence diagrams. arXiv:2006.16824,
  version 7 (2025), Sect. 2 and Theorem 2.3. <https://doi.org/10.48550/arXiv.2006.16824>
