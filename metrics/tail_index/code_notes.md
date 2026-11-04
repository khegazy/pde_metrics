# Code notes: tail_index

This is the coding record of the same build (pull request #23), condensed from the builder's and
the reviewer's records. The research record is in [research_notes.md](research_notes.md).

## Summary

`metric.py` holds three functions: the curve companion `tail_index_curve`, which computes the Hill
estimate at every order; the metric `tail_index`, which reads the registered point of that curve
from the pipeline's cache; and `orders`, which computes the orders exactly in integers. The
increments are imported unchanged from `metrics/increment_flatness/metric.py`. The review round
added exact integer orders and a refusal of non-finite input, and left one known defect, the
exact-zero axis rule, open as an issue with a strict expected-failure test.

## Implementation

- **The curve.** For each channel and each spatial axis, `tail_index_curve` takes the absolute
  one-cell increments from `increment_flatness`'s `increments`, sorts them in descending order,
  keeps the largest `ks.max() + 1`, and computes every order at once as
  `np.cumsum(logs)[ks - 1] / ks - logs[ks]`, which is the mean of $\ln X_{(i)}$ for $i \le k$
  minus $\ln X_{(k+1)}$ (Boucheron & Thomas 2015, Sect. 1, cited in a comment on that line). A
  pair's estimate at an order is replaced by NaN where `top[ks]` is not positive, and the curve is
  the mean over the pairs with a finite estimate, NaN where none has one.
- **The metric** reads `(thetas, values)` from `ctx.cache[COMPANION_KEY]` when the pipeline has
  computed the curve, and otherwise computes it, then returns the value where `thetas ==
  REGISTERED_THETA`. Selecting 0.5 by float equality was checked by the reviewer:
  `np.arange(1,10)/10` and three other ways of writing the grid all give exactly 0.5 at index 4,
  and the pipeline writes the row's curve into the cache immediately before each call, so no curve
  can leak from another variant.
- **Constants.** `THETA_TENTHS = np.arange(1, 10)` and `THETAS = THETA_TENTHS / 10` are the
  curve's coordinates, the agent's choice; `REGISTERED_THETA = 0.5` is the largest-$\sqrt{n}$ rule
  of Clauset, Shalizi & Newman (2009, Sect. 3.5); the literal 10 in `orders` is the same tenths;
  a field of fewer than 2 cells is refused, since Equation (2) needs $X_{(1)}$ and $X_{(2)}$.
- **`orders(n)`** computes the least $k$ with $k^{10} \ge n^j$ in Python integers, starting from
  the floating-point ceiling and correcting by one in either direction, then caps at $n - 1$ so an
  $X_{(k+1)}$ exists. It is a helper with one caller, which AGENTS.md §1 allows here because it is
  exact integer arithmetic that a test pins on its own.
- **Input checks.** A spatial shape of fewer than two cells and any non-finite value raise
  `ValueError`. The non-finite check was added in the review round in preference to documenting
  the drop, following the repository's rule of validating at boundaries; the harness never passes
  non-finite fields.
- **Decorator.** Single-field arity, `fields=("*",)` and `higher_is_better=False`, as
  `increment_flatness`; `symmetric=False`; dimensionless; `requires_periodic=True` for the
  wrap-around increments; `differentiable=True` (a sort and logarithms, piecewise smooth, as
  `increment_w1`'s sort), kept after the review because the value is differentiable wherever
  $X_{(k+1)} > 0$; `cost="cheap"`; `monotone_under_smoothing=False`, which is true on the contract
  test's synthetic blur ladder ($\sigma$ = 0, 0.5, 1, 2, 4 cells reads 0.114, 0.131, 0.113, 0.106,
  0.082, reproduced exactly by the reviewer).
- **Outside the bundle.** `tail_index` was added to the literal set of
  `test_the_catalog_supports_the_query_it_exists_for` in `tests/test_cards.py`, since it is
  differentiable, cheap and measured. No shared code needed a new argument.

- **2026-11-04 (task `metrics-tails`).** The estimator moved into `hill_estimates(x, field, ks)`,
  shared by the two curve companions `tail_index_curve` (theta = 0.01 to 0.99, `analysed` at the
  tenths) and `tail_index_by_order` (k = 1 to n // 10, `analysed=(10,)`); `orders(n, thetas)`
  reads each theta as its printed decimal p/q (`fractions.Fraction(str(theta))`) and finds the
  least k with k^q >= n^p, exact for any grid the harness can hold (the float first guess is
  within one of the root only while n^theta is far below 2^53). The increments come from
  `increment_samples(x, ctx.field)`, so `ctx` is now required.

## Tests

All in `metrics/tail_index/test_metric.py`; the contract tests already cover one finite float,
dtype stability, the declared non-monotone blur, a fixed curve coordinate and the cached number.

- `test_worked_example_matches_the_card`: the card's sawtooth gives $\ln 3 = 1.0986$ and the
  alternating field 0, derived by hand in the docstring.
- `test_distinct_increments_pin_the_order_statistics`: the 1-D field 0, 1, 3, 7, 15 gives
  $\ln(60)/3 = 1.364782$; every size is distinct, so using $X_{(k)}$ as the threshold, summing
  $k+1$ terms, or dividing by $k-1$ each gives a different number. Added in the review round.
- `test_orders_are_exact_at_exact_roots`: on $n = 1024$ the orders are $2^j$ exactly, and on
  65536 the registered order is 256. Added in the review round.
- `test_a_non_finite_field_is_refused`: NaN and infinity in one channel raise. Added in the review
  round.
- `test_spatial_clustering_lowers_the_estimate_of_a_power_law_field`: a 2-cell blur lowers every
  one of eight Pareto($\alpha=1$) seeds on 128 by 64 (measured mean 1.039 to 0.481); asserts the
  raw mean within 0.1 of 1 and the blurred mean below 0.7. Added in the review round.
- `test_round_off_on_a_constant_axis_does_not_change_the_value`: `xfail(strict=True)` against
  issue 103; a 64 by 32 field reads 0.0937 exactly constant along one axis and 0.1215 with a
  1e-12 perturbation. Added in the review round.
- `test_the_registered_number_is_the_curve_at_theta_one_half`, `test_invariant_to_scale_offset_and_periodic_shift`
  (scale, offset and integer roll, rel 1e-12), `test_a_constant_field_is_nan`,
  `test_a_single_cell_is_refused`.
- `test_estimates_the_inverse_power_of_a_power_law_tail`: iid Pareto with $\alpha$ = 1 and 2 on
  128 by 64 ($k$ = 91 of 8192), 16 seeds, mean within 0.1 of $1/\alpha$ (measured 1.003 and 0.545;
  the reviewer reproduced 1.0031 and 0.5448).
- `test_a_heavier_tail_scores_higher`: Pareto 1 above Pareto 2 above Gaussian on every one of 8
  seeds. Kept after the review because it is true on independent fields.

Each review-round test was checked to fail without its fix by mutating `metric.py` from a saved
copy: with the correction loops of `orders` disabled, the orders test failed with
`[2, 4, 8, 17, 32, 64, ...] == [2, 4, 8, 16, 32, 64, ...]`; with the finite check replaced by
`if False:`, the refusal test failed with "DID NOT RAISE ValueError"; with the threshold mutated
to $X_{(k)}$, only the distinct-value test failed among the four estimator tests.

- 2026-11-04: `test_dense_orders_are_exact_at_hundredths` (on 2^20 cells a float power is one
  too large at 7 of the 19 exact roots j = 5, 10, ..., 95); `test_the_classical_hill_plot_by_hand`;
  `test_the_two_hill_plots_agree_where_their_orders_meet`; `test_velocity_reads_its_longitudinal_increments`.

## Bugs and fixes

- **Floating-point orders one too large at exact roots** (review round, fixed in commit a79bbca
  on #23). `ceil(n ** THETAS)` gave 17, 257 and 513 instead of 16, 256 and 512 at $\theta$ = 0.4,
  0.8 and 0.9 on 32 by 32; it was wrong at four orders on 1024 by 1024 and three on 32 cubed,
  because `1024 ** 0.4` evaluates to 16.000000000000004. $\theta = 0.5$ was exact for every perfect
  square up to $20000^2$, and the 256 by 256 grid was unaffected. Fixed by `orders`; regression test
  `test_orders_are_exact_at_exact_roots`. A search for other ceilings of a power in `metrics`,
  `fmeval` and `degradations` found none.
- **Non-finite input dropped silently pair by pair** (review round, fixed in a79bbca). One NaN or
  infinity in channel 0 of a 2-channel field returned exactly channel 1's value with no warning,
  because `np.sort` puts NaN last, the reversal puts it first, and the cumulative sum makes every
  order of that pair NaN, which the finite mask then dropped; in a one-channel field it returned
  NaN, like a constant field. Fixed by raising `ValueError`; regression test
  `test_a_non_finite_field_is_refused`. The same behaviour in `increment_flatness` is
  [issues/107](../../issues/107-increment-flatness-drops-a-non-finite-channel.md).
- **The power-law tests would pass a broken estimator** (review round, fixed). Three mutants
  (threshold $X_{(k)}$, $k+1$ terms over $X_{(k+1)}$, division by $k-1$) all passed the Pareto
  tests; only the tied sawtooth caught them, and only because of where its ties fall. Fixed by the
  distinct-value test and the clustering test.
- **Round-off on an exactly constant axis changes the value** (review round, left open). A pair is
  left out only when $X_{(k+1)}$ is exactly zero, and Equation (2) is scale-free, so a 1e-12
  perturbation of a 256 by 256 channel varying along one axis moved the value from 0.289 to 0.191
  (reviewer) and the test field from 0.0937 to 0.1215; `increment_flatness` moves from 2.60 to
  2.82. The gradient through $-\ln X_{(k+1)}$ also diverges as $X_{(k+1)} \to 0$. Left open
  because every alternative rule has no source, changes every anisotropic field's number, and the
  rule is shared with `increment_flatness`, which this bundle could not edit:
  [issues/103](../../issues/103-exact-zero-axis-rule-is-discontinuous.md), with the strict xfail
  test. A search for other scale-free per-pair statistics that skip undefined pairs found that
  `increment_w1` keeps degenerate pairs as a well-defined zero and `increment_w1_by_separation`'s
  numerator is in field units, so neither has the problem.

## Performance

- Smoke run `results/tail_index_1793349654` (`kinet_re5e4_dev`, quick ladder): 3000 rows in
  19.9 s, of which metrics 7.6 s, about 2.5 ms per row.
- Evidence run `results/tail_index_1793350342` (256 grid, 161 frames): 1631.1 s wall (io 10.8 s,
  degradation 1481.0 s, metrics 126.8 s), 28497 rows, 3.2 to 7.5 ms per row. The degradation time
  was inflated by the `energy_distance` agent's concurrent run, at about 25 cores, on the same
  login node.
- Nothing was done about cost; the metric is declared cheap. The card's profile gives the cost
  relative to the cheapest metric in the pinned shared run (card, Performance).

## Tooling and environment problems

- No PDF reader was installed (no pdftotext, pypdf or poppler). The builder wrote a crude
  stream-inflating text extractor to read Clauset et al.; it was not kept, was lost between
  rounds because the first round's scratch folder was not archived, and was rewritten for the
  review round.
- Project Euclid served a bot check for Hill (1975); a second download attempt was refused by the
  sandbox as bot-check circumvention, so the builder stopped. The Cornell eCommons copy of Drees
  et al. rate-limited the fetch tool and then served an HTML page.
- The orchestrator's fingerprint check filtered rows by `field in fields`, so a metric declaring
  `fields: ["*"]`, as the decorator requires it to match, had its follows and blind declarations
  silently never checked. Fixed in the orchestrator's checker the same day.
- `pytest -n` was not available (no xdist), so the full suite ran serially.
- The first full suite failed only `test_bundle_prose_has_no_errors[metric:tail_index]`, on
  `TODO(fill)` placeholders left under the empty Results blocks; the recipe says to leave the
  readings empty until measurements exist, so the placeholders were deleted.
- `python <file>` from the worktree imports the main checkout's `metrics` package, which had no
  `tail_index`; scratch scripts insert the worktree on `sys.path`.
- The `agent-metric` label does not exist on the repository and `gh` is not installed, so the
  pull request was opened, without a label, through the GitHub connector.
- The review round's message named a `feedback.md` that was never written for this launch.

## For the next agent

- Check first that `ks - 1` and `ks` index the $k$-th and $(k+1)$-th largest in the Hill line of
  `tail_index_curve`, against Boucheron & Thomas (2015, Sect. 1). The reviewer matched it to an
  independent pure-Python estimator to 6e-16 on six shapes (1-D, 2-D, 3-D, non-square, 1 to 3
  channels).
- Issue 103's xfail test will start passing, and so fail as strict, when the exact-zero rule is
  changed; the rule should change in `increment_flatness` at the same time.
- `differentiable=True` stands although the gradient is unbounded as $X_{(k+1)} \to 0$, for example
  on coarse staircases; that matters only for use as a training loss.
- The reviewer found float32 input agrees with float64 to about 5e-6 relative on unit-variance
  fields but about 1e-3 on a density-like field ($1 + 10^{-4}$ noise), from the quantisation of the
  input itself; the pipeline casts every reader to float64, so it is not this bundle's defect.
- The reviewer also confirmed that `-0.0` and all-`-0.0` fields give NaN, denormal staircases
  behave, the $n-1$ cap holds on tiny fields (a repeated $k$ gives repeated values at distinct
  coordinates), and the `top[ks] > 0` mask implies every log among the top $k$ is finite.
