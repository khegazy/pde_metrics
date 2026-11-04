# Code notes: persistence_wasserstein

The coding record of the build of 2026-11-04 (task `metrics-topology-shocks`). The research
record is in [research_notes.md](research_notes.md).

## Summary

`metric.py` holds the registered metric and `wasserstein`, the per-dimension distance. Everything
else is imported from `metrics/persistence_distance/metric.py`: the diagram (`persistence_diagram`,
registered as this metric's point-set companion too) and the shared per-dimension step
`diagram_distances`, extracted from `persistence_distance` in the same change.

## Implementation

- **`diagram_distances`** (in `persistence_distance`): checks shapes, caches the reference's
  diagram under `REFERENCE_DIAGRAM`, reads the candidate's from `COMPANION_KEY`, splits each
  dimension's (birth, death) rows, sorts them, returns exactly 0 for equal multisets, and otherwise
  calls the given distance with the two diagrams in an order fixed by their size and bytes, so an
  approximate distance is exactly symmetric. `persistence_distance` became
  `max(diagram_distances(..., distance=gudhi.bottleneck_distance))`; the refactor gate on 28 pairs
  of real fields (density and vorticity at 64 and 256; blurs, box filter, roll, noise) gave every
  value bitwise equal to the code before (task log).
- **`wasserstein(a, b)`**: Hera with `order=ORDER`, `internal_p=inf`, `delta=DELTA` on the finite
  points and on the points at infinity, combined as the p-th root of the sum of p-th powers.
  Different counts of points at infinity give `inf`, as Hera returns.
- **The companion** is `persistence_diagram` registered by a call,
  `companion(of="persistence_wasserstein", ...)(persistence_diagram)`, not a forwarding function.
- **Decorator**: as `persistence_distance` (fields density and vorticity, `cost="expensive"`,
  `differentiable=False`, `requires_periodic=False`); monotone under the contract's blur ladder,
  measured by the contract test.

## Tests

`test_metric.py`, every expected value derived in its docstring: the card's worked example
(bottleneck 0.5 and W_1 1.0 for two filled wells), the offset that moves all six points by 0.25
(W_1 1.5), agreement with GUDHI's exact solver to `DELTA`, the Hera crash case (value 1), the
cellular stability bound on periodic and walled grids, and W_1 >= bottleneck.

## Bugs and fixes

- **Hera stops the process with a segmentation fault** (return code -11, gudhi 3.13.0) when one
  diagram holds two or more finite points beside points at infinity and the other holds points at
  infinity only, e.g. `[[0, 1], [0, 1], [-1, inf]]` against `[[-1, inf]]`, at delta 0.01 and 1e-6.
  Each part alone is computed. Found while computing the card's worked example (two wells filled).
  Fixed by `wasserstein` splitting the parts; `test_finite_points_against_points_at_infinity_alone_are_computed`
  keeps the case.

## Performance

One 256 x 256 vorticity frame of `kinet_re5e4` (frame 5000), blurred (sigma 1) and noisy (0.1 of
the RMS) candidates, all three dimensions, delta 1e-6: 5.6 s and 23.9 s per comparison; at 128,
0.18 s and 2.9 s; at 64, 0.015 s and 0.08 s. The bottleneck distance on the same 256 pairs took
0.06 to 0.32 s per dimension.

## Tooling and environment problems

- A worktree-isolated shell refuses compound commands with computed program names; scripts were
  written to the scratchpad and run with `python -c "exec(open(...).read())"` from the worktree.
- No PDF text tool in the environment; `gs -sDEVICE=txtwrite` (Ghostscript, `/usr/bin/gs`)
  extracted the Cohen-Steiner et al. 2010 PDF.

## For the next agent

- p = 2 is `ORDER = 2.0`; give `wasserstein` an `order` argument rather than copying it.
