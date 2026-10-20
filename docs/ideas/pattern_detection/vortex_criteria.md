# Vortex criteria: Q, λ₂ and Okubo–Weiss

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

These are the established vortex-identification criteria. Each is computed from the velocity
gradient at a point, split into its symmetric part $S$ (the strain rate) and its antisymmetric
part $\Omega$ (the rotation rate), and each marks a point as inside a vortex when rotation
dominates strain by its own measure.

- The *$Q$-criterion* marks points where $Q = \tfrac{1}{2}\left(\|\Omega\|^2 - \|S\|^2\right)$
  is positive.
- The *$\lambda_2$ criterion* marks points where the middle eigenvalue $\lambda_2$ of
  $S^2 + \Omega^2$ is negative.
- The *Okubo–Weiss parameter*, used for two-dimensional flows, compares the squared strain with
  the squared vorticity and marks points where the vorticity dominates.

## Precedent

These criteria are the established tools of the vortex-identification literature, and
$\lambda_2$ in particular is due to Jeong and Hussain (1995).

## Pitfalls

- All of them are threshold dependent: a point counts as inside a vortex only above or below
  a chosen cut.
- None of them is frame invariant, meaning that the answer can change when the flow is viewed
  from a rotating or accelerating frame of reference.

## Rationale

*The team's judgement.* Medium priority: the criteria are cheap and familiar, and they provide
a sensible baseline against which to judge whether the [winding angle](winding_angle.md) adds
anything.

## References

- Jeong, J. & Hussain, F. (1995). On the identification of a vortex. *Journal of Fluid
  Mechanics* 285, 69–94. <https://doi.org/10.1017/S0022112095000462>
