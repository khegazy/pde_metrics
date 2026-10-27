# Reacting-flow diagnostics need reacting data

**Category:** data generation
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, waiting on data

## Context

Idea: [Reacting-flow and scalar-mixing diagnostics](../docs/ideas/regime_specific/reacting_flows.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

Mixture fraction, scalar dissipation, flame surface density, the flame index and thermochemical bounds need species mass fractions or a progress variable.

## Why it is not built

No dataset carries a scalar, a species or a reaction.

## What would unblock it

A reacting or scalar-mixing dataset.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
