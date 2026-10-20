# Overlap of shock masks

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Once a [shock detector](shock_detector.md) has produced a mask of shocked cells for each
field, overlap measures score how much the two masks coincide. Intersection-over-union is the
number of cells shocked in both masks divided by the number shocked in either. The Dice
coefficient is twice the number shocked in both, divided by the total number of shocked cells
in the two masks. Both are cheap and easy to compute. The boundary F-score compares only the
boundaries of the two masks, counting a boundary point as matched when the other boundary
lies within a small tolerance of it. It is the variant aware of thin structures, and the one
to prefer.

## Pitfalls

- Overlap measures degrade badly for *thin* objects. A one-cell shift of a shock two cells
  thick can drive the intersection-over-union close to zero, which brings back the
  double-penalty problem (a correct feature in a slightly wrong place scored as two errors) in
  a new form.

## Rationale

*The team's judgement.* Medium priority rather than high, because the
[distance between extracted shock sets](shock_set_distance.md) dominates it for this purpose.
