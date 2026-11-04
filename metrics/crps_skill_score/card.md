---
name: crps_skill_score
kind: metric
---

## Definition

The skill score compares the mean CRPS of the ensemble with the mean CRPS of a reference
forecast. Gneiting and Raftery define a skill score for any score $S$ averaged over a set of
cases [@gneitingraftery2007]:

$$
S^{\mathrm{skill}} = \frac{\bar S^{\mathrm{fcst}} - \bar S^{\mathrm{ref}}}
{\bar S^{\mathrm{opt}} - \bar S^{\mathrm{ref}}} \tag{1}
$$

which is their Equation (8), with $\bar S$ the mean score over the cases. For the CRPS, lower
is better and the optimum is zero, so Equation (1) becomes

$$
\mathrm{CRPSS} = 1 - \frac{\overline{\mathrm{CRPS}}}{\overline{\mathrm{UNC}}} \tag{2}
$$

a ratio of the two means, not a mean of per-cell ratios. The numerator is the fair ensemble
CRPS that [crps](../../metrics/crps/card.md) registers, averaged over channels and cells.

**The reference is climatology**, which Gneiting and Raftery describe as "an estimate of the
marginal distribution of the predictand" [@gneitingraftery2007]. Here it is the empirical
distribution of the reference's own values over the whole domain of the same frame, one per
channel (`judgements/011`). For channel $c$ with values $y_{c,1} \dots y_{c,n}$, the mean CRPS
of that distribution over the same values is

$$
\mathrm{UNC}_c = \frac{1}{2n^2}\sum_{i=1}^{n}\sum_{j=1}^{n} |y_{c,i} - y_{c,j}| \tag{3}
$$

which follows from the kernel form of the CRPS (Equation (2) of the `crps` card) with $F$ the
empirical distribution, its expectations taken exactly. It is the uncertainty term
$\mathrm{UNC}_0$ shared by every decomposition of the mean CRPS (Arnold and colleagues,
Equation (10) of the published version, Equation (11) of the arXiv version) [@arnold2024], so
Equation (2) reads the ensemble's score as a fraction of the uncertainty of the field's values.
$\overline{\mathrm{UNC}}$ is the mean of $\mathrm{UNC}_c$ over channels, so the two components
of a velocity each have their own climatology and are never pooled into one distribution.
Equation (3) is evaluated by sorting each channel's values, with the same helper `crps` uses
for its pair sum.

Two consequences of the definitions are worth stating. Equation (3) includes the self-pairs,
because the climatological forecast *is* the empirical distribution rather than a sample of
one, while the fair CRPS of the numerator excludes them. So an ensemble whose members are
exactly the $n$ climatological values, at every cell, does not score zero: its fair CRPS
averages $\Sigma/n^2 - \Sigma/(2n(n-1))$ for $\Sigma$ the double sum of Equation (3), and its
skill score is $1/(n-1)$ (a derivation of this card's, pinned by this bundle's tests). With
$n = 4096$ cells that is $2.4 \times 10^{-4}$. And the score is undefined where every channel
of the reference is constant, since climatology is then exact; the metric returns NaN there.

### Boundary handling

None. Both the CRPS and the climatological score are computed from values at single cells; the
climatology pools every cell of the domain without regard to where it sits, so the edge of the
domain and its periodicity never enter.

### How its field reports it

The field is probabilistic forecast verification.

- **The object and its normalisation.** Equation (1), a ratio of mean scores over a set of
  cases with a climatological reference (Gneiting and Raftery, Section 2.3) [@gneitingraftery2007].
  The CRPS decompositions fix the reference as the empirical distribution of the observations
  in the verification set, whose mean score is $\mathrm{UNC}_0$ (Arnold and colleagues,
  Equation (10)) [@arnold2024]. Here the verification set is the cells of one frame and channel,
  which is why the climatology is that frame's values.
