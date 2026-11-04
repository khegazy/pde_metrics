# Code notes: shock_set_distance

This is the coding record of the same build (pull request #22), condensed from the builder's and reviewer's records. The research record is in [research_notes.md](research_notes.md).

## Summary

`metric.py` holds three functions. `shock_mask` is the detector, written as shared code for the shock metrics that follow; `shock_mask_overlap` imports it. `surface_distances` is an exact Euclidean distance transform at the grid spacing that never wraps. The third is the registered metric, which pools the two directions into the average symmetric surface distance (ASSD). The review round fixed two bugs in commit 0fdab79 on #22: the inverted ranking on a non-positive pressure, and the silent scoring of a non-finite input. It also fixed a float32 edge case, added four regression tests and tightened the Sod test. At the end, 11 bundle tests and 10 contract tests passed. The full suite gave 1884 passed, 202 skipped, 9 deselected and 2 xfailed.

## Implementation

- **The detector (`shock_mask`).**
  - The field is cast to float64 and padded by one cell with `mode="edge"`. This is a zero-gradient wall that never wraps, because the Sod tube has walls.
  - For each axis, the neighbours behind and ahead of every cell are sliced from the padded array.
  - A cell is flagged when `(low > 0) & (max >= R * low)` along any axis, with the axes combined by OR.
  - $R$ is Schaal and Springel's (2015) Eq. (2), the Rankine-Hugoniot ratio $2\gamma M^2/(\gamma+1) - (\gamma-1)/(\gamma+1)$, at $M_{\min} = 1.3$ and $\gamma = 1.4$. Then $R = 1.805$.
  - The test is written multiplicatively rather than in log pressure. The registry-wide contract tests run every metric on a smooth, signed, periodic 16×8 synthetic field and on a cosine against zeros, whatever fields it declares, so a pressure detector must return a finite float on a negative "pressure". A log form would return NaN there and fail the contract.
  - The `low > 0` condition and the float64 cast were added in the review round (see Bugs and fixes).
- **Constants.**
  - `MACH_MIN = 1.3` comes from Schaal & Springel (2015), Sect. 2.3.2, criterion (iii).
  - `GAMMA` is read with `inspect.signature(SodShockTube).parameters["gamma"].default`, so that 1.4 has one definition in the repository. The reviewer noted two consequences. First, this is the constructor default, not the γ of the reader a run builds. Second, a metric module now imports a dataset reader.
  - The other literals, recorded in the PR body, are 2.0 (the factor in Eq. 2) and 2 (the square of $M_{\min}$, the square in the diagonal's Pythagorean sum, and the slice offset of the stencil's neighbour ahead).
- **The distances (`surface_distances`).** The function calls `scipy.ndimage.distance_transform_edt(~b, sampling=spacing)[a]`, and the reverse. It raises `ValueError` on an empty set, because the caller scores empty sets. The reviewer checked the sampling order on an anisotropic grid: 4 cells × 2 gives 8 along axis 0, and 6 along axis 1. It also checked that the transform finds the nearest True cell of the other mask.
- **The metric.** In order, the metric:
  1. checks that the two shapes match each other and `ctx.grid.shape`;
  2. returns NaN if either field is non-finite anywhere;
  3. computes the domain diagonal $\sqrt{\sum_j (N_j \Delta x_j)^2}$;
  4. caches the reference's masks in `ctx.cache` under the constant key `"shock_set_distance/reference_masks"`;
  5. scores each channel: 0 if both sets are empty, the diagonal if one is empty, and the pooled mean of both directions otherwise;
  6. averages the channels.

  The reviewer noted that channel averaging can mix a flag with a distance (4.75 = mean(1.5, 8)), but pressure has one channel. It also noted that `ctx.grid` is the remapped grid, so the shape check holds on a coarser analysis grid.
- **Decorator.**
  - `arity="pairwise"`, `fields=("pressure",)` and `symmetric=True`.
  - `differentiable=False` and `monotone_under_smoothing=False`, because a thresholded set changes in jumps. The synthetic blur ladder gave $\rho = 0.975$ before the review fix and 0.900 after.
  - `cost="cheap"`, `higher_is_better=False` and `units="length"`.
  - `requires_periodic=False`: the metric takes no Fourier transform, and on a periodic grid it is approximate at the seam (card, Boundary handling).
- **Changes outside the bundle.**
  - `tests/test_metric_contract.py`: `shock_set_distance` joined the spacing-scaling parametrisation with factor 2, because it is a length. Before the review fix, the cosine case gave 1/15 and 2/15 cells. After it, a zero reference with no shock against a cosine with eight flagged cells scores the diagonal, 11.31 and then 22.63, so the check is not vacuous.
  - `docs/catalog.json` was regenerated.
  - No shared code changed.

## Tests

The tests are in `test_metric.py`. Each hand-computed value carries its derivation in the docstring.

- **`test_worked_example_matches_the_card`.** It pins the card's Intuition example. A step of ratio 10 on eight cells flags cells {3, 4}. The step moved two cells flags {5, 6}. The distances are 2, 1, 1 and 2, so the score is 6/4 = 1.5.
- **`test_a_one_cell_shift_overlaps_the_two_flagged_cells`.** The flagged pairs {3, 4} and {4, 5} give (1 + 0 + 0 + 1)/4 = 0.5. This pins $(s - 1/2)$ for $s = 1$.
- **`test_the_threshold_is_the_pressure_ratio_of_a_mach_1_3_shock`.** $2 \cdot 1.4 \cdot 1.69/2.4 - 0.4/2.4 = 1.805$. A step of ratio 1.80 is not flagged, and one of 1.81 flags the middle two cells.
- **`test_the_walls_are_not_wrapped`.** A geometric fall from 1 to 0.1 over 16 cells has a ratio of $10^{2/15} = 1.36$ across any cell's neighbours, so nothing is flagged. If the ends were wrapped, they would meet as a jump of 10.
- **`test_a_non_positive_pressure_is_never_flagged`.** A zero or negative neighbour, an all-zero field or a negative constant flags nothing. This test was added in the review round.
- **`test_a_non_positive_candidate_cannot_score_better_than_a_missed_shock`.** An all-zero or all-negative candidate against the step scores the diagonal, 8. The docstring derives the 1.2 the old convention gave: (0 + 3+2+1+0+0+1+2+3)/10. This test was added in the review round.
- **`test_a_non_finite_field_scores_nan`.** It covers a NaN candidate against a smooth reference, a single NaN cell, an infinite block and a NaN reference. All return NaN. This test was added in the review round.
- **`test_float32_and_float64_agree_at_the_threshold`.** A step of exactly 1.805 is flagged alike in both precisions. This test was added in the review round.
- **`test_empty_sets_score_zero_together_and_the_diagonal_alone`.** Two empty sets score 0. One empty set on 8 cells of spacing 0.5 scores 4, in either order.
- **`test_surface_distances_are_euclidean_at_the_grid_spacing`.** It checks 5 cells between (0, 0) and (3, 4) on a unit grid, and $\sqrt{52}$ on a grid twice as wide along x. An empty set raises `ValueError`.
- **`test_on_the_exact_sod_solution_it_finds_the_shock_and_tracks_its_speed`.** It uses the exact Sod solution at $t = 0.1$ and 0.11 on 2048 cells. Exactly two adjacent cells are flagged, within one cell of $0.5 + S_R t$. The flagged pair moves a whole number $s$ of cells, within one cell of $S_R \cdot 0.01$ (35.9 cells). The score equals $(s - 1/2)\Delta x$ at rel 1e-12. $S_R = 1.75216$ is taken from the reader, which `tests/test_analytic_datasets.py` checks against the published value. The tight assertion on $(s - 1/2)$ was added in the review round.
- **Contract tests** (`tests/test_metric_contract.py`) cover zero on identical fields, symmetry, a finite float, dtype agreement, the declared smoothing behaviour and the spacing doubling. The bundle's entry is the spacing parametrisation described under Implementation.

## Bugs and fixes

1. **A non-positive pressure scored better than a missed shock, so the ranking inverted.**
   - *Symptom.* The first convention flagged every cell beside a non-positive pressure, as if the ratio were infinite. On the exact Sod pressure at $t = 0.1$ (2048 cells), an all-zero or constant −1 candidate scored 0.280 of the diagonal. The exact field smeared by a 3-cell Gaussian, with its shock in the right place, scored the worst value, 1. A single cell set to −1e−3 far from the shock scored 0.209.
   - *Found by* the adversarial review.
   - *Cause.* $R \cdot \min \le \min \le \max$ whenever $\min \le 0$. The builder had reasoned about the ratio's limit as $p \to 0^+$ without measuring what a fully flagged field scores.
   - *Fix* (0fdab79 on #22). Flag only where $\min(p_-, p_+) > 0$.
   - *Regression tests.* `test_a_non_positive_pressure_is_never_flagged` and `test_a_non_positive_candidate_cannot_score_better_than_a_missed_shock`. Both failed on 2469846 (`assert 1.2 == 8.0`) and pass on 0fdab79.
   - *Same mistake elsewhere.* A grep of every `metrics/*/metric.py` for a ratio or threshold test of a quantity that should be positive found only `shock_mask`.
2. **A NaN or infinite field was silently scored.**
   - *Symptom.* A cell next to a NaN was never flagged, so a NaN candidate against a shock-free reference scored a perfect 0. Sod with its first 500 cells set to NaN also scored 0, and Sod with a `+inf` block scored 0.135.
   - *Found by* the review. It was a likely future bug for diverging ML surrogates.
   - *Fix* (0fdab79). Return NaN when either field is non-finite anywhere.
   - *Regression test.* `test_a_non_finite_field_scores_nan` failed on 2469846 and passes on 0fdab79.
   - *Same mistake elsewhere.* A sweep calling every registered non-ensemble metric with one NaN cell found that all 14 return NaN. `shock_set_distance` was the only one that had turned NaN into a number.
3. **float32 disagreed with float64 at the threshold.** At a ratio of exactly 1.805, a float32 input was flagged and a float64 input was not, because `ratio` was cast to float32. *Fix* (0fdab79): compare in float64. *Regression test:* `test_float32_and_float64_agree_at_the_threshold`, which failed on 2469846 (`[False, False, False, False] == [False, True, True, False]`).
4. **The Sod test could not tell $(s - 1/2)$ from $s$.** The shock moves 35.9 cells, so with a one-cell tolerance both 35.5 and 36 passed. *Fix* (0fdab79): measure the integer shift of the flagged pair and assert $(s - 1/2)\Delta x$ at rel 1e-12.
5. **The contract tests reached the metric only through the non-positive convention.**
   - *Symptom.* 94.5-95.3% of the synthetic contract field's flagged cells were flagged only because a neighbour was ≤ 0. The symmetry, dtype and blur-ladder checks ($\rho = 0.975$, which "verified" `monotone_under_smoothing=False`) therefore never exercised the Mach-1.3 threshold. The reviewer reasoned, without running it, that a field made positive (+3) would flag nothing, give a NaN Spearman $\rho$ and fail the declaration test.
   - *Resolved* by the fix to bug 1. Afterwards, 38 of 128 synthetic cells are flagged by the ratio itself. The blur ladder is [0.0, 0.2004, 0.4027, 0.5645, 0.5434] with $\rho = 0.900$, so its last step falls and the declaration is confirmed by a decreasing step rather than by ties. The spacing case gives 11.31 and then 22.63.
   - The general weakness, a signed contract input for metrics whose field must be positive, is outside the bundle. It was routed to [issue 101](../../issues/101-a-metric-cannot-declare-it-needs-an-absolute-positive-field.md) as the option of a positive-offset contract input.
6. **The reference cache key is a constant string.**
   - *Symptom.* A `ctx` reused with a different reference returns the first reference's masks: 8.0 against 0.0 with a fresh `ctx`.
   - *Rejected* as a fix in this bundle. The pipeline builds one `FieldContext` per (frame, field, metric) and passes the same reference to every variant, including on ensemble datasets. `fmeval/context.py` documents this pattern, and `increment_w1_by_separation` uses the same constant-key pattern. If the contract changes, the shared pattern should change, not one bundle.
   - It is now tracked repository-wide in [issue 116](../../issues/116-context-cache-trusts-one-context-per-frame.md). The orchestrator added this bundle there.

## Performance

- The decorator declares `cost="cheap"`.
- The first evidence run, `results/shock_set_distance_1793350452` at d9dcb84 on #22, took 11.8 s of wall time on `sod_shock_tube`: 10 frames, 2048 cells, the default ladder.
- The current evidence run, `results/shock_set_distance_1793381550` at 0fdab79, logged 3.7 s for reading, degrading and scoring 590 rows.
- The card's profile gives a compute cost of 1, relative to the cheapest metric in the same run. This metric was the only one in that run.
- Nothing was done about cost.

## Tooling and environment problems

- **Sandbox refusals.** The sandbox refused a multi-file heredoc and a Python one-liner whose text contained "git". The builder wrote files with the Write tool and put scripts in scratch files instead.
- **Scratch scripts and the import path.** Running a scratch script by its path from a scratch folder inside the worktree (`python <scratch folder>/x.py`) puts the scratch folder first on the path, and it then imports the main checkout's `metrics` package instead of the worktree's. The builder and the reviewer ran scripts as `python -c "exec(open(...).read())"` from the worktree root.
- **Refused fetches.** The Taha and Hanbury and Marzouk publisher pages refused the fetch. PMC served Taha and Hanbury. The reviewer's fetch of PMC for Yeghiazaryan and Voiculescu got a reCAPTCHA.
- **Missing PR label.** No `agent-metric` label existed, so the draft PR was opened without one.
- **First verification attempt.** The first run of the verification script failed and was fixed before the passing run, which the PR body reports. The records do not say what failed.
- **Scratch work not kept.** The pytest counts of the first build ("1880 passed") went to a scratch file that was removed with the old worktree, so the reviewer could not verify them. The off-run probes were also not kept. These were the contract-input probe, the noise check, the per-frame fingerprint reader, the Taylor-Green probe and the NaN sweep across metrics. Any of them would be short to rewrite from the descriptions above.
- **Between rounds.** The worktree was removed after the build and recreated at 2469846 for the review round. The orchestrator stopped the first reviewer so that a log audit could be added. The reviewer could read the build transcript only in small pieces, so it did not search it.
- **The card checker.** It reported 0 errors and one warning, for the unsigned card, which needs a person to sign.

## For the next agent

- **The constant cache key** is safe only while one context holds one reference ([issue 116](../../issues/116-context-cache-trusts-one-context-per-frame.md)).
- **`GAMMA`** is read from the Sod reader's default when the module is imported. A run that overrides the reader's $\gamma$ silently keeps 1.4, and the metric module depends on `fmeval.data.analytic`.
- **Higher dimensions.** The detector and the distance transform are written for any number of dimensions. The reviewer checked the stencil on 5×7 and 3×4×5 spikes, with no transposition error, but no dataset with a shock in two or three dimensions exercises them.
- **Periodic grids.** On a periodic grid the metric misses a jump exactly on the seam and overstates distances across it (card, Boundary handling). This is untested.
- **An unrun claim.** The reviewer's claim that a positive contract input would make the declaration test fail through a NaN $\rho$ was reasoned, not run.

## Round of 2026-11-04 (task `metrics-topology-shocks`)

- The metric's body was split into shared pieces: `shock_set_score` (checks, NaN rule, cached
  reference masks under `REFERENCE_MASKS`, channel mean), `set_distance` (the empty-set
  conventions) and `average_symmetric_surface_distance`. `shock_mask_overlap` and the four
  siblings import them. The cache key changed from `shock_set_distance/reference_masks` to
  `shock_set/reference_masks`; a cache lives for one metric, so nothing collides.
- Companions added for the card's line-out figure: `shock_positions` (the metric's own point set,
  (cell index, pressure) of the flagged cells; the metric does not read it from the cache, which
  the contract allows) and `pressure_profile` (named `profile`, a one-field map).
- Gate: 520 old-versus-new comparisons on the exact Sod pressure (rolls, noise, a blur, an
  offset, zero, negative and constant fields, a NaN cell, both argument orders) all identical, and
  the Sod smoke run `shock_set_distance_1793799367` matches the cited evidence run
  `shock_set_distance_1793381550` on all 590 shared rows exactly.
