# Winding angle and Poincaré index: no experiment changes the vortices in a known way

**Category:** data generation
**Priority:** high, the team's priority for the idea
**Status:** open, waiting on an experiment

## Context

Idea: [Winding angle and Poincaré index](../docs/ideas/pattern_detection/winding_angle.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The winding-angle method (Sadarjoen and Post 2000) detects vortices from streamline geometry and yields a count of vortices that does not depend on the local velocity magnitude. Its stated strength is detecting weak vortices.

## Why it is not built

The rule this follows: a metric is built only if an existing experiment changes, in a controlled and known way, the property it is built to detect; a degradation that moves it only incidentally does not count. The current experiments are the 24 degradations (`python -m degradations`) applied to single snapshots of `kinet_re5e4`, `synthetic_ensemble` and `sod_shock_tube`. The property the metric detects is the presence and number of vortices. No degradation adds, removes or weakens individual vortices by design. Smoothing and spectral filters change amplitudes, to which the method is insensitive by construction; translations leave the count unchanged (which tests only invariance); noise may create spurious critical points, but only incidentally. The method's clustering and seeding parameters would also have to be fixed from the source.

## What would unblock it

An experiment with a known vortex population (see [the known-vortex proposal](../proposals/EXP-orchestrator-20261023-known-vortex-field.md)).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
