---
type: "EXP"
kind: "degradation"
related: ["energy_score", "variogram_score", "crps", "docs/datasets/synthetic_ensemble.md"]
seen_in: "Scheuerer & Hamill 2015, Monthly Weather Review 143(4), 1321-1334"
doi: "10.1175/MWR-D-14-00269.1"
found_by: "energy_score, 2026-10-30"
---

# EXP: A synthetic ensemble with a known spatial correlation, and a ladder that miscorrelates it

## What the experiment is

The calibrated null of `synthetic_ensemble` with its per-cell noise replaced by a Gaussian
random field of known correlation length, drawn independently for the reference and each
member, plus one ensemble operator that redraws the members' noise with a different
correlation length at the same per-cell variance. Scheuerer and Hamill run exactly this
experiment on a one-dimensional exponential correlation model, corr = exp(-|i - j| / r) with
r = 3 for the truth and r = 2 or 4.5 for the forecast (Sect. 3b, Eq. 5, Fig. 2), and with
correlation functions of different shape at matching lag-one correlation (Sect. 3c).

## What it tests

It changes only the joint distribution, in a controlled and known way: the marginal
distribution at every cell, and hence every cell-by-cell score (`crps`, `spread_skill`,
`rank_histogram`, `ensemble_mean_rmse`), is unchanged in expectation, while the correlation
between cells moves by a known amount. A multivariate score that sees correlation structure
must rise as the forecast correlation length departs from the truth's in either direction;
the cell-by-cell scores must stay flat, which is a declared blindness the harness can test.

## Metrics it would test

`energy_score` and `variogram_score` (the first Scheuerer and Hamill find nearly blind to
this, the second sensitive), and the four cell-by-cell ensemble metrics as the blind
controls. A distribution-of-spectra score from the idea page would also respond, since the
correlation length sets the spectrum.

## Why it is helpful

Today no experiment in the repository changes an ensemble's spatial correlation: the
synthetic ensemble has independent noise in every cell, so on it the energy score and the mean
CRPS move together up to a constant (`metrics/energy_score/card.md`, Results). The property
these multivariate scores exist to judge, whether a generative model gets the spatial
structure of its members right, is therefore untested, and this is the smallest experiment
that tests it with a known answer.

## Cost and requirements

A spectral draw per member and frame, which `degradations/gaussian_impostor` already does for
a matched spectrum (a periodic grid, an FFT, Hermitian-symmetric phases). Seconds per run on a
64 by 64 grid with 16 members. One reader option (the correlation length of the noise) and
one ensemble operator with `preserves: [ensemble_mean]` is not right, since a redraw changes
the members; it preserves the per-cell variance in expectation only, which the registry's
`preserves` vocabulary cannot yet express. No licence issues.

## References

- Scheuerer, M. & Hamill, T. M. (2015). Variogram-based proper scoring rules for
  probabilistic forecasts of multivariate quantities. Monthly Weather Review 143(4),
  1321-1334. https://doi.org/10.1175/MWR-D-14-00269.1 (Sect. 3b-3c, Eq. 5, Figs. 2-3).
