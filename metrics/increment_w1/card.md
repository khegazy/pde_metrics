---
name: increment_w1
kind: metric
---

## Definition

Let $f$ be one channel of a field on a periodic grid, $\mathbf{e}_j$ the unit step along
spatial axis $j$, and take the increment at a separation of one cell,

$$
(\delta_j f)_{\mathbf{n}} = f_{\mathbf{n} + \mathbf{e}_j} - f_{\mathbf{n}} \tag{1}
$$

the same definition ``increment_flatness`` uses, imported rather than restated so the two
cannot drift apart. Collecting Equation (1) over all $N$ cells gives an empirical
distribution with $N$ equally weighted atoms. Writing $a_{(1)} \le \dots \le a_{(N)}$ for
the sorted increments of the reference and $b_{(1)} \le \dots \le b_{(N)}$ for those of the
candidate, the 1-Wasserstein distance between the two along axis $j$ is

$$
W_1^{(c, j)} = \frac{1}{N} \sum_{i=1}^{N} \bigl| a_{(i)} - b_{(i)} \bigr| \tag{2}
$$

and the reported value averages Equation (2) over every channel and spatial axis:

$$
W_1 = \frac{1}{C \, D} \sum_{c=1}^{C} \sum_{j=1}^{D} W_1^{(c, j)} \tag{3}
$$

Equation (2) is exact rather than an approximation, and the reason is worth stating because
it is what makes the metric cost a sort instead of a linear program. The transport cost
$|x - y|$ is convex, so by the rearrangement inequality the cheapest way to match two equally
weighted point sets on the line is the monotone one: pair the smallest with the smallest and
so on upward. For equal weights that pairing is exactly "sort both and subtract". The general
treatment is [@peyrecuturi2019], Chapter 2; no equation number is cited from it because the
copy that could be read did not show the numbering, and a plausible-looking one would be
worse than none.

Averaging in Equation (3) runs over per-axis distances rather than over one pooled sample of
increments. Pooling would compare a mixture against a mixture, where an error along one axis
can be cancelled by an opposite error along another; keeping the axes separate cannot hide
that. Unlike the flatness of the same increments, every pair is included even when its
increments vanish in both fields, because the transport distance between two identical
degenerate distributions is a well-defined zero rather than undefined.

Two exact invariances follow from Equation (1) and are properties of the metric rather than
accidents of the discretisation. Translating the field permutes its increments without
changing the multiset, so Equation (2) is unchanged and a translated prediction is at
distance zero. Adding a constant cancels in the difference, so a uniform bias is likewise
invisible.

### Boundary handling

