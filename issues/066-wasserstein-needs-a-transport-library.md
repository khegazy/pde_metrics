# Wasserstein distance for horizontal displacement needs a transport library

**Category:** deferred functionality
**Priority:** high, the team's priority for the idea
**Status:** open, waiting on the signed-field decision for velocity and vorticity. The dependency is resolved on `metric_build`: `pot` 0.9.7.post1 is a core dependency, so the positive field (density) is buildable once that reaches `main`.

## Context

Idea: [Wasserstein distance for horizontal displacement](../docs/ideas/optimal_transport/wasserstein.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The quadratic Wasserstein distance between two fields on the 256 × 256 grid of `kinet_re5e4` is a transport problem between 65 536-point distributions.

## Why it is not built

Solving that problem exactly needs a dedicated solver (for example POT); a general linear-programming solution is far too slow at this size. For velocity and vorticity, which take both signs, the metric also needs the signed-field formulation, which is an open question (issue on transport between signed fields). Density is positive and would not need it.

## What would unblock it

The signed-field decision (issue 047) for velocity and vorticity. The transport library is done on `metric_build`: POT 0.9.7.post1, whose `emd2` was smoke-tested in the repository's environment.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
