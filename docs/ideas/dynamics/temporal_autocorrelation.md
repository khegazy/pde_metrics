# Temporal autocorrelation

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The temporal autocorrelation measures how quickly a field forgets its own past. For the
fluctuation $u'=u-\bar u$ of a statistically stationary signal, at a point or for a global
quantity,

$$
R(\tau)=\frac{\langle u'(t)\,u'(t+\tau)\rangle}{\langle u'^2\rangle},\qquad
T=\int_0^{\infty}R(\tau)\,d\tau, \tag{1}
$$

where the average runs over time, and over space for a homogeneous field, and $T$ is the
*integral time scale*, the typical time over which the signal stays correlated with itself.
The metric compares the autocorrelation function and the integral time scale of a rollout
with those of the reference.

Unlike a pointwise error, this compares each trajectory with itself, so it needs no phase
alignment between rollout and reference and stays meaningful after they have decorrelated.

It is aimed at a specific failure. A model trained to minimise a mean-squared error learns,
at best, the conditional mean of the next state given the current one,

$$
\hat u^\star=\mathbb{E}\big[u_{n+1}\,\big|\,u_n\big], \tag{2}
$$

and when the future is uncertain, as in a chaotic flow, that average over the possible
futures is smoother than any of them. Rolled out, such a model drains fluctuation energy and
evolves too sluggishly. Its autocorrelation decays too slowly and its integral time scale is
too long.

## Pitfalls

- It is insensitive to spatial structure. A rollout with the right decorrelation time and
  entirely wrong structures passes.
- It requires statistically stationary segments of both trajectories; for a decaying flow
  the autocorrelation depends on the starting time.
- The estimated $R(\tau)$ is noisy at large lags, so the upper limit of the integral in (1)
  must be declared once and kept fixed.

## Rationale

*From the field guide; the team has not yet set a priority.* The temporal autocorrelation
detects over-smoothed dynamics that evolve and decorrelate too slowly, the signature of
collapse toward the conditional mean in (2). It is cheap, needs only time series the rollout
already produces, and complements the [valid prediction time](valid_prediction_time.md),
which measures departure from the reference rather than the rollout's own memory.

## Keywords

temporal autocorrelation, integral time scale, decorrelation time, conditional-mean
collapse, regression to the mean, over-smoothing.