Periodic wrap on every axis: the increment of the last cell along an axis is taken against
the first, so every cell contributes exactly one increment per axis and the two samples in
Equation (2) are guaranteed the same size, which is what the closed form requires.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence increment_w1 --results results/comparison_1790639359`, do not edit -->

| test family | field | degradations | rank correlation | weakest gap between neighbouring strengths | first strength detected |
|---|---|---|---|---|---|
| Displacement | density | 2 | -0.714 to -0.714 | 0 | level — |
| Displacement | velocity | 2 | -0.714 to -0.714 | 0 | level — |
| Displacement | vorticity | 2 | -0.6 to -0.6 | 0 | level — |
| Resolution loss | density | 2 | 1 to 1 | 0.719 | level — |
| Resolution loss | velocity | 2 | 1 to 1 | 0.774 | level — |
| Resolution loss | vorticity | 2 | 1 to 1 | 0.685 | level — |
| Smoothing | density | 3 | 1 to 1 | 0.96 | level — |
| Smoothing | velocity | 3 | 1 to 1 | 0.771 | level — |
| Smoothing | vorticity | 3 | 1 to 1 | 0.638 | level — |
| Spectral filtering | density | 4 | 1 to 1 | 0.829 | level — |
| Spectral filtering | velocity | 4 | 1 to 1 | 0.881 | level — |
| Spectral filtering | vorticity | 4 | 1 to 1 | 0.595 | level — |
| Noise | density | 1 | 1 to 1 | 1 | level — |
| Noise | velocity | 1 | 1 to 1 | 1 | level — |
| Noise | vorticity | 1 | 1 to 1 | 1 | level — |
| trap test: fake prediction, right spectrum | density | 1 | — | — | damage — |
| trap test: fake prediction, right spectrum | velocity | 1 | — | — | damage — |
| trap test: fake prediction, right spectrum | vorticity | 1 | — | — | damage — |

One row per family of degradation and physical field. **Rank correlation** asks whether the metric put the strengths of one degradation in the right order: it is the Spearman correlation between the metric and the applied strength, computed inside a single frame, and the column gives the range over the degradations in that family. A value of 1 means every strength was ordered correctly in every frame. **Weakest gap between neighbouring strengths** asks whether the metric can tell one strength from the next: it is the smallest Mann-Whitney overlap between any two neighbouring strengths, where 1 means the two never overlap and 0.5 means the metric cannot separate them at all. **First strength detected** is the mildest strength at which the metric has moved a tenth of the way from the undegraded reference toward a field with no relation to the truth; a dash means the metric never reached that tenth. **Damage** is that same 0-to-1 scale read as a number: 0 is the undegraded reference and 1 is an unrelated field.

This table reports what was measured and grades none of the measurements. What the numbers mean for this metric is written in the subsections below, beside the test that produced each number.

**Profile.**

| field | selectivity | charges most for | charges least for | response provably below 0.05 at 90% on | elasticity to a sub-pixel shift, against severity (distance) | compute cost (x cheapest in this run) |
|---|---|---|---|---|---|---|
| density | — | — | — | `box_blur` `coarsen` `coarsen_bandlimited` `gaussian_blur` `highpass_butterworth` `highpass_ideal` `lowpass_butterworth` `lowpass_ideal` `median_blur` `translate_subpixel` `translate_x` | 0.327 | 40.5 |
| velocity | — | — | — | `box_blur` `coarsen` `coarsen_bandlimited` `gaussian_blur` `highpass_butterworth` `highpass_ideal` `lowpass_butterworth` `lowpass_ideal` `median_blur` `translate_subpixel` `translate_x` | 0.3 | 80.2 |
| vorticity | — | — | — | `translate_subpixel` `translate_x` | 0.253 | 39.4 |

One row per physical field. **Selectivity** is how concentrated the metric's response is on a few degradations, measured per unit of field change: 0 means it charges every degradation the same, as mean squared error does by construction, and values toward 1 that one degradation carries most of it. **Charges most and least for** name the two ends of that profile. **Response provably below** lists degradations on which the upper confidence bound of the largest damage lies below the margin -- an equivalence test, so an entry says the response is provably small, not merely not significant; a dash means no degradation met the bound. **Elasticity** is the slope of log damage against log shift over the smallest shifts: 1 means damage grows in proportion to the shift, 2 with its square. **Compute cost** is wall-clock per evaluation over the cheapest metric and field in the same run.

<!-- END GENERATED performance -->

## Intuition

This metric compares two fields by the statistics of how much they change from one cell to
the next, and by nothing else. It collects every neighbour-to-neighbour difference in the
reference into one pile and does the same for the prediction, then asks how much work it
would take to reshape one pile into the other, where work means total distance moved. If the
prediction has the same mixture of gentle and steep changes as the reference, the two piles
coincide and the answer is zero, however differently those changes are arranged in space.

The reshaping cost has a shortcut that makes the whole thing cheap. Line both piles up in
increasing order, match the smallest with the smallest, the second smallest with the second
smallest, and so on, then average the gaps. That matching is provably the cheapest one when
the cost of moving is proportional to distance, so no search is needed and the metric is
really just two sorts.

What makes it useful is what it refuses to look at. A pointwise error norm is at its harshest
when a sharp feature is correct in every respect except its position, because it compares each
cell against the cell at the same index. This metric never asks where anything is, so that
error costs nothing. What it charges for instead is the prediction having the wrong *mix* of
steep and gentle transitions — too few steep ones, which is what over-smoothing does, or too
many, which is what a noisy prediction does.

A worked example, four cells by four cells. On the left the reference: the top row is zero and
the rest is one, so reading down any column there is a single step. On the right the
prediction: the value alternates every row, so reading down a column there is a step at every
position.

```
reference        candidate        increment_w1
0 0 0 0          0 0 0 0
1 1 1 1          1 1 1 1              0.25
1 1 1 1          0 0 0 0
1 1 1 1          1 1 1 1
```

Reading down the columns, the reference's changes are one step up, two flat, and one step
down where the grid wraps; the prediction's are up, down, up, down. Half the pairs match and
half differ by one, so that direction costs one half. Reading across the rows, both fields are
flat, both piles are all zeros, and that direction costs nothing. The reported number averages
the two directions.

What it ignores: position, entirely. Two fields whose changes have the same statistics but are
arranged into completely different structures are indistinguishable here, and so are two fields
differing only by a constant added everywhere.

## Reading the output

Zero and unbounded above, in the field's own units, so a value is meaningless until the field
is named. Lower is better, and zero means the increment statistics match rather than that the
fields match.

Because the value carries the field's units it cannot be compared across fields without
normalising — which is the opposite of the situation for ``increment_flatness``, a ratio that
is scale-free and comparable everywhere. The two are meant to be read together: flatness
summarises the increment distribution by one moment and has an absolute anchor at 3 but can be
matched for the wrong reason, while this compares the entire distribution and cannot be fooled
that way but has no anchor of its own.

Comparison across analysis-grid resolutions is invalid for the same reason it is for flatness:
the separation in Equation (1) is one cell, so a finer grid measures increments at a physically
smaller separation, and in turbulence the increment distribution depends on that separation.

## Limitations

The blind spot is total and is the point of the metric, which means it must never be read
alone. A prediction that has every structure in the wrong place, or that is a spatially
scrambled rearrangement of the truth, is at distance zero. So is one offset by a constant. A
panel containing this metric and no pointwise control would score a badly wrong field perfectly.

A subtler case is cancellation within one axis. Equation (2) compares sorted samples, so a
prediction that is too smooth in one region and too noisy in another can produce an increment
distribution close to the reference's while matching it nowhere locally. The single number
cannot distinguish that from a uniformly faithful prediction.

Finally the units make it easy to misread across fields. On this data density fluctuates by
parts in ten thousand while vorticity is of order one, so the raw values differ by orders of
magnitude for reasons that have nothing to do with prediction quality. Only the normalised
damage columns in the evaluation are comparable between fields.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence increment_w1 --results results/comparison_1790639359`, do not edit -->

