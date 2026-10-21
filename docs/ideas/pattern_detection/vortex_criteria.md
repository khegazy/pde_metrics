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
  the squared vorticity and marks points where the vorticity dominates. For a planar velocity
  $(u, v)$ it is $W = s_n^2 + s_s^2 - \omega^2$, with normal strain
  $s_n = \partial_x u - \partial_y v$, shear strain $s_s = \partial_x v + \partial_y u$ and
  vorticity $\omega = \partial_x v - \partial_y u$, and vortices are where $W < 0$. In
  two dimensions $W = -4Q$, so this criterion and the $Q$-criterion mark the same points.
- The *swirling strength* $\lambda_{ci}$ is the imaginary part of the complex-conjugate pair of
  eigenvalues of the velocity gradient, where such a pair exists; it marks points where it is
  positive, or above a threshold, and its size measures how fast the local flow spirals
  (Zhou et al. 1999).

$Q$ is also one of the two invariants whose joint distribution is the subject of
[the Q and R invariants page](../turbulence_statistics/qr_invariants.md).

## Precedent

These criteria are the established tools of the vortex-identification literature, and
$\lambda_2$ in particular is due to Jeong and Hussain (1995). Chakraborty, Balachandar and
Adrian (2005) compare the local criteria, including swirling strength, and set out the
relationships between them.

## Pitfalls

- All of them are threshold dependent: a point counts as inside a vortex only above or below
  a chosen cut.
- None of them is frame invariant, meaning that the answer can change when the flow is viewed
  from a rotating frame of reference. A frame that translates, even with acceleration, adds
  the same velocity everywhere, which leaves the velocity gradient and so every criterion
  here unchanged; rotation of the frame is what changes them.
- Together, the arbitrary threshold and the frame dependence make a comparison between
  models fragile: two predictions can differ in their vortex counts because of the cut
  rather than the flow, which is why the threshold must be fixed by the evaluator and never
  tuned per model.

## Rationale

*The team's judgement.* Medium priority: the criteria are cheap and familiar, and they provide
a sensible baseline against which to judge whether the [winding angle](winding_angle.md) adds
anything.

## References

- Chakraborty, P., Balachandar, S. & Adrian, R. J. (2005). On the relationships between
  local vortex identification schemes. *Journal of Fluid Mechanics* 535, 189–214.
  <https://doi.org/10.1017/s0022112005004726>
- Jeong, J. & Hussain, F. (1995). On the identification of a vortex. *Journal of Fluid
  Mechanics* 285, 69–94. <https://doi.org/10.1017/S0022112095000462>
- Zhou, J., Adrian, R. J., Balachandar, S. & Kendall, T. M. (1999). Mechanisms for generating
  coherent packets of hairpin vortices in channel flow. *Journal of Fluid Mechanics* 387,
  353–396. <https://doi.org/10.1017/s002211209900467x>
