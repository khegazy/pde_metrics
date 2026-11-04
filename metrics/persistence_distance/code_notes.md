# Code notes: persistence_distance

This is the coding record of the same build (pull request #29, merged as 16c08b1), condensed from
the builder's and the reviewer's records. It also covers the shared point-set companion kind this
launch added to the harness. The research record is in [research_notes.md](research_notes.md).

## Summary

`metric.py` holds the registered metric `persistence_distance`, its point-set companion
`persistence_diagram` (the diagram of one field), and two exported helpers, `betti_curves` and
`euler_characteristic_curve`, for a future metric built on those curves. The launch also added a
third companion kind, `kind="points"`, to the registry, the pipeline and the report, so that a
metric can store an `(N, D)` point set per frame; shock positions can use it unchanged. The review
round found no coding bug in the bundle; it led to a fix of the point-set renderer's panel order,
documentation fixes in shared docstrings, and three tests. The full suite passed after the round
(2111 passed, 284 skipped, 9 deselected, 4 xfailed).

## Implementation

**The metric.** `persistence_distance` checks that the shapes match, computes the reference's
diagram once per frame and caches it in `ctx.cache` under `REFERENCE_DIAGRAM`, and takes the
candidate's diagram from `ctx.cache[COMPANION_KEY]` when the pipeline has computed it, or
computes it otherwise. For each homology dimension $k = 0, \dots, n$ (`range(reference.ndim)`,
since the array carries one channel axis plus $n$ spatial axes) it splits out the (birth, death)
rows of that dimension, and returns 0 for the term when the two sorted arrays are equal
(`np.lexsort` then `np.array_equal`), else calls `gudhi.bottleneck_distance(a, b)` at its
default precision. The value is the maximum of the terms (Skraba & Turner 2020, Eq. 1; card,
Definition).

**The identical-diagram shortcut** exists because gudhi is slowest on identical diagrams (about
5 s at 256 x 256, where it returns 1.5e-308 rather than 0; see Performance). The identity
bijection makes 0 exact, and the shortcut removes the slow case for every whole-cell translation.
The reviewer checked it is correct with infinite entries, repeated rows and empty `(0, 2)` arrays.

**The companion.** `persistence_diagram` refuses more than one channel and any non-finite value,
builds `gudhi.PeriodicCubicalComplex(top_dimensional_cells=x[0], periodic_dimensions=[b == "periodic" for b in ctx.grid.boundary])`,
computes persistence, and returns an `(N, 3)` array of rows (birth, death, dimension), ordered by
dimension. The gudhi conventions it relies on were measured with gudhi 3.13.0 by the builder and
re-checked by the reviewer:

- `periodic_dimensions` follows the numpy array's own axis order (`[True, False]` wraps axis 0).
- Built from `top_dimensional_cells`, every lower cell takes the minimum of its adjacent top
  cells (read off `CubicalComplex.all_cells()`), so cells touching only at a corner are connected:
  the T-construction. Built from vertices instead, the same corner-touching minima stay separate.
- The final complex has Betti numbers [1, 2, 1] doubly periodic, [1, 1, 0] periodic in one axis,
  [1, 0, 0] in none.
- The default coefficient field is $\mathbb{Z}/11$, and the default `min_persistence=0.0` keeps
  only intervals strictly longer than it, so zero-length intervals are dropped.
- `bottleneck_distance` matches points at infinity among themselves at cost $|b_1 - b_2|$, returns
  `inf` when their counts differ, and returns `inf` for a $-\infty$ birth.

**`betti_curves`** counts, per dimension, the points with $b \le t < d$ at each threshold;
`euler_characteristic_curve` takes the alternating sum. This metric does not use them.

**Decorator declarations.** `arity="pairwise"`, `fields=("density", "vorticity")` (vorticity is
one channel in 2-D only), `differentiable=False`, `cost="expensive"`, `higher_is_better=False`,
`symmetric=True`, `units="field"`, `requires_periodic=False` because the complex wraps exactly
the axes the grid declares and nothing is padded. The reasons for `differentiable` and `cost` are
in research_notes.md, Method choices. The only numeric literal besides 0 and 1 is 2, structural:
the width of a reshaped interval array and the column index of the dimension in the companion's
rows. `import gudhi` at module level costs 23 ms (measured by the reviewer with
`python -X importtime`), so it does not conflict in practice with AGENTS.md's rule on heavy
imports.

**Shared-test lists not joined.** The brief named `differentiable` and `cheap` as triggers for the
catalog test's literal list; the metric is neither, so it was not added. It carries no power of
length beyond the field's own units, so it was not added to the spacing-scaling parametrisation
either.

**The harness change: the point-set companion kind.** Declared as
`@companion(of=..., kind="points", coordinate=(("birth", "field"), ("death", "field"), ...))`;
it returns an `(N, D)` array, one row per point and one named column per coordinate.

- `metrics/registry.py`: `"points"` beside `"field"` and `"curve"`; the declaration check needs at
  least two `(name, units)` columns; a one-field signature is allowed for a pairwise metric, as for
  a curve; `describe()` writes the column pairs as plain lists.
- `fmeval/pipeline.py`: a point set is called before the metric on every row and handed over
  under `COMPANION_KEY`, as a curve is, and is stored, as a per-cell map is, only on the frames,
  ladder entries and fields that `report.error_map` names, plus the clean level of those frames,
  in the same `error_maps.npz` under the same key. One selection decides which frames keep their
  companions, so no config key was added. This was chosen over a second store and a second
  selection, for one source of truth. The curve path now reads the curve back from the cache
  (`zip(*ctx.cache[COMPANION_KEY])`) instead of from local names; the reviewer read the three
  curve metrics and found none writes to or mutates the cached arrays.
- `fmeval/report/plots.py`: the renderer `companion_points` draws the stored sets on shared axes,
  the first two coordinates as axes and a third as colour, infinite coordinates as triangles on
  the panel's edge. `field_gallery` skips point sets by the companion kind read from the run's
  registry snapshot; `_companion` and `_axis_label` are shared with the curve renderer. After the
  review, panels are ordered by parsed frame index with the clean level first in each frame, the
  caption says when more sets were stored than drawn, and one constant `_MAX_PANELS = 12` replaces
  the literal 12 that `field_gallery` also used (no change to the gallery's output).
- `fmeval/io.py` and, after the review, `fmeval/context.py`: docstrings say `error_maps.npz` and
  `COMPANION_KEY` hold point sets as well as curves.
- Documentation: `TEST_DESCRIPTION.md` (point sets in `error_maps.npz`; the `companion_points`
  figure), `AGENTS.md` §3.3 and `docs/recipes/add-a-metric.md` step 2 (one bullet each).

The builder's design choice that a point set is always stored on the clean level of the chosen
frames, even when `report.error_map.axes` does not list it, is its own; it flagged that a reviewer
might prefer users to add the reference explicitly. On ensemble data that clean-level set is the
member mean's, not the reference's (see Bugs and fixes).

## Tests

In `metrics/persistence_distance/test_metric.py`, every expected value is derived in the test's
docstring:

- `test_worked_example_from_the_card`: the 4 x 4 periodic two-wells field. Its diagram is derived
  by hand as H0 = {(-1, inf), (0, 1)}, H1 = {(1, inf), (1, inf)}, H2 = {(1, inf)}. Moving the
  shallow well gives distance 0 against `max_error` 1; filling it leaves (0, 1) matched to the
  diagonal at half its lifetime, 0.5, against `max_error` 1.
- `test_betti_and_euler_curves_of_the_worked_example`: Betti numbers (1, 0, 0), (2, 0, 0),
  (2, 0, 0), (1, 2, 1) at thresholds -1, 0, 0.5, 1, and Euler characteristics 1, 2, 2, 0, counted
  by hand from the intervals $[b, d)$.
- `test_the_euler_curve_matches_a_direct_count_of_cells`: the Euler-Poincare formula checked at
  every threshold of a random periodic 8 x 6 field, the Betti side from the diagram and the cell
  side from gudhi's own filtration of every cell (dimension = number of odd index entries). The
  reviewer noted this test also confirms the half-open convention at thresholds equal to cell
  values.
- `test_a_whole_cell_translation_on_a_periodic_grid_is_at_distance_zero`: three periodic rolls
  give exactly 0 while `max_error` is positive.
- `test_the_distance_never_exceeds_the_largest_pointwise_difference`: Equation (5), on blurred,
  noisy and unrelated candidates, with a factor $1 + 10^{-12}$ for gudhi's last-bits error. In the
  review round it was parametrised over seven grids (2-D periodic, mixed and walled; 1-D periodic
  and walled; 3-D periodic and mixed), each candidate with a fresh cache. The reviewer had run 600
  random cases over 1-D, 2-D and 3-D grids with mixed boundaries: the largest ratio
  PD / `max_error` was 1.000000000000000, one case above 1 by less than 1e-15 relative. This test
  widens coverage and guards no fixed bug.
- `test_the_first_grid_axis_is_the_first_axis_of_the_complex` (review round): a band of zeros down
  column 0 of a 4 x 4 field of ones. Wrapping axis 0 closes a loop at threshold 0, H1 = [(0, inf)];
  wrapping axis 1 needs a whole row, which first exists at 1, H1 = [(1, inf)]. With
  `periodic_dimensions` reversed in `metric.py` on purpose,
  `python -m pytest -q -p no:cacheprovider metrics/persistence_distance -k "axis or wrapped"` gave
  "1 failed, 1 passed" (the new test fails, the old Betti test passes); restored, "2 passed". The
  code was already right; the old test could not catch the mistake because a cylinder has Betti
  numbers (1, 1, 0) whichever axis wraps.
- `test_only_the_axes_the_grid_declares_periodic_are_wrapped`: Betti numbers (1, 2, 1), (1, 1, 0),
  (1, 0, 0) above the field's maximum for torus, cylinder and disk.
- `test_a_vector_field_or_a_non_finite_cell_is_refused`: a two-channel field and a NaN cell raise.

Shared tests the build changed:

- `tests/test_metric_contract.py`: `test_a_point_set_has_one_column_per_declared_coordinate`; the
  cache test now covers curves and point sets (the pipeline computes the companion once per row
  and the metric reads it); the declaration test refuses a point set with fewer than two named
  columns and checks the one-field signature.
- `tests/test_report.py`: `test_a_point_set_is_stored_on_the_chosen_frames_and_drawn` (stored on
  the chosen frames and the clean level, handed to the metric, drawn with its point at infinity,
  left alone by the gallery) and, from the review round,
  `test_point_set_panels_run_in_time_order_and_stop_at_twelve` (frames 2 and 10 with seven sets
  each; panels run seven of frame 2, then five of frame 10, clean level first in each). With the
  old string sort put back,
  `python -m pytest -q -p no:cacheprovider tests/test_report.py -k "time_order"` failed with
  `assert [10, 2, 10, 2, 10, 2, ...] == [2, 2, 2, 2, 2, 2, ...]`; with the fix, "1 passed".

## Bugs and fixes

No coding bug was found in the bundle, during the build or the review. The review's code-level
critiques and their outcomes:

- **`companion_points` sorted frames as strings and dropped panels silently past twelve.** Found
  by reading: the key `t10000` sorts before `t2000`, and with two frames stored, ten of twenty
  degraded sets would be dropped with no log line. Nothing was lost on the evidence run (11 sets
  per field on one frame). Fixed in commit 5cc157c on #29 (parsed frame index, caption on
  truncation, shared `_MAX_PANELS`), with the regression test above. `field_gallery` has the same
  string sort; that line predates the branch and was not fixed (see issue 117 below).
- **On ensemble data the stored clean-level point set is the member mean's, not the reference's.**
  The reviewer ran the real pipeline on `SyntheticEnsembleTrajectory`: the stored set equalled the
  member mean's diagram, and the clean row's values were 0.306 and 0.357, not 0, because the
  ladder's clean candidate on an ensemble frame is the member mean (`fmeval/ladder.py`). Four texts
  (the `MapRequest` docstring and storage comment in `fmeval/pipeline.py`, the
  `companion(kind="points")` docstring in `metrics/registry.py`, `TEST_DESCRIPTION.md`, and the
  card's Reading the output) said it was the reference's. Fixed in 5cc157c by correcting the texts
  to "the undamaged prediction's set"; storing the reference's own set under a second key was
  rejected as a new store path for a figure only. No number was affected.
- **A two-field point-set companion's clean-level set is `companion(reference, reference)`**, a
  comparison of the reference with itself, which the pipeline comment did not allow for. Fixed with
  the item above: the registry docstring now distinguishes one-field and two-field companions.
- **`fmeval/context.py` described `COMPANION_KEY` as holding only a curve.** Both docstrings fixed
  in 5cc157c.
- **The reference diagram is cached by name only, so a reused context compares against a stale
  reference.** Reproduced: `d(a, b)` 0.11483840387427577 on a fresh context, `d(b, a)` 0.0 on the
  same context reused (the reviewer's own case gave 0.608 against 0.0); a stale `COMPANION_KEY`
  likewise gives `d(a, a)` = 0.608. Rejected as a fix in this bundle: four bundles rely on the
  documented one-context-per-(frame, field, metric) contract (`persistence_distance`,
  `spectral_energy_flux` and `increment_w1_by_separation` cache a reference quantity; those three
  and `tail_index` read `COMPANION_KEY`), and the pipeline, the only caller that hands a context
  to a metric, honours it (`fmeval/cards/exemplars.py` builds contexts for degradations only). A
  harness-level guard, for example a cache tied to the reference array, would protect all of them.
  Routed to [issues/116](../../issues/116-context-cache-trusts-one-context-per-frame.md); the
  orchestrator added `shock_set_distance`, which also caches the reference.
- **A 3-D dataset with vorticity would stop the whole run.** `MetricSpec.accepts` matches by name,
  the registry cannot declare accepted grid dimensions or channel counts, and the pipeline has no
  handler around a metric call, so the companion's refusal of three-component vorticity would lose
  every other metric's rows. No 3-D dataset exists. Documented on the card with the workaround
  `fields=[density]`; the harness gap, together with `field_gallery`'s string sort, is
  [issues/117](../../issues/117-one-metric-error-stops-the-run.md).

## Performance

- On a synthetic 256 x 256 periodic field with a $k^{-3}$ spectrum (about 2900 H0 and 5300 H1
  points): persistence under 0.1 s; `gudhi.bottleneck_distance` at its default `e` about 0.35 s
  for H0 and H1 together, about 5 s when the diagrams are identical (a periodic roll), and 10-26 s
  per pair with `e=0`, the exact algorithm. This led to the identical-diagram shortcut and to the
  default precision.
- About 0.4 s per comparison at 256 x 256, the basis of `cost="expensive"`.
- Evidence run `results/persistence_distance_1793439285`: 7684 s wall time for the whole run
  (metrics 6718 s), and per evaluation 0.0938 s on density and 0.664 s on vorticity (the
  fingerprint's `cost_s`). The smoke run on `kinet_re5e4_dev` with `degradation=quick` took 386 s.
- The Wasserstein variant measured about eight times the bottleneck's cost on a 64 x 64 field
  (research_notes.md, Rejected formulations).

## Tooling and environment problems

- The first exploration script ran more than ten minutes with no output: stdout was buffered and
  the exact bottleneck algorithm on 256 x 256 identical diagrams is slow. Rerun with `-u` and
  smaller grids.
- No PDF tool was installed, so the builder wrote a small zlib text extractor to read the
  Cohen-Steiner PDF (not kept in the repository). The Martinez et al. 2026 PDF did not extract:
  its fonts are CID-encoded and the extractor recovered only glyph indices. The reviewer's
  extractor ran over two minutes without finishing (a non-greedy regex over 7 MB).
- The sandbox refused a Python heredoc that edited `fmeval/pipeline.py`, as the brief warned; the
  Edit tool was used instead. An earlier heredoc that edited `metrics/registry.py` was allowed.
- `latexmk` was absent, which only skips compiling. `gh` was not installed, so the draft PR was
  opened through the GitHub connector; no `agent-metric` label exists.
- The orchestrator's audit check gave 70 PASS and 1 FAIL: the PR body's "What was added" did not
  name the deleted idea page `docs/ideas/topology/persistence_diagrams.md`; the body was corrected.
  The source copies were verified by hand.
- The orchestrator's verification script (`agent_verify.sh persistence_distance`, kept outside the repository) passed every step after the review round
  (cards-check with one warning, the unsigned card; ruff; catalog; pytest; `mkdocs --strict`;
  card-coupling; selfcheck).

## For the next agent

- A refactor gate at rtol 1e-12 on the curve path was still outstanding when the builder finished;
  the orchestrator then ran it and found the curve path bitwise unchanged on `kinet_re5e4_dev`
  with `degradation=quick` (`increment_w1_by_separation`, `spectral_energy_flux`).
- A comparison folder holding a per-cell-map metric beside a point-set metric rendered correctly
  in the reviewer's smoke run (`mse` and `persistence_distance`), but this is not a committed test.
- The cache keyed by name only (issue 116) and the 3-D refusal stopping the run (issue 117) are
  harness gaps a new caller or a 3-D dataset would hit first.
- Whether the clean level should always be stored for a point set, rather than only when the user
  lists it, is the builder's design choice and was not reviewed as a question.