Measured on `kinet_re5e4`, frames 2000 to 10000 (161 frames of developed flow), on the 256 analysis grid, seed 20260807, at commit `ce78cb2d30d8` (working tree dirty). Run `comparison_1790639359`.

Every number in this section comes from that one run. Regenerate with `python -m fmeval.cards evidence <name> --results results/comparison_1790639359`.

<!-- END GENERATED run -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence increment_w1 --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `box_blur` | density | 4 | 1 | 1 | 0.96 |
| `box_blur` | velocity | 4 | 1 | 1 | 0.809 |
| `box_blur` | vorticity | 4 | 1 | 1 | 0.638 |
| `gaussian_blur` | density | 4 | 1 | 1 | 0.967 |
| `gaussian_blur` | velocity | 4 | 1 | 1 | 0.889 |
| `gaussian_blur` | vorticity | 4 | 1 | 1 | 0.678 |
| `median_blur` | density | 3 | 1 | 1 | 0.978 |
| `median_blur` | velocity | 3 | 1 | 1 | 0.771 |
| `median_blur` | vorticity | 3 | 1 | 1 | 0.762 |

<!-- END GENERATED results_smoothing -->

All three kernels are ordered perfectly on all three fields, with the weakest separation on
vorticity. Smoothing narrows the increment distribution, which is a change of shape rather
than of position, so it is the kind of damage this metric is built to see.

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence increment_w1 --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `highpass_butterworth` | density | 4 | 1 | 1 | 0.832 |
| `highpass_butterworth` | velocity | 3 | 1 | 1 | 0.885 |
| `highpass_butterworth` | vorticity | 4 | 1 | 1 | 0.888 |
| `highpass_ideal` | density | 3 | 1 | 1 | 0.829 |
| `highpass_ideal` | velocity | 2 | 1 | 1 | 0.995 |
| `highpass_ideal` | vorticity | 4 | 1 | 1 | 0.801 |
| `lowpass_butterworth` | density | 4 | 1 | 1 | 0.86 |
| `lowpass_butterworth` | velocity | 3 | 1 | 0.919 | 0.939 |
| `lowpass_butterworth` | vorticity | 4 | 1 | 1 | 0.595 |
| `lowpass_ideal` | density | 3 | 1 | 1 | 0.958 |
| `lowpass_ideal` | velocity | 2 | 1 | 1 | 0.881 |
| `lowpass_ideal` | vorticity | 4 | 1 | 0.925 | 0.595 |

<!-- END GENERATED results_spectral -->

Ordered perfectly on all four filters and all three fields. Separability is weakest on
vorticity and strongest on velocity, but nowhere near the chance floor — unlike
`h_minus_one`, this metric does not lose resolution on the high-pass axis, because removing
low modes changes the increment distribution as readily as removing high ones does.

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence increment_w1 --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `translate_subpixel` | density | 6 | -0.714 | 0 | 0 |
| `translate_subpixel` | velocity | 6 | -0.714 | 0 | 0 |
| `translate_subpixel` | vorticity | 6 | -0.6 | 0 | 0 |
| `translate_x` | density | 5 | — | — | — |
| `translate_x` | velocity | 5 | — | — | — |
| `translate_x` | vorticity | 5 | — | — | — |

