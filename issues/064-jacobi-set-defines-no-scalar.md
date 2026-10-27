# Jacobi sets define a set, not a number

**Category:** method
**Priority:** medium, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Jacobi sets](../docs/ideas/topology/jacobi_sets.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The Jacobi set of two functions is "the set of points where the gradients of the functions are parallel" (Edelsbrunner and Harer 2004). The page argues it is natively a comparison object but does not say what number is reported.

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. A further obstacle, an observation made in the screening, not on the page: when a prediction is close to its reference the two gradients are nearly parallel almost everywhere, so the Jacobi set approaches the whole domain and its size does not decrease toward a perfect prediction. The page's algorithm is for piecewise-linear functions on triangulations.

## What would unblock it

A definition of the reported number that behaves sensibly as the prediction approaches the reference.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
