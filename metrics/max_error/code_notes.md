# Code notes: max_error

This is the coding record of the build in pull request #25, condensed from the builder's and the
reviewer's records. The research record is in [research_notes.md](research_notes.md).

## Summary

`metric.py` holds the metric `max_error`, its companion `max_error_map` and one helper,
`absolute_error`, which both call and `max_error_channel_mean` imports. The build added a `max`
entry to `REDUCTIONS` in `metrics/registry.py`. In the review round it made three further changes outside the bundle: it
documented the reductions in AGENTS.md §3.3, made the map-reduction contract test run on two
channels, and tightened a documentation test. No fix changed a number the metric produces. The
bundle was merged with every verification step passing.

## Implementation

- **The number.** `max_error` returns `float(absolute_error(reference, candidate).max())`, the
  maximum over every (channel, cell) entry, which is Roy (2005) Eq. 7 with channels pooled.
- **The map.** `max_error_map` returns `absolute_error(...).max(axis=0)`: the absolute error at
  each cell, the largest over channels. Its maximum is the metric.
- **`absolute_error`** (added in the review; called by the metric, its map and
  `max_error_channel_mean`) raises `ValueError` when the two shapes differ, then returns `np.abs(reference - candidate)`. It follows the inline check that
  `increment_w1` already makes.
- **Constants.** There are no numeric literals at all.
- **Decorator.** `arity="pairwise"`, `fields=("*",)`, `differentiable=True` (piecewise linear: a
  gradient wherever one entry attains the maximum with nonzero error, and a subgradient at ties
  and at zero), `cost="cheap"`, `higher_is_better=False`, `symmetric=True`, `units="field"` and
  `reduction="max"`. `requires_periodic` is left False and `monotone_under_smoothing` at its
  default, True; the reviewer found both consistent with the code and the evidence.
- **Docstring contract.** NaN propagates, as in the controls. An empty field raises (numpy's
  "zero-size array to reduction operation maximum"), which is louder than the controls' NaN.
  Readers return float64, so integer input is outside the contract.
- **Changes outside the bundle.**
  - `metrics/registry.py`: a one-line `max` entry in `REDUCTIONS`, `lambda m, c: float(m.max())`,
    which ignores the channel count. AGENTS.md §3.3 sanctions adding a reduction there, and no
    existing number changes. In the review the comment above `REDUCTIONS` was reworded: the
    channel-sum convention now belongs to `mean`, `sum` and `sqrt_mean`, and the maximum over
    channels to `max`.
  - `tests/test_cards.py`: `max_error` joins the literal set in
    `test_the_catalog_supports_the_query_it_exists_for` (differentiable, cheap, measured). In the
    review its comment was corrected (research_notes.md, Review round, the point about differentiability).
  - `AGENTS.md` §3.3, `tests/test_metric_contract.py` and `tests/test_documentation.py`, all in
    the review (Bugs and fixes).
  - `docs/catalog.json` was regenerated.

## Tests

`metrics/max_error/test_metric.py`:

- `test_worked_example_from_the_card`: the card's four-by-four example. A unit square moved by one
  cell scores 1, at half height it scores 0.5, and a one-cell spike scores 1 while `mae` charges
  it $1/16 = 0.0625$.
- `test_a_jump_on_a_cell_face_costs_its_full_height_at_every_shift` (added in the review): a
  plateau of height 1, two cells wide, with both edges on cell faces in an 8-cell row. Shifts of
  1, 2 and 3 cells, never wrapping, all score 1. It replaced the first round's test, which passed
  only because `np.roll(..., 2, axis=2)` on a 4-cell axis wrapped the square round the boundary.
- `test_a_jump_inside_a_cell_costs_half_its_height_at_a_one_cell_shift` (added in the review): a
  step whose face sits mid-cell, so that cell holds 0.5. It scores 0.5 at one cell and 1.0 at two,
  which pins Equation (4) of the card at $a = 1/2$.

  The two jump tests pin the corrected card prose, not a code bug, and pass with the unchanged
  arithmetic. The varying-background case is not tested.
