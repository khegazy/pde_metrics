---
name: nrmse
kind: metric
---

## Definition

For fields $f$ (reference) and $g$ (candidate) on the same analysis grid, with $C$ channels and
$N$ cells per channel, the normalised root mean squared error of PDEBench [@takamoto2022] divides
each channel's root mean squared error by the root mean square of that channel of the reference,
and averages over channels:

$$
\mathrm{nRMSE}(f, g) = \frac{1}{C} \sum_{c=1}^{C}
\frac{\sqrt{\frac{1}{N} \sum_{i} \bigl( f_{c,i} - g_{c,i} \bigr)^2}}
{\sqrt{\frac{1}{N} \sum_{i} f_{c,i}^2}} \tag{1}
$$

The paper writes it as $\lVert u_{\mathrm{pred}} - u_{\mathrm{true}} \rVert_2 / \lVert
u_{\mathrm{true}} \rVert_2$ (App. B, unnumbered); Equation (1) is how its code evaluates that
ratio: for each sample, channel and time step, the RMSE over space divided by
$\sqrt{\mathrm{mean}(u_{\mathrm{true}}^2)}$ over space, with no small constant added, then the
mean over samples and over channels and time steps (`pdebench/models/metrics.py`, `metric_func`,
`err_nRMSE`). The harness scores one frame of one field at a time, so the mean over channels is
the reduction that remains.

The denominator is the raw root mean square of the reference: its spatial mean is **not**
removed. Writing $\bar f_c$ for the spatial mean of channel $c$ and $\sigma_c$ for the root mean
square of its fluctuation, the denominator is $\sqrt{\bar f_c^{\,2} + \sigma_c^2}$, so on a channel
whose mean is much larger than its fluctuation

$$
\mathrm{nRMSE}_c \approx \frac{\sigma_c}{|\bar f_c|} \, \frac{\mathrm{RMSE}_c}{\sigma_c} \tag{2}
$$

that is, the fluctuation-normalised error of [vrmse](../../metrics/vrmse/card.md) multiplied by the ratio of
fluctuation to mean. On `kinet_re5e4` density has mean 1 and a fluctuation root mean square of
$2.1 \times 10^{-3}$ to $6.7 \times 10^{-3}$ over frames 2000 to 10000 (`AGENTS.md` §4), so on
density this metric is that factor, two to three orders of magnitude, below `vrmse`, and near
zero for every degradation: the reference's own spatial mean, the damage anchor, scores about
$\sigma / \bar f$ there. That is the standard's behaviour, not a defect of this implementation;
The Well reports VRMSE rather than NRMSE for exactly this reason, saying that a 2-norm denominator
"down-weights errors" on fields such as density and pressure "whose mean is often bounded away
from zero" [@ohana2024] (Sect. 4, Results). On a one-channel field the factor cancels from
damage, the value over the anchor's value. On vorticity, whose spatial mean on a periodic domain is zero, the
denominator is the fluctuation itself and this metric equals `vrmse` up to The Well's two
numerical conventions.

The reference alone sets the denominator, so Equation (1) is not symmetric, and since each term
of a triangle is divided by a different reference's scale, it does not satisfy the triangle
inequality (`test_metric.py` gives a three-field example). Where a channel of the reference is
zero in every cell PDEBench's division has no value, and the metric returns NaN.

### Boundary handling

None. The operation is local to each cell, and the root mean square is taken over the whole
field, so no neighbourhood and no boundary condition enter.

### How its field reports it

The name and the definition are PDEBench's. Two other fields normalise the error differently, and
each of those forms is its own bundle.

- **PDEBench** [@takamoto2022]. The object is Equation (1) per sample and time step, averaged over
  the held-out tenth of the samples (Sect. 4.1) and then over channels and time steps, described as
  ensuring scale independence (Sect. 3.3, table of metrics). It is reported in the tables of every
  metric per PDE and model (App. E), and drawn against a parameter of the PDE: Fig. 3b plots nRMSE
  against the Darcy-flow force term on logarithmic axes, one line per model, and the text reads its
  rise as the solution's scale falls (Sect. 4.2). The experiment is autoregressive rollouts, or a
  parameter-to-solution map, over many samples of each PDE.
- **The Well** [@ohana2024]. It defines NRMSE as the same ratio with $10^{-7}$ added to the mean
  square (App. E.3), which differs from Equation (1) only by that constant and is not built
  separately, and reports instead the variance-scaled form, [vrmse](../../metrics/vrmse/card.md).
- **Numerical analysis and weather verification** report unnormalised norms:
  [rmse](../../metrics/rmse/card.md) and [max_error](../../metrics/max_error/card.md).

