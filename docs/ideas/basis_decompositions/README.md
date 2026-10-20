# Basis decompositions and the turbulence transform

A basis decomposition rewrites a field as a sum of simple building blocks, such as Fourier
modes or wavelets, so that two fields can be compared block by block. The Fourier basis is
the standard choice, but its usual summaries, the energy spectrum and the two-point
correlation, keep only the amplitude of each mode and discard its *phase*, which is where the
arrangement of structures in space is recorded. Wavelets are localised in both space and
scale, so they can describe a sharp feature where it sits instead of spreading it over every
wavenumber. This theme collects the decompositions that go beyond the amplitude spectrum, up
to the leading candidate for a single "turbulence transform". It also holds the comparisons
that split an error by scale, and the spectral statistics astrophysics developed for data
that never has a reference aligned in phase with it.

Built already, and so not listed here: the comparison of energy spectra
([spectrum_l2](../../metrics/spectrum_l2.md)).

## Ideas in this theme

- [Two-point correlation](two_point_correlation.md): how strongly a field at one point is
  related to the same field a given distance away, which carries the same information as the
  energy spectrum.
- [Wavelets and coherent vortex extraction](coherent_vortex_extraction.md): a split of a
  field into a few large wavelet coefficients that carry its coherent structures and a
  noise-like background carried by the rest.
- [Wavelet scattering and phase harmonics](wavelet_scattering.md): a cascade of wavelet
  transforms whose second layer measures how different scales are coupled, which is exactly
  what a spectrum discards.
- [Bispectrum and bicoherence](bispectrum.md): the phase coupling of Fourier modes in triads,
  identically zero for a Gaussian field with the same spectrum.
- [Error by wavenumber band](spectral_band_error.md): the error split into low, intermediate
  and high wavenumber bands fixed by the reference's resolved range.
- [Spectral coherence and phase error](spectral_coherence.md): the wavenumber at which a
  rollout's phases first drift from the reference's, while it is still aligned.
- [Delta-variance spectral slope](delta_variance.md): a filter-based stand-in for the
  spectrum that works on bounded and irregular maps where a Fourier transform does not.
- [Velocity channel analysis](velocity_channel_analysis.md): spectra of a projected,
  line-of-sight reference, compared in observation space.
