# Spectral energy flux

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The energy spectrum says how much energy sits at each scale; the spectral energy flux says
how fast energy moves between scales. Two fields can have the same spectrum while one carries
a cascade and the other does not, so matching the [energy spectrum](../../metrics/spectrum_l2.md)
does not imply matching the transfer.

For incompressible flow, the nonlinear term of the Navier–Stokes equations changes the
energy held in the Fourier modes inside a sphere of radius $k$ at the rate
$-\int_{|\mathbf{k}'| < k} \mathrm{Re}\bigl[\hat{\mathbf{u}}^* \cdot
\widehat{(\mathbf{u} \cdot \nabla \mathbf{u})}\bigr] \, d\mathbf{k}'$; the pressure term does
no work there because the velocity is divergence-free. The flux through wavenumber $k$ is the
rate at which nonlinearity removes energy from those modes:

$$
\Pi(k) = \int_{|\mathbf{k}'| < k} \mathrm{Re}\Bigl[ \hat{\mathbf{u}}^*(\mathbf{k}') \cdot
\widehat{(\mathbf{u} \cdot \nabla \mathbf{u})}(\mathbf{k}') \Bigr] \, d\mathbf{k}' , \tag{1}
$$

where a hat denotes the Fourier transform and the star the complex conjugate. With this sign,
$\Pi > 0$ means energy moving from large scales to small ones, and *backscatter* means
$\Pi < 0$.

$\Pi$ is a triple correlation of the velocity, a sum over interacting wavenumber triads of
the [bispectrum](../basis_decompositions/bispectrum.md), so its expected value is zero for a
Gaussian field. A Gaussian field with a perfect inertial-range spectrum carries no cascade.

The idea has three forms.

1. **Against a reference.** Report the error of the curve $\Pi(k)$ across the inertial range,
   and the *backscatter sign fraction*: the fraction of wavenumbers at which the prediction
   has $\Pi < 0$ where the reference has $\Pi > 0$. Sign errors flag spurious backscatter,
   for example from blurring.
2. **Without a reference.** In the inertial range the flux should be constant and equal to
   the dissipation rate, $\Pi(k) \approx \hat\varepsilon$, with $\hat\varepsilon$ estimated
   from the prediction as on [the four-fifths law page](four_fifths_law.md). A prediction
   with nonzero $\hat\varepsilon$ but $\Pi(k) \approx 0$ dissipates energy that no cascade
   supplies, which is the signature of a Gaussian-like state.
3. **As a field.** Coarse-graining, meaning filtering the velocity at a scale $\ell$, gives
   a flux at every point rather than one number per wavenumber. The distributions of that
   local flux in the prediction and the reference can then be compared with the 1-Wasserstein
   distance, as on
   built [increment_w1_by_separation](../../metrics/increment_w1_by_separation.md).

**Compressible and variable-density flow.** When density varies, the pressure does work and
kinetic energy can be exchanged with internal energy, so Equation (1) is incomplete. The
coarse-graining approach of Aluie writes the budget of the kinetic energy at scales larger
than $\ell$ with three exchange terms. Two of them move energy across scale $\ell$: the
deformation work $\Pi_\ell$, done by the large-scale strain on the small-scale stress, and the
baropycnal work $\Lambda_\ell$, which couples large-scale pressure gradients with small-scale
mass flux. The third, the large-scale pressure dilatation $PD_\ell$, does not move energy
between scales; it converts kinetic into internal energy (Aluie 2011; Aluie 2013). In
subsonic and transonic simulations, Aluie, Li and Li (2012) find that mean pressure
dilatation acts mainly at large scales, so that beyond a transitional range of scales the
kinetic-energy cascade is conservative. That is what allows a flux-constancy check to be
carried over to compressible turbulence; their simulations do not establish it for the
supersonic, shocklet-populated regime. Comparing the three terms separately shows whether a
prediction moves energy by the right mechanism.

**Learned closures.** For a surrogate that predicts a filtered field with a learned
subgrid closure, the Germano identity gives an exact consistency condition. If $\tau_{ij}$ is
the subgrid stress at the first filter and $T_{ij}$ the stress at the combined filter, a
coarser test filter applied on top of the first, then

$$
T_{ij} - \widetilde{\tau_{ij}} = \widetilde{\bar u_i \bar u_j} - \tilde{\bar u}_i
\tilde{\bar u}_j , \tag{2}
$$

where a bar is the first filter and a tilde the test filter (Germano et al. 1991; reviewed
by Meneveau and Katz 2000). The right-hand side is
computable from the resolved field, so a learned closure's stresses at two widths can be
checked against it.

## Pitfalls

- The flux needs phase-resolved fields and resolved gradients, so it is noisy on coarse
  grids.
- It costs more than the spectrum: the nonlinear term must be formed in physical space and
  transformed.
- Away from a clean inertial range, the expected shape of $\Pi(k)$ is not fixed, and the
  reference-free form has no target.
- In two dimensions the energy flux is negative over the range of scales larger than the
  forcing, because energy cascades toward large scales (Kraichnan 1967); a sign test tuned to
  three dimensions misreads it. See
  [helicity, potential vorticity and information transfer across scales](inviscid_invariants.md).

## Rationale

*From the field guide; the team has not yet set a priority.* The flux detects
wrong-cascade and spurious-backscatter errors that the energy spectrum cannot see, and a flux
that falls to zero is the direct signature of a prediction drifting toward a Gaussian-like
state. Its reference-free form remains meaningful after decorrelation.

## Keywords

spectral energy flux, energy transfer, backscatter, coarse-graining, filtering approach,
baropycnal work, pressure dilatation, Germano identity, dynamic subgrid model.

## References

- Aluie, H. (2011). Compressible turbulence: the cascade and its locality. *Physical Review
  Letters* 106, 174502. <https://doi.org/10.1103/PhysRevLett.106.174502>
- Aluie, H. (2013). Scale decomposition in compressible turbulence. *Physica D* 247, 54–65.
  <https://doi.org/10.1016/j.physd.2012.12.009>
- Aluie, H., Li, S. & Li, H. (2012). Conservative cascade of kinetic energy in compressible
  turbulence. *The Astrophysical Journal Letters* 751, L29.
  <https://doi.org/10.1088/2041-8205/751/2/l29>
- Germano, M., Piomelli, U., Moin, P. & Cabot, W. H. (1991). A dynamic subgrid-scale eddy
  viscosity model. *Physics of Fluids A* 3, 1760–1765. <https://doi.org/10.1063/1.857955>
- Kraichnan, R. H. (1967). Inertial ranges in two-dimensional turbulence. *Physics of
  Fluids* 10, 1417–1423. <https://doi.org/10.1063/1.1762301>
- Meneveau, C. & Katz, J. (2000). Scale-invariance and turbulence models for large-eddy
  simulation. *Annual Review of Fluid Mechanics* 32, 1–32.
  <https://doi.org/10.1146/annurev.fluid.32.1.1>
