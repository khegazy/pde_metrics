---
name: h1_seminorm
kind: metric
---

## Definition

For the error field $d = f - g$ on a periodic grid, the homogeneous $\dot{H}^1$ seminorm is
the root mean square of its gradient,

$$
\mathrm{H}^1(f, g) = \left(
\frac{1}{C} \Bigl\langle \sum_{c=1}^{C} \sum_j
\bigl( \partial_j d^{(c)} \bigr)^2 \Bigr\rangle \right)^{1/2} \tag{1}
$$

with $j$ over the spatial directions, $c$ over the $C$ channels and $\langle \cdot \rangle$
the average over cells. Derivatives are spectral, $\partial_j \to i k_j$ with
$k_j = 2\pi \, \mathrm{fftfreq}(N_j, h_j)$ [@pope2000], the convention used throughout this
repository.

Equation (1) is the finite-element seminorm in what it measures and differs from it in three
places, each this repository's choice rather than that field's:

- **A mean, not an integral.** Finite-element analysis integrates, $|v|_1 = (\int_\Omega
  |\nabla v|^2 \, dx)^{1/2}$ with no division by the domain's size ([@arnold2015], Ch. 4, the
  seminorm defined before Theorem 4.6; [@langtangen2016], Sect. 5.5.4, `errornorm` with
  `norm_type='H10'`). Equation (1) averages over cells, so it is that integral divided by the
  square root of the domain's area $|\Omega|$.
- **The channels are pooled with $1/C$.** A vector field's seminorm sums over components; the
  $1/C$ is this repository's, so that one channel and several sit on one scale.
- **The derivative is spectral.** Finite elements differentiate the piecewise polynomial of each
  element; here the gradient is taken in Fourier space.

What it shares with that field: it is homogeneous, with no zeroth-order term, and absolute, not
divided by the reference's own seminorm. The mean and the $1/C$ were chosen to match
[h_minus_one](../../metrics/h_minus_one/card.md), and the payoff is an exact identity. For an
error carried by a single Fourier mode of wavenumber magnitude $|\mathbf{k}|$,

$$
\mathrm{H}^1 = |\mathbf{k}| \cdot \mathrm{rms}(d),
\qquad
\mathrm{H}^{-1} = \frac{\mathrm{rms}(d)}{|\mathbf{k}|},
\qquad
\mathrm{H}^1 \cdot \mathrm{H}^{-1} = \mathrm{rms}(d)^2 = \mathrm{MSE} \tag{2}
$$

for any $|\mathbf{k}|$ whatsoever. Equation (2) is the cleanest statement of what the pair
is: one error, weighted by $|\mathbf{k}|$ and by $|\mathbf{k}|^{-1}$, on one scale, with
[mse](../../metrics/mse/card.md) sitting exactly between them.

The gradient annihilates constants, so this seminorm is blind to a uniform offset between
the two fields. That is the same blindness [h_minus_one](../../metrics/h_minus_one/card.md) has, arrived
at differently — there by excluding the zero mode from a sum, here by differentiating — and
it makes both pseudometrics rather than metrics.

### Boundary handling

Periodic on every axis, inherited from the spectral derivative. The spacing is read from the
analysis grid rather than assumed, because the value carries an inverse length: on a grid
coarsened by a factor, using the native spacing would inflate the result by exactly that
factor.

It therefore declares `requires_periodic`, and the harness does not run it on a dataset with a
non-periodic axis, such as the Sod shock tube; it reports why in the run log.

### How its field reports it

Two fields report an H^1 error, differently, and each is its own bundle.

- **Finite-element analysis**, this bundle's field. The object is the absolute seminorm of the
  error between the exact solution and the discrete one. Its theory bounds it by a power of the
  mesh size: for Lagrange elements of degree $r$ the interpolation error is
  $|u - I_h u|_1 \le c\, h^{r} |u|_{r+1}$ ([@arnold2015], Ch. 4, Theorem 4.6). For Poisson's
  problem, Galerkin orthogonality ([@arnold2015], Ch. 4, Eq. (4.3)) makes the discrete solution
  the best approximation in that seminorm, so the same bound holds for $|u - u_h|_1$; that step
  is our derivation from the two, not a statement read in the source, which states the bound in
  the full norm (Eq. (4.10)). It is reported as the
  observed convergence rate between successive meshes,
  $r = \ln(E_i/E_{i-1}) / \ln(h_i/h_{i-1})$, in a table against the mesh size
  ([@langtangen2016], Sect. 5.5.4). The experiment is a sequence of refined meshes on a problem
  with a known exact or manufactured solution. The repository does not have it:
  [EXP-max_error-grid-convergence-with-a-known-solution](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-max_error-grid-convergence-with-a-known-solution.md)
  writes it up. `forecast_re5e4` has three resolutions, but no exact solution and no record of
  how the predictions were produced, so it is not a convergence study (`issues/126`).
- **Neural-operator learning** reports a *relative, inhomogeneous* H^1 error, with the
  zeroth-order term included and the reference's norm as the denominator:
  [h1_relative](../../metrics/h1_relative/card.md).

The figure the field draws, error against mesh size, needs that experiment. The card's first
figure is instead the damage against an applied shift beside the pointwise errors, the
comparison by which a Sobolev norm's weighting of displaced error is read, and on a forecast run
the error against lead time. The metric runs on the degradation ladder on `kinet_re5e4`, on the
Reynolds ladder and on `forecast_re5e4`.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

![the metric against time: the clean field's own history in black and each strength of the operator applied at each time, or a real forecast's error against its lead time, one panel per start and one line per run](_generated/response_along_time__dataset-forecast_re5e4__field-density__along-lead.svg)

*As this metric's own field draws it, from run `comparison_1793811840`.* h1_seminorm on density against lead time, the physical time since the forecast started, one panel per start and one line per run, darker the finer the run's grid. Each point is one prediction step of one forecast.

![the metric against time: the clean field's own history in black and each strength of the operator applied at each time, or a real forecast's error against its lead time, one panel per start and one line per run](_generated/response_along_time__dataset-forecast_re5e4__field-velocity__along-lead.svg)

*As this metric's own field draws it, from run `comparison_1793811840`.* h1_seminorm on velocity against lead time, the physical time since the forecast started, one panel per start and one line per run, darker the finer the run's grid. Each point is one prediction step of one forecast.

![the metric against time: the clean field's own history in black and each strength of the operator applied at each time, or a real forecast's error against its lead time, one panel per start and one line per run](_generated/response_along_time__dataset-forecast_re5e4__field-vorticity__along-lead.svg)

*As this metric's own field draws it, from run `comparison_1793811840`.* h1_seminorm on vorticity against lead time, the physical time since the forecast started, one panel per start and one line per run, darker the finer the run's grid. Each point is one prediction step of one forecast.

![how the metric responded to each degradation, by field: rank correlation, separation of neighbouring strengths, damage per unit of field change, and the bound on its largest response](_generated/sensitivity_profile.svg)

Four measured statistics for h1_seminorm, one row per degradation grouped by family and one marker per field. From left: the rank correlation between the metric and the applied strength within a frame, with the line showing the resampling interval; the separation of neighbouring strengths as Cliff's delta, where 0 means the metric cannot tell one strength from the next and the faint ticks at 0.12, 0.28 and 0.42 are Vargha and Delaney's small, medium and large anchors, for scale and not as grades; the damage charged per unit of field change at the harshest strength; and the upper confidence bound on the largest damage, beside the fixed margin of 0.05. A hollow marker is a field and degradation on which that bound lies below the margin, so the response is provably small. A missing marker is a statistic the analysis withheld, as the rank correlation is on an axis the metric is invariant to.

![median damage against severity level, one panel per degradation family and field, on one shared scale](_generated/response_curves.svg)

