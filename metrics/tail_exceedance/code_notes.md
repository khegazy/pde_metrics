# Code notes: tail_exceedance

This is the coding record of the same build (pull request #31), condensed from the builder's and
the reviewer's records. The research record is in [research_notes.md](research_notes.md).

## Summary

`metric.py` holds the curve companion `tail_exceedance_curve`, which computes the frequency bias at
every order; the metric `tail_exceedance`, which reads the registered point from the pipeline's
cache; and two small helpers that list the absolute increments per pair and count exceedances. It
reuses `increments` from `increment_flatness` and `orders`, `THETAS` and `REGISTERED_THETA` from
`tail_index`, and caches the reference's thresholds in `ctx.cache`. Outside the bundle, two
contract identity tests were generalised to expect a declared target. The review round found no
coding bug; the shared analysis defects it confirmed were left open as issues, because the build's
brief allowed no harness change.

## Implementation

- **The curve.** After the shape, size and finiteness checks, the reference's thresholds are
  computed once per context: for each (channel, axis) pair, the absolute increments are sorted in
  descending order and the $k$-th largest is taken at every order `ks - 1` from `tail_index`'s
  `orders(n)`. The reference's own counts are stored with them under the cache key
  `REFERENCE_EVENTS = "tail_exceedance/reference_events"`, the same pattern by which
  `increment_w1_by_separation` caches its reference scale. The candidate's counts are
  `#{|delta| >= a}` per pair and threshold; counts are summed over the pairs with a positive
  threshold, and the ratio is NaN where no pair has one.
- **The metric** reads `(thetas, values)` from `ctx.cache[COMPANION_KEY]` when the pipeline has
  computed the curve, and otherwise computes it, then returns the point $\theta = 1/2$.
- **Helpers.** `_sizes` lists each pair's flattened absolute increments in channel-major then axis
  order, the order of the thresholds; `_exceedances` counts per pair and threshold, zipping with
  `strict=True`. The reviewer checked the order against a hand loop on a two-channel 12 by 20 input
  and on 3-D input.
- **Constants.** The only literal is 2, the smallest number of cells for which an order
  $k = \min(\lceil n^\theta\rceil, n-1) \ge 1$ exists; a guard, not a parameter. The orders and
  $\theta$ grid are imported from `tail_index`.
- **Decorator.** Pairwise arity; all fields; `target=1.0` (JWGFVR's perfect score);
  `higher_is_better=False`, required with a target because the analysis orders by
  $\lvert\log(\text{value}/1)\rvert$; `symmetric=False`, since the threshold is the reference's;
  dimensionless; `differentiable=False`, since counts are piecewise constant; `cost="cheap"`;
  `requires_periodic=True`; `monotone_under_smoothing=False`. The last rests on a measured example:
  a 16-cell one-dimensional field holding one spike of height 8 on noise of standard deviation 0.01
  (seed 0) scores 1, 1, 2, 3, 3.5 and 0 under Gaussian blur of $\sigma$ = 0, 0.5, 1, 2, 4 and 8
  cells, because the blur spreads one tall jump over several cells that each still exceed a low
  threshold.
- **Outside the bundle: the contract tests.** Before this bundle, `tests/test_metric_contract.py`
  expected 0 from every pairwise metric on identical fields, so no pairwise metric could declare a
  target. The two identity tests now expect `spec.target or 0.0`, and in the review round they were
  renamed `test_pairwise_identity_is_zero_or_the_target` and
  `test_a_comparison_curve_is_zero_or_the_target_on_identical_fields`. This bundle is the only
  registered pairwise metric with a target, so no other expectation changed; the reviewer checked
  that the edited tests still fail for a target metric returning 1.5, a curve off target, a
  target-less metric returning 1.0, and a metric with `target=0.0` returning 1.0. The builder chose
  to change the tests rather than transform the metric, following the rule of adapting the harness
  to the metric.

## Tests

All in `metrics/tail_exceedance/test_metric.py`, each value derived by hand in its docstring.

- `test_worked_example_matches_the_card`: on the sawtooth, cutting two of the four big jumps scores
  $2/4 = 0.5$ and tripling the field scores $16/4 = 4$; the constant row axis is left out.
- `test_ties_at_the_threshold_are_all_events`: a reference whose sixteen steps are all 1 has 16
  events, not $k = 4$, and the sawtooth reaches 1 everywhere: $16/16 = 1$.
- `test_a_constant_candidate_scores_zero_and_a_constant_reference_nan`.
- `test_a_non_finite_field_is_refused`: NaN and infinity raise in either field.
- `test_an_independent_twin_scores_one_at_the_smallest_order`: at $\theta = 0.1$ on 1024 cells
  ($k = 2$), independent periodic random walks score $n/(n+1) = 0.999$ in expectation; measured mean
  1.015 with standard error 0.052 over 400 seeds, asserted within 0.2 of 1. The other convention
  measures 1.5625 on the same seeds, so the bound separates the two.
- `test_blur_can_raise_the_value_before_it_lowers_it`: pins the exact spike sequence
  `[1.0, 1.0, 2.0, 3.0, 3.5, 0.0]` (candidate counts 4, 4, 8, 12, 14 and 0 over the reference's 4).
  Changed in the review round; see Bugs and fixes.
- `test_scaling_both_fields_and_moving_the_candidate_change_nothing`: scaling both fields by 7 and an
  integer roll of the candidate leave the value exactly unchanged.

## Bugs and fixes

- **The spike example's documented numbers were not what the test's field gives** (review round,
  fixed in commit 9cf70cb on #31). The decorator comment, the test docstring, the card, the PR body
  and the record of the example said 1, 1.25, 2, 3, 3.5, 0, but the test's own field gives 1, 1, 2,
  3, 3.5, 0. The 1.25 came from an exploration loop that shared one generator across five fields, so
  the field documented was the fifth draw rather than a fresh seed-0 field; the test asserted only a
  rise and a fall, so it did not catch the mismatch. Fixed everywhere, and the test now pins the
  sequence, which fails against the previously documented one. A search found no other documented
  number drawn from a shared generator.
- **A target-valued metric's zero becomes infinity and the frame is called round-off** (found during
  the evidence run, confirmed by the reviewer with one-frame inputs; shared harness, left open).
  `fmeval/analysis.py::_oriented` maps 0 to $+\infty$ on purpose, but `_is_round_off` keeps only
  finite values and calls a frame with fewer than two of them round-off, so (0.3, 0, 0, 0) gives
  rho NaN for a perfectly ordered frame, and (0.3, 0.1, 0, 0) gives 0.9487 whatever the finite
  values. `_monotone_fraction` counts (finite, finite, inf, inf) as out of order, because
  $\infty - \infty$ is NaN, which is also the source of numpy's "invalid value encountered in
  subtract" warning during `cards evidence`. In the evidence run this withheld `gaussian_blur`,
  `box_blur`, `lowpass_ideal` and `lowpass_butterworth` on density and velocity, the axes the metric
  responds to most. `spread_skill`, the other target-valued metric, can also reach 0 and was not
  re-examined. Routed to
  [issues/123](../../issues/123-analysis-cannot-read-a-target-valued-metric.md).
- **A target-valued metric gets direction +1 everywhere, no blindness bound, and an un-oriented
  damage** (same route). `summarise_axes` sets the sign to 1 when a target is declared and builds no
  damage, so `_blindness_bound` never runs and `blind_axes` is empty: the declared falls of the
  blurs read +1 and `translate_x`, exactly 1 at every level, is not listed blind. The damage is the
  raw `(v - clean) / span`, so with clean 1 and the anchor at 0 it is $1 - v$; noise at
  $v \approx 195$ has damage about −194, read as moving away from the anchor, and the fingerprint's
  `damage_max` on noise (0.0547, 0.0518, 0.0332) is the mildest level's dip below 1. The damage
  columns and the noise response curve are therefore not readable for this metric; `spread_skill`
  shares the path. Also in issue 123.
- **The reference cache is keyed by name only** (review round, likely future bug, not fixed in the
  bundle). A context filled with one reference and reused for another gave 21.625 instead of 1.0
  (the reviewer) and 0.0 instead of 1.0 (the builder), and a reference of a different shape gave
  0.21875 with no error, because `zip(strict=True)` checks only the number of pairs. It is not a
  present bug: `fmeval/pipeline.py` builds one context per (frame, field, metric), the reference is
  the same object for every variant, and the companion's context shares the cache dict and runs
  first. A shape guard would miss a same-shape reference, an identity guard depends on the pipeline
  never copying, and the same pattern is in `increment_w1_by_separation`, `spectral_energy_flux`,
  `persistence_distance` and `shock_set_distance`, so the guard belongs once in
  `fmeval/context.py`. The docstring says the context must belong to this reference. Added as a
  paragraph to [issues/116](../../issues/116-context-cache-trusts-one-context-per-frame.md).
- **The contract blur test accepts `monotone_under_smoothing=False` through ties** (review round,
  shared test, not changed). It passes when $\lvert\rho\rvert < 1$, which a monotone metric that
  saturates satisfies: this metric gives 1.0, 0.16, 0, 0, 0 on the contract ladder (never rising)
  and $\lvert\rho\rvert = 0.894$. This bundle's declaration rests on its own spike test instead. The
  same test compares a pairwise metric's raw values with +1, so a future pairwise target metric
  declaring `monotone_under_smoothing=True` would need them oriented by
  $\lvert\log(\text{value}/\text{target})\rvert$ as the analysis does. Both added as a paragraph to
  [issues/113](../../issues/113-not-monotone-declaration-passes-on-round-off.md).

## Performance

- Evidence run `results/tail_exceedance_1793494833` (256 grid, 161 frames, 28497 rows): 1319.8 s
  wall (io 8.6 s, degradation 1067.2 s, metrics 230.8 s).
- The reference's thresholds are computed once per frame through `ctx.cache` rather than for every
  variant. Nothing else was done about cost; the metric is declared cheap.

## Tooling and environment problems

- **The committed-file size cap.** `tests/test_cards.py::test_committed_figures_fit_the_size_budget`
  failed with this bundle: 25.3 MB against the 25 MB cap (`main` was at 24.27 MB; this bundle's
  generated files are 1.05 MB, its `fingerprint.json` 533 KB). The reviewer found the size expected:
  the companion block holds 405 rows (9 coordinates by 15 axes by 3 fields), 383 KB of 546 KB, the
  same structure as `tail_index`'s 405 rows (392 KB of 556 KB), with nothing duplicated. Following
  `docs/decisions.md`, the cap was not changed and the figures were not slimmed; the pull request
  was opened marked "Blocked" and the question went to Kareem. The cap was raised from 25 MB to
  40 MB in #34, and #31 was merged on 2026-11-02.
- **The orchestrator's checker** first could not express the declaration of a target-valued metric
  (see Bugs and fixes); it was taught the target convention, then reported 19 PASS and 4 MANUAL
  entries, the blur axes whose ordering statistic the analysis withheld, which the orchestrator
  accepted by hand. It then crashed on refs.bib: the template header comment
  `% Cite from the card as [@key]` is parsed by pybtex as an entry ("syntax error in line 4"), so
  its citation and Crossref checks did not run, here or for six other bundles carrying the header.
  The checker was fixed to strip comment lines before parsing; the header, which the scaffold writes
  into every bundle, was left. The full check then reported 36 PASS, with the citations matching
  Crossref.
- The sandbox refused multi-file heredocs and scripts run by path, and `python path.py` imports the
  main checkout's `metrics` rather than the worktree's because the script's folder is first on
  `sys.path`; scratch scripts were run as `python -c "import runpy; runpy.run_path(...)"` from the
  worktree root, and files were written with the Write tool.
- Publisher pages for Ferro & Stephenson (2011), Stephenson et al. (2008), Zhang et al. (2005) and a
  WIREs paper refused the fetch tool (403), and `curl` downloaded nothing.
- The first contract-test run failed the pairwise identity tests, because the frequency bias is 1,
  not 0, on identical fields; resolved by generalising the tests to the declared target.
- The first full suite failed only on the stale catalog, which was regenerated.
- A first wait loop for the evidence run grepped the evaluate log for "RC=", which the command never
  wrote there; it was stopped and the wait keyed on the "wrote" line instead.
- Neither the `agent-blocked` nor the `agent-metric` label exists and `gh` is not installed, so the
  pull request was opened through the GitHub connector without labels.

## For the next agent

- Check first that `_exceedances` counts `>=` and that the threshold index `ks - 1` is the $k$-th
  largest; `test_worked_example_matches_the_card` and `test_an_independent_twin_scores_one_at_the_smallest_order`
  pin both.
- The `ctx.cache` entry is safe in the pipeline but not for a direct caller reusing one context
  across references (issue 116).
- The contract-test change `spec.target or 0.0` is 0 for every target-less metric, so it changes no
  other metric's expectation; a metric declaring `target=0.0` is also handled.
- The reviewer found that a reference constant along one axis up to 1e-15 moves the value from 3.0
  to 33.5, the discontinuity `issues/103` records for `tail_index`; and that float32 quantisation of
  a field with mean 1 and fluctuations of 1e-6 creates ties (32 values at the threshold) and a 1.2%
  difference, which the pipeline's cast to float64 makes unreachable.
