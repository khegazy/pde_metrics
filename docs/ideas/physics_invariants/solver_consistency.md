# Consistency with one step of a trusted solver

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Take the model's predicted field, advance it by one small step using a trusted numerical
solver, and measure how far the model's own next state lies from the solver's. With
$\hat u_n$ the prediction at step $n$ and $\mathcal{S}_{\Delta t}$ the solver advancing a
state by one time step $\Delta t$, the normalised drift is

$$
r_n = \frac{\big\|\hat u_{n+1} - \mathcal{S}_{\Delta t}(\hat u_n)\big\|_2}
{\big\|\hat u_n\big\|_2} \tag{1}
$$

This is the evaluation-side mirror of solver-in-the-loop training, in which a numerical solver
is part of the training loop (Um et al. 2020). It requires no ground truth, it is local in
time, and it remains meaningful long after the predicted trajectory has decorrelated from any
reference. It flags states that the governing equations would immediately reject. For shocked
flows the closely related cell-level form is the
[residual of the equations in weak form](weak_residual.md), which stays valid at
discontinuities.

It needs a trusted solver in the repository. The planned
[solver predictor for the degradation ladder](../infrastructure/degradation_ladder_reference.md),
a Boltzmann solver, would provide one.

## Pitfalls

- A small one-step residual can still conceal slow secular drift, an error that accumulates
  steadily over many steps. Pair this metric with conservation drift measured over the full
  rollout, one of the [admissibility checks](admissibility_checks.md).
- The solver must be consistent with the equations the model is meant to approximate, and must
  run at the model's resolution.
- *Added during conversion, not from the field guide or the team:* the denominator of (1) includes the mean state. For
  a field with a large mean, such as density or pressure, $r_n$ can be small even when the
  fluctuations are badly wrong; normalising by the norm of the fluctuations avoids this.

## Rationale

*The team's judgement.* High priority: like the
[residual of the equations in weak form](weak_residual.md), it is reference-free, and it is
nearly free once a trusted solver is in the repository.

## References

- Um, K., Brand, R., Fei, Y., Holl, P. & Thuerey, N. (2020). Solver-in-the-loop: learning from
  differentiable physics to interact with iterative PDE-solvers. *Advances in Neural
  Information Processing Systems* (NeurIPS). <https://arxiv.org/abs/2007.00016>
