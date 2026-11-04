---
name: max_error_channel_mean
kind: metric
---

## Definition

For fields $f$ (reference) and $g$ (candidate) on the same analysis grid, with $C$ channels and
$N$ cells per channel, this bundle reports the mean over channels of each channel's largest
absolute error:

$$
\mathrm{MaxE}_{\mathrm{ch}}(f, g) = \frac{1}{C} \sum_{c=1}^{C} \max_{1 \le i \le N}
\bigl| f_{c,i} - g_{c,i} \bigr| \tag{1}
$$

This is how PDEBench's code reduces its maximum error [@takamoto2022]: the maximum of the absolute
error over space for each sample, channel and time step, the maximum over the samples of a batch,
and then the mean over channels and time steps (`pdebench/models/metrics.py`, `metric_func`,
`err_Max`). The paper names the metric and gives no equation for it (Sect. 3.3; App. B says it
"measures the model's worst prediction"). The harness scores one frame of one field at a time,
so the mean over channels is the reduction that remains. The Well's $L^\infty$ error is the same
maximum per field, which its library averages over fields [@ohana2024] (App. E.3;
`the_well/benchmark/metrics/spatial.py`, `LInfinity`).

[max_error](../../metrics/max_error/card.md) takes one maximum over every channel and cell, the discrete
$L^\infty$ norm of numerical analysis [@roy2005] (Sect. 2.5, Eq. 7). On a one-channel field
(density, vorticity) the two are the same number. On several channels a mean of $C$ maxima is
never larger than the largest of them, which is `max_error`, and never smaller than that over $C$:

$$
\frac{\mathrm{MaxE}}{C} \le \mathrm{MaxE}_{\mathrm{ch}} \le \mathrm{MaxE} \tag{2}
$$

with equality on the right when every channel's worst error is the same size and on the left
when only one channel is wrong.

No per-cell map is stored. A mean of per-channel maxima cannot be recovered from a map reduced
over channels; `max_error`'s map shows where the worst cells are.

### Boundary handling

None. The operation is local to each cell, so no neighbourhood is ever consulted and no boundary
condition can enter.

### How its field reports it

This is the reduction of the machine-learning benchmarks for PDEs. Numerical analysis reports
the pooled maximum, [max_error](../../metrics/max_error/card.md), whose card describes the
order-of-accuracy test it is used in.

- **PDEBench** [@takamoto2022]. The object is Equation (1) per time step, taken as the worst case
  over the samples of each batch, then averaged over batches, channels and time steps (code
  above); it is described as the local worst case and a proxy for the stability of time-stepping
  (Sect. 3.3, table of metrics). It is reported in the tables of every metric per PDE and model
  (App. E); no figure of it is drawn. The experiment is autoregressive rollouts on a held-out
  tenth of each dataset's samples (Sect. 4.1).
- **The Well** [@ohana2024]. The $L^\infty$ error is one of its library's spatial metrics, one
  value per field (App. E.3); its tables and figures report VRMSE, not this.

**The experiments here.** Rollouts over many initial conditions do not exist; `forecast_re5e4`
(`docs/datasets/reynolds_ladder_2d.md`, "Forecast pairs") gives one model's predictions at ten
prediction steps from two starting times, on which the error is drawn against lead time, and
[EXP-nrmse-rollouts-over-many-initial-conditions](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-nrmse-rollouts-over-many-initial-conditions.md)
writes up the missing test set. The metric also runs on the degradation ladder on `kinet_re5e4`,
on `sod_shock_tube`, on the member mean of `synthetic_ensemble` and on the Reynolds ladder: it
needs nothing but two fields on one grid.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence max_error_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence max_error_channel_mean`.

<!-- END GENERATED performance -->

## Intuition

This is the worst single-cell error taken separately for each component of a field and then
averaged. A velocity field has two components; for each, the cell where it is most wrong is found
and its error read off, and the two worst errors are averaged.

The difference from taking one maximum over every component shows when the components are
predicted unequally. On a four-by-four grid with two components, one in which a bright square
moved by one cell and one predicted exactly:

```
first component                second component
reference      candidate       reference      candidate
0 0 0 0        0 0 0 0         0 0 0 0        0 0 0 0
0 1 1 0        0 0 1 1         0 1 1 0        0 1 1 0
0 1 1 0        0 0 1 1         0 1 1 0        0 1 1 0
0 0 0 0        0 0 0 0         0 0 0 0        0 0 0 0

worst cell: 1                  worst cell: 0

max_error_channel_mean = 0.5   max_error (one maximum) = 1
```

The first component's worst cell is wrong by the full height of the square and the second's by
nothing, so their average is a half, while a single maximum over both reports the one cell that
is completely wrong. On a field with one component the two are identical.

What this metric ignores is everything except each component's worst cell: how many cells are
wrong, and by how much, below those.

## Reading the output

The value runs from zero upwards with no upper limit, in the field's own units, so values on
different fields cannot be compared. Lower is better, and zero means the fields agree in every
cell. Unlike `max_error` it is not a bound on the error of any one cell: on velocity, one
component can be wrong by up to twice this value somewhere.

On density and vorticity it equals `max_error` exactly. On velocity it is the number to set beside
a PDEBench table entry. Comparisons across models on one field, dataset and analysis grid are the
intended use; comparisons across resolutions are invalid as they stand, because a finer grid
offers more cells to take the maximum over and a remap onto cell averages lowers peaks.

## Limitations

Averaging the channel maxima loses the one property that makes a maximum useful, a guarantee. A
reader who takes a value of 0.1 to mean that no cell is off by more than 0.1 is wrong on a
two-component field whenever one component's worst error is larger than the other's. Equation
(2) bounds the gap: the largest single error is at most $C$ times this value.

It inherits every limitation of `max_error`: the value is set by one cell per component, so it is
noisy from frame to frame, and a displaced sharp front scores its full height once the shift
reaches a cell, so it cannot tell a small displacement from a large one.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence max_error_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence max_error_channel_mean`.

<!-- END GENERATED run -->

Each subsection links to the degradations that subsection reports. What those degradations
do, and what their strength numbers mean, is documented on their own pages.

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence max_error_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence max_error_channel_mean`.

<!-- END GENERATED results_smoothing -->

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence max_error_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence max_error_channel_mean`.

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence max_error_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence max_error_channel_mean`.

<!-- END GENERATED results_geometric -->

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence max_error_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence max_error_channel_mean`.

<!-- END GENERATED results_resolution -->

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence max_error_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence max_error_channel_mean`.

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence max_error_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence max_error_channel_mean`.

<!-- END GENERATED results_canaries -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence max_error_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence max_error_channel_mean`.

<!-- END GENERATED results_summary -->

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence max_error_channel_mean`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence max_error_channel_mean`.

<!-- END GENERATED results_damage_by_level -->

## References

\bibliography
