# Curvature without smooth structure defines no metric for flow fields

**Category:** method
**Priority:** low, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Curvature without smooth structure](../docs/ideas/curvature/metric_geometry_curvature.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page names Alexandrov (CAT(k)) and Ollivier–Ricci curvature and says "the application to flow fields would be invented from scratch, with no precedent".

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. Neither which space the curvature is computed on (a point cloud, a graph built from the field, ...) nor how two fields are compared is defined. Ollivier–Ricci curvature is also built on the unbuilt [Wasserstein distance](../docs/ideas/optimal_transport/wasserstein.md).

## What would unblock it

A definition of the space, the curvature estimator and the comparison.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
