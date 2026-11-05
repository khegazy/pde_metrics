---
name: rank_histogram
kind: metric
---

## Definition

At every channel and cell, sort the $M$ ensemble members and record where the reference
falls among them. The rank is the number of members below it,

$$
r_{c,i} = \#\{ m : x_{m,c,i} < y_{c,i} \} \in \{0, 1, \dots, M\} \tag{1}
$$

giving $M+1$ possible outcomes, one for each gap in the sorted ensemble including the two
open ends. Collect these over all channels and cells of the frame into a histogram with
$M+1$ bins and let $f_k$ be the fraction in bin $k$. The reported scalar is the
**reliability index**, the total absolute departure from flat [@dellemonache2006]:

$$
\Delta = \sum_{k=1}^{M+1} \Bigl| f_k - \frac{1}{M+1} \Bigr| \tag{2}
$$

If the ensemble is a genuine sample from the distribution the reference was drawn from, then
the reference is exchangeable with the members and equally likely to occupy any of the
$M+1$ positions, so $\mathbb{E} f_k = 1/(M+1)$ and $\Delta$ is zero up to sampling noise
[@anderson1996; @hamill2001]. The index is bounded: $\Delta = 0$ for a flat histogram and
$\Delta = 2M/(M+1)$ when every draw lands in a single bin, which approaches 2 for a large
ensemble.

**Ties are broken at random.** Where several members equal the reference exactly, Equation
(1) is ambiguous, and resolving it by counting only members strictly below would place every
tied draw in the lowest bin and manufacture a spike that reads as bias. Hamill notes that ties
need a special rule and refers to earlier work for it (Section 2) [@hamill2001]; the rule here,
this bundle's, draws the rank uniformly from the range the tie spans, which keeps an
exchangeable but discretised forecast flat, because the reference is then equally likely to
sit anywhere in the tied run. The draw uses the seeded generator the pipeline supplies, so a
run remains reproducible. This matters for a collapsed ensemble and for any coarsely quantised
field.

The histogram is formed **per frame**, not pooled across frames. Pooling would average away
a calibration failure that changes sign along the trajectory, and it is the same rule the
rank correlations in this suite follow for the same reason.

The histogram itself, the fractions $f_0 \dots f_M$ against the rank, is the metric's curve
companion, stored on every row and handed to the metric, so the number is computed from exactly
the histogram that is stored and drawn. The chi-square goodness-of-fit statistic, the other
summary the field reports, is the sibling bundle
[rank_histogram_chi2](../../metrics/rank_histogram_chi2/card.md), computed from the same histogram. It
grows with the number of draws, and its reading as a test needs independent draws, which the
cells of a spatially correlated field are not; Equation (2) is descriptive, bounded, and does
not grow with the number of cells.

### Boundary handling

None in space: the rank at a cell uses only that cell's values across the ensemble. The
"boundary" that does need a rule is at the ends of the rank ordering, and ties are handled
as described above.

### How its field reports it

The field is ensemble forecast verification in meteorology, where the rank histogram is also
called the Talagrand diagram.

- **The object and the figure.** The histogram itself: bars of the relative frequency of each
  rank against the rank, from 1 to $M + 1$ (Hamill, Figure 1, "P(rank)" against "Rank") or the
  count of verifications in each bin (Anderson, Figure 8) [@hamill2001; @anderson1996]. Hamill's
  and Anderson's figures carry no line at the flat value; Delle Monache and colleagues draw one
  ("the perfect Talagrand diagram shape", Figure 4 of the preprint read) [@dellemonache2006].
  Here the histogram is the metric's curve companion, as fractions against the rank $0 \dots M$
  (the number of members below the reference), and is drawn from the stored curves on this
  card.
