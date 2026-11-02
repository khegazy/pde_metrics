# Boundary F-score of shock masks

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Once a shock detector has produced a mask of shocked cells for each field, the boundary F-score
compares the two masks with a matching tolerance: a shocked cell of one field counts as matched
when a shocked cell of the other lies within a small distance of it. Precision is the fraction
of the candidate's shocked cells that are matched, recall the fraction of the reference's, and
the score is their harmonic mean. It comes from the evaluation of boundary detectors in natural
images, where a detected boundary is scored by its precision and recall against boundaries
drawn by people (Martin et al. 2004).

The plain overlap scores, intersection over union and the Dice coefficient, are built:
[shock_mask_overlap](../../metrics/shock_mask_overlap.md) registers the Dice coefficient, which
is the boundary F-score at zero tolerance (a derivation on its card, not a source's), and names intersection over union as its monotone
equivalent. What remains is the tolerance. Overlap at zero tolerance drops to zero once a thin
shock has moved by its own detected width, two cells, and stays there however far it moved; a
tolerance of a few cells would keep a near miss distinguishable from a far one. The nearest-cell
distances the score thresholds are already computed by `surface_distances` in the built
[shock_set_distance](../../metrics/shock_set_distance.md), so a builder imports them.

## Pitfalls

- **The tolerance is a threshold and must be fixed once, with a source.** Two defaults exist,
  neither checked against Martin et al. 2004 itself. MATLAB's `bfscore` documentation gives
  0.75% of the image diagonal; the Berkeley benchmark's own matching routine,
  `correspondPixels.m`, defaults its `maxDist` to 0.01 of the image diagonal (its header
  comment). On the 2048-cell Sod tube these are 15.4 and 20.5 cells, which would leave the score
  blind to every `translate_x` shift below 16 cells; on a 256-cell square grid they are 2.7
  and 3.6 cells. A fraction of the domain diagonal has no physical meaning for a shock, so a
  builder must find the tolerance in a primary source and decide whether to take it in cells
  instead.
- **One-to-one or nearest-cell matching.** Matching each cell to its nearest cell, as a distance
  transform does, can match many cells to one, and gives a different number from a one-to-one
  correspondence when the two sets differ in size. The header of `correspondPixels.m` says it
  computes a "minimum-cost correspondance between two boundary maps", which points to one-to-one
  matching in the benchmark code; what Martin et al. write has not been checked against the
  paper, and a builder must read it before choosing.

## Rationale

*The team's judgement.* Medium priority rather than high, because the
[distance between extracted shock sets](../../metrics/shock_set_distance.md) dominates it for
this purpose.

## References

- Martin, D. R., Fowlkes, C. C. & Malik, J. (2004). Learning to detect natural image boundaries
  using local brightness, color, and texture cues. *IEEE Transactions on Pattern Analysis and
  Machine Intelligence* 26, 530–549. <https://doi.org/10.1109/TPAMI.2004.1273918>
