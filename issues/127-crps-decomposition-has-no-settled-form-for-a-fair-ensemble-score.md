# The CRPS decomposition the field reports has no settled form for this repository's fair ensemble score

**Category:** method
**Priority:** low — the mean CRPS and its skill score are built; the decomposition explains them
**Status:** open. Researched, not built.

## Context

Beside the mean CRPS, ensemble verification reports a decomposition of it into a
miscalibration (reliability) term, a discrimination (resolution) term and an uncertainty term,
`CRPS = MCB - DSC + UNC`. Two forms exist, and `metrics/crps` (plan Part 5, wave 1) was asked
to add one as a companion or siblings if it is a standard reported quantity computable on this
data with cells as cases. It is not built, for the three reasons below.

Sources, read for task `metrics-ensemble` (2026-11-04):

- Arnold, Walz, Ziegel & Gneiting, "Decompositions of the mean continuous ranked probability
  score", Electron. J. Stat. 18(2), 4992–5044 (2024), doi:10.1214/24-EJS2316; arXiv:2311.14122v1.
  Read in full, both versions; the numbering below is the published one unless marked.
- Hersbach (2000), Wea. Forecasting 15(5), 559–570. **Not read**: the publisher refused the
  download and no repository copy was found. Its definitions are known here only as Arnold et
  al. restate them (Sect. 2.5, Appendix B) and as the R package `verification`
  (`crpsDecomposition`, R. Frenette) implements them.

## Why it is not built

1. **The field's own recommendation is a form this repository cannot compute without new
   machinery.** Arnold et al. recommend the isotonicity-based decomposition (Sect. 3.1, Eq. 25):
   `MCB_ISO = CRPS - CRPS_ISO`, `DSC_ISO = CRPS_mg - CRPS_ISO`, with `CRPS_ISO` the mean score of
   the forecasts recalibrated by isotonic distributional regression under the stochastic order
   (Henzi, Ziegel & Gneiting 2021; Appendix C shows that order is the only valid one), at
   `O(n^2)` cost (Table 2), with replication code in R only. That is a partial-order isotonic
   regression over every threshold, not plain pool-adjacent-violators, and nothing in this
   repository or its environment implements it. It would be a new numerical method, with tests
   of its own, rather than a companion of `crps`.
2. **Hersbach's form, the one popular for ensembles, is flawed and sums to a different score.**
   Arnold et al. (Sect. 2.6): "The Hersbach decomposition has been popular in the specific
   setting of ensemble forecasts, but has serious shortcomings including but not limited to the
   possibility of a negative discrimination component" (Proposition 2.3: properties E2,
   non-negative components, and E4, zero discrimination for a constant forecast, fail; the proof
   gives `DSC = -1/6`). They recommend it only in a modified form (Sect. 2.5) and only when `n`
   is too large for the isotonic one (Sect. 6). And its components sum to the CRPS of the
   ensemble's empirical step distribution, the plug-in score with self-pairs, not to the fair
   score `crps` registers: a numerical check of the `verification` package's definitions for
   this task reproduced the plug-in value to machine precision. A decomposition of `crps` would
   therefore not add up to `crps`, and how to make a fair one is an open question with no
   source found.
3. **The definitions could not be confirmed from the primary source.** Arnold et al.'s
   statement of Hersbach's upper outlier bin, `o_m = (1/n) sum 1{x_m < y}`, does not make the
   terms sum to the score in that check; the `verification` package's complement,
   `mean 1{y <= x_m}`, does. Which is Hersbach's cannot be settled without his paper.

On the data that exists, the discrimination term would also say little: `synthetic_ensemble`
has one dispersion for every cell, so forecasts differ from case to case only by sampling
noise (critique finding 2, `agent_logs/2026-11-03-update_metric_eval_principles/CRITIQUE.md`).

## What is built instead

`crps_skill_score`, `1 - CRPS / UNC_0`, whose denominator is the uncertainty term every one of
these decompositions shares (Arnold et al., Eq. 10; `judgements/010` for the climatology).

## What would settle it

- Read Hersbach (2000) to fix the outlier-bin definitions, then decide whether a decomposition
  of the plug-in CRPS, labelled as such beside the fair `crps`, is acceptable.
- Or implement isotonic distributional regression under the stochastic order for empirical
  forecasts (or add a dependency that does), test it against the R replication code on Arnold
  et al.'s Table 1 values, and register `MCB_ISO`, `DSC_ISO` and `UNC_0` as a labelled curve
  companion of `crps` with the MCB–DSC plot (their Sect. 5, Fig. 3) as its figure.
- An experiment where the decomposition carries information needs case-to-case variation in
  the forecast's dispersion:
  [EXP-spread_skill-heteroscedastic-synthetic-ensemble](../proposals/EXP-spread_skill-heteroscedastic-synthetic-ensemble.md).
