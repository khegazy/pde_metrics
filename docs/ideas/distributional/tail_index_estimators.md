# Tail-index estimators

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Heavy tails, meaning extreme values that occur far more often than a Gaussian distribution
would predict, can be quantified at three tiers of increasing sophistication. The first tier
is the flatness (kurtosis) of velocity increments and gradients, which equals exactly three
for a Gaussian field and greatly exceeds three for real turbulence. That tier is built, as
[increment_flatness](../../metrics/increment_flatness.md). This idea is the remaining two
tiers.

1. **Tail exceedance probabilities.** For a quantity $q$, such as a velocity increment or a
   gradient, compare the probability $P(|q| > a)$ that its magnitude exceeds a threshold $a$,
   between prediction and reference.
2. **Tail-index estimation from extreme-value theory.** Extreme-value theory is the branch of
   statistics that models the largest values of a sample. The *tail index* summarises how
   slowly the tail of a distribution decays. It can be estimated with the Hill estimator,
   which uses only the largest values in the sample, or by a *peaks-over-threshold* fit, in
   which the values above a high threshold are fitted with a generalised Pareto
   distribution.

## Precedent

The flatness tier is one of the three physics-based criteria used to train and evaluate a
generative adversarial network for turbulent fields (Granero-Belinchón & Cabeza Gallucci
2024). The two tiers here are the more sophisticated steps of the same measurement.

## Rationale

*The team's judgement.* High priority: *intermittency*, the concentration of a field's
activity into rare, intense events, is the first property an over-smoothed emulator
destroys and the last one an $L^2$ loss notices. Like the flatness already built, these
estimators are cheap, have no positivity problem to solve, and measure intermittency
directly.

## Keywords

flatness kurtosis velocity increments, intermittency exponent, Hill estimator tail index,
peaks over threshold generalized Pareto.

## References

- Granero-Belinchón, C. & Cabeza Gallucci, M. (2024). A multiscale and multicriteria
  generative adversarial network to synthesize 1-dimensional turbulent fields. *Machine
  Learning: Science and Technology* 5(2), 025032.
  <https://doi.org/10.1088/2632-2153/ad43b3>
