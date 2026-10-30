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
is exact. `scipy.stats.energy_distance` [@scipyenergy] evaluates it: its documentation gives
the identity, and its source (`scipy.stats._stats_py._cdf_distance`) sorts the pooled
samples and evaluates both empirical cumulative functions between consecutive values by
binary search, so the cost is a few sorts of $2N$ values. The reported value averages Equation (4) over
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
not a source's, and `test_metric.py` pins both halves of it.

1. *A change confined to the tails.* Moving two of $N$ atoms outward by $h$, one in each
   tail, costs $W_1 = 2h/N$ in transport distance and $D^2 = 4h/N^2$ in Equation (3), so
   $D^2/W_1 = 2/N$ whatever the size of $h$.
2. *A broad change.* Stretching every increment by a factor $1 + \epsilon$ moves the
   cumulative function by about $\epsilon x f(x)$ at each value $x$, where $f$ is the
   density, so $D^2 \approx 2\epsilon^2 \int x^2 f(x)^2 \, dx$ while
   $W_1 = \epsilon\,\mathbb{E}|X|$. A broad change is suppressed too, by its own relative
   size: for a Gaussian $f$, $D^2/W_1 = \epsilon/(2\sqrt{2})$.
3. *At equal transport cost*, the tail change therefore costs
   $(2/N)/(\epsilon/(2\sqrt{2})) = 4\sqrt{2}/(N\epsilon)$ of the broad change in Equation (3),
   and the square root of that in the registered $D$.

On one axis of a 256 by 256 grid with a Gaussian bulk, a tail change of the same transport
cost as a 1% to 10% stretch of the whole distribution is charged about 9% to 3% of what the
stretch is charged in $D$ (about 0.9% to 0.09% in $D^2$). This is the sense in which the
energy distance averages, and is the property it is registered beside `increment_w1` to
expose. Two caveats: the ratio depends on the shape of the bulk, and it is a statement about
one (channel, axis) term; the registered mean over terms can mix terms of different sizes.

### Boundary handling

