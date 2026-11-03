# Code notes: energy_distance

This is the coding record of the same build (pull request #24), condensed from the builder's and
the reviewer's records. The research record is in [research_notes.md](research_notes.md).

## Summary

`metric.py` is one function: it checks that the two shapes match, then averages
`scipy.stats.energy_distance` over every (channel, axis) pair of one-cell increments taken from
`increment_flatness`'s `increments`. No shared code was changed. The review round found no bug in
the computation; it changed the cost declaration from cheap to moderate, corrected a docstring,
and added one regression test for the card's corrected tail derivation.

## Implementation

- **The computation.** For each channel and each spatial axis in `range(-n_spatial, 0)` (correct
  for 1-D, 2-D and 3-D fields, as the reviewer checked), the reference's and the candidate's
  increments are raveled and passed to `scipy.stats.energy_distance`, and the result is the mean
  over all pairs. Every pair is included, also one whose increments vanish in both fields, where
  the distance is a well-defined zero.
- **Why SciPy rather than a merge of its own.** Least new code: the function is exact for
  empirical distributions and returns the square-root form the card registers. It does not accept
  presorted samples, so the reference's sort cannot be cached per frame; that is the cost noted
  under Performance. Its source, `scipy.stats._stats_py._cdf_distance` with $p = 2$, runs two
  argsorts, a sort of the pooled samples and two `searchsorted` calls; the docstring was corrected
  in the review round to say so rather than "one merge".
- **Numerical check.** On 200-sample Student-t and normal draws, SciPy's squared value matched the
  all-pairs V-statistic to 2.7e-16 absolute, 1.9e-14 relative; the reviewer's independent check on
  400 and 300 samples gave 1.9e-14 relative, and $D/\mathrm{MMD}_b = 1.41421356237310$.
- **Constants.** None in `metric.py` other than 0 and 1 (axis indices and `ndim - 1`). The
  method's one constant, the exponent 1 on $\lvert x-y\rvert$, is implicit in SciPy's function
  (Székely & Rizzo 2013, Definition 1).
- **Decorator.** Pairwise arity; `fields=("*",)` as `increment_w1`, since the increment
  distribution is defined for any scalar channel; `symmetric=True` (the reviewer found it bitwise
  symmetric); units `field^(1/2)`; `requires_periodic=True` for the wrap-around increments;
  `higher_is_better=False`; `differentiable=True`, smooth away from ties and from identical
  samples as `rmse` is away from identical fields; `cost="moderate"` since the review round. The
  card's `triangle_inequality: true` holds because a mean of pseudometrics is a pseudometric (the
  reviewer's check).
- **Outside the bundle.** The first commit added `energy_distance` to the "differentiable, cheap,
  measured" set of `test_the_catalog_supports_the_query_it_exists_for` in `tests/test_cards.py`;
  the review round removed it again when the cost became moderate, so that file ended identical to
  main.

## Tests

All in `metrics/energy_distance/test_metric.py`; the registry-wide contract (symmetry, zero on
identical fields, shape rejection, dtype stability, monotonicity under blur) is in
`tests/test_metric_contract.py`. Every expected value is derived in its docstring.

- `test_worked_example_from_the_card`: the card's 4 by 4 step against alternating pair scores
  0.25, derived both from the cumulative functions and from the mean distances of Eq. (2.4).
- `test_a_rare_extreme_increment_costs_less_than_a_broad_change_of_equal_transport_cost`: two
  candidates both at `increment_w1` 0.5 score 0.5 (broad) and $\sqrt{1/8}/2 = 0.1768$ (tail). Its
  docstring was clarified in the review round: the broad ratio of 1 is a property of this
  two-valued example, not of broad changes.
- `test_on_a_gaussian_bulk_a_tail_change_costs_4_sqrt2_over_n_eps_of_an_equal_cost_stretch`:
  added in the review round. On $N = 1024$ Gaussian-quantile increments with $\epsilon = 0.05$ it
  asserts $D^2/W_1 = 0.017678$ for the stretch and a tail-to-stretch ratio of 0.11049, both within
  5% (measured 0.01731 and 0.1128). The old claim written as a test on the same construction
  failed with `assert 0.11284727410806697 == 0.001953125 ± 9.8e-05`; the new test passes.
- `test_translation_and_a_constant_offset_are_invisible`: an integer roll gives exactly 0 and an
  offset gives 0 within 1e-6.
- `test_scaling_both_fields_scales_the_distance_by_the_root_of_the_factor`: with $c = -4$ the
  value doubles.

## Bugs and fixes

Nothing recorded. The reviewer found no bug in the computation; its critiques were about the
card's claims, records and the cost tier, and are in [research_notes.md](research_notes.md) under
Review round and here under Performance.

## Performance

- Smoke run `results/energy_distance_1793349238` (`kinet_re5e4_dev`, quick ladder): 3000 rows,
  297.6 s in metrics, about 0.1 s per row.
- Evidence run `results/energy_distance_1793350409` (256 grid, 161 frames, 28497 rows): 4484.1 s
  wall (io 11.1 s, degradation 892.8 s, metrics 3569.5 s) on a login node shared with other
  agents; about 0.125 s per row, 0.19 s on two-channel velocity.
- The reviewer's timing on one 256 by 256 channel: `energy_distance` 0.1359 s per call,
  `increment_w1` 0.0034 s, `increment_w1_by_separation` (declared moderate) 0.0259 s; a second run
  gave 0.1253, 0.0033 and 0.0359; the builder's re-run gave 0.1386, 0.0033 and 0.0256. So the
  metric costs about forty times `increment_w1` on the same samples and 3.5 to 5 times
  `increment_w1_by_separation`, because SciPy re-sorts both samples on every call.
- What was done: the declaration was changed from `cost="cheap"` to `cost="moderate"`, with the
  measured reason in a comment, and the name removed from the cheap-metrics catalog query. The
  alternative weighed was to sort the reference's increments once per frame in `ctx.cache` and
  merge with the candidate's sorted increments, which would bring the cost to that of
  `increment_w1`. It was not done, because it replaces a library call with new code and changes
  the numbers at round-off, which would need a new evidence run. Not routed.

## Tooling and environment problems

- The sandbox refused heredocs and compound shell commands, including a heredoc writing findings
  files; commands were split or the editor was used.
- No PDF library or poppler was installed; ghostscript's `txtwrite` device extracted the text.
  Equations came out garbled in places, but equation numbers and their placement were legible.
- The full-suite and docs commands wrote their output into the worktree's scratch folder rather
  than `/tmp`, so nothing was written outside the worktree.
- A script run directly from the scratch folder could not import the worktree's new bundle,
  because its own directory, not the worktree root, is first on the path; it was run through
  `python -c "import runpy; runpy.run_path(...)"` from the root.
- The orchestrator's fetch log missed the Székely & Rizzo (2013) PDF, which was downloaded by a
  `curl` inside a compound command that exited non-zero; the command log and the transcript record
  it. A checker must fall back to the command log before concluding a source was never read. The
  orchestrator's tooling was fixed to list such downloads, marked.
- The reviewer's timing script stopped at `spectrum_l2`, which needs `ctx`; the three timings
  before it were the ones used.
- The `agent-metric` label does not exist on the repository, so the pull request has none.

## For the next agent

- The builder was unsure whether `differentiable=True` is fair for a square root at zero: the
  gradient is unbounded at identical samples, as for `rmse`.
- The reviewer's edge cases: NaN in the candidate gives NaN and infinity gives infinity silently,
  as in the sibling metrics (the reader runs with `nan_policy: error`); an array with no spatial
  axis gives NaN with a "Mean of empty slice" warning, as `increment_w1` does; 1-D, length-1-axis
  and 3-D inputs work; a constant reference against a noisy candidate is finite; float32 agrees
  with float64 to 1.3e-8 relative.
- If the sort-once speed-up is built, the numbers change at round-off, so the evidence must be
  re-run and compared.