<!-- END GENERATED results_geometric -->

This is the axis the metric is invariant to, and the table records that rather than a
response. `translate_x` is an integer shift, which permutes the increments without changing
the multiset, so the value is identically zero at every strength and the rank correlation is
withheld as round-off. `translate_subpixel` interpolates and therefore does change the field
slightly; the small residual it produces is not ordered, giving a negative correlation and a
separability of 0.

The invariance is exact and intended. Its consequence is not confined to this family: the
unrelated-field anchor is itself built from a large translation, so this metric scores that
anchor at zero too and has **no damage scale on any axis**, which is why every `first
strength detected` column on this card reads as absent. That is a property of the protocol
meeting a position-blind metric, not a defect in either; it is written up with its numbers in
`issues/037-position-blind-metrics-have-no-damage-anchor.md`.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence increment_w1 --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `coarsen` | density | 4 | 1 | 1 | 0.828 |
| `coarsen` | velocity | 4 | 1 | 1 | 0.864 |
| `coarsen` | vorticity | 4 | 1 | 0.919 | 0.685 |
| `coarsen_bandlimited` | density | 4 | 1 | 1 | 0.719 |
| `coarsen_bandlimited` | velocity | 4 | 1 | 1 | 0.774 |
| `coarsen_bandlimited` | vorticity | 4 | 1 | 0.988 | 0.805 |

<!-- END GENERATED results_resolution -->

Ordered perfectly on all three fields under both coarsenings, but the values differ by one to
two orders of magnitude at small factors: at a factor of 2, 5.2e-5, 3.8e-4 and 1.3e-4 under
`coarsen` against 7.2e-7, 3.3e-6 and 1.3e-5 under `coarsen_bandlimited`, on density, velocity
and vorticity. The staircase turns most one-cell increments into exact zeros and the rest into
jumps, which moves the increment distribution far more than the lost resolution does. By a
factor of 16 the gap has closed on vorticity, 2.8e-4 against 2.4e-4, because the coarse grid
genuinely cannot hold vorticity's structure at that size.

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence increment_w1 --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `additive_noise` | density | 4 | 1 | 1 | 1 |
| `additive_noise` | velocity | 4 | 1 | 1 | 1 |
| `additive_noise` | vorticity | 4 | 1 | 1 | 1 |

<!-- END GENERATED results_stochastic -->

Ordered perfectly with no overlap at all between neighbouring strengths on any field — the
cleanest axis for this metric. Additive noise widens the increment distribution directly and
by a controlled amount, which is the most direct thing that can be done to the quantity this
metric measures.

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence increment_w1 --results results/comparison_1790639359`, do not edit -->

| field | damage assigned to the fake prediction | closest real degradation | value on an unrelated field |
|---|---|---|---|
| density | — | `` | 0 |
| velocity | — | `` | 0 |
| vorticity | — | `` | 0 |

The fake prediction here has exactly the reference field's amplitude spectrum and completely scrambled structure. Damage of 1 is what a field with no relation to the truth scores, so the damage column says how close to useless this metric considers that fake prediction: a low number means the metric was fooled. The third column translates the same number into an ordinary degradation whose damage the fake prediction matches, which is easier to picture.

<!-- END GENERATED results_canaries -->

Neither trap can be scored on the damage scale, for the reason given under Displacement:
the unrelated-field anchor is a translation and this metric is translation-invariant, so the
anchor sits at exactly zero and there is no span to normalise against.

The raw values still say something and are worth recording even though the table cannot. On
vorticity the impostor scores 0.000294 against exactly 0 for the anchor, so the metric does
detect that the phase-scrambled field has different increment statistics from the reference —
it is not blind to the impostor, it simply has no scale on which to express how far off it
is. Read this as the trap tests being *unavailable* for this metric rather than as it passing
or failing them.

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence increment_w1 --results results/comparison_1790639359`, do not edit -->

| compared with | rank correlation over every degradation |
|---|---|
| `spectrum_l2` | 0.749 |
| `h1_seminorm` | 0.225 |
| `nrmse` | 0.0858 |
| `rmse` | 0.0846 |
| `mse` | 0.0844 |
| `mae` | 0.0547 |
| `h_minus_one` | -0.0552 |
| `increment_flatness` | -0.489 |
| `enstrophy` | -0.495 |
| `kinetic_energy` | -0.552 |
| `palinstrophy` | -0.583 |

