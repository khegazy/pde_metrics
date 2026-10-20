# Sliced Wasserstein distance

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Project the field onto many random one-dimensional directions, compute the
[Wasserstein distance](wasserstein.md) along each direction, and average the results. In one
dimension the Wasserstein distance is cheap, because it reduces to sorting the two samples and
comparing them in order. The total cost of the sliced distance is therefore close to linear in
the size of the field.

Projecting a field onto planes and comparing the projections is the same idea whenever each
projection is compared with a one-dimensional transport distance. It is therefore kept here
rather than as a separate idea, and its remaining use is as a visualisation rather than as a
separate metric.

The mathematics underneath is the Radon transform, which integrates a field along lines or
planes and so produces exactly these projections. The
[Hough transform](../pattern_detection/hough_transform.md) is essentially a discretised Radon
transform, so the Hough transform, the sliced distance and projecting onto planes are the same
mathematical object viewed from different angles.

## Pitfalls

- Slicing discards information in a way that is difficult to characterise, so it introduces
  errors of its own. Use it for screening and for studies of how cost scales with grid size,
  and validate it against the exact Wasserstein distance on small cases.

## Rationale

*The team's judgement.* High priority: it brings the displacement-aware behaviour of the
[Wasserstein distance](wasserstein.md) at close to linear cost, using only the cheap
sort-based one-dimensional distance.

## Keywords

sliced Wasserstein distance, max-sliced Wasserstein, Radon transform, projection-based optimal
transport.
