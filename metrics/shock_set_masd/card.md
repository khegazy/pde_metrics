---
name: shock_set_masd
kind: metric
---

## Definition

The shock sets are those of [shock_set_distance](../../metrics/shock_set_distance/card.md),
found by the same detector (the pressure half of criterion (iii) of [@schaal2015], Sect. 2.3.2, at
Mach 1.3; that card's Equation (1)). With $A$ and $B$ the shocked cells of the reference and of
the candidate, each cell standing for its centre, and
$d(A, B) = \frac{1}{|A|} \sum_{a \in A} \min_{b \in B} \lVert a - b \rVert$ the directed average
distance at the grid's own spacing ([@taha2015], Eq. (51)), the registered number is the mean of
the two directions:

$$
\mathrm{MASD}(A, B) = \tfrac{1}{2} \bigl( d(A, B) + d(B, A) \bigr), \tag{1}
$$

the mean average surface distance, as the Metrics Reloaded code computes it
([@metricsreloadedcode], `measured_masd`). [@maierhein2024], Suppl. Note 2.3, recommend it as the
default boundary distance when errors should be penalised by distance, because it "has
mathematical advantages over" the average symmetric surface distance that `shock_set_distance`
registers. The two differ only in weighting: `shock_set_distance` pools every distance, so each
direction counts in proportion to its number of cells, while Equation (1) gives each direction
half. They are equal when the two sets have the same number of cells, as for a sharp shock moved
by $s \ge 1$ cells, where both are $s - \tfrac{1}{2}$ cells. Every flagged cell is a point of the
set, as in `shock_set_distance`.

**Empty sets** are scored as `shock_set_distance` scores them, by the same code: two empty sets
0, one empty set the domain's diagonal; both are conventions
([issue 102](https://github.com/khegazy/pde_metrics/blob/main/issues/102-shock-set-distance-empty-and-non-positive-conventions.md)).
Channels, of which pressure has one, are averaged, and a field that is NaN or infinite anywhere
scores NaN.

### Boundary handling

As for `shock_set_distance`: the detector extends the field by its edge value, a zero-gradient
wall, and the distance transform measures across the domain and never around it, so the metric
is exact on bounded domains and approximate on periodic ones. It does not declare
`requires_periodic` and runs on the bounded `sod_shock_tube`.

### How its field reports it

- **Medical image segmentation**, where it is Metrics Reloaded's recommended boundary distance
  ([@maierhein2024], Suppl. Note 2.3), reports it per case beside an overlap score, measured
  between the borders of the two masks; the consortium's code returns NaN when a set is empty and
  leaves the value to the aggregation ([@metricsreloadedcode], `measured_distance`). Here every
  flagged cell is used and the empty sets take this repository's conventions, as
  `shock_set_distance`'s card explains with the field's test sets.
- **Spatial forecast verification** reports the directed mean distances one at a time, as the
  "mean error distance" of each field to the other ([@spatialvx], `locmeasures2d`, measure "med");
  Equation (1) is their mean. The field's test cases and the scores not built here are on
  `shock_set_distance`'s card.
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

<!-- GENERATED performance: written by `python -m fmeval.cards evidence shock_set_masd`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_masd`.

<!-- END GENERATED performance -->

## Intuition

The metric finds the shocks in both fields and asks two questions: on average, how far is a
shocked cell of the reference from the nearest shocked cell of the candidate, and how far is a
shocked cell of the candidate from the nearest of the reference? It reports the mean of the two
answers. Missing a true shock and inventing a false one are charged through different questions,
and each question counts half, however many cells it is about.

A worked example on sixteen cells of unit width. The reference is a pressure step of a factor
ten, which marks the two cells beside the jump, the 8th and 9th. One candidate moves the step two
cells; another keeps it in place but adds a one-cell spike of ten in the high state, which marks
its two neighbours, the 1st and 3rd cells, as false shocks.

```
reference   1 1 1 1 1 1 1 1 .1 .1 .1 .1 .1 .1 .1 .1     marked: 8th, 9th
moved       1 1 1 1 1 1 1 1  1  1 .1 .1 .1 .1 .1 .1     marked: 10th, 11th
spike       1 10 1 1 1 1 1 1 .1 .1 .1 .1 .1 .1 .1 .1    marked: 1st, 3rd, 8th, 9th

                     this metric   shock_set_distance
moved                1.5           1.5
spike                1.5           2
```

For the moved step each direction's mean distance is 1.5, and so is their mean. For the spike the
reference's cells are all matched, a mean of 0, and the candidate's four cells are 7, 5, 0 and 0
away, a mean of 3: the metric reports 1.5. The pooled average of `shock_set_distance` counts the
candidate's four cells against the reference's two and reports 2.

The metric ignores the strength of the shock and every smooth part of the field, and it does not
say whether a value comes from a missed shock or a false one.

## Reading the output

- **Range and units.** From 0 to the length of the domain's diagonal, in the units of the grid
  spacing; NaN when either field is NaN or infinite anywhere.
- **Direction.** Lower is better; 0 means the shocks are in the same cells, or neither field has
  one.
- **What a value means.** Below the diagonal, an average distance between the two fields' shocks
  with the two directions weighted equally; $s - \tfrac{1}{2}$ cells for one sharp shock moved by
  $s$ cells. Exactly the diagonal means one field has a shock and the other none, a flag rather
  than a distance.
- **Valid comparisons.** As for `shock_set_distance`. The two differ by
  $(|A| - |B|)\,(d(A, B) - d(B, A)) / (2(|A| + |B|))$, so a MASD below `shock_set_distance`'s value
  says the field with more shocked cells is also the one whose cells lie farther from the other's,
  for example a candidate with false shocks; above it, the reverse.
- **The damage scale** is the value as a fraction of the diagonal, as on `shock_set_distance`'s
  card.
- **Companions.** `shock_set_masd`, the detected shock cells of one field as rows of (cell index
  along the first grid axis, pressure there), and `shock_set_masd.profile`, the pressure itself,
  stored for the candidate on the frames `report.error_map` names and on their clean level, the
  reference, and drawn together as the line-out figure.

## Limitations

- **Half the weight for any number of false shocks.** Many false detections and a few cost the
  same half of the value if they lie at the same mean distance, so a candidate covered in spurious
  shocks near the true one can score well.
- **A missed second shock is diluted.** If the reference has a strong and a weak shock and the
  candidate only the strong one, the weak one's distance is averaged over the reference's cells
  and halved.
- **The detector's limits carry over**: a smeared shock is lost and the value jumps to the
  diagonal, there is no compression gate, the ratio of specific heats is fixed and a gauge pressure
  gets a meaningless number (`shock_set_distance`'s card).
- **Only one dimension is evidenced**, the Sod tube with one shock per field
  ([issue 002](https://github.com/khegazy/pde_metrics/blob/main/issues/002-shocklet-dataset.md)).

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence shock_set_masd`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_masd`.

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

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence shock_set_masd`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_masd`.

<!-- END GENERATED results_smoothing -->

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence shock_set_masd`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_masd`.

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence shock_set_masd`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_masd`.

<!-- END GENERATED results_geometric -->

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence shock_set_masd`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_masd`.

<!-- END GENERATED results_resolution -->

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence shock_set_masd`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_masd`.

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence shock_set_masd`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_masd`.

<!-- END GENERATED results_canaries -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence shock_set_masd`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence shock_set_masd`.

<!-- END GENERATED results_summary -->

## References

\bibliography
