# Curvature without smooth structure

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Some notions of curvature require no smooth structure, so they apply to point clouds,
meshes and graphs as readily as to smooth surfaces. Two families are relevant:

- **Alexandrov or $\mathrm{CAT}(k)$ curvature** compares triangles drawn in the space with
  triangles of the same side lengths on a model surface of constant curvature $k$. A space
  whose triangles are no fatter than the model's has curvature at most $k$.
- **Ollivier–Ricci curvature** is defined through optimal transport between the measures
  that describe the neighbourhoods of two nearby points. Because it is built on the
  [Wasserstein distance](../optimal_transport/wasserstein.md), it connects this theme back
  to transport.

## Precedent

Ollivier–Ricci curvature has a genuine track record as a structural descriptor for networks.

## Rationale

*The team's judgement.* Low priority for the coming year: the application to flow fields
would be invented from scratch, with no precedent whose failure modes could be borrowed,
while cheaper ideas remain untested. Revisit it if a mesh-native or graph-native structural
descriptor turns out to be needed.

## Keywords

Ollivier-Ricci curvature, Forman curvature, Alexandrov curvature, coarse Ricci curvature
networks.
