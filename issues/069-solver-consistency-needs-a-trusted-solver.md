# Consistency with one step of a trusted solver needs the solver

**Category:** deferred functionality
**Priority:** high, the team's priority for the idea
**Status:** open, waiting on infrastructure

## Context

Idea: [Consistency with one step of a trusted solver](../docs/ideas/physics_invariants/solver_consistency.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The metric advances the predicted state by one step of a trusted solver and measures the distance to the model's own next state. The page: "It needs a trusted solver in the repository."

## Why it is not built

No solver is in the repository. The planned [solver predictor](../docs/ideas/infrastructure/degradation_ladder_reference.md) is an infrastructure idea, outside the scope of agent-built metrics. The metric also needs consecutive predicted states, which the single-snapshot ladder does not supply.

## What would unblock it

A trusted solver runnable at the model's resolution, and predicted states one step apart.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
