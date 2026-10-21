# Valid prediction time

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

In a chaotic system, two trajectories that start a small distance $\delta_0$ apart separate
as

$$
\delta(t)\approx\delta_0\,e^{\lambda_1 t}, \tag{1}
$$

where $\lambda_1$ is the leading Lyapunov exponent and $\tau_\lambda=1/\lambda_1$ is the
*Lyapunov time* (Boffetta et al. 2002). The separation grows until it reaches the size of the
attractor, the set of states the system visits in the long run. At that point the prediction
$\hat u$ and the reference $u$ are effectively independent draws from the same statistics.
If both have mean $\bar u$ and variance $\sigma_u^2$ and are independent, then

$$
\big\langle(\hat u-u)^2\big\rangle=\big\langle(\hat u-\bar u)^2\big\rangle
+\big\langle(u-\bar u)^2\big\rangle=2\sigma_u^2, \tag{2}
$$

so the root-mean-square error saturates at $\sqrt{2}\,\sigma_u$ whatever the model's quality.
After a few Lyapunov times a pointwise error carries no information about the model.

The *valid prediction time* is the time at which the normalised error of a rollout first
exceeds a declared threshold $\theta$:

$$
t_{\mathrm{VPT}}=\min\big\{\,t \;:\; \|\hat u(t)-u(t)\|\,/\,\|u(t)\|>\theta\,\big\}, \tag{3}
$$

reported in units of the Lyapunov time. A companion is the *time to decorrelation*: the time
at which the correlation between a predicted field, such as vorticity, and the reference
first drops below a declared threshold (Kochkov et al. 2021; Lippe et al. 2023).

## Precedent

Pathak et al. report that reservoir computers predicted the Kuramoto–Sivashinsky equation for
about eight Lyapunov times (Pathak et al. 2018). Whether that paper states the threshold
definition (3) itself has not been checked against its full text; its abstract does not.
Kochkov et al. evaluate their machine-learning-accelerated solver by its vorticity
correlation with the reference and note that decorrelation within a few Lyapunov times is
expected from chaos alone (Kochkov et al. 2021). PDE-Refiner's headline result is the time
until the correlation between rollout and reference drops below 0.8 (Lippe et al. 2023).

## Pitfalls

- It says nothing about whether the state after decorrelation is physical. A rollout that
  decorrelates at the right time and then collapses onto a smooth, wrong attractor has a good
  valid prediction time. It must be paired with statistical comparisons, such as the
  [invariant measure](invariant_measure.md), or with reference-free physics checks.
- The thresholds $\theta$ and the correlation level are choices. They are fixed once in the
  evaluator and never tuned per model, or the metric becomes gameable.
- The Lyapunov time must be estimated from the reference system, and the unit is meaningful
  only for a chaotic, statistically stationary system. For a decaying or transient flow an
  eddy-turnover time or another declared physical time is the natural unit instead.

## Rationale

*From the field guide; the team has not yet set a priority.* Surrogates are usually
validated one step ahead from true inputs but deployed autoregressively on their own outputs.
This is the mismatch known in sequence modelling as exposure bias (Bengio et al. 2015), and it
lets the one-step validation loss fall while rollouts degrade. The valid prediction time is
measured on rollouts, so it is immune to that mismatch. It is the measure of rollout quality
used by the guide's procedure for
[selecting checkpoints](../infrastructure/checkpoint_selection.md).

## Keywords

valid prediction time, VPT, Lyapunov time, predictability horizon, time to decorrelation,
vorticity correlation, autoregressive rollout, exposure bias.

## References

- Bengio, S., Vinyals, O., Jaitly, N. & Shazeer, N. (2015). Scheduled sampling for sequence
  prediction with recurrent neural networks. *NeurIPS* 28. <https://arxiv.org/abs/1506.03099>
- Boffetta, G., Cencini, M., Falcioni, M. & Vulpiani, A. (2002). Predictability: a way to
  characterize complexity. *Physics Reports* 356, 367–474.
  <https://doi.org/10.1016/S0370-1573(01)00025-4>
- Kochkov, D., Smith, J. A., Alieva, A., Wang, Q., Brenner, M. P. & Hoyer, S. (2021). Machine
  learning–accelerated computational fluid dynamics. *Proceedings of the National Academy of
  Sciences* 118, e2101784118. <https://doi.org/10.1073/pnas.2101784118>
- Lippe, P., Veeling, B. S., Perdikaris, P., Turner, R. E. & Brandstetter, J. (2023).
  PDE-Refiner: Achieving accurate long rollouts with neural PDE solvers. *NeurIPS* 36.
  <https://arxiv.org/abs/2308.05732>
- Pathak, J., Hunt, B., Girvan, M., Lu, Z. & Ott, E. (2018). Model-free prediction of large
  spatiotemporally chaotic systems from data: a reservoir computing approach. *Physical
  Review Letters* 120, 024102. <https://doi.org/10.1103/PhysRevLett.120.024102>
