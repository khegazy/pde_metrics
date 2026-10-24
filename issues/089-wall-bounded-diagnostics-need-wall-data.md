# Wall-bounded flow diagnostics need a dataset with walls

**Category:** data generation
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, waiting on data

## Context

Idea: [Wall-bounded flow diagnostics](../docs/ideas/regime_specific/wall_bounded_flows.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

Friction velocity, wall units, skin friction, separation and the logarithmic law all need the velocity gradient at a solid wall.

## Why it is not built

No dataset has a solid wall with a resolved near-wall layer: `kinet_re5e4` is doubly periodic, and `sod_shock_tube` is one-dimensional and inviscid.

## What would unblock it

A wall-bounded dataset (channel, boundary layer or pipe).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
