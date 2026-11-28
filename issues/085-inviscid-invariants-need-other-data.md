# Helicity, potential vorticity and information transfer need data the repository does not have

**Category:** data generation
**Priority:** unset — the team has not set a priority for the idea
**Status:** open. Helicity, potential vorticity and the information measures still wait on data;
the two-dimensional cascade checks now have forced data (`kinet_forced_re40k`, 2026-11-27) and
wait only on being built.

## Context

Idea: [Helicity, potential vorticity and information transfer across scales](../docs/ideas/turbulence_statistics/inviscid_invariants.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page collects helicity, the two-dimensional cascades, potential vorticity, and mutual information and transfer entropy between scale bands.

## Why it is not built

Part by part:

- *Helicity* is identically zero in planar two-dimensional flow (the page's first pitfall), and all data are two-dimensional ([005](005-3d-and-cost-extrapolation.md)).
- *Potential vorticity* needs a rotating frame and a potential temperature; no dataset has either.
- *Two-dimensional cascades.* The page's natural checks are "the direction of each cascade and the spectral slope on each side of the forcing scale"; `kinet_re5e4` is unforced and decaying, so there is no forcing scale. Since 2026-11-27 `kinet_forced_re40k` supplies one: forced, statistically stationary two-dimensional turbulence with a linear drag on $1024^2$ cells, forced in the shell $31 \le |n| \le 33$ (`docs/datasets/forced_turbulence_2d.md`). Its check measured an inverse range of slope $-1.53$ over shells 6 to 28 and a direct range of slope $-4.48$ over shells 40 to 120 (`docs/datasets/logs/kinet_runs/forced_turbulence_2d/checks/final_220000.txt`). It is weakly compressible (Mach 0.1), so it is not the compressible flux loop of `proposals/EXP-spectral_energy_flux-forced-2d-compressible-flux-loop.md`. No cascade check is built; that part now waits on the metric, not on data.
- *Transfer entropy* needs time series (Eq. 3 conditions on the next value); *mutual information* between bands needs a density estimator, which the page warns is "data-hungry and sensitive to the estimator", with no standard named.

## What would unblock it

Three-dimensional data for helicity, a built cascade check (its forced two-dimensional data exists), rotating stratified data for potential vorticity, and trajectories with a declared estimator for the information measures.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
