# Curvature statistics of level sets: which isovalue

**Category:** method
**Priority:** medium, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Curvature statistics of level sets](../docs/ideas/curvature/isosurface_curvature.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The metric extracts level sets of density or vorticity magnitude and compares their curvature distributions. Its first pitfall is "The result is sensitive to the choice of isovalue", and the page gives no rule for choosing it.

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. In combustion, where the page's precedent lies, the flame front is a specific level of a progress variable; a turbulent density or vorticity field has no such canonical level. Possible answers (one level in units of the fluctuation rms, a set of levels, or every level weighted by the gradient magnitude) give different numbers. Which distance compares the two curvature distributions is also not stated.

## What would unblock it

A decision on the isovalue rule and the distance between curvature distributions.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
