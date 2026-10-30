# 003 — The spectral energy flux is computed from the velocity alone

**Date:** 2026-10-30. **Made by:** the agent building `spectral_energy_flux` (branch
`metric/spectral_energy_flux`).
**Reverse with:** delete the bundle `metrics/spectral_energy_flux`, or replace it with a
compressible-budget metric once several fields can be handed to one metric (`issues/096`); then
delete this file and the card's references to it.

## The question that would have been asked

The idea page defines the flux for incompressible flow and says that "when density varies, the
pressure does work and kinetic energy can be exchanged with internal energy, so Equation (1) is
incomplete". `kinet_re5e4` is weakly compressible (Mach 0.1, density varying by a few percent).
The complete budget needs density and pressure together with the velocity; a metric is handed
one field at a time (`issues/096`), and pressure is never computed from density in this
repository. Should the flux be built from the velocity alone, treating density as uniform, or
should the metric wait for the multi-field input path?

## The evidence

- **What the compressible budget contains.** Coarse-graining at scale $\ell$, the large-scale
  kinetic energy changes through deformation work $\Pi_\ell$, baropycnal work $\Lambda_\ell$ and
  large-scale pressure dilatation (Aluie 2013, *Physica D* 247(1), 54–65,
  doi:10.1016/j.physd.2012.12.009, Eq. 13 of arXiv:1012.5877). Only the first two move energy
  across scales (Aluie 2011, *Phys. Rev. Lett.* 106, 174502, Eqs. 3–5).
- **What each term becomes at uniform density.** Deformation work (Eq. 14) is "similar to its
  incompressible counterpart except that the strain is not traceless" (Sect. 4.1); baropycnal
  work (Eq. 15) "vanishes in the absence of density variations" (Sect. 4.2); pressure dilatation
  vanishes at every point in the incompressible limit (Sect. 4.3). Aluie (2011) calls
  incompressible turbulence a limiting case of the analysis. So the velocity-only flux is the
  uniform-density limit of the cross-scale transfer, with the velocity's own divergence kept.
- **How large the omitted terms are here.** I did not measure baropycnal work, because it needs
  pressure. The density fluctuation is small (its RMS is 1.8e-4 of its mean, `CLAUDE.md`), which
  is what makes the density weighting and the baropycnal term small. The only published
  measurement I found of how far pressure dilatation reaches is three-dimensional, at an rms
  Mach number of 0.43: it acts mainly at large scales and the kinetic-energy flux is close to
  constant beyond a transitional range (Aluie, Li & Li 2012, *ApJL* 751(2), L29, Figs. 2–3). In
  two dimensions at Mach 0.33–0.54 a flux loop through the acoustic modes appears (Kritsuk 2018,
  arXiv:1802.08228, Sect. 3), so the approximation is a weak-compressibility one, not a general
  one.

## The choice

Build Equation (1) of the idea page from the velocity alone, with the advective form
$(\mathbf{u}\cdot\nabla)\mathbf{u}$ of Alexakis and Biferale (2018, *Physics Reports* 767–769,
Eq. 18 of arXiv:1808.06186), and say on the card that it is the constant-density flux. Waiting
for `issues/096` would leave the flux, the measurable form of the idea that `docs/ideas/`
already lists, unbuilt for a dataset on which the omitted terms are small by construction; the
compressible terms stay on the narrowed idea page as unbuilt work.

## What it changes

The metric's value on `kinet_re5e4` is the velocity-only flux. On a strongly compressible
dataset it would miss baropycnal work and the exchange with internal energy, and with a
divergent velocity the flux through a wavenumber beyond every mode is
$-\langle(\nabla\cdot\mathbf{u})|\mathbf{u}|^2\rangle/2$ rather than zero; the card's
Limitations say both.
