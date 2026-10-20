# Discrete differential geometry on meshes

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Discrete differential geometry builds the objects of smooth geometry, such as gradients,
curls and curvature, directly on a mesh. Its operator framework, discrete exterior calculus,
supplies structure-preserving operators: discrete operators that keep the exact identities
of their continuous counterparts. These matter if the project compares fields that live on
different meshes, the path described under
[comparing refinement maps across meshes](../infrastructure/refinement_map_comparison.md).
As a diagnostic in its own right the idea is indirect.

## Rationale

*The team's judgement.* Low priority: as a diagnostic in its own right it is indirect, and
its value depends on the project taking up comparison across meshes.