Periodic wrap on every axis: the increment of the last cell along an axis is taken against
the first, so every cell contributes exactly one increment per axis and both samples in
Equation (4) have $N$ atoms. It therefore declares `requires_periodic`, and the harness does
not run it on a dataset with a non-periodic axis, such as the Sod shock tube.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence energy_distance --results results/energy_distance_1793350409`, do not edit -->

![how the metric responded to each degradation, by field: rank correlation, separation of neighbouring strengths, damage per unit of field change, and the bound on its largest response](_generated/sensitivity_profile.svg)

Four measured statistics for energy_distance, one row per degradation grouped by family and one marker per field. From left: the rank correlation between the metric and the applied strength within a frame, with the line showing the resampling interval; the separation of neighbouring strengths as Cliff's delta, where 0 means the metric cannot tell one strength from the next and the faint ticks at 0.12, 0.28 and 0.42 are Vargha and Delaney's small, medium and large anchors, for scale and not as grades; the damage charged per unit of field change at the harshest strength; and the upper confidence bound on the largest damage, beside the fixed margin of 0.05. A hollow marker is a field and degradation on which that bound lies below the margin, so the response is provably small. A missing marker is a statistic the analysis withheld, as the rank correlation is on an axis the metric is invariant to.

![median damage against severity level, one panel per degradation family and field, on one shared scale](_generated/response_curves.svg)

Median damage over frames against severity level for energy_distance, one row per family of degradation and one column per field, on one shared scale. The solid grey line is damage 1, the anchor (by default the field's own mean); the dotted black line is the damage assigned to the fake prediction with the right spectrum, where the run included it. The hollow black ring marks the first level at which the metric has moved a tenth of the way to the anchor. Hollow grey markers are strengths excluded for repeating a milder one or for doing nothing. Degradations with three or fewer usable levels are drawn as markers only; points beyond 2 either side are drawn as triangles at the edge. Damage is negative where a degradation moves the metric away from the anchor, as noise raises a single-field quantity the field's mean sets to zero.

**Trend: does the response follow the degradation?**

| test family | field | degradations | rank correlation | fraction of frames in order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| Displacement | density | 2 | -0.714 | 0 | 0 |
| Displacement | velocity | 2 | -0.714 | 0 | 0 |
| Displacement | vorticity | 2 | -0.6 | 0 | 0 |
| Resolution loss | density | 2 | 1 | 0.988 to 1 | 0.618 to 0.827 |
| Resolution loss | velocity | 2 | 1 | 1 | 0.816 to 0.916 |
| Resolution loss | vorticity | 2 | 1 | 0.764 to 1 | 0.677 to 0.79 |
| Smoothing | density | 3 | 1 | 1 | 0.916 to 1 |
| Smoothing | velocity | 3 | 1 | 1 | 0.818 to 0.999 |
| Smoothing | vorticity | 3 | 1 | 1 | 0.704 to 0.78 |
| Spectral filtering | density | 4 | 1 | 0.932 to 1 | 0.793 to 0.995 |
| Spectral filtering | velocity | 4 | 1 | 0.839 to 1 | 0.823 to 1 |
| Spectral filtering | vorticity | 4 | 1 | 0.739 to 1 | 0.628 to 0.796 |
| Noise | density | 1 | 1 | 1 | 1 |
| Noise | velocity | 1 | 1 | 1 | 1 |
| Noise | vorticity | 1 | 1 | 1 | 0.939 |

**Reactivity: how far does it move?**

| test family | field | change from clean at the harshest strength | elasticity | first strength detected |
|---|---|---|---|---|
| Displacement | density | — | 0.313 | level — |
| Displacement | velocity | — | 0.304 | level — |
| Displacement | vorticity | — | 0.29 | level — |
| Resolution loss | density | — | 0.481 to 0.526 | level 1 |
| Resolution loss | velocity | — | 0.461 to 2.3 | level 1 |
| Resolution loss | vorticity | — | 0.433 to 1.57 | level 1 |
| Smoothing | density | — | 0.958 to 1.32 | level 3 |
| Smoothing | velocity | — | 0.558 to 0.577 | level 1 |
| Smoothing | vorticity | — | 0.485 to 0.732 | level 1 |
| Spectral filtering | density | — | 0.772 to 8.86 | level 1 |
| Spectral filtering | velocity | — | 0.611 to 1.07 | level 1 |
| Spectral filtering | vorticity | — | 0.492 to 3.2 | level 1 |
| Noise | density | — | 1.31 | level 2 |
| Noise | velocity | — | 1.17 | level 2 |
| Noise | vorticity | — | 1.38 | level 3 |
| trap test: fake prediction, right spectrum | density | — | — | damage 0.613 |
| trap test: fake prediction, right spectrum | velocity | — | — | damage 0.289 |
| trap test: fake prediction, right spectrum | vorticity | — | — | damage 0.871 |

**Consistency: how much does it vary from snapshot to snapshot?**

| test family | field | consistency, in the strength's units | snapshots per independent block |
|---|---|---|---|
| Displacement | density | 0.11 | 1 to 21 |
| Displacement | velocity | 0.166 | 1 to 20 |
| Displacement | vorticity | 0.271 | 1 to 21 |
| Resolution loss | density | 0.186 to 2.46 | 16 to 21 |
| Resolution loss | velocity | 0.468 to 0.973 | 21 to 22 |
| Resolution loss | vorticity | 1.87 to 2.91 | 21 to 22 |
| Smoothing | density | 0.00626 to 0.0204 | 18 to 20 |
| Smoothing | velocity | 0.00703 to 0.0158 | 21 |
| Smoothing | vorticity | 0.0273 to 0.0567 | 22 |
| Spectral filtering | density | 0.0124 to 0.0662 | 13 to 20 |
| Spectral filtering | velocity | 0.0274 to 0.0693 | 21 to 22 |
| Spectral filtering | vorticity | 0.0497 to 0.146 | 20 to 22 |
| Noise | density | 0.0009 | 19 |
| Noise | velocity | 0.00179 | 20 |
| Noise | vorticity | 0.0137 | 22 |

One row per family of degradation and physical field; a cell gives the range over the degradations in that family. **Trend.** The rank correlation is the Spearman correlation between the strength and how far the metric has moved from its value on the undegraded field of the same frame, in the one direction it moves under that degradation, computed inside a single frame. A value of 1 means every strength moved it further than the last in every frame, whichever way it moves; a response that scatters to both sides scores near 0. The fraction of frames in order counts the frames with no exception. The weakest gap is the smallest Mann-Whitney overlap between two neighbouring strengths across frames: 1 means they never overlap, 0.5 that they cannot be told apart. **Reactivity.** The change from clean is the median, at the harshest strength, of the departure from the undegraded value of the same frame over the size of that value: 0.3 means 30%. It does not exist for this metric, whose undegraded value is exactly zero; the damage below is its relative reading. The elasticity is the percentage change of that departure per percentage change in strength over the mildest strengths. First strength detected is the mildest at which the metric has moved a tenth of the way to the anchor; **damage** reads that 0-to-1 scale as a number. A dash means the measurement is not defined there. A metric's reactivity scales with the power it is expressed in: mean squared error's elasticity is twice root-mean-square error's, though the two carry the same information, so compare magnitudes across metrics with that in mind. **Consistency** is how much the response varies from snapshot to snapshot relative to its size, in the strength's units; the snapshots of one trajectory are correlated, and the last column is how many consecutive snapshots one independent block spans.

These tables report what was measured and grade none of the measurements. What the numbers mean for this metric is written in the subsections below, beside the test that produced each number.

**Profile.**

| field | selectivity | charges most for | charges least for | response provably below 0.05 at 90% on | elasticity to a sub-pixel shift, against severity (distance) | compute cost (x cheapest in this run) |
|---|---|---|---|---|---|---|
| density | 0.695 | `additive_noise` | `translate_x` | `coarsen_bandlimited` `translate_subpixel` `translate_x` | 0.313 | 1 |
| velocity | 0.633 | `coarsen_bandlimited` | `translate_x` | `translate_subpixel` `translate_x` | 0.304 | 1.99 |
| vorticity | 0.516 | `additive_noise` | `translate_x` | `translate_subpixel` `translate_x` | 0.29 | 1.07 |

One row per physical field. **Selectivity** is how concentrated the metric's response is on a few degradations, measured per unit of field change: 0 means it charges every degradation the same, as mean squared error does by construction, and values toward 1 that one degradation carries most of it. **Charges most and least for** name the two ends of that profile. **Response provably below** lists degradations on which the upper confidence bound of the largest damage lies below the margin -- an equivalence test, so an entry says the response is provably small, not merely not significant; a dash means no degradation met the bound. **Elasticity** is the slope of log damage against log shift over the smallest shifts: 1 means damage grows in proportion to the shift, 2 with its square. **Compute cost** is wall-clock per evaluation over the cheapest metric and field in the same run.

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
smaller still. A broad change in the typical size of the differences is squared too, but it
shifts the tally by a little everywhere rather than by a sliver in one place, so for the same
amount of moving it counts for far more than a difference confined to the rare extremes.

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
the same name, a value from another code must be checked for which of the two it is. For a
single (channel, axis) term the choice changes no ranking and exactly doubles the
elasticity; for the registered mean over several terms, the mean of square roots and the mean
of squares can in principle order two strengths differently, so neither statement is exact
there.

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
distribution right, is charged far less than a prediction whose whole increment distribution
is slightly too wide or too narrow, even when `increment_w1` charges the two the same: on one
axis of a 256 by 256 grid with a Gaussian bulk, a few percent to about a tenth as much (the
derivation under Definition). Read a small value as "the typical increments match",
never as "the tails match".

Within one axis, a prediction too smooth in one region and too noisy in another can produce
an increment distribution close to the reference's while matching it nowhere locally; the
single number cannot tell that apart from a faithful prediction.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence energy_distance --results results/energy_distance_1793350409`, do not edit -->

