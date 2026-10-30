---
type: "MTR"
kind: "variant of variogram_score"
related: ["variogram_score", "energy_score", "crps"]
seen_in: "agent's own"
doi: "none"
found_by: "energy_score, 2026-10-30"
---

# MTR: A fair variogram score, unbiased at every ensemble size

## What it measures

The same mismatch between the reference's and the forecast's variogram of order p as
`variogram_score`, with the finite-ensemble bias of the plug-in estimate removed, so that a
calibrated ensemble scores the same in expectation at any ensemble size and narrowing an
ensemble cannot lower the expected score.

## Definition

With v_ij = |y_i - y_j|^p for the reference, u^(k)_ij = |x^(k)_i - x^(k)_j|^p for member k,
their member mean ubar_ij and unbiased sample variance s2_ij (divisor M - 1),

    VS_fair = sum_{i,j} w_ij [ (v_ij - ubar_ij)^2 - s2_ij / M ].

Scheuerer & Hamill (2015, MWR 143(4), Eq. 3) define the score with E_F|X_i - X_j|^p and
estimate the expectation by ubar_ij (Eq. 4). Since E[(v - ubar)^2] = (v - E u)^2 + Var(u)/M
for members independent of v, and E[s2/M] = Var(u)/M, subtracting s2/M gives an estimator
whose expectation is the score of the distribution the members are drawn from (agent's own
derivation; the same idea as the fair CRPS of Ferro 2014, QJRMS 140(683), Definition 1). It
needs M >= 2 and can be negative on one draw.

## Relation to existing work

`variogram_score` implements the plug-in estimate, which Pacchiardi et al. (2024, JMLR 25(45),
App. C.1.3) call unbiased; it is not, and its expected value falls with ensemble size (measured
in `metrics/variogram_score/test_metric.py`: mean 1139 at four members against 971 at sixteen
for one calibrated process). Neither the catalog nor docs/ideas has a fair variant. I found no
published fair variogram score; this is my own proposal.

## How it could be tested

On `synthetic_ensemble` with the `ensemble_miscalibration` ladder, like `variogram_score`,
plus one unit test: the mean over many draws of a calibrated process agrees at M = 4 and M =
16, where the plug-in estimate differs by about twelve standard errors.

## Why it is helpful

A generative surrogate and its reference ensemble rarely have the same number of members; a
score biased by ensemble size compares the ensembles' sizes as well as their quality, and the
plug-in estimate slightly favours underdispersion, the failure a calibration check exists to
catch.

## References

- Scheuerer, M. & Hamill, T. M. (2015). Monthly Weather Review 143(4), 1321-1334.
  https://doi.org/10.1175/MWR-D-14-00269.1 (Eqs. 3-4).
- Ferro, C. A. T. (2014). Fair scores for ensemble forecasts. QJRMS 140(683), 1917-1923.
  https://doi.org/10.1002/qj.2270 (Definition 1).
- Pacchiardi, L., Adewoyin, R. A., Dueben, P. & Dutta, R. (2024). JMLR 25(45), 1-64.
  https://jmlr.org/papers/v25/23-0038.html (App. C.1.3).
