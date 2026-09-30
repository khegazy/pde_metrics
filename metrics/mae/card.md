---
name: mae
kind: metric
---

## Definition

For fields $f$ (reference) and $g$ (candidate) sampled on the same analysis grid, with $C$
channels and $N$ cells per channel,

$$
\mathrm{MAE}(f, g) = \frac{1}{CN} \sum_{c=1}^{C} \sum_{i=1}^{N}
\bigl| f_{c,i} - g_{c,i} \bigr| \tag{1}
$$

For a vector field the channels are pooled rather than reduced separately. The analysis
grid is uniform, so cells carry equal weight; on a non-uniform grid Equation (1) would
need cell volumes and would no longer be a plain mean.

Unlike the squared error, Equation (1) is a metric in the mathematical sense: it is the
L1 distance, and it satisfies the triangle inequality.

For a displacement $\delta$ small compared with the scale of variation, expanding
$f(x + \delta) - f(x) \simeq \delta\, \partial_x f$ in Equation (1) gives

$$
\mathrm{MAE} \simeq \delta \bigl\langle |\partial_x f| \bigr\rangle \tag{2}
$$

which is linear in the displacement where the squared error is quadratic. That single
difference in exponent is what separates the two in practice.

### Boundary handling

None. The operation is local to each cell, so no neighbourhood is ever consulted and no
boundary condition can enter.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence mae --results results/comparison_1790639359`, do not edit -->

| test family | field | degradations | rank correlation | weakest gap between neighbouring strengths | first strength detected |
|---|---|---|---|---|---|
| Displacement | density | 2 | 1 to 1 | 0.959 | level 3 |
| Displacement | velocity | 2 | 1 to 1 | 0.96 | level 5 |
| Displacement | vorticity | 2 | 1 to 1 | 0.795 | level 1 |
| Resolution loss | density | 2 | 1 to 1 | 0.542 | level 4 |
| Resolution loss | velocity | 2 | 1 to 1 | 0.958 | level — |
| Resolution loss | vorticity | 2 | 1 to 1 | 0.738 | level 1 |
| Smoothing | density | 3 | 1 to 1 | 0.963 | level 3 |
| Smoothing | velocity | 3 | 1 to 1 | 0.977 | level 4 |
| Smoothing | vorticity | 3 | 1 to 1 | 0.815 | level 2 |
| Spectral filtering | density | 4 | 0.5 to 1 | 0.192 | level 1 |
| Spectral filtering | velocity | 4 | 1 to 1 | 0.864 | level 1 |
| Spectral filtering | vorticity | 4 | 0.8 to 1 | 0.323 | level 1 |
| Noise | density | 1 | 1 to 1 | 1 | level 3 |
| Noise | velocity | 1 | 1 to 1 | 1 | level 4 |
| Noise | vorticity | 1 | 1 to 1 | 1 | level 3 |
| trap test: fake prediction, right spectrum | density | 1 | — | — | damage 1.36 |
| trap test: fake prediction, right spectrum | velocity | 1 | — | — | damage 0.757 |
| trap test: fake prediction, right spectrum | vorticity | 1 | — | — | damage 1.41 |

One row per family of degradation and physical field. **Rank correlation** asks whether the metric put the strengths of one degradation in the right order: it is the Spearman correlation between the metric and the applied strength, computed inside a single frame, and the column gives the range over the degradations in that family. A value of 1 means every strength was ordered correctly in every frame. **Weakest gap between neighbouring strengths** asks whether the metric can tell one strength from the next: it is the smallest Mann-Whitney overlap between any two neighbouring strengths, where 1 means the two never overlap and 0.5 means the metric cannot separate them at all. **First strength detected** is the mildest strength at which the metric has moved a tenth of the way from the undegraded reference toward a field with no relation to the truth; a dash means the metric never reached that tenth. **Damage** is that same 0-to-1 scale read as a number: 0 is the undegraded reference and 1 is an unrelated field.

This table reports what was measured and grades none of the measurements. What the numbers mean for this metric is written in the subsections below, beside the test that produced each number.

**Profile.**

| field | selectivity | charges most for | charges least for | response provably below 0.05 at 90% on | elasticity to a sub-pixel shift (against severity (distance)) | compute cost (x cheapest in this run) |
|---|---|---|---|---|---|---|
| density | 0.6 | `coarsen_bandlimited` | `lowpass_ideal` | `coarsen_bandlimited` | 0.999 | 1.21 |
| velocity | 0.463 | `coarsen_bandlimited` | `highpass_ideal` | `coarsen_bandlimited` | 0.999 | 2.08 |
| vorticity | 0.13 | `additive_noise` | `highpass_butterworth` | — | 0.992 | 1.03 |

One row per physical field. **Selectivity** is how concentrated the metric's response is on a few degradations, measured per unit of field change: 0 means it charges every degradation the same, as mean squared error does by construction, and values toward 1 that one degradation carries most of it. **Charges most and least for** name the two ends of that profile. **Response provably below** lists degradations on which the upper confidence bound of the largest damage lies below the margin -- an equivalence test, so an entry says the response is provably small, not merely not significant; a dash means no degradation met the bound. **Elasticity** is the slope of log damage against log shift over the smallest shifts: 1 means damage grows in proportion to the shift, 2 with its square. **Compute cost** is wall-clock per evaluation over the cheapest metric and field in the same run.

<!-- END GENERATED performance -->

## Intuition

Mean absolute error compares two fields one cell at a time: subtract, take the size of
the difference regardless of sign, average. Taking the size rather than the square means
every unit of error counts the same wherever it appears, so one badly wrong cell and many
slightly wrong cells contribute in proportion to their total error rather than being
dominated by the worst. Nothing in the calculation looks beyond a single cell, so the
metric carries no notion of shape or position.

It shares that blindness with mean squared error and differs in how steeply it responds.
On a four-by-four grid, with one candidate that moved the bright square a cell and another
that halved its brightness where it stands:

```
reference        moved one cell    half brightness
0 0 0 0          0 0 0 0           0    0    0    0
0 1 1 0          0 0 1 1           0   0.5  0.5   0
0 1 1 0          0 0 1 1           0   0.5  0.5   0
0 0 0 0          0 0 0 0           0    0    0    0

                 mae = 0.25        mae = 0.125
