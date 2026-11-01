# The Wasserstein distance for velocity and vorticity waits on the signed-field formulation

**Category:** deferred functionality
**Priority:** high, the team's priority for the idea
**Status:** open for velocity and vorticity, which wait on the signed-field decision (issue 047). The positive field is built: [wasserstein](../metrics/wasserstein/card.md) is the quadratic Wasserstein distance between density fields.

## Context

Idea: [Wasserstein distance for velocity and vorticity](../docs/ideas/optimal_transport/wasserstein_signed_fields.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The quadratic Wasserstein distance compares two nonnegative distributions of equal mass. Density is one, after each field is divided by its mean, and `metrics/wasserstein` computes it by solving the periodic Monge–Ampère equation (Saumier, Agueh & Khouider 2015, *IMA J. Appl. Math.* 80(1), 135–157). An exact transport between one point per cell is not used. On a 256 × 256 grid its cost matrix has 65 536² entries, and for displacements below a cell it measures the grid rather than the field (the bundle's card, Definition).

## Why it is not built

Velocity and vorticity take both signs, so they are not measures, and every way of applying transport to them is one of the formulations that issue 047 leaves undecided. They give different numbers. The bundle declares `fields=("density",)` and returns NaN for a field with a non-positive cell rather than choosing one.

## What would unblock it

The signed-field decision (issue 047). Its options interact with what the density build found. Density is a small fluctuation on a large positive mean. That is the same situation as the "add a constant, then normalise" option, under which the distance stops growing as the square of a shift (Yang et al. 2018, *Geophysics* 83(1), R43–R62, Sect. 3.1; Engquist & Yang 2022, *CPAM* 75(10), 2201–2244, Theorem 4.6). It also stays close to the H^-1 seminorm of `h_minus_one` (Peyre 2018, *ESAIM: COCV* 24(4), 1489–1501, Corollary 3 and Theorem 5). The Monge–Ampère solver in `metrics/wasserstein` applies unchanged to whatever positive densities the chosen formulation produces.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23). Narrowed to the signed fields when `wasserstein` was built for density (2026-10-31).
