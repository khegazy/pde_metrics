# Signed entropy production: the over-smeared-shock contradiction, and consecutive time levels

**Category:** method
**Priority:** high, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Signed entropy production](../docs/ideas/physics_invariants/entropy_production.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page opens with a warning box: the team's tracker says an over-smeared shock produces too *little* entropy; the field guide says it shows *excessive* dissipation; "they cannot both describe the same error", and whoever implements it "must look at this carefully and determine which is correct ... before the excess-dissipation score and the sign convention of the signed mismatch are fixed".

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. Settling the contradiction fixes the sign convention of two of the three scores, which is exactly the kind of choice an implementer must not make alone. Separately, Eq. (1), the only formula on the page, differences two consecutive time levels $\eta^{n+1}_K - \eta^n_K$ of the prediction; the degradation ladder damages single snapshots, so no existing experiment supplies a damaged pair of consecutive states. `sod_shock_tube` is admitted as evidence for this metric once its harness change lands, but its frames are 0.011 time units apart, not one solver step.

## What would unblock it

A decision on the contradiction, with the derivation or a direct check on a smeared shock; and a temporal experiment that damages consecutive states consistently (see [the temporal ladder proposal](../proposals/EXP-orchestrator-20261023-temporal-ladder.md)).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
