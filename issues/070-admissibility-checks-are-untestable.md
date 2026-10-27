# Admissibility checks: no existing experiment violates an admissibility condition

**Category:** deferred functionality
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, waiting on an experiment

## Context

Idea: [Admissibility checks](../docs/ideas/physics_invariants/admissibility_checks.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page lists positivity of density and pressure, finite values and blow-up, conservation drift, the divergence error, Reynolds-stress realizability and species bounds, each computed from the prediction alone.

## Why it is not built

The rule this follows: a metric is built only if an existing experiment changes, in a controlled and known way, the property it is built to detect; a degradation that moves it only incidentally does not count. The current experiments are the 24 degradations (`python -m degradations`) applied to single snapshots of `kinet_re5e4`, `synthetic_ensemble` and `sod_shock_tube`. Part by part:

- *Positivity and finite values.* No degradation is built to produce a negative density or pressure or a non-finite value. Noise amplitudes are fractions of the fluctuation rms; on `kinet_re5e4`, whose density stays within a few percent of its mean ([002](002-shocklet-dataset.md) measures 0.9612 to 1.0065 at t = 5000), none goes negative. On `sod_shock_tube` large noise could, but only incidentally.
- *Divergence error.* A constraint of incompressible flow; `kinet_re5e4` is weakly compressible, so a nonzero divergence is not a violation.
- *Conservation drift.* Needs a rollout ([010](010-forecast-pair-reader.md)).
- *Realizability.* The page notes that a covariance computed from the prediction's own fluctuations satisfies it automatically.
- *Species bounds.* No reacting data.

## What would unblock it

An experiment that violates a condition in a controlled way (see [the constraint-violation proposal](../proposals/EXP-orchestrator-20261023-constraint-violation.md)), and rollouts for the drift.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
