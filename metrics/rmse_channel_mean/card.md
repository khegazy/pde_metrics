---
name: rmse_channel_mean
kind: metric
---

## Definition

For fields $f$ (reference) and $g$ (candidate) on the same analysis grid, with $C$ channels and
$N$ cells per channel, the root mean squared error of channel $c$ is

$$
\mathrm{RMSE}_c(f, g) = \sqrt{\frac{1}{N} \sum_{i=1}^{N} \bigl( f_{c,i} - g_{c,i} \bigr)^2} \tag{1}
$$

and this bundle reports their mean over channels,

$$
\mathrm{RMSE}_{\mathrm{ch}}(f, g) = \frac{1}{C} \sum_{c=1}^{C} \mathrm{RMSE}_c(f, g) \tag{2}
$$

which is how PDEBench's code reduces its RMSE [@takamoto2022]: the root mean square over space
for each sample, channel and time step, then the mean over samples, and then over channels and
time steps (`pdebench/models/metrics.py`, `metric_func`, `err_mean` and `err_RMSE`). The harness
scores one frame of one field at a time, so the mean over channels is the reduction that remains.
The Well computes the same per-channel RMSE and averages it over its fields [@ohana2024]
(App. E.3; `the_well/benchmark/metrics/spatial.py`, `RMSE`).

[rmse](../../metrics/rmse/card.md) pools the channels before the square root,
$\sqrt{\frac{1}{C} \sum_c \mathrm{RMSE}_c^2}$. On a one-channel field (density, vorticity) the two
are the same number. On several channels a mean of square roots is never larger than the square
root of their mean, and never smaller than that over $\sqrt{C}$:

$$
\frac{\mathrm{RMSE}}{\sqrt{C}} \le \mathrm{RMSE}_{\mathrm{ch}} \le \mathrm{RMSE} \tag{3}
$$

with equality on the right when every channel is equally wrong and on the left when all the error
is in one channel. The two bundles therefore differ on velocity only through how unequally its
components are predicted.

No per-cell map is stored. A mean of per-channel square roots cannot be recovered from a map
summed over channels, which is the form every stored map takes; `rmse`'s map, the squared error,
is the object behind both numbers.

### Boundary handling

None. The operation is local to each cell, so no neighbourhood is ever consulted and no boundary
condition can enter.

### How its field reports it

This is the reduction of the machine-learning benchmarks for PDEs. The numerical-analysis and
weather-verification forms are pooled and live in [rmse](../../metrics/rmse/card.md), whose card sets the
three side by side.

- **PDEBench** [@takamoto2022]. The object is Equation (2) per sample and time step, averaged over
  the test samples and then over channels and time steps (code above), reported in tables of
  RMSE, nRMSE and maximum error per PDE and model (App. E) and named as one of three data-view
  metrics (Sect. 3.3). Its figure is the RMSE against the unrolled time step (Sect. 4.3, Fig. 5a
  and 5c). In its code that curve is the root mean square over a batch, space and channels pooled
  (`metrics`, `val_l2_time`), so the curve is `rmse`'s object and the table entry is this one.
  The experiment is autoregressive rollouts on a held-out tenth of each dataset's samples
  (Sect. 4.1).
- **The Well** [@ohana2024]. The object is the RMSE of each field over space (App. E.3), kept per
  field and also averaged over fields (`the_well/benchmark/trainer/training.py`,
  `split_up_losses`, the `full` entry); its headline metric is the normalised form, which is
  [vrmse](../../metrics/vrmse/card.md).

