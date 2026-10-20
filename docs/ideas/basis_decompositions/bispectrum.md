# Bispectrum and bicoherence

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The power spectrum keeps the amplitude of each Fourier mode and discards its phase, the part
of the mode that records where structures sit. The bispectrum is the lowest-order spectral
statistic that keeps phase information. For a scalar field $a$ with Fourier coefficients
$\hat a(\mathbf{k})$, it averages the product of three modes whose wavevectors close a
triangle, $\mathbf{k}_1 + \mathbf{k}_2 = \mathbf{k}_3$, called a *triad*:

$$
B(\mathbf{k}_1,\mathbf{k}_2)=\big\langle \hat a(\mathbf{k}_1)\,\hat a(\mathbf{k}_2)\,
\hat a^{*}(\mathbf{k}_1+\mathbf{k}_2)\big\rangle . \tag{1}
$$

Writing each coefficient as an amplitude times $e^{i\phi}$, the product in (1) carries the
phase combination $\phi_1+\phi_2-\phi_3$. If the three phases are independent and uniformly
distributed, that combination is uniform too and the average vanishes. A nonzero bispectrum
therefore means the phases of the triad are locked together, which is what nonlinear
interactions between scales do when they build shocks, fronts and vortices. The
*bicoherence* is its normalised, dimensionless form (Burkhart et al. 2009):

$$
b^2(\mathbf{k}_1,\mathbf{k}_2)=\frac{\big|B(\mathbf{k}_1,\mathbf{k}_2)\big|^2}
{\big\langle \big|\hat a(\mathbf{k}_1)\,\hat a(\mathbf{k}_2)\big|^2\big\rangle\,
\big\langle \big|\hat a(\mathbf{k}_1+\mathbf{k}_2)\big|^2\big\rangle}\in[0,1]. \tag{2}
$$

The metric compares the predicted bicoherence map with the reference's. The guide does not
fix which distance between the two maps to use.

A Gaussian random field has independent, uniformly distributed Fourier phases, so its
bispectrum and bicoherence are identically zero (Burkhart et al. 2009). The
[gaussian_impostor](../../degradations/gaussian_impostor.md) degradation keeps every mode's
amplitude and draws new uniform phases, so it matches the reference's energy spectrum
exactly while its expected bispectrum is zero. It is the field this metric should separate
from the reference, and the one a phase-blind check such as the
[two-point correlation](two_point_correlation.md) cannot.

The bispectrum is the statistical sibling of the
[spectral energy flux](../turbulence_statistics/spectral_energy_flux.md): the flux through a
wavenumber is a triple velocity correlation, a sum over triads of the velocity bispectrum,
and so it also vanishes for a Gaussian field. The bispectrum is cheaper to compute because it
needs only the field, not its nonlinear term.

## Precedent

Burkhart et al. used the bispectrum to characterise density in simulations of
magnetohydrodynamic interstellar turbulence, alongside statistical moments and correlations
(Burkhart et al. 2009). Astrophysics developed this family of statistics because it never has
a reference aligned in phase with its data, which is also the situation of a surrogate's
rollout after it has decorrelated from the reference. Implementations of the bispectrum and
related statistics are collected in the TurbuStat package (Koch et al. 2019).

## Pitfalls

- The bispectrum says nothing about amplitude or spectral slope on its own, so it must be
  paired with a spectrum comparison such as [spectrum_l2](../../metrics/spectrum_l2.md).
- It is statistically hungry. The average in (1) runs over many triads or many realizations,
  and an average of $N$ independent random phase factors has magnitude of order $N^{-1/2}$
  rather than zero. A finite sample of a Gaussian field therefore gives a small positive
  bicoherence, and the estimate is reliable only with large ensembles or long averaging.
- The guide writes (1) as a function of two wavenumbers. For a field in two or three
  dimensions the full bispectrum is a function of two wavevectors, which is costly in three
  dimensions; reducing it, for example to wavevector magnitudes, is a choice that must be
  declared once and kept fixed.

## Rationale

*From the field guide; the team has not yet set a priority.* A spectral loss depends only on
Fourier amplitudes, and so cannot tell a turbulent field from a Gaussian field with the same
spectrum. The bicoherence directly measures the Fourier phases such a loss discards, is
identically zero for a Gaussian field, and detects nonlinear phase coupling and driving
scales more cheaply than an audit of the energy flux. Unlike a pointwise error, it needs no
phase alignment with the reference, so it stays meaningful after a rollout has decorrelated.

## Keywords

bispectrum, bicoherence, triadic phase coupling, higher-order spectra, polyspectra,
non-Gaussianity.

## References

- Burkhart, B., Falceta-Gonçalves, D., Kowal, G. & Lazarian, A. (2009). Density studies of
  MHD interstellar turbulence: statistical moments, correlations and bispectrum.
  *The Astrophysical Journal* 693, 250–266. <https://doi.org/10.1088/0004-637X/693/1/250>
- Koch, E. W. et al. (2019). TurbuStat: turbulence statistics in Python. *The Astronomical
  Journal* 158, 1. <https://doi.org/10.3847/1538-3881/ab1cc0>
