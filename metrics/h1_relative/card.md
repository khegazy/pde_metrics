---
name: h1_relative
kind: metric
---

## Definition

Write $f$ for the reference and $g$ for the candidate, each with $C$ channels on a periodic grid
of $N_j$ cells along axis $j$, and $e = g - f$ for the error. For one channel $v$, the
discrete H^1 norm used here sums the squares of the field and of its centred first differences
over all cells $\mathbf{i}$,

$$
\| v \|_{H^1}^2 = \sum_{\mathbf{i}} v_{\mathbf{i}}^2
+ \sum_j \sum_{\mathbf{i}} \Bigl( \frac{N_j}{2}
\bigl( v_{\mathbf{i} + \mathbf{e}_j} - v_{\mathbf{i} - \mathbf{e}_j} \bigr) \Bigr)^2 \tag{1}
$$

where $\mathbf{e}_j$ is one cell along axis $j$ and indices wrap around. The factor $N_j/2$ is
$1/(2h_j)$ with $h_j = 1/N_j$: the domain is taken as one unit long on every axis, whatever the
analysis grid's spacing. The metric is the relative norm of the error, summed over channels,

$$
\mathrm{H}^1_{\mathrm{rel}}(f, g) = \sum_{c=1}^{C}
\frac{\| e^{(c)} \|_{H^1}}{\| f^{(c)} \|_{H^1} + 10^{-8}} \tag{2}
$$

Equations (1) and (2) are what `H1Loss` of the neural-operator library computes with its
defaults, line for line [@neuraloperator2026]: the zeroth-order term and the first derivatives
(`compute_terms`), periodic centred differences (`FiniteDiff`), the spacing `measure / N` with
`measure = 1.0` (`uniform_quadrature`), the ratio of square roots with `eps = 1e-8` added to the
denominator (`rel`), and the sum over channels (`reduction="sum"`). Nothing in them is this
repository's choice. Two of the library's conventions are worth naming because they change the
number. The sums are not divided by the cell count, which cancels in the ratio except against the
$10^{-8}$. And taking the domain as one unit long makes a mode with $m$ periods across the box
weigh about $(2\pi m)^2$ in the derivative term against 1 in the value term, so on any field
with structure the derivative term dominates. Taking the derivative in the dataset's own length
unit instead would make the weight depend on that unit; the choice and its reversal are in
`judgements/017`.

The derivative of the error is the difference of the derivatives, so Equation (2) is also the
ratio of the H^1 distance between the two fields to the reference's H^1 norm.

### Boundary handling

Periodic on every axis: the centred difference wraps around the domain (`np.roll`), as the
library's default `periodic_in_x=True` does with `torch.roll`. The metric therefore declares
`requires_periodic` and is not run on a dataset with a non-periodic axis, such as the Sod shock
tube. The library also offers one-sided third-order differences at a wall
(`periodic_in_x=False`); they are not built here, because the only non-periodic dataset is Sod,
whose shock is not in H^1, so the derivative term there would measure the grid spacing rather
than the fields (see [h1_seminorm](../../metrics/h1_seminorm/card.md), Limitations).

### How its field reports it

**Neural-operator learning.** The relative inhomogeneous H^1 error is that field's Sobolev
error, used both as a training loss and as a reported test error.

- **The object and its normalisation.** Equation (2), per test sample, then averaged over the
  test set: the library's `Trainer.evaluate` sums the loss over batches and divides by the
  number of samples [@neuraloperator2026]. The Markov neural operator paper defines the Sobolev
  norm of the error with the sum over derivative orders starting at zero, so inhomogeneous
  ([@li2022mno], Sect. 3, Eq. (3), with its Fourier form in Eq. (4)), and trains with relative
  losses ([@li2022mno], Sect. 4). Its authors' own code takes the derivatives spectrally, with
  integer wavenumbers; the library takes centred differences, which this bundle follows. The two
  share the value term and differ in how the slope term is weighted, and which of them produced
  a published table is not stated (`issues/138`).
- **What is reported beside it.** A table of test errors per model, an H^1 column beside the
  relative L^2 one ([@li2022mno], App. A.3, Table 3, Kolmogorov flow at Re = 40, and Table 5;
  [@kossaifi2023], Tables 3 and 4), or the two side by side in a figure across models
  ([@kossaifi2023], Fig. 1). Dropping the derivative terms from both sums of Equation (2)
  leaves the relative L^2 error, the error the Fourier neural operator papers report ([@li2021fno], Sects.
  5.1-5.3; defined in [@kovachki2023], Sect. 6); PDEBench's per-channel form of it is
  [nrmse](../../metrics/nrmse/card.md), which averages over channels where this bundle sums.
- **The experiment.** Held-out test samples of a parametric problem or test trajectories of a
  dynamical one, predicted one step ahead and rolled out (the Kolmogorov flow of [@li2022mno], App. A.3). The repository
  has `forecast_re5e4`: one model's rollouts from two starting times, ten prediction steps each,
  in three runs, where the error is drawn against lead time. Many test trajectories are written
  up in
  [EXP-nrmse-rollouts-over-many-initial-conditions](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-nrmse-rollouts-over-many-initial-conditions.md).
  The metric also runs on the degradation ladder on `kinet_re5e4`, on the Reynolds ladder and on
  the member mean of `synthetic_ensemble`.
- **The other field.** Finite-element analysis reports the absolute H^1 *seminorm* of the error
  against mesh size, with no zeroth-order term and no division by the solution's norm:
  [h1_seminorm](../../metrics/h1_seminorm/card.md).

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence h1_relative`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence h1_relative`.

<!-- END GENERATED performance -->

## Intuition

