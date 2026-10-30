# Admissibility checks

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

An admissibility condition is a property that every physical solution of the governing
equations has, whatever its initial state. Each check below is computed from the prediction
alone, with no reference field, and a prediction that violates one is non-physical. The
checks are reported as separate flags and counts rather than folded into a weighted average
with other errors, where a large violation could be offset by small errors elsewhere.

- **Positivity.** Density and pressure must be positive in every cell. Report the number of
  cells where either is not, and the most negative value reached.
- **Finite values and blow-up.** Flag any cell that holds a NaN (not-a-number) or an infinite
  value, and any rollout whose field norm grows without bound.
- **Conservation drift.** For a conservation law $\partial_t U + \nabla\cdot F(U) = S$ on a
  periodic or closed domain $\Omega$ with no source $S$, the totals
  $\int_\Omega U\,d\mathbf{x}$ of mass, momentum and energy do not change in time. The
  conservation-budget error $E_{\text{cons}}(t)$ tracks the change of each total from its
  initial value over a rollout. Each total is compared against a declared scale, because a
  total can be zero: the net momentum of a periodic box usually is, so dividing by the initial
  total is undefined. On an open domain the budget must include the fluxes through the
  boundaries and the sources. The cell-by-cell version of the same balance is the
  [residual of the equations in weak form](weak_residual.md), and summing that residual over
  all cells gives exactly this budget, because the fluxes through interior faces cancel.
- **Divergence error.** In incompressible flow the velocity $\mathbf{u}$ must satisfy
  $\nabla\cdot\mathbf{u} = 0$, and the pressure acts as the Lagrange multiplier that enforces
  this constraint (Chorin 1968). A norm of $\nabla\cdot\hat{\mathbf{u}}$, where
  $\hat{\mathbf{u}}$ is the predicted velocity, measures how far the prediction departs from
  it.
- **Reynolds-stress realizability.** The Reynolds stress
  $R_{ij} = \langle u_i' u_j' \rangle$, the covariance of the velocity fluctuations $u_i'$, is
  a covariance matrix, so it must be symmetric with minimum eigenvalue
  $\lambda_{\min} \ge 0$ (checked with a slack scaled to the size of the stress), and must
  satisfy the Schwarz inequality $R_{ij}^2 \le R_{ii} R_{jj}$ (no summation over repeated
  indices here). Equivalently, the invariants of the anisotropy tensor
  $b_{ij} = R_{ij}/R_{kk} - \delta_{ij}/3$ must lie inside the region of realizable states,
  drawn either as the Lumley triangle (Lumley and Newman 1977) or as the barycentric map
  (Banerjee et al. 2007). A covariance computed from the prediction's own fluctuations
  satisfies all of this automatically, so the check constrains a model only when the model
  predicts the stress directly, as a turbulence closure does.
- **Species bounds.** In a reacting or multi-species flow the mass fraction $Y_k$ of each
  species must satisfy $0 \le Y_k \le 1$ and $\sum_k Y_k = 1$, and the temperature must be
  positive. These are discussed with the other
  [reacting-flow diagnostics](../regime_specific/reacting_flows.md).

Three further conditions of the same kind have their own pages: the
[residual of the equations in weak form](weak_residual.md), the sign of
[entropy production](entropy_production.md) in shocked flow, and
[equivariance under Galilean boosts and rotations](equivariance_tests.md). Where helicity, or
enstrophy in two dimensions, is an invariant of the inviscid equations, its drift is a check
of the same kind; see [helicity, potential vorticity and information transfer across
scales](../turbulence_statistics/inviscid_invariants.md).

## Pitfalls

- These conditions are necessary and not sufficient. An over-dissipated, near-laminar field
  satisfies all of them, and so does a constant field. They are therefore paired with
  reference-free quantities that such a field cannot reproduce, such as the
  [four-fifths law](../turbulence_statistics/four_fifths_law.md) and the
  reference-free flux constancy on [energy-transfer checks](../turbulence_statistics/energy_transfer_checks.md), which pin the
  amplitude and slope of the inertial range.
- A reference-free score is trusted where no reference exists only after it has been checked,
  by Spearman rank correlation against the true error, on cases where a reference does exist.
- Every tolerance, such as the slack on $\lambda_{\min}$ or the drift allowed before a flag is
  raised, is fixed once by the evaluator and never tuned per model.

## Rationale

*From the field guide; the team has not yet set a priority.* These checks catch catastrophic
non-physical predictions, such as negative density or pressure, blow-up and mass leakage, that
no soft error can excuse. They cannot be satisfied by matching statistics, they need no
reference, and so they stay meaningful after a rollout has decorrelated from every reference
trajectory. They are also cheap, and give a vector of flags that a procedure for
[selecting checkpoints by rollout](../infrastructure/checkpoint_selection.md) can consult
before comparing any scores.

## Keywords

positivity preservation, conservation drift, divergence-free constraint, Reynolds-stress
realizability, Lumley triangle, barycentric map, anisotropy invariants, mass-fraction bounds.

## References

- Banerjee, S., Krahl, R., Durst, F. & Zenger, C. (2007). Presentation of anisotropy
  properties of turbulence, invariants versus eigenvalue approaches. *Journal of Turbulence*
  8, N32. <https://doi.org/10.1080/14685240701506896>
- Chorin, A. J. (1968). Numerical solution of the Navier–Stokes equations. *Mathematics of
  Computation* 22, 745–762. <https://doi.org/10.1090/S0025-5718-1968-0242392-2>
- Lumley, J. L. & Newman, G. R. (1977). The return to isotropy of homogeneous turbulence.
  *Journal of Fluid Mechanics* 82, 161–178. <https://doi.org/10.1017/S0022112077000585>
