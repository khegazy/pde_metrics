---
name: energy_distance
kind: metric
---

## Definition

Let $f$ be one channel of a field on a periodic grid of $N$ cells, $\mathbf{e}_j$ the unit
step along spatial axis $j$, and take the increment at a separation of one cell,

$$
(\delta_j f)_{\mathbf{n}} = f_{\mathbf{n} + \mathbf{e}_j} - f_{\mathbf{n}} \tag{1}
$$

the definition `increment_flatness` and `increment_w1` use, imported rather than restated.
For two real random variables $X \sim F$ and $Y \sim G$ with independent copies $X'$ and
$Y'$, the squared energy distance is

$$
D^2(F, G) = 2\,\mathbb{E}|X - Y| - \mathbb{E}|X - X'| - \mathbb{E}|Y - Y'| \tag{2}
$$

([@szekely2013], Definition 1, Eq. (2.4), where this squared form is itself called the energy
distance), and the energy distance is its square root $D(F, G)$, the form that satisfies the
axioms of a metric on distributions ([@rizzo2016], p. 27). On the line Equation (2) is twice
the integrated squared gap between the two cumulative distribution functions ([@szekely2013],
the display immediately before Eq. (2.3)),

$$
D^2(F, G) = 2 \int_{-\infty}^{\infty} \bigl( F(x) - G(x) \bigr)^2 \, dx \tag{3}
$$

Collecting Equation (1) over all $N$ cells gives an empirical distribution with $N$ equally
weighted atoms, $F^{(c,j)}_N$ for the reference and $G^{(c,j)}_N$ for the candidate. The
distance along axis $j$ of channel $c$ is Equation (3) between those two empirical
distributions,

$$
D^{(c, j)} = \Bigl( 2 \int_{-\infty}^{\infty} \bigl( F^{(c,j)}_N(x) - G^{(c,j)}_N(x) \bigr)^2 \, dx \Bigr)^{1/2} \tag{4}
$$

which equals the square root of the two-sample V-statistic of [@szekely2013], Eq. (6.1),
the average of Equation (2)'s distances over all pairs including a sample with itself. The
V-statistic is used rather than the unbiased U-statistic because it is never negative
([@szekely2013], Sect. 1) and is zero for identical samples, where the U-statistic is
negative; the increments of one frame are, besides, the whole population compared, not a
random sample of it. Both empirical cumulative functions are step functions, so Equation (4)
is exact: it is evaluated by one merge of the two sorted samples, by
`scipy.stats.energy_distance` [@scipyenergy]. The reported value averages Equation (4) over
every channel and spatial axis, as `increment_w1` averages its transport distances:

$$
D = \frac{1}{C \, d} \sum_{c=1}^{C} \sum_{j=1}^{d} D^{(c, j)} \tag{5}
$$

**Where it sits among distances between distributions.** Both the energy distance and the
1-Wasserstein distance of `increment_w1` belong to the *integral probability metrics*, the
largest difference in expectation over a class of test functions [@muller1997]. The energy
distance is, up to a factor, the maximum mean discrepancy [@gretton2012] (Definition 2,
Eq. (1)) for one particular kernel: the squared form of Equation (2) equals twice the
squared maximum mean discrepancy for any kernel that generates the distance $|x - y|$
([@sejdinovic2013], Theorem 22), such as $k(x, y) = \tfrac{1}{2}(|x| + |y| - |x - y|)$
([@sejdinovic2013], Eq. (4.2)). Equation (4) is therefore $\sqrt{2}$ times the biased
estimate of [@gretton2012], Eq. (5), with that kernel. The kernel has no bandwidth to choose.
Its only parameter is the exponent on $|x - y|$, which may lie anywhere in $(0, 2)$
([@szekely2013], Proposition 2, Eq. (5.1)) and is fixed at 1, the value of Definition 1.

**How it differs from the transport distance on the same samples.** On the line the
1-Wasserstein distance is the integral of the *absolute* gap $|F - G|$, where Equation (3)
integrates its *square*. A rare increment far out in a tail moves the cumulative functions by
only $1/N$ per atom, and squaring shrinks that further. The following derivation is mine,
not a source's, and `test_metric.py` pins it. Moving two of $N$ atoms outward by $h$, one in
each tail, costs $2h/N$ in transport distance and $4h/N^2$ in Equation (3), a ratio of $2/N$
whatever the size of $h$. For a change spread over all atoms the ratio is instead set by the
size of the change against the spread of the distribution; in the test's example, a
two-valued reference whose every increment grows by one unit, it is 1. So at equal transport
cost that test charges the change confined to two extreme increments $2/N = 1/8$ as much in
Equation (3) as the change spread over all sixteen. This is the sense in which the energy
distance averages, and is the property it is registered beside `increment_w1` to expose.

