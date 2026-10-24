# Riemann curvature of the flow's configuration space has no discrete algorithm

**Category:** method
**Priority:** low, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Riemann curvature of the flow's configuration space](../docs/ideas/curvature/riemann_curvature.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

Arnold (1966) computes the curvature of the group of volume-preserving maps, whose geodesics are ideal incompressible flows. The page: "Computing sectional curvatures of the diffeomorphism group for a discrete velocity field is a research project in itself."

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. There is no algorithm for a gridded velocity field, the theory is for ideal incompressible flow while the data are weakly compressible, and no comparison between two fields is defined.

## What would unblock it

A discrete formulation and a comparison, or a decision to retire the idea in favour of Lyapunov exponents, which the page says deliver the same content more cheaply.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
