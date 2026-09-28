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

Equation (1) is normalised as a root *mean* square, deliberately matching
[h_minus_one](../../metrics/h_minus_one/card.md) rather than following an integral convention, and the
payoff is an exact identity. For an error carried by a single Fourier mode of wavenumber
magnitude $|\mathbf{k}|$,

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

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1789632054`, do not edit -->

| test family | field | degradations | rank correlation | weakest gap between neighbouring strengths | first strength detected |
|---|---|---|---|---|---|
| Displacement | density | 2 | 1 to 1 | 0.896 | level 2 |
| Displacement | velocity | 2 | 1 to 1 | 0.754 | level 1 |
| Displacement | vorticity | 2 | 0.7 to 1 | 0.501 | level 1 |
| Resolution loss | density | 1 | 1 to 1 | 0.924 | level 1 |
| Resolution loss | velocity | 1 | 1 to 1 | 0.991 | level 1 |
| Resolution loss | vorticity | 1 | 0.2 to 0.2 | 0.41 | level 1 |
| Smoothing | density | 3 | 1 to 1 | 0.945 | level 1 |
| Smoothing | velocity | 3 | 1 to 1 | 0.648 | level 1 |
| Smoothing | vorticity | 3 | 1 to 1 | 0.56 | level 1 |
| Spectral filtering | density | 4 | 1 to 1 | 0.762 | level 1 |
| Spectral filtering | velocity | 4 | 1 to 1 | 0.584 | level 1 |
| Spectral filtering | vorticity | 4 | 1 to 1 | 0.516 | level 1 |
| Noise | density | 1 | 1 to 1 | 1 | level 2 |
| Noise | velocity | 1 | 1 to 1 | 1 | level 2 |
| Noise | vorticity | 1 | 1 to 1 | 1 | level 3 |
| trap test: fake prediction, right spectrum | density | 1 | — | — | damage 0.996 |
| trap test: fake prediction, right spectrum | velocity | 1 | — | — | damage 0.938 |
| trap test: fake prediction, right spectrum | vorticity | 1 | — | — | damage 0.992 |

One row per family of degradation and physical field. **Rank correlation** asks whether the metric put the strengths of one degradation in the right order: it is the Spearman correlation between the metric and the applied strength, computed inside a single frame, and the column gives the range over the degradations in that family. A value of 1 means every strength was ordered correctly in every frame. **Weakest gap between neighbouring strengths** asks whether the metric can tell one strength from the next: it is the smallest Mann-Whitney overlap between any two neighbouring strengths, where 1 means the two never overlap and 0.5 means the metric cannot separate them at all. **First strength detected** is the mildest strength at which the metric has moved a tenth of the way from the undegraded reference toward a field with no relation to the truth; a dash means the metric never reached that tenth. **Damage** is that same 0-to-1 scale read as a number: 0 is the undegraded reference and 1 is an unrelated field.

This table reports what was measured and grades none of the measurements. What the numbers mean for this metric is written in the subsections below, beside the test that produced each number.

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
isotropy assumption: a strongly anisotropic spectrum can break it. `test_metric.py` checks
the ordering on a field varying in one direction, and Results records it on the real flow.
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

<!-- GENERATED run: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1789632054`, do not edit -->

Measured on `kinet_re5e4`, frames 2000 to 10000 (161 frames of developed flow), on the 256 analysis grid, seed 20260807, at commit `0104b46cf8d9` (working tree dirty). Run `comparison_1789632054`.

Every number in this section comes from that one run. Regenerate with `python -m fmeval.cards evidence <name> --results results/comparison_1789632054`.

<!-- END GENERATED run -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1789632054`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `box_blur` | density | 4 | 1 | 1 | 0.95 |
| `box_blur` | velocity | 4 | 1 | 1 | 0.651 |
| `box_blur` | vorticity | 4 | 1 | 1 | 0.56 |
| `gaussian_blur` | density | 4 | 1 | 1 | 0.945 |
| `gaussian_blur` | velocity | 4 | 1 | 1 | 0.692 |
| `gaussian_blur` | vorticity | 4 | 1 | 1 | 0.583 |
| `median_blur` | density | 3 | 1 | 1 | 0.953 |
| `median_blur` | velocity | 3 | 1 | 1 | 0.648 |
| `median_blur` | vorticity | 3 | 1 | 1 | 0.707 |

<!-- END GENERATED results_smoothing -->

Ordered correctly on every smoothing axis and field. Relative to its own unrelated-field
value, this metric departs from clean sooner than `rmse` does: at the mildest `gaussian_blur`
it has reached 0.08, 0.30 and 0.19 of that value on density, velocity and vorticity, against
0.02, 0.02 and 0.05 for `rmse`. Blur removes exactly the rapidly varying part of the field
that the gradient weights most.

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1789632054`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
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

