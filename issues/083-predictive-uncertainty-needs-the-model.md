# Quality of predictive uncertainty needs a surrogate that reports uncertainty

**Category:** deferred functionality
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, waiting on model access

## Context

Idea: [Quality of predictive uncertainty](../docs/ideas/distributional/predictive_uncertainty.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

Conformal prediction, error–uncertainty correlation, calibration curves, sharpness and out-of-distribution detection all score uncertainty that a surrogate reports.

## Why it is not built

No dataset carries a surrogate's own uncertainty. Split conformal prediction needs a calibration set of separate trajectories and a predictor to wrap. `synthetic_ensemble` has the same dispersion in every cell, so a correlation between reported uncertainty and error across cells is undefined there; ensemble calibration on average is already covered by `spread_skill` and `rank_histogram`.

## What would unblock it

A surrogate (or dataset) that reports per-cell uncertainty, and separate trajectories for calibration.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
