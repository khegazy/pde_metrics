# Modal decompositions need time-resolved trajectories

**Category:** deferred functionality
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, waiting on data and an experiment

## Context

Idea: [Modal decompositions and radiated sound](../docs/ideas/dynamics/modal_decompositions.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page: "All five need a time-resolved trajectory rather than single frames".

## Why it is not built

The rule this follows: a metric is built only if an existing experiment changes, in a controlled and known way, the property it is built to detect; a degradation that moves it only incidentally does not count. The current experiments are the 24 degradations (`python -m degradations`) applied to single snapshots of `kinet_re5e4`, `synthetic_ensemble` and `sod_shock_tube`. No experiment damages a trajectory in a controlled way; the radiated-sound part also needs an acoustic far field and a declared observer geometry, which no dataset has.

## What would unblock it

Time-resolved predicted trajectories and a temporal experiment (see [the temporal ladder proposal](../proposals/EXP-orchestrator-20261023-temporal-ladder.md)).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
