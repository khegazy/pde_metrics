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

## Precedent

All three measures come from fields that compare sets. Intersection-over-union is Jaccard's
index, introduced to compare the plant species found in different regions (Jaccard 1912).
The Dice coefficient was introduced to measure how strongly two species associate (Dice
1945). The boundary F-score comes from the evaluation of boundary detectors in natural
images, where a detected boundary is scored by its precision and recall against boundaries
drawn by people (Martin et al. 2004).

## Pitfalls

- Overlap measures degrade badly for *thin* objects. Across a shock two cells thick, a
  one-cell shift leaves one cell shared out of three covered, an intersection-over-union of
  one third, and a two-cell shift drives it to zero. That brings back the
  double-penalty problem (a correct feature in a slightly wrong place scored as two errors) in
  a new form.

## Rationale

*The team's judgement.* Medium priority rather than high, because the
[distance between extracted shock sets](shock_set_distance.md) dominates it for this purpose.

## References

- Dice, L. R. (1945). Measures of the amount of ecologic association between species.
  *Ecology* 26, 297–302. <https://doi.org/10.2307/1932409>
- Jaccard, P. (1912). The distribution of the flora in the alpine zone. *New Phytologist* 11,
  37–50. <https://doi.org/10.1111/j.1469-8137.1912.tb05611.x>
- Martin, D. R., Fowlkes, C. C. & Malik, J. (2004). Learning to detect natural image boundaries
  using local brightness, color, and texture cues. *IEEE Transactions on Pattern Analysis and
  Machine Intelligence* 26, 530–549. <https://doi.org/10.1109/TPAMI.2004.1273918>