```

The displaced candidate scores twice as badly as the damped one. Mean squared error, on
these same fields, makes it four times. Both prefer the damped candidate; they disagree
about by how much, and below one cell that disagreement grows into a factor of tens.

What this metric ignores is the arrangement of the errors: the same total error
concentrated at a sharp front and scattered as noise across the domain are the same
number.

## Reading the output

The value runs from zero upwards with no upper limit, in the field's own units, so a
density field and a vorticity field produce numbers that cannot be compared with each
other. Lower is better, and zero means the two fields are identical cell for cell. Because
it is linear rather than squared, the number is directly readable as a typical error size:
an MAE of 0.01 means the average cell is off by about 0.01 of whatever the field measures.

What counts as good depends entirely on the variance of the field being predicted, which
is why the suite reports damage — the value rescaled so that zero is the reference and one
is what two statistically similar but positionally unrelated fields score.

Comparisons across models on the same field, dataset and analysis grid are meaningful and
are the intended use. Comparisons across fields need normalising because of the units.
Comparisons across resolutions are invalid as they stand: the value is a mean over cells,
so refining the grid reweights the small scales even when nothing about the prediction has
changed. Compare on a common analysis grid, which is what this suite remaps onto before
measuring.

## Limitations

The linear response is a double-edged property. It makes MAE far more sensitive than MSE
to sub-cell displacement, which is useful when position matters, but it also means a
single catastrophically wrong region is not flagged any more urgently than the same total
error spread thinly everywhere. A model that is excellent across the domain and badly
wrong in one small area can score better than one that is mediocre throughout, and MAE
will not tell you which situation you are in.

It is also blind to position in the same way as every metric that compares fields cell by
cell, so a shock with exactly the right shape and strength sitting one cell over is
penalised twice: once where it should be and is not, once where it is and should not be.
And the absolute value is not differentiable at zero error, which matters if it is used as
a training loss rather than a diagnostic.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence mae --results results/comparison_1790639359`, do not edit -->

Measured on `kinet_re5e4`, frames 2000 to 10000 (161 frames of developed flow), on the 256 analysis grid, seed 20260807, at commit `ce78cb2d30d8` (working tree dirty). Run `comparison_1790639359`.

Every number in this section comes from that one run. Regenerate with `python -m fmeval.cards evidence <name> --results results/comparison_1790639359`.

<!-- END GENERATED run -->

Each subsection links to the degradations that subsection reports. What those degradations
do, and what their strength numbers mean, is documented on their own pages.

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence mae --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `box_blur` | density | 4 | 1 | 1 | 0.963 |
| `box_blur` | velocity | 4 | 1 | 1 | 1 |
| `box_blur` | vorticity | 4 | 1 | 1 | 0.815 |
| `gaussian_blur` | density | 4 | 1 | 1 | 0.976 |
| `gaussian_blur` | velocity | 4 | 1 | 1 | 1 |
| `gaussian_blur` | vorticity | 4 | 1 | 1 | 0.933 |
| `median_blur` | density | 3 | 1 | 1 | 0.973 |
| `median_blur` | velocity | 3 | 1 | 1 | 0.977 |
| `median_blur` | vorticity | 3 | 1 | 1 | 0.887 |

