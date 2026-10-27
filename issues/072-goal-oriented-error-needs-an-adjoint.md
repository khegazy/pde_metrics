# Goal-oriented error estimates need an adjoint solver and a declared output

**Category:** deferred functionality
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, waiting on infrastructure

## Context

Idea: [Goal-oriented error estimates](../docs/ideas/physics_invariants/goal_oriented_error.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The dual-weighted-residual estimate needs the adjoint $\psi$ of the governing equations linearised about the prediction. The page: "That is substantial infrastructure, and none exists in the repository."

## Why it is not built

No adjoint solver exists, no output quantity $J$ is declared for any dataset, and the residual it weights needs consecutive states (see the weak-residual issue).

## What would unblock it

An adjoint solver, a declared output per dataset, and the weak residual.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
