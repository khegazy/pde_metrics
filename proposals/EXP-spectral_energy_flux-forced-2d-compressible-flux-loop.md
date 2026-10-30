---
type: "EXP"
kind: "benchmark problem"
related: ["spectral_energy_flux", "docs/ideas/turbulence_statistics/energy_transfer_checks.md", "docs/ideas/turbulence_statistics/inviscid_invariants.md", "docs/ideas/physics_invariants/helmholtz_split.md"]
seen_in: "Kritsuk 2018, arXiv:1802.08228; Falkovich & Kritsuk 2017, Physical Review Fluids 2(9), 092603(R)"
doi: "10.1103/PhysRevFluids.2.092603"
found_by: "spectral_energy_flux, 2026-10-30"
---

# EXP: Forced two-dimensional compressible turbulence at Mach 0.3 to 0.5

## What the experiment is

Doubly periodic two-dimensional compressible turbulence driven by a solenoidal, white-in-time
random force at a fixed wavenumber, run to a statistically steady state at an rms Mach number of
about 0.33 to 0.54 (Kritsuk 2018, arXiv:1802.08228, Sect. 3 and Table 1, read as full text on
ar5iv). Falkovich and Kritsuk (2017) describe the steady state: a box-size pair of long-lived
vortices linked by shocks (read from the abstract only).

## What it tests

It has known transfer signatures. Below the forcing wavenumber the solenoidal kinetic energy
cascades inversely while acoustic energy goes forward, so the kinetic and potential fluxes form a
loop (Kritsuk 2018, Sect. 3, Fig. 6), and with forcing there is a forcing scale on each side of
which the two-dimensional cascades have a sign. It also contains shocklets, which `kinet_re5e4`
does not.

## Metrics it would test

`spectral_energy_flux` on a flow where the velocity-only flux is no longer a good approximation
(judgements/003), the compressible budget and the reference-free flux checks on the
energy-transfer checks idea page, the two-dimensional cascade checks of issue 085, the Helmholtz
split, and the shock metrics.

## Why it is helpful

It is the nearest published setting to the north-star case that keeps two dimensions: weakly to
moderately compressible, forced, with shocklets. It is what issue 085 asks for ("forced
two-dimensional data for the cascade checks") with compressibility added.

## Cost and requirements

A new simulation; kinet could run it if it supports forcing at that Mach number (not checked).
Kritsuk's runs used a different solver and are not, as far as I found, published as data.

## References

- Kritsuk, A. G. (2018). Energy transfer and spectra in simulations of two-dimensional
  compressible turbulence. arXiv:1802.08228.
- Falkovich, G. & Kritsuk, A. G. (2017). How vortices and shocks provide for a flux loop in
  two-dimensional compressible turbulence. *Physical Review Fluids* 2(9), 092603(R).
  doi:10.1103/PhysRevFluids.2.092603
