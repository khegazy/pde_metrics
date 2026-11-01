---
type: MTR
kind: variant of wasserstein
related: ["wasserstein", "docs/ideas/optimal_transport/sinkhorn.md"]
seen_in: "agent's own"
doi: "none"
found_by: "wasserstein, 2026-10-31"
---

# MTR: Exact discrete transport between cell histograms on a coarsened grid (considered, not built)

## What it measures

The quadratic Wasserstein distance between the two densities read as one point mass per cell
of a coarsened grid, solved exactly by POT's network simplex (`ot.emd2`), with the squared
distance on the torus as the cost.

## Definition

W_2^2 = min over couplings P with marginals a, b of the sum of P_ij d_T(x_i, x_j)^2, with
a and b the normalised cell masses and d_T the periodic distance (Peyre & Cuturi 2019, Eq. 2.17
and Eq. 2.18, arXiv numbering). Coarsening to 32^2 or 64^2 cells is needed to make it
affordable.

## Relation to existing work

It is the obvious alternative to the Monge-Ampere solve that `wasserstein` uses, and the one
the orchestrator's brief anticipated. It was rejected on two measurements (mine). Cost: a
256^2 pair is a 65,536^2 cost matrix (34 GB), and a 64^2 solve took 5 to 11 s. Fidelity: on
near-uniform densities, its squared value scales as the relative fluctuation times the cell
size, not as the square of the fluctuation. In 1-D on 256 cells it is 10.4 times the
continuous value at a fluctuation of 0.003. In 2-D it halved each time the grid doubled
(32^2: 1.9e-5, 48^2: 1.1e-5, 64^2: 8.4e-6 at a fluctuation of 0.03). It therefore measures
how displacements smaller than a cell are rounded to whole cells.

## How it could be tested

Against the known-answer pairs of EXP-wasserstein-known-answer-transport, at several grid
sizes. The discrete value should approach the exact one only once displacements exceed a cell.

## Why it is helpful

It records why the repository does not use the standard discrete solver for gridded densities,
and when the discrete solver would become acceptable: when features move by many cells, as for
compact features on an empty background.

## References

- Peyre, G. & Cuturi, M. (2019). Found. Trends Mach. Learn. 11(5-6), 355-607. doi:10.1561/2200000073.
