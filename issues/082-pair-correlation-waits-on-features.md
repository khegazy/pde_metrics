# Pair-correlation function of features waits on feature extraction

**Category:** deferred functionality
**Priority:** medium, the team's priority for the idea
**Status:** open, waiting on another metric

## Context

Idea: [Pair-correlation function of features](../docs/ideas/distributional/pair_correlation.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page: "The idea depends on features being extracted first, by the winding angle and Poincaré index or by the eddy census."

## Why it is not built

The rule this follows: an idea that builds on a metric not yet on `main` is not implemented; it waits until that metric is merged. Neither extractor is built, and both are blocked (their own issues).

## What would unblock it

A feature extractor merged, and an experiment that changes feature positions in a known way (see [the known-vortex proposal](../proposals/EXP-orchestrator-20261023-known-vortex-field.md)).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
