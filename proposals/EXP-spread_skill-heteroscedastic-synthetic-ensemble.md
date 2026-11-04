---
type: "EXP"
kind: "degradation"
related: ["spread_skill", "rank_histogram", "crps", "ensemble_mean_rmse", "energy_score", "docs/datasets/synthetic_ensemble.md", "proposals/EXP-crps-gneiting-forecaster-suite.md", "proposals/EXP-spread_skill-perturbed-initial-condition-ensemble.md"]
seen_in: "Leutbecher & Palmer 2008, J. Comput. Phys. 227(7), 3515-3539, Sect. 2.2, Eqs. 5-7, Figs. 4-5 (numbering of ECMWF Tech. Memo. 514)"
doi: "10.1016/j.jcp.2007.02.014"
found_by: "update_metric_eval_principles, 2026-11-03"
---

# EXP: A synthetic ensemble whose true spread varies from case to case

## What the experiment is

A variant of `synthetic_ensemble` in which the noise amplitude sigma of Equation (1) of its
dataset page is no longer one constant but varies over a known range from case to case (from
frame to frame, or from one region of the grid to another), with the truth still drawn as one
more member at the same sigma. Ensemble operators then damage the members in ways that matter
only because sigma varies:

1. **Flow-dependence removed**: every member drawn with the case-averaged sigma, so the
   ensemble's average spread is right but carries no information about which cases are
   uncertain.
2. **Flow-dependence too strong or too weak**: the members' sigma set to sigma_true^a for
   exponents a above or below one, rescaled to keep the average variance.
3. **Flow-dependence inverted**: large spread where sigma_true is small and the reverse.

The analysis is the spread-error diagram of ensemble forecasting: cases are sorted by the
ensemble's predicted spread into equally populated bins, and the root-mean-square error of
the ensemble mean is plotted against the root-mean-square spread in each bin (Leutbecher &
Palmer 2008, Sect. 2.2, Fig. 4: 89 ECMWF forecasts, 20 bins, lead times of 2, 5 and 10 days).
For a perfect ensemble of N members the two match up to a factor that depends only on N
(their Eqs. 5-7: the expected squared error of the mean is (N+1)/N times the true variance).

## What it tests

It changes, in a controlled and known way, the one property the binned diagram exists to
judge: whether the ensemble knows *which* cases are uncertain. In the calibrated case every
bin lies on the diagonal; operator 1 collapses the bins to one point; operators 2 and 3 tilt
the points to a known slope. The case-averaged spread-to-skill ratio, which is what
`spread_skill` registers, stays near one on operators 1 and 2 by construction (the agent's
construction, to be confirmed numerically), so the experiment also shows what the pooled ratio
cannot see.

## Metrics it would test

`spread_skill` and its binned spread-error figure; `rank_histogram`, which should stay
nearly flat under operator 1 when pooled over all cases (Hamill 2001, Sect. 3a, shows a flat
histogram from an unreliable ensemble; the exact shape here is not derived); `crps`, which
rewards an ensemble that tracks the case-to-case uncertainty and should rise under all three
operators; `ensemble_mean_rmse`, which is blind to them all (the ensemble mean is unchanged in
expectation); `energy_score`.

## Why it is helpful

`synthetic_ensemble` has one sigma for every cell and frame (`docs/datasets/synthetic_ensemble.md`,
Eq. 1), so binning cases by spread gives bins of equal true spread, and the spread-error
diagram is a single point repeated: the evaluation plan therefore withholds the figure as
degenerate on current data. The miscalibration ladder (`spread_inflate`, `spread_deflate`,
`bias`) changes the spread uniformly. An ensemble with the right average spread and no
flow-dependence is therefore a failure no experiment here contains, and no card can say
whether its metric detects it.

## Cost and requirements

A reader option for a sigma field (a closed-form function of position or frame, seeded) and
three ensemble operators. Seconds per run on 64^2 with 16 members. The binned diagram needs a
companion that stores per-bin spread and error, which the multiple-companion harness change of
the plan would allow.

## References

- Leutbecher, M. & Palmer, T. N. (2008). Ensemble forecasting. *Journal of Computational
  Physics* 227(7), 3515-3539. <https://doi.org/10.1016/j.jcp.2007.02.014>. Read in full as
  ECMWF Technical Memorandum 514 (2007),
  <https://www.ecmwf.int/sites/default/files/elibrary/2007/10729-ensemble-forecasting.pdf>; the
  equation and figure numbers above are the memorandum's and were not checked against the
  journal version.
- Hamill, T. M. (2001). Interpretation of rank histograms for verifying ensemble forecasts.
  *Monthly Weather Review* 129(3), 550-560.
  <https://doi.org/10.1175/1520-0493(2001)129<0550:IORHFV>2.0.CO;2> (read in full).
