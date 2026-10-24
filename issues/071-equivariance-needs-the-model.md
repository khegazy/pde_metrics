# Galilean and rotational equivariance needs the model

**Category:** deferred functionality
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, waiting on model access

## Context

Idea: [Galilean and rotational equivariance](../docs/ideas/physics_invariants/equivariance_tests.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page: "The score needs no reference field, but it needs the model itself, because the model must be run on transformed inputs."

## Why it is not built

The repository consumes stored fields only; no model is run. The related statistical check that needs no model, anisotropy in a nominally isotropic prediction, is untestable because no degradation is anisotropic (see [the anisotropic-blur proposal](../proposals/EXP-orchestrator-20261023-anisotropic-blur.md)).

## What would unblock it

A way to run a model on transformed inputs, which belongs with [010](010-forecast-pair-reader.md) and the model interface.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
