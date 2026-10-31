# Tail exceedance and peaks-over-threshold

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Heavy tails, meaning extreme values that occur far more often than a Gaussian distribution
would predict, can be quantified at three tiers of increasing sophistication. The first is the
flatness (kurtosis) of increments, built as
[increment_flatness](../../metrics/increment_flatness.md). The Hill estimator of the tail index,
from the largest square-root-of-n absolute one-cell increments, with the Hill plot as its curve, is
built as [tail_index](../../metrics/tail_index.md). This page is what remains of the other two
tiers.

1. **Tail exceedance probabilities.** For a quantity $q$, such as a velocity increment or a
   gradient, compare the probability $P(|q| > a)$ that its magnitude exceeds a threshold $a$,
   between prediction and reference. If built as its own bundle, its name is
   `tail_exceedance`. Two things are open: how the threshold $a$ is fixed once for every model
   (for example in units of the reference's increment standard deviation), and how two
   probabilities are compared (a difference, a ratio, or a curve over $a$).
2. **Peaks-over-threshold fits.** The values above a high threshold are fitted with a
   generalised Pareto distribution, whose shape parameter is the extreme-value index the Hill
   estimator estimates, but which, unlike the Hill estimator, is defined for tails that are
   bounded or fall off faster than any power. That matters here: the Hill estimator is consistent
   only for a power-law tail (Boucheron & Thomas 2015, Sect. 1), and the
   [tail_index](../../metrics/tail_index.md) card records how its value behaves on this
   repository's fields.

## Precedent

The flatness tier is one of the three physics-based criteria used to train and evaluate a
generative adversarial network for turbulent fields (Granero Belinchon & Cabeza Gallucci
2024). Before reading any fitted tail parameter as an exponent, Clauset, Shalizi and Newman
(2009, Sects. 4 and 5) test whether a power law fits at all and compare it with alternatives.

## Rationale

*The team's judgement.* High priority: *intermittency*, the concentration of a field's
activity into rare, intense events, is the first property an over-smoothed emulator
destroys and the last one an $L^2$ loss notices. Like the flatness already built, these
estimators are cheap, have no positivity problem to solve, and measure intermittency
directly.

## Keywords

tail exceedance probability, peaks over threshold, generalized Pareto distribution, threshold
selection, mean residual life.

## References

- Granero Belinchon, C. & Cabeza Gallucci, M. (2024). A multiscale and multicriteria
  generative adversarial network to synthesize 1-dimensional turbulent fields. *Machine
  Learning: Science and Technology* 5(2), 025032.
  <https://doi.org/10.1088/2632-2153/ad43b3>
- Boucheron, S. & Thomas, M. (2015). Tail index estimation, concentration and adaptivity.
  *Electronic Journal of Statistics* 9(2), 2751–2792.
  <https://doi.org/10.1214/15-EJS1088>
- Clauset, A., Shalizi, C. R. & Newman, M. E. J. (2009). Power-law distributions in empirical
  data. *SIAM Review* 51(4), 661–703. <https://doi.org/10.1137/070710111>
