# Velocity channel analysis needs a projected reference

**Category:** data generation
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, waiting on data

## Context

Idea: [Velocity channel analysis](../docs/ideas/basis_decompositions/velocity_channel_analysis.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page: "It applies only when the reference is a projection that carries a line-of-sight velocity. For a reference that is the full field on a grid, the ordinary spectra are available directly and this adds nothing."

## Why it is not built

Every dataset is a full two-dimensional field on a grid. A position–position–velocity cube needs a three-dimensional field projected along a line of sight ([005](005-3d-and-cost-extrapolation.md)).

## What would unblock it

A dataset whose reference is a line-of-sight projection, with the observation operator declared.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
