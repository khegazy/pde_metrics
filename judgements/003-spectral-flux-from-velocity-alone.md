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
  doi:10.1016/j.physd.2012.12.009, Eqs. 13–15 of arXiv:1012.5877v2, numbering read from the TeX
  source). Only the first two move energy across scales (Aluie 2011, *Phys. Rev. Lett.* 106,
  174502, Eqs. 3–5).
- **What each term becomes at uniform density.** Baropycnal work (Eq. 15) "vanishes in the
  absence of density variations" (Sect. 4.2), and pressure dilatation vanishes at every point in
  the incompressible limit (Sect. 4.3). Deformation work (Eq. 14) stays, and with a divergent
  velocity it is not the incompressible flux $\langle\mathbf{u}^{<K}\cdot(\mathbf{u}\cdot\nabla)
  \mathbf{u}\rangle$. For the sharp spectral filter (his Eq. 21), Sect. 4.1 gives the compressible
  "unsubtracted flux", $\tilde u_i\,\overline{\partial_j(\rho u_iu_j)} - \tfrac12|\tilde{\mathbf
  u}|^2\,\overline{\partial_j(\rho u_j)}$. It differs from Eq. 14 by a total gradient, and its
  space average vanishes once every mode is kept. At uniform density it becomes
  $\langle\mathbf{u}^{<K}\cdot\nabla\cdot(\mathbf{u}\mathbf{u})\rangle -
  \tfrac12\langle|\mathbf{u}^{<K}|^2\,\nabla\cdot\mathbf{u}^{<K}\rangle$. The incompressible form
  instead leaves $-\langle(\nabla\cdot\mathbf{u})|\mathbf{u}|^2\rangle/2$ over all modes, a
  residual that is not a transfer. Equation numbers were read in the paper's TeX source,
  arXiv:1012.5877v2.
- **How large the omitted terms are here.** I did not measure baropycnal work, because it needs
  pressure. The density varies more than `AGENTS.md`'s "1.0 ± 1.8e-4" suggests. Measured on
  `kinet_re5e4`, its RMS is 2.1e-3, 6.7e-3 and 6.6e-3 of its mean at frames 2000, 6000 and 10000,
  and its range 1.3% to 4.5%. The only published measurement I found of how far pressure
  dilatation reaches is three-dimensional, at an rms Mach number of 0.43: it acts mainly at large
  scales, and the kinetic-energy flux is close to constant beyond a transitional range (Aluie, Li
  & Li 2012, *ApJL* 751(2), L29, Figs. 2–3). In two dimensions at Mach 0.33–0.54 a flux loop
  through the acoustic modes appears (Kritsuk 2018, arXiv:1802.08228, Sect. 3). The approximation
  is therefore a weak-compressibility one, not a general one.

## The choice

Build the flux from the velocity alone, with the density taken as uniform in Aluie's
sharp-spectral unsubtracted flux (Sect. 4.1), and say on the card that baropycnal work, pressure
dilatation and density weighting are omitted. For a divergence-free velocity this is the
incompressible flux of Alexakis and Biferale (2018, *Physics Reports* 767–769, Eq. 18 of
arXiv:1808.06186), the idea page's Equation (1). For a divergent one it stays a pure exchange
between scales.

Waiting for `issues/096` would leave the flux unbuilt for a dataset on which the omitted terms
are small. The flux is the measurable form of the idea that `docs/ideas/` already lists. The
compressible terms stay on the narrowed idea page as unbuilt work.

## What it changes

The metric's value on `kinet_re5e4` is the uniform-density flux of the velocity, including
transfer through its compressive modes. On a strongly compressible dataset it would miss
baropycnal work, density weighting and the exchange with internal energy; the card's
Limitations say so.

## Revised in the adversarial review (2026-10-30)

The first version of this judgement used the incompressible advective form for a divergent
velocity, and claimed that this was what deformation work becomes at uniform density. The
reviewer showed that this is false, because Eq. 14 differs from the advective form by divergence
terms. On `kinet_re5e4` the residual it left made up a large part of the curve. The bundle now
implements the form above, and the reasons are in the round's commit message.
