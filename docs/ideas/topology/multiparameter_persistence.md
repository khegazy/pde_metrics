# Multiparameter persistence

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

[Persistence diagrams](../../metrics/persistence_distance.md) filter a field by one parameter, its value.
Multiparameter persistence filters by two parameters at once, for instance the field value
together with a spatial scale or distance, so that it captures the interplay between distance
and field value. The motivation is sound.

## Precedent

Lesnick and Wright noted in 2015 that there was "no publicly available software which extends
the usual persistent homology pipeline for exploratory data analysis to the multidimensional
persistence". Their RIVET, the Rank Invariant Visualization and Exploration Tool, was built to
fill that gap. It provides interactive visualisation of the barcodes of one-dimensional affine
slices of a two-dimensional persistence module, that is, of the one-parameter summaries seen
along straight lines through the two-parameter space (Lesnick and Wright 2015). Efficient
algorithms for minimal presentations and Betti numbers were added later (Lesnick and Wright
2022).

## Pitfalls

- With two or more parameters there is no complete discrete invariant analogous to the
  persistence diagram. This is an obstruction at the level of theorems rather than a gap in
  software.
- The tooling has improved since 2015 and is usable, but it remains research grade compared
  with the one-parameter tooling.

## Rationale

*The team's judgement.* Low priority, because of the theoretical obstruction and the
research-grade tooling. The idea is parked. If
[persistence diagrams](../../metrics/persistence_distance.md) succeed and their main failure turns out to be
confounding structures of different scale, this idea should be revisited, starting from
RIVET.

## References

- Lesnick, M. & Wright, M. (2015). Interactive visualization of 2-D persistence modules.
  <https://arxiv.org/abs/1512.00180>
- Lesnick, M. & Wright, M. (2022). Computing minimal presentations and bigraded Betti numbers
  of 2-parameter persistent homology. *SIAM Journal on Applied Algebra and Geometry* 6(2),
  267–298. <https://arxiv.org/abs/1902.05708>
