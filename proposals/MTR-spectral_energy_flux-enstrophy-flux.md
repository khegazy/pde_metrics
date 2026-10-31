---
type: "MTR"
kind: "new metric"
related: ["spectral_energy_flux", "enstrophy", "palinstrophy", "docs/ideas/turbulence_statistics/inviscid_invariants.md"]
seen_in: "Alexakis & Biferale 2018, Physics Reports 767-769, 1-101, Sect. 3.2.1"
doi: "10.1016/j.physrep.2018.08.001"
found_by: "spectral_energy_flux, 2026-10-30"
---

# MTR: Spectral enstrophy flux of two-dimensional flow

## What it measures

The rate at which advection moves enstrophy (mean squared vorticity) across each wavenumber. In
two dimensions enstrophy is the invariant that cascades to small scales, while energy goes to
large ones, so on two-dimensional data this is the forward-cascade counterpart of the built
`spectral_energy_flux`.

## Definition

With w the vorticity and w^{<k} its low-pass part keeping the modes inside k, the enstrophy flux
is Pi_Z(k) = < w^{<k} (u . grad) w > (Alexakis & Biferale 2018, Eq. 53 of arXiv:1808.06186,
Sect. 3.2.1). In the forward (enstrophy) range of forced 2D turbulence it is approximately
constant and positive, equal to the enstrophy dissipation rate (their Eq. 54); the accompanying
text states the forward flux with the opposite sign, an inconsistency in the source that the
summary I read reported, so the sign convention should be checked in the published version
before building. The comparison against a reference would be the same octave-sampled relative L2
distance as `spectral_energy_flux` (a convention, issues/105).

## Relation to existing work

Not in docs/catalog.json or docs/ideas/. The built `enstrophy` and `palinstrophy` are one-field
quadratic quantities; the inviscid-invariants page names the "direction of each cascade" as the
natural two-dimensional check but has no enstrophy-flux metric. It needs velocity and vorticity on
the same cells: as a velocity-only metric it can recompute the vorticity with
`fmeval.derived.vorticity_from_velocity` and reuse `radial_energy_spectrum`'s co-spectrum, so no
multi-field input path is needed.

## How it could be tested

On the existing smoothing, spectral, resolution and noise axes, as `spectral_energy_flux` is; the
vorticity sits at higher wavenumbers than the velocity, so the axes bite at different severities.
The graded phase randomisation proposed beside this (EXP-spectral_energy_flux-graded-phase-
randomisation) would test it as a triple correlation.

## Why it is helpful

All data here are two-dimensional, where the energy flux is weak at small scales and the
enstrophy flux carries the small-scale transfer; a model that blurs small scales should show it
there first.

## References

- Alexakis, A. & Biferale, L. (2018). Cascades and transitions in turbulent flows. *Physics
  Reports* 767-769, 1-101. doi:10.1016/j.physrep.2018.08.001 (Eqs. 53-54 of arXiv:1808.06186).
