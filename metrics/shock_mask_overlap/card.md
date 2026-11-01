---
name: shock_mask_overlap
kind: metric
---

## Definition

The metric runs in two steps: a detector marks the shocked cells of each pressure field, and
the overlap of the two marked sets is reported.

**The detector** is the one of
[shock_set_distance](../../metrics/shock_set_distance/card.md), imported and not restated,
with its thresholds fixed there: a cell is shocked when, along some grid axis, the pressures
of its two neighbours differ by at least the Rankine-Hugoniot ratio of a Mach 1.3 shock,
1.805 at $\gamma = 1.4$ (the pressure half of criterion (iii) of [@schaal2015], Sect. 2.3.2,
with their Eq. (2); its Equation (1)). A cell beside a zero or negative pressure is never
flagged, and the detector's other conventions are stated on that card.

**The overlap.** Let $A$ and $B$ be the shocked cells of the reference and of the candidate.
The registered number is the Dice coefficient, [@taha2015], Eq. (6):

$$
\mathrm{DICE}(A, B) = \frac{2\,|A \cap B|}{|A| + |B|}, \tag{1}
$$

the number of cells flagged in both fields over the mean number flagged in each, introduced
by [@dice1945] to measure how often two species occur together. It is the F1 score of the
candidate's flags read as a prediction of the reference's ([@taha2015], Table 1). The
Jaccard index, or intersection over union, $|A \cap B| / |A \cup B|$ ([@jaccard1912];
[@taha2015], Eq. (7)), is not registered: it is the monotone function
$\mathrm{DICE} / (2 - \mathrm{DICE})$ of Equation (1) ([@taha2015], Eq. (8)), so it ranks
every set of candidates the same way, which Taha and Hanbury state in so many words.
[@maierhein2024], Suppl. Note 2.3, recommends "the DSC or IoU" as the default overlap score
and calls the choice between them a community preference; Dice is registered because it is
also the boundary F-score of the idea this bundle comes from at zero matching tolerance (my
derivation: at zero tolerance a flagged cell is matched only by the same cell, so precision
and recall are $|A \cap B|/|B|$ and $|A \cap B|/|A|$, whose harmonic mean is Equation (1)).

