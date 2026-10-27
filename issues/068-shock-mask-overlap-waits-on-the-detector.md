# Overlap of shock masks waits on the shock detector

**Category:** deferred functionality
**Priority:** medium, the team's priority for the idea
**Status:** open, waiting on another metric

## Context

Idea: [Overlap of shock masks](../docs/ideas/shock_geometry/shock_mask_overlap.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

Intersection-over-union, Dice and the boundary F-score compare two shock masks, which a shock detector produces.

## Why it is not built

The rule this follows: an idea that builds on a metric not yet on `main` is not implemented; it waits until that metric is merged. The detector is built as shared code inside the first shock metric, the [distance between extracted shock sets](../docs/ideas/shock_geometry/shock_set_distance.md), which is not yet on `main`. Once it is, this metric is testable on `sod_shock_tube` with `translate`, which shifts the shock by a known distance.

## What would unblock it

The distance between shock sets merged.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
