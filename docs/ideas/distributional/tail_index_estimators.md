# Peaks-over-threshold fits

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Heavy tails, meaning extreme values that occur far more often than a Gaussian distribution
would predict, can be quantified at several tiers of increasing sophistication. The flatness
(kurtosis) of increments is built as [increment_flatness](../../metrics/increment_flatness.md).
The Hill estimator of the tail index, from the largest square-root-of-n absolute one-cell
increments, with the Hill plot as its curve, is built as
[tail_index](../../metrics/tail_index.md). The comparison of how often a prediction's increments
reach the reference's extreme level, the frequency bias of that exceedance with a curve over the
level, is built as [tail_exceedance](../../metrics/tail_exceedance.md). This page is what remains.

**Peaks-over-threshold fits.** The values above a high threshold are fitted with a generalised
Pareto distribution, whose shape parameter is the extreme-value index the Hill estimator
estimates, but which, unlike the Hill estimator, is defined for tails that are bounded or fall off
faster than any power. That matters here: the Hill estimator is consistent only for a power-law
tail (Boucheron & Thomas 2015, Sect. 1), and the [tail_index](../../metrics/tail_index.md) card
records how its value behaves on this repository's fields. The threshold above which the fit is
made is open; [tail_exceedance](../../metrics/tail_exceedance.md) fixes its exceedance level as a
percentile of the reference, the $\sqrt{n}$-th largest increment, and a fit could reuse it.

## Precedent

Before reading any fitted tail parameter as an exponent, Clauset, Shalizi and Newman (2009,
Sects. 4 and 5) test whether a power law fits at all and compare it with alternatives.

## Rationale

*The team's judgement.* High priority: *intermittency*, the concentration of a field's
activity into rare, intense events, is the first property an over-smoothed emulator
destroys and the last one an $L^2$ loss notices. A fitted shape parameter measures the tail
directly, for any sign of the extreme-value index.

## Keywords

peaks over threshold, generalized Pareto distribution, threshold selection, mean residual life.

## References

- Boucheron, S. & Thomas, M. (2015). Tail index estimation, concentration and adaptivity.
  *Electronic Journal of Statistics* 9(2), 2751–2792.
  <https://doi.org/10.1214/15-EJS1088>
- Clauset, A., Shalizi, C. R. & Newman, M. E. J. (2009). Power-law distributions in empirical
  data. *SIAM Review* 51(4), 661–703. <https://doi.org/10.1137/070710111>
