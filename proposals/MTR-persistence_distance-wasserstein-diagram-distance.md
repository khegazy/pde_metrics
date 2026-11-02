---
type: MTR
kind: variant of persistence_distance
related: ["metrics/persistence_distance", "metrics/max_error", "metrics/mse"]
seen_in: "Skraba & Turner 2020, arXiv:2006.16824, Definition 2.5 and Theorem 4.6"
doi: "10.48550/arXiv.2006.16824"
found_by: "persistence_distance, 2026-10-31"
---

# MTR: p-Wasserstein distance between persistence diagrams

## What it measures

The total cost of turning one field's persistence diagram into the other's, every feature
counted, rather than the single worst mismatch the bottleneck distance reports. A prediction
that gets every vortex's strength slightly wrong, or that adds many weak spurious features,
scores worse than one that gets one feature wrong by the same largest amount; the bottleneck
distance cannot tell them apart.

## Definition

Per homology dimension k, with matchings M between the diagrams (points free to match the
diagonal) and the l_p ground norm (Skraba & Turner 2020, Definition 2.5):

    W_p(D_k(f), D_k(g)) = inf_M ( sum_{(x,y) in M} ||x - y||_p^p )^(1/p)

and the total over dimensions is ( sum_k W_p(D_k(f), D_k(g))^p )^(1/p), whose p -> inf limit is
the bottleneck distance `persistence_distance` registers (their Eq. 1). Their Theorem 4.6
(cellular Wasserstein stability) bounds W_p(Dgm(f), Dgm(g)) by ||f - g||_p, the p-norm over all
cells of a finite CW complex; Theorem 5.1 carries it to images with a constant depending only on
the dimension. `gudhi.wasserstein.wasserstein_distance` computes it (its `order` is p, its
`internal_p` the ground norm), with `pot` already a core dependency.

## Relation to existing work

A variant of `persistence_distance`, which is its p = inf case. Its stability bound is the
cell-sum p-norm, so W_1 relates to `mae` and W_2 to `mse` scaled by the cell count, the way the
bottleneck relates to `max_error`. Not in the catalog or `docs/ideas/`.

## How it could be tested

On the same ladder as `persistence_distance`: `additive_noise` should separate it most from the
bottleneck, since noise adds many short-lived points each costing a little. Measured by me on a
synthetic 64 x 64 field (the building agent's script `try_gudhi.py`, kept in its private log archive): W_1 on H1 rose from 0.40 to 152 between
noise amplitudes 0.001 and 0.5 (380 times) while the H1 bottleneck rose from 0.0039 to 0.96 (250
times). Cost: about 0.6 s per H0/H1 pair at 64 x 64 with 1100 points against 0.07 s for the
bottleneck, so at 256 x 256 it needs measuring before a full run.

## Why it is helpful

Its gradient, where it exists, moves every matched point rather than the one pair the bottleneck
depends on, which makes it the better candidate for a training loss (my reasoning, not a
source's), and its stability theorem is in the cell-sum norms the repository's pointwise
controls use.

## References

- Skraba, P. & Turner, K. (2020). Wasserstein stability for persistence diagrams.
  arXiv:2006.16824. Definition 2.5, Eq. 1, Theorems 4.6 and 5.1.
  <https://doi.org/10.48550/arXiv.2006.16824>
