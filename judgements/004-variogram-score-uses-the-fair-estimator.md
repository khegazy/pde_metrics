# 004 — The variogram score uses the fair ensemble estimate, not Scheuerer and Hamill's plug-in

**Date:** 2026-10-31. **Made by:** the agent building `energy_score` and `variogram_score`
(branch `metric/energy_score`), after the adversarial review of that branch.
**Reverse with:** delete the two lines after `mismatch = ...` in
`metrics/variogram_score/metric.py` (the subtraction of the members' sample variance over M),
restore the tests that pin it, re-run the bundle's evidence, then delete this file.

## The question that would have been asked

Scheuerer and Hamill define the variogram score with the forecast's expectation
E_F|X_i − X_j|^p (MWR 143(4), 2015, Sect. 2, Eq. 3) and estimate it from an ensemble by the
member average (their Eq. 4). Inserted into the square of Eq. 3, that average adds the members'
variance of |x_i − x_j|^p divided by M to every term in expectation. Should the bundle register
the score with the paper's estimator, or with the unbiased ("fair") one that `crps` and
`energy_score` use?

## What was measured

- At fixed M the plug-in estimate rewards an overconfident ensemble, because the extra term
  shrinks as the members narrow. On a 12 by 12 field with members scaled about the true mean,
  200 paired draws (`.agent/adversary/vs_fairness.py` of the review): a 20% narrower ensemble
  beat the calibrated one by 66.4 ± 1.4 at two members and 21.5 ± 1.2 at four; at sixteen the
  calibrated one won.
- Across ensemble sizes the plug-in estimate scored one calibrated process 1139 at four members
  against 971 at sixteen, twelve standard errors apart.
- The plug-in estimate also made the score fall on the first step of the contract test's blur
  ladder (109 to 97), because blurred members have less variable differences.

## The choice

**The fair estimate**: each term is (|y_i − y_j|^p − ū)² − s²/M, with ū and s² the members' mean
and sample variance of |x_i − x_j|^p. At M = 1 the correction is empty.

- **It estimates the same score.** The variogram score is a kernel score (Allen, Ginsbourger &
  Ziegel 2023, SIAM/ASA J. Uncertainty Quantification 11(3), 906–940, Sect. 4.1, with their
  Definition 1, Eq. 3), and the unbiased ensemble estimate of a kernel score averages the pair
  term over distinct members only (Pacchiardi et al. 2024, JMLR 25(45), App. C.1.2). Expanded,
  that estimate is the formula above. It is the variogram analogue of the fair CRPS (Ferro 2014,
  QJRMS 140(683), Definition 1) that `crps` uses, and of the fair estimator `energy_score` uses.
- **Software practice.** The `scoringrules` Python package implements both,
  `vs_ensemble(estimator="nrg")` (the plug-in, its default) and `estimator="fair"` (this one).
- **The project's goal.** Overconfidence is the failure an ensemble score exists to catch; an
  estimator that rewards it at the ensemble sizes a generative surrogate is likely to produce
  (a handful of members) defeats the score's purpose.

Measured after the change, with the tests in `metrics/variogram_score/test_metric.py`: a
narrowed two-member ensemble no longer beats the calibrated one, and the means at four and
sixteen members agree within four standard errors.

## What it changes

Every number `variogram_score` produces, by the subtracted variance; the fair estimate can fall
slightly below zero on one draw, so the card's lower bound is removed. The bundle's evidence was
re-run after the change. Comparisons with published variogram scores computed with Eq. 4 are no
longer exact: the two differ by the sum of the weighted variances over M.

## How to reverse it

Remove the subtraction, restore `lower: 0.0` in `card.yaml`, replace the fairness tests with the
plug-in's (its ensemble-size dependence was pinned in the bundle's first commit, d2464fb), re-run
the evidence, and delete this file and its row in `README.md`.
