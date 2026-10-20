# Hough transform for eddy size

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The circle Hough transform detects circular arcs by voting in a parameter space of centres
and radii. Each point on an edge in the image casts a vote for every circle that could pass
through it, the votes are tallied in an array called the *accumulator*, and peaks in the
accumulator mark the circles that are present. The line version of the transform detects
straight edges in the same way. Applied to a flow field, circles would correspond to eddies
and lines to shock fronts.

The Hough transform is essentially a discretised Radon transform, which records the integrals
of a field along lines. The Radon transform is also the machinery underlying the
[sliced Wasserstein distance](../optimal_transport/sliced_wasserstein.md), and underlying the
idea of projecting a field onto planes and comparing the projections. These are the same
mathematical object viewed from different angles.

## Precedent

A search for a precedent for detecting eddies with the Hough transform found none. The vortex-
and eddy-detection literature that does exist is built on streamline geometry (see the
[winding angle](winding_angle.md)), on velocity-gradient criteria (see the
[vortex criteria](vortex_criteria.md)), and on closed-contour methods, not on Hough voting.
This does not show that the idea is bad. It means that this would be the first attempt, with
no known failure modes to borrow and no baseline to compare against.

## Pitfalls

- The output is an accumulator in parameter space, which is not naturally a metric. A
  distance between two Hough accumulators would still have to be defined.

## Rationale

*The team's judgement.* Low priority. The priority was lowered from medium to low because the
expected precedent is absent, because the output is not naturally a metric, and because the
[winding angle](winding_angle.md) covers the same intent with an implemented, documented
method. Visualising a Hough accumulator of a shocked field is still worth an afternoon,
because the question of what it looks like is legitimate and cheap to answer, but the idea is
not queued as a metric candidate ahead of the winding angle.
