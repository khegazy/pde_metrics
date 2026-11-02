---
type: EXP
kind: degradation
related: ["metrics/persistence_distance", "proposals/EXP-orchestrator-20261023-known-vortex-field.md", "issues/073", "issues/086"]
seen_in: "Edelsbrunner, Morozov & Pascucci 2006, Proc. 22nd Annu. Symp. Comput. Geom., 127-134"
doi: "10.1145/1137856.1137878"
found_by: "persistence_distance, 2026-10-31"
---

# EXP: Persistence-sensitive simplification as a degradation

## What the experiment is

A degradation whose severity is a persistence threshold epsilon, in units of the field's
fluctuation RMS about its mean: it replaces the field by an epsilon-simplification, a field within
epsilon of it everywhere whose persistence diagram is the original's with every point closer than
epsilon to the diagonal removed. Edelsbrunner, Morozov and Pascucci (2006) prove such
simplifications exist for functions on 2-manifolds, the torus included, in dimensions 0 and 1, and
give an algorithm for piecewise-linear functions; Morozov's later "Persistence-sensitive
simplification simplified" gives a simpler one.

## What it tests

It removes the weakest features (the shallowest vortices, the smallest eddies) and nothing else,
by a controlled and known amount: the diagram after simplification is known exactly from the
diagram before, and the field moves by at most epsilon. It is the second form of the
known-vortex-field proposal (`proposals/EXP-orchestrator-20261023-known-vortex-field.md`, "removes
or weakens a known fraction of the vortices"), with a published algorithm and a known effect.
No current degradation changes the vortex population without also changing the strong vortices:
smoothing lowers every peak, and noise adds features.

## Metrics it would test

`persistence_distance` (whose value on it is known: each removed point costs half its lifetime, so
the distance is the largest removed half-lifetime, at most epsilon/2), the Wasserstein and
Betti-curve variants proposed beside it, the eddy census (issue 073), the winding angle (issue
086), and every pointwise control, which would see only the small removed features.

## Why it is helpful

It is the first degradation that changes the topology of the field by a known amount while
leaving its large structures in place, the exact counterpart of a surrogate that drops weak
vortices.

## Cost and requirements

One degradation bundle and a simplification routine on the periodic grid. No library in the
environment implements it for cubical complexes as far as I know (not checked exhaustively); an
implementation on the cubical T-construction would need its own validation against the diagram it
promises, which `persistence_diagram` provides. Deterministic, so it can be calibrated.

## References

- Edelsbrunner, H., Morozov, D. & Pascucci, V. (2006). Persistence-sensitive simplification of
  functions on 2-manifolds. Proc. 22nd Annu. Symp. Comput. Geom., 127-134. Read through the
  author page's abstract and a search summary, not the full text.
  <https://doi.org/10.1145/1137856.1137878>
