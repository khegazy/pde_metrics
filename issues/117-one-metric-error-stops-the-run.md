# One metric's error stops the whole run, and a metric cannot declare which grids it accepts

**Category:** technical debt
**Priority:** low — no current dataset triggers it
**Status:** open.

## Context

The registry (`metrics/registry.py`, `MetricSpec.accepts`) matches a metric to a field by name
only. A metric cannot declare the number of spatial dimensions or channels it accepts. The
pipeline (`fmeval/pipeline.py`) wraps the degradation in a `try`, but not the metric call, so a
metric that refuses a field it declared stops the run and loses every other metric's rows.

`persistence_distance` declares `vorticity` and takes one scalar channel. On a 3-D dataset,
vorticity has three components, so the metric raises `ValueError` and the whole run stops. Its
card documents this and gives the workaround of running it with `fields=[density]`.

A related ordering defect sits in the same report code. `field_gallery`
(`fmeval/report/plots.py`) orders its panels with `sorted(stored)`, sorting the map keys as
strings, so frame `t10000` is drawn before `t2000`. `companion_points` was fixed to sort by the
parsed frame index; `field_gallery` was not.

Found by the agent that built `persistence_distance` (finding 025, adversarial review
2026-10-31).

## Options

1. Let a metric declare the spatial dimensions and channel counts it accepts, and skip
   (with a recorded reason) a field that does not match.
2. Catch a metric's exception per row, record it as a failed row with its reason, and carry on.
3. Sort `field_gallery`'s panels by the parsed frame index, as `companion_points` does.
