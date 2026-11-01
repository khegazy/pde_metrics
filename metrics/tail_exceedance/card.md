---
name: tail_exceedance
kind: metric
---

## Definition

Let $f$ be one channel of the reference and $g$ the same channel of the prediction, on a
periodic grid of $n$ cells, and $\mathbf{e}_j$ the unit step along spatial axis $j$. The
one-cell increment is the one `increment_flatness` defines,

$$
(\delta_j f)_{\mathbf{m}} = f_{\mathbf{m} + \mathbf{e}_j} - f_{\mathbf{m}} \tag{1}
$$

The reference's $n$ absolute increments along axis $j$, sorted from largest to smallest, are
$X_{(1)} \ge X_{(2)} \ge \dots \ge X_{(n)}$, and the threshold at order $k$ is the $k$-th
largest of them,

$$
a_j^{(c)}(k) = X_{(k)}, \qquad
k(\theta) = \min\bigl(\lceil n^{\theta} \rceil,\; n - 1\bigr), \qquad
\theta \in \{0.1, 0.2, \dots, 0.9\} \tag{2}
$$

the orders of `tail_index`, computed by the same function. The event is an increment at least
that large, and each field's count of events is

$$
N_j^{(c)}(h) = \#\bigl\{\mathbf{m} : \lvert (\delta_j h)_{\mathbf{m}} \rvert \ge a_j^{(c)}(k)\bigr\},
\qquad h \in \{f, g\} \tag{3}
$$

The reference has $k$ events per pair when its $k$-th and $(k+1)$-th largest differ, and more
when they tie. The value at each $\theta$ is the frequency bias of the event, the prediction's
count over the reference's, with the counts of every channel-and-axis pair in the set $A$ of pairs
whose threshold is positive summed first,

$$
B(\theta) = \frac{\sum_{(c,j) \in A} N_j^{(c)}(g)}{\sum_{(c,j) \in A} N_j^{(c)}(f)} \tag{4}
$$

The frequency bias is the verification score defined as "(hits + false alarms) / (hits +
misses)", forecast events over observed events, with perfect score 1, below 1 meaning the event is
under-forecast and above 1 over-forecast [@jwgfvr], section "Frequency bias (bias score)"; the
page numbers no equations. Here the reference stands in for the observation and the prediction for
the forecast. A threshold set by a percentile of a reference sample, against which another sample's
exceedances are counted, is the construction of the percentile-based climate-extremes indices,
such as TX90p, "the percentage of days when TX > 90th percentile" of a base period [@etccdi],
item 13. The reported value is $B(\tfrac{1}{2})$, at $k = \lceil \sqrt{n} \rceil$, the largest
$\sqrt{n}$ that Clauset, Shalizi and Newman [@clauset2009], Section 3.5, name as a fixed rule for
the tail and `tail_index` reads; on the 256 by 256 analysis grid that is $k = 256$ of $n = 65536$
increments per axis. It is NaN when $A$ is empty, as on a constant reference.

**Choices made here, not by a source.** That the quantity counted is the one-cell increment follows
`tail_index` and `increment_flatness`, whose precedent is the increment statistics Granero-Belinchón
and Cabeza Gallucci [@granero2024] use as physics criteria; both signs are pooled into one tail.
That the threshold is the reference's own order statistic, rather than a multiple of its
increment rms or of `ctx.fluctuation_rms`, is this bundle's choice (`judgements/005`): it fixes the
reference's event rate at $k/n$ on every field and frame, with no assumption about the shape of the
distribution. That $B(\tfrac{1}{2})$ is the number registered for the panel, rather than another
point of the curve or a summary of all of it, is a convention with no source (`issues/118`). The
counts are summed over pairs before the ratio, as a verification contingency table is summed over
cases, which, with no ties at the threshold, equals the mean over pairs of each pair's ratio,
since every pair's reference count is then $k$.

**Why the $k$-th largest and $\ge$.** A threshold estimated from the reference sample is exceeded
at a different rate inside that sample than outside it, the effect Zhang, Hegerl, Zwiers and
Kenyon [@zhang2005] describe for percentile indices. The derivation that follows is this bundle's.
For a continuous distribution $F$ and $n$ independent reference values, $F(X_{(k)})$ follows a
$\mathrm{Beta}(n-k+1, k)$ distribution, so a new value reaches $X_{(k)}$ with probability
$\mathbb{E}[1 - F(X_{(k)})] = k/(n+1)$, and an independent prediction with the reference's
distribution has an expected frequency bias of

$$
\mathbb{E}\,B = \frac{n}{k} \cdot \frac{k}{n+1} = \frac{n}{n+1} \tag{5}
$$

within $1/(n+1)$ of the target. With the $(k+1)$-th largest and a strict inequality the same
calculation gives $(k+1)/k$, which is 1.25 at the curve's first point on the 256 by 256 grid, where
$k = 4$. A test in `test_metric.py` checks Equation (5) on independent samples at $k = 2$.

**The curve behind the number** is Equation (4) at every $\theta$ of Equation (2). Small $\theta$
reads the few largest increments; large $\theta$ lowers the threshold into the body of the
distribution, where the count is no longer about extremes.

### Boundary handling