Median damage over frames against severity level for h1_seminorm, one row per family of degradation and one column per field, on one shared scale. The solid grey line is damage 1, the anchor (by default the field's own mean); the dotted black line is the damage assigned to the fake prediction with the right spectrum, where the run included it. The hollow black ring marks the first level at which the metric has moved a tenth of the way to the anchor. Hollow grey markers are strengths excluded for repeating a milder one or for doing nothing. Degradations with three or fewer usable levels are drawn as markers only; points beyond 2 either side are drawn as triangles at the edge. Damage is negative where a degradation moves the metric away from the anchor, as noise raises a single-field quantity the field's mean sets to zero.

**Trend: does the response follow the degradation?**

| test family | field | degradations | rank correlation | fraction of frames in order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| Displacement | density | 3 | 1 | 0.994 to 1 | 0.881 to 0.896 |
| Displacement | velocity | 3 | 1 | 1 | 0.657 to 0.838 |
| Displacement | vorticity | 3 | 0.7 to 1 | 0.0559 to 1 | 0.44 to 0.625 |
| Cell-value distortion | density | 2 | 1 | 1 | 0.971 |
| Cell-value distortion | velocity | 2 | 1 | 1 | 1 |
| Cell-value distortion | vorticity | 2 | 1 | 1 | 0.994 |
| Resolution loss | density | 3 | 0.8 to 1 | 0.317 to 1 | 0.483 to 0.936 |
| Resolution loss | velocity | 3 | 1 | 1 | 0.693 to 0.991 |
| Resolution loss | vorticity | 3 | 0.2 to 1 | 0 to 1 | 0.408 to 0.546 |
| Smoothing | density | 5 | 1 | 1 | 0.945 to 0.957 |
| Smoothing | velocity | 5 | 1 | 1 | 0.648 to 0.692 |
| Smoothing | vorticity | 5 | 1 | 1 | 0.56 to 0.707 |
| Spectral filtering | density | 5 | 1 | 1 | 0.674 to 0.931 |
| Spectral filtering | velocity | 5 | 1 | 1 | 0.584 to 1 |
| Spectral filtering | vorticity | 5 | 1 | 1 | 0.516 to 0.858 |
| Noise | density | 2 | 1 | 1 | 1 |
| Noise | velocity | 2 | 1 | 1 | 1 |
| Noise | vorticity | 2 | 1 | 1 | 1 |

**Reactivity: how far does it move?**

| test family | field | change from clean at the harshest strength | elasticity | first strength detected |
|---|---|---|---|---|
| Displacement | density | — | 0.598 to 0.984 | level 1 |
| Displacement | velocity | — | 0.684 to 0.993 | level 1 |
| Displacement | vorticity | — | 0.412 to 0.988 | level 1 |
| Cell-value distortion | density | — | 1 | level 3 |
| Cell-value distortion | velocity | — | 1 | level 3 |
| Cell-value distortion | vorticity | — | 1 | level 3 |
| Resolution loss | density | — | 0.205 to 0.517 | level 1 |
| Resolution loss | velocity | — | 0.444 to 1.44 | level 1 |
| Resolution loss | vorticity | — | 0.105 to 0.78 | level 1 |
| Smoothing | density | — | 0.636 to 1.05 | level 1 |
| Smoothing | velocity | — | 0.262 to 0.305 | level 1 |
| Smoothing | vorticity | — | 0.552 to 0.757 | level 1 |
| Spectral filtering | density | — | 0.266 to 8.07 | level 1 |
| Spectral filtering | velocity | — | 0.112 to 1.2 | level 1 |
| Spectral filtering | vorticity | — | 0.133 to 2.55 | level 1 |
| Noise | density | — | 1 | level 1 |
| Noise | velocity | — | 1 | level 2 |
| Noise | vorticity | — | 0.999 to 1 | level 3 |
| trap test: fake prediction, right spectrum | density | — | — | damage 1.38 |
| trap test: fake prediction, right spectrum | velocity | — | — | damage 1.45 |
| trap test: fake prediction, right spectrum | vorticity | — | — | damage 1.4 |

**Consistency: how much does it vary from snapshot to snapshot?**

| test family | field | consistency, in the strength's units | snapshots per independent block |
|---|---|---|---|
| Displacement | density | 0.143 to 0.709 | 12 to 21 |
| Displacement | velocity | 0.141 to 1.2 | 21 to 22 |
| Displacement | vorticity | 0.161 to 8.89 | 21 to 22 |
| Cell-value distortion | density | 0.023 | 17 |
| Cell-value distortion | velocity | 0.0196 | 1 to 22 |
| Cell-value distortion | vorticity | 0.0306 | 19 to 21 |
| Resolution loss | density | 0.619 to 2.19 | 17 to 21 |
| Resolution loss | velocity | 0.201 to 1.36 | 22 |
| Resolution loss | vorticity | 0.867 to 7.03 | 21 to 22 |
| Smoothing | density | 0.00786 to 0.0174 | 13 to 18 |
| Smoothing | velocity | 0.0106 to 0.0388 | 21 to 22 |
| Smoothing | vorticity | 0.00966 to 0.0381 | 21 |
| Spectral filtering | density | 0.0271 to 0.0983 | 14 to 20 |
| Spectral filtering | velocity | 0.00719 to 0.0855 | 20 to 22 |
| Spectral filtering | vorticity | 0.032 to 0.0673 | 21 to 22 |
| Noise | density | 0.000255 to 0.0159 | 1 to 20 |
| Noise | velocity | 0.000201 to 0.000333 | 1 |
| Noise | vorticity | 0.00079 to 0.000963 | 1 |

One row per family of degradation and physical field; a cell gives the range over the degradations in that family. **Trend.** The rank correlation is the Spearman correlation between the strength and how far the metric has moved from its value on the undegraded field of the same frame, in the one direction it moves under that degradation, computed inside a single frame. A value of 1 means every strength moved it further than the last in every frame, whichever way it moves; a response that scatters to both sides scores near 0. The fraction of frames in order counts the frames with no exception. The weakest gap is the smallest Mann-Whitney overlap between two neighbouring strengths across frames: 1 means they never overlap, 0.5 that they cannot be told apart. **Reactivity.** The change from clean is the median, at the harshest strength, of the departure from the undegraded value of the same frame over the size of that value: 0.3 means 30%. It does not exist for this metric, whose undegraded value is exactly zero; the damage below is its relative reading. The elasticity is the percentage change of that departure per percentage change in strength over the mildest strengths. First strength detected is the mildest at which the metric has moved a tenth of the way to the anchor; **damage** reads that 0-to-1 scale as a number. A dash means the measurement is not defined there. A metric's reactivity scales with the power it is expressed in: mean squared error's elasticity is twice root-mean-square error's, though the two carry the same information, so compare magnitudes across metrics with that in mind. **Consistency** is how much the response varies from snapshot to snapshot relative to its size, in the strength's units; the snapshots of one trajectory are correlated, and the last column is how many consecutive snapshots one independent block spans.

These tables report what was measured and grade none of the measurements. What the numbers mean for this metric is written in the subsections below, beside the test that produced each number.

**Profile.**

| field | selectivity | charges most for | charges least for | response provably below 0.05 at 90% on | elasticity to a sub-pixel shift, against severity (distance) | compute cost (x cheapest in this run) |
|---|---|---|---|---|---|---|
| density | 0.927 | `band_attenuate` | `bias` | `bias` | 0.984 | 55.8 |
| velocity | 0.757 | `band_attenuate` | `bias` | `bias` | 0.993 | 113 |
| vorticity | 0.469 | `additive_noise` | `bias` | `bias` | 0.988 | 57.2 |

One row per physical field. **Selectivity** is how concentrated the metric's response is on a few degradations, measured per unit of field change: 0 means it charges every degradation the same, as mean squared error does by construction, and values toward 1 that one degradation carries most of it. **Charges most and least for** name the two ends of that profile. **Response provably below** lists degradations on which the upper confidence bound of the largest damage lies below the margin -- an equivalence test, so an entry says the response is provably small, not merely not significant; a dash means no degradation met the bound. **Elasticity** is the slope of log damage against log shift over the smallest shifts: 1 means damage grows in proportion to the shift, 2 with its square. **Compute cost** is wall-clock per evaluation over the cheapest metric and field in the same run.

<!-- END GENERATED performance -->

## Intuition

This metric measures how wrong a prediction is, weighted so that errors which vary rapidly
from cell to cell count for much more than errors spread smoothly over a large region. It is
the exact opposite trade to a norm that divides by frequency: instead of forgiving fine-grained
disagreement it punishes it, more harshly than a plain cell-by-cell average does.

The mechanism is that it compares the *slopes* of the two fields rather than their values.
Take the difference between prediction and reference, measure how steeply that difference
changes from each cell to its neighbour, and average the square of that steepness. A smooth
offset between the two fields has gentle slopes and costs little. A difference made of rapid
wiggles has steep slopes everywhere and costs a great deal.

That has a consequence worth stating plainly, because it is the reason this metric is recorded
here rather than recommended. A sharp feature that is correct in shape and amplitude but sits
slightly off its true position produces a difference made entirely of steep, rapidly varying
error concentrated at the feature's edges, which is exactly what this metric weights most.
Measured against what each metric charges for an unrelated field, a small shift costs a larger
share here than under a plain cell-by-cell norm, which is already bad at it; Limitations gives
the conditions under which that holds for every field. There is a deeper version of the same
objection:
a genuinely discontinuous field does not belong to the function space this norm is defined on
at all, so at a true shock the value is set by how finely the grid resolves the jump rather
than by anything physical.

Its weighting points the right way for the opposite failure. A prediction that is too smooth,
or one carrying grid-scale noise, differs from the reference in exactly the rapidly varying way
this metric weights most heavily. How that compares with a pointwise norm on the real flow is
measured under Results rather than asserted here.

A worked example on an eight by eight grid. The reference is flat at zero and the prediction is
a single wave with one full oscillation across the box.

```
reference        candidate        h1_seminorm    rmse
0 0 0 0 ...       1.00 ...
0 0 0 0 ...       0.71 ...            0.5554     0.7071
0 0 0 0 ...       0.00 ...
0 0 0 0 ...      -0.71 ...
```

Squeeze the same wave to three oscillations across the box and the cell-by-cell error is
unchanged at 0.7071, while this metric triples to 1.666. The ratio between the two metrics is
exactly the number of oscillations, which is the whole of its behaviour.

What it ignores: the average level of the error. A prediction uniformly too high everywhere
has no slope to its error and scores zero, however large the offset.

## Reading the output

Zero and unbounded above, in the field's units divided by a length, so a value means nothing
until the field and the domain are named. Lower is better. Identical fields score zero, and so
do fields differing by a constant.

Comparison across analysis-grid resolutions is invalid and more strongly so than for most
metrics here: the gradient is dominated by the finest scales the grid resolves, so a finer grid
admits steeper error that a coarser one cannot represent, and the value moves for reasons that
have nothing to do with the prediction.

The comparison that is always meaningful is against [h_minus_one](../../metrics/h_minus_one/card.md) and
[mse](../../metrics/mse/card.md) on the same pair of fields, because Equation (2) fixes their relationship
exactly. Reading the three together says immediately whether a prediction's error sits at large
scales or small ones: error concentrated at fine scales makes this metric large and
`h_minus_one` small, and error at coarse scales does the reverse.

## Limitations

The metric is at its worst on the failure this repository exists to address, and for small
displacements that can be shown rather than argued. Shift a field $f$ by a small $\delta$ along
$x$, so the error is $d \approx \delta\,\partial_x f$, and compare with an unrelated field of the
same statistics, for which the cross terms average away. Writing $\langle \cdot \rangle_f$ for
an average over wavevectors weighted by $|\hat f(\mathbf{k})|^2$, the share of its
unrelated-field value that the shift costs is

$$
\frac{\mathrm{H}^1(f, f_\delta)}{\mathrm{H}^1(f, g)}
\approx \frac{\delta}{\sqrt 2}
\left( \frac{\langle k_x^2 |\mathbf{k}|^2 \rangle_f}{\langle |\mathbf{k}|^2 \rangle_f} \right)^{1/2},
\qquad
\frac{\mathrm{RMSE}(f, f_\delta)}{\mathrm{RMSE}(f, g)}
\approx \frac{\delta}{\sqrt 2} \, \langle k_x^2 \rangle_f^{1/2} \tag{3}
$$

If the spectrum is isotropic, so that the direction of $\mathbf{k}$ is independent of its
magnitude under that weight, $\langle k_x^2 |\mathbf{k}|^2 \rangle_f = c\,\langle |\mathbf{k}|^4
\rangle_f$ and $\langle k_x^2 \rangle_f = c\,\langle |\mathbf{k}|^2 \rangle_f$ with the same
$c$, and the ratio of the two shares in Equation (3) is
$\langle |\mathbf{k}|^4 \rangle_f^{1/2} / \langle |\mathbf{k}|^2 \rangle_f \ge 1$ by the
Cauchy–Schwarz inequality, with equality only when all the energy sits at one wavenumber
magnitude. This derivation is ours rather than taken from a citation, and it needs the
isotropy assumption: a strongly anisotropic spectrum can break it. Measured against the
field's own mean, which is the damage scale under Results, both denominators in Equation (3)
are smaller by the same factor $\sqrt 2$, so the two shares become damages and their ratio is
unchanged. `test_metric.py` checks the ordering on a field varying in one direction, and
Results records it on the real flow.
A model-selection procedure using this metric would therefore prefer a blurred prediction to a
correctly sharp but slightly misplaced one more strongly than a pointwise norm does — the
double-penalty pathology made worse rather than better.

The second limitation is structural rather than a matter of degree. At a true discontinuity the
$\dot{H}^1$ seminorm of the error does not converge as the grid is refined: the gradient at the
jump grows without bound as the cell size shrinks. Any value reported for a shocked flow is
therefore a statement about the mesh as much as about the fields, and two runs at different
resolutions are not measuring the same quantity even approximately. This is the structural
reason the tracker rates the idea Low, and it is not repairable by normalisation.

Finally, its sensitivity to fine scales makes it sensitive to numerical artefacts of the
prediction rather than to its physics. Grid-scale ringing that a viewer would dismiss produces a
large value here.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

Measured on `kinet_re5e4`, frames 2000 to 10000 (161 frames of developed flow), on the 256 analysis grid, seed 20260807, at commit `adbdc88e4950`. Run `comparison_1793829127`.

Every number in this section comes from that run, except in the subsections headed with another experiment and in a figure whose caption names another run, each of which names its own run. Regenerate with `python -m fmeval.cards evidence <name> --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`.

<!-- END GENERATED run -->

<!-- GENERATED experiments: written by `python -m fmeval.cards catalog`, do not edit -->

**Across the experiments.**

| experiment | what a run on it is evidence of | on this card |
|---|---|---|
| `kinet_re5e4` | developed flow | measured, run `comparison_1793829127`: the main results |
| `kinet_re1e6` | developed flow at Re = 1e6, twenty times the Reynolds number of kinet_re5e4, from the same initial condition | measured, run `comparison_1793829231`: under *On `kinet_re1e6`* |
| `synthetic_ensemble` | a calibrated null: evidence that the estimator computes what it claims to compute, and nothing about turbulence | not applicable: every axis there leaves the value at its clean value (measured, 2.9e-16 relative at most): the dispersion axes do not move the member mean, and a uniform bias has no gradient |
| `sod_shock_tube` | an analytic check: evidence that the metric locates and scores a known shock correctly, and nothing about turbulence | not applicable: needs a periodic domain, and this dataset is not periodic |
| `forecast_re5e4` | real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded | measured, run `comparison_1793811840`: under *On `forecast_re5e4`* |

One row per dataset a card may cite (`configs/cards/default.yaml`). *Measured* names the run the card cites: the main results are `## Performance` and the subsections below, and every other run has its own subsection headed with its dataset. *Not applicable* gives the reason: one that follows from what the metric declares and what the dataset offers, or one a person wrote on the card (`not_run` in `card.yaml`) because the result would carry no information. *Not yet run* means the metric can run there and the card cites no run on it yet.

<!-- END GENERATED experiments -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `box_blur` | density | 4 | 1 | 1 | 0.95 |
| `box_blur` | velocity | 4 | 1 | 1 | 0.651 |
| `box_blur` | vorticity | 4 | 1 | 1 | 0.56 |
| `disk_blur` | density | 3 | 1 | 1 | 0.951 |
| `disk_blur` | velocity | 3 | 1 | 1 | 0.672 |
| `disk_blur` | vorticity | 3 | 1 | 1 | 0.577 |
| `epanechnikov_blur` | density | 3 | 1 | 1 | 0.957 |
| `epanechnikov_blur` | velocity | 3 | 1 | 1 | 0.682 |
| `epanechnikov_blur` | vorticity | 3 | 1 | 1 | 0.641 |
| `gaussian_blur` | density | 4 | 1 | 1 | 0.945 |
| `gaussian_blur` | velocity | 4 | 1 | 1 | 0.692 |
| `gaussian_blur` | vorticity | 4 | 1 | 1 | 0.583 |
| `median_blur` | density | 3 | 1 | 1 | 0.953 |
| `median_blur` | velocity | 3 | 1 | 1 | 0.648 |
| `median_blur` | vorticity | 3 | 1 | 1 | 0.707 |

<!-- END GENERATED results_smoothing -->

Ordered correctly on every smoothing axis and field, with every frame in order. Relative to its
own value on the field's mean, this metric departs from clean sooner than
[rmse](../../metrics/rmse/card.md) does on the same run: at the mildest `gaussian_blur` it has
moved further toward the anchor on all three fields (the response curves here and on `rmse`'s
card), and it is first detected at level 1 under every blur on every field. On velocity it
then saturates: its elasticity over the mildest strengths is 0.262 to 0.305, against 0.636 to
1.05 on density. Blur removes exactly the rapidly varying part of the field that the gradient
weights most. Density's neighbouring strengths are well separated across frames (weakest gaps
0.945 to 0.957); velocity's and vorticity's less so (0.56 to 0.707).

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `band_attenuate` | density | 4 | 1 | 1 | 0.674 |
| `band_attenuate` | velocity | 4 | 1 | 1 | 0.7 |
| `band_attenuate` | vorticity | 4 | 1 | 1 | 0.692 |
| `highpass_butterworth` | density | 4 | 1 | 1 | 0.891 |
| `highpass_butterworth` | velocity | 3 | 1 | 1 | 1 |
| `highpass_butterworth` | vorticity | 4 | 1 | 1 | 0.858 |
| `highpass_ideal` | density | 3 | 1 | 1 | 0.898 |
| `highpass_ideal` | velocity | 2 | 1 | 1 | 1 |
| `highpass_ideal` | vorticity | 4 | 1 | 1 | 0.85 |
| `lowpass_butterworth` | density | 4 | 1 | 1 | 0.762 |
| `lowpass_butterworth` | velocity | 3 | 1 | 1 | 0.584 |
| `lowpass_butterworth` | vorticity | 4 | 1 | 1 | 0.521 |
| `lowpass_ideal` | density | 3 | 1 | 1 | 0.931 |
| `lowpass_ideal` | velocity | 2 | 1 | 1 | 0.654 |
| `lowpass_ideal` | vorticity | 4 | 1 | 1 | 0.516 |

