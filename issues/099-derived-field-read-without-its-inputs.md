# A derived field read without its inputs is scored on the solver's operator, not ours

**Category:** pipeline / data
**Priority:** medium
**Status:** open in part. `evaluate.py::select_fields` now reads a derived field's inputs
whenever the dataset recomputes derived fields, so no run of `evaluate.py` scores the stored
operator (`tests/test_pipeline.py::test_a_derived_field_is_read_with_its_inputs`). What remains is
the direct path: `RecomputingTrajectory.frame(t, ["vorticity"])` called without velocity still
keeps the stored field, pinned by the strict xfail below.

## Context

`fmeval/derived.py` replaces the solver's stored vorticity, a D2Q9 lattice stencil, with a
spectral curl of the velocity at every analysis grid, because the two differ by 8.1% rms on
the native grid and mixing them would make a grid comparison measure the operator. Its module
docstring states the rule: never mix a stored derived field with a recomputed one.

The rule holds only when velocity is read. `evaluate.py::select_fields` reads the fields the
chosen metrics accept, so a run whose metrics accept only vorticity (`metrics=[enstrophy]`,
`metrics=[palinstrophy]`, or `fields=[vorticity]`) never reads velocity. Then:

- `RecomputingTrajectory` finds nothing to recompute from and keeps the stored lattice-stencil
  vorticity (`fmeval/derived.py::recompute_frame`, "a derived field whose inputs are absent is
  kept");
- on a coarser analysis grid `remap_frame` block-averages that stored vorticity, the fallback
  its own comment calls "wrong in principle" (`fmeval/remap.py`).

Neither path warns.

## Evidence

The test pipeline call of
`tests/test_capabilities.py::test_h_minus_one_is_more_displacement_tolerant_than_the_l2_baseline`
(`kinet_re5e4`, t = 5000..6000, reduction 250, translations and `mean_field`), run twice and
compared on vorticity only:

| fields read | `mse` of `mean_field` (= variance) | `mse` damage at 1 / 4 / 16 cells | `h_minus_one` damage at 1 / 4 / 16 cells |
|---|---|---|---|
| vorticity only | 6.19e-6 | 0.068 / 0.559 / 1.167 | 0.031 / 0.119 / 0.408 |
| velocity and vorticity | 6.56e-6 | 0.095 / 0.657 / 1.196 | 0.032 / 0.121 / 0.409 |

The same metric on the same frames reports a 40% different damage at one cell depending on
which other metrics ran beside it. The pinned evidence run (`comparison_1793657627`) reads
velocity, so every committed card uses the spectral vorticity; a single-metric run of a
vorticity-only metric does not, and its numbers are not comparable with the card's.

`tests/test_pipeline.py::test_a_derived_field_is_the_same_whether_or_not_its_inputs_are_requested`
reproduces it on the `write_kinet_raw` fixture and is marked `xfail(strict=True)`.

On `forecast_re5e4` the stored field would be wrong by a factor, not a few percent: the stored
vorticity of a coarse run's prediction is computed at unit grid spacing and its target's at the
physical spacing, so at the first step of the $128^2$ run the prediction's is about 1.9 times
the target's for the same velocity (`docs/datasets/reynolds_ladder_2d.md`, "Forecast pairs").
Its reader therefore refuses vorticity requested without velocity, which turns this issue into an
error there; a `metrics=[enstrophy]` run on it fails until this is fixed.

## What would fix it

Read a derived field's inputs whenever the field is read, carry them through the remap and
the recomputation, and score only the fields the metrics asked for. The inputs are listed once,
in `fmeval/derived.py`'s table of derived fields. The open design point is where the extra
fields are dropped: after the remap (`fmeval/pipeline.py`), so that the coarse-grid
recomputation also has its inputs.

## Acceptance

The xfail test passes and its marker is removed; a `metrics=[enstrophy]` run and a
`metrics=[enstrophy,kinetic_energy]` run report the same enstrophy rows.
