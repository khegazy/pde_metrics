# Turbulence statistics and exact laws

A turbulent field must satisfy statistical relations that its energy spectrum does not
determine: a few laws that hold exactly at high Reynolds number, signs fixed by the
dynamics, and characteristic distributions of velocity gradients. A Gaussian random field
built to match the reference energy spectrum, such as the
[gaussian_impostor](../../degradations/gaussian_impostor.md), has zero mean for every
odd-order moment of its velocity increments, so it carries no energy cascade and no net
vortex stretching however well its spectrum agrees. The statistics in this theme are the
ones such a field cannot reproduce, together with the one-point quantities and scales they
are normalised by. Several of them need only the prediction, with no reference, and so remain
meaningful after a long rollout has drifted out of phase with the reference trajectory. Most
are derived for three-dimensional, incompressible, homogeneous turbulence, and each page says
where that assumption matters.

Built already, and so not listed here: the flatness of one-cell increments
([increment_flatness](../../metrics/increment_flatness.md)), the Wasserstein distance between
one-cell increment distributions ([increment_w1](../../metrics/increment_w1.md)), and the mean
kinetic energy ([kinetic_energy](../../metrics/kinetic_energy.md)).

## Ideas in this theme

- [Four-fifths law and the third-order structure function](four_fifths_law.md): an
  exact law of the inertial range, scored against a reference or against the prediction's
  own dissipation, with the scale-by-scale energy budget it comes from.
- [Structure functions and scaling exponents](structure_functions.md): moments of velocity
  increments at every separation and order, and the exponents that measure intermittency.
- [Velocity-derivative skewness](derivative_skewness.md): a single cheap number that is zero
  for a Gaussian field and close to $-0.5$ in real turbulence.
- [Spectral energy flux](spectral_energy_flux.md): the rate at which energy passes from large
  to small scales, which a correct spectrum does not guarantee.
- [Vortex stretching and energy budgets](vortex_stretching.md): the sign of mean enstrophy
  production and the closure of the energy and enstrophy budgets.
- [Joint distribution of the velocity-gradient invariants Q and R](qr_invariants.md): the
  distribution of local flow topology, whose characteristic shape a Gaussian field lacks.
- [Helicity, potential vorticity and information transfer across scales](inviscid_invariants.md):
  conserved quantities beyond energy, and measures of how information moves between scales.
- [One-point statistics and characteristic scales](one_point_statistics.md): Reynolds
  stresses, density-weighted averages, dissipation, and the integral, Taylor, Kolmogorov and
  Batchelor scales.
