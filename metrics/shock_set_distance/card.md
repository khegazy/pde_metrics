---
name: shock_set_distance
kind: metric
---

## Definition

The metric runs in two steps: a detector marks the shocked cells of each pressure field, and
a distance between the two marked sets is reported.

**The detector.** Let $p$ be one channel of the pressure. A cell $\mathbf{n}$ is shocked when,
along some spatial axis $j$ with unit step $\mathbf{e}_j$, the pressures of its two
neighbours differ by at least the ratio across a normal shock of Mach number
$M_{\min} = 1.3$:

$$
\max\bigl(p_{\mathbf{n}-\mathbf{e}_j},\, p_{\mathbf{n}+\mathbf{e}_j}\bigr) \;\ge\; R \,
\min\bigl(p_{\mathbf{n}-\mathbf{e}_j},\, p_{\mathbf{n}+\mathbf{e}_j}\bigr),
\qquad
R = \frac{2\gamma M_{\min}^2}{\gamma + 1} - \frac{\gamma - 1}{\gamma + 1}. \tag{1}
$$

This is the pressure half of the shock-zone criterion (iii) of [@schaal2015], Sect. 2.3.2,
$\Delta \log p \ge \log(p_2/p_1)|_{M_{\min}}$, written without the logarithm; $R$ is their
Rankine-Hugoniot pressure ratio, Eq. (2), and $M_{\min} = 1.3$ is the value of the same
section. With $\gamma = 1.4$, the ratio of specific heats of the `sod_shock_tube` dataset, read
from its reader rather than restated, $R = 1.805$.
Schaal and Springel state that a minimum pressure jump "discriminates against tangential
discontinuities and contacts": a contact carries a density jump and no pressure jump, so it is
not flagged. Three choices here are mine, not theirs. The jump is tested along every grid axis
and any axis flags the cell, where they measure it along the shock direction, which needs a
temperature gradient this metric is not given. Their criteria (i) and (ii), on the velocity
divergence and the temperature and density gradients, need fields a metric handed one field
does not receive, so only criterion (iii) is applied. And a non-positive pressure satisfies
Equation (1) automatically, so a cell beside one is flagged: the ratio across it is unbounded
([issue 102](https://github.com/khegazy/pde_metrics/blob/main/issues/102-shock-set-distance-empty-and-non-positive-conventions.md)).

**The distance.** Let $A$ and $B$ be the shocked cells of the reference and of the candidate,
each cell standing for its centre, and $d(x, S) = \min_{y \in S} \lVert x - y \rVert$ the
Euclidean distance from a point to a set at the grid's own spacing ([@yeghiazaryan2018],
Sect. 2.3; it is the minimum inside the directed distances of [@taha2015], Eqs. (49) and
(51)). The registered number is the average symmetric surface distance, "the average of all
the distances from points on the boundary of machine segmented region to the boundary of the
ground truth, and vice versa" ([@yeghiazaryan2018], Sect. 2.3.2, unnumbered in the copy read):

$$
\mathrm{ASSD}(A, B) = \frac{\sum_{a \in A} d(a, B) + \sum_{b \in B} d(b, A)}{|A| + |B|}. \tag{2}
$$

Every flagged cell is a point of the set; no boundary is extracted from the mask, because a
detected shock is already a thin layer (my choice). A sharp jump between two cells flags both
of them, so moving a sharp step by $s \ge 1$ cells gives, from Equation (2),

$$
\mathrm{ASSD} = \Bigl(s - \tfrac{1}{2}\Bigr)\Delta x, \tag{3}
$$

because each flagged cell's nearest partner is $s - 1$ or $s$ cells away. A sharp shock moved by
$s$ cells therefore scores half a cell less than $s$ cells, and the one-dimensional distance
between two shock positions $|x - x'|$ is recovered to within half a cell.

**Empty sets.** Equation (2) is undefined when a set is empty. Two empty sets score $0$: both
fields agree there is no shock (my choice). One empty set scores the length of the domain's
diagonal, $\sqrt{\sum_j (N_j \Delta x_j)^2}$, the worst-possible value that [@maierhein2024],
Suppl. Note 2.3, recommends for an undefined distance, naming the image diagonal; it exceeds
the distance between any two cell centres, so a missed or invented shock always scores worse
than a misplaced one. Both are conventions
([issue 102](https://github.com/khegazy/pde_metrics/blob/main/issues/102-shock-set-distance-empty-and-non-positive-conventions.md)).
Channels, of which pressure has one, are averaged.

**Not registered.** [@taha2015] give three other summaries of the same nearest-point distances:
the Hausdorff distance, the larger of the two directed maxima, Eq. (48), which they call
"generally sensitive to outliers"; its quantile form, which they call "one way to handle
outliers"; and the average distance, the larger of the two directed means, Eq. (50), which they
call "stable and less sensitive to outliers than the HD". [@maierhein2024], Suppl. Note 2.3,
recommends the mean of the two directed means over Equation (2) as its default. For a single
shock in each field all of these are equal; they differ when the detector flags cells away
from the shock. Each would be a sibling bundle importing `surface_distances`.

### Boundary handling

The detector's stencil reaches one cell beyond the domain. There the field is extended by
repeating its edge value, a zero-gradient wall, so an edge cell compares itself with its one
inner neighbour; nothing wraps around. The distance transform measures straight across the
domain and never around it. On a periodic grid this misses a jump that sits exactly on the
seam and overstates the distance between two shocks on either side of it, so the metric is
exact on bounded domains and approximate on periodic ones. It takes no Fourier transform and
does not declare `requires_periodic`, and it runs on the bounded `sod_shock_tube`.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED performance -->

## Intuition

The metric asks where the shocks are, not what values the field takes. A shock is a thin layer
across which the pressure jumps; a prediction can get its strength exactly right and still
place it a few cells off. A cell-by-cell error charges that twice, once where the shock should
be and once where it is. This metric finds the shocks in both fields and reports how far
apart they lie, as a length.

It works in two steps. First, a cell counts as shocked when the pressures on its two sides
differ by a factor of at least 1.805, the pressure jump across the weakest shock the detector
reports, one moving at 1.3 times the speed of sound. A smooth pressure change spread over many
cells never reaches that factor between neighbours, and a contact surface, where only the
density jumps, has no pressure jump at all. Second, every shocked cell in each field is
measured to the nearest shocked cell of the other field, and all of those distances are
averaged.

A worked example on eight cells of unit width, one row each:

```
reference   1    1    1    1    0.1  0.1  0.1  0.1     shocked cells: 4th and 5th
candidate   1    1    1    1    1    1    0.1  0.1     shocked cells: 6th and 7th
```

The jump of a factor ten flags the two cells on either side of it. The reference's shocked
cells are 2 and 1 cells from the nearest shocked candidate cell, and the candidate's are 1 and
2 cells from the reference's, so the result is 6 / 4 = 1.5 cells. Moved by one cell instead,
the two pairs share a cell and the result is 0.5. A candidate with no jump at all would score
the length of the domain, 8 cells.

The metric ignores everything except where the detector fires: the strength of a shock, the
state on either side of it, and every smooth part of the field.

## Reading the output

- **Range and units.** From 0 to the length of the domain's diagonal, in the units of the grid
  spacing: on the unit-length Sod tube, 0 to 1.
- **Direction.** Lower is better; 0 means the two fields have their shocks in the same cells,
  or both have none.
- **What a value means.** Below the diagonal, the value is a distance between shocks that
  both fields have: half a cell less than the shift, for one sharp shock moved by a whole
  number of cells (Equation (3)). Exactly the diagonal means one field has a shock and the
  other has none, which is a different failure from a misplaced shock, and the value should
  be read as a flag rather than as a distance. A value between a few cells and the diagonal
  usually means the detector flagged cells away from any shock, for example in noise.
- **Valid comparisons.** Values on one grid and one domain compare directly. Across grids,
  divide by the spacing, because a shock captured on a coarser grid spans more cells. Across
  domains, the empty-set value changes with the diagonal, so compare only values below it.

## Limitations

- **A smeared shock disappears.** The detector compares the two neighbours of a cell only. If
  the log pressure rises linearly across a shock of width $w$ cells, the two neighbours see
  $2/w$ of its jump, so Sod's shock, a pressure ratio of 3.03, is no longer flagged once it is
  wider than $2 \ln 3.03 / \ln 1.805 = 3.8$ cells (my estimate), and the score jumps to the
  diagonal. Schaal and Springel measure the jump
  across the whole shock zone instead [@schaal2015], which would tolerate a wide shock but needs
  the velocity and temperature this metric does not receive.
- **No compression gate.** Without the velocity divergence, any steep enough pressure change
  is flagged, compressive or not, and noise whose cell-to-cell ratio exceeds 1.805 is flagged
  as shocks. A sensor gated on dilatation, as Ducros et al. propose for shock capturing in
  turbulence [@ducros1999], would reject both, but needs the velocity
  ([issue 096](https://github.com/khegazy/pde_metrics/blob/main/issues/096-several-fields-handed-to-one-metric.md)).
- **A fixed equation of state.** The threshold uses $\gamma = 1.4$ whatever the gas. For $\gamma$
  between 1.1 and 2 the ratio $R$ moves only between 1.72 and 1.92, but a dataset of another gas
  shifts the weakest shock reported.
- **Pooling favours the larger set.** Equation (2) weights each direction by its number of
  points, so a candidate with many spurious detections is scored mostly by how far they lie
  from the true shock, and a missed weak shock beside a strong one barely moves the value.
- **Only one dimension is evidenced.** The distance transform and the detector are written
  for any number of dimensions, but the only dataset with a shock is the one-dimensional Sod
  tube, where each field has one shock. Many shocklets in two or three dimensions, the case
  this metric is meant for, are untested
  ([issue 002](https://github.com/khegazy/pde_metrics/blob/main/issues/002-shocklet-dataset.md)).
  Matching objects between forecast and observation before measuring their distances, as
  weather verification does [@davis2006a], is not done here: every shocked cell is matched to
  the nearest one, whichever shock it belongs to.

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

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_summary -->

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_damage_by_level -->

## References

\bibliography
