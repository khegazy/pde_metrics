# Variable-density mixing

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

When a heavy and a light fluid meet at an interface that is accelerated, the interface becomes
unstable and a turbulent mixing layer grows between them. Under steady acceleration this is the
Rayleigh–Taylor instability; under the impulsive acceleration of a passing shock it is the
Richtmyer–Meshkov instability. The regime is not reducible to shock and turbulence metrics,
because what matters is how fast the layer grows, how thoroughly the fluids mix at the
molecular level, and how the layer's anisotropy evolves.

- **Atwood number and mixing width.** The density contrast is measured by the Atwood number
  $A = (\rho_h - \rho_l)/(\rho_h + \rho_l)$, with $\rho_h$ and $\rho_l$ the heavy and light
  densities. With $f_1$ and $f_2$ the volume fractions of the two fluids, $z$ the direction of
  acceleration and $\langle\cdot\rangle$ an average over planes normal to $z$, the mixing
  width is $W(t) = \int \langle f_1\rangle\langle f_2\rangle\,dz$.
- **Growth laws.** A Rayleigh–Taylor layer grows quadratically in time,
  $W \sim \alpha A g t^2$ with $g$ the acceleration, and the coefficient $\alpha$ was compared
  across codes by the Alpha-Group collaboration (Dimonte et al. 2004). A Richtmyer–Meshkov
  layer grows as a power law, $W \sim t^\theta$, with the $\theta$-group consensus
  $\theta = 0.292 \pm 0.009$ for the narrowband case; the exponent decays slowly in time
  (Thornber et al. 2017).
- **Early-time growth.** Before the layer is turbulent, linear theory predicts the growth of
  each perturbation. In the impulsive model for the Richtmyer–Meshkov instability, a
  perturbation of wavenumber $k$ and initial amplitude $a_0$ grows at the rate
  $\dot a = k\,\Delta u\,A\,a_0$, where $\Delta u$ is the velocity jump imparted by the shock
  and $A$ and $a_0$ take their post-shock values (Richtmyer 1960; Meshkov 1969). Comparing
  early-time growth rates tests the linear physics directly, which the root-mean-square error
  of the field does not isolate. Zhou (2017) reviews both instabilities and the turbulence and
  mixing they induce.
- **Molecular mixing fraction.** The ratio $\Theta$ defined in (1) below distinguishes fluids
  that are merely stirred together, interleaved without mixing at the molecular level
  ($\Theta = 0$), from fluids that are molecularly mixed ($\Theta \to 1$).
  For the narrowband Richtmyer–Meshkov case the late-time value is
  $\Theta = 0.792 \pm 0.014$ (Thornber et al. 2017). Two fields with the same root-mean-square
  error in density can have very different $\Theta$.
- **Variable-density second moments.** Two quantities that variable-density turbulence models
  such as the BHR closure (Besnard et al. 1992) are built to predict: the turbulent mass flux
  $a_i = \bar\rho^{-1}\langle\rho' u_i'\rangle = \tilde u_i - \bar u_i$, which is the
  difference between the density-weighted (Favre) mean velocity $\tilde u_i$ and the plain
  mean $\bar u_i$, and the density–specific-volume covariance
  $b = -\langle\rho'\,(1/\rho)'\rangle \ge 0$, which is nonnegative because density and its
  reciprocal always vary in opposite directions (Livescu 2013). Dimotakis (2000) describes the
  mixing transition, a Reynolds-number threshold beyond which turbulent mixing changes
  character; *added during conversion, not from the field guide or the team:* simulations on opposite sides of it are
  not expected to agree on these moments.
- **Persistent anisotropy.** The layer does not return to isotropy. In the $\theta$-group data
  the latest time has "between 49% and 66% higher kinetic energy in the shock parallel
  direction compared to perpendicular" (Thornber et al. 2017, abstract), so the partition of
  kinetic energy among directions is scored, not only its total.
- **Mixing geometry.** The finite-time Lyapunov exponent (FTLE) is the rate at which nearby
  fluid particles separate over a finite time window. Its ridges mark Lagrangian coherent
  structures, the material surfaces that organise the mixing (Shadden et al. 2005; Haller
  2015). Ridges extracted from the prediction and the reference can be compared with the
  surface distances under
  [distance between extracted shock sets](../../metrics/shock_set_distance.md).

The molecular mixing fraction is