Computed on the median value at each combination of degradation and strength, over every degradation and physical field in the run, with the undegraded reference excluded. Two metrics correlating near 1 put the degradations in the same order, but the two may still weight those degradations very differently. A correlation near 1 therefore means the two metrics are redundant for ranking models, not that the two are interchangeable as training losses.

<!-- END GENERATED results_summary -->

Every axis except displacement is ranked perfectly on every field. Displacement is ranked
not at all, by construction.

The number worth the most here is the cross-metric correlation: 0.09, 0.08, 0.08 and 0.05
against `nrmse`, `rmse`, `mse` and `mae`. This metric is close to uncorrelated with the
entire pointwise family across the whole ladder, which is the strongest such result in the
repository — `h_minus_one`, by contrast, correlates with them above 0.91. That is the
property this metric was proposed for, and it is now measured rather than argued: a panel containing
this metric and a pointwise control is measuring two nearly independent things. It correlates
-0.49 with `increment_flatness`, which reads the same increment distribution through a single
moment, so the two are related but far from redundant.

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence increment_w1 --results results/comparison_1790639359`, do not edit -->

**Displacement, density, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `increment_w1` | — | — | — | — | — | — |
| `mae` | 0.00328 | 0.00655 | 0.0131 | 0.0262 | 0.0521 | 0.103 |
| `mse` | 1.49e-05 | 5.97e-05 | 0.000238 | 0.000952 | 0.00379 | 0.015 |
| `rmse` | 0.00386 | 0.00772 | 0.0154 | 0.0309 | 0.0616 | 0.123 |
| `nrmse` | 0.00362 | 0.00723 | 0.0145 | 0.0289 | 0.0576 | 0.115 |

**Displacement, density, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `increment_w1` | — | — | — | — | — |
| `mae` | 0.0262 | 0.0521 | 0.103 | 0.205 | 0.401 |
| `mse` | 0.000952 | 0.00379 | 0.015 | 0.0584 | 0.211 |
| `rmse` | 0.0309 | 0.0616 | 0.123 | 0.242 | 0.46 |
| `nrmse` | 0.0289 | 0.0576 | 0.115 | 0.226 | 0.43 |

**Displacement, velocity, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `increment_w1` | — | — | — | — | — | — |
| `mae` | 0.00163 | 0.00325 | 0.0065 | 0.013 | 0.0257 | 0.05 |
| `mse` | 4.76e-06 | 1.91e-05 | 7.61e-05 | 0.000303 | 0.00118 | 0.00445 |
| `rmse` | 0.00218 | 0.00437 | 0.00873 | 0.0174 | 0.0344 | 0.0667 |
| `nrmse` | 0.00219 | 0.00437 | 0.00873 | 0.0174 | 0.0343 | 0.0667 |

**Displacement, velocity, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `increment_w1` | — | — | — | — | — |
| `mae` | 0.013 | 0.0257 | 0.05 | 0.0951 | 0.18 |
| `mse` | 0.000303 | 0.00118 | 0.00445 | 0.016 | 0.0541 |
| `rmse` | 0.0174 | 0.0344 | 0.0667 | 0.127 | 0.233 |
| `nrmse` | 0.0174 | 0.0343 | 0.0667 | 0.127 | 0.232 |

**Displacement, vorticity, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `increment_w1` | — | — | — | — | — | — |
| `mae` | 0.0225 | 0.045 | 0.0892 | 0.172 | 0.306 | 0.453 |
| `mse` | 0.000476 | 0.0019 | 0.00747 | 0.028 | 0.0889 | 0.187 |
| `rmse` | 0.0218 | 0.0436 | 0.0865 | 0.167 | 0.298 | 0.432 |
| `nrmse` | 0.0219 | 0.0437 | 0.0868 | 0.169 | 0.304 | 0.447 |

**Displacement, vorticity, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `increment_w1` | — | — | — | — | — |
| `mae` | 0.172 | 0.306 | 0.453 | 0.581 | 0.69 |
| `mse` | 0.028 | 0.0889 | 0.187 | 0.288 | 0.468 |
| `rmse` | 0.167 | 0.298 | 0.432 | 0.537 | 0.684 |
| `nrmse` | 0.169 | 0.304 | 0.447 | 0.555 | 0.702 |

Median damage over frames at every strength, this metric in the first row and the pointwise controls beneath it, all on the same 0-to-1 scale where 0 is the undegraded reference and 1 an unrelated field; a dash means no damage scale on that field. The rank correlations under *Compared with the other metrics* say whether two metrics put the strengths in the same order; this table says how much each one charges for the same strength, which decides whether two metrics are interchangeable as training losses.

<!-- END GENERATED results_damage_by_level -->

## References

\bibliography
