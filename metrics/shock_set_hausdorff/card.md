---
name: shock_set_hausdorff
kind: metric
---

## Definition

The shock sets are those of [shock_set_distance](../../metrics/shock_set_distance/card.md),
found by the same detector: a cell is shocked when, along some grid axis, the pressures of its
two neighbours differ by at least the Rankine-Hugoniot ratio of a Mach 1.3 shock, 1.805 at
$\gamma = 1.4$ (the pressure half of criterion (iii) of [@schaal2015], Sect. 2.3.2; that card's
Equation (1) and the choices stated beside it). Let $A$ and $B$ be the shocked cells of the
reference and of the candidate, each cell standing for its centre, and
$d(x, S) = \min_{y \in S} \lVert x - y \rVert$ the Euclidean distance at the grid's own spacing.
The directed Hausdorff distance is the largest distance from a point of one set to the other set,
and the registered number is the larger of the two directions, [@taha2015], Eqs. (48)-(49):

$$
\mathrm{HD}(A, B) = \max\Bigl( \max_{a \in A} d(a, B),\; \max_{b \in B} d(b, A) \Bigr). \tag{1}
$$

It is also the largest difference over every cell $x$ of the grid between the two sets' distance
maps, $\max_x \lvert d(x, A) - d(x, B) \rvert$, which is Baddeley's Delta at an infinite exponent
and no cutoff ([@spatstatdelta], Details); the weather-verification package SpatialVx computes it
that way, and `test_metric.py` checks the two forms agree. Every flagged cell is a point of the
set, as in `shock_set_distance`. A sharp step moved by $s \ge 1$ cells flags two cells in each
field, and the farther cell of each pair is $s$ cells from the nearer of the other, so

$$
\mathrm{HD} = s\,\Delta x, \tag{2}
$$

half a cell more than `shock_set_distance`'s $s - \tfrac{1}{2}$; `test_metric.py` checks this on
the exact Sod solution.

