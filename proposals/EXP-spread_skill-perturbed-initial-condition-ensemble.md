---
type: "EXP"
kind: "protocol"
related: ["spread_skill", "crps", "rank_histogram", "ensemble_mean_rmse", "energy_score", "variogram_score", "issues/003", "issues/004", "issues/083", "proposals/EXP-spread_skill-heteroscedastic-synthetic-ensemble.md", "docs/datasets/reynolds_ladder_2d.md"]
seen_in: "Leutbecher & Palmer 2008, J. Comput. Phys. 227(7), 3515-3539, Sect. 2.2, Eqs. 5-7, Fig. 4 (numbering of ECMWF Tech. Memo. 514)"
doi: "10.1016/j.jcp.2007.02.014"
found_by: "update_metric_eval_principles, 2026-11-03"
---

# EXP: Spread and error against lead time, and the binned spread-error diagram, on the solver's ensemble

*Built 2026-11-27: the ensemble.* `kinet_shear_layer_ensemble` reads 17 kinet runs of the
Re 5e4 shear layer from each of three start states, every run started from an independent small
perturbation, with one fixed truth (`member_00`) and the other 16 runs as members, at leads of
500 to 5 000 solver steps; its rows carry `lead_time`, and the ensemble ladder
(`degradation=ensemble_miscalibration`) applies to its members
(`configs/dataset/kinet_shear_layer_ensemble.yaml`; `docs/datasets/reynolds_ladder_2d.md`;
`dataset_specs/BUILD_ORDER.md`, step 21). Taking each run as the truth in turn and pooling tests
nothing: the pooled ratio of the ensemble mean's squared error to the members' variance is
(N + 1)/N for any data (`dataset_specs/01_physical_ensemble.md`, Section 3, correction). What
remains is the analysis this file now asks for: the two figures the field draws first, which no
code here draws on an ensemble yet.

## What the experiment is

The standard analyses of an operational ensemble (Leutbecher & Palmer 2008, Sect. 2.2), drawn
on `kinet_shear_layer_ensemble`:

1. **Spread and error against lead time.** The root-mean-square spread of the members and the
   root-mean-square error of the ensemble mean, each against lead time, per start and pooled
   over the three starts. The card figures here draw a curve against prediction step only for
   rows that carry a `lead_step` (`fmeval/cards/metric_figures.py`, `_forecasts`); the ensemble's
   rows carry `lead_time` alone.
2. **The binned spread-error diagram.** Cases binned by predicted spread into equally populated
   bins, the error of the ensemble mean plotted against the spread in each bin (their Fig. 4,
   at lead times of 2, 5 and 10 days). A per-bin companion of `spread_skill` would store it;
   `EXP-spread_skill-heteroscedastic-synthetic-ensemble.md` asks for the same figure on the
   synthetic ensemble, where the true spread of each bin is known.

For a perfect ensemble of N members scored against one truth drawn from the same distribution,
the expected squared error of the ensemble mean is (N + 1)/N times the true variance (their
Eqs. 5-7), so both figures have a known answer at every lead time and in every bin.

## What it tests

Real chaotic error growth: the spread grows with lead time at a rate set by the flow, and
differs from region to region and from start time to start time. A single truth's calibration
scatters about the perfect-ensemble answer (`configs/dataset/kinet_shear_layer_ensemble.yaml`
gives the measured range over the 51 possible truths), so the figures must show that scatter
across the three starts rather than one pooled number.

## Metrics it would test

`spread_skill` (against lead time and binned), `crps`, `rank_histogram`, `ensemble_mean_rmse`,
`energy_score` and `variogram_score`, each against lead time.

## Why it is helpful

Weather ensembles are evaluated across many cases and lead times, and a card that shows its
metric without the lead-time axis gives a user from that field no reading they recognise. The
data now exists; only the figures are missing.

## Cost and requirements

A lead-time figure that reads `lead_time` on ensemble rows, and a per-bin companion of
`spread_skill`. No new data.

## References

- Leutbecher, M. & Palmer, T. N. (2008). Ensemble forecasting. *Journal of Computational
  Physics* 227(7), 3515-3539. <https://doi.org/10.1016/j.jcp.2007.02.014>. Read in full as
  ECMWF Technical Memorandum 514 (2007),
  <https://www.ecmwf.int/sites/default/files/elibrary/2007/10729-ensemble-forecasting.pdf>; the
  equation and figure numbers are the memorandum's and were not checked against the journal
  version.
