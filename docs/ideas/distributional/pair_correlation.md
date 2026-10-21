# Pair-correlation function of features

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Once point-like features, such as eddy centres or shocklet locations, have been identified in
a field, their positions form a set of points. The distribution of distances between pairs
of those points says whether features cluster, repel one another, or are scattered at
random, and comparing it between prediction and reference tests whether the prediction
arranges its features correctly.

The rigorous form of this "PDF of pairwise distances" comes from spatial point-process
statistics, the branch of statistics that describes random sets of points. *Ripley's K
function* gives, for each distance $r$, the expected number of other points within $r$ of a
typical point, divided by the average density of points. The *pair-correlation function* is
the corresponding density: how likely a second point is to be found at exactly distance $r$,
relative to a random arrangement.

The idea depends on features being extracted first, by the
[winding angle and Poincaré index](../pattern_detection/winding_angle.md) or by the
[eddy census](../pattern_detection/eddy_census.md).

It belongs to a wider family. [Persistence diagrams](../topology/persistence_diagrams.md),
the eddy census, Ripley's K function and the object matching used in weather forecast
verification all identify features and then compare their distributions. They differ in how a
feature is defined and in whether features are matched pairwise before the comparison.

## Rationale

*The team's judgement.* Medium priority: the comparison cannot be computed until point-like
features have been extracted by another idea, so it waits on those.