**Empty sets** are scored as `shock_set_distance` scores them, by the same code: two empty sets
0, one empty set the length of the domain's diagonal, the worst value [@maierhein2024], Suppl.
Note 2.3, recommend for an undefined distance; both are conventions
([issue 102](https://github.com/khegazy/pde_metrics/blob/main/issues/102-shock-set-distance-empty-and-non-positive-conventions.md)).
Channels, of which pressure has one, are averaged, and a field that is NaN or infinite anywhere
scores NaN.

### Boundary handling

As for `shock_set_distance`: the detector extends the field by its edge value, a zero-gradient
wall, and the distance transform measures across the domain and never around it, so the metric
is exact on bounded domains and approximate on periodic ones. It does not declare
`requires_periodic` and runs on the bounded `sod_shock_tube`.

### How its field reports it

- **Medical image segmentation** reports the Hausdorff distance per case beside an overlap score,
  as the worst boundary error, and warns that it is "generally sensitive to outliers" and "not
  recommended" for direct use ([@taha2015], beside Eq. (48)); its 95th-percentile form,
  [shock_set_hausdorff95](../../metrics/shock_set_hausdorff95/card.md), is the usual answer.
  Implementations measure between the borders of the two masks ([@medpy], `hd`); here every
  flagged cell is used, as on `shock_set_distance`'s card, which describes the field's empty-set
  practice and its test sets.
- **Spatial forecast verification** computes it for binary event fields as the limit of
  Baddeley's Delta ([@spatstatdelta]; [@spatialvx], `locmeasures2d`, measure "haus"), beside
  [shock_set_baddeley_delta](../../metrics/shock_set_baddeley_delta/card.md), which it bounds.
  The field's test cases and the scores not built here are on `shock_set_distance`'s card.
- **Shock detection in computational fluid dynamics** reports where the detector fires against
  the exact shock, on blast waves and shock tubes ([@schaal2015], Sect. 3), not a distance
  between two detected sets; `shock_set_distance`'s card says how this repository's Sod run
  stands in for it and which tests are missing.

The metric needs pressure, so it runs only on `sod_shock_tube`, an analytic check; the skip on
every other dataset is derived from the data. The missing experiments are those of
`shock_set_distance`:
[EXP-shock_set_distance-2d-shock-dataset](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-shock_set_distance-2d-shock-dataset.md),
[EXP-shock_mask_overlap-geometric-and-perturbed-cases](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-shock_mask_overlap-geometric-and-perturbed-cases.md)
and
[EXP-sod_evidence-sod-time-offset](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-sod_evidence-sod-time-offset.md).

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence shock_set_hausdorff`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_hausdorff`.

<!-- END GENERATED performance -->

## Intuition

The metric finds the shocks in both fields and reports the worst-placed shocked cell of either:
the largest distance from any shocked cell of one field to the nearest shocked cell of the other.
A displaced shock costs its displacement; a single false detection far from any true shock costs
its whole distance, however right the rest of the field is.

A worked example on sixteen cells of unit width. The reference is a pressure step of a factor
ten, which marks the two cells beside the jump, the 8th and 9th. One candidate moves the step two
cells; another keeps it in place but adds a one-cell spike of ten in the high state, which marks
its two neighbours, the 1st and 3rd cells, as false shocks.

```
reference   1 1 1 1 1 1 1 1 .1 .1 .1 .1 .1 .1 .1 .1     marked: 8th, 9th
moved       1 1 1 1 1 1 1 1  1  1 .1 .1 .1 .1 .1 .1     marked: 10th, 11th
spike       1 10 1 1 1 1 1 1 .1 .1 .1 .1 .1 .1 .1 .1    marked: 1st, 3rd, 8th, 9th

                     this metric   shock_set_distance
moved                2             1.5
spike                7             2
```

For the moved step the farther marked cell of each pair is two cells from the other pair, so the
value is 2, where the average distance is 1.5. For the spike the true shock is matched exactly,
but the false mark in the 1st cell is seven cells from the nearest true one, and the value is 7.

The metric ignores everything but the single worst cell: how many cells are misplaced, the
strength of the shock, and every smooth part of the field.

## Reading the output

- **Range and units.** From 0 to the length of the domain's diagonal, in the units of the grid
  spacing: on the unit-length Sod tube, 0 to 1. NaN when either field is NaN or infinite
  anywhere.
- **Direction.** Lower is better; 0 means the shocks are in the same cells, or neither field has
  one.
- **What a value means.** Below the diagonal, the distance of the worst-placed shocked cell: for
  one sharp shock moved by a whole number of cells, the shift itself (Equation (2)). Exactly the
  diagonal means one field has a shock and the other has none, a flag rather than a distance.
- **Valid comparisons.** Values on one grid and one domain compare directly; across grids divide
  by the spacing, since a shock spans a number of cells; across domains compare only values below
  the diagonal. Read beside `shock_set_distance`: a Hausdorff distance far above the average says
  one outlying cell sets it.
- **The damage scale** is the value as a fraction of the diagonal, as on `shock_set_distance`'s
  card, so a misplaced shock reads as a damage of a few thousandths on 2048 cells.
- **Companions.** `shock_set_hausdorff`, the detected shock cells of one field as rows of (cell
  index along the first grid axis, pressure there), and `shock_set_hausdorff.profile`, the
  pressure itself, stored for the candidate on the frames `report.error_map` names and on their
  clean level, the reference, and drawn together as the line-out figure.

## Limitations

- **One cell sets the value.** A single false detection anywhere, from noise or a spurious
  oscillation, replaces the distance of the true shock by its own; the spike example costs 7
  cells with the shock exactly right.
- **The detector's limits carry over.** A shock smeared over more than about four cells is not
  detected and the value jumps to the diagonal; there is no compression gate; the ratio of specific
  heats is fixed; a gauge pressure gets a number that means nothing. Each is stated on
  `shock_set_distance`'s card.
- **One cell decides between a distance and a flag**, as for `shock_set_distance`: a harsher
  degradation that leaves one flagged cell anywhere scores below the diagonal and so better than a
  milder one that removed the shock.
- **Only one dimension is evidenced.** The only dataset with a shock is the one-dimensional Sod
  tube, with one shock per field
  ([issue 002](https://github.com/khegazy/pde_metrics/blob/main/issues/002-shocklet-dataset.md)).

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence shock_set_hausdorff`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_hausdorff`.

<!-- END GENERATED run -->

Each subsection links to the degradations that subsection reports. What those degradations
do, and what their strength numbers mean, is documented on their own pages.

<!-- GENERATED experiments: written by `python -m fmeval.cards catalog`, do not edit -->

**Across the experiments.**

| experiment | what a run on it is evidence of | on this card |
|---|---|---|
| `kinet_re5e4` | developed flow | not applicable: needs pressure, which this dataset does not provide |
| `kinet_re1e6` | developed flow at Re = 1e6, twenty times the Reynolds number of kinet_re5e4, from the same initial condition | not applicable: needs pressure, which this dataset does not provide |
| `synthetic_ensemble` | a calibrated null: evidence that the estimator computes what it claims to compute, and nothing about turbulence | not applicable: needs pressure, which this dataset does not provide |
| `sod_shock_tube` | an analytic check: evidence that the metric locates and scores a known shock correctly, and nothing about turbulence | not yet run |
| `forecast_re5e4` | real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded | not applicable: needs pressure, which this dataset does not provide |

One row per dataset a card may cite (`configs/cards/default.yaml`). *Measured* names the run the card cites: the main results are `## Performance` and the subsections below, and every other run has its own subsection headed with its dataset. *Not applicable* gives the reason: one that follows from what the metric declares and what the dataset offers, or one a person wrote on the card (`not_run` in `card.yaml`) because the result would carry no information. *Not yet run* means the metric can run there and the card cites no run on it yet.

<!-- END GENERATED experiments -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence shock_set_hausdorff`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_hausdorff`.

<!-- END GENERATED results_smoothing -->

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence shock_set_hausdorff`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_hausdorff`.

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence shock_set_hausdorff`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_hausdorff`.

<!-- END GENERATED results_geometric -->

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence shock_set_hausdorff`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_hausdorff`.

<!-- END GENERATED results_resolution -->

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence shock_set_hausdorff`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_hausdorff`.

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence shock_set_hausdorff`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_hausdorff`.

<!-- END GENERATED results_canaries -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence shock_set_hausdorff`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_hausdorff`.

<!-- END GENERATED results_summary -->

## References

\bibliography