- `test_channels_are_pooled_into_one_maximum`: channel errors of 0.25 and 0.5 in different cells
  give 0.5, not PDEBench's $(0.25 + 0.5)/2 = 0.375$. In the review it also checks the map cell by
  cell (0.25 and 0.5, the largest over channels, not a channel sum).
- `test_a_shape_mismatch_that_numpy_would_broadcast_is_refused`, parametrised over the metric and
  the map (added in the review): one channel against two must raise.

Shared tests the build changed:

- `tests/test_metric_contract.py::test_pointwise_map_reduces_to_metric` now also runs on two
  channels for every metric declaring `fields=("*",)`. `_args_for` gained an `n_channels` argument
  whose default keeps the old behaviour. All six metrics with a field map pass it: `h1_seminorm`,
  `h_minus_one`, `mae`, `max_error`, `mse` and `rmse`.
- `tests/test_documentation.py::test_agents_api_claims_match_the_code` now requires each reduction
  name in backticks.

Verification: before the review, `agent_verify.sh` exited 0 at every step, with pytest at 1878
passed, 200 skipped, 9 deselected and 2 xfailed in 233 s. After the review, on the tree committed
as 9a211e0 on #25, every step again exited 0, with pytest at 1881 passed in 242 s and the catalog
unchanged. The reviewer ran `python -m pytest metrics/max_error tests/test_metric_contract.py -q
-k max_error`, which gave 14 passed and 7 skipped.

## Bugs and fixes

No present bug was found in the metric's arithmetic. These are the review's code findings, each
fixed in commit 9a211e0 on #25 with a regression test shown to fail without its fix.

- **The `max` reduction was never exercised on two channels** (likely future bug; high
  confidence). `max_error` declares `fields=("*",)`, so the contract test used one channel, where a
  channel-summed map and a channel-maximised map coincide. The bundle's own channel test never
  called the map. A future metric pairing `reduction="max"` with a `mae`-style summed map would
  have passed the whole suite and been wrong on velocity. The reviewer's check gave
  "summed map, C=1 agrees: True ; C=2 agrees: False (6.983 vs 4.297)"; `max_error` itself was
  correct on two channels. **Fix**: the two-channel pass of the contract test, and a map check in
  the bundle's channel test. With `max_error_map` temporarily summing over channels,
  `python -m pytest tests/test_metric_contract.py -q -k "map_reduces and max_error"` gave
  "AssertionError: max_error: reduction 'max' of the 2-channel map gives 0.2804006186998222, but
  the metric gives 0.2001762645545483 ... 1 failed". With the map restored it passed.
- **AGENTS.md still said maps are summed over channels, and its guard test matched "maximally"**
  (documentation; high confidence). AGENTS.md stated the sum convention as universal
  and did not document `max`. `test_agents_api_claims_match_the_code` checked `name in text` as a
  substring, and "max" occurred in AGENTS.md only inside "maximally". **Fix**: AGENTS.md §3.3 lists
  all four reductions in code quotes and adds a `max` bullet (its map is maximised over channels,
  and its reduction ignores $C$). The `mean` bullet now reads "a map reduced by `mean` is summed
  over channels". The `kind="field"` bullet says "per-cell quantity (a density for a mean or a
  sum, the error itself for a maximum)". The tightened test, run before the AGENTS.md edit, failed
  with "AssertionError: reduction 'sum' is undocumented in AGENTS.md", so `sum` had also passed
  the substring check unseen, inside words such as "summary". After the edit,
  `python -m pytest tests/test_documentation.py -q` gave 130 passed.
