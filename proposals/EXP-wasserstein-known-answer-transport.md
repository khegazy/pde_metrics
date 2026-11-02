---
type: EXP
kind: benchmark problem
related: ["wasserstein", "docs/ideas/optimal_transport/sliced_wasserstein.md", "docs/ideas/optimal_transport/sinkhorn.md"]
seen_in: "Saumier, Agueh & Khouider 2015, IMA J. Appl. Math. 80(1), 135-157; Delon, Salomon & Sobolevski 2010, SIAM J. Appl. Math. 70(7), 2239-2258"
doi: "10.1093/imamat/hxt032"
found_by: "wasserstein, 2026-10-31"
---

# EXP: Known-answer transport problems on the torus

## What the experiment is

Two families of periodic density pairs whose quadratic Wasserstein distance is known exactly,
for checking any transport metric in the repository.

1. **Manufactured map** (Saumier et al. 2015, Sect. 5.1). Choose a periodic potential u, for
   example (1/k) cos(2 pi gamma x1) sin(2 pi gamma x2), and a target density g. Compute the
   source f = g(x + grad u) det(I + D^2 u) from their Eq. (4). If x + grad u is the gradient
   of a convex function, it is the optimal map, and W_2^2 is the f-weighted mean of
   |grad u|^2 (their Eq. 3).
2. **One-dimensional profiles on the circle** (Delon, Salomon & Sobolevski 2010, Sect. 2). A
   density varying along one axis only has a one-dimensional optimal map. Its exact distance
   is the least, over a rotation of the mass levels, of the distance between the two quantile
   functions.

## What it tests

Each pair has a known answer, so it tests whether a solver returns the transport distance and
not an approximation of it. `metrics/wasserstein/test_metric.py` already uses family 2: on a
profile between 0.63 and 1.37 times its mean, moved by 1 to 128 of 256 cells, the
Monge-Ampere solve matched it to a relative 2.6e-5 to 4.9e-5.

## Metrics it would test

`wasserstein`; a future sliced Wasserstein distance (issue 048 asks for validation "against
the exact Wasserstein distance on small cases"); a future Sinkhorn divergence (issue 067),
whose entropic bias against the exact value this would measure.

## Why it is helpful

Issues 048 and 067 both need a reference value to validate against. These pairs supply one
at any grid size, with no transport solver involved. Family 1 also reaches genuinely 2-D maps,
which family 2 cannot.

## Cost and requirements

A test fixture of about twenty lines in `tests/analytic_fields.py`; no data, no licence.

## References

- Saumier, L.-P., Agueh, M. & Khouider, B. (2015). IMA J. Appl. Math. 80(1), 135-157. doi:10.1093/imamat/hxt032 (arXiv:1009.6039v2 numbering).
- Delon, J., Salomon, J. & Sobolevski, A. (2010). SIAM J. Appl. Math. 70(7), 2239-2258. doi:10.1137/090772708.
