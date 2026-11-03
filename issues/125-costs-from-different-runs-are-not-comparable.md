# Costs recorded in different runs are not comparable

**Category:** technical debt
**Priority:** low
**Status:** open.

## Context

Each card's `cost` (`cost_s` in `fmeval/analysis.py`) is the mean wall-clock time per
evaluation in the run the card is pinned to. On NERSC's shared login nodes the time per call
depends on the node and its load. `h_minus_one`'s 2.2 ms was recorded on login05. On login10,
loaded above its 244 cores, one call took 2.7 ms in one measurement and 5.0 ms a few minutes
later (the `wasserstein` agent's interleaved timings, finding 031). Before PR #32, the two
metrics' recorded costs, from different runs, gave a ratio of about 90. Timed in one process,
the ratio was 72, and 28 after the speedup.

Within one run the comparison is sound: `cost_relative` is each metric's cost over the
cheapest in the same run, and the cards pinned to the shared comparison run are
comparable with each other. The catalog's `cost` field puts every card's number side by side,
though, including cards pinned to their own runs (the ensemble metrics on
`synthetic_ensemble`, `shock_set_distance` and `shock_mask_overlap` on Sod).

## What would settle it

Record the host and its load with each run's cost and mark in the catalog which costs share a
run. Or drop the absolute `cost` from the catalog and keep only the within-run
`cost_relative`.
