# Hough transform for eddy size defines no distance between accumulators

**Category:** method
**Priority:** low, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Hough transform for eddy size](../docs/ideas/pattern_detection/hough_transform.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page's own pitfall: "The output is an accumulator in parameter space, which is not naturally a metric. A distance between two Hough accumulators would still have to be defined." It also records that no precedent for detecting eddies this way was found.

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. With no precedent there is no published standard to follow for the distance, the edge detector feeding the votes, or the radius range.

## What would unblock it

A definition of the distance between accumulators, or a decision to keep the idea as the visualisation the page suggests.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
