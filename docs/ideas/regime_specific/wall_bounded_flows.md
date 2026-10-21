# Wall-bounded flow diagnostics

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Near a solid wall, turbulence is organised by the friction the wall exerts on the flow. The
standard diagnostics measure that friction and the velocity profile it sets up, and they are
also the quantities an engineer needs.

- **Friction velocity and wall units.** The wall shear stress is
  $\tau_w = \mu\,\partial u/\partial y$ at the wall, where $\mu$ is the dynamic viscosity, $u$
  the velocity parallel to the wall and $y$ the distance from it. The friction velocity is
  $u_\tau = \sqrt{\tau_w/\rho}$, with $\rho$ the density. Distances and velocities measured in
  wall units are $y^+ = y\,u_\tau/\nu$ and $u^+ = u/u_\tau$, where $\nu = \mu/\rho$ is the
  kinematic viscosity.
- **Skin friction and integrated forces.** The skin-friction coefficient is
  $C_f = \tau_w / (\tfrac12\rho U_\infty^2)$, where $U_\infty$ is the free-stream velocity.
  Integrating the wall stress and pressure over a body gives its drag and lift.
- **Separation.** The location where the flow separates from the wall, which is where the
  wall shear stress changes sign.

**The logarithmic law of the wall.** Between the viscous layer at the wall and the outer
flow, the mean velocity follows

$$
u^+ = \frac{1}{\kappa}\ln y^+ + B \tag{1}
$$

with the von Kármán coefficient $\kappa$ and an additive constant $B$. Here $\kappa$ is not
universal: Nagib and Chauhan (2008) find $\kappa \approx 0.384$ in boundary layers with zero
pressure gradient, consistent with Österlund et al. (2000), but conclude from a reanalysis of
pipe-flow data that $\kappa \approx 0.41$ describes pipe flow better. A comparison of a
prediction against (1) therefore uses the constant appropriate to the flow. Computing $u_\tau$
from the predicted wall stress and testing the predicted mean profile against (1) checks the
prediction's own consistency, with no reference field.

## Pitfalls

- Because $\kappa$ depends on the flow, forcing a single value onto every flow biases a
  comparison across flows.
- The wall stress needs the velocity gradient at the wall, which is accurate only when the
  near-wall layer is resolved.
- These diagnostics apply only to datasets with walls.

## Rationale

*From the field guide; the team has not yet set a priority.* These are the engineering
quantities of interest for wall-bounded flow and the standard diagnosis of the near-wall
region. The logarithmic law with $u_\tau$ taken from the predicted wall stress also gives a
reference-free consistency check.

## Keywords

friction velocity, wall units, law of the wall, logarithmic overlap region, von Kármán
coefficient, skin friction coefficient, flow separation.

## References

- Nagib, H. M. & Chauhan, K. A. (2008). Variations of von Kármán coefficient in canonical
  flows. *Physics of Fluids* 20, 101518. <https://doi.org/10.1063/1.3006423>
- Österlund, J. M., Johansson, A. V., Nagib, H. M. & Hites, M. H. (2000). A note on the overlap
  region in turbulent boundary layers. *Physics of Fluids* 12, 1–4.
  <https://doi.org/10.1063/1.870250>
