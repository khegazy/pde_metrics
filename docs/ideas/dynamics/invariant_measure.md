# Invariant measure and attractor comparison

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Once a rollout has decorrelated from the reference, which in a chaotic system happens after a
few Lyapunov times even for a perfect model (see the
[valid prediction time](valid_prediction_time.md)), the right notion of a correct answer is no
longer a trajectory but a *statistical state*. A chaotic system run for a long time visits
its states with a fixed long-run frequency, its *invariant measure*, supported on its
*attractor*. The comparison is then between the rollout's long-time statistics and the
reference's (Boffetta et al. 2002):

1. **Long-time distributions.** The one-point probability distributions of the fields and of
   their increments, accumulated over a long stretch of the rollout, compared with a
   distributional distance.
2. **Lyapunov exponents.** The rates at which nearby trajectories of the learned dynamics
   separate, compared with those of the reference system.
3. **Attractor dimension.** The correlation dimension, a fractal dimension of the set of
   states the rollout visits. If $C(r)$ is the fraction of pairs of visited states closer
   than $r$, then $C(r)\propto r^{D_2}$ at small $r$, and the exponent $D_2$ is the
   dimension.

Kochkov et al. use this logic when they compare energy spectra "when all solutions have
decorrelated with the reference solution" (Kochkov et al. 2021).

The comparison catches *attractor collapse*: the rollout settling onto a smaller, smoother
attractor than the true one, for example a near-periodic or near-laminar state. Such a
rollout can have a respectable [valid prediction time](valid_prediction_time.md) and still
have the wrong long-time behaviour, with too few dimensions, too small a leading Lyapunov
exponent and too narrow distributions.

Several built metrics already compare distributions and spectra frame by frame, among them
[spectrum_l2](../../metrics/spectrum_l2.md), [increment_w1](../../metrics/increment_w1.md)
and [increment_flatness](../../metrics/increment_flatness.md). Applied to statistics pooled
over a long rollout they cover part of the first item. What this idea adds is the protocol of
long rollouts and the dynamical invariants, Lyapunov exponents and dimension.

## Precedent

Jiang et al. train neural operators so that their long rollouts preserve the invariant
measure of a chaotic attractor, and evaluate them on it (Jiang et al. 2023). The line of
work on Markov neural operators, which learn the dynamics of dissipative chaotic systems,
develops the same idea (Li et al. 2022).

## Pitfalls

- It needs long trajectories, both for the rollout and for the reference, and the
  statistics converge slowly.
- It is blind to short-time accuracy: a model that is wrong at every step but samples the
  right attractor scores well. It must be paired with the
  [valid prediction time](valid_prediction_time.md).
- Dimension estimators are unreliable in high dimensions, where they need very many states
  to resolve the small-$r$ scaling of $C(r)$.
- One-point distributions and spectra can both match while coherent structures and the
  coupling between scales are wrong, so the long-time comparison should include increment
  statistics and phase-sensitive quantities such as the
  [bispectrum](../basis_decompositions/bispectrum.md).

## Rationale

*From the field guide; the team has not yet set a priority.* Beyond the predictability
horizon, the invariant measure is the correct notion of the right answer, since pointwise
tracking is impossible even for a perfect model. Comparing it catches attractor collapse,
which a pointwise error cannot see after decorrelation and the valid prediction time cannot
see at all.

## Keywords

invariant measure, attractor, long-time statistics, Lyapunov spectrum, correlation dimension,
attractor collapse, climate of a surrogate, Markov neural operator.

## References

- Boffetta, G., Cencini, M., Falcioni, M. & Vulpiani, A. (2002). Predictability: a way to
  characterize complexity. *Physics Reports* 356, 367–474.
  <https://doi.org/10.1016/S0370-1573(01)00025-4>
- Jiang, R., Lu, P. Y., Orlova, E. & Willett, R. (2023). Training neural operators to
  preserve invariant measures of chaotic attractors. *NeurIPS* 36.
  <https://arxiv.org/abs/2306.01187>
- Kochkov, D., Smith, J. A., Alieva, A., Wang, Q., Brenner, M. P. & Hoyer, S. (2021). Machine
  learning–accelerated computational fluid dynamics. *Proceedings of the National Academy of
  Sciences* 118, e2101784118. <https://doi.org/10.1073/pnas.2101784118>
- Li, Z., Liu-Schiaffini, M., Kovachki, N., Azizzadenesheli, K., Liu, B., Bhattacharya, K.,
  Stuart, A. & Anandkumar, A. (2022). Learning dissipative dynamics in chaotic systems.
  *NeurIPS* 35. <https://arxiv.org/abs/2106.06898>
