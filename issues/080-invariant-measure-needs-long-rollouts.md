# Invariant measure and attractor comparison needs long rollouts and the model

**Category:** deferred functionality
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, waiting on data and model access

## Context

Idea: [Invariant measure and attractor comparison](../docs/ideas/dynamics/invariant_measure.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The comparison is of long-time distributions, Lyapunov exponents and attractor dimension of a long rollout.

## Why it is not built

It needs long predicted trajectories, which no dataset supplies, and the Lyapunov exponents of the learned dynamics need the model itself. No existing experiment changes the attractor in a controlled way.

## What would unblock it

Long rollouts ([010](010-forecast-pair-reader.md) is the first step), model access for the Lyapunov exponents, and a temporal experiment (see [the temporal ladder proposal](../proposals/EXP-orchestrator-20261023-temporal-ladder.md)).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
