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

<!-- GENERATED performance: written by `python -m fmeval.cards evidence shock_set_masd --results results/comparison_1793812304`, do not edit -->

![the point sets behind the number, each degraded set over the reference's, as its field draws them](_generated/companion_points__field-pressure.svg)

*As this metric's own field draws it.* The point set behind shock_set_masd on pressure, one panel per stored variant, on shared axes. Grey rings are the clean level's set of the same frame, the reference's, drawn under every panel. The lines are the field's line-out on this one-dimensional grid against the cell index, the clean level's in grey. Triangles on a panel's edge are points with an infinite coordinate. Only the first 4 of the 5 stored sets are drawn, in time order; every set is in data/error_maps.npz.

![how the metric responded to each degradation, by field: rank correlation, separation of neighbouring strengths, damage per unit of field change, and the bound on its largest response](_generated/sensitivity_profile.svg)

Four measured statistics for shock_set_masd, one row per degradation grouped by family and one marker per field. From left: the rank correlation between the metric and the applied strength within a frame, with the line showing the resampling interval; the separation of neighbouring strengths as Cliff's delta, where 0 means the metric cannot tell one strength from the next and the faint ticks at 0.12, 0.28 and 0.42 are Vargha and Delaney's small, medium and large anchors, for scale and not as grades; the damage charged per unit of field change at the harshest strength; and the upper confidence bound on the largest damage, beside the fixed margin of 0.05. A hollow marker is a field and degradation on which that bound lies below the margin, so the response is provably small. A missing marker is a statistic the analysis withheld, as the rank correlation is on an axis the metric is invariant to.

![median damage against severity level, one panel per degradation family and field, on one shared scale](_generated/response_curves.svg)

Median damage over frames against severity level for shock_set_masd, one row per family of degradation and one column per field, on one shared scale. The solid grey line is damage 1, the anchor (by default the field's own mean); the dotted black line is the damage assigned to the fake prediction with the right spectrum, where the run included it. The hollow black ring marks the first level at which the metric has moved a tenth of the way to the anchor. Hollow grey markers are strengths excluded for repeating a milder one or for doing nothing. Degradations with three or fewer usable levels are drawn as markers only; points beyond 2 either side are drawn as triangles at the edge. Damage is negative where a degradation moves the metric away from the anchor, as noise raises a single-field quantity the field's mean sets to zero.

**Trend: does the response follow the degradation?**

| test family | field | degradations | rank correlation | fraction of frames in order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| Displacement | pressure | 2 | 0.986 to 1 | 0 to 1 | 0.5 to 1 |
| Cell-value distortion | pressure | 2 | 0.775 | 0 | 0.5 |
| Resolution loss | pressure | 3 | 0.775 | 0 | 0.5 |
| Smoothing | pressure | 4 | — | — | — |
| Spectral filtering | pressure | 5 | -1 to 1 | 0 to 0.1 | 0.45 to 0.55 |
| Noise | pressure | 2 | 0.707 to 0.949 | 0 | 0.5 |

**Reactivity: how far does it move?**

| test family | field | change from clean at the harshest strength | elasticity | first strength detected |
|---|---|---|---|---|
| Displacement | pressure | — | 1.4 | level — |
| Cell-value distortion | pressure | — | — | level 4 |
| Resolution loss | pressure | — | 6.29 | level 2 |
| Smoothing | pressure | — | — | level — |
| Spectral filtering | pressure | — | — | level — |
| Noise | pressure | — | — | level 5 |
| trap test: fake prediction, right spectrum | pressure | — | — | damage 1 |

**Consistency: how much does it vary from snapshot to snapshot?**

| test family | field | consistency, in the strength's units | snapshots per independent block |
|---|---|---|---|
| Displacement | pressure | 0 | 1 |
| Cell-value distortion | pressure | 0 | 1 |
| Resolution loss | pressure | 3.91 to 7.11 | 1 |
| Smoothing | pressure | — | 1 |
| Spectral filtering | pressure | 0.316 to 1.64 | 1 |
| Noise | pressure | 0.141 to 0.198 | 1 |

One row per family of degradation and physical field; a cell gives the range over the degradations in that family. **Trend.** The rank correlation is the Spearman correlation between the strength and how far the metric has moved from its value on the undegraded field of the same frame, in the one direction it moves under that degradation, computed inside a single frame. A value of 1 means every strength moved it further than the last in every frame, whichever way it moves; a response that scatters to both sides scores near 0. The fraction of frames in order counts the frames with no exception. The weakest gap is the smallest Mann-Whitney overlap between two neighbouring strengths across frames: 1 means they never overlap, 0.5 that they cannot be told apart. **Reactivity.** The change from clean is the median, at the harshest strength, of the departure from the undegraded value of the same frame over the size of that value: 0.3 means 30%. It does not exist for this metric, whose undegraded value is exactly zero; the damage below is its relative reading. The elasticity is the percentage change of that departure per percentage change in strength over the mildest strengths. First strength detected is the mildest at which the metric has moved a tenth of the way to the anchor; **damage** reads that 0-to-1 scale as a number. A dash means the measurement is not defined there. A metric's reactivity scales with the power it is expressed in: mean squared error's elasticity is twice root-mean-square error's, though the two carry the same information, so compare magnitudes across metrics with that in mind. **Consistency** is how much the response varies from snapshot to snapshot relative to its size, in the strength's units; the snapshots of one trajectory are correlated, and the last column is how many consecutive snapshots one independent block spans.

These tables report what was measured and grade none of the measurements. What the numbers mean for this metric is written in the subsections below, beside the test that produced each number.

**Profile.**

| field | selectivity | charges most for | charges least for | response provably below 0.05 at 90% on | elasticity to a sub-pixel shift, against severity (distance) | compute cost (x cheapest in this run) |
|---|---|---|---|---|---|---|
| pressure | 0.939 | `coarsen_bandlimited` | `band_attenuate` | `band_attenuate` `subsample` `translate_subpixel` `translate_x` | — | 89.5 |

One row per physical field. **Selectivity** is how concentrated the metric's response is on a few degradations, measured per unit of field change: 0 means it charges every degradation the same, as mean squared error does by construction, and values toward 1 that one degradation carries most of it. **Charges most and least for** name the two ends of that profile. **Response provably below** lists degradations on which the upper confidence bound of the largest damage lies below the margin -- an equivalence test, so an entry says the response is provably small, not merely not significant; a dash means no degradation met the bound. **Elasticity** is the slope of log damage against log shift over the smallest shifts: 1 means damage grows in proportion to the shift, 2 with its square. **Compute cost** is wall-clock per evaluation over the cheapest metric and field in the same run.

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

<!-- GENERATED run: written by `python -m fmeval.cards evidence shock_set_masd --results results/comparison_1793812304`, do not edit -->

Measured on `sod_shock_tube`, frames 0 to 9 (10 frames of an analytic check: evidence that the metric locates and scores a known shock correctly, and nothing about turbulence), on the 2048 analysis grid, seed 20260807, at commit `adbdc88e4950`. Run `comparison_1793812304`.

Every number in this section comes from that one run. Regenerate with `python -m fmeval.cards evidence <name> --results results/comparison_1793812304`.

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
| `sod_shock_tube` | an analytic check: evidence that the metric locates and scores a known shock correctly, and nothing about turbulence | measured, run `comparison_1793812304`: the main results |
| `forecast_re5e4` | real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded | not applicable: needs pressure, which this dataset does not provide |

One row per dataset a card may cite (`configs/cards/default.yaml`). *Measured* names the run the card cites: the main results are `## Performance` and the subsections below, and every other run has its own subsection headed with its dataset. *Not applicable* gives the reason: one that follows from what the metric declares and what the dataset offers, or one a person wrote on the card (`not_run` in `card.yaml`) because the result would carry no information. *Not yet run* means the metric can run there and the card cites no run on it yet.

<!-- END GENERATED experiments -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence shock_set_masd --results results/comparison_1793812304`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `box_blur` | pressure | 4 | — | — | — |
| `disk_blur` | pressure | 3 | — | — | — |
| `epanechnikov_blur` | pressure | 3 | — | — | — |
| `gaussian_blur` | pressure | 4 | — | — | — |

<!-- END GENERATED results_smoothing -->

Every blur in the table smears Sod's shock beyond the detector's reach at every calibrated
strength, so the candidate has no shock and every strength scores the diagonal, 1, in every
frame. No rank correlation is defined. The test shows only that the metric flags a lost shock,
at the mildest strength. The median blur left the pressure unchanged at every strength and the
run excluded it as doing nothing.

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence shock_set_masd --results results/comparison_1793812304`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `band_attenuate` | pressure | 4 | — | — | — |
| `highpass_butterworth` | pressure | 2 | 1 | 0.1 | 0.55 |
| `highpass_ideal` | pressure | 1 | — | — | — |
| `lowpass_butterworth` | pressure | 2 | — | — | — |
| `lowpass_ideal` | pressure | 2 | -1 | 0 | 0.45 |

<!-- END GENERATED results_spectral -->

The filters switch the detector between finding the shock and losing it, as described on
`shock_set_distance`'s card, and this metric reads the same switch. `band_attenuate` leaves the
shocked cells in place and scores 0 at every strength. The low-pass filters lose the shock and
score 1, except in the first frame, where the harsher distinct strength of `lowpass_ideal` leaves
a flagged cell far from the shock and scores 0.28 while the milder scores the diagonal; that one
frame is the rank correlation of −1, every other frame tying. The rank correlation of 1 under
`highpass_butterworth` likewise comes from the first frame alone. These filters test the
empty-set convention, not the distance.

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence shock_set_masd --results results/comparison_1793812304`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `translate_subpixel` | pressure | 6 | 0.986 | 0 | 0.5 |
| `translate_x` | pressure | 5 | 1 | 1 | 1 |

<!-- END GENERATED results_geometric -->

This is the test the metric is built for. The whole-cell translation is ranked perfectly in every
frame, and with the same number of flagged cells in both fields its values equal
`shock_set_distance`'s, $s - \tfrac{1}{2}$ cells for a shift of $s$ cells (Definition): from
0.000244 at one cell to 0.00757 at sixteen, in units of the tube's length. The elasticity of 1.4
in the Reactivity table is that half-cell offset, as on `shock_set_distance`'s card. The
sub-pixel shift ranks at 0.986 in every frame: its two smallest shifts leave the flagged cells in
place and score 0, which is the only tie. A shift of half a cell flags one cell shared with the
reference's pair; the reference's direction averages 0 and 1 cell and the candidate's is 0, so
the value is a quarter of a cell, where the pooled average of `shock_set_distance` gives a third.
That is the two directions' equal weighting at work on the smallest example the run holds. The
largest shift scores 0.00171. The profile reads both translations as provably small only because
damage is a fraction of the domain's diagonal.

The first figure under Performance draws the test as a line-out of the last frame: the pressure
translated by 1, 2, 4 and 8 cells over the reference's in grey, the two flagged cells moving with
the step by the shift.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence shock_set_masd --results results/comparison_1793812304`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `coarsen` | pressure | 4 | 0.775 | 0 | 0.5 |
| `coarsen_bandlimited` | pressure | 4 | 0.775 | 0 | 0.5 |
| `subsample` | pressure | 4 | 0.775 | 0 | 0.5 |

<!-- END GENERATED results_resolution -->

The reductions move the shock to a block edge, by an amount set by where the block boundaries
fall, so in every frame two neighbouring factors score the same; no harsher factor scores below a
milder one in this run's `results.csv`, and the ties hold the rank correlation at 0.775 on all
three. `coarsen` and `subsample` agree at the three mildest factors; at factor 16 `subsample`
keeps a flagged pair, up to 0.00464, while `coarsen` loses the shock in three of the ten frames
and scores the diagonal. The band-limited reconstruction smears the jump, losing the shock in most
frames from its second factor and in all from its third, which is why the Profile names
`coarsen_bandlimited` as the degradation charged most for per unit of field change.

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence shock_set_masd --results results/comparison_1793812304`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `additive_noise` | pressure | 4 | 0.949 | 0 | 0.5 |
| `multiplicative_noise` | pressure | 5 | 0.707 | 0 | 0.5 |

<!-- END GENERATED results_stochastic -->

Noise is where the equal weighting of the two directions shows. The two weakest additive
amplitudes leave the detector's output unchanged and score 0; the two strongest flag many false
shocks, and the value rises to 0.118 at most. In every frame where either noise flags false
cells, the value is below `shock_set_distance`'s on the same pair (compared off the card in this
run's `results.csv`): the candidate's many false cells carry only half the weight, however many
there are, the limitation "Half the weight for any number of false shocks" measured. Under
additive noise the median value never moves a tenth of the way to the anchor, so the first
strength detected in the Reactivity table, level 5, is multiplicative noise's strongest
amplitude, where the value reaches 0.188; its three weakest amplitudes score 0. Ties at the weak
amplitudes are all that hold the rank correlations at 0.949 and 0.707; no frame scores a stronger
amplitude below a weaker one.

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence shock_set_masd --results results/comparison_1793812304`, do not edit -->

| field | damage assigned to the fake prediction | closest real degradation | damage of the reference moved far away | value on the anchor |
|---|---|---|---|---|
| pressure | 1 | `bias=0.5` | 0.537 | 1 |

The fake prediction here has exactly the reference field's amplitude spectrum and completely scrambled structure. Damage 1 is what the anchor scores, by default the reference's own spatial mean, a prediction that knows the mean and nothing else. The damage column therefore says how close to useless this metric considers that fake prediction: a low number means the metric was fooled. The third column translates the same number into an ordinary degradation whose damage the fake prediction matches, which is easier to picture. The fourth is the reference moved by a large random offset, the right statistics in the wrong place; where a field's energy sits in its largest scales that copy stays partly correlated with the reference, so it is not the score of an unrelated field.

<!-- END GENERATED results_canaries -->

The fake prediction with the right spectrum scores damage 1 in the median frame: in most frames
the detector finds no shock in it and the empty-set value is charged. In the frames where it does
flag cells, the value falls as low as 0.0519, so the metric is not fooled in the median but can
be in a single frame. The reference moved far away scores a damage of 0.537: on a tube with walls
that copy is a mirrored window whose shock lies elsewhere, and the metric reports how far.

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence shock_set_masd --results results/comparison_1793812304`, do not edit -->

| compared with | pressure |
|---|---|
| `shock_set_distance` | 1 |
| `shock_set_baddeley_delta` | 1 |
| `shock_set_hausdorff95` | 0.999 |
| `shock_set_hausdorff` | 0.998 |
| `nrmse` | 0.698 |
| `rmse` | 0.698 |
| `mse` | 0.698 |
| `vrmse` | 0.697 |
| `max_error` | 0.68 |
| `mae` | 0.644 |
| `shock_mask_overlap` | -0.881 |

Rank correlation over every degradation, computed separately for each physical field on the median value at each combination of degradation and strength, with the undegraded reference excluded. A dash marks a metric that does not run on that field. Two metrics correlating near 1 put the degradations in the same order, but the two may still weight those degradations very differently. A correlation near 1 therefore means the two metrics are redundant for ranking models, not that the two are interchangeable as training losses.

<!-- END GENERATED results_summary -->

On Sod's pressure the other shock-set distances order the degradations almost exactly as this
metric does, `shock_set_distance` and `shock_set_baddeley_delta` most closely, the pointwise
errors only moderately, and `shock_mask_overlap` strongly in reverse, which is agreement, since
the overlap falls where a distance rises. My reading, not a measurement: on Sod most degradations
either keep the shock in place or lose it, so any metric built on the same detector sorts them
alike; the difference in weighting from `shock_set_distance` moves values (Noise) more than it
moves the order.

## References

\bibliography
