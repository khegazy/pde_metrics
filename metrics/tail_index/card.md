---
name: tail_index
kind: metric
---

## Definition

Let $f$ be one channel of a field on a periodic grid of $n$ cells and $\mathbf{e}_j$ the unit
step along spatial axis $j$. The one-cell increment is the one `increment_flatness` defines,

$$
(\delta_j f)_{\mathbf{m}} = f_{\mathbf{m} + \mathbf{e}_j} - f_{\mathbf{m}} \tag{1}
$$

and its $n$ absolute values, sorted from largest to smallest, are
$X_{(1)} \ge X_{(2)} \ge \dots \ge X_{(n)}$. The Hill estimator from the $k$ largest of them is

$$
H_j^{(c)}(k) = \frac{1}{k} \sum_{i=1}^{k} \ln \frac{X_{(i)}}{X_{(k+1)}} \tag{2}
$$

the form printed by Boucheron and Thomas [@boucheron2015], Section 1, of the estimator of Hill
[@hill1975]; the copy of the first that was read shows no number on the definition, and the
second was read only through its abstract, so neither is cited by equation. It is the mean
log-ratio of the $k$ largest values to the next one. When the tail is a power law,
$P(X > x) \propto x^{-\alpha}$, it estimates the extreme-value index $\gamma = 1/\alpha$:
Boucheron and Thomas state that $H(k)$ converges to $\gamma$ for every $k$ that grows with $n$
while $k/n$ shrinks, exactly when the tail lies in the domain of attraction with $\gamma > 0$.
It is equivalent to the power-law maximum-likelihood estimator of Clauset, Shalizi and Newman
[@clauset2009], Eq. (3.1). When the tail is not a power law, Equation (2) is still defined and
still scale-free, but it no longer estimates a tail index; it is then the mean log-excess of the
$k$ largest values over the next one, and depends on $k$.

The order $k$ is set on a logarithmic scale,

$$
k(\theta) = \min\bigl(\lceil n^{\theta} \rceil,\; n - 1\bigr), \qquad
\theta \in \{0.1, 0.2, \dots, 0.9\} \tag{3}
$$

the cap leaving an $X_{(k+1)}$ to divide by. The reported value is the mean of Equation (2) at
$\theta = 1/2$ over the set $A$ of channel-and-axis pairs whose $X_{(k+1)}$ is positive,

$$
T = \frac{1}{|A|} \sum_{(c, j) \in A} H_j^{(c)}\bigl(k(\tfrac{1}{2})\bigr) \tag{4}
$$

and is NaN when $A$ is empty, as on a constant field. $\theta = 1/2$ keeps the largest
$\sqrt{n}$ values, one of the two fixed rules Clauset, Shalizi and Newman [@clauset2009] name in
Section 3.5 as an alternative to choosing $k$ from the data. On the 256 by 256 analysis grid that
is $k = 256$ of $n = 65536$ increments per axis.

**Choices made here, not by a source.** Which of the fixed rules to register is this bundle's
choice: the largest $\sqrt{n}$ satisfies the condition under which Equation (2) is consistent,
$k$ growing while $k/n$ shrinks, and the other rule Section 3.5 names, the largest $n/10$, does
not. The rule is fixed once for every field and every variant rather than chosen from each
field's data, as the Kolmogorov-Smirnov method of Clauset, Shalizi and Newman [@clauset2009],
Section 3.3 and Eq. (3.9), would choose it, so that the reference and every variant are read at
the same order. The quantity whose tail is read is the absolute one-cell increment, because
increment statistics are the physics criteria Granero-Belinchón and Cabeza Gallucci
[@granero2024] train a generative turbulence model against; both signs of increment are pooled
into one tail. Equation (4) averages per-pair estimates rather than pooling every increment, the
rule `increment_flatness` gives for its Equation (3), so an anisotropic field is not read as a
mixture. The nine values of $\theta$ in Equation (3), a tenth apart, are this bundle's choice.

**The curve behind the number** is Equation (2), averaged as in Equation (4), at every $\theta$
of Equation (3): a Hill plot, as Section 3.5 of Clauset, Shalizi and Newman [@clauset2009] names
it, with $k$ on a logarithmic scale, the form Boucheron and Thomas [@boucheron2015] read $k$ off
in Section 2.3. It is stored on every row; the registered number is its value at
$\theta = 1/2$.

### Boundary handling

