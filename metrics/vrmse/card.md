---
name: vrmse
kind: metric
---

## Definition

For fields $f$ (reference) and $g$ (candidate) on the same analysis grid, with $C$ channels and
$N$ cells per channel, write $\bar f_c$ for the spatial mean of channel $c$ of the reference and

$$
s_c^2 = \frac{1}{N - 1} \sum_{i=1}^{N} \bigl( f_{c,i} - \bar f_c \bigr)^2 \tag{1}
$$

for its variance. The variance-scaled root mean squared error of The Well [@ohana2024] divides
each channel's mean squared error by that variance plus a constant, takes the square root, and
averages over channels:

$$
\mathrm{VRMSE}(f, g) = \frac{1}{C} \sum_{c=1}^{C}
\sqrt{\frac{\frac{1}{N} \sum_{i} \bigl( f_{c,i} - g_{c,i} \bigr)^2}{s_c^2 + \epsilon}} ,
\qquad \epsilon = 10^{-7} \tag{2}
$$

The paper writes VRMSE as $\bigl(\langle |u - v|^2 \rangle / (\langle |u - \bar u|^2 \rangle +
\epsilon)\bigr)^{1/2}$ with $u$ the truth, $\langle \cdot \rangle$ the spatial mean and
$\epsilon = 10^{-7}$ (App. E.3, unnumbered). Equation (2) follows its code in the two places the
code is more specific: the variance is `torch.std(y) ** 2`, which divides by $N - 1$, and
$\epsilon$ is added to the variance, not to its square root
(`the_well/benchmark/metrics/spatial.py`, `VRMSE` through `NMSE` with `norm_mode="std"`). The code
returns one value per field; the library logs each and their mean over fields, and the paper's
tables report that mean (`the_well/benchmark/trainer/training.py`, `split_up_losses`, the `full`
entry; Sect. 4, Table 2: "averaged over all physical fields"). The mean over channels in Equation
(2) is that mean, for the channels of one field.

Predicting the reference's own spatial mean everywhere scores
$\sqrt{(N-1)/N \cdot s_c^2 / (s_c^2 + \epsilon)}$, just under one; The Well reads its tables
against that landmark (Table 2 caption: "predicting the mean value of the target field results in
a score of 1"). That prediction is this repository's damage anchor (`judgements/001`), so on a
one-channel field the value and the damage differ only by that factor.

$\epsilon$ is in the square of the field's units, so it is not scale-free. On a channel whose
variance is far above $10^{-7}$ it changes nothing; on one whose variance is comparable it lowers
the value by $\sqrt{s_c^2 / (s_c^2 + \epsilon)}$. On `kinet_re5e4` density's fluctuation root mean
square is $2.1 \times 10^{-3}$ to $6.7 \times 10^{-3}$ over frames 2000 to 10000 (`AGENTS.md` §4),
a variance of $4.5 \times 10^{-6}$ to $4.5 \times 10^{-5}$, so the factor is 0.989 to 0.9989; the
stored vorticity's fluctuation is of the same order ($2.1 \times 10^{-3}$ to $3.1 \times 10^{-3}$
at frames 2000, 6000 and 10000, measured from the files on 2026-11-04). That is The Well's
behaviour, kept so that the number is the one its tables report. On a one-channel field the factor
cancels from damage. On the development dataset, whose density fluctuation is about $10^{-8}$ of
its mean, $\epsilon$ is the whole denominator.

The reference alone sets the denominator, so Equation (2) is not symmetric, and because each term
of a triangle is scaled by a different reference it does not satisfy the triangle inequality
(`test_metric.py` gives a three-field example). A uniform reference channel has $s_c = 0$ and is
divided by $\sqrt{\epsilon}$, so the value is always finite.

### Boundary handling

None. The operation is local to each cell, and the mean and variance are taken over the whole
field, so no neighbourhood and no boundary condition enter.

### How its field reports it

The name and the definition are The Well's. PDEBench's normalisation, by the raw root mean square
with no mean removed, is the bundle [nrmse](../../metrics/nrmse/card.md); on density here the two differ by
two to three orders of magnitude.

- **The Well** [@ohana2024]. The object is Equation (2) per field and prediction step, averaged
  over the test trajectories and over fields. Its tables report the one-step value on sliding
  windows of the test set (Sect. 4, Table 2) and the value averaged over the prediction-step
  windows 6 to 12 and 13 to 30 of rollouts started from the beginning of each simulation
  (Table 3). Its figure sets the VRMSE of each state variable side by side for several models,
  beside the growth along the rollout of a binned spectral error (Sect. 4.1, Fig. 6). Its library
  also logs the value of each field against prediction step (`split_up_losses`, `time_logs`).
  The experiment is a test split of a tenth of each dataset's trajectories (Sect. 3, the
  0.8/0.1/0.1 split), predicted one step at a time and as rollouts.