Measured on `kinet_re5e4`, frames 2000 to 10000 (161 frames of developed flow), on the 256 analysis grid, seed 20260807, at commit `4dbecc34d1da`. Run `energy_distance_1793350409`.

Every number in this section comes from that one run. Regenerate with `python -m fmeval.cards evidence <name> --results results/energy_distance_1793350409`.

<!-- END GENERATED run -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence energy_distance --results results/energy_distance_1793350409`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `box_blur` | density | 4 | 1 | 1 | 0.975 |
| `box_blur` | velocity | 4 | 1 | 1 | 0.97 |
| `box_blur` | vorticity | 4 | 1 | 1 | 0.704 |
| `gaussian_blur` | density | 4 | 1 | 1 | 1 |
| `gaussian_blur` | velocity | 4 | 1 | 1 | 0.999 |
| `gaussian_blur` | vorticity | 4 | 1 | 1 | 0.723 |
| `median_blur` | density | 3 | 1 | 1 | 0.916 |
| `median_blur` | velocity | 3 | 1 | 1 | 0.818 |
| `median_blur` | vorticity | 3 | 1 | 1 | 0.78 |

<!-- END GENERATED results_smoothing -->

All three kernels are ordered perfectly on all three fields, as pre-registered. Neighbouring
strengths separate least on vorticity (0.704 under `box_blur`), the field whose increments sit
at the smallest scales, where even the mildest calibrated width already moves most of them. In
damage the smoothing axes are mild on density: `median_blur` never reaches a tenth of the way
to the anchor there (the Reactivity table's "first strength detected" is level 3 for the
family on density and level 1 on the other two fields).

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence energy_distance --results results/energy_distance_1793350409`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `highpass_butterworth` | density | 4 | 1 | 0.932 | 0.793 |
| `highpass_butterworth` | velocity | 3 | 1 | 0.888 | 0.823 |
| `highpass_butterworth` | vorticity | 4 | 1 | 0.801 | 0.796 |
| `highpass_ideal` | density | 3 | 1 | 1 | 0.796 |
| `highpass_ideal` | velocity | 2 | 1 | 0.839 | 0.896 |
| `highpass_ideal` | vorticity | 4 | 1 | 0.739 | 0.632 |
| `lowpass_butterworth` | density | 4 | 1 | 1 | 0.882 |
| `lowpass_butterworth` | velocity | 3 | 1 | 1 | 0.941 |
| `lowpass_butterworth` | vorticity | 4 | 1 | 1 | 0.634 |
| `lowpass_ideal` | density | 3 | 1 | 1 | 0.995 |
| `lowpass_ideal` | velocity | 2 | 1 | 1 | 1 |
| `lowpass_ideal` | vorticity | 4 | 1 | 0.764 | 0.628 |