$$
\Theta = \frac{\int \langle f_1 f_2 \rangle\,dz}{\int \langle f_1\rangle\langle f_2\rangle\,dz}
\tag{1}
$$

which is 0 where the two volume fractions never overlap within a cell, and 1 where their
product equals the product of their plane averages, as it does when the fluids are uniformly
mixed across each plane.

Because different physics dominates at different times, the diagnostics are tagged by phase:

1. **Linear phase:** the error in the growth rate.
2. **Nonlinear phase:** the positions of the fronts and the growth exponents.
3. **Turbulent phase:** $\Theta$, $a_i$, $b$ and the anisotropy.
4. **Shock-coupled phase:** the
   [jump conditions](../shock_geometry/shock_front_error.md),
   [entropy production](../physics_invariants/entropy_production.md) and the
   [corrugation of the shock](../shock_geometry/shock_turbulence_interaction.md).
5. **Structure:** FTLE ridges and the
   [Minkowski functionals](../topology/minkowski_functionals.md).

## Pitfalls

- The growth rate alone is blind to the internal state of the layer: a model can match $\theta$
  while making the layer isotropic, which is the wrong physics.
- Because the Richtmyer–Meshkov exponent decays slowly in time, a comparison of $\theta$ is
  meaningful only over a declared time window.

## Rationale

*From the field guide; the team has not yet set a priority.* These diagnostics separate stirred
from molecularly mixed states and expose anisotropy that the growth rate alone cannot see.
Published collaborations have measured several of them across many codes, which supplies
targets with stated uncertainties.

## Keywords

Rayleigh–Taylor instability, Richtmyer–Meshkov instability, Atwood number, mixing width,
molecular mixing fraction, turbulent mass flux, density–specific-volume covariance, BHR model,
mixing transition, finite-time Lyapunov exponent, Lagrangian coherent structures.

## References

- Besnard, D., Harlow, F. H., Rauenzahn, R. M. & Zemach, C. (1992). Turbulence transport
  equations for variable-density turbulence and their relationship to two-field models. Los
  Alamos National Laboratory report LA-12303-MS. <https://doi.org/10.2172/7271399>
- Dimonte, G. et al. (2004). A comparative study of the turbulent Rayleigh–Taylor instability
  using high-resolution three-dimensional numerical simulations: The Alpha-Group
  collaboration. *Physics of Fluids* 16, 1668–1693. <https://doi.org/10.1063/1.1688328>
- Dimotakis, P. E. (2000). The mixing transition in turbulent flows. *Journal of Fluid
  Mechanics* 409, 69–98. <https://doi.org/10.1017/S0022112099007946>
- Haller, G. (2015). Lagrangian coherent structures. *Annual Review of Fluid Mechanics* 47,
  137–162. <https://doi.org/10.1146/annurev-fluid-010313-141322>
- Livescu, D. (2013). Numerical simulations of two-fluid turbulent mixing at large density
  ratios and applications to the Rayleigh–Taylor instability. *Philosophical Transactions of
  the Royal Society A* 371, 20120185. <https://doi.org/10.1098/rsta.2012.0185>
- Meshkov, E. E. (1969). Instability of the interface of two gases accelerated by a shock wave.
  *Fluid Dynamics* 4, 101–104. <https://doi.org/10.1007/BF01015969>
- Richtmyer, R. D. (1960). Taylor instability in shock acceleration of compressible fluids.
  *Communications on Pure and Applied Mathematics* 13, 297–319.
  <https://doi.org/10.1002/cpa.3160130207>
- Shadden, S. C., Lekien, F. & Marsden, J. E. (2005). Definition and properties of Lagrangian
  coherent structures from finite-time Lyapunov exponents in two-dimensional aperiodic flows.
  *Physica D* 212, 271–304. <https://doi.org/10.1016/j.physd.2005.10.007>
- Thornber, B. et al. (2017). Late-time growth rate, mixing, and anisotropy in the multimode
  narrowband Richtmyer–Meshkov instability: The $\theta$-group collaboration. *Physics of
  Fluids* 29, 105107. <https://doi.org/10.1063/1.4993464>
- Zhou, Y. (2017). Rayleigh–Taylor and Richtmyer–Meshkov instability induced flow, turbulence,
  and mixing. I. *Physics Reports* 720–722, 1–136.
  <https://doi.org/10.1016/j.physrep.2017.07.005>