- **The summaries reported beside it.** The reliability index of Delle Monache and colleagues,
  Equation (2) here, which is their Equation (1) without its factor of 100: they report it in
  percent (Section 3.1 of the preprint read). They also give a form divided by
  $\sqrt{M/M_{\min}}$, their Equation (2), because the index "tends to increase with increasing
  ensemble size", with no derivation shown; the bundle registers the undivided index, whose
  value has a fixed meaning for a given histogram [@dellemonache2006]. The chi-square statistic
  and its test of uniformity (Anderson, Section 2c; Hamill, Section 4) [@anderson1996;
  @hamill2001] are the sibling bundle [rank_histogram_chi2](../../metrics/rank_histogram_chi2/card.md),
  which also records why Jolliffe and Primo's decomposition of it is not built.
- **How the field reads it.** Hamill's warnings are part of the standard reading: "a uniform
  rank histogram is a necessary but not sufficient criterion for determining that the ensemble
  is reliable" (Section 3a), a U shape can come from conditional biases rather than too little
  spread (Figure 4), correct variances with wrong covariances show only in histograms of
  combinations of grid points such as differences (Section 3b, Figure 5), and observation error
  makes a calibrated ensemble look U-shaped (Section 3c) [@hamill2001].
- **The experiment.** Histograms over many forecasts at many grid points, by lead time
  (Anderson), and synthetic ensembles of known miscalibration, including flat histograms from
  unreliable ensembles (Hamill, Section 3, Figures 2 to 4). Here only the calibrated null of
  `synthetic_ensemble` and its miscalibration ladder exist; real ensembles wait on
  [issue 004](https://github.com/khegazy/pde_metrics/blob/main/issues/004-independent-realizations.md).
  The missing experiments are
  [EXP-spread_skill-heteroscedastic-synthetic-ensemble](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-spread_skill-heteroscedastic-synthetic-ensemble.md)
  (Hamill's flat-but-unreliable mixture),
  [EXP-crps-gneiting-forecaster-suite](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-crps-gneiting-forecaster-suite.md)
  (calibrated forecasters of different sharpness, whose histograms are all flat) and
  [EXP-spread_skill-perturbed-initial-condition-ensemble](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-spread_skill-perturbed-initial-condition-ensemble.md)
  (forecasts against lead time).

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence rank_histogram --results results/comparison_1793812401`, do not edit -->

![the curve behind the number against its coordinate, as its field draws it, at every strength of each degradation, the clean curve in black](_generated/companion_curves__field-density.svg)

*As this metric's own field draws it.* The curve behind rank_histogram on density: the median over frames at every strength of every degradation, the clean curve in black, the anchor dashed and the impostor dotted. Each bin's bars are the strengths, mildest first, then the clean level. Values are the literature's own, untransformed.

![how the metric responded to each degradation, by field: rank correlation, separation of neighbouring strengths, damage per unit of field change, and the bound on its largest response](_generated/sensitivity_profile.svg)

Four measured statistics for rank_histogram, one row per degradation grouped by family and one marker per field. From left: the rank correlation between the metric and the applied strength within a frame, with the line showing the resampling interval; the separation of neighbouring strengths as Cliff's delta, where 0 means the metric cannot tell one strength from the next and the faint ticks at 0.12, 0.28 and 0.42 are Vargha and Delaney's small, medium and large anchors, for scale and not as grades; the damage charged per unit of field change at the harshest strength; and the upper confidence bound on the largest damage, beside the fixed margin of 0.05. A hollow marker is a field and degradation on which that bound lies below the margin, so the response is provably small. A missing marker is a statistic the analysis withheld, as the rank correlation is on an axis the metric is invariant to.

![median damage against severity level, one panel per degradation family and field, on one shared scale](_generated/response_curves.svg)

Median damage over frames against severity level for rank_histogram, one row per family of degradation and one column per field, on one shared scale. The solid grey line is damage 1, the anchor (by default the field's own mean); the dotted black line is the damage assigned to the fake prediction with the right spectrum, where the run included it. The hollow black ring marks the first level at which the metric has moved a tenth of the way to the anchor. Hollow grey markers are strengths excluded for repeating a milder one or for doing nothing. Degradations with three or fewer usable levels are drawn as markers only; points beyond 2 either side are drawn as triangles at the edge. Damage is negative where a degradation moves the metric away from the anchor, as noise raises a single-field quantity the field's mean sets to zero.

**Trend: does the response follow the degradation?**

| test family | field | degradations | rank correlation | fraction of frames in order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| Ensemble dispersion | density | 2 | 1 | 1 | 1 |
| Cell-value distortion | density | 1 | 1 | 1 | 1 |

**Reactivity: how far does it move?**

| test family | field | change from clean at the harshest strength | elasticity | first strength detected |
|---|---|---|---|---|
| Ensemble dispersion | density | 21.4 to 26.6 | 0.85 to 1.41 | level 1 |
| Cell-value distortion | density | 32.5 | 1.07 | level 2 |

**Consistency: how much does it vary from snapshot to snapshot?**

| test family | field | consistency, in the strength's units | snapshots per independent block |
|---|---|---|---|
| Ensemble dispersion | density | 0.00513 to 0.0188 | 1 |
| Cell-value distortion | density | 0.00324 | 1 |

One row per family of degradation and physical field; a cell gives the range over the degradations in that family. **Trend.** The rank correlation is the Spearman correlation between the strength and how far the metric has moved from its value on the undegraded field of the same frame, in the one direction it moves under that degradation, computed inside a single frame. A value of 1 means every strength moved it further than the last in every frame, whichever way it moves; a response that scatters to both sides scores near 0. The fraction of frames in order counts the frames with no exception. The weakest gap is the smallest Mann-Whitney overlap between two neighbouring strengths across frames: 1 means they never overlap, 0.5 that they cannot be told apart. **Reactivity.** The change from clean is the median, at the harshest strength, of the departure from the undegraded value of the same frame over the size of that value: 0.3 means 30%. The elasticity is the percentage change of that departure per percentage change in strength over the mildest strengths. First strength detected is the mildest at which the metric has moved a tenth of the way to the anchor; **damage** reads that 0-to-1 scale as a number. A dash means the measurement is not defined there. A metric's reactivity scales with the power it is expressed in: mean squared error's elasticity is twice root-mean-square error's, though the two carry the same information, so compare magnitudes across metrics with that in mind. **Consistency** is how much the response varies from snapshot to snapshot relative to its size, in the strength's units; the snapshots of one trajectory are correlated, and the last column is how many consecutive snapshots one independent block spans.

These tables report what was measured and grade none of the measurements. What the numbers mean for this metric is written in the subsections below, beside the test that produced each number.

**Profile.**

| field | selectivity | charges most for | charges least for | response provably below 0.05 at 90% on | elasticity to a sub-pixel shift | compute cost (x cheapest in this run) |
|---|---|---|---|---|---|---|
| density | 0.634 | `spread_deflate` | `bias` | — | — | 28 |

One row per physical field. **Selectivity** is how concentrated the metric's response is on a few degradations, measured per unit of field change: 0 means it charges every degradation the same, as mean squared error does by construction, and values toward 1 that one degradation carries most of it. **Charges most and least for** name the two ends of that profile. **Response provably below** lists degradations on which the upper confidence bound of the largest damage lies below the margin -- an equivalence test, so an entry says the response is provably small, not merely not significant; a dash means no degradation met the bound. **Elasticity** is the slope of log damage against log shift over the smallest shifts: 1 means damage grows in proportion to the shift, 2 with its square. **Compute cost** is wall-clock per evaluation over the cheapest metric and field in the same run.

<!-- END GENERATED performance -->

## Intuition

Line the ensemble members up in order at one point in the field and ask where the true value
sits among them. Repeat that everywhere and count how often the truth came last, second to
last, and so on down to first. If the ensemble is honest, the truth is just one more draw
from the same distribution, so it is equally likely to land in any of the slots and the
counts come out flat. This metric measures how far from flat they came out.

What makes the diagnostic worth more than a single ratio is that the *shape* of the
departure names the fault. If the members huddle too closely together, the truth keeps
falling outside them and the counts pile up at both ends — a U. If they are spread too
widely, the truth is usually caught somewhere in the middle and the counts pile up there — a
dome. If the whole ensemble is offset, the counts slope to one side. The reported number
collapses that shape to a single magnitude, so it says how badly without saying which; the
histogram itself, if you plot it, says which.

The property that earns this metric its place beside the others is that it responds to
changes nothing built on the ensemble mean can see. Squeezing an ensemble toward its own
centre leaves that centre exactly where it was, so any mean-based score is unchanged, while
the truth starts falling outside the members and this index rises immediately. A test in
this bundle pins that contrast directly.

A worked example with three members and four cells, arranged so the reference takes each
possible rank exactly once:

```
reference        members (three per cell)      result
0 0 0 0          per cell, one rank each        0.0
```

Four cells and four bins with one draw each is a perfectly flat histogram, so the index is
zero.

It ignores magnitude entirely. Only the ordering matters, so an ensemble can be wrong by any
amount and still be perfectly calibrated by this measure.

## Reading the output

The value is dimensionless and runs from zero to just under 2, with zero the best. There is
no target other than zero, so unlike the spread-to-skill ratio this reads like an ordinary
error metric: lower is better and the ordering statistics apply directly.

What counts as small depends on the sample, and this is the number people get wrong. Even a
perfectly calibrated ensemble produces a non-zero index, because a finite histogram is never
exactly flat; the floor scales roughly as the square root of the bin count over the number
of draws. On the synthetic ensemble here, with 4096 cells and sixteen members, that floor
is the clean value in Results. Compare a measured value against that floor rather than against zero,
and the cheapest way to establish the floor is to read this metric at the clean severity
level of the same run.

Because ranks are invariant to any monotone rescaling of the field, the metric is scale free
and comparable across fields of wildly different magnitude. Comparison across ensemble sizes
is meaningful in the sense that the bound is nearly the same, but the sampling floor is not,
so a small index on a four-member ensemble is weaker evidence than the same index on fifty.
Comparison across resolutions changes the number of draws and therefore the floor.

The curve companion is the histogram: one value per rank $0 \dots M$, the fraction of the
frame's draws at which exactly that many members fell below the reference, summing to one. A
flat histogram sits at $1/(M+1)$ in every bin; the analysis reads every rank as its own
coordinate, so its tables say which ranks a degradation moved, the two ends for a U, the middle
for a dome, one end for a bias.

## Limitations

The index says how far from calibrated an ensemble is but not in which direction, and the two
directions have opposite remedies: a U-shaped histogram means widen the ensemble, a dome
means narrow it. Reading only this number, a user cannot tell which. `spread_skill`, whose
sign carries exactly that information, is its natural companion.

The aggregate hides spatial structure. An ensemble that is overconfident in one region and
overdispersed in another can produce a histogram that is flat overall, and this metric will
report a well-calibrated prediction. The failure is invisible to any whole-field summary.

The sampling floor is a trap in the other direction. Because the index is bounded below by
the noise of a finite histogram rather than by zero, a small positive value proves nothing
on its own, and comparing a value measured on a coarse grid against one from a fine grid
compares two different floors. The effective number of independent draws is also far smaller
than the cell count on these fields, since neighbouring cells of a turbulent flow are
strongly correlated — so the true floor is higher than an independence assumption would
suggest, and the value is noisier frame to frame than the raw count of cells implies.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence rank_histogram --results results/comparison_1793812401`, do not edit -->

Measured on `synthetic_ensemble`, frames 0 to 11 (12 frames of a calibrated null: evidence that the estimator computes what it claims to compute, and nothing about turbulence), on the 64 analysis grid, seed 20260807, at commit `adbdc88e4950`. Run `comparison_1793812401`.

Every number in this section comes from that one run. Regenerate with `python -m fmeval.cards evidence <name> --results results/comparison_1793812401`.

<!-- END GENERATED run -->

**What these numbers are evidence of, and what they are not.** The run behind them is on
`synthetic_ensemble`, which is generated rather than simulated: the reference is drawn from
the same process as the members, with the same dispersion, so the two are exchangeable and
every quantity below has a value derivable in advance. That is what makes the run worth
citing — an estimator agreeing with arithmetic it could not have fitted to is a real
result, and it is the claim a first implementation has to establish.

It is not evidence about turbulence. The fields have no shocks, no intermittency and no
coherent structure, so nothing here says how this metric behaves on the flows this
repository exists to evaluate. The degradation families a physical run would exercise —
smoothing, spectral filtering, displacement, resolution loss — are absent from these
tables for that reason, and so are the trap tests. When an ensemble of real runs exists
([issue 004](https://github.com/khegazy/pde_metrics/blob/main/issues/004-independent-realizations.md)), this card should be
regenerated against it and this section will say something different.

<!-- GENERATED experiments: written by `python -m fmeval.cards catalog`, do not edit -->

**Across the experiments.**

| experiment | what a run on it is evidence of | on this card |
|---|---|---|
| `kinet_re5e4` | developed flow | not applicable: needs an ensemble, and this dataset has one realisation per frame |
| `kinet_re1e6` | developed flow at Re = 1e6, twenty times the Reynolds number of kinet_re5e4, from the same initial condition | not applicable: needs an ensemble, and this dataset has one realisation per frame |
| `synthetic_ensemble` | a calibrated null: evidence that the estimator computes what it claims to compute, and nothing about turbulence | measured, run `comparison_1793812401`: the main results |
| `sod_shock_tube` | an analytic check: evidence that the metric locates and scores a known shock correctly, and nothing about turbulence | not applicable: needs an ensemble, and this dataset has one realisation per frame |
| `forecast_re5e4` | real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded | not applicable: needs an ensemble, and this dataset has one realisation per frame |

One row per dataset a card may cite (`configs/cards/default.yaml`). *Measured* names the run the card cites: the main results are `## Performance` and the subsections below, and every other run has its own subsection headed with its dataset. *Not applicable* gives the reason: one that follows from what the metric declares and what the dataset offers, or one a person wrote on the card (`not_run` in `card.yaml`) because the result would carry no information. *Not yet run* means the metric can run there and the card cites no run on it yet.

<!-- END GENERATED experiments -->

### Ensemble dispersion

[spread_inflate](../../degradations/spread_inflate/card.md) ·
[spread_deflate](../../degradations/spread_deflate/card.md)

<!-- GENERATED results_ensemble: written by `python -m fmeval.cards evidence rank_histogram --results results/comparison_1793812401`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `spread_deflate` | density | 4 | 1 | 1 | 1 |
| `spread_inflate` | density | 4 | 1 | 1 | 1 |

<!-- END GENERATED results_ensemble -->

The clean ensemble reads 0.0451, which is the sampling floor rather than zero: 16 members
over a 64x64 grid give 17 bins and a finite histogram is never exactly flat. Every measured
departure below should be read against 0.0451, not against zero.

Both directions rise well clear of it, with a rank correlation of 1 on each: at the harshest
strengths the index has risen by 26.6 times its clean value under deflation and 21.4 times
under inflation (the reactivity table); deflation is detected at the mildest strength and
inflation at the second. The
index cannot say which direction it saw, and that is the limitation stated above made
concrete: a value near one could be either fault, and only `spread_skill`'s side of one
distinguishes them.

The histogram itself, the curve companion drawn in the Performance section, is the field's
own figure (Hamill, Figure 1) [@hamill2001], and on it the two faults take the shapes the
Limitations section names. Under deflation both end bins grow, ranks 0 and 16 rising by 5.14 and 5.34 times
their clean values at the harshest strength, and every interior bin shrinks: the U of an
over-narrow ensemble, with up to 0.382 of a frame's draws in rank 0 alone. Under inflation
the end bins empty, ranks 0 and 16 falling to none at the harshest strength, and the middle
fills, rank 8 rising by 2.35 times its clean value: the dome of an over-wide ensemble. The
`bias` axis gives the slope of a biased one, rank 0 rising by 11.3 times its clean value and
rank 16 emptying. On the clean ensemble every rank holds between 0.0565 and 0.0609 of the
draws, about the flat value of 1/17 (numbers from the companion statistics in the card's
fingerprint).

Deflation registers more strongly than inflation at the harshest strengths here, which follows
from the shapes: an over-narrow ensemble pushes the truth outside the members entirely, piling
draws into the two end bins, while an over-wide one merely concentrates them toward the middle
and leaves the interior bins occupied (this card's reasoning). The same shapes say why the
curve's ordering is less tidy under inflation: as the dome narrows, the bins at its flanks,
ranks 5 and 11, first fill and then empty again, so their rank correlations with the strength
are 0.4 and 0.1. For the same reason the curves of neighbouring inflation strengths do not
nest: for at least one pair of neighbouring strengths, no frame has the harsher one at least
as far from clean as the milder one at every rank (the companion's dominance, 0 for inflation
against 0.417 for deflation in the fingerprint).

On the damage scale the anchor, each member replaced by its own spatial mean, scores 1.75: a
collapsed ensemble ranks the truth below or above every member at almost every cell, putting
about half of the draws in each end bin. Against it the harshest deflation reaches a damage of
0.718, the harshest inflation 0.577 and the harshest offset 0.870 (the largest in any frame).
The `bias` axis has no subsection of its own on this card; its numbers are those of the
Performance tables and the card's fingerprint.

The profile row above ranks the degradations by damage per unit of field change, but the two
dispersion axes leave the ensemble mean, and so the measured field change, unchanged to
round-off; its "charges most for", "charges least for" and selectivity are therefore not
meaningful for this metric ([issue 111](https://github.com/khegazy/pde_metrics/blob/main/issues/111-damage-per-change-divides-by-round-off-on-ensemble-axes.md)).

### Cell-value distortion

[gain](../../degradations/gain/card.md) ·
[bias](../../degradations/bias/card.md)

<!-- GENERATED results_pointwise: written by `python -m fmeval.cards evidence rank_histogram --results results/comparison_1793812401`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `bias` | density | 4 | 1 | 1 | 1 |

<!-- END GENERATED results_pointwise -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence rank_histogram --results results/comparison_1793812401`, do not edit -->

| compared with | density |
|---|---|
| `rank_histogram_chi2` | 0.967 |
| `crps` | 0.94 |
| `energy_score` | 0.94 |
| `spread_skill` | 0.918 |
| `variogram_score` | 0.616 |
| `max_error` | 0.579 |
| `ensemble_mean_rmse` | 0.323 |
| `h1_relative` | 0.323 |
| `mae` | 0.323 |
| `mse` | 0.323 |
| `nrmse` | 0.323 |
| `rmse` | 0.323 |
| `vrmse` | 0.267 |
| `crps_skill_score` | -0.94 |

Rank correlation over every degradation, computed separately for each physical field on the median value at each combination of degradation and strength, with the undegraded reference excluded. A dash marks a metric that does not run on that field. A metric with a target value enters by its distance from the target. Two metrics correlating near 1 put the degradations in the same order, but the two may still weight those degradations very differently. A correlation near 1 therefore means the two metrics are redundant for ranking models, not that the two are interchangeable as training losses.

<!-- END GENERATED results_summary -->

## References

\bibliography