<!-- END GENERATED results_smoothing -->

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence mae --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `highpass_butterworth` | density | 4 | 0.8 | 0 | 0.308 |
| `highpass_butterworth` | velocity | 3 | 1 | 1 | 0.864 |
| `highpass_butterworth` | vorticity | 4 | 0.8 | 0.298 | 0.323 |
| `highpass_ideal` | density | 3 | 0.5 | 0 | 0.192 |
| `highpass_ideal` | velocity | 2 | 1 | 1 | 0.874 |
| `highpass_ideal` | vorticity | 4 | 0.8 | 0 | 0.324 |
| `lowpass_butterworth` | density | 4 | 1 | 1 | 0.843 |
| `lowpass_butterworth` | velocity | 3 | 1 | 1 | 1 |
| `lowpass_butterworth` | vorticity | 4 | 1 | 1 | 0.719 |
| `lowpass_ideal` | density | 3 | 1 | 1 | 0.948 |
| `lowpass_ideal` | velocity | 2 | 1 | 1 | 0.995 |
| `lowpass_ideal` | vorticity | 4 | 1 | 1 | 0.657 |

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence mae --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `translate_subpixel` | density | 6 | 1 | 1 | 0.961 |
| `translate_subpixel` | velocity | 6 | 1 | 1 | 0.96 |
| `translate_subpixel` | vorticity | 6 | 1 | 1 | 0.862 |
| `translate_x` | density | 5 | 1 | 1 | 0.959 |
| `translate_x` | velocity | 5 | 1 | 1 | 0.96 |
| `translate_x` | vorticity | 5 | 1 | 1 | 0.795 |

<!-- END GENERATED results_geometric -->

The response is linear in the displacement, as Equation (2) gives: on vorticity the damage
ratios per doubling below one cell are 2.00, 1.98 and 1.93 against the 2 implied by that
scaling. Against MSE over the same shifts, MAE assigns 47 times the damage at an eighth of
a cell and 6.2 times at one cell, and its damage at an eighth of a cell is 0.023 against
MSE's 0.00048. Of the cell-by-cell baselines, MAE is the one that notices sub-cell
displacement.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence mae --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `coarsen` | density | 4 | 1 | 1 | 0.962 |
| `coarsen` | velocity | 4 | 1 | 1 | 1 |
| `coarsen` | vorticity | 4 | 1 | 1 | 0.942 |
| `coarsen_bandlimited` | density | 4 | 1 | 0.59 | 0.542 |
| `coarsen_bandlimited` | velocity | 4 | 1 | 1 | 0.958 |
| `coarsen_bandlimited` | vorticity | 4 | 1 | 1 | 0.738 |

<!-- END GENERATED results_resolution -->

Both coarsenings are ordered correctly on every field, with a rank correlation of 1. They differ in size. At a factor of 16, `coarsen` costs 0.16, 0.07 and 0.46 of the unrelated-field value on density, velocity and vorticity, and `coarsen_bandlimited` 0.03, 0.03 and 0.49. The two operators keep the same block means, so on the smooth fields most of what `coarsen` charges is its staircase; on vorticity, whose structure the coarse grid genuinely cannot hold, they nearly agree. Under the band-limited operator density is in the right order in only 59% of frames: its damage at factors 2 and 4 is 0.002 at both, and which of the two is larger changes from frame to frame. The other pointwise metrics, `spectrum_l2` and `h1_seminorm` show this on density too, and its
cause is not established; `issues/039` records what was ruled out.

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence mae --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `additive_noise` | density | 4 | 1 | 1 | 1 |
| `additive_noise` | velocity | 4 | 1 | 1 | 1 |
| `additive_noise` | vorticity | 4 | 1 | 1 | 1 |

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence mae --results results/comparison_1790639359`, do not edit -->

| field | damage assigned to the fake prediction | closest real degradation | value on an unrelated field |
|---|---|---|---|
| density | 1.36 | `highpass_ideal=3.03099` | 0.00521 |
| velocity | 0.757 | `highpass_ideal=4.02293` | 0.0593 |
| vorticity | 1.41 | `translate_x=16` | 0.00186 |

The fake prediction here has exactly the reference field's amplitude spectrum and completely scrambled structure. Damage of 1 is what a field with no relation to the truth scores, so the damage column says how close to useless this metric considers that fake prediction: a low number means the metric was fooled. The third column translates the same number into an ordinary degradation whose damage the fake prediction matches, which is easier to picture.

<!-- END GENERATED results_canaries -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence mae --results results/comparison_1790639359`, do not edit -->

