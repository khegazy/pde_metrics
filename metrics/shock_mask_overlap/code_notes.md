# Code notes: shock_mask_overlap

This is the coding record of the same build (pull request #30), condensed from the builder's
and the reviewer's records. The research record is in [research_notes.md](research_notes.md).

## Summary

`metric.py` is one decorated function that imports the shock detector `shock_mask` from
`metrics/shock_set_distance/metric.py` unchanged, caches the reference's masks for the frame,
and returns the channel mean of the Dice coefficient. The build changed no shared code; outside
the bundle it touched only documentation (the renamed idea page and the links to it, issue 120)
and the regenerated catalog. The review round found two coding defects, a missing grid check that
let a field without its channel axis score a perfect 1 and a Sod test that accepted a wrong value,
both fixed in commit d8deb68 on #30 with a regression test. The bundle has ten tests.

## Implementation

1. **Shape check.** The function raises unless `reference.shape == candidate.shape` and
   `reference.shape[1:] == ctx.grid.shape`, the same condition `shock_set_distance` uses. The
   metric never reads the grid; the grid comparison is what catches a field passed without its
   channel axis (Bugs and fixes).
2. **Non-finite guard.** If either field is NaN or infinite anywhere, the result is NaN, as in
   `shock_set_distance`. The guard runs before the cache is filled, so a non-finite reference
   never leaves masks in the cache.
3. **Reference masks, cached.** `shock_mask(channel)` for each reference channel is stored under
   the key `"shock_mask_overlap/reference_masks"` (the module constant `REFERENCE_MASKS`) on the
   first call for a context. A `ctx.cache` lives for one (frame, field, metric), so the masks that
   `shock_set_distance` caches cannot be shared with another metric. The builder read the brief's
   "reuse its `ctx.cache` use" as the same pattern under a key of its own, and imported
   `shock_mask` rather than copying it. The reviewer confirmed from `fmeval/pipeline.py` that the
   harness builds a new `FieldContext` per (frame, field, metric) and passes the undamaged
   `frame.fields[field]` as the reference (on an ensemble frame the truth, with the damaged member
   mean as the candidate), so the cached masks always belong to the reference passed, and that
   nothing else writes the key.
4. **Dice per channel.** For each channel, with `a` the cached reference mask and `b` the
   candidate's, `flagged = a.sum() + b.sum()`, and the value is `2.0 * (a & b).sum() / flagged`,
   or 1.0 when `flagged` is 0 (two empty sets, the convention of issue 120). The literal 2.0 is the
   factor of Taha & Hanbury (2015), BMC Med. Imaging 15, 29, Eq. (6), recorded in the PR body's
   list of literals. The channel values are averaged; pressure has one channel, so averaging
   rather than pooling cells over channels is untested on data.
5. **Detector constants.** None are restated: the Mach 1.3 and $\gamma = 1.4$ thresholds live in
   `shock_set_distance` and are imported with `shock_mask`.
6. **Decorator.** `arity="pairwise"`, `fields=("pressure",)`, `differentiable=False` (a
   thresholded detector changes in jumps), `cost="cheap"`, `higher_is_better=True`,
   `symmetric=True`, `monotone_under_smoothing=False`, `units="dimensionless"`,
   `requires_periodic=False` (no Fourier transform; the detector extends the field by its edge
   value). `monotone_under_smoothing=False` was measured on the contract test's synthetic blur
   ladder before it was declared: 37 of 128 reference cells flagged, values 1, 0.815, 0.641, 0.5
   and 0.525, Spearman $-0.9$, with float32 and float64 agreeing. The reviewer found the symmetry
   contract test non-vacuous: its synthetic fields flag 38 and 35 cells, and the score is 0.7123
   both ways.
7. **No companion** (card, Definition), and no entry in `tests/test_cards.py` or
   `tests/test_metric_contract.py`: the metric is not differentiable, and it is dimensionless, so
   it carries no power of length.

## Tests

All in `metrics/shock_mask_overlap/test_metric.py`; each expected literal is derived in its
docstring. The shared contract (symmetry, one finite float, shape rejection, float32 agreement,
the declared non-monotone response to blur) is in `tests/test_metric_contract.py`, and the
detector's own threshold and wall handling are tested with `shock_set_distance`.

- `test_worked_example_matches_the_card`: an eight-cell step of ratio 10 against itself moved one
  cell; flagged pairs {3, 4} and {4, 5} share one cell, $2 \cdot 1/(2+2) = 0.5$.
- `test_a_shock_moved_past_its_width_scores_zero_however_far`: shifts of two and three cells both
  give 0, the near-miss saturation.
- `test_empty_sets_score_one_together_and_zero_alone`: two flat fields give 1 (issue 120); a step
  against a flat field gives 0 either way round, $2 \cdot 0/(2+0)$.
- `test_channels_are_averaged`: a one-cell shift (0.5) and two flat channels (1) average to 0.75.
- `test_a_shock_inside_a_cell_is_marked_as_one_to_three_cells` (review round): a cell-averaged
  ratio-10 step with the jump 40% into cell 4 (value 0.46) marks cells 3, 4 and 5 (ratios 2.17, 10
  and 4.6); a step of Sod's ratio with the middle cell at 0.175 marks only cell 3 (ratios 1.73,
  3.03 and 1.75), and that single cell scores $2 \cdot 1/(2+1) = 2/3$ against the sharp pair.
- `test_a_field_without_its_channel_axis_is_rejected` (review round): `(8,)` inputs raise a
  `ValueError` mentioning the grid. It fails on the code before the fix.