Periodic wrap on every axis: the increment of the last cell along an axis is taken against the
first, as in `increment_flatness`. A pair whose reference threshold is exactly zero, an axis along
which the reference is constant, is left out of both sums in Equation (4); that rule is
discontinuous, as `issues/103` records for `tail_index`. A field holding NaN or an infinity is
refused with an error rather than scored, because a NaN fails every comparison and would lower a
count silently. The metric declares `requires_periodic`, so the harness does not run it on a
dataset with a non-periodic axis, such as the Sod shock tube.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED performance -->

## Intuition

This metric asks whether a prediction has as many extreme jumps between neighbouring cells as the
reference has. It takes the reference's neighbour-to-neighbour differences, finds the size of the
largest few, as many as the square root of the number of cells, and calls any difference at least
that large an extreme event. It then counts the events in the prediction and divides by the count
in the reference. One means the prediction has the right number of extreme jumps; less than one
means too few, which is what smoothing does to sharp structures; more than one means too many,
which is what noise does. The threshold comes from the reference alone, so it is the same for every
prediction of that reference.

A worked example, four cells by four cells. The reference is a sawtooth down each column: the
values 0, 3, 2, 1, wrapping back to 0, so going down a column the field jumps up by 3 once and
steps down by 1 three times. In the first prediction two columns have their jump cut to 2; the
second prediction is the reference tripled.

```
reference        first prediction     second prediction
0 0 0 0          0 0 0 0              0 0 0 0
3 3 3 3          3 3 2 2              9 9 9 9
2 2 2 2          2 2 2 2              6 6 6 6
1 1 1 1          1 1 1 1              3 3 3 3

                 0.5                  4
```

Sixteen cells means the four largest steps set the threshold: the reference's four jumps of 3, so
an event is a step of at least 3, and the reference has four. The first prediction keeps two jumps
of 3, so it scores two over four, 0.5. The tripled prediction has steps of 9 and 3, all sixteen at
least 3, so it scores sixteen over four, 4. Along the rows the reference is constant, so that
direction has no extreme steps and is left out.

What it ignores: where the extreme jumps are, how large they are beyond the threshold, and
everything about the smaller jumps.

## Reading the output

Dimensionless, zero or positive, and unbounded above; at most $n/k$, 256 on the 256 by 256 grid.
The target is 1: the analysis orders the value by its distance from 1 on a logarithmic scale, so
0.5 and 2 are equally far from right. Below 1 the prediction has fewer increments as large as the
reference's extreme ones, above 1 more. The prediction that is the reference itself scores exactly
1, and an independent draw from the reference's distribution scores $n/(n+1)$ on average
(Equation (5)), with a spread across draws that grows as $k$ shrinks.

Because the threshold and the counts scale together, multiplying both fields by one constant
changes nothing, and a prediction can be compared with a reference of any magnitude. Values are
comparable across predictions of the same reference. Values at different analysis-grid
resolutions are not comparable: the increment is one cell long, and $k$ is set by the number of
cells.

The companion is the curve `tail_exceedance[theta]`: Equation (4) at $k = \lceil n^{\theta}
\rceil$ for $\theta$ from 0.1 to 0.9. Small $\theta$ is a rarer event, larger $\theta$ a commoner
one, and on 256 by 256 $\theta = 0.9$ counts about a third of all increments.

## Limitations

The value saturates. Once a prediction has no increment as large as the reference's $\sqrt{n}$-th
largest, it scores 0 however much further it is smoothed, and on the distance-from-1 scale that is
infinitely far: two predictions both at 0 cannot be ranked against each other, and a mild blur and
a total one are scored alike. Before the run, on nine frames of `kinet_re5e4`, the second strength
of either Gaussian or box blur already reached 0 on every field. The stored curve at larger
$\theta$ is where such predictions are still told apart.

A value above 1 does not mean the prediction is more intermittent or more turbulent. Anything that
puts more one-cell jumps above the reference's extreme level raises it: noise, and also a
blocky reconstruction whose block edges concentrate the change between blocks into single-cell
jumps. Below 1 does not mean smoother everywhere either, only fewer extreme jumps.

It is not monotone under smoothing in general, which the decorator declares and the contract test
checks. Spreading one tall, isolated jump over several cells can put each of them above a low
threshold, so blur can raise the count before it lowers it: a 16-cell spike of height 8 on faint
noise scores 1, 1.25, 2, 3, 3.5 and then 0 as the blur widens (`test_metric.py`).

The counts are piecewise constant in the prediction, so the metric has no useful gradient and is
not a training loss. A pair along which the reference is exactly constant is left out, but the same
pair with round-off variation is not and then sets a round-off threshold that almost any prediction
exceeds everywhere; the rule is discontinuous, as `issues/103` records for `tail_index`. Ties in
the reference at its threshold make the reference's count larger than $k$, which only matters for
fields with repeated increment values, such as a staircase.

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

No reading yet: the evidence run has not been made.

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_spectral -->

No reading yet: the evidence run has not been made.

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_geometric -->

No reading yet: the evidence run has not been made.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_resolution -->

No reading yet: the evidence run has not been made.

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_stochastic -->

No reading yet: the evidence run has not been made.

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_canaries -->

No reading yet: the evidence run has not been made.

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_summary -->

No reading yet: the evidence run has not been made.

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_damage_by_level -->

No reading yet: the evidence run has not been made.

### The curve behind the number

<!-- GENERATED results_companion: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_companion -->

No reading yet: the evidence run has not been made.

## References

\bibliography
