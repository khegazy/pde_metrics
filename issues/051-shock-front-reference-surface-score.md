# Shock front position, speed and jump conditions: the reference-surface score is unsettled

**Category:** method
**Priority:** medium, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Shock front position, speed and jump conditions](../docs/ideas/shock_geometry/shock_front_error.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page fixes a procedure for the Rankine–Hugoniot residual on a detected surface and scores it on the predicted and on the reference surface. It then states: "How the reference-surface score should register a missing or displaced shock is not settled". A field with no jump at the sampled location gives a zero residual, so the residual alone scores a missing shock as good; "Which such quantity to use is an open question".

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. Two further obstacles: the speed error and the normal speed $V_n$ in Eq. (1) come from "a level-set or temporally smoothed track of the surface", which needs consecutive frames of the prediction, while the degradation ladder damages single snapshots; and the residual needs the shock detector, which is not built yet.

## What would unblock it

A decision on the quantity paired with the residual on the reference surface; a temporal experiment for the speed part (see [the temporal ladder proposal](../proposals/EXP-orchestrator-20261023-temporal-ladder.md)); and the shock detector, which the first shock metric builds.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