- **The statistics reported beside it.** Gneiting and Raftery note that skill scores of the form
  of Equation (1) "are generally improper, even if the underlying scoring rule $S$ is proper"
  (Section 2.3) [@gneitingraftery2007]: a forecaster can gain skill-score points without
  improving the mean score when the reference changes from case to case. Ranking ensembles
  therefore uses the mean CRPS, [crps](../../metrics/crps/card.md); the skill score is its reading on a
  scale where zero is climatology. Arnold and colleagues define no skill score; they report
  the mean CRPS beside $\mathrm{UNC}_0$ and the miscalibration and discrimination terms (Table
  1) [@arnold2024], which are not built here
  ([issue 127](https://github.com/khegazy/pde_metrics/blob/main/issues/127-crps-decomposition-has-no-settled-form-for-a-fair-ensemble-score.md)).
- **The figure.** The skill score against lead time, one line per forecasting system, is the
  usual reading of a skill score; this card found no primary source that fixes it, so it is
  named here as practice rather than as a cited standard. It cannot be drawn on the data that
  exists: `synthetic_ensemble` has no lead time.
- **The experiment.** As for `crps`: many forecast cases against observations, at each lead
  time, and forecasters of known calibration and sharpness. Only the calibrated null of
  `synthetic_ensemble` exists here; real ensembles wait on
  [issue 004](https://github.com/khegazy/pde_metrics/blob/main/issues/004-independent-realizations.md).
  The missing experiments are
  [EXP-crps-gneiting-forecaster-suite](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-crps-gneiting-forecaster-suite.md),
  whose climatological forecaster is the reference of Equation (2) by construction, and
  [EXP-spread_skill-perturbed-initial-condition-ensemble](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-spread_skill-perturbed-initial-condition-ensemble.md),
  which has lead times.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED performance -->

## Intuition

This number says how much better an ensemble does than a forecast that knows only which values
the field takes, not where it takes them. The comparison forecast, climatology, predicts at
every point the whole spread of values seen across the field. An ensemble that has learned the
field's structure narrows that down at each point; the skill score is the fraction of
climatology's error it removes.

It is built from the continuous ranked probability score, which scores a set of predicted
values against the truth by rewarding members near the truth and honest spread. Scoring
climatology the same way gives the error of knowing nothing about position. One minus the
ratio of the two is the skill: one for a perfect ensemble, zero for one no better than
climatology, negative for one that is worse, for example an ensemble that is confidently in the
wrong place.

A worked example on one channel of two cells, whose reference values are 0 and 2, with two
members per cell:

```
reference        member 1        member 2        result
0  2             1  2            1  4            0.0
```

Climatology predicts "0 or 2, equally likely" at both cells; its score is half the average
distance between the field's values, 0.5. The first cell's members both say 1 against a truth
of 0: a score of 1. The second cell's members, 2 and 4, straddle the truth of 2 in a way that
the spread credit exactly cancels: a score of 0. The ensemble's mean score is 0.5, the same as
climatology's, so its skill is zero.

What it ignores is the same as the CRPS: position. A feature drawn in the right shape one cell
away is penalised at both places, and climatology, which ignores position entirely, is no
help.

## Reading the output

The value is dimensionless, at most one, and unbounded below; higher is better. One is a
perfect ensemble, zero is the climatological score, and a negative value means the ensemble
scores worse than predicting the field's distribution of values everywhere.

What counts as good depends on how much of the field's variation is predictable. On a field
whose structure is known and whose noise is not, skill is high even for an ensemble that is no
better than chance about the noise; on a field that is mostly noise, the same ensemble scores
near zero. Read it as the fraction of the climatological score removed, and compare across
models on the same dataset, where the denominator is the same for every model, frame by frame.

Comparisons across datasets and fields are weaker than they look: the denominator is each
frame's own climatology, so a field with a wider spread of values has a larger denominator and,
for the same CRPS, a higher skill. Comparisons across ensemble sizes of two or more inherit the
fairness of the numerator. Because the skill score is a ratio, it is not itself a proper
score, so to rank ensembles on one dataset use `crps`; this number says where that ranking
sits between climatology and perfection.

## Limitations

The reference changes from frame to frame, so the skill score of one ensemble can rise between
two frames while its CRPS rises too, because the field's spread of values grew faster. Averaging
skill scores over frames, rather than taking the ratio of averaged scores, mixes those
denominators; the number on each row is a per-frame ratio and should be read that way.

Climatology here knows nothing about position, so on any field with large-scale structure it is
a weak reference, and skill near one says only that the ensemble knows the structure. It does
not say that the ensemble's spread is honest: an ensemble that has the structure right and is
badly overconfident about the small-scale noise still scores high, because the structure carries
most of the climatological score. `spread_skill` and `rank_histogram` see that failure; this
does not.

On a nearly constant reference the denominator is tiny and the ratio is dominated by it: a
CRPS that is not equally small becomes a large negative skill. The metric is undefined, and returns NaN,
only when every channel is exactly constant.

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

The skill score scores an ensemble, so the synthetic ensemble is the one experiment in this
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