This metric measures how wrong a prediction is as a fraction of how large the true field is,
counting both the values and the slopes. A prediction whose values are close but whose slopes are
wrong, such as a correct pattern drawn slightly too smooth or too jagged, is charged for the
slopes, which a plain relative error would not see.

It works by adding up, over every cell, the square of the error and the squares of how fast the
error changes from one neighbour to the next, taking the root, and dividing by the same total for
the true field. The slopes are measured as if the box were one unit wide, so a pattern that
repeats several times across the box has slopes many times its height, and on most real fields
the slopes dominate the total. Each component of a field is scored on its own and the scores are
added.

A worked example on a four by four grid whose rows are all the same.

```
one row of each field (every row the same)    h1_relative    relative L2 error
reference        1     0    -1     0
moved one cell   0     1     0    -1             1.414           1.414
checkerboard     1.5  -0.5  -0.5  -0.5           0.1715          0.7071
added
```

Moving the pattern by one cell gives the same score as the plain relative error, because the
error is the same single wave in its values and in its slopes. Adding a checkerboard that
alternates every cell gives a much smaller score than the plain relative error: the slope at each
cell is taken from its two neighbours, which for a checkerboard are equal, so the slopes of that
error are zero, while the true field's slopes still enlarge the denominator.

What it ignores: the error that alternates from cell to cell, in its slope term, and anything
about where the error sits, since it is a sum over the whole domain.

## Reading the output

- **Range and units.** Zero and up, dimensionless. A prediction of zero scores one per channel,
  so a two-component velocity field scores up to about two for a prediction of zero and a
  one-channel field about one.
- **Direction.** Lower is better. Identical fields score zero.
- **What is a good value.** A fraction of the reference's own size in this norm, so 0.05 means an
  error a twentieth of the reference's H^1 norm. Where a field's mean is much larger than its
  fluctuation, as density's is here, the mean sets most of the denominator's value term, and the
  number reads small for an error that is large against the fluctuation; read it beside
  [vrmse](../../metrics/vrmse/card.md), which divides by the fluctuation.
- **Valid comparisons.** Models scored against the same reference field on the same analysis
  grid. Across fields only with the channel count in mind, because channels are summed, not
  averaged. Across analysis grids for structure both grids resolve: the domain is one unit long on
  every grid, so a smooth mode's slope does not depend on the cell count, but the centred
  difference weighs modes near each grid's own finest scale differently.
- **Not symmetric.** The reference's norm is the denominator, so the arguments cannot be swapped.

## Limitations

- **A checkerboard error is free in the slope term.** The centred difference of the alternating
  mode is exactly zero, so error at the grid scale is charged only through the value term, which
  is small next to a reference whose slopes dominate its norm. The worked example scores such an
  error at 0.17 where the plain relative error reads 0.71. A prediction with grid-scale ringing
  can therefore score better here than under a plain relative error, the opposite of what a
  Sobolev norm is chosen for.
- **The derivative weight depends on the domain convention.** On the unit domain the slope term
  of a mode with $m$ periods across the box weighs about $(2\pi m)^2$ against 1, so on these
  fields the number is close to a relative gradient error. The same formula with the derivative
  taken in the dataset's own unit of length (`judgements/017`) would make the slope term negligible
  on kinet, whose box is 256 long, and the number would be the relative L^2 error.
- **At a shock the slope term measures the grid.** A discontinuity is not in H^1; the centred
  difference across a jump grows with the cell count, so on a shocked flow the value depends on
  the resolution as much as on the prediction.
- **Channels are summed.** A velocity error and a density error of the same relative size score
  in a ratio of two to one.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence h1_relative`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence h1_relative`.

<!-- END GENERATED run -->

Each subsection links to the degradations that subsection reports. What those degradations
do, and what their strength numbers mean, is documented on their own pages.

<!-- GENERATED experiments: written by `python -m fmeval.cards catalog`, do not edit -->

**Across the experiments.**

| experiment | what a run on it is evidence of | on this card |
|---|---|---|
| `kinet_re5e4` | developed flow | not yet run |
| `kinet_re1e6` | developed flow at Re = 1e6, twenty times the Reynolds number of kinet_re5e4, from the same initial condition | not yet run |
| `synthetic_ensemble` | a calibrated null: evidence that the estimator computes what it claims to compute, and nothing about turbulence | not yet run; on this dataset the metric scores the member mean of the ensemble |
| `sod_shock_tube` | an analytic check: evidence that the metric locates and scores a known shock correctly, and nothing about turbulence | not applicable: needs a periodic domain, and this dataset is not periodic |
| `forecast_re5e4` | real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded | not yet run |

One row per dataset a card may cite (`configs/cards/default.yaml`). *Measured* names the run the card cites: the main results are `## Performance` and the subsections below, and every other run has its own subsection headed with its dataset. *Not applicable* gives the reason: one that follows from what the metric declares and what the dataset offers, or one a person wrote on the card (`not_run` in `card.yaml`) because the result would carry no information. *Not yet run* means the metric can run there and the card cites no run on it yet.

<!-- END GENERATED experiments -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence h1_relative`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence h1_relative`.

<!-- END GENERATED results_smoothing -->

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence h1_relative`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence h1_relative`.

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence h1_relative`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence h1_relative`.

<!-- END GENERATED results_geometric -->

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence h1_relative`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence h1_relative`.

<!-- END GENERATED results_resolution -->

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence h1_relative`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence h1_relative`.

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence h1_relative`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence h1_relative`.

<!-- END GENERATED results_canaries -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence h1_relative`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence h1_relative`.

<!-- END GENERATED results_summary -->

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence h1_relative`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence h1_relative`.

<!-- END GENERATED results_damage_by_level -->

## References

\bibliography