| compared with | rank correlation over every degradation |
|---|---|
| `rmse` | 0.986 |
| `mse` | 0.986 |
| `nrmse` | 0.963 |
| `h_minus_one` | 0.913 |
| `h1_seminorm` | 0.677 |
| `spectrum_l2` | 0.136 |
| `increment_w1` | 0.0547 |
| `increment_flatness` | -0.101 |
| `enstrophy` | -0.103 |
| `palinstrophy` | -0.114 |
| `kinetic_energy` | -0.208 |

Computed on the median value at each combination of degradation and strength, over every degradation and physical field in the run, with the undegraded reference excluded. Two metrics correlating near 1 put the degradations in the same order, but the two may still weight those degradations very differently. A correlation near 1 therefore means the two metrics are redundant for ranking models, not that the two are interchangeable as training losses.

<!-- END GENERATED results_summary -->

MAE and MSE correlate at 0.986 across every degradation, above the 0.95 redundancy
threshold, and MAE against NRMSE at 0.963 — they order the degradations almost identically
while differing by 47 times in sub-cell displacement damage. For ranking models the
cell-by-cell baselines are duplicates of one another; as training losses they are not.

One place MAE differs in kind rather than degree: it assigns the phase-scrambled fake
prediction a damage of 1.41 on vorticity, above the 1.0 an unrelated field scores. Reach
for MAE over MSE when small displacements are what you need to see, and when you do not
want the score dominated by the worst cell.

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence mae --results results/comparison_1790639359`, do not edit -->

**Displacement, density, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `mae` | 0.00328 | 0.00655 | 0.0131 | 0.0262 | 0.0521 | 0.103 |
| `mse` | 1.49e-05 | 5.97e-05 | 0.000238 | 0.000952 | 0.00379 | 0.015 |
| `rmse` | 0.00386 | 0.00772 | 0.0154 | 0.0309 | 0.0616 | 0.123 |
| `nrmse` | 0.00362 | 0.00723 | 0.0145 | 0.0289 | 0.0576 | 0.115 |

**Displacement, density, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `mae` | 0.0262 | 0.0521 | 0.103 | 0.205 | 0.401 |
| `mse` | 0.000952 | 0.00379 | 0.015 | 0.0584 | 0.211 |
| `rmse` | 0.0309 | 0.0616 | 0.123 | 0.242 | 0.46 |
| `nrmse` | 0.0289 | 0.0576 | 0.115 | 0.226 | 0.43 |

**Displacement, velocity, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `mae` | 0.00163 | 0.00325 | 0.0065 | 0.013 | 0.0257 | 0.05 |
| `mse` | 4.76e-06 | 1.91e-05 | 7.61e-05 | 0.000303 | 0.00118 | 0.00445 |
| `rmse` | 0.00218 | 0.00437 | 0.00873 | 0.0174 | 0.0344 | 0.0667 |
| `nrmse` | 0.00219 | 0.00437 | 0.00873 | 0.0174 | 0.0343 | 0.0667 |

**Displacement, velocity, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `mae` | 0.013 | 0.0257 | 0.05 | 0.0951 | 0.18 |
| `mse` | 0.000303 | 0.00118 | 0.00445 | 0.016 | 0.0541 |
| `rmse` | 0.0174 | 0.0344 | 0.0667 | 0.127 | 0.233 |
| `nrmse` | 0.0174 | 0.0343 | 0.0667 | 0.127 | 0.232 |

**Displacement, vorticity, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `mae` | 0.0225 | 0.045 | 0.0892 | 0.172 | 0.306 | 0.453 |
| `mse` | 0.000476 | 0.0019 | 0.00747 | 0.028 | 0.0889 | 0.187 |
| `rmse` | 0.0218 | 0.0436 | 0.0865 | 0.167 | 0.298 | 0.432 |
| `nrmse` | 0.0219 | 0.0437 | 0.0868 | 0.169 | 0.304 | 0.447 |

**Displacement, vorticity, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `mae` | 0.172 | 0.306 | 0.453 | 0.581 | 0.69 |
| `mse` | 0.028 | 0.0889 | 0.187 | 0.288 | 0.468 |
| `rmse` | 0.167 | 0.298 | 0.432 | 0.537 | 0.684 |
| `nrmse` | 0.169 | 0.304 | 0.447 | 0.555 | 0.702 |

Median damage over frames at every strength, this metric in the first row and the pointwise controls beneath it, all on the same 0-to-1 scale where 0 is the undegraded reference and 1 an unrelated field; a dash means no damage scale on that field. The rank correlations under *Compared with the other metrics* say whether two metrics put the strengths in the same order; this table says how much each one charges for the same strength, which decides whether two metrics are interchangeable as training losses.

<!-- END GENERATED results_damage_by_level -->

## References

\bibliography
