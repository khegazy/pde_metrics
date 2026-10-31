# The cost warning ignores grid size, and a stored map is computed beside its metric

**Category:** technical debt
**Priority:** low — it costs time, not correctness
**Status:** open.

## Context

`fmeval/pipeline.py` warns about an `expensive` metric only when more than 500 frames are
evaluated; it never considers the analysis grid. And on frames whose maps are stored, it calls a
metric's field companion (`pipeline.py`, the `companion.kind == "field"` branch) as well as the
metric itself, so a metric whose value is the sum or mean of its map is computed twice there.

Found by the agent that built `variogram_score` (finding 021, adversarial review 2026-10-30), whose
cost grows with the square of the number of cells.

## Evidence

`variogram_score`, sixteen members, as measured by that agent: 0.12 s, 1.41 s and 17.8 s per
evaluation at 32², 64² and 128²; by the same scaling, over an hour at 512².

## Options

1. Warn by an estimate of cells times frames, or let a metric declare how its cost grows.
2. Where a metric's declared reduction of its map equals its value, take the value from the map on
   frames whose maps are stored.
