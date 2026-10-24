# Reeb graphs and Morse–Smale complexes: no standard distance between graphs

**Category:** method
**Priority:** medium, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Reeb graphs and Morse–Smale complexes](../docs/ideas/topology/reeb_graphs.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page's pitfall: "The metrics used to compare two such graphs are less standardised than those for persistence diagrams", naming interleaving and edit distances.

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. The choice of distance decides what the metric measures and has no standard. The page's implementation route is TTK (Tierny et al. 2018), which is not installed and cannot be added now (no `uv`).

## What would unblock it

A decision on the distance, and the library added.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
