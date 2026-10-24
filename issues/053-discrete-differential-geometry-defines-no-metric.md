# Discrete differential geometry on meshes defines no metric

**Category:** method
**Priority:** low, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Discrete differential geometry on meshes](../docs/ideas/curvature/discrete_differential_geometry.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page describes structure-preserving operators on a mesh and says: "As a diagnostic in its own right the idea is indirect." Its value depends on comparing fields across meshes, which belongs to the out-of-scope infrastructure idea [comparing refinement maps across meshes](../docs/ideas/infrastructure/refinement_map_comparison.md).

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. No number comparing two fields is defined, and every dataset is on a uniform Cartesian grid, so no experiment exercises mesh-native operators.

## What would unblock it

A definition of the quantity to compare, and data on more than one mesh.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