- **PDEBench** [@takamoto2022] normalises without removing the mean: [nrmse](../../metrics/nrmse/card.md).
- **Numerical analysis and weather verification** report unnormalised norms:
  [rmse](../../metrics/rmse/card.md) and [max_error](../../metrics/max_error/card.md).

**The experiments here.** Neither of The Well's two settings exists as it does there.
`forecast_re5e4` (`docs/datasets/reynolds_ladder_2d.md`, "Forecast pairs") gives one model's
rollouts from two starting times, ten prediction steps each, in three runs; the error is drawn
against lead time, and the steps cover part of the 6-to-12 window and none of the 13-to-30 one.
Many test trajectories are written up in
[EXP-nrmse-rollouts-over-many-initial-conditions](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-nrmse-rollouts-over-many-initial-conditions.md).
The metric also runs on the degradation ladder on `kinet_re5e4`, on `sod_shock_tube`, on the
member mean of `synthetic_ensemble` and on the Reynolds ladder: it needs nothing but two fields
on one grid.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence vrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence vrmse`.

<!-- END GENERATED performance -->

## Intuition

The variance-scaled root mean squared error is the root mean squared error expressed as a
fraction of how much the reference field actually varies about its own average. An error of one
unit means something different in a field that swings by a thousand and in one that swings by
two, and dividing by the swing is what makes the two produce the same number.

The swing is measured about the field's mean, not from zero, which decides what happens on a
field sitting on a large constant background. On a four-by-four grid, the same displaced square
scored as it stands and on a background of a thousand:

```
                            rmse      vrmse      nrmse
as it stands                0.5       1.118      1.0
on a background of 1000     0.5       1.118      0.0005
```

The background changes neither the error nor the swing about the mean, so this metric does not
move; PDEBench's form, in the last column, measures the size from zero and reads the second row as
nearly perfect. The value 1.118 says the error is a little larger than the swing itself, which is
worse than predicting the field's average everywhere: that prediction scores just under one, and
it is the landmark The Well's tables are read against. Each component of a field is scaled by its
own swing before the components are averaged.

What this metric ignores is where the errors sit, as every cell-by-cell error does, and the
absolute size of the error.

## Reading the output

The value runs from zero upwards with no upper limit and is dimensionless. Lower is better, and
zero means the fields are identical. One is the landmark: predicting the reference's own mean
everywhere scores just under one, so a value above one means the prediction is worse than that.

Because it is dimensionless and measured about each field's mean, it is the cell-by-cell error
whose values can be set side by side across fields: a value of 0.1 means an error a tenth of the
field's swing, on density, velocity or vorticity alike. The reference must be the trusted field:
the metric is asymmetric. On a one-channel field it orders candidates exactly as `rmse` does.

## Limitations

The normalisation hides absolute magnitude. Two predictions with the same value on fields whose
fluctuations differ by three orders of magnitude have very different absolute errors, and if the
downstream use cares about absolute error the number will not say so.

The denominator is measured from the reference on each frame. As a decaying flow loses its
fluctuation the same absolute error scores higher, so a value rising along a trajectory does not
by itself mean the prediction got worse.

The constant $10^{-7}$ is in the field's own units squared. On a field whose variance is near or
below it, such as density on the development dataset, the value no longer measures the error
against the field's swing at all, and on `kinet_re5e4` it lowers the value by up to about one
percent on density and vorticity, more on frames where the fluctuation is smallest.

It shares every cell-by-cell metric's blindness to position and its quadratic response to sub-cell
displacement.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence vrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence vrmse`.

<!-- END GENERATED run -->

Each subsection links to the degradations that subsection reports. What those degradations
do, and what their strength numbers mean, is documented on their own pages.

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence vrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence vrmse`.

<!-- END GENERATED results_smoothing -->

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence vrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence vrmse`.

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence vrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence vrmse`.

<!-- END GENERATED results_geometric -->

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence vrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence vrmse`.

<!-- END GENERATED results_resolution -->

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence vrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence vrmse`.

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence vrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence vrmse`.

<!-- END GENERATED results_canaries -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence vrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence vrmse`.

<!-- END GENERATED results_summary -->

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence vrmse`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence vrmse`.

<!-- END GENERATED results_damage_by_level -->

## References

\bibliography