<!-- END GENERATED results_spectral -->

Ordered correctly on every filter and field. The response splits by which end of the spectrum
is removed. Every low-pass filter is detected at level 1 on every field, and at the mildest
`lowpass_ideal` the metric has moved further toward the anchor than `rmse` has on every field
(the response curves here and on `rmse`'s card). A high-pass removes the large scales, whose
error has shallow gradients: `highpass_ideal` is first detected only at level 3 on density and
velocity and level 2 on vorticity, and at its mildest strength on vorticity this metric has
moved far less toward the anchor than `rmse` has. This is the mirror image of
[h_minus_one](../../metrics/h_minus_one/card.md), which is gentlest on exactly the errors this
metric charges most. The milder high-pass strengths that repeat one another or do nothing are
excluded, which leaves three and two usable strengths on velocity.

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `translate_subpixel` | density | 6 | 1 | 1 | 0.896 |
| `translate_subpixel` | velocity | 6 | 1 | 1 | 0.838 |
| `translate_subpixel` | vorticity | 6 | 1 | 1 | 0.625 |
| `translate_x` | density | 5 | 1 | 1 | 0.896 |
| `translate_x` | velocity | 5 | 1 | 1 | 0.754 |
| `translate_x` | vorticity | 5 | 0.7 | 0.186 | 0.501 |
| `translate_y` | density | 5 | 1 | 0.994 | 0.881 |
| `translate_y` | velocity | 5 | 1 | 1 | 0.657 |
| `translate_y` | vorticity | 5 | 0.7 | 0.0559 | 0.44 |

<!-- END GENERATED results_geometric -->

The ordering is correct on seven of the nine rows, and the magnitude confirms Equation (3) on
the real flow. A one-cell `translate_x` costs this metric a larger share of its value on the
field's mean than it costs `rmse` and [h_minus_one](../../metrics/h_minus_one/card.md) on every
field (the table under *Damage beside the other metrics* and the response curves of the three
cards). Over the smallest shifts its damage grows in proportion to the shift: the elasticity to
a sub-pixel shift is 0.984, 0.993 and 0.988 on density, velocity and vorticity (Profile). On
vorticity it then saturates: from about a two-cell shift the median damage is above 1, more
than the field's mean costs, and from four cells it sits level with the 1.41 of the reference
moved far away (Trap tests), so the remaining strengths differ only by frame-to-frame scatter.
That is why the vorticity `translate_x` and `translate_y` rows read 0.7, with 0.186 and 0.0559
of frames in order. This is the double penalty made worse, measured.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `coarsen` | density | 4 | 1 | 1 | 0.924 |
| `coarsen` | velocity | 4 | 1 | 1 | 0.991 |
| `coarsen` | vorticity | 4 | 0.2 | 0 | 0.41 |
| `coarsen_bandlimited` | density | 4 | 0.8 | 0.317 | 0.483 |
| `coarsen_bandlimited` | velocity | 4 | 1 | 1 | 0.693 |
| `coarsen_bandlimited` | vorticity | 4 | 1 | 1 | 0.546 |
| `subsample` | density | 4 | 1 | 1 | 0.936 |
| `subsample` | velocity | 4 | 1 | 1 | 0.97 |
| `subsample` | vorticity | 4 | 0.2 | 0.0559 | 0.408 |

<!-- END GENERATED results_resolution -->

`coarsen` and `subsample` are ordered correctly on density and velocity, but not on vorticity,
where the rank correlation is 0.2 for both, with no frame in order under `coarsen` and 0.0559
of frames under `subsample`. The response curves show the median damage on vorticity under
`coarsen` rising from factor 2 to 4 and then falling, while `mse` and `h_minus_one` rise throughout on their own
cards. The degradation expands each block back to the fine grid as a constant, and on a field
that varies as quickly as vorticity the metric ends up measuring the jumps between blocks
rather than the detail coarsening removed. A test on synthetic fields, recorded in
`issues/039`, shows the peak moving to larger factors as the field gets smoother, which matches
that account.

`coarsen_bandlimited` settles it. It keeps the same block means without adding edges, and under
it vorticity is in the right order in every frame, with a rank correlation of 1. The size of
the staircase's contribution is plain at the mildest factor: in the response curves,
coarsening by 2 costs more than the field's mean on every field under `coarsen`, and a small
fraction of that under the band-limited operator. Density is the exception under the
band-limited operator, in the right order in only 0.317 of frames with a rank correlation of
0.8 and a weakest gap of 0.483: its values at factors 2 and 4 are nearly equal and ordered
differently from frame to frame. The cause is not established (`issues/039`).

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `additive_noise` | density | 4 | 1 | 1 | 1 |
| `additive_noise` | velocity | 4 | 1 | 1 | 1 |
| `additive_noise` | vorticity | 4 | 1 | 1 | 1 |
| `multiplicative_noise` | density | 5 | 1 | 1 | 1 |
| `multiplicative_noise` | velocity | 5 | 1 | 1 | 1 |
| `multiplicative_noise` | vorticity | 5 | 1 | 1 | 1 |

<!-- END GENERATED results_stochastic -->

Ordered correctly with complete separation (weakest gap 1) on every field. Noise is where the
weighting by wavenumber is most extreme: under `additive_noise` the largest damage over the
frames is 25.6 on density, 29.0 on velocity and 4.17 on vorticity (fingerprint), many times
the field's mean and many times what `rmse` charges at the same strength. Under
`multiplicative_noise` on density it reaches 3610, because the noise there scales with the
density itself, whose mean is far larger than its fluctuation (my reading of the operator).
Uncorrelated cell-to-cell noise is almost pure gradient.

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| field | damage assigned to the fake prediction | closest real degradation | damage of the reference moved far away | value on the anchor |
|---|---|---|---|---|
| density | 1.38 | `coarsen=2` | 1.38 | 0.000357 |
| velocity | 1.45 | `coarsen=2` | 1.54 | 0.00175 |
| vorticity | 1.4 | `translate_y=16` | 1.41 | 0.000962 |

The fake prediction here has exactly the reference field's amplitude spectrum and completely scrambled structure. Damage 1 is what the anchor scores, by default the reference's own spatial mean, a prediction that knows the mean and nothing else. The damage column therefore says how close to useless this metric considers that fake prediction: a low number means the metric was fooled. The third column translates the same number into an ordinary degradation whose damage the fake prediction matches, which is easier to picture. The fourth is the reference moved by a large random offset, the right statistics in the wrong place; where a field's energy sits in its largest scales that copy stays partly correlated with the reference, so it is not the score of an unrelated field.

<!-- END GENERATED results_canaries -->

The fake prediction scores farther from the truth than the field's own mean, with damage
between 1.38 and 1.45 on all three fields, close to the 1.38 to 1.54 of the reference moved far
away, so this metric is not fooled by it. That follows from comparing the two fields cell by
cell, and says nothing about the displacement problem.

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| compared with | density | velocity | vorticity |
|---|---|---|---|
| `h1_relative` | 0.935 | 0.939 | 0.964 |
| `max_error` | 0.771 | 0.784 | 0.765 |
| `max_error_channel_mean` | 0.771 | 0.786 | 0.765 |
| `rmse` | 0.705 | 0.608 | 0.7 |
| `rmse_channel_mean` | 0.705 | 0.604 | 0.7 |
| `mse` | 0.705 | 0.608 | 0.7 |
| `vrmse` | 0.702 | 0.605 | 0.697 |
| `nrmse` | 0.705 | 0.605 | 0.695 |
| `mae` | 0.682 | 0.582 | 0.646 |
| `wasserstein` | 0.584 | — | — |
| `h_minus_one` | 0.597 | 0.539 | 0.572 |
| `energy_distance` | 0.545 | 0.458 | 0.168 |
| `increment_w1` | 0.55 | 0.457 | 0.177 |
| `increment_w1_by_separation` | 0.485 | 0.373 | 0.0457 |
| `spectral_energy_flux` | — | 0.334 | — |
| `tail_exceedance` | 0.333 | 0.306 | 0.037 |
| `spectrum_l2` | 0.23 | 0.227 | -0.0731 |
| `tail_index` | 0.306 | 0.168 | 0.0947 |
| `persistence_distance` | 0.277 | — | -0.0445 |
| `palinstrophy` | — | — | 0.0767 |
| `enstrophy` | — | — | 0.00852 |
| `increment_flatness` | -0.127 | -0.0729 | 0.231 |
| `kinetic_energy` | — | -0.133 | — |

Rank correlation over every degradation, computed separately for each physical field on the median value at each combination of degradation and strength, with the undegraded reference excluded. A dash marks a metric that does not run on that field. A metric with a target value enters by its distance from the target. Two metrics correlating near 1 put the degradations in the same order, but the two may still weight those degradations very differently. A correlation near 1 therefore means the two metrics are redundant for ranking models, not that the two are interchangeable as training losses.

<!-- END GENERATED results_summary -->

This metric orders the ladder most like its relative, inhomogeneous sibling
[h1_relative](../../metrics/h1_relative/card.md), then like `max_error` and the pointwise
family (`rmse`, `mse`, `nrmse`, `vrmse`, `mae`), and less like `h_minus_one`. The two Sobolev
orders agree on direction for most degradations and disagree on which ones are severe, which
is the whole content of Equation (2). On vorticity its ordering is close to unrelated to the
distribution, increment and spectrum metrics.

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

![damage against applied strength for this metric beside the pointwise controls, log-log, one panel per displacement degradation and field](_generated/damage_beside_controls.svg)

Median damage over frames against the applied strength, log-log, for h1_seminorm (bold, in colour) and the pointwise controls mae, mse, rmse, vrmse (thin, grey), one column per displacement degradation and one row per field. The grey line is damage 1, the anchor (by default the field's own mean). Parallel lines charge in the same proportion at every strength; a steeper line charges relatively more for the larger shifts, which is what decides whether two metrics are interchangeable as training losses. These are the same numbers as the table beneath.

**Displacement, density, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `h1_seminorm` | 0.0168 | 0.0334 | 0.0656 | 0.123 | 0.2 | 0.291 |
| `mae` | 0.00383 | 0.00767 | 0.0153 | 0.0306 | 0.061 | 0.121 |
| `mse` | 2.17e-05 | 8.68e-05 | 0.000347 | 0.00138 | 0.00551 | 0.0219 |
| `rmse` | 0.00466 | 0.00931 | 0.0186 | 0.0372 | 0.0743 | 0.148 |
| `vrmse` | 0.00463 | 0.00926 | 0.0185 | 0.037 | 0.0738 | 0.147 |

**Displacement, density, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `h1_seminorm` | 0.123 | 0.2 | 0.291 | 0.544 | 0.924 |
| `mae` | 0.0306 | 0.061 | 0.121 | 0.24 | 0.469 |
| `mse` | 0.00138 | 0.00551 | 0.0219 | 0.0849 | 0.307 |
| `rmse` | 0.0372 | 0.0743 | 0.148 | 0.291 | 0.555 |
| `vrmse` | 0.037 | 0.0738 | 0.147 | 0.29 | 0.55 |

**Displacement, density, `translate_y`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `h1_seminorm` | 0.127 | 0.201 | 0.291 | 0.544 | 0.94 |
| `mae` | 0.031 | 0.0616 | 0.122 | 0.244 | 0.476 |
| `mse` | 0.00142 | 0.00565 | 0.0224 | 0.0869 | 0.316 |
| `rmse` | 0.0377 | 0.0752 | 0.15 | 0.295 | 0.562 |
| `vrmse` | 0.0376 | 0.075 | 0.149 | 0.294 | 0.56 |

**Displacement, velocity, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `h1_seminorm` | 0.0335 | 0.0669 | 0.133 | 0.257 | 0.458 | 0.663 |
| `mae` | 0.00279 | 0.00559 | 0.0112 | 0.0223 | 0.0441 | 0.0859 |
| `mse` | 1.45e-05 | 5.81e-05 | 0.000232 | 0.000924 | 0.0036 | 0.0136 |
| `rmse` | 0.00381 | 0.00762 | 0.0152 | 0.0304 | 0.06 | 0.117 |
| `vrmse` | 0.00365 | 0.00729 | 0.0146 | 0.029 | 0.0574 | 0.111 |

**Displacement, velocity, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `h1_seminorm` | 0.257 | 0.458 | 0.663 | 0.824 | 1.05 |
| `mae` | 0.0223 | 0.0441 | 0.0859 | 0.163 | 0.31 |
| `mse` | 0.000924 | 0.0036 | 0.0136 | 0.0489 | 0.165 |
| `rmse` | 0.0304 | 0.06 | 0.117 | 0.221 | 0.406 |
| `vrmse` | 0.029 | 0.0574 | 0.111 | 0.209 | 0.383 |

**Displacement, velocity, `translate_y`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `h1_seminorm` | 0.293 | 0.532 | 0.793 | 0.922 | 1.08 |
| `mae` | 0.0223 | 0.0442 | 0.0856 | 0.16 | 0.295 |
| `mse` | 0.000935 | 0.00366 | 0.0138 | 0.0473 | 0.158 |
| `rmse` | 0.0306 | 0.0605 | 0.117 | 0.218 | 0.397 |
| `vrmse` | 0.0303 | 0.0599 | 0.115 | 0.212 | 0.384 |

**Displacement, vorticity, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `h1_seminorm` | 0.104 | 0.208 | 0.411 | 0.778 | 1.28 | 1.38 |
| `mae` | 0.0428 | 0.0854 | 0.169 | 0.328 | 0.582 | 0.86 |
| `mse` | 0.00112 | 0.00448 | 0.0176 | 0.066 | 0.21 | 0.44 |
| `rmse` | 0.0335 | 0.0669 | 0.133 | 0.257 | 0.458 | 0.663 |
| `vrmse` | 0.0329 | 0.0656 | 0.13 | 0.253 | 0.455 | 0.671 |

**Displacement, vorticity, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `h1_seminorm` | 0.778 | 1.28 | 1.38 | 1.36 | 1.41 |
| `mae` | 0.328 | 0.582 | 0.86 | 1.1 | 1.31 |
| `mse` | 0.066 | 0.21 | 0.44 | 0.679 | 1.1 |
| `rmse` | 0.257 | 0.458 | 0.663 | 0.824 | 1.05 |
| `vrmse` | 0.253 | 0.455 | 0.671 | 0.832 | 1.05 |

**Displacement, vorticity, `translate_y`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `h1_seminorm` | 0.722 | 1.22 | 1.49 | 1.43 | 1.4 |
| `mae` | 0.333 | 0.603 | 0.93 | 1.25 | 1.43 |
| `mse` | 0.0858 | 0.283 | 0.628 | 0.849 | 1.17 |
| `rmse` | 0.293 | 0.532 | 0.793 | 0.922 | 1.08 |
| `vrmse` | 0.268 | 0.495 | 0.793 | 0.927 | 1.08 |

Median damage over frames at every strength, this metric in the first row and the pointwise controls beneath it, all on the same 0-to-1 scale where 0 is the undegraded reference and 1 the anchor (by default the field's own mean); a dash means no damage scale on that field. The rank correlations under *Compared with the other metrics* say whether two metrics put the strengths in the same order; this table says how much each one charges for the same strength, which decides whether two metrics are interchangeable as training losses.

<!-- END GENERATED results_damage_by_level -->

On density and velocity this metric charges more than every pointwise control at every shift,
and its line is roughly parallel to theirs over the smallest shifts. On vorticity it levels off
from four cells while the controls keep rising, and at the largest `translate_y` `mae` passes
it. This is Equation (3) seen on the real flow: a shift costs a larger share here than under a
pointwise norm until the metric saturates.

### On `forecast_re5e4`

<!-- GENERATED results_on_forecast_re5e4: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

**Real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded.**

Measured on `forecast_re5e4`, frames 0 to 59 (60 frames of real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded), on the 64 analysis grid, seed 20260807, at commit `adbdc88e4950`. Run `comparison_1793811840`.

[mean_field](../../degradations/mean_field/card.md)

![the metric against time: the clean field's own history in black and each strength of the operator applied at each time, or a real forecast's error against its lead time, one panel per start and one line per run](_generated/response_along_time__dataset-forecast_re5e4__field-density__along-lead.svg)

h1_seminorm on density against lead time, the physical time since the forecast started, one panel per start and one line per run, darker the finer the run's grid. Each point is one prediction step of one forecast.

![the metric against time: the clean field's own history in black and each strength of the operator applied at each time, or a real forecast's error against its lead time, one panel per start and one line per run](_generated/response_along_time__dataset-forecast_re5e4__field-velocity__along-lead.svg)

h1_seminorm on velocity against lead time, the physical time since the forecast started, one panel per start and one line per run, darker the finer the run's grid. Each point is one prediction step of one forecast.

![the metric against time: the clean field's own history in black and each strength of the operator applied at each time, or a real forecast's error against its lead time, one panel per start and one line per run](_generated/response_along_time__dataset-forecast_re5e4__field-vorticity__along-lead.svg)

h1_seminorm on vorticity against lead time, the physical time since the forecast started, one panel per start and one line per run, darker the finer the run's grid. Each point is one prediction step of one forecast.

**density, h1_seminorm on the prediction, at each lead time.**

| lead time | 64², start 0 | 128², start 0 | 256², start 0 | 64², start 1.13 | 128², start 1.13 | 256², start 1.13 |
|---|---|---|---|---|---|---|
| 0.1128 | 8.03e-06 | 1.31e-06 | 4.59e-09 | 0.000113 | 1.85e-05 | 5.21e-08 |
| 0.2255 | 6.16e-06 | 3.25e-06 | 9.08e-09 | 5.28e-05 | 1.6e-05 | 7.95e-08 |
| 0.3383 | 1.39e-05 | 8.57e-06 | 4.44e-08 | 5.99e-05 | 2.21e-05 | 1.14e-07 |
| 0.4511 | 4.84e-05 | 2.84e-05 | 3.8e-07 | 6.34e-05 | 2.85e-05 | 1.6e-07 |
| 0.5638 | 0.000197 | 0.000133 | 9.87e-06 | 7.46e-05 | 3.31e-05 | 2.45e-07 |
| 0.6766 | 0.000246 | 0.000144 | 3.28e-05 | 7.59e-05 | 3.8e-05 | 4.42e-07 |
| 0.7893 | 0.000211 | 0.000129 | 4.33e-05 | 9.28e-05 | 4.68e-05 | 4.61e-07 |
| 0.9021 | 0.000198 | 0.000129 | 4.54e-05 | 9.35e-05 | 4.24e-05 | 3.92e-07 |
| 1.015 | 0.000198 | 0.000129 | 4.8e-05 | 0.000105 | 4.91e-05 | 4.52e-07 |
| 1.128 | 0.000193 | 0.000122 | 4.86e-05 | 0.000115 | 5.56e-05 | 4.97e-07 |

**density, h1_seminorm damage, at each lead time.**

| lead time | 64², start 0 | 128², start 0 | 256², start 0 | 64², start 1.13 | 128², start 1.13 | 256², start 1.13 |
|---|---|---|---|---|---|---|
| 0.1128 | 0.326 | 0.0533 | 0.000188 | 0.309 | 0.0508 | 0.000143 |
| 0.2255 | 0.322 | 0.168 | 0.000465 | 0.153 | 0.0462 | 0.00023 |
| 0.3383 | 0.35 | 0.217 | 0.00113 | 0.169 | 0.0622 | 0.000321 |
| 0.4511 | 0.512 | 0.299 | 0.004 | 0.178 | 0.0799 | 0.00045 |
| 0.5638 | 0.803 | 0.541 | 0.0402 | 0.212 | 0.0941 | 0.000696 |
| 0.6766 | 0.713 | 0.417 | 0.0952 | 0.215 | 0.108 | 0.00126 |
| 0.7893 | 0.603 | 0.369 | 0.124 | 0.264 | 0.133 | 0.00131 |
| 0.9021 | 0.549 | 0.359 | 0.126 | 0.269 | 0.122 | 0.00113 |
| 1.015 | 0.539 | 0.352 | 0.131 | 0.293 | 0.138 | 0.00127 |
| 1.128 | 0.54 | 0.343 | 0.136 | 0.331 | 0.16 | 0.00142 |

**velocity, h1_seminorm on the prediction, at each lead time.**

| lead time | 64², start 0 | 128², start 0 | 256², start 0 | 64², start 1.13 | 128², start 1.13 | 256², start 1.13 |
|---|---|---|---|---|---|---|
| 0.1128 | 0.000689 | 0.000258 | 1.13e-06 | 0.000557 | 0.00024 | 1.15e-06 |
| 0.2255 | 0.000824 | 0.000391 | 2.2e-06 | 0.000587 | 0.000314 | 2.09e-06 |
| 0.3383 | 0.000932 | 0.000486 | 3.47e-06 | 0.000604 | 0.000359 | 2.83e-06 |
| 0.4511 | 0.00107 | 0.000618 | 1.11e-05 | 0.000571 | 0.000378 | 3.63e-06 |
| 0.5638 | 0.00134 | 0.000914 | 0.000129 | 0.000553 | 0.000376 | 4.14e-06 |
| 0.6766 | 0.00137 | 0.00103 | 0.000333 | 0.000559 | 0.000399 | 5.11e-06 |
| 0.7893 | 0.00126 | 0.00105 | 0.000559 | 0.00056 | 0.000406 | 5.46e-06 |
| 0.9021 | 0.00119 | 0.00106 | 0.000684 | 0.000537 | 0.000382 | 5.65e-06 |
| 1.015 | 0.00113 | 0.00104 | 0.000778 | 0.000528 | 0.000366 | 6.04e-06 |
| 1.128 | 0.00107 | 0.000966 | 0.000793 | 0.000527 | 0.000371 | 6.79e-06 |

**velocity, h1_seminorm damage, at each lead time.**

| lead time | 64², start 0 | 128², start 0 | 256², start 0 | 64², start 1.13 | 128², start 1.13 | 256², start 1.13 |
|---|---|---|---|---|---|---|
| 0.1128 | 0.313 | 0.117 | 0.000515 | 0.334 | 0.144 | 0.000693 |
| 0.2255 | 0.378 | 0.179 | 0.00101 | 0.36 | 0.192 | 0.00128 |
| 0.3383 | 0.432 | 0.225 | 0.00161 | 0.379 | 0.225 | 0.00177 |
| 0.4511 | 0.501 | 0.289 | 0.0052 | 0.365 | 0.242 | 0.00232 |
| 0.5638 | 0.636 | 0.435 | 0.0614 | 0.359 | 0.244 | 0.00269 |
| 0.6766 | 0.677 | 0.512 | 0.165 | 0.368 | 0.262 | 0.00337 |
| 0.7893 | 0.654 | 0.545 | 0.29 | 0.373 | 0.27 | 0.00363 |
| 0.9021 | 0.648 | 0.576 | 0.371 | 0.361 | 0.257 | 0.0038 |
| 1.015 | 0.636 | 0.588 | 0.438 | 0.357 | 0.247 | 0.00409 |
| 1.128 | 0.623 | 0.565 | 0.464 | 0.359 | 0.252 | 0.00462 |

**vorticity, h1_seminorm on the prediction, at each lead time.**

| lead time | 64², start 0 | 128², start 0 | 256², start 0 | 64², start 1.13 | 128², start 1.13 | 256², start 1.13 |
|---|---|---|---|---|---|---|
| 0.1128 | 0.000468 | 0.000192 | 8.88e-07 | 0.000477 | 0.000219 | 1.07e-06 |
| 0.2255 | 0.0005 | 0.000273 | 1.7e-06 | 0.000458 | 0.000271 | 1.89e-06 |
| 0.3383 | 0.000516 | 0.000312 | 2.57e-06 | 0.000443 | 0.000299 | 2.5e-06 |
| 0.4511 | 0.000543 | 0.000361 | 8.75e-06 | 0.000404 | 0.000299 | 3.03e-06 |
| 0.5638 | 0.0006 | 0.000468 | 0.000106 | 0.000375 | 0.00029 | 3.35e-06 |
| 0.6766 | 0.000657 | 0.000585 | 0.000253 | 0.000346 | 0.000278 | 3.82e-06 |
| 0.7893 | 0.000669 | 0.000626 | 0.000408 | 0.00032 | 0.000263 | 3.94e-06 |
| 0.9021 | 0.000659 | 0.00066 | 0.000448 | 0.000299 | 0.000244 | 4.06e-06 |
| 1.015 | 0.000641 | 0.000647 | 0.000478 | 0.000281 | 0.000231 | 4.24e-06 |
| 1.128 | 0.00059 | 0.000579 | 0.000452 | 0.000264 | 0.000225 | 4.56e-06 |

**vorticity, h1_seminorm damage, at each lead time.**

| lead time | 64², start 0 | 128², start 0 | 256², start 0 | 64², start 1.13 | 128², start 1.13 | 256², start 1.13 |
|---|---|---|---|---|---|---|
| 0.1128 | 0.626 | 0.257 | 0.00119 | 0.816 | 0.375 | 0.00183 |
| 0.2255 | 0.687 | 0.376 | 0.00234 | 0.844 | 0.499 | 0.00348 |
| 0.3383 | 0.734 | 0.444 | 0.00366 | 0.874 | 0.589 | 0.00494 |
| 0.4511 | 0.784 | 0.521 | 0.0126 | 0.867 | 0.643 | 0.00651 |
| 0.5638 | 0.87 | 0.68 | 0.154 | 0.871 | 0.673 | 0.00779 |
| 0.6766 | 0.92 | 0.819 | 0.354 | 0.868 | 0.697 | 0.00958 |
| 0.7893 | 0.937 | 0.876 | 0.571 | 0.863 | 0.709 | 0.0106 |
| 0.9021 | 0.948 | 0.949 | 0.644 | 0.856 | 0.698 | 0.0116 |
| 1.015 | 0.95 | 0.96 | 0.708 | 0.858 | 0.706 | 0.0129 |
| 1.128 | 0.954 | 0.936 | 0.732 | 0.854 | 0.729 | 0.0148 |

Every prediction of every forecast, nothing pooled: a cell is one prediction step of one forecast, a row the lead time (the physical time since the forecast started) and a column the forecast, named by its run's native grid and its starting time (`64², start 0` is `F-906861_64_Re_50k_from_256_to_64/forecast_t0-0`; `128², start 0` is `F-906861_64_Re_50k_from_256_to128/forecast_t0-0`; `256², start 0` is `F-906861_64/forecast_t0-0`; `64², start 1.13` is `F-906861_64_Re_50k_from_256_to_64/forecast_t0-1250`; `128², start 1.13` is `F-906861_64_Re_50k_from_256_to128/forecast_t0-2500`; `256², start 1.13` is `F-906861_64/forecast_t0-5000`). **Damage** is the prediction's departure from the target as a fraction of the anchor's in the same frame, by default the target's own spatial mean, so each step is scaled by its own target. A dash means no value there.

<!-- END GENERATED results_on_forecast_re5e4 -->

Finite-element analysis reads this seminorm against mesh size on a problem with a known
solution; these forecasts are not that experiment (`issues/126`), and the figure is the error
against lead time instead. What they show:

- **The coarser the forecast's grid, the larger the error**, at almost every step on every
  field. At the first lead time, 0.1128, the density damage is 0.326, 0.0533 and 0.000188 on
  the 64², 128² and 256² forecasts from start 0. On vorticity the 64² forecasts are already at
  0.626 (start 0) and 0.816 (start 1.13) at that step.
- **From start 1.13 the 256² forecast stays close to its target**: its damage is at most 0.00142
  on density, 0.00462 on velocity and 0.0148 on vorticity over the ten steps.
- **From start 0 it does not**: its damage is small for four steps and then rises quickly from
  lead time 0.5638, reaching 0.136 on density, 0.464 on velocity and 0.732 on vorticity at
  1.128. The coarser forecasts from start 0 rise over the same steps, and the 64² density error
  peaks there (0.803) before easing to 0.54.
- **A damage near 1 is an error as large as predicting the target's mean**, because each step
  is scaled by its own target's mean; the 64² vorticity forecasts come close to that from start 0
  (0.954 at lead time 1.128).

### On `kinet_re1e6`

<!-- GENERATED results_on_kinet_re1e6: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

**Developed flow at Re = 1e6, twenty times the Reynolds number of kinet_re5e4, from the same initial condition.**

Measured on `kinet_re1e6`, frames 2000 to 10000 (161 frames of developed flow at Re = 1e6, twenty times the Reynolds number of kinet_re5e4, from the same initial condition), on the 128 analysis grid, seed 20260807, at commit `adbdc88e4950`. Run `comparison_1793829231`.

[additive_noise](../../degradations/additive_noise/card.md) ·
[band_attenuate](../../degradations/band_attenuate/card.md) ·
[bias](../../degradations/bias/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md) ·
[disk_blur](../../degradations/disk_blur/card.md) ·
[epanechnikov_blur](../../degradations/epanechnikov_blur/card.md) ·
[gain](../../degradations/gain/card.md) ·
[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[mean_field](../../degradations/mean_field/card.md) ·
[median_blur](../../degradations/median_blur/card.md) ·
[multiplicative_noise](../../degradations/multiplicative_noise/card.md) ·
[subsample](../../degradations/subsample/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md) ·
[translate_x](../../degradations/translate/card.md) ·
[translate_y](../../degradations/translate/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

**Smoothing.**

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `box_blur` | density | 4 | 1 | 1 | 0.951 |
| `box_blur` | velocity | 4 | 1 | 1 | 0.654 |
| `box_blur` | vorticity | 2 | 1 | 1 | 0.656 |
| `disk_blur` | density | 3 | 1 | 1 | 0.953 |
| `disk_blur` | velocity | 3 | 1 | 1 | 0.685 |
| `disk_blur` | vorticity | 2 | 1 | 1 | 0.657 |
| `epanechnikov_blur` | density | 3 | 1 | 1 | 0.959 |
| `epanechnikov_blur` | velocity | 3 | 1 | 1 | 0.701 |
| `epanechnikov_blur` | vorticity | 2 | 1 | 1 | 0.798 |
| `gaussian_blur` | density | 4 | 1 | 1 | 0.948 |
| `gaussian_blur` | velocity | 4 | 1 | 1 | 0.705 |
| `gaussian_blur` | vorticity | 4 | 1 | 1 | 0.685 |
| `median_blur` | density | 3 | 1 | 1 | 0.939 |
| `median_blur` | velocity | 3 | 1 | 1 | 0.687 |
| `median_blur` | vorticity | 1 | — | — | — |

**Spectral filtering.**

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `band_attenuate` | density | 4 | 1 | 1 | 0.713 |
| `band_attenuate` | velocity | 4 | 1 | 1 | 0.817 |
| `band_attenuate` | vorticity | 4 | 1 | 1 | 0.834 |
| `highpass_butterworth` | density | 4 | 1 | 1 | 0.896 |
| `highpass_butterworth` | velocity | 3 | 1 | 1 | 1 |
| `highpass_butterworth` | vorticity | 4 | 1 | 1 | 0.958 |
| `highpass_ideal` | density | 3 | 1 | 1 | 0.901 |
| `highpass_ideal` | velocity | 2 | 1 | 1 | 1 |
| `highpass_ideal` | vorticity | 4 | 1 | 1 | 0.973 |
| `lowpass_butterworth` | density | 4 | 1 | 1 | 0.786 |
| `lowpass_butterworth` | velocity | 3 | 1 | 1 | 0.645 |
| `lowpass_butterworth` | vorticity | 4 | 1 | 1 | 0.539 |
| `lowpass_ideal` | density | 3 | 1 | 1 | 0.932 |
| `lowpass_ideal` | velocity | 3 | 1 | 1 | 0.512 |
| `lowpass_ideal` | vorticity | 4 | 1 | 1 | 0.533 |

**Displacement.**

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `translate_subpixel` | density | 6 | 1 | 1 | 0.966 |
| `translate_subpixel` | velocity | 6 | 1 | 1 | 0.773 |
| `translate_subpixel` | vorticity | 6 | 0.943 | 0.292 | 0.464 |
| `translate_x` | density | 5 | 1 | 1 | 0.943 |
| `translate_x` | velocity | 5 | 1 | 1 | 0.773 |
| `translate_x` | vorticity | 5 | 0.1 | 0.137 | 0.464 |
| `translate_y` | density | 5 | 1 | 1 | 0.939 |
| `translate_y` | velocity | 5 | 1 | 1 | 0.672 |
| `translate_y` | vorticity | 5 | 0.1 | 0 | 0.382 |

**Resolution loss.**

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `coarsen` | density | 4 | 1 | 0.894 | 0.814 |
| `coarsen` | velocity | 4 | 1 | 1 | 1 |
| `coarsen` | vorticity | 4 | 0.4 | 0.00621 | 0.44 |
| `coarsen_bandlimited` | density | 4 | 1 | 1 | 0.964 |
| `coarsen_bandlimited` | velocity | 4 | 1 | 1 | 0.738 |
| `coarsen_bandlimited` | vorticity | 4 | 1 | 1 | 0.524 |
| `subsample` | density | 4 | 1 | 1 | 0.941 |
| `subsample` | velocity | 4 | 1 | 1 | 0.822 |
| `subsample` | vorticity | 4 | 0.8 | 0.0807 | 0.414 |

**Noise.**

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `additive_noise` | density | 4 | 1 | 1 | 1 |
| `additive_noise` | velocity | 4 | 1 | 1 | 1 |
| `additive_noise` | vorticity | 4 | 1 | 1 | 1 |
| `multiplicative_noise` | density | 5 | 1 | 1 | 1 |
| `multiplicative_noise` | velocity | 5 | 1 | 1 | 1 |
| `multiplicative_noise` | vorticity | 5 | 1 | 1 | 1 |

**Cell-value distortion.**

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `bias` | density | 4 | — | — | — |
| `bias` | velocity | 4 | — | — | — |
| `bias` | vorticity | 4 | — | — | — |
| `gain` | density | 4 | 1 | 1 | 0.971 |
| `gain` | velocity | 4 | 1 | 1 | 1 |
| `gain` | vorticity | 4 | 1 | 1 | 1 |

**Trap tests.**

| field | damage assigned to the fake prediction | closest real degradation | damage of the reference moved far away | value on the anchor |
|---|---|---|---|---|
| density | 1.39 | `coarsen=2` | 1.39 | 9.42e-05 |
| velocity | 1.41 | `subsample=2` | 1.52 | 0.00048 |
| vorticity | 1.4 | `translate_x=16` | 1.42 | 8.42e-05 |

The fake prediction here has exactly the reference field's amplitude spectrum and completely scrambled structure. Damage 1 is what the anchor scores, by default the reference's own spatial mean, a prediction that knows the mean and nothing else. The damage column therefore says how close to useless this metric considers that fake prediction: a low number means the metric was fooled. The third column translates the same number into an ordinary degradation whose damage the fake prediction matches, which is easier to picture. The fourth is the reference moved by a large random offset, the right statistics in the wrong place; where a field's energy sits in its largest scales that copy stays partly correlated with the reference, so it is not the score of an unrelated field.

<!-- END GENERATED results_on_kinet_re1e6 -->

At twenty times the Reynolds number, on a 128² grid instead of 256², the metric is ordered as on
`kinet_re5e4` on every blur, filter, noise and cell-value axis on density and velocity, and it
again rejects the fake prediction (damage 1.39, 1.41 and 1.4, beside 1.39 to 1.52 for the
reference moved far away). What differs is vorticity, and one density row:

- **Displacement on vorticity is barely ordered**: `translate_x` and `translate_y` fall to rank
  correlation 0.1, with 0.137 and no frames in order, and `translate_subpixel` to 0.943 with
  0.292 of frames in order.
- **`coarsen` and `subsample` on vorticity** stay out of order (rank correlation 0.4 and 0.8,
  0.00621 and 0.0807 of frames in order); `coarsen_bandlimited` is again in order on every frame.
- **`coarsen_bandlimited` on density** is in order on every frame here (weakest gap 0.964),
  where on `kinet_re5e4` it was in order in 0.317 of frames.
- **Fewer usable blur strengths on vorticity**: two for `box_blur`, `disk_blur` and
  `epanechnikov_blur` and one for `median_blur`, which has no rank correlation.
- **Noise costs less**: the largest damage under `additive_noise` is 12.4 on density, 13.3 on
  velocity and 1.53 on vorticity (fingerprint), half or less of what it is on `kinet_re5e4`.

The grid differs between the two runs as well as the Reynolds number.

## References

\bibliography