- `test_a_non_finite_field_scores_nan`: a NaN in either field, or an infinity, gives NaN.
- `test_the_reference_masks_are_cached_for_the_frame`: after one call the cache holds one mask;
  a flat reference scored against the step with the step's mask still cached gives 1, which only
  the cached mask can give. The reviewer confirmed it would fail if the masks were recomputed.
- `test_on_the_exact_sod_solution_it_scores_the_moving_shock`: the exact Sod pressure at
  $t = 0.1$ on 2048 cells against itself (1), against $t = 0.1 + 2\times10^{-5}$ (exactly 1: the
  shock moves from 1382.34 to 1382.41 cells, still between the centres of cells 1382 and 1383,
  using the shock speed 1.75216) and against $t = 0.11$ (0: a move of 35.9 cells). Tightened to
  exactly 1 in the review round.
- `test_a_pressure_offset_erases_a_shock_in_the_right_place` (review round): an offset of 0.15
  leaves the ratio at $0.45313/0.25 = 1.81 > 1.805$ and the score at 1; an offset of 0.2 gives
  $0.50313/0.3 = 1.68$ and 0.

The suite counts recorded by `agent_verify.sh`: 2137 passed at the pre-registration commit, then
2138, and 2141 passed (295 skipped, 9 deselected, 4 xfailed) after the review round.

## Bugs and fixes

- **A field without its channel axis scored a perfect 1** (review round, found by the reviewer).
  Symptom: the Sod step of shape `(8,)` against its one-cell shift returned 1.0 instead of 0.5.
  Cause: the only shape check compared the two fields with each other, so the loop over channels
  read each cell as a 0-d channel; no 0-d channel can be flagged, so every channel was both-empty
  and scored 1. Fix: the reviewer added the grid check of `shock_set_distance`
  (`reference.shape[1:] != ctx.grid.shape`) and updated the error message and the `Raises`
  docstring; the builder checked it by loading the committed `metric.py` from `git show HEAD`
  under another registry name (committed code 1.0 on `(8,)`, fixed code raises, `(1, 8)` gives
  0.5), and kept it. Commit d8deb68 on #30. Regression test:
  `test_a_field_without_its_channel_axis_is_rejected`, which failed on the committed code
  ("1 failed, 1 passed") and passes after the fix. No evidence number moved, since the pipeline
  always passes `(C, *spatial)` arrays on the context's grid. The same pattern in other bundles is
  under For the next agent.
- **The Sod test accepted a value one cell wrong** (review round, found by the reviewer). The
  assertion `in (1.0, 0.5)` also accepted 0.5, the value of a one-cell displacement, so a defect
  that shifted the candidate's mask by one cell would have passed. The value is deterministic
  (Tests). Fix: assert `== 1.0` with the position derived in the docstring; the builder checked
  the derivation by hand. Commit d8deb68 on #30.
- **A draft test moved the eight-cell step by four cells**, which pushes the jump off the grid and
  leaves no shock. Caught by reading the arrays before running; a three-cell shift is used
  instead.
- **Not fixed: an input with zero channels**, shape `(0, N)`, returns NaN with a NumPy "Mean of
  empty slice" warning rather than an error (the reviewer's side note).

## Performance

- Evidence run `results/shock_mask_overlap_1793494245`: 4.2 s wall time for 590 rows, metric time
  under 0.1 s. The card's profile gives a compute cost of 1 times the cheapest metric and field in
  that run.
- Declared `cost="cheap"`; complexity $O(N)$, one stencil pass per field and a count. Caching the
  reference masks means the reference is passed through the detector once per frame rather than
  once per ladder variant. Nothing further was done about cost.

## Tooling and environment problems

- The sandbox refused a multi-file heredoc into the findings folder; each record was written with
  the Write tool.
- Scratch scripts could not be run as `python <script>.py`, because Python puts the script's
  folder, not the worktree, on the import path; they were run as
  `python -c "import runpy; runpy.run_path(...)"`.
- Loading the committed `metric.py` beside the fixed one first failed with a duplicate registry
  name; resolved by renaming the old copy's registered name in the scratch script (not kept).
- `gh` was not installed, so the pull request was opened through the GitHub connector; no
  `agent-metric` label existed, so none was applied.
- No PDF text tool was available, so Martin et al. 2004 could not be read and the Metrics
  Reloaded PDF fetch failed on its size limit; the summarising fetch tool also mislabelled a
  section (research_notes.md, Review round).
- The first `agent_verify.sh` self-check failed only because the PR body did not yet list the
  literal 2.0. The orchestrator's checker first failed to match a source title written in JATS
  markup and was fixed by the orchestrator (31 checks passed, then 33 after the review round); it
  left as manual items the sources read through a PMC or arXiv copy rather than fetched by DOI,
  and the one idea-page pitfall.

## For the next agent

- A field without its channel axis is not caught by the registry's contract tests. Called with a
  32-cell field missing its channel axis, `increment_w1` and `energy_distance` return NaN with a
  NumPy warning instead of raising, `max_error` returns the right value, and `spectrum_l2`,
  `spectral_energy_flux` and `persistence_distance` raise; none returns a confident wrong number,
  so nothing outside this bundle was changed. A contract test that such a field raises would cover
  all of them: [issue 109](../../issues/109-pointwise-controls-accept-broadcastable-shapes.md).
- The cache's correctness rests on the pipeline building a fresh context per (frame, field,
  metric) and on the reference argument being the same array for every ladder variant of a frame;
  a change to `fmeval/pipeline.py` that broke either would make the cached masks stale silently.
- Averaging Dice over channels, rather than pooling cells over channels, has never been exercised
  on data, since pressure has one channel.
- Zero-channel input returns NaN with a warning rather than raising.
