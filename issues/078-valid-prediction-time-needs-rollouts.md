# Valid prediction time needs rollouts and a temporal experiment

**Category:** deferred functionality
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, waiting on data and an experiment

## Context

Idea: [Valid prediction time](../docs/ideas/dynamics/valid_prediction_time.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The valid prediction time is the first time a rollout's normalised error exceeds a declared threshold, in Lyapunov times.

## Why it is not built

The rule this follows: a metric is built only if an existing experiment changes, in a controlled and known way, the property it is built to detect; a degradation that moves it only incidentally does not count. The current experiments are the 24 degradations (`python -m degradations`) applied to single snapshots of `kinet_re5e4`, `synthetic_ensemble` and `sod_shock_tube`. The metric needs a predicted trajectory and a reference trajectory. The degradation ladder damages single snapshots, and the forecast pairs on disk are not read yet ([010](010-forecast-pair-reader.md)). Even with them, real forecasts are not a controlled experiment.

## What would unblock it

The forecast pair reader, and a temporal experiment (see [the temporal ladder proposal](../proposals/EXP-orchestrator-20261023-temporal-ladder.md)).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
