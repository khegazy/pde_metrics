# Code notes: shock_set_hausdorff95

The coding record of the build of 2026-11-04 (task `metrics-topology-shocks`). The research
record is in [research_notes.md](research_notes.md).

## Summary

One decorated metric and one summary function of two non-empty masks; everything else is imported
from `metrics/shock_set_distance/metric.py`.

## Implementation

The metric is `shock_set_score(reference, candidate, ctx=ctx, score=partial(set_distance,
summary=...))`. `shock_set_score` (extracted from `shock_set_distance` in the same change, also
used by `shock_mask_overlap`) checks shapes against each other and the grid, returns NaN on a
non-finite field, caches the reference's masks under `REFERENCE_MASKS`, and averages the channels;
`set_distance` scores two empty sets 0 and one empty set the domain's diagonal. The refactor of
`shock_set_distance` and `shock_mask_overlap` onto these was checked twice: 520 old-versus-new
comparisons on the exact Sod pressure all identical, and the Sod smoke run's 590 rows of each
matching their cited evidence runs exactly (task log). The companions `shock_positions` (points,
coordinates (x, cells) and (pressure, field)) and `pressure_profile` (named field map `profile`)
are registered by `companion(...)(fn)` calls.

## Tests

`test_metric.py`: the worked example (1.95 and 6.7), the pooled form's 6.5 against this metric's 6.7 on the spike, and HD95 <= HD on random sets. The examples use `SHOCK_STEP`, `SHOCK_STEP_MOVED` and
`SHOCK_STEP_SPIKE` from `tests/conftest.py`, shared by the four siblings. The bundle joined the
spacing-doubling contract test (`tests/test_metric_contract.py`).

## Bugs and fixes

None found.

## Performance

`cost="cheap"`: the Sod smoke run of the six shock metrics scored 5160 rows in 1.0 s of metric
time.

## Tooling and environment problems

As recorded in `persistence_wasserstein/code_notes.md` (shell isolation; no PDF tool).

## For the next agent

- A change to the empty-set conventions belongs in `set_distance` and moves all five distance
  bundles together.
