# Eddy census waits on a vortex detector

**Category:** deferred functionality
**Priority:** medium, the team's priority for the idea
**Status:** open, waiting on another metric

## Context

Idea: [Eddy census](../docs/ideas/pattern_detection/eddy_census.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page: "the census can only follow once the winding angle or the vortex criteria has identified the eddies." Lifetimes also need eddies tracked across frames.

## Why it is not built

The rule this follows: an idea that builds on a metric not yet on `main` is not implemented; it waits until that metric is merged. Neither the [winding angle](../docs/ideas/pattern_detection/winding_angle.md) nor the [vortex criteria](../docs/ideas/pattern_detection/vortex_criteria.md) is built, and both are themselves blocked (their own issues). The lifetime part needs a temporal experiment (see [the temporal ladder proposal](../proposals/EXP-orchestrator-20261023-temporal-ladder.md)).

## What would unblock it

A vortex detector merged, and an experiment that changes vortex number or size in a known way (see [the known-vortex proposal](../proposals/EXP-orchestrator-20261023-known-vortex-field.md)).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
