---
type: "EXP"
kind: "protocol"
related: ["spread_skill", "rank_histogram", "crps", "ensemble_mean_rmse", "energy_score", "docs/datasets/synthetic_ensemble.md", "proposals/EXP-spread_skill-perturbed-initial-condition-ensemble.md"]
seen_in: "Leutbecher & Palmer 2008, J. Comput. Phys. 227(7), 3515-3539, Sect. 2.2, Eqs. 5-7, Figs. 4-5 (numbering of ECMWF Tech. Memo. 514)"
doi: "10.1016/j.jcp.2007.02.014"
found_by: "update_metric_eval_principles, 2026-11-03"
---

# EXP: The binned spread-error diagram on a synthetic ensemble whose true spread varies

*Built 2026-11-26: the data and the operators.* The `synthetic_ensemble` reader option
`sigma_ratio` makes the true noise level vary across the domain, for truth and members alike,
and the ensemble operator `flow_dependence` (`degradations/flow_dependence/`) gives the
members a spread that follows the true one too weakly (`direction: damp`, severity below 1), not
at all (damp 1), inversely (damp 2) or too strongly (`direction: amplify`), keeping the ensemble
mean and the frame's mean variance (`docs/datasets/synthetic_ensemble.md`;
`dataset_specs/08_synthetic_ensemble_extensions.md`, Sect. 3.2; ladder entries
`flow_dependence_damp` and `flow_dependence_amplify` in
`configs/degradation/ensemble_miscalibration.yaml`). The noise level varies between regions of
the grid, not between frames, because an operator sees one frame at a time. What remains is the
figure these operators exist for, which no code here draws yet.

## What the experiment is

The spread-error diagram of ensemble forecasting, drawn on the ensemble above: cases are sorted
by the ensemble's predicted spread into equally populated bins, and the root-mean-square error
of the ensemble mean is plotted against the root-mean-square spread in each bin (Leutbecher &
Palmer 2008, Sect. 2.2, Fig. 4: 89 ECMWF forecasts, 20 bins, lead times of 2, 5 and 10 days).
For a perfect ensemble of N members the two match up to a factor that depends only on N (their
Eqs. 5-7: the expected squared error of the mean is (N+1)/N times the true variance).

## What it tests

Whether the ensemble knows *which* cases are uncertain. In the calibrated case the bins follow
the diagonal; `flow_dependence` at damp 1 collapses them to one point, and its other settings
tilt them to a slope spec 08 derives (Sect. 3.2, known answer 3). The case-averaged
spread-to-skill ratio that `spread_skill` registers does not change under the operator, which
keeps the frame's mean variance, so the figure shows what the pooled ratio cannot see.

## Metrics it would test

`spread_skill` and its binned spread-error figure. The same operators also reach `crps`,
`rank_histogram`, `ensemble_mean_rmse` (blind to them, since the ensemble mean is unchanged) and
`energy_score` without the figure, as ordinary ladder entries.

## Why it is helpful

The `spread_skill` card withholds the binned diagram as degenerate on an ensemble with one
noise level everywhere. The data that makes it informative now exists; the figure does not.
`EXP-spread_skill-perturbed-initial-condition-ensemble.md` asks for the same figure on the
solver's physical ensemble, where the true spread is not known.

## Cost and requirements

A companion of `spread_skill` that stores per-bin spread and error (a metric may declare
several companions, `metrics/registry.py`), and a figure drawn from it. Binning by the reader's known
noise level, as well as by the members' sample spread, separates sampling noise from
miscalibration (spec 08, Sect. 3.2, known answer 2). Seconds per run on 64^2 with 16 members.

## References

- Leutbecher, M. & Palmer, T. N. (2008). Ensemble forecasting. *Journal of Computational
  Physics* 227(7), 3515-3539. <https://doi.org/10.1016/j.jcp.2007.02.014>. Read in full as
  ECMWF Technical Memorandum 514 (2007),
  <https://www.ecmwf.int/sites/default/files/elibrary/2007/10729-ensemble-forecasting.pdf>; the
  equation and figure numbers above are the memorandum's and were not checked against the
  journal version.
