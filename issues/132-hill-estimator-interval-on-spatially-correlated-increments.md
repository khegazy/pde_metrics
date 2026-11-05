# The Hill estimator's interval is not reported, because its variance on spatially correlated increments is unknown

**Category:** method
**Priority:** low — the estimate and both Hill plots are built; the interval would say how far apart two values must be to differ
**Status:** open. Researched, not built.

## Context

Beside the Hill estimate, its field reports an interval. For independent, identically
distributed samples the estimate at order $k$ is asymptotically normal with variance
$\gamma^2/k$, so its standard error is $\gamma/\sqrt{k}$:

- Resnick and Stărică, "Smoothing the Hill estimator", Cornell ORIE technical report 1114 (1995),
  published as Adv. Appl. Probab. 29(1), 271–293 (1997): p. 2, "asymptotically normal with
  asymptotic variance $\alpha^{-2}$" under further assumptions, for iid data. Technical report
  read in full; the journal version not opened.
- Drees, de Haan and Resnick, "How to make a Hill plot", Ann. Stat. 28(1), 254–274 (2000):
  Section 2 assumes iid data; its Theorem 1, Eq. (2.3), approximates $H_{k,n}$ by
  $\gamma + \gamma W(k)/k$ for a standard Brownian motion $W$, so the variance is $\gamma^2/k$
  when the bias is negligible (the step to $\gamma/\sqrt{k}$ is this issue's derivation, not a
  sentence of the paper). Read in full in its discussion-paper and technical-report versions.
- Clauset, Shalizi and Newman, SIAM Rev. 51(4), 661–703 (2009), arXiv 0706.1062v2: Eq. (3.2),
  $\sigma = (\hat\alpha - 1)/\sqrt{n}$, and Appendix B, stated there for independent,
  identically distributed draws. Section 4 adds a bootstrap Kolmogorov-Smirnov goodness-of-fit
  p-value, also for independent data.

`tail_index` reads the one-cell increments of a flow field. They are strongly correlated in
space: on kinet frames 2000, 5000 and 8000, 87% to 100% of the top-256 cells of every
(channel, axis) pair have another top-256 cell among their 8 neighbours
(`metrics/tail_index/research_notes.md`, "Review round"), and a two-cell blur of an independent
Pareto field halves the estimate (`test_spatial_clustering_lowers_the_estimate_of_a_power_law_field`).

## What is known under dependence

- Hsing, "On tail index estimation using dependent data", Ann. Stat. 19(3), 1547–1569 (1991):
  the abstract says consistency and asymptotic normality extend to strictly stationary mixing
  sequences. **Read through its abstract only** (Project Euclid refused the fetch); the theorem
  numbers (2.2 for consistency, 2.4 for the limit law) come from a secondary source, J. B. Hill,
  "On tail index estimation for dependent, heterogeneous data" (working paper econwpa 0505005).
- Drees, "Some aspects of extreme value statistics under serial dependence", Extremes 11, 35–53
  (2008), arXiv 0710.5879, read in full: Section 2.2 gives the variance of the Hill estimator
  applied to a moving-average series as $\gamma^2$ times a factor of the form
  $1 + 2\sum(\text{tail-dependence terms})$, "strictly larger than the asymptotic variance
  $\gamma^2$" of the independent case; for AR(1) it is
  $\gamma^2 (1 + |\phi_1|^{1/\gamma}) / (1 - |\phi_1|^{1/\gamma})$.
- Drees, Bernoulli 9(4), 617–657 (2003): its abstract says consistent estimators of the
  asymptotic variance are introduced under beta-mixing. Not read.
- Nothing read gives the variance, or an estimator of it, for a random field on a two- or
  three-dimensional grid, nor for the mean over channel-and-axis pairs this bundle reports.

So $\gamma/\sqrt{k}$ would be too narrow on these fields by a factor set by how the largest
increments cluster, which is unknown here (this issue's reasoning, from the sources above).

## What would settle it

1. **A source** for the Hill estimator's variance on a stationary random field, or a block
   estimator whose blocks are spatial tiles (Drees 2003 is the place to start for series).
2. **A measurement**: the spread of the estimate across many independent realisations of one
   flow, compared with $\gamma/\sqrt{k}$. The repository has one realisation per configuration
   (`issues/004`).
3. **A spatial block bootstrap**, the same device the analysis uses across frames
   (`fmeval/stats.py`), applied to tiles of one field, if a source supports the tile size.

Until then the card states the interval and why it is not drawn
(`metrics/tail_index/card.md`, "How its field reports it" and Limitations).

## Related

- `metrics/tail_index/card.md`; `judgements/002` (the estimator on fields without a power-law tail).
- `proposals/MTR-tail_index-ks-threshold.md`: the Kolmogorov-Smirnov threshold, whose p-value
  carries the same independence assumption.
