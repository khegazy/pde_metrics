# Vortex stretching and energy budgets

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

In three-dimensional flow, vortex lines are stretched by the velocity gradient, and the
stretching amplifies vorticity. In the equation for the vorticity $\boldsymbol{\omega}$ the
stretching term is $\omega_j \partial_j u_i$. Splitting the velocity gradient into its
symmetric part $S_{ij}$ (the strain rate) and antisymmetric part $\Omega_{ij}$ (the rotation
rate), the antisymmetric part contributes $\Omega_{ij}\omega_j = -\tfrac{1}{2}
(\boldsymbol{\omega} \times \boldsymbol{\omega})_i = 0$, so only the strain acts. Multiplying by
$\omega_i$ and averaging gives the mean *enstrophy production*

$$
P_\omega = \bigl\langle \omega_i S_{ij} \omega_j \bigr\rangle . \tag{1}
$$

In three-dimensional turbulence $P_\omega$ is positive: on average vortex lines are stretched
rather than compressed. The alignment behind this is not the simple one. Vorticity aligns
preferentially with the *intermediate* eigenvector of the strain-rate tensor, and in intense
vorticity it tends to be weakly orthogonal to the most extensive one; yet the dominant
contribution to producing large enstrophy still comes from the most extensive eigendirection
(Buaria, Bodenschatz and Pumir 2020). For a Gaussian field it is zero in expectation, since it is a third moment of the
velocity gradient. The idea's first part is a sign test on the prediction: $P_\omega > 0$,
with no reference needed, and where a reference exists a comparison of the two values.

The second part is budget closure. For homogeneous, incompressible flow the mean enstrophy
$\tfrac{1}{2}\langle |\boldsymbol{\omega}|^2 \rangle$ (built as
[enstrophy](../../metrics/enstrophy.md)) evolves as

$$
\frac{d}{dt} \tfrac{1}{2} \bigl\langle |\boldsymbol{\omega}|^2 \bigr\rangle
= P_\omega - 2 \nu P , \tag{2}
$$

where $\nu$ is the kinematic viscosity and $P = \tfrac{1}{2} \langle |\nabla
\boldsymbol{\omega}|^2 \rangle$ is the palinstrophy (built as
[palinstrophy](../../metrics/palinstrophy.md)); the viscous term follows from integrating
$\nu\, \boldsymbol{\omega} \cdot \nabla^2 \boldsymbol{\omega}$ by parts, and any forcing adds
its own term. In statistically stationary flow the left side vanishes, so stretching must
balance viscous destruction. The same test applies to the turbulent kinetic energy:
production must balance dissipation plus transport. A prediction whose terms do not balance
is losing or gaining energy or enstrophy through something other than the equations, for
example hidden numerical or learned dissipation.

## Pitfalls

- In planar two-dimensional flow the vorticity points out of the plane and the strain has no
  out-of-plane component, so $P_\omega$ is identically zero and Equation (2) loses its
  production term. The sign test is a three-dimensional test only.
- The compressible vorticity equation has further terms, from dilatation and from
  misaligned density and pressure gradients, which must enter the budget.
- Budgets need averaging windows long enough for the time derivative and the transport terms
  to converge.
- Every term is gradient-heavy and so sensitive to resolution.

## Rationale

*From the field guide; the team has not yet set a priority.* The sign of $P_\omega$ is a
binary, physics-anchored check that a Gaussian-like prediction fails, and it needs no
reference. Budget closure catches dissipation that the model introduces without the
equations asking for it, and it reuses quantities that are already built.

## Keywords

vortex stretching, enstrophy production, vorticity–strain alignment, enstrophy budget, TKE
budget, palinstrophy.

## References

- Buaria, D., Bodenschatz, E. & Pumir, A. (2020). Vortex stretching and enstrophy production
  in high Reynolds number turbulence. *Physical Review Fluids* 5, 104602.
  <https://arxiv.org/abs/2006.01312>
