---
name: max_error
kind: metric
---

## Definition

For fields $f$ (reference) and $g$ (candidate) sampled on the same analysis grid, with $C$
channels and $N$ cells per channel, the maximum error is the discrete $L^\infty$ norm of their
difference, Equation 7 of [@roy2005]:

$$
\mathrm{MaxE}(f, g) = \max_{1 \le c \le C} \; \max_{1 \le i \le N} \bigl| f_{c,i} - g_{c,i} \bigr| \tag{1}
$$

PDEBench reports this "max error" for machine-learned surrogates beside RMSE and nRMSE, as the
local worst case and a proxy for the stability of time-stepping, in the table of metrics of
Section 3.3 of [@takamoto2022].

For a vector field the channels are pooled, so the maximum runs over every component of every
cell, as `mae` and `mse` pool channels into their means. That choice is this bundle's, not a
source's. PDEBench's code takes the maximum per channel and then averages over channels; the
two agree on every one-channel field and differ only on velocity. A maximum carries no cell
weights, so Equation (1) holds unchanged on a non-uniform grid.

The per-cell map stored beside the scalar is the absolute error, reduced over channels by its
largest value,

$$
m_i = \max_{1 \le c \le C} \bigl| f_{c,i} - g_{c,i} \bigr| \tag{2}
$$

and the declared reduction is `max`: the largest value of the map is Equation (1).

Two consequences follow directly from Equation (1). For a displacement $\delta$ small compared
with the scale of variation, expanding $g(x) = f(x + \delta) \simeq f(x) + \delta\, \partial_x f$
gives

$$
\mathrm{MaxE} \simeq \delta \max_{c,i} \bigl| \partial_x f_{c,i} \bigr| \tag{3}
$$

which is linear in the displacement, like the mean absolute error, but set by the steepest
gradient in the domain rather than the mean gradient. For a jump of height $h$ moved by one
cell or more, there is a cell on which one field sits on the high side of the jump and the
other on the low side, so $\mathrm{MaxE} = h$ whatever the size of the displacement.

On the damage scale the anchor is the reference's own spatial mean, taken channel by channel
(`judgements/001`), so damage 1 is the reference's largest departure from its mean,
$\max_{c,i} |f_{c,i} - \bar f_c|$.

### Boundary handling

None. The operation is local to each cell, so no neighbourhood is ever consulted and no
boundary condition can enter.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED performance -->

## Intuition

The maximum error compares two fields one cell at a time, takes the size of each difference
regardless of sign, and reports the largest. It answers the question of where the prediction
is worst, and how bad it is there. It reveals a local failure that an average hides: one
spurious spike, an overshoot next to a sharp front, or the first cell of an instability that
is starting to grow.

An average spreads each cell's error over the whole domain, so a single wrong cell among
many counts for very little. The maximum gives that cell all of the weight and every other
cell none. On a four-by-four grid, with a bright square, a copy moved by one cell, a copy at
half the brightness, and a copy with one extra bright cell in a corner:

```
reference      moved one cell   half brightness      one spike
0 0 0 0        0 0 0 0          0    0    0    0     1 0 0 0
0 1 1 0        0 0 1 1          0   0.5  0.5   0     0 1 1 0
0 1 1 0        0 0 1 1          0   0.5  0.5   0     0 1 1 0
0 0 0 0        0 0 0 0          0    0    0    0     0 0 0 0

               max error = 1    max error = 0.5      max error = 1
                                                     (mean absolute error = 0.0625)
```

The moved square and the single spike both score the full height of the square, because each
has at least one cell that is completely wrong. The mean absolute error charges the spike only
one sixteenth of that. Moving the square by two cells instead of one also scores 1: once a
sharp feature has left its own cells, the maximum cannot tell a small miss from a large one.

What this metric ignores is everything except the single worst cell: how many cells are
wrong, and by how much, below that one.

## Reading the output

The value runs from zero upwards with no upper limit, in the field's own units, so a density
field and a vorticity field produce numbers that cannot be compared with each other. Lower is
better, and zero means the two fields agree in every cell. The number is directly readable as
a bound: no cell is off by more than it.

What counts as good depends on how far the field itself strays from its mean, which is why
the suite reports damage, the value rescaled so that zero is the reference and one is what the
reference's own spatial mean scores. For this metric that anchor is the reference's largest
departure from its mean, so a damage of 0.1 says the worst cell is off by a tenth of the
field's largest excursion.

Comparisons across models on the same field, dataset and analysis grid are meaningful and are
the intended use. Comparisons across fields need normalising because of the units. Comparisons
across resolutions are invalid as they stand: a finer grid offers more cells to take the
maximum over, and a remap onto cell averages lowers peaks, so the same prediction scores
differently on different grids. Compare on a common analysis grid, which is what this suite
remaps onto before measuring.

The companion is a per-cell map, Equation (2): the absolute error at each cell, the largest
over channels. Its brightest cell is the metric. A single isolated bright cell is a local
excursion; a ridge along a front is a displaced sharp feature.

## Limitations

It suffers the double penalty in its most extreme form. A sharp front, a shock or a
shocklet, with the right shape and strength but sitting one cell from where it should be,
scores the full height of its jump, exactly as much as a prediction that has no front at all.
On a field with sharp features the maximum error therefore saturates at the height of the
largest jump as soon as anything is misplaced, and stops distinguishing a near miss from a
gross one (the second test in `test_metric.py`).

It rests on one cell, so it is noisy and depends on the grid. Two predictions that differ
only in where their noise happens to peak score differently. The largest of many independent
noise values tends to exceed the largest of a few, so on a finer grid the same noise level
scores higher with nothing else about the prediction changed.

Like every pointwise error, it is meaningful only while the prediction is still aligned with
the reference. Once a rollout has decorrelated from the truth, the maximum error measures the
size of the field's own excursions and carries no information about the model.

On velocity, pooling the channels means the number is the largest single-component error,
which depends on the orientation of the axes: the same error vector pointing along an axis or
along a diagonal scores differently, by up to the square root of two. And as a training loss
its gradient reaches only the one cell that attains the maximum.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED run -->

Each subsection links to the degradations that subsection reports. What those degradations
do, and what their strength numbers mean, is documented on their own pages.

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_smoothing -->

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_geometric -->

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_resolution -->

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_canaries -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_summary -->

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_damage_by_level -->

## References

\bibliography
