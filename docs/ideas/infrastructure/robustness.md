# Robustness against the equations' own sensitivity

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Perturb a surrogate's input slightly and measure how much its output changes. Three kinds of
perturbation are standard.

1. **Local Lipschitz estimate.** The largest ratio of output change to input change over
   small perturbations $\delta$ of an input $x$,
   $\max_{\|\delta\| \le \epsilon} \|f(x + \delta) - f(x)\| / \|\delta\|$, for the surrogate
   $f$. It is estimated by sampling directions or from the norm of the surrogate's Jacobian.
2. **Adversarial perturbation.** The perturbation within a small ball that changes the output
   the most. The fast gradient sign method takes one step of size $\epsilon$ along the sign
   of the gradient of the loss with respect to the input (Goodfellow, Shlens & Szegedy 2015).
3. **Noise robustness.** Random perturbations of a declared amplitude and spectrum.

The point of this idea is the yardstick. Machine-learning robustness usually reads a smaller
response as better, but the governing equations have a sensitivity of their own: a chaotic
flow amplifies a small perturbation, and a strongly damped one suppresses it. The surrogate's
response is therefore judged *against the response of the equations* to the same
perturbation. A surrogate that responds much more strongly than the equations is fragile; one
that responds much less has smoothed away dynamics the equations would amplify. One way to
make the comparison concrete (*added during conversion, not from the field guide or the
team*) is the ratio

$$
\frac{\| f(x + \delta) - f(x) \|}{\| \mathcal{S}(x + \delta) - \mathcal{S}(x) \|}, \tag{1}
$$

where $\mathcal{S}$ is a trusted solver advanced over the same horizon as the surrogate. A
ratio near one means the surrogate is as sensitive as the equations.

## Pitfalls

- Equation (1) needs a trusted solver, such as the one planned under the
  [reference and solver predictor](degradation_ladder_reference.md).
- An adversarial perturbation may not be a physically admissible state, for example one that
  breaks a divergence-free constraint. The response to it then says little about the
  surrogate's behaviour on real inputs, so perturbations should be restricted to admissible
  states.
- Sampling directions gives only a lower bound on the local Lipschitz constant, since the
  worst direction may not be sampled.
- Over long horizons both the surrogate and a chaotic solver decorrelate from the
  unperturbed trajectory, and the ratio saturates. The comparison is informative at horizons
  shorter than the [valid prediction time](../dynamics/valid_prediction_time.md).

## Rationale

*From the field guide; the team has not yet set a priority.* The guide includes robustness
with goal-oriented error and calibration among the properties that decide whether a
surrogate can be deployed, and insists that sensitivity be judged against the physical
sensitivity of the equations: too sensitive is fragile, too insensitive means smoothed-away
dynamics. The second failure is the over-smoothing that this project's metrics target from
the output side; this idea detects it from the input side.

## Keywords

local Lipschitz constant, adversarial robustness, fast gradient sign method, noise
robustness, sensitivity analysis, Lyapunov exponent.

## References

- Goodfellow, I. J., Shlens, J. & Szegedy, C. (2015). Explaining and harnessing adversarial
  examples. *International Conference on Learning Representations*.
  <https://arxiv.org/abs/1412.6572>