<!-- END GENERATED results_spectral -->

Both low-passes, which were pre-registered, and both high-passes, which were not, are ordered
with a rank correlation of 1 on every field. The high-passes are the less regular: some frames
fall out of order, down to a fraction of 0.739 under `highpass_ideal` on vorticity. Where a
row lists fewer than four strengths, the others resolved to a repeated or a do-nothing
severity on that field and were excluded, as the calibration of a sharp filter on these
spectra predicts (see the degradation pages).

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence energy_distance --results results/energy_distance_1793350409`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `translate_subpixel` | density | 6 | -0.714 | 0 | 0 |
| `translate_subpixel` | velocity | 6 | -0.714 | 0 | 0 |
| `translate_subpixel` | vorticity | 6 | -0.6 | 0 | 0 |
| `translate_x` | density | 5 | — | — | — |
| `translate_x` | velocity | 5 | — | — | — |
| `translate_x` | vorticity | 5 | — | — | — |

<!-- END GENERATED results_geometric -->

The metric is exactly blind to `translate_x`, as pre-registered: an integer shift permutes the
increments, every value is exactly zero and the rank correlation is withheld. The profile table
lists it among the degradations with a provably small response on every field. The sub-pixel
shift interpolates and so changes the increments slightly; that residual is not ordered with
the shift (rank correlation -0.714 on density and velocity, -0.6 on vorticity) and it is tiny,
at most 0.00745 in damage on vorticity, so it is also listed as provably small. Displacement
is the failure this metric does not see.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence energy_distance --results results/energy_distance_1793350409`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `coarsen` | density | 4 | 1 | 1 | 0.827 |
| `coarsen` | velocity | 4 | 1 | 1 | 0.816 |
| `coarsen` | vorticity | 4 | 1 | 1 | 0.677 |
| `coarsen_bandlimited` | density | 4 | 1 | 0.988 | 0.618 |
| `coarsen_bandlimited` | velocity | 4 | 1 | 1 | 0.916 |
| `coarsen_bandlimited` | vorticity | 4 | 1 | 0.764 | 0.79 |

