# Residual of the equations in weak form needs states one solver step apart

**Category:** data generation
**Priority:** high, the team's priority for the idea
**Status:** open, waiting on data

## Context

Idea: [Residual of the equations in weak form](../docs/ideas/physics_invariants/weak_residual.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

Eq. (1) on the page differences two cell averages one time step apart. Its own pitfall: "A prediction stored only every few steps gives an update in (1) that matches no single step of any scheme."

## Why it is not built

The rule this follows: a metric is built only if an existing experiment changes, in a controlled and known way, the property it is built to detect; a degradation that moves it only incidentally does not count. The current experiments are the 24 degradations (`python -m degradations`) applied to single snapshots of `kinet_re5e4`, `synthetic_ensemble` and `sod_shock_tube`. The ladder damages single snapshots, so no experiment supplies a damaged pair of consecutive states. `kinet_re5e4` is evaluated every 50th stored frame, and the forecast files of [010](010-forecast-pair-reader.md) are 500 solver steps apart. The numerical flux must also be declared.

## What would unblock it

Pairs of states one solver step apart, and a temporal experiment that damages both states consistently (see [the temporal ladder proposal](../proposals/EXP-orchestrator-20261023-temporal-ladder.md)).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