**The experiments here.** Rollouts against the solver over many initial conditions do not
exist. The nearest is `forecast_re5e4` (`docs/datasets/reynolds_ladder_2d.md`, "Forecast
pairs"): one model's predictions at ten prediction steps from two starting times, in three
runs, on which the error is drawn against lead time. A test set of many initial conditions is
written up in
[EXP-nrmse-rollouts-over-many-initial-conditions](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-nrmse-rollouts-over-many-initial-conditions.md).
The metric runs on the degradation ladder on `kinet_re5e4` and on the Reynolds ladder, where
velocity has two components. It is not run on `sod_shock_tube` or `synthetic_ensemble`: every
field there has one channel, where Equation (2) is `rmse` exactly (`card.yaml`, `not_run`).

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence rmse_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence rmse_channel_mean`.

<!-- END GENERATED performance -->

## Intuition

This is the root mean squared error taken separately for each component of a field and then
averaged. A velocity field has two components; the error in each is measured on its own, and the
two sizes are averaged with equal weight.

The difference from pooling every component into one root mean square shows when the components
are predicted unequally. On a four-by-four grid with two components, one in which a bright square
moved by one cell and one predicted exactly:

```
first component                second component
reference      candidate       reference      candidate
0 0 0 0        0 0 0 0         0 0 0 0        0 0 0 0
0 1 1 0        0 0 1 1         0 1 1 0        0 1 1 0
0 1 1 0        0 0 1 1         0 1 1 0        0 1 1 0
0 0 0 0        0 0 0 0         0 0 0 0        0 0 0 0

per component: 0.5             per component: 0

rmse_channel_mean = 0.25       rmse (pooled) = 0.354
```

The first component has a root mean squared error of one half and the second none, so their
average is a quarter. Pooling all thirty-two entries first gives the square root of an eighth,
0.354: the square root is taken after the averaging, so the bad component counts for more. On a
field with one component the two are identical.

What this metric ignores is everything a root mean squared error ignores: where in the domain the
errors sit, and therefore whether a feature is displaced or wrong.

## Reading the output

The value runs from zero upwards with no upper limit, in the field's own units, so values on
different fields cannot be compared. Lower is better, and zero means the two fields are identical
cell for cell. There is no good value in the abstract: it depends on how much the field varies,
which is why the suite reports damage beside it, the value over what the reference's own spatial
mean scores.

On density and vorticity it equals `rmse` exactly, so on those fields it adds nothing. On velocity
it is the number to set beside a PDEBench table entry; compare it with `rmse` to see how unequally
the two components are predicted. Comparisons across models on one field, dataset and analysis
grid are the intended use; comparisons across resolutions are invalid as they stand, because the
mean over cells reweights the small scales when the grid is refined.

## Limitations

Averaging after the square root rewards improving the better-predicted component more than
pooling does. With one component wrong by an RMSE of $a$ and the other by $b$ much smaller,
removing the second error lowers Equation (2) by $b/2$, linearly in $b$, while it lowers `rmse`
only by about $b^2 / (2\sqrt{2}\,a)$, quadratically. A model can therefore lower this number by
perfecting a component that was already nearly right while the badly predicted one does not move.
That follows from Equation (2); it is not a measurement. Reading `rmse` beside it shows when
that is happening.

It also inherits every limitation of `rmse`: a displaced feature is charged twice, once where it
should be and once where it is, and the response to a sub-cell displacement is quadratic in the
squared error underneath.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence rmse_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence rmse_channel_mean`.

<!-- END GENERATED run -->

Each subsection links to the degradations that subsection reports. What those degradations
do, and what their strength numbers mean, is documented on their own pages.

<!-- GENERATED experiments: written by `python -m fmeval.cards catalog`, do not edit -->

**Across the experiments.**

| experiment | what a run on it is evidence of | on this card |
|---|---|---|
| `kinet_re5e4` | developed flow | not yet run |
| `kinet_re1e6` | developed flow at Re = 1e6, twenty times the Reynolds number of kinet_re5e4, from the same initial condition | not yet run |
| `synthetic_ensemble` | a calibrated null: evidence that the estimator computes what it claims to compute, and nothing about turbulence | not applicable: the dataset holds density alone, one channel, where this metric is rmse exactly |
| `sod_shock_tube` | an analytic check: evidence that the metric locates and scores a known shock correctly, and nothing about turbulence | not applicable: every field of the one-dimensional tube has one channel, where this metric is rmse exactly |
| `forecast_re5e4` | real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded | not yet run |

One row per dataset a card may cite (`configs/cards/default.yaml`). *Measured* names the run the card cites: the main results are `## Performance` and the subsections below, and every other run has its own subsection headed with its dataset. *Not applicable* gives the reason: one that follows from what the metric declares and what the dataset offers, or one a person wrote on the card (`not_run` in `card.yaml`) because the result would carry no information. *Not yet run* means the metric can run there and the card cites no run on it yet.

<!-- END GENERATED experiments -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence rmse_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence rmse_channel_mean`.

<!-- END GENERATED results_smoothing -->

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence rmse_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence rmse_channel_mean`.

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence rmse_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence rmse_channel_mean`.

<!-- END GENERATED results_geometric -->

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence rmse_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence rmse_channel_mean`.

<!-- END GENERATED results_resolution -->

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence rmse_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence rmse_channel_mean`.

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence rmse_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence rmse_channel_mean`.

<!-- END GENERATED results_canaries -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence rmse_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence rmse_channel_mean`.

<!-- END GENERATED results_summary -->

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence rmse_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence rmse_channel_mean`.

<!-- END GENERATED results_damage_by_level -->

## References

\bibliography
