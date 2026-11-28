---
type: "EXP"
kind: "benchmark problem"
related: ["spectral_energy_flux", "spectrum_l2", "docs/ideas/turbulence_statistics/energy_transfer_checks.md", "docs/ideas/turbulence_statistics/inviscid_invariants.md", "docs/ideas/physics_invariants/helmholtz_split.md"]
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
split, and the shock metrics. Also `spectrum_l2` (added by update_metric_eval_principles,
2026-11-03): its field compares energy spectra of forced, statistically steady turbulence,
whose two-dimensional inertial ranges have known slopes, k^-5/3 for the inverse energy
cascade and k^-3 for the direct enstrophy cascade in the incompressible case (Boffetta &
Ecke 2012, Annu. Rev. Fluid Mech. 44, 427-451, Eqs. 12-13, p. 431,
doi:10.1146/annurev-fluid-120710-101240); `kinet_re5e4` decays and is unforced, so it has no
such range to recover.

## Why it is helpful

It is the nearest published setting to the north-star case that keeps two dimensions: weakly to
moderately compressible, forced, with shocklets. It is what issue 085 asks for ("forced
two-dimensional data for the cascade checks") with compressibility added.

**What exists now (2026-11-27).** `kinet_forced_re40k` is forced, statistically stationary
two-dimensional turbulence from kinet, with a linear drag and a force in the shell
$31 \le |n| \le 33$ on $1024^2$ cells (`docs/datasets/forced_turbulence_2d.md`). It supplies
the forcing scale and the two cascades this proposal names for `spectrum_l2` and the cascade
checks of issue 085: an inverse range of slope $-1.53$ over shells 6 to 28 and a steep direct
range of slope $-4.48$ over shells 40 to 120. It does **not** supply this experiment: it is
weakly compressible at an rms Mach number of 0.096 (local Mach at most 0.37), not 0.33 to 0.54,
has no shocklets and no acoustic flux loop, and stores only the solver's gauge pressure, which
is not converted. kinet's compressible physics does not support a forced run with shocklets,
and shocklets are set aside for now (`dataset_specs/BUILD_ORDER.md`, decision 7, steps 23 and
26). This proposal stays for the compressible case.

## Cost and requirements

A new simulation; kinet could run it if it supports forcing at that Mach number (not checked).
Kritsuk's runs used a different solver and are not, as far as I found, published as data.

## References

- Kritsuk, A. G. (2018). Energy transfer and spectra in simulations of two-dimensional
  compressible turbulence. arXiv:1802.08228.
- Falkovich, G. & Kritsuk, A. G. (2017). How vortices and shocks provide for a flux loop in
  two-dimensional compressible turbulence. *Physical Review Fluids* 2(9), 092603(R).
  doi:10.1103/PhysRevFluids.2.092603
