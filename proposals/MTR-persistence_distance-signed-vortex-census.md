---
type: MTR
kind: variant of persistence_distance
related: ["metrics/persistence_distance", "docs/ideas/pattern_detection/eddy_census.md"]
seen_in: "agent's own"
doi: "none"
found_by: "persistence_distance, 2026-10-31"
---

# MTR: Signed vortex census from zero-dimensional persistence

## What it measures

On two-dimensional vorticity, the strengths of the clockwise and of the counter-clockwise
vortices separately, each compared between prediction and reference. A model that gets one sign
of vortex right and the other wrong is told which.

## Definition

The zero-dimensional sublevel diagram D_0(omega) records each local minimum of vorticity (a
clockwise vortex core) at its depth b and the saddle level d where it merges into a deeper one;
D_0(-omega) does the same for the maxima, the counter-clockwise cores. The variant reports the
bottleneck distance of each separately:

    C_minus(f, g) = d_B(D_0(f), D_0(g)),   C_plus(f, g) = d_B(D_0(-f), D_0(-g))

with d_B as in Cohen-Steiner, Edelsbrunner & Harer (2005), Sect. 3.1. Bleile et al. (2022, Theorems 6.1-6.2) relate the diagrams of the T-construction of f and the
V-construction of -f, dimension k to dimension d - k - 1, so in two dimensions D_0(-f) carries
roughly what `persistence_distance` reads in H1, split off by sign; it is only roughly, because
the metric uses the T-construction for both (my reading, a conjecture to check). The use of the
pair as a census by sign is my own idea.

## Relation to existing work

A variant of `persistence_distance`, which takes the maximum over dimensions. The eddy census
idea (`docs/ideas/pattern_detection/eddy_census.md`) waits on a vortex detector (issue 073); the
H0 diagram is a threshold-free detector that needs no tuned criterion, so this could also serve
that idea.

## How it could be tested

The `persistence_distance` ladder for the smoothing axes; a degradation that weakens only the
vortices of one sign does not exist, and the known-vortex-field proposal
(`proposals/EXP-orchestrator-20261023-known-vortex-field.md`) would supply it.

## Why it is helpful

It turns the diagram into a statement about vortices a fluid dynamicist reads directly, and the
two numbers can disagree where the maximum over dimensions hides which sign failed.

## References

- Cohen-Steiner, D., Edelsbrunner, H. & Harer, J. (2005). Stability of persistence diagrams.
  Proc. 21st Annu. Symp. Comput. Geom., 263-271. <https://doi.org/10.1145/1064092.1064133>
- Bleile, B., Garin, A., Heiss, T., Maggs, K. & Robins, V. (2022). The persistent homology of dual
  digital image constructions. Research in Computational Topology 2, AWM Series 30, 1-26.
  <https://doi.org/10.1007/978-3-030-95519-9_1>