Periodic wrap on every axis: the increment of the last cell along an axis is taken against the
first, as in `increment_flatness`. A pair whose $(k+1)$-th largest absolute increment is zero
has no estimate at that $k$ and is left out of Equation (4) rather than given one. The metric
declares `requires_periodic`, so the harness does not run it on a dataset with a non-periodic
axis, such as the Sod shock tube.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED performance -->

## Intuition

This metric asks how far the very largest jumps between neighbouring cells stand out from the
slightly smaller ones. It collects the size of every difference between a cell and its
neighbour, keeps the biggest few, as many as the square root of the number of cells, and takes
the average of how many times larger each of them is than the next one down, measured on a
logarithmic scale. If the biggest jumps are all about the same size, the answer is near zero. If
a few jumps are many times larger than the rest of the biggest ones, the answer is large. For
values that follow a power law, where the chance of exceeding a size falls as one over that size
raised to some power, the answer is one over that power, so a heavier tail scores higher.

What it reveals is a change in how the largest local gradients are distributed: a prediction
that has smoothed away the rarest, sharpest events, or that has manufactured spurious ones.

A worked example, four cells by four cells. On the left, a sawtooth down each column: the values
0, 3, 2, 1, wrapping back to 0, so going down a column the field jumps up by 3 once and steps
down by 1 three times. On the right, rows alternate between 0 and 1, so every step has size 1.

```
sawtooth          alternating
0 0 0 0           0 0 0 0
3 3 3 3           1 1 1 1
2 2 2 2           0 0 0 0
1 1 1 1           1 1 1 1

1.0986            0
```

Sixteen cells means the four largest steps are kept. In the sawtooth those are the four jumps of
3, one per column, and the next largest step is 1, so each is 3 times the next one down and the
answer is the natural logarithm of 3, 1.0986. In the alternating field the four largest steps and
the next one are all 1, so the answer is 0. Along the rows both fields are constant, so that
direction has no steps at all and is left out.

What it ignores: everything about the field except the sizes of its largest neighbour-to-neighbour
steps, including where those steps are and the shape of the rest of the distribution.

## Reading the output

Dimensionless, zero or positive, and unbounded above. There is no direction in which the number
is better: what is read is the drift of a prediction's value from the reference field's own value,
in either direction. A value above the reference's means the prediction's largest increments are
more spread out relative to one another than the reference's are; a value below means they are
more uniform.

Because Equation (2) uses only ratios of increments, multiplying a field by a constant or adding
one to it changes nothing, so values can be compared across fields of different magnitude. For a
sample whose tail is a power law the value estimates one over the power; for any other tail it is
the mean log-ratio at the stated $k$ and is not a tail index, and a value from one field should
not be read as an exponent without first checking that a power law fits (Clauset, Shalizi and
Newman [@clauset2009], Sections 4 and 5).

Values at different analysis-grid resolutions are not comparable, for two reasons: the increment
is one cell long, so its physical length changes with the grid, and $k$ is set by the number of
cells, so the order read changes too.

The companion is the curve `tail_index[theta]`: Equation (4) at $k = \lceil n^{\theta} \rceil$ for
$\theta$ from 0.1 to 0.9. Small $\theta$ reads the few largest increments and is noisy; large
$\theta$ reaches into the bulk of the distribution and stops being a statement about its tail.

## Limitations

The estimator's guarantee is for a power-law tail, and a field whose increments are bounded or
fall off faster than any power has none to estimate. There the value at $k = \sqrt{n}$ measures
how the largest increments are spaced at that one order, and a change in it does not mean the
tail index changed. A reader who sees two values and reads off two exponents is misreading it.

The theory behind Equation (2) assumes independent samples, and the increments of a smooth field
are not: the largest increments of one frame tend to sit side by side across a few sharp
structures, so the largest few hundred are a handful of events counted many times. The value is
then a property of those few structures and can jump from frame to frame when one of them grows or
decays.

The number depends on $k$, and $\sqrt{n}$ is one rule among several. The stored curve shows how
the value moves with $k$; where the curve is steep, a different rule would give a different
number.

Its response to smoothing is not monotone, which the decorator declares and the contract test
checks: on that test's synthetic blur ladder the value rises and then falls. Ranking two
predictions by closeness to the reference's value can therefore put a more heavily smoothed
field ahead of a less smoothed one.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED run -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_smoothing -->


### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md)

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


### The curve behind the number

<!-- GENERATED results_companion: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_companion -->


## References

\bibliography
