---
type: "EXP"
kind: "benchmark problem"
related: ["crps", "rank_histogram", "spread_skill", "ensemble_mean_rmse", "energy_score", "variogram_score", "docs/datasets/synthetic_ensemble.md", "proposals/EXP-spread_skill-heteroscedastic-synthetic-ensemble.md"]
seen_in: "Gneiting, Balabdaoui & Raftery 2007, J. R. Stat. Soc. B 69(2), 243-268, Sect. 1, Tables 1, 4, 5, Fig. 1; Sects. 2.2-2.4"
doi: "10.1111/j.1467-9868.2007.00587.x"
found_by: "update_metric_eval_principles, 2026-11-03"
---

# EXP: The ideal, climatological, unfocused and Hamill forecasters as an ensemble ladder

## What the experiment is

The simulation study with which Gneiting, Balabdaoui and Raftery (2007) introduce the
paradigm "maximising the sharpness of the predictive distributions subject to calibration"
(Sect. 1; Sect. 2.4). Nature draws a case mean mu ~ N(0, 1) and the observation from
N(mu, 1). Four forecasters issue a predictive distribution for each case (Sect. 1, Table 1):

| Forecaster | Predictive distribution |
|---|---|
| Ideal | N(mu, 1) |
| Climatological | N(0, 2) |
| Unfocused | (1/2) [N(mu, 1) + N(mu + tau, 1)], tau = +1 or -1 with probability 1/2 each |
| Hamill's | N(mu + delta, s^2), (delta, s^2) = (1/2, 1), (-1/2, 1) or (0, 169/100), each with probability 1/3 |

Transferred here: each cell of `synthetic_ensemble` is a case, with mu drawn per cell; the
truth is drawn from N(mu, 1); the members of each forecaster are draws from its predictive
distribution. The four forecasters are four entries of an ensemble ladder.

## What it tests

It has published answers. All four forecasters have essentially uniform PIT histograms
(Sect. 1, Fig. 1b), so calibration alone cannot separate them; the climatological forecaster is
probabilistically and marginally calibrated (Sect. 2.2.2, Example 2) and the least sharp
(Sect. 3.3, Table 4: central 90% interval 4.65 wide against 3.29 for the ideal). The CRPS
ranks them ideal 0.56, Hamill's 0.61, unfocused 0.63, climatological 0.78 (Sect. 3.4,
Table 5, averages over 10,000 cases). The agent's arithmetic, not from the paper, for the
other metrics, ignoring finite-ensemble terms: the expected squared error of the ensemble mean
equals the mean predictive variance for the ideal (1 against 1), climatological (2 against
2) and unfocused (1.25 against 1.25) forecasters, and nearly so for Hamill's (7/6 against
1.23), so a spread-to-skill ratio reads about one for all four; the ensemble-mean RMSE is about
1, 1.41, 1.12 and 1.08.

## Metrics it would test

`crps` against Table 5, the clearest known-answer check a CRPS estimator can have on more than
one forecaster; `rank_histogram` and `spread_skill`, which should read calibrated for all four
and so must be read beside a sharpness or score; `ensemble_mean_rmse`; `energy_score` and
`variogram_score` (on independent cells they add nothing beyond the per-cell scores, which is
itself a check). The climatological forecaster is also the reference a CRPS skill score needs.

## Why it is helpful

The miscalibration ladder here changes spread (`spread_inflate`, `spread_deflate`) or adds a
`bias`; every rung is miscalibrated, so it never asks a metric to tell a calibrated but useless
forecast from a calibrated and sharp one. That distinction is the centre of the field's
paradigm, and a user of `rank_histogram` or `spread_skill` needs to see on the card that a
climatological forecast passes both.

## Cost and requirements

A reader option for the case means and four ensemble operators that replace the members
(not perturb them), each a few lines of seeded sampling. Seconds per run on 64^2 cells with
16 members. The operators change the ensemble mean, so they declare no `preserves`.

## References

- Gneiting, T., Balabdaoui, F. & Raftery, A. E. (2007). Probabilistic forecasts, calibration
  and sharpness. *Journal of the Royal Statistical Society Series B* 69(2), 243-268.
  <https://doi.org/10.1111/j.1467-9868.2007.00587.x> (read in full: Sect. 1 and Table 1
  p. 245, Sect. 2.2-2.4, Table 4, Table 5 p. 257).
