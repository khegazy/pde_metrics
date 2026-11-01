---
type: MTR
kind: variant of wasserstein
related: ["wasserstein", "docs/ideas/shock_geometry/shock_turbulence_interaction.md"]
seen_in: "Saumier, Agueh & Khouider 2015, IMA J. Appl. Math. 80(1), 135-157"
doi: "10.1093/imamat/hxt032"
found_by: "wasserstein, 2026-10-31"
---

# MTR: The same W2, with a full Newton step for high-contrast densities

## What it measures

The same quantity as `wasserstein`, the quadratic Wasserstein distance between two
mass-normalised densities on the torus, computed with a solver that also converges where a
density is several times its mean, as behind a strong shock.

## Definition

Saumier et al. (2015), Eq. (5) (arXiv:1009.6039v2 numbering), linearise the periodic
Monge-Ampere equation as g(x + grad u) Tr(Adj(I + D^2 u) D^2 theta) + det(I + D^2 u)
grad g(x + grad u) . grad theta. Their Sect. 4.2, after Strain, solves that variable-coefficient
equation with GMRES on L Lbar^-1 sigma = h, where Lbar is the operator with averaged
coefficients, inverted by FFT. `wasserstein` replaces Eq. (5) by its leading term with g divided
out cell by cell and damps the step adaptively; that converges, measured against the exact
circle cost, up to a density peak of about 2.3 to 2.9 times the mean and fails beyond. A full
Newton step would converge quadratically wherever their convergence theorem holds.

## Relation to existing work

A solver variant of `wasserstein`; same value wherever both converge (the converged potential
is fixed by the residual, not by the operator). Adversarial critique 1 of the bundle found the
range limit; finding 025 measured it.

## How it could be tested

The peaked circle profiles of `metrics/wasserstein/test_metric.py`, raised to a peak of 3.5
and 10 times the mean, against the exact circle cost of Delon et al. (2010), Sect. 2; and the
background-ratio sweep (EXP-wasserstein-background-ratio-sweep), whose tall bumps are the
high-contrast regime.

## Why it is helpful

The north-star case is shocklet-populated compressible turbulence, where density compression
across a shock can exceed the range the current solver handles; there `wasserstein` returns NaN
with a warning. scipy.sparse.linalg.gmres with a LinearOperator is enough; no new dependency.

## References

- Saumier, L.-P., Agueh, M. & Khouider, B. (2015). IMA J. Appl. Math. 80(1), 135-157. doi:10.1093/imamat/hxt032.
- Delon, J., Salomon, J. & Sobolevski, A. (2010). SIAM J. Appl. Math. 70(7), 2239-2258. doi:10.1137/090772708.
