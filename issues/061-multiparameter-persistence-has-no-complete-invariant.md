# Multiparameter persistence: no complete invariant, research-grade tooling, and it builds on persistence

**Category:** method
**Priority:** low, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Multiparameter persistence](../docs/ideas/topology/multiparameter_persistence.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page: "With two or more parameters there is no complete discrete invariant analogous to the persistence diagram. This is an obstruction at the level of theorems", and the tooling (RIVET; Lesnick and Wright 2015) "remains research grade".

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. Which incomplete invariant to compare, and with which distance, is a choice with no standard. The idea also builds on [persistence diagrams](../docs/ideas/topology/persistence_diagrams.md), which are not built, and RIVET is not a Python dependency that can be added now.

## What would unblock it

Persistence diagrams built first, and a decision on the invariant and distance.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
