---
type: MTR
kind: variant of persistence_wasserstein
related: ["metrics/persistence_wasserstein", "metrics/persistence_distance", "metrics/mse"]
seen_in: "Cohen-Steiner, Edelsbrunner, Harer & Mileyko 2010, Found. Comput. Math. 10, 127-139, Sects. 3-4; giotto-tda 0.4.0, gtda.diagrams.PairwiseDistance"
doi: "10.1007/s10208-010-9060-6"
found_by: "persistence_distance, 2026-10-31; narrowed by metrics-topology-shocks, 2026-11-04"
---

# MTR: 2-Wasserstein distance between persistence diagrams

The 1-Wasserstein distance with the L-infinity ground norm, GUDHI's default, is built as
`persistence_wasserstein` (2026-11-04). What remains of this proposal is the exponent p = 2.

## What it measures

The same matching of every feature of one field's persistence diagram to the other's as
`persistence_wasserstein`, with each matched cost squared before summing, so a few large
mismatches weigh more against many small ones than at p = 1 and less than in the bottleneck
distance of `persistence_distance`.

## Definition

Per homology dimension k, with matchings M between the diagrams (points free to match the
diagonal) and the L-infinity ground norm (Cohen-Steiner et al. 2010, Sect. 3, "Wasserstein
distance", which sums the p-th powers over all dimensions):

    W_2(D_k(f), D_k(g)) = inf_M ( sum_{(x,y) in M} ||x - y||_inf^2 )^(1/2)

and the total over dimensions ( sum_k W_2(D_k(f), D_k(g))^2 )^(1/2) (Skraba & Turner 2020,
arXiv:2006.16824v7, Definition 2.5). giotto-tda's `PairwiseDistance(metric="wasserstein")`
defaults to this exponent and combines the dimensions by a 2-norm, the same total. In code it is
`persistence_wasserstein` with `ORDER = 2.0`: the shared `diagram_distances` and its `wasserstein`
already take the exponent from that constant.

## Relation to existing work

The p = 2 member of the family whose p = 1 member is `persistence_wasserstein` and whose limit
p -> inf is `persistence_distance`. Cohen-Steiner et al. (2010), Sect. 4, suggest W_2 for
clustering gene-expression time series; Skraba & Turner's Theorem 4.6 bounds W_2 with the L2
ground norm by the L2 norm of the difference over the cells of the complex, the analogue for
`mse` of the bound that ties `persistence_distance` to `max_error`.

## How it could be tested

On the same ladder as `persistence_wasserstein`, beside it. Cost, measured on one 256 x 256
vorticity frame of `kinet_re5e4` with Hera at a relative error of 1e-4 (the agent's scratch
script, 2026-11-04, not kept): 5 to 13 s for H0 and 17 to 68 s for H1 on blurred and noisy candidates,
four to five times the p = 1 cost, so a full run of the ladder at 256 needs a smaller grid or fewer frames.

## Why it is helpful

It is the other software default of the field (giotto-tda), so a reader from the
machine-learning side of topological data analysis expects it; and it sits between the
sum of `persistence_wasserstein` and the maximum of `persistence_distance` in how much a single
large mismatch dominates.

## References

- Cohen-Steiner, D., Edelsbrunner, H., Harer, J. & Mileyko, Y. (2010). Lipschitz functions have
  Lp-stable persistence. *Found. Comput. Math.* 10(2), 127-139. Sects. 3-4 (authors' copy read).
  <https://doi.org/10.1007/s10208-010-9060-6>
- Skraba, P. & Turner, K. (2020). Wasserstein stability for persistence diagrams.
  arXiv:2006.16824v7. Definition 2.5, Remark 2.6, Theorem 4.6.
  <https://doi.org/10.48550/arXiv.2006.16824>
- giotto-tda 0.4.0, `gtda/diagrams/distance.py`, `PairwiseDistance` (documentation read).
