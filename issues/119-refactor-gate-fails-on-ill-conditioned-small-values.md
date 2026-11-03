# A refactor gate at rtol 1e-12 cannot pass where a metric's value is ill-conditioned

**Category:** technical debt
**Priority:** low
**Status:** open.

## Context

`docs/recipes/compare_runs.py` accepts two runs when every number agrees to
`np.isclose(rtol=1e-12, atol=0)`. That tolerance assumes a value moves by a few units in the last
place when the order of floating-point operations changes. Near zero, some metrics are far more
sensitive than that.

`wasserstein` showed it on near-identical pairs: additive noise at 1e-3 of the fluctuation rms,
the mildest band-limited coarsening and the mildest high-pass levels. On the worst row
(`coarsen_bandlimited` level 1, frame 2000, a value of 4.4e-8 cells), perturbing the candidate
by one unit in the last place moves the value by 1.4e-12 to 2.7e-11 relative, against 4e-16 to
3e-15 on a 16-cell shift. Replacing the eigenvalue solve by a closed-form determinant (PR #32,
589ff0d) changed 122 of 9499 rows by more than 1e-12, at most 3.3e-11. Every one of those rows
has a value of 2e-4 or less, against a median of 0.014. Every larger value agreed to 9.7e-13.
The absolute differences are about 1e-15 or less. The orchestrator recomputed the
comparison and accepted the change (agent record, finding 030).

## What would settle it

A rule for when a gate failure is round-off rather than a change. Two options:

- An absolute tolerance per metric, scaled to the metric's typical value in the run (for
  example `atol = 1e-12 * median |value|`). This is simple, but it hides a real change confined
  to small values.
- Keep atol 0. When rows fail, measure how much each failing row moves under a one-ulp
  perturbation of its input, and accept the row when the difference is within that. This is
  more work per failure, but it is evidence rather than a threshold.
