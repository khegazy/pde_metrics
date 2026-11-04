---
name: rank_histogram_chi2
kind: metric
---

## Definition

At every channel and cell the rank of the reference among the $M$ ensemble members is the
number of members below it, an integer from $0$ to $M$, with ties broken at random; the
histogram of those ranks over the frame is the companion of
[rank_histogram](../../metrics/rank_histogram/card.md), which defines it. With $n_k$ the number of draws
at rank $k$, $K = M + 1$ bins and $n$ draws in all, one per channel and cell, the reported
value is Pearson's chi-square statistic against the flat histogram [@jolliffeprimo2008]:

$$
T = \sum_{k=1}^{K} \frac{(n_k - e)^2}{e}, \qquad e = \frac{n}{K} \tag{1}
$$

which is Jolliffe and Primo's Equation (1), their $e_i = n p_0$ with $p_0 = 1/K$. In terms of
the fractions $f_k = n_k / n$ that the histogram companion stores,

$$
T = n K \sum_{k=1}^{K} \Bigl( f_k - \frac{1}{K} \Bigr)^2 \tag{2}
$$

which is how it is computed. It is zero for a flat histogram and at most $n(K - 1) = nM$, when
every draw lands in one bin.

If the draws are independent and the reference is exchangeable with the members, $T$ is
approximately chi-square distributed with $K - 1 = M$ degrees of freedom, so its expectation is
$M$ whatever the number of draws (Jolliffe and Primo, Section 2) [@jolliffeprimo2008]. At a
fixed histogram shape away from flat, Equation (2) grows in proportion to $n$: the statistic
measures how surely the histogram departs from flat, not how far. The
reliability index of `rank_histogram`, $\sum_k |f_k - 1/K|$, is the size of the departure,
independent of $n$. The two are reported side by side because the field reports both.

No p-value is computed. The chi-square distribution of $T$ assumes independent draws, and the
cells of a field are not independent: neighbouring cells of a flow are strongly correlated, so
the effective number of draws is far smaller than $n$, and a p-value computed from $n$ would be
far too small. On `synthetic_ensemble` the noise is drawn independently at every cell, so there
the draws are independent and $M$ is the null expectation; on any physical field it is not.

### Boundary handling

None in space: each rank uses only that cell's values across the ensemble, and the histogram
pools every cell without regard to position.

### How its field reports it

The field is ensemble forecast verification in meteorology.

- **The object.** Pearson's chi-square statistic of the rank counts against uniform, with
  $K - 1$ degrees of freedom (Jolliffe and Primo, Section 2, Equation (1)) [@jolliffeprimo2008].
  Anderson applies "the traditional chi-square test" to his binned ranks (Section 2c)
  [@anderson1996], and Hamill names it as the test of uniformity (Section 4) [@hamill2001].
- **The statistics reported beside it.** The test's significance: Anderson plots the
  significance of chi-square against forecast lead time (Figures 1 to 4) and maps it by grid
  point (Figures 5, 6, 9 and 10), and stresses that "the chi-square test is measuring the
  statistical significance of the difference between the distributions, not the strength of the
  difference" and that it is "sensitive to the number of samples" [@anderson1996]. Jolliffe and
  Primo decompose $T$ into one-degree-of-freedom components for a slope (Linear) and for a U or
  dome shape (Ends, or V-shape), plus a residual, by orthogonal contrasts (Section 2, Appendix
  Table A1), and report each with its p-value (Tables 1 and 2) [@jolliffeprimo2008]. That
  decomposition is not built here: Jolliffe and Primo present it as "a valuable additional tool"
  (Section 4) without claiming it is routinely reported, they offer two alternative shape
  contrasts that are not orthogonal to each other and say the decomposition "should be decided
  before looking at the rank histogram" (Section 4), and every component's p-value rests on the
  same independence assumption as $T$'s.
- **Independence, which the field insists on.** Hamill: "If samples used to populate the rank
  histogram are independent, then a $\chi^2$ hypothesis test ... may be performed ... However,
  the statistical hypothesis test may produce misleading results if samples have correlated
  errors, as may happen if two adjacent grid points are both used as samples" (Section 4); his
  Figures 7 and 8 measure the correlation of ranks between grid points and conclude that
  "samples must often be located far apart in space and in time" [@hamill2001]. Jolliffe and
  Primo, on a real ensemble: "the observations should be independent. Clearly they are not
  here", and they shrink 290 304 draws to about 420 effective ones before testing (Section 3b)
  [@jolliffeprimo2008]. This bundle does neither; it reports $T$ on all $n$ draws, as a
  statistic, and states the assumption instead.
- **The figure.** The rank histogram itself, bars of relative frequency against rank (Hamill,
  Figure 1; Jolliffe and Primo, Figures 1 and 2), is drawn on the `rank_histogram` card from its
  companion; this bundle stores no curve of its own.