**Empty sets.** When one set is empty, Equation (1) gives 0. When both are, it is $0/0$, and
the metric returns 1: both fields agree there is no shock (my convention,
[issue 120](https://github.com/khegazy/pde_metrics/blob/main/issues/120-shock-mask-overlap-both-empty-convention.md)).
[@maierhein2024], Suppl. Note 2.3, would instead set an undefined value to the worst possible
one, 0, which charges a smooth prediction of a smooth reference as heavily as a missed shock.
Channels, of which pressure has one, are averaged. A field that is NaN or infinite anywhere
scores NaN.

The metric has no companion. The object behind the number is a per-cell map of which cells
both fields flag, which only the reference flags and which only the candidate flags; it is a
map of three classes, and none of the registry's reductions (a mean, a sum, a root mean or a
maximum of one map) turns it into the ratio of Equation (1).

### Boundary handling

The overlap counts cells and never looks beyond one. The detector's stencil reaches one cell
beyond the domain, and there the field is extended by repeating its edge value, a
zero-gradient wall, so nothing wraps around; a jump that sits exactly on the seam of a
periodic grid is missed. The metric takes no Fourier transform, does not declare
`requires_periodic`, and runs on the bounded `sod_shock_tube`.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED performance -->

## Intuition

The metric asks whether a prediction puts its shocks in exactly the right cells. A shock is a
thin layer across which the pressure jumps; the detector marks the cells on either side of
every jump steep enough to be a shock, in both fields. The metric then counts the marked cells
the two fields have in common and divides by the average number each field marked. A
prediction with every shock in the right cells scores 1; one whose shocks share no cell with
the true ones scores 0.

A worked example on eight cells, one row each:

```
reference   1    1    1    1    0.1  0.1  0.1  0.1     shocked cells: 4th and 5th
candidate   1    1    1    1    1    0.1  0.1  0.1     shocked cells: 5th and 6th
```

The jump of a factor ten marks the two cells beside it. The fields share one marked cell, the
5th, and each marked two, so the result is 2 times 1 over 2 plus 2, which is 0.5. Moved two
cells instead, the two pairs share no cell and the result is 0; moved three cells, it is
still 0.

That last line is the metric's character. A shock occupies two cells, so once it has moved two
cells the overlap is gone, and a miss by two cells scores the same as a miss across the whole
domain. The metric ignores how far apart non-coinciding shocks are, how strong a shock is,
and every smooth part of the field.

## Reading the output

- **Range and units.** From 0 to 1, dimensionless. NaN when either field is NaN or infinite
  anywhere.
- **Direction.** Higher is better; 1 means the two fields have their shocks in the same cells,
  or both have none.
- **What a value means.** For one sharp shock in each field, which the detector marks as two
  cells, 1 means the same cells, 0.5 a shift of one cell, and 0 a shift of two cells or more,
  or a shock in one field only. Values between those come from shocks the detector marks with
  a different number of cells, or from cells marked away from any shock, as noise can mark
  them. A value of 0 does not say whether the shock was a few cells off, far off, or missing.
- **Valid comparisons.** Values on one grid compare directly. Across grids they do not: a
  sharp shock is marked as two cells whatever the cell size, so the same displacement in length is
  more cells, and a lower score, on a finer grid. That holds for a sharp shock, which the
  detector marks as two cells on any grid; a shock a solver spreads over a few cells is marked
  over a number of cells that also depends on the grid.
- **The damage scale.** The repository's damage 1 is the score of the field's spatial mean,
  which has no shock and so scores 0 against a reference that has one; damage is then one
  minus the value.

## Limitations

- **A near miss scores the same as a far miss.** Two cells of displacement drive the value to
  0, and every larger displacement leaves it there; overlap scores "provide the same value
  regardless of how far the segments are from each other" ([@taha2015]). On a shock-tube
  translation the metric distinguishes no shift of two cells or more, so it cannot rank two
  predictions whose shocks are both a few cells off, the case a model-selection score most
  needs to rank. [shock_set_distance](../../metrics/shock_set_distance/card.md) measures how
  far.
- **A smeared shock disappears.** The detector compares only the two neighbours of a cell, so
  a shock spread over more than about four cells is not marked at all and the value drops to
  0 as for a missing shock (the estimate is on the detector's card). A prediction that
  captures the shock a little diffusely therefore scores the same as one with no shock.
- **Two empty sets score 1.** A prediction that smooths away every shock of a reference that
  has none scores perfectly, which is right; but on a frame with a shock the same prediction
  scores 0, so the value can jump from 1 to 0 between frames of one trajectory according to
  whether the reference happens to hold a shock
  ([issue 120](https://github.com/khegazy/pde_metrics/blob/main/issues/120-shock-mask-overlap-both-empty-convention.md)).
- **False detections and missed shocks count alike.** A marked cell away from any shock in the
  candidate costs the same as a true shocked cell the candidate missed, and many false marks
  can push a value with the right shock in the right cells well below 1.
- **The detector's limits carry over.** No compression gate, a fixed ratio of specific heats,
  and nothing defined for a gauge pressure; each is stated on the detector's card.
- **Only one dimension is evidenced.** The only dataset with a shock is the one-dimensional
  Sod tube, with one shock per field. Many shocklets in two or three dimensions are untested
  ([issue 002](https://github.com/khegazy/pde_metrics/blob/main/issues/002-shocklet-dataset.md)).

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED run -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_smoothing -->

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_geometric -->

### Resolution loss

[coarsen](../../degradations/coarsen/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_resolution -->

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_canaries -->

## References

\bibliography