The response splits by which end of the spectrum is removed. At the mildest `lowpass_ideal`
the metric stands at 0.43 to 0.55 of its unrelated-field value against 0.13 to 0.20 for
`rmse`. At the mildest `highpass_ideal` on vorticity, which removes 45% of the energy from
the lowest shells, it reads 0.05 against 0.43 for `rmse`: error at large scales has shallow
gradients and costs little here. This is the mirror image of `h_minus_one`, which is gentlest
on exactly the errors this metric charges most.

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1789632054`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `translate_subpixel` | density | 6 | 1 | 1 | 0.896 |
| `translate_subpixel` | velocity | 6 | 1 | 1 | 0.838 |
| `translate_subpixel` | vorticity | 6 | 1 | 1 | 0.625 |
| `translate_x` | density | 5 | 1 | 1 | 0.896 |
| `translate_x` | velocity | 5 | 1 | 1 | 0.754 |
| `translate_x` | vorticity | 5 | 0.7 | 0.186 | 0.501 |

<!-- END GENERATED results_geometric -->

The ordering is correct on five of the six rows, and the magnitude confirms Equation (3) on
the real flow. A one-cell `translate_x` costs this metric 0.09, 0.17 and 0.55 of its unrelated-field value on density,
velocity and vorticity, against 0.03, 0.02 and 0.17 for `rmse` and 0.03, 0.01 and 0.02 for
`h_minus_one`. On vorticity a two-cell shift already costs 0.91 and a four-cell shift is
indistinguishable from an unrelated field, which is why the vorticity `translate_x` row reads
0.7: the metric has saturated, and the remaining strengths differ only by frame-to-frame
scatter. This is the double penalty made worse, measured.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1789632054`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `coarsen` | density | 4 | 1 | 1 | 0.924 |
| `coarsen` | velocity | 4 | 1 | 1 | 0.991 |
| `coarsen` | vorticity | 4 | 0.2 | 0 | 0.41 |

<!-- END GENERATED results_resolution -->

Ordered correctly on density and velocity, but not on vorticity, where the rank correlation is
0.2 and no single frame is in the right order. The median value rises from factor 2 to 4 and
then falls at 8 and 16, while `mse` and `h_minus_one` rise throughout. The degradation expands
each block back to the fine grid as a constant, and on a field that varies as quickly as
vorticity the metric ends up measuring the jumps between blocks rather than the detail
coarsening removed. A test on synthetic fields, recorded in `issues/039`, shows the peak
moving to larger factors as the field gets smoother, which matches that account.

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1789632054`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `additive_noise` | density | 4 | 1 | 1 | 1 |
| `additive_noise` | velocity | 4 | 1 | 1 | 1 |
| `additive_noise` | vorticity | 4 | 1 | 1 | 1 |

<!-- END GENERATED results_stochastic -->

Ordered correctly with complete separation. Noise is where the weighting by wavenumber is
most extreme: at the strongest level the metric reads 17 to 19 times its unrelated-field value
on density and velocity, and 2.3 times on vorticity, where `rmse` reads 0.29 to 0.42. Uncorrelated
cell-to-cell noise is almost pure gradient.

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1789632054`, do not edit -->

| field | damage assigned to the fake prediction | closest real degradation | value on an unrelated field |
|---|---|---|---|
| density | 0.996 | `coarsen=2` | 0.000493 |
| velocity | 0.938 | `coarsen=2` | 0.00271 |
| vorticity | 0.992 | `translate_x=16` | 0.00136 |

The fake prediction here has exactly the reference field's amplitude spectrum and completely scrambled structure. Damage of 1 is what a field with no relation to the truth scores, so the damage column says how close to useless this metric considers that fake prediction: a low number means the metric was fooled. The third column translates the same number into an ordinary degradation whose damage the fake prediction matches, which is easier to picture.

<!-- END GENERATED results_canaries -->

The fake prediction scores close to an unrelated field, with damage between 0.94 and 1.0 on
all three fields, so this metric rejects it firmly. That is expected of a phase-sensitive
error metric and says nothing about the displacement problem.

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence h1_seminorm --results results/comparison_1789632054`, do not edit -->

| compared with | rank correlation over every degradation |
|---|---|
| `rmse` | 0.682 |
| `mse` | 0.682 |
| `mae` | 0.658 |
| `nrmse` | 0.628 |
| `h_minus_one` | 0.477 |
| `enstrophy` | 0.288 |
| `increment_w1` | 0.196 |
| `palinstrophy` | 0.119 |
| `increment_flatness` | -0.146 |
| `spectrum_l2` | -0.19 |

Computed on the median value at each combination of degradation and strength, over every degradation and physical field in the run, with the undegraded reference excluded. Two metrics correlating near 1 put the degradations in the same order, but the two may still weight those degradations very differently. A correlation near 1 therefore means the two metrics are redundant for ranking models, not that the two are interchangeable as training losses.

<!-- END GENERATED results_summary -->

This metric ranks the ladder most like the pointwise family, at 0.63 to 0.68 with `nrmse`,
`mae`, `mse` and `rmse`, and less like `h_minus_one`, at 0.48. The two Sobolev orders agree on
direction for most degradations and disagree on which ones are severe, which is the whole
content of Equation (2).

## References

\bibliography