<!-- END GENERATED results_resolution -->

Both coarsenings follow the factor with a rank correlation of 1 on every field, as
pre-registered, but they differ in size. The staircase reconstruction of `coarsen` turns most
one-cell increments into exact zeros, which moves the increment distribution almost as far as
the anchor does (its largest damage is 0.960 on density). The band-limited reconstruction
removes only the content above the coarse grid's resolution, and on density, whose fluctuation
sits in the largest scales, that leaves the increment distribution nearly intact: the largest
damage there is 0.0487, and the profile table lists `coarsen_bandlimited` on density among the
degradations with a provably small response, although its ordering is still perfect.

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence energy_distance --results results/energy_distance_1793350409`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `additive_noise` | density | 4 | 1 | 1 | 1 |
| `additive_noise` | velocity | 4 | 1 | 1 | 1 |
| `additive_noise` | vorticity | 4 | 1 | 1 | 0.939 |

<!-- END GENERATED results_stochastic -->

Ordered perfectly on every field, as pre-registered, with no overlap between neighbouring
strengths on density and velocity. Noise is the degradation this metric charges most for on
density and vorticity (the profile table), and at the harshest amplitude it goes far past the
anchor, to a largest damage of 6.37 on density. The anchor's distance is fixed by the
reference: its increments are a point mass at zero, whose distance from the reference's
increment distribution is set by that distribution alone. Noise of growing amplitude widens the
whole increment distribution without bound, so its distance is not capped by the anchor's.

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence energy_distance --results results/energy_distance_1793350409`, do not edit -->

| field | damage assigned to the fake prediction | closest real degradation | damage of the reference moved far away | value on the anchor |
|---|---|---|---|---|
| density | 0.613 | `coarsen=4` | 0 | 0.00727 |
| velocity | 0.289 | `highpass_ideal=2.14412` | 0 | 0.0194 |
| vorticity | 0.871 | `coarsen=16` | 0 | 0.01 |

The fake prediction here has exactly the reference field's amplitude spectrum and completely scrambled structure. Damage 1 is what the anchor scores, by default the reference's own spatial mean, a prediction that knows the mean and nothing else. The damage column therefore says how close to useless this metric considers that fake prediction: a low number means the metric was fooled. The third column translates the same number into an ordinary degradation whose damage the fake prediction matches, which is easier to picture. The fourth is the reference moved by a large random offset, the right statistics in the wrong place; where a field's energy sits in its largest scales that copy stays partly correlated with the reference, so it is not the score of an unrelated field.

<!-- END GENERATED results_canaries -->

The fake prediction with the right spectrum scores a median damage of 0.613 on density, 0.289
on velocity and 0.871 on vorticity. On velocity the metric is largely fooled: it charges the
phase-scrambled field about what it charges `highpass_ideal` at the level whose cutoff resolves
to wavenumber 2.14 on velocity. This run does not show why velocity scores lower than
vorticity. A difference in tail weight is not the explanation on the evidence available:
`increment_flatness`'s card reports nearly the same one-cell increment flatness for the
velocity and vorticity references, and the fake prediction keeps the reference's spectrum and
therefore the variance of its increments, so what this metric sees is a difference of shape
that flatness does not separate between those two fields. The reference moved far away scores
exactly 0 on every field, for the reason given under Displacement.

This run held only this metric, so the comparison with `increment_w1` on the same samples, the
point of building it, is not in these tables; it needs a run of both metrics together.

## References

\bibliography
