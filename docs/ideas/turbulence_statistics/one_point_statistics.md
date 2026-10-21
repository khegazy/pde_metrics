# One-point statistics and characteristic scales

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

**One-point statistics** are averages of quantities at a single point: mean profiles, the
root-mean-square fluctuation (turbulence intensity), the Reynolds stresses
$R_{ij} = \langle u_i' u_j' \rangle$ built from the fluctuations $u_i'$ about the mean, the
turbulent kinetic energy $\tfrac{1}{2} R_{ii}$, and the mean dissipation rate

$$
\varepsilon = 2 \nu \bigl\langle S_{ij} S_{ij} \bigr\rangle, \qquad
S_{ij} = \tfrac{1}{2} \bigl( \partial_i u_j + \partial_j u_i \bigr) , \tag{1}
$$

with $\nu$ the kinematic viscosity. The idea is to compare each with its reference value. The
averaging set, whether over space, time, an ensemble, or a conditioned region, must be
declared, since the same symbol means different numbers under different averages. For
compressible flow, density-weighted (*Favre*) averages $\tilde u = \langle \rho u \rangle /
\langle \rho \rangle$ are reported alongside ordinary (Reynolds) averages (Lele 1994).

The mean kinetic energy is built as [kinetic_energy](../../metrics/kinetic_energy.md). That
the Reynolds-stress tensor must be a valid covariance is an admissibility condition, covered
on [admissibility checks](../physics_invariants/admissibility_checks.md).

**Characteristic scales** summarise where the energy and the dissipation sit (Pope 2000,
Chapter 6):

- the *integral scale* $L$, the size of the energy-containing eddies;
- the *Taylor microscale* $\lambda$, defined in isotropic turbulence by
  $\varepsilon = 15 \nu u'^2 / \lambda^2$ with $u'$ the root-mean-square velocity of one
  component, which defines the Taylor-scale Reynolds number
  $\mathrm{Re}_\lambda = u' \lambda / \nu$;
- the *Kolmogorov scale* $\eta = (\nu^3 / \varepsilon)^{1/4}$, the size of the smallest
  eddies, where viscosity acts;
- the *Batchelor scale* $\eta_B = \eta\, \mathrm{Sc}^{-1/2}$, the smallest scale of a
  transported scalar whose Schmidt number $\mathrm{Sc}$ (viscosity over scalar diffusivity)
  exceeds one.

Their ratio measures scale separation, $L / \eta \sim \mathrm{Re}^{3/4}$, and the product of
the largest resolved wavenumber with $\eta$ measures whether a grid resolves the dissipation
range. Comparing predicted and reference scales checks both, and the scales are the
normalisations that other pages in this theme need: $\varepsilon$ for the
[four-fifths law](four_fifths_law.md) and $\mathrm{Re}_\lambda$ for the
[velocity-derivative skewness](derivative_skewness.md).

## Pitfalls

- These are the archetypal degenerate statistics: a prediction can match the mean and still
  have the wrong fluctuations, or match the second moments and have the wrong structure.
- Every quantity on this page is a first- or second-order statistic, and the scales follow
  from the energy spectrum and $\nu$. A Gaussian field with the reference's mean and
  second-order statistics therefore matches all of them, whatever its structure, which is
  the weakness the [gaussian_impostor](../../degradations/gaussian_impostor.md) exists to
  expose. They belong beside the third-order tests of this theme, not in place of them.
- They are integrals over the domain and so insensitive to where an error sits.
- Equation (1) is biased low when the grid does not resolve the dissipation range.

## Rationale

*From the field guide; the team has not yet set a priority.* These statistics are cheap,
standard first-order checks, and the scales are the reference against which resolution and
the other statistics of this theme are judged. They are not in themselves a test of
turbulent structure.

## Keywords

Reynolds stresses, turbulence intensity, Favre average, dissipation rate, integral scale,
Taylor microscale, Kolmogorov scale, Batchelor scale, scale separation.

## References

- Lele, S. K. (1994). Compressibility effects on turbulence. *Annual Review of Fluid
  Mechanics* 26, 211–254. <https://doi.org/10.1146/annurev.fl.26.010194.001235>
- Pope, S. B. (2000). Turbulent Flows. *Cambridge University Press*.
  <https://doi.org/10.1017/CBO9780511840531>
