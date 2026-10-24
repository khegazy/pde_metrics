# One-point statistics and characteristic scales: what remains that is neither built, three-dimensional, nor untestable

**Category:** method
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [One-point statistics and characteristic scales](../docs/ideas/turbulence_statistics/one_point_statistics.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page lists Reynolds stresses, Favre averages, the dissipation rate $\varepsilon = 2\nu\langle S_{ij}S_{ij}\rangle$ and the integral, Taylor, Kolmogorov and Batchelor scales. The mean kinetic energy is built as `kinetic_energy`.

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. Reading each remaining item against the data:

- *Dissipation rate.* For periodic incompressible flow $\langle S_{ij}S_{ij}\rangle = \tfrac12\langle|\boldsymbol\omega|^2\rangle$ (integrate $\partial_i u_j \partial_j u_i$ by parts with $\nabla\cdot\mathbf u = 0$), so $\varepsilon = \nu\langle|\boldsymbol\omega|^2\rangle$, a fixed multiple of the built `enstrophy`. On `kinet_re5e4` (Mach 0.1) the two differ only by the small dilatational part. Building it would duplicate a metric (derived in the screening from the definitions on the page).
- *Taylor and Kolmogorov scales.* The relations on the page ($\varepsilon = 15\nu u'^2/\lambda^2$, $\eta = (\nu^3/\varepsilon)^{1/4}$) are for three-dimensional isotropic turbulence ([005](005-3d-and-cost-extrapolation.md)).
- *Reynolds-stress anisotropy.* No degradation is anisotropic, so nothing changes it in a controlled way (see [the anisotropic-blur proposal](../proposals/EXP-orchestrator-20261023-anisotropic-blur.md)); its trace is twice the built kinetic energy.
- *Integral scale.* A candidate, but its standard formula from the energy spectrum carries three-dimensional isotropic constants.
- *Batchelor scale.* No transported scalar in any dataset.

## What would unblock it

A decision on which part, if any, to build in two dimensions, and with which formula.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
