# Residual of the equations in weak form

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

A residual measures how far a predicted field is from satisfying the governing equations.
The *strong-form* residual, obtained by substituting the field into the differential
operator, is meaningless at a discontinuity. Solutions with shocks are weak solutions: they
satisfy the equations only after integration over cells or against test functions, and their
derivatives are distributions rather than functions.

The *finite-volume weak residual* is the cell-average update plus the flux balance across the
cell faces minus the source term. It remains valid at shocks, and it is the residual that
should be reported. For a conservation law $\partial_t U + \nabla\cdot F(U) = S$, its value on
cell $K$ between time levels $n$ and $n+1$ is

$$
R^n_K = \frac{|K|}{\Delta t}\big(U^{n+1}_K - U^n_K\big) + \sum_{f} |f|\,\hat F_f - |K|\,S_K
\tag{1}
$$

where $|K|$ is the cell's volume, $U_K$ its cell average, $\Delta t$ the time step, the sum
runs over the faces $f$ of the cell, $|f|$ is a face's area, $\hat F_f$ is the numerical flux
leaving the cell through that face, and $S_K$ is the cell average of the source. The numerical
flux and the time level at which it is evaluated are declared as part of the metric, since the
residual depends on both.

Summing (1) over every cell cancels the fluxes through interior faces, each of which leaves
one cell and enters its neighbour. What remains is the global conservation budget: the change
of $\int_\Omega U\,d\mathbf{x}$ against the boundary fluxes and sources. Its drift over a
rollout, $E_{\text{cons}}(t)$, is the conservation check among the
[admissibility checks](admissibility_checks.md).

## Precedent

Strong-form residuals are the training signal of physics-informed neural networks (Raissi et
al. 2019), and they inherit the problem at shocks described above. Two training-side
counterparts keep the residual valid there: weak physics-informed neural networks, discussed
under [signed entropy production](entropy_production.md), and loss functions built on
Godunov's method, the finite-volume scheme that computes each face flux from the solution of a
local Riemann problem (Cassia and Kerswell 2025).

## Pitfalls

- A small residual is necessary and not sufficient: an over-dissipated, near-laminar field can
  satisfy the equations closely. See the [admissibility checks](admissibility_checks.md).
- Formula (1) needs consecutive states one solver time step apart. A prediction stored only
  every few steps gives an update in (1) that matches no single step of any scheme.

## Rationale

*The team's judgement.* High priority: the residual is reference-free, cheap, and always
available.

## References

- Cassia, R. & Kerswell, R. (2025). Godunov loss functions for modelling of hyperbolic
  conservation laws. *Computer Methods in Applied Mechanics and Engineering* 437, 117782.
  <https://doi.org/10.1016/j.cma.2025.117782>
- Raissi, M., Perdikaris, P. & Karniadakis, G. E. (2019). Physics-informed neural networks: A
  deep learning framework for solving forward and inverse problems involving nonlinear partial
  differential equations. *Journal of Computational Physics* 378, 686–707.
  <https://doi.org/10.1016/j.jcp.2018.10.045>
