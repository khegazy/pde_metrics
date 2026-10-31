# Eddy census

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Once eddies have been identified, for example by the [winding angle](winding_angle.md) or by
the [vortex criteria](vortex_criteria.md), the distributions of their number, size and
lifetime become natural targets for comparison. Each of these distributions can be compared
between prediction and reference with a one-dimensional Wasserstein distance, the least cost
of moving the probability mass of one distribution onto the other.

The related classical tool is Ripley's $K$ function, or equivalently the
[pair-correlation function](../distributional/pair_correlation.md), from spatial
point-process statistics. It describes how the distances between pairs of point-like features,
such as eddy centres, are distributed.

The census belongs to a family of methods that identify features and then compare their
distributions, which also includes [persistence diagrams](../../metrics/persistence_distance.md).
The members differ in how a feature is defined and in whether features are matched pairwise
before comparison.

## Precedent

The title of Sadarjoen and Post's paper names detection, *quantification* and *tracking* of
vortices (Sadarjoen and Post 2000), so the census and its evolution in time come from the same
machinery as the detector.

## Rationale

*The team's judgement.* Medium priority: the distributions are natural comparison targets, but
the census can only follow once the [winding angle](winding_angle.md) or the
[vortex criteria](vortex_criteria.md) has identified the eddies.

## References

- Sadarjoen, I. A. & Post, F. H. (2000). Detection, quantification, and tracking of vortices
  using streamline geometry. *Computers & Graphics* 24(3), 333–341.
  <https://doi.org/10.1016/S0097-8493(00)00029-7>