**The experiments here.** Rollouts over many initial conditions do not exist; `forecast_re5e4`
(`docs/datasets/reynolds_ladder_2d.md`, "Forecast pairs") gives one model's predictions at ten
prediction steps from two starting times, on which the error is drawn against lead time, and
[EXP-nrmse-rollouts-over-many-initial-conditions](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-nrmse-rollouts-over-many-initial-conditions.md)
writes up the missing test set. PDEBench's error against a PDE parameter has its nearest analogue
in the Reynolds ladder (`dataset_family=reynolds_ladder_2d`), two members at
$\mathrm{Re} = 5 \times 10^4$ and $10^6$, whose report section compares rank statistics rather
than raw values. The metric also runs on the degradation ladder on `kinet_re5e4`, on
`sod_shock_tube` and on the member mean of `synthetic_ensemble`.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence nrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence nrmse`.

<!-- END GENERATED performance -->

## Intuition

Normalised root mean squared error, in PDEBench's form, is the root mean squared error as a
fraction of the typical size of the reference, measured from zero. An error of one unit means
something different in a field whose values are near a thousand and in one whose values are near
two, and dividing by the reference's size is meant to remove that.

Measuring the size from zero rather than from the field's mean decides what the number says on a
field that sits on a large constant background. On a four-by-four grid, the same displaced square
scored as it stands and on a background of a thousand:

```
                            rmse      nrmse        vrmse
as it stands                0.5       1.0          1.118
on a background of 1000     0.5       0.0005       1.118
```

The error is the same in both rows. As it stands, the reference's size is a half, so the error is
as large as the field. On the background the reference's size is about a thousand, so the same
error is a two-thousandth of it and the metric reads it as nearly perfect. The variance-scaled form
in the last column measures the size about the mean instead and does not move. Each component of
a field is normalised by its own size before the components are averaged.

What this metric ignores is where the errors sit, as every cell-by-cell error does, and, on a
field with a large mean, the size of the error relative to how much the field actually varies.

## Reading the output

The value runs from zero upwards with no upper limit and is dimensionless. Lower is better, and
zero means the fields are identical. A value of one means the error is as large as the reference's
root mean square; predicting zero everywhere scores exactly one.

Its comparisons across fields are only as meaningful as the fields' means are alike. On a field
whose mean is near zero (vorticity, and here velocity) it behaves like `vrmse`; on density, which
sits on a mean two to three orders of magnitude above its fluctuation, every value is small, and
a small value there does not mean a good prediction. Compare models on one field, dataset and
analysis grid; set it beside a PDEBench table entry; read `vrmse` beside it on density. The
reference must be the trusted field: the metric is asymmetric.

## Limitations

On any field with a large mean the metric is compressed towards zero by the ratio of fluctuation
to mean, Equation (2). On density here a prediction no better than the field's own mean scores
less than one percent, and a reader who reads the value against the landmark of one, as on a
field without a mean, will take a useless prediction for an excellent one. The damage column,
which divides by what the mean scores, is the reading that survives this.

The denominator is measured from the reference on each frame. As a decaying flow loses its
fluctuation the denominator of a zero-mean field falls, and the same absolute error scores
higher; on density, whose mean does not decay, it does not. A trend along a trajectory therefore
means different things on different fields.

On a one-channel field, with the reference fixed, it orders candidates exactly as `rmse` does,
and on every field it shares that metric's blindness to position and its quadratic response to
sub-cell displacement.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence nrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence nrmse`.

<!-- END GENERATED run -->

Each subsection links to the degradations that subsection reports. What those degradations
do, and what their strength numbers mean, is documented on their own pages.

<!-- GENERATED experiments: written by `python -m fmeval.cards catalog`, do not edit -->

**Across the experiments.**

| experiment | what a run on it is evidence of | on this card |
|---|---|---|
| `kinet_re5e4` | developed flow | measured, run `comparison_1793657627`: the main results |
| `kinet_re1e6` | developed flow at Re = 1e6, twenty times the Reynolds number of kinet_re5e4, from the same initial condition | not yet run |
| `synthetic_ensemble` | a calibrated null: evidence that the estimator computes what it claims to compute, and nothing about turbulence | not yet run; on this dataset the metric scores the member mean of the ensemble |
| `sod_shock_tube` | an analytic check: evidence that the metric locates and scores a known shock correctly, and nothing about turbulence | not yet run |
| `forecast_re5e4` | real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded | not yet run |

One row per dataset a card may cite (`configs/cards/default.yaml`). *Measured* names the run the card cites: the main results are `## Performance` and the subsections below, and every other run has its own subsection headed with its dataset. *Not applicable* gives the reason: one that follows from what the metric declares and what the dataset offers, or one a person wrote on the card (`not_run` in `card.yaml`) because the result would carry no information. *Not yet run* means the metric can run there and the card cites no run on it yet.

<!-- END GENERATED experiments -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence nrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence nrmse`.

<!-- END GENERATED results_smoothing -->

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence nrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence nrmse`.

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence nrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence nrmse`.

<!-- END GENERATED results_geometric -->

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence nrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence nrmse`.

<!-- END GENERATED results_resolution -->

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence nrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence nrmse`.

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence nrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence nrmse`.

<!-- END GENERATED results_canaries -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence nrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence nrmse`.

<!-- END GENERATED results_summary -->

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence nrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence nrmse`.

<!-- END GENERATED results_damage_by_level -->

## References

\bibliography
