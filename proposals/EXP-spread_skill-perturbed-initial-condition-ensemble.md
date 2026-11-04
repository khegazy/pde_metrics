---
type: "EXP"
kind: "benchmark suite or dataset"
related: ["spread_skill", "crps", "rank_histogram", "ensemble_mean_rmse", "energy_score", "variogram_score", "issues/003", "issues/004", "issues/083", "proposals/EXP-spread_skill-heteroscedastic-synthetic-ensemble.md"]
seen_in: "Leutbecher & Palmer 2008, J. Comput. Phys. 227(7), 3515-3539, Sect. 2.2, Eqs. 5-7, Fig. 4 (numbering of ECMWF Tech. Memo. 514)"
doi: "10.1016/j.jcp.2007.02.014"
found_by: "update_metric_eval_principles, 2026-11-03"
---

# EXP: A perfect-model ensemble of the solver from perturbed initial conditions, over lead times

## What the experiment is

The physical counterpart of `synthetic_ensemble`. Start N + 1 runs of the kinet solver from
one initial state plus N + 1 independent small perturbations, at several start times; call one
run the truth and the other N the ensemble; score the ensemble against the truth at every
stored lead time. Because truth and members are draws from the same distribution, this is a
*perfect ensemble* in the sense of Leutbecher and Palmer (2008, Sect. 2.2), and their Eqs. 5-7
give the expected answer at every lead time: averaged over cases, the squared error of the
ensemble mean is (N+1)/N times the true variance, and matches the ensemble spread up to a
factor that depends only on N. Repeating with each run in turn as the truth multiplies the
cases at no extra cost.

The field's standard analyses then apply as they are drawn for operational ensembles:
spread and error of the ensemble mean against lead time, and the spread-error diagram, with
cases binned by predicted spread (their Fig. 4, at lead times of 2, 5 and 10 days).

## What it tests

Real chaotic error growth: the spread grows with lead time at a rate set by the flow, and
differs from region to region and from start time to start time, so the ensemble's spread is
flow-dependent in a way no synthetic construction reproduces. Its answer is still known (a
perfect ensemble, calibrated at every lead time and in every spread bin), so a metric that
reports miscalibration on it is wrong. Applying the ensemble degradations (`spread_inflate`,
`spread_deflate`, `bias`) to its members gives the same ladder as today on physical members.

## Metrics it would test

Every ensemble metric: `spread_skill` (against lead time and binned), `crps`,
`rank_histogram`, `ensemble_mean_rmse`, `energy_score` and `variogram_score`, the last two now
on members whose spatial correlation is physical. A generative surrogate's ensemble could later
be scored on the same cases, which is issue 083's need.

## Why it is helpful

The ensemble metrics are evaluated here only on generated, independent-cell noise with one
sigma (`docs/datasets/synthetic_ensemble.md`), with no lead time, so their cards cannot draw
the figures their field draws first; the evaluation plan withholds them as degenerate. Issue
003 records that physical ensemble data is open, and issue 004 asks for runs from different
seeds to serve as independent realisations; this experiment uses a related set of runs, a
small perturbation instead of a new seed, for a different purpose. Weather ensembles are
evaluated this way across many cases and lead times, and a card that shows its metric only on
synthetic noise gives a user from that field no reading they recognise.

## Cost and requirements

(N + 1) solver runs per start time; with 16 members and three start times, 51 runs of the
rollout horizon at 256^2 (the agent's arithmetic). A perturbation amplitude small against the
flow's fluctuation and a check that the members have decorrelated from one another by the
lead times scored; a reader that assembles members from separate runs into the existing
`Frame.members` slot; a lead-time axis in the analysis, which the forecast-pair reader of issue
010 introduces for the deterministic case.

## References

- Leutbecher, M. & Palmer, T. N. (2008). Ensemble forecasting. *Journal of Computational
  Physics* 227(7), 3515-3539. <https://doi.org/10.1016/j.jcp.2007.02.014>. Read in full as
  ECMWF Technical Memorandum 514 (2007),
  <https://www.ecmwf.int/sites/default/files/elibrary/2007/10729-ensemble-forecasting.pdf>; the
  equation and figure numbers are the memorandum's and were not checked against the journal
  version.
