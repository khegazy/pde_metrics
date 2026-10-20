# Wavelet scattering and phase harmonics

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

This is the leading candidate for a single "turbulence transform": one family of descriptors
that summarises a turbulent field well enough to compare two fields by. A scattering
transform applies a wavelet transform, takes the modulus (absolute value) of the result,
and repeats. The first layer of coefficients depends on a single scale and orientation. The
second layer probes the *coupling between two oriented scales*, which is exactly the
information a power spectrum discards. The astrophysics literature describes it as "a
low-variance statistical description of non-Gaussian processes" that is "inspired by
convolutional neural networks but that does not require any training stage" (Regaldo-Saint
Blancard et al. 2020). The transform originates with Mallat (2012) and was developed by Bruna
and Mallat (2013).

It fits the problem of comparing shocked, turbulent fields for two reasons.

- The transform is invariant to translation and stable to small deformations, which is the
  formal version of the requirement that a slightly shifted shock should not make the metric
  blow up.
- Its second-layer coefficients measure the coupling across scales, which is what
  distinguishes real turbulence from a Gaussian random field with an identical spectrum,
  such as the [gaussian_impostor](../../degradations/gaussian_impostor.md).

## Precedent

The transform has been used on magnetohydrodynamic (MHD) turbulence, in simulations and in
observations, in a field that never has ground truth aligned in phase with the data. Allys
and colleagues introduced the reduced wavelet scattering transform (RWST) for the
interstellar medium (Allys et al. 2019). The approach was then extended to polarised dust
emission (Regaldo-Saint Blancard et al. 2020) and used to classify MHD simulations (Saydjari
et al. 2021).

## Rationale

*The team's judgement.* High priority: this is the only idea in the plan that plausibly
delivers a single family of descriptors sensitive to smooth structure, sharp structure and
*intermittency* (the concentration of a field's activity into rare, intense events) at once,
and therefore the only real candidate for a unified metric for shocklets, the many small
shocks embedded in compressible turbulence. Its astrophysical track record on compressible
MHD turbulence is close enough to that regime to be informative.

## Keywords

wavelet scattering transform, reduced wavelet scattering transform, RWST, scattering
covariance, wavelet phase harmonics, Mallat scattering.

## References

- Allys, E., Levrier, F., Zhang, S., Colling, C., Regaldo-Saint Blancard, B., Boulanger, F.,
  Hennebelle, P. & Mallat, S. (2019). The RWST, a comprehensive statistical description of
  the non-Gaussian structures in the ISM. *Astronomy & Astrophysics* 629, A115.
  <https://arxiv.org/abs/1905.01372>
- Bruna, J. & Mallat, S. (2013). Invariant scattering convolution networks. *IEEE
  Transactions on Pattern Analysis and Machine Intelligence* 35(8), 1872–1886.
  <https://doi.org/10.1109/TPAMI.2012.230>
- Mallat, S. (2012). Group invariant scattering. *Communications on Pure and Applied
  Mathematics* 65(10), 1331–1398. <https://doi.org/10.1002/cpa.21413>
- Regaldo-Saint Blancard, B., Levrier, F., Allys, E., Bellomi, E. & Boulanger, F. (2020).
  Statistical description of dust polarized emission from the diffuse interstellar medium: A
  RWST approach. *Astronomy & Astrophysics* 642, A217.
  <https://doi.org/10.1051/0004-6361/202038044>
- Saydjari, A. K., Portillo, S. K. N., Slepian, Z., Kahraman, S., Burkhart, B. & Finkbeiner,
  D. P. (2021). Classification of magnetohydrodynamic simulations using wavelet scattering
  transforms. *The Astrophysical Journal* 910(2), 122.
  <https://doi.org/10.3847/1538-4357/abe46d>
