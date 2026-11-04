---
name: shock_set_baddeley_delta
kind: metric
---

## Definition

The shock sets are those of [shock_set_distance](../../metrics/shock_set_distance/card.md),
found by the same detector (the pressure half of criterion (iii) of [@schaal2015], Sect. 2.3.2, at
Mach 1.3; that card's Equation (1)). Let $A$ and $B$ be the shocked cells of the reference and of
the candidate, and for every cell $x$ of the grid, shocked or not, let
$d(x, S) = \min_{y \in S} \lVert x - y \rVert$ be the Euclidean distance from its centre to the
nearest cell of $S$ at the grid's own spacing. Baddeley's Delta compares the two distance maps
over the whole grid of $N$ cells:

$$
\Delta_{p}^{w}(A, B) = \Bigl[ \frac{1}{N} \sum_{x} \bigl\lvert w\bigl(d(x, A)\bigr) -
w\bigl(d(x, B)\bigr) \bigr\rvert^{p} \Bigr]^{1/p}, \qquad w(t) = \min(t, c), \tag{1}
$$

the definition of [@baddeley1992] as its own implementation states and computes it on a pixel
image, the mean over the window of the $p$-th power of the difference of the two distance maps,
each cut off at $c$ ([@spatstatdelta], Details and source). The registered number takes that
implementation's defaults, $p = 2$ and $c = \infty$, which leave the maps uncut; SpatialVx, Gilleland's
spatial-verification package, whose documentation cites [@gilleland2011] for the metric, calls
the same function with the same defaults ([@spatialvx], `locmeasures2d`, arguments `p = 2`
and `bdconst`, which is set to infinity when left empty). At $p = \infty$ and $c = \infty$
Equation (1) is the Hausdorff distance of
[shock_set_hausdorff](../../metrics/shock_set_hausdorff/card.md) [@spatstatdelta]; since
$\lvert d(x, A) - d(x, B) \rvert$ never exceeds that distance, Equation (1) never does either
(`test_metric.py` checks the bound). Unlike the surface distances of `shock_set_distance`, every
cell of the grid enters, shocked or not.

For one pair of flagged cells moved by $s$ cells along a long one-dimensional grid, the two maps
differ by exactly $s$ at every cell outside the $s + 2$ cells the two pairs span, so
$\Delta \approx s$ cells, slightly less (`test_metric.py` checks the bounds on 2048 cells).

**Empty sets.** The distance map of an empty set is infinite everywhere, so Equation (1) is
undefined with $c = \infty$. The sets are scored as `shock_set_distance` scores them, by the same
code: two empty sets 0, one empty set the domain's diagonal, which bounds Equation (1) for any two
non-empty sets; both are conventions
([issue 102](https://github.com/khegazy/pde_metrics/blob/main/issues/102-shock-set-distance-empty-and-non-positive-conventions.md)).
Channels, of which pressure has one, are averaged, and a field that is NaN or infinite anywhere
scores NaN.

### Boundary handling

The detector extends the field by its edge value, a zero-gradient wall, as for
`shock_set_distance`. The distance maps are exact Euclidean distance transforms that measure
across the domain and never around it, over the grid's own cells, as `spatstat`'s window is the
image's own extent. The metric is exact on bounded domains and approximate on periodic ones; it
does not declare `requires_periodic` and runs on the bounded `sod_shock_tube`.

### How its field reports it

- **Spatial forecast verification**, whose methods fall into the neighbourhood, scale-separation,
  features-based and field-deformation families [@gilleland2009], uses Baddeley's Delta as "a
  mathematical displacement metric" for gridded forecasts against gridded observations,
  thresholded into binary event fields, and tested it on the intercomparison project's test cases
  [@gilleland2011]: geometric forecasts displaced, enlarged and stretched by known amounts and real
  fields shifted by known distances [@ahijevych2009]. The value is reported per case and per
  threshold, beside the Hausdorff distance and the mean error distances that the same package
  computes ([@spatialvx], `locmeasures2d`). The full text of [@gilleland2011] could not be read
  here, so the constant $c$ and exponent $p$ it used are not known; this bundle takes the
  package's defaults. The test cases are written up for shock sets in
  [EXP-shock_mask_overlap-geometric-and-perturbed-cases](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-shock_mask_overlap-geometric-and-perturbed-cases.md);
  the field's neighbourhood and categorical scores are not built, for the reason on
  `shock_set_distance`'s card.
- **Image analysis**, where [@baddeley1992] introduced it as an error metric for binary images,
  topologically equivalent to the Hausdorff metric but more stable in practice
  ([@spatstatdelta], Details).
- **Shock detection in computational fluid dynamics** compares the detector with the exact shock
  rather than two detected sets ([@schaal2015], Sect. 3); see `shock_set_distance`'s card.

The metric needs pressure, so it runs only on `sod_shock_tube`, an analytic check; the skip on
every other dataset is derived from the data. The missing experiments are those of
`shock_set_distance`:
[EXP-shock_set_distance-2d-shock-dataset](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-shock_set_distance-2d-shock-dataset.md),
[EXP-shock_mask_overlap-geometric-and-perturbed-cases](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-shock_mask_overlap-geometric-and-perturbed-cases.md)
and
[EXP-sod_evidence-sod-time-offset](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-sod_evidence-sod-time-offset.md).

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence shock_set_baddeley_delta`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_baddeley_delta`.

<!-- END GENERATED performance -->

## Intuition

The metric finds the shocks in both fields and then, for every cell of the grid, measures how far
that cell is from the nearest shock of each field. Where the two fields' shocks are in the same
place, the two distances agree everywhere; where they are not, they disagree, by up to the
displacement. The metric reports the root mean square of the disagreement over all cells. A false
shock far away therefore matters in proportion to how many cells it is the nearest shock to.

A worked example on sixteen cells of unit width. The reference is a pressure step of a factor
ten, which marks the two cells beside the jump, the 8th and 9th. One candidate moves the step two
cells; another keeps it in place but adds a one-cell spike of ten in the high state, which marks
its two neighbours, the 1st and 3rd cells, as false shocks.

```
reference   1 1 1 1 1 1 1 1 .1 .1 .1 .1 .1 .1 .1 .1     marked: 8th, 9th
moved       1 1 1 1 1 1 1 1  1  1 .1 .1 .1 .1 .1 .1     marked: 10th, 11th
spike       1 10 1 1 1 1 1 1 .1 .1 .1 .1 .1 .1 .1 .1    marked: 1st, 3rd, 8th, 9th

                     this metric   shock_set_hausdorff   shock_set_distance
moved                1.904         2                     1.5
spike                2.610         7                     2
```

For the moved step the two distance maps differ by 2 at fourteen cells and by 1 at two, so the
root mean square is the square root of 58/16, 1.904: close to the shift. For the spike the maps
differ only at the five cells nearest the false marks, by 7, 5, 5, 3 and 1, and the root mean
square is the square root of 109/16, 2.610, far below the Hausdorff distance's 7.

The metric ignores the strength of the shock and every smooth part of the field, and its value
depends on the size of the grid as well as on the shocks.

## Reading the output

- **Range and units.** From 0 to the Hausdorff distance between the two shock sets, and so below
  the length of the domain's diagonal, in the units of the grid spacing; NaN when either field is
  NaN or infinite anywhere.
- **Direction.** Lower is better; 0 means the shocks are in the same cells, or neither field has
  one.
- **What a value means.** Below the diagonal, a root-mean-square disagreement between where the
  two fields' nearest shocks are; for one shock moved along a long tube, nearly the shift.
  Exactly the diagonal means one field has a shock and the other none, a flag rather than a
  distance.
- **Valid comparisons.** On one grid and one domain directly. Across domains of different size
  the mean over cells changes with the domain, even for the same shocks, so values do not compare.
- **The damage scale** is the value as a fraction of the diagonal, as on `shock_set_distance`'s
  card.
- **Companions.** `shock_set_baddeley_delta`, the detected shock cells of one field as rows of
  (cell index along the first grid axis, pressure there), and `shock_set_baddeley_delta.profile`,
  the pressure itself, stored for the candidate on the frames `report.error_map` names and on
  their clean level, the reference, and drawn together as the line-out figure.

## Limitations

- **The domain enters the value.** Every cell is averaged, so a false shock in a large empty
  region weighs more than the same false shock in a small one, and the same error scores
  differently on a longer tube. With $c = \infty$, cells far from both fields' shocks still carry
  the full displacement.
- **No cutoff chosen for this data.** The cutoff $c$, the distance beyond which the
  implementation stops counting, is left at infinity, its default, because no source read here
  fixes it for shocks, and a value tuned to make this metric behave would be the threshold tuning
  the repository forbids.
- **The detector's limits carry over**: a smeared shock is lost and the value jumps to the
  diagonal, there is no compression gate, the ratio of specific heats is fixed and a gauge
  pressure gets a meaningless number (`shock_set_distance`'s card).
- **Only one dimension is evidenced**, the Sod tube with one shock per field
  ([issue 002](https://github.com/khegazy/pde_metrics/blob/main/issues/002-shocklet-dataset.md)).

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence shock_set_baddeley_delta`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_baddeley_delta`.

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

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence shock_set_baddeley_delta`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_baddeley_delta`.

<!-- END GENERATED results_smoothing -->

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence shock_set_baddeley_delta`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_baddeley_delta`.

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence shock_set_baddeley_delta`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_baddeley_delta`.

<!-- END GENERATED results_geometric -->

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence shock_set_baddeley_delta`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_baddeley_delta`.

<!-- END GENERATED results_resolution -->

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence shock_set_baddeley_delta`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_baddeley_delta`.

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence shock_set_baddeley_delta`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_baddeley_delta`.

<!-- END GENERATED results_canaries -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence shock_set_baddeley_delta`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_baddeley_delta`.

<!-- END GENERATED results_summary -->

## References

\bibliography