- **The experiment.** Many forecasts of one variable at grid points over a season, at each lead
  time (Anderson, Figures 1 to 4), and synthetic ensembles of known miscalibration, including flat
  histograms from unreliable ensembles (Hamill, Section 3, Figures 2 to 4). Here only the
  calibrated null of `synthetic_ensemble` exists, with its miscalibration ladder; real
  ensembles wait on
  [issue 004](https://github.com/khegazy/pde_metrics/blob/main/issues/004-independent-realizations.md).
  The missing experiments are
  [EXP-spread_skill-heteroscedastic-synthetic-ensemble](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-spread_skill-heteroscedastic-synthetic-ensemble.md)
  (Hamill's flat-but-unreliable mixture),
  [EXP-crps-gneiting-forecaster-suite](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-crps-gneiting-forecaster-suite.md)
  and
  [EXP-spread_skill-perturbed-initial-condition-ensemble](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-spread_skill-perturbed-initial-condition-ensemble.md)
  (forecasts against lead time).

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED performance -->

## Intuition

Line the ensemble members up in order at each point and note where the truth falls among them;
count how often it falls in each slot. An honest ensemble gives equal counts. This number adds
up, slot by slot, the squared gap between the count seen and the count expected, each divided by
the count expected. It is the classical statistic for asking whether counts in categories could
have come from equal chances.

What distinguishes it from a plain measure of how uneven the counts are is that it grows with
the number of counts. The same uneven shape seen over a hundred times as many points gives a
statistic a hundred times larger, because the evidence that the shape is real is a hundred times
stronger. With independent points and an honest ensemble its typical value is the number of
slots minus one, whatever the number of points.

A worked example with two members, so three slots, at six points against a reference of 0:

```
reference        member 1               member 2               result
0 at all six     1  1  1 -1 -1 -1       2  2  2  1 -2 -2       1.0
```

The truth is below both members at the first three points, between them at the fourth, and above
both at the last two: counts of 3, 1 and 2 against an expected 2 each. The statistic is
(1 + 1 + 0) / 2 = 1.0.

It ignores the shape of the unevenness: a slope, a U and a dome with the same squared gaps give
the same number.

## Reading the output

The value is dimensionless, from zero up to the number of draws times the number of members;
lower is better and there is no target. With independent draws from an honest ensemble its
expectation is the number of members, so a value near that is consistent with calibration and a
value many times larger is not.

Because it grows with the number of draws, it compares two ensembles only on the same grid and
the same field: on a finer grid the same miscalibration reads larger. Across ensemble sizes the
null expectation changes with the number of bins. For a size that does not grow with the sample,
read the reliability index of `rank_histogram`.

On a physical field the independence behind the null expectation fails, so a value above the
number of members is not, by itself, evidence of miscalibration: correlated neighbouring cells
inflate it. On `synthetic_ensemble`, whose cells are independent, the comparison holds.

## Limitations

On any grid of thousands of cells, every real miscalibration is overwhelming in this statistic:
Jolliffe and Primo report a value "over 33 000" on a real ensemble, where every departure is
extremely significant [@jolliffeprimo2008]. Read as a test, it then says only that the
ensemble is not perfect, which was known.

It cannot say which way the ensemble is wrong. Jolliffe and Primo's own example has four
histograms of different shapes with the same statistic, 19.467, which only their decomposition
tells apart (Figure 1) [@jolliffeprimo2008]. A U-shaped histogram means the ensemble is
too narrow and a dome that it is too wide, opposite remedies the number does not separate;
`spread_skill`'s side of one does.

Like the reliability index, it pools every cell, so an ensemble overconfident in one region
and overdispersed in another can give a flat histogram and a small statistic; Hamill shows that
a flat histogram does not imply a reliable ensemble (Section 3a) [@hamill2001].

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED run -->

<!-- GENERATED experiments: written by `python -m fmeval.cards catalog`, do not edit -->

**Across the experiments.**

| experiment | what a run on it is evidence of | on this card |
|---|---|---|
| `kinet_re5e4` | developed flow | not applicable: needs an ensemble, and this dataset has one realisation per frame |
| `kinet_re1e6` | developed flow at Re = 1e6, twenty times the Reynolds number of kinet_re5e4, from the same initial condition | not applicable: needs an ensemble, and this dataset has one realisation per frame |
| `synthetic_ensemble` | a calibrated null: evidence that the estimator computes what it claims to compute, and nothing about turbulence | not yet run |
| `sod_shock_tube` | an analytic check: evidence that the metric locates and scores a known shock correctly, and nothing about turbulence | not applicable: needs an ensemble, and this dataset has one realisation per frame |
| `forecast_re5e4` | real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded | not applicable: needs an ensemble, and this dataset has one realisation per frame |

One row per dataset a card may cite (`configs/cards/default.yaml`). *Measured* names the run the card cites: the main results are `## Performance` and the subsections below, and every other run has its own subsection headed with its dataset. *Not applicable* gives the reason: one that follows from what the metric declares and what the dataset offers, or one a person wrote on the card (`not_run` in `card.yaml`) because the result would carry no information. *Not yet run* means the metric can run there and the card cites no run on it yet.

<!-- END GENERATED experiments -->

The statistic scores an ensemble, so the synthetic ensemble is the one experiment in this
repository it can run on; the experiments its field relies on are listed in the Definition.

### Ensemble dispersion

[spread_inflate](../../degradations/spread_inflate/card.md) ·
[spread_deflate](../../degradations/spread_deflate/card.md)

<!-- GENERATED results_ensemble: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_ensemble -->

The reading of this test is written once the evidence is generated from the final run of every
metric on `synthetic_ensemble`; until then this card cites no measurement.

## References

\bibliography