- **No input validation** (minor; high confidence). `max_error` accepted shapes numpy
  can broadcast: $(1,8,8)$ against $(2,8,8)$ returned 0.1000, and $(1,8,8)$ against $(1,8,1)$
  returned 3.190. The contract's shape test uses $16\times8$ against $16\times10$, which cannot
  broadcast, so it could not catch this. `uint8` 0 against 1 gave 255. An empty array raised
  `ValueError`, where every control returns NaN with a warning. **Fixed for shape**: the
  `absolute_error` check and its regression test, which gave "2 failed, 4 passed" before the
  check and "6 passed" after. The agent's `response_edge.py` (not kept) then showed `ValueError`
  for both broadcastable cases. **Rejected with evidence for the rest**: every reader returns
  float64 (`fmeval/data/base.py`, `np.ascontiguousarray(..., dtype=np.float64)`; AGENTS.md §3.3,
  "Both receive `(C, *spatial)` float64 arrays"), so integer input is outside the contract; an
  empty field raising is louder than NaN; and NaN propagates as in the controls. All three are now
  stated in the docstring.
- **The same broadcasting gap in the controls.** `mae`, `mse`, `rmse` and `nrmse` (since renamed
  `vrmse`, which now refuses) also return a number for $(1,8,8)$ against $(2,8,8)$. The pipeline always feeds matching float64 arrays, so
  only direct callers, such as a training loss, are exposed. Those bundles are outside this branch.
  The orchestrator reproduced the problem and wrote
  [issues/109](../../issues/109-pointwise-controls-accept-broadcastable-shapes.md), with the options
  of adding a broadcastable case to the contract test and a check to each control, validating
  shapes once in the pipeline, or accepting it.

## Performance

- **Smoke run** `results/max_error_1793354376`: 3000 rows in 20 s on `kinet_re5e4_dev`.
- **Evidence run** `results/max_error_1793355020`: 28497 rows in 907.7 s, of which 7.7 s was input
  and output, 885.7 s the degradations and 2.7 s the metric, on 161 frames of the 256 grid.
- **The full default test suite** before the first commit: 1877 passed in 358 s.
- `cost="cheap"` is declared. Nothing was done about cost, and none was needed.

## Tooling and environment problems

- **No PDF tool.** No pdftotext, pdftoppm, pypdf or fitz was installed, and WebFetch returned raw
  PDF bytes. The agent wrote a small inflate-and-extract stream decoder (`pdftext.py`, not kept)
  and read equation numbers from its text, which loses symbols (Roy's infinity subscript read as
  "L1"). The reviewer wrote its own decoder for the same purpose.
- **A truncated download.** The arXiv PDF of PDEBench arrived truncated, so Appendix B was read
  from the ar5iv HTML.
- **Sandbox refusals.** The sandbox refused a heredoc that wrote several findings files at once,
  so each was written with the editor. It also refused a background command that redirected the
  `agent_verify.sh` output, and a one-line `python -c` that mentioned `git` in a dictionary key.
  Both were rerun as plain commands or as a small script. The reviewer confirmed that the first,
  failed `agent_verify` call in the command log was that refused redirect.
- **A clean tree for the evidence run.** A second, one-file commit tracked `_generated/.gitkeep`
  after the declaration commit, so that the evidence run would see a clean tree.
- **Scratch scripts imported the wrong `metrics` package.** A script run with plain `python`
  imports `metrics` from the main checkout (the editable install) unless it puts the worktree root
  on `sys.path`. The agent's and the reviewer's scripts did so, and the agent's printed the module
  path to confirm it was the worktree's. `pytest` and `evaluate.py` are not affected, because they
  run from the root.
- **No `agent-metric` label** existed on GitHub, so the PR was left unlabelled.
- **`latexmk` absent.** It matters only for compiling reports.

## For the next agent

- The builder's first check would be that the `max` reduction comment in `metrics/registry.py` is
  accurate and that no other code assumes channel-summed maps. The review's two-channel contract
  test now covers the six metrics with a field map.
- The `field_gallery` renderer still clips the worst cell
  ([issues/108](../../issues/108-field-gallery-hides-the-cell-a-maximum-map-is-about.md)), so read
  a maximum map's value from the stored arrays, not from the figure.