### Boundary handling

Periodic wrap on every axis: the increment of the last cell along an axis is taken against
the first, so every cell contributes exactly one increment per axis and both samples in
Equation (4) have $N$ atoms. It therefore declares `requires_periodic`, and the harness does
not run it on a dataset with a non-periodic axis, such as the Sod shock tube.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED performance -->

## Intuition

This metric compares two fields by the statistics of how much they change from one cell to
the next, and by nothing else. It collects every neighbour-to-neighbour difference of the
reference into one pile and does the same for the prediction. It then compares the two piles
through average distances: how far apart a value from one pile and a value from the other
typically are, against how far apart two values from the same pile typically are. When the
piles have the same make-up these averages balance and the result is zero; the more the piles
differ, the more the cross distances exceed the within-pile ones.

An equivalent reading makes its character plain. Line each pile up into a running tally of
the fraction of values below each level. The metric squares the gap between the two tallies,
adds it up over all levels, and takes a square root at the end. Squaring is what sets it apart
from a transport distance on the same piles, which adds up the gap itself. A handful of
extreme values in one pile shift its tally by only a sliver, and the square of a sliver is
smaller still, so a difference confined to the rare extremes counts for little here while a
broad change in the typical size of the differences counts in full.

A worked example, four cells by four cells. On the left the reference: the top row is zero and
the rest is one, so reading down any column there is a single step. On the right the
prediction: the value alternates every row, so reading down a column there is a step at every
position.

```
reference        candidate        energy_distance
0 0 0 0          0 0 0 0
1 1 1 1          1 1 1 1              0.25
1 1 1 1          0 0 0 0
1 1 1 1          1 1 1 1
```

Reading down the columns, the reference's changes are one step up, two flat and one step down
where the grid wraps, while the prediction's are up, down, up, down. The prediction has twice
as many steps of each sign and no flat stretches, which puts the two tallies a quarter apart
over two unit-wide ranges; squaring, summing and doubling gives one quarter, whose square root
is one half. Reading across the rows both fields are flat and that direction costs nothing.
The reported number averages the two directions, one quarter.

What it ignores: position, entirely, and a constant added everywhere. Of what it does see, it
largely ignores differences confined to a few extreme values.

## Reading the output

Zero and unbounded above, in the square root of the field's own units, because each distance
inside it is averaged and then square-rooted. Lower is better, and zero means the increment
statistics match, not that the fields match. Multiplying both fields by a constant multiplies
the value by the square root of its size.

The units make three comparisons invalid. Raw values cannot be compared across fields: on
this data density fluctuates by parts in ten thousand while vorticity is of order one. They
cannot be compared with `increment_w1`, which is in the field's own units, so only the
normalised damage columns of an evaluation put the two side by side. And because some
implementations, and [@szekely2013] itself, report the squared form of Equation (2) under
the same name, a value from another code must be checked for which of the two it is; the
rank correlations do not depend on that choice, but the damage and elasticity do, by a
factor of two in the elasticity.

Comparison across analysis-grid resolutions is invalid for the same reason as for
`increment_w1`: the separation in Equation (1) is one cell, so a finer grid compares
increments at a physically smaller separation.

The value is a distance between two fixed sets of increments, not a test statistic. The
increments of one field are neither independent nor a random sample, so the null
distributions and permutation tests built on Equation (4) in [@szekely2013] do not apply.

The metric has no companion. The object behind the number is the gap between the two
cumulative distribution functions, plotted against the increment value; its coordinate is in
the field's units and moves from frame to frame, so it is not a curve at fixed coordinates
and needs a companion kind the harness does not have.

## Limitations

The blind spot to position is total. A prediction with every structure in the wrong place, or
a spatially scrambled rearrangement of the truth, is at distance zero, and so is one offset by
a constant. A panel holding this metric and no pointwise control would score a badly wrong
field perfectly.

It is weak exactly where intermittency lives. A prediction that has lost the rare, extreme
increments of the reference, the intense thin structures, and kept the bulk of the
distribution right, is charged a factor of order $1/N$ less here than by `increment_w1` for
the same transport cost (the derivation under Definition). On a 256 by 256 grid that factor
is a few parts in a hundred thousand. Read a small value as "the typical increments match",
never as "the tails match".

Within one axis, a prediction too smooth in one region and too noisy in another can produce
an increment distribution close to the reference's while matching it nowhere locally; the
single number cannot tell that apart from a faithful prediction.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED run -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_smoothing -->

No measurements yet.

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_spectral -->

No measurements yet.

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_geometric -->

No measurements yet.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_resolution -->

No measurements yet.

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_stochastic -->

No measurements yet.

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_canaries -->

No measurements yet.

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_summary -->

No measurements yet.

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_damage_by_level -->

No measurements yet.

## References

\bibliography
