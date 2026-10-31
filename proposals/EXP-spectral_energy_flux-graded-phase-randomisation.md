---
type: "EXP"
kind: "degradation"
related: ["spectral_energy_flux", "gaussian_impostor", "docs/ideas/basis_decompositions/bispectrum.md", "docs/ideas/basis_decompositions/spectral_coherence.md", "docs/ideas/turbulence_statistics/derivative_skewness.md"]
seen_in: "agent's own"
doi: "none"
found_by: "spectral_energy_flux, 2026-10-30"
---

# EXP: Graded phase randomisation, an ordinal axis between the reference and the impostor

## What the experiment is

A degradation that keeps every Fourier amplitude of the field and rotates each mode's phase by
a random angle drawn uniformly from an interval of half-width `s * pi`, with Hermitian symmetry
kept as `gaussian_impostor` keeps it. The severity `s` runs from 0 (the reference) to 1 (the
impostor's uniform phases). This is my own proposal; I found no published version of it in the
sources I read.

## What it tests

It removes phase coherence by a controlled amount while leaving the amplitude spectrum exactly
unchanged, so every spectrum-based metric must be blind to it and every phase-sensitive
statistic must follow it. A triple correlation such as the spectral energy flux is a sum over
triads of products of three modes, so (my own derivation, not a citation) its expected value is
multiplied by the cube of the characteristic function of the phase perturbation, sinc(s pi)^3,
which falls monotonically from 1 to 0 on [0, 1]. The known answer is therefore the expected
fraction of the reference's flux that survives at each severity.

## Metrics it would test

`spectral_energy_flux` (which today meets phase destruction only through the impostor, a probe
excluded from every rank correlation), the bispectrum and bicoherence (issue 065), spectral
coherence, velocity-derivative skewness, and `increment_flatness`. It would also be a blind axis
for `spectrum_l2` and the two-point correlation.

## Why it is helpful

The impostor is a single all-or-nothing probe. An ordinal axis between it and the reference turns
"is this metric phase-blind" into a measured response curve, with a predicted shape to check
against, for the whole family of statistics the impostor exists for.

## Cost and requirements

One new degradation bundle, reusing the Hermitian-symmetric phase draw of
`degradations/gaussian_impostor`; `preserves=("amplitude_spectrum", "spatial_mean")`; stochastic,
so never calibrated. No new data.

## References

None; the proposal and the sinc-cubed expectation are my own.
