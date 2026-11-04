# Code notes: variogram_score

This is the coding record of the variogram score's part of pull request #27, condensed from the
builder's and the reviewer's records. The same launch built [energy_score](../energy_score/card.md).
The tooling and environment problems common to both bundles (PDF extraction, the self-check's
ladder labels, the one-bundle assumption, `mkdocs -q`, the scratch import path and the sandbox
refusals) are recorded once in
[energy_score's code notes](../energy_score/code_notes.md#tooling-and-environment-problems). The
research record is in [research_notes.md](research_notes.md).

## Summary

`metric.py` holds the metric, `variogram_score`, which returns the sum of its companion,
`variogram_score_map`. All the work is done in the map: a loop over every displacement between two
cells, which visits each ordered pair once. The first version used Scheuerer and Hamill's plug-in
estimate and straight-line distances. The review round rewrote it to the fair estimate with
periodic distances, made it 3.4 times faster than the first fair version, and added seven
regression tests that failed on the old code. The bundle was merged with every verification step
passing.

## Implementation

- **Input.** `as_ensemble(..., min_members=1, what="variogram_score")` validates the ensemble. The
  map raises `ValueError` if the field's spatial shape differs from `ctx.grid.shape`. The spacing
  and the boundary of each axis come from `ctx.grid`.
- **Periodic partners as slices.** Along every axis the grid declares periodic, the reference and
  the members are concatenated with themselves, so a wrapped partner is a plain slice of the
  doubled array.
- **The displacement loop.** It runs over `itertools.product` of the offsets along each axis: 0 to
  $n-1$ on a periodic axis (the partner wraps), and $-(n-1)$ to $n-1$ on a bounded axis (both cells
  inside the domain). The zero offset is skipped. On a periodic axis the separation is
  `min(k, n - k)`, the shorter way round. The weight is $1/r$ with $r$ the Euclidean length of the
  separation times the spacing (Scheuerer & Hamill 2015, Sect. 2). Each ordered pair is visited
  once and charged to its first cell, so the map sums to the score.
- **The fair term.** For each offset the code computes $\lvert y_i - y_j\rvert^{0.5}$ for the
  reference and $u_k = \lvert x^{(k)}_i - x^{(k)}_j\rvert^{0.5}$ for each member. The term is
  $(\text{observed} - \bar u)^2$, less $\mathrm{var}(u, \text{ddof}=1)/M$ when $M > 1$ (Allen et
  al. 2023, Sect. 4.1; Pacchiardi et al. 2024, App. C.1.2). The term is weighted and summed over
  channels into the map.
- **Constants.** `ORDER = 0.5` (Scheuerer & Hamill 2015, Sects. 3a, 3c and 3d; tied in 3b; the
  only order in 3e). The literal 2 is the square of the mismatch in their Eq. 3 and the square
  inside the Euclidean distance of their inverse-distance weights (Sect. 2). No numeric literal
  was added in the review round.
- **Decorator.** `arity="ensemble"`, `fields=("*",)`, `differentiable=False` ($\lvert a - b\rvert^{0.5}$
  has an unbounded gradient where two values agree), `cost="expensive"` ($O(MN^2)$),
  `higher_is_better=False`, `symmetric=False`, `units="field/length"`, `reduction="sum"`.
  `requires_periodic=False` is declared explicitly with its reason: the metric wraps only the axes
  the grid declares periodic and runs on any boundary. `monotone_under_smoothing` is the default,
  True (research_notes.md, Method choices, for its history).
- **Companion.** `variogram_score_map`, a field map with `reduction="sum"`. The metric is the map's
  sum, so the pipeline computes the whole score again when it stores a map (Performance).
- **Changes outside the bundle.** `tests/test_metric_contract.py`: `variogram_score` joins the
  spacing-scaling parametrisation with factor 0.5, since the score is an inverse length. That test
  gained an `ensemble` branch, a one-member ensemble of the cosine against a zero reference,
  because it handled only the pairwise and single arities.

## Tests

`metrics/variogram_score/test_metric.py`:

- `test_worked_example_from_the_card`: a periodic row of three cells, reference $(0, 4, 0)$,
  members $(0, 1, 0)$ and $(0, 0, 0)$, unit spacing. For each neighbouring pair the squared
  mismatch is $(2 - 0.5)^2 = 2.25$. The fair correction subtracts $0.5/M = 0.25$, leaving 2, and
  the end pair costs 0. Counting ordered pairs gives $2 \times (2 + 2) = 8$. The first, plug-in
  version gave 9.
- `test_the_map_charges_each_cell_its_pairs`: the map is $(2, 4, 2)$.
- `test_matches_the_double_sum_over_every_ordered_pair`, parametrised over `neumann` and
  `periodic` (added in the review): the displacement loop against a literal double sum, on a
  non-square 5 by 4 grid with unequal spacing $(0.5, 2.0)$, so that a transposed axis or a dropped
  spacing fails.
- `test_a_periodic_grid_has_no_preferred_origin` (added in the review): a cyclic shift of the
  reference and the members together leaves the score unchanged on a periodic 9 by 6 grid.
- `test_blind_to_an_offset_common_to_every_cell`: adding 3 to every member changes nothing
  (Scheuerer & Hamill 2015, Sect. 2).
- `test_blind_to_a_sign_flip_of_the_members` (added in the review): negated members score the same
  (Pacchiardi et al. 2024, Sect. 3.2.1, below Eq. 11).
- `test_penalises_strong_over_and_under_dispersion`: the calibrated ensemble beats one three times
  wider and one five times narrower.
- `test_a_narrowed_two_member_ensemble_does_not_beat_the_calibrated_one` (added in the review): at
  $M = 2$, a 20% narrower ensemble must cost, over 200 draws. On the plug-in code it won by 38.7,
  where the test needs a loss above three standard errors (3.2).
- `test_a_calibrated_ensemble_scores_the_same_at_any_size_from_two` (added in the review, replacing
  the first round's test of ensemble-size dependence): the means at 4 and 16 members must agree
  within four combined standard errors. The plug-in code scored about 1139 against 971, a gap of
  167.7 against a limit of 53.6.

**The shared blur-ladder test lets a false "not monotone" declaration through.**
`tests/test_metric_contract.py::test_monotone_on_synthetic_blur_ladder` checks a
`monotone_under_smoothing=False` declaration with `abs(rho) < 1.0`. SciPy's Spearman coefficient of
a perfectly monotone five-point ladder can come out as 0.9999999999999999, so a false declaration
passes. This was seen with the fair score's ladder 90.86, 91.68, 403.5, 1195.85, 2431.37 while the
stale False declaration was still in place. A tolerance such as `abs(rho) < 1 - 1e-9` would close
it. `increment_flatness`, the only other metric declaring False, reads $-0.90$ there and is
unaffected. The test was not changed in this branch; the orchestrator wrote
[issues/113](../../issues/113-not-monotone-declaration-passes-on-round-off.md) and reproduced the
problem.

## Bugs and fixes

The reviewer found no wrong number from the first version's code as written. The displacement
loop, the member and channel axes, the plug-in pair term and the map all held against a literal
double sum. The bugs below are method errors that the review exposed (research_notes.md, Review
round) and the code changes that fixed them, all in commit b88d490 on #27.

- **The plug-in estimate and straight-line distances** were replaced by the fair estimate and the
  shorter distance on periodic axes. The regression tests were written first and run on the old
  code with `python -m pytest -q metrics/variogram_score -p no:cacheprovider`, which gave
  "7 failed, 3 passed":
  - the worked example gave 9 where 8 was expected;
  - the double sums gave 79.17 against 62.36 (neumann, which also fails on the fair term) and 70.04
    (periodic);
  - the cyclic shift gave 234.11 against 237.26;
  - the narrowed two-member ensemble scored $-38.7$ where the test needs more than 3.2;
  - sizes 4 and 16 differed by 167.7 where the limit is 53.6.

  The same command after the fix gave "10 passed". A wider literal double sum on 1-D, 3-D,
  length-1-axis and mixed-boundary grids, at $M = 1$ and 3, agrees to $5.3\times10^{-15}$ or better
  in every map cell.
- **The map's charging rule** changed with the rewrite: each ordered pair is now visited once and
  charged to its first cell. The map still sums to the score, and the contract test passes.
- **`monotone_under_smoothing`** went from False back to the default True once the fair estimate
  made the contract blur ladder monotone (Tests, above, on why the stale False still passed).
- **The search for the same mistake elsewhere.** The agent looked for estimates squared or
  square-rooted after averaging over members in the other ensemble metrics.
  - `crps` and `energy_score` use the fair pair term.
  - `spread_skill` takes the square root of the mean variance and corrects for ensemble size with
    $\sqrt{(M+1)/M}$, the known-correct form.
  - `ensemble_mean_rmse` squares the error of the member mean, which carries Var/M by
    construction. But it is the error of the ensemble mean, not a score of the ensemble, and its
    card does not claim propriety.
  - `rank_histogram` has no such term.

  No other occurrence was found.

## Performance

- **Per evaluation**, fair and periodic version, sixteen members, measured on a NERSC login node:
  0.12 s at 32 by 32, 1.41 s at 64 by 64 and 17.8 s at 128 by 128. The reviewer measured the
  first, plug-in version at 0.79 s at 64 by 64 and 8.29 s at 128 by 128; the PR body gives 0.77 s
  for it at 64 by 64. By the measured growth, a 512 by 512 grid would take over an hour per
  evaluation.
- **Implementation speed.** The first fair implementation used fancy indexing and took 4.9 s at 64
  by 64. Slices of a doubled array gave the identical value in 1.4 s, 3.4 times faster. That is
  still about twice the first round's time, because every ordered pair is now visited.
- **Evidence runs.** The plug-in run took 115.8 s for 156 rows, and the re-run 234.1 s.
- **Cost unguarded; the map is computed twice** (likely future bug;
  medium confidence, since the 512 by 512 figure is an extrapolation). The default `analysis_grid`
  is the native resolution. The harness warns about an expensive metric only when more than 500
  frames are evaluated, never by grid size. On frames whose maps are stored, `fmeval/pipeline.py`
  calls a field companion as well as the metric, so a metric whose value is its map's sum is
  computed twice there. **Fixed in part**: the card states the measured cost and advises a coarse
  `analysis_grid.resolution` (card, Limitations), and `cost="expensive"` was already declared. A
  grid-size cost guard and reuse of a map's sum are harness changes that apply to every metric with
  a field companion. The build's remit was a plain metric, which rules out a harness change, so
  these went to [issues/114](../../issues/114-cost-warning-ignores-grid-and-maps-are-computed-twice.md).

## Tooling and environment problems

Shared with energy_score; see
[energy_score's code notes](../energy_score/code_notes.md#tooling-and-environment-problems).

## For the next agent

- The builder's first check would be the displacement loop against the double-sum test. The
  reviewer and the agent have both since checked it on 1-D, 3-D, length-1-axis, single-cell and
  mixed-boundary grids.
- The reviewer confirmed these edge cases: an empty ensemble raises `ValueError`; float32 and
  float64 agree exactly; a spacing whose length does not match the field raises; NaN propagates
  silently to a NaN result, as in `crps`, and the reader's default `nan_policy="error"` stops it
  before a metric is called.
- The reviewer's warning stands until issue 114 is resolved. Once an ensemble dataset at 256 or 512
  squared exists, a default run would take days, and nothing warns before it starts.
