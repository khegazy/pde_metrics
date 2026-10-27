# Helicity, potential vorticity and information transfer need data the repository does not have

**Category:** data generation
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, waiting on data

## Context

Idea: [Helicity, potential vorticity and information transfer across scales](../docs/ideas/turbulence_statistics/inviscid_invariants.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page collects helicity, the two-dimensional cascades, potential vorticity, and mutual information and transfer entropy between scale bands.

## Why it is not built

Part by part:

- *Helicity* is identically zero in planar two-dimensional flow (the page's first pitfall), and all data are two-dimensional ([005](005-3d-and-cost-extrapolation.md)).
- *Potential vorticity* needs a rotating frame and a potential temperature; no dataset has either.
- *Two-dimensional cascades.* The page's natural checks are "the direction of each cascade and the spectral slope on each side of the forcing scale"; `kinet_re5e4` is unforced and decaying, so there is no forcing scale.
- *Transfer entropy* needs time series (Eq. 3 conditions on the next value); *mutual information* between bands needs a density estimator, which the page warns is "data-hungry and sensitive to the estimator", with no standard named.

## What would unblock it

Three-dimensional data for helicity, forced two-dimensional data for the cascade checks, rotating stratified data for potential vorticity, and trajectories with a declared estimator for the information measures.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
