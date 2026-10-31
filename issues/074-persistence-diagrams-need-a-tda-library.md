# Persistence diagrams need a topology library

**Category:** deferred functionality
**Priority:** high, the team's priority for the idea
**Status:** open until the metric is built. `gudhi` 3.13.0 is now a core dependency on `metric_build` (the dependency change of the metric-building plan); once that reaches `main`, the idea is buildable and the change that builds it deletes this file.

## Context

Idea: [Persistence diagrams](../docs/ideas/topology/persistence_diagrams.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page: "Off-the-shelf software exists, including GUDHI, Ripser.py, giotto-tda and TTK ... so building it is a pure implementation task." It is first under "What to build next".

## Why it is not built

Writing persistent homology and the bottleneck distance from scratch would replace mature, tested software with new code that would itself need validating. On the doubly periodic `kinet_re5e4` domain the library must support periodic cubical complexes. Once installed the metric is testable: `additive_noise` creates short-lived features near the diagonal, and on a periodic domain `translate` leaves the diagram unchanged.

## What would unblock it

Done on `metric_build`: GUDHI 3.13.0, whose `CubicalComplex` was smoke-tested on a 32 × 32 field in the repository's environment. What remains is building the metric once it is on `main`.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
