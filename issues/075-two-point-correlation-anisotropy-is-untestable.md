# Two-point correlation: what it adds beyond spectrum_l2 is untestable

**Category:** deferred functionality
**Priority:** medium, the team's priority for the idea
**Status:** open, waiting on an experiment

## Context

Idea: [Two-point correlation](../docs/ideas/basis_decompositions/two_point_correlation.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page: the correlation carries the same information as the energy spectrum, and "A correlation kept as a function of the separation *vector* ... also records how the variation depends on direction (anisotropy) ... that is what this idea would add."

## Why it is not built

The rule this follows: a metric is built only if an existing experiment changes, in a controlled and known way, the property it is built to detect; a degradation that moves it only incidentally does not count. The current experiments are the 24 degradations (`python -m degradations`) applied to single snapshots of `kinet_re5e4`, `synthetic_ensemble` and `sod_shock_tube`. The direction-averaged part duplicates the built `spectrum_l2`. The part that is new, anisotropy, is not changed in a controlled way by any degradation: every smoothing, spectral and noise operator is isotropic, and [015](015-rotation-degradation.md) (rotation) would not change the anisotropy of an isotropic field either.

## What would unblock it

An anisotropic degradation (see [the anisotropic-blur proposal](../proposals/EXP-orchestrator-20261023-anisotropic-blur.md)).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
