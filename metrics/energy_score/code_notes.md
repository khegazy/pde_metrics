# Code notes: energy_score

This is the coding record of the build in pull request #27, condensed from the builder's and the
reviewer's records. The same launch built [variogram_score](../variogram_score/card.md). The
tooling and environment problems common to both bundles are recorded here once;
[variogram_score's code notes](../variogram_score/code_notes.md) hold what is specific to its code.
The research record is in [research_notes.md](research_notes.md).

## Summary

`metric.py` holds one function, `energy_score`, with no companion. It validates its input with the
shared `metrics/_ensemble.as_ensemble` and computes the fair estimator of Equation (2) on the card
directly from flattened member vectors. The review round found no bug in this code; its fixes to
energy_score were to the docstring, the card and the tests. A later CI failure of the docs build
came from two kinds of broken links, which were fixed in commit 5d8bead on #27. The bundle was
merged with every verification step passing.

## Implementation

- **Input.** `as_ensemble(reference, members, min_members=1, what="energy_score")` checks that the
  members carry a leading member axis over an array shaped like the reference and that the
  ensemble is not empty. The members are reshaped to `(M, -1)`, so every channel of every cell is
  one vector.
- **Distance term.** The mean over members of the Euclidean norm of member minus reference. This
  is the first term of Gneiting & Raftery's Eq. 22.
- **Pair term.** The code sums the norms over unordered pairs $i < j$ in a loop over $i$ and
  divides by $M(M-1)$. That equals $1/(2M(M-1))$ over ordered pairs, the fair pair term of
  Pacchiardi et al. 2024, App. C.1.1, halved because they write the estimator for twice the score.
  At $M = 1$ the pair term is skipped and the distance term is returned, as `crps` does.
- **Constants.** There is no numeric literal other than 0 and 1. The index $\beta = 1$ is implicit
  in using the plain norm.
- **Decorator.** `arity="ensemble"`, `fields=("*",)`, `differentiable=True` (a sum of Euclidean
  norms, with a subgradient where a norm is zero), `cost="cheap"` ($M(M+1)/2$ norms of one field
  each), `higher_is_better=False`, `symmetric=False` (reference and ensemble are different kinds
  of object), and `units="field"`. The default `reduction="mean"` is unused, since there is no
  companion. The reviewer noted that every companion-less metric in `docs/catalog.json` declares
  it the same way.
- **Changes outside the bundle.**
  - `tests/test_metric_contract.py`: `energy_score` joins `test_an_ensemble_metric_rises_with_bias`.
  - `tests/test_cards.py`: `energy_score` joins the literal set of the differentiable, cheap,
    measured catalog query.
  - `docs/catalog.json` was regenerated.
  - `metrics/_ensemble.py` and `metrics/crps/metric.py` are imported, not edited.

  The variogram score's changes outside its bundle are in its code notes.

## Tests

`metrics/energy_score/test_metric.py`:

- `test_worked_example_from_the_card`: a two-cell reference $(0,0)$ against members $(3,4)$ and
  $(0,4)$. The distances 5 and 4 average 4.5; the members are 3 apart, counted in both orders and
  divided by 4, a credit of 1.5; so the score is 3.
- `test_the_worked_example_is_not_the_mean_crps`: the same ensemble scores a mean CRPS of 2 cell by
  cell.
- `test_one_cell_is_the_crps`: on one value per field the score equals `crps`, which the test
  imports.
- `test_one_member_is_the_euclidean_distance`: at $M = 1$ the score is the L2 norm of the
  difference, to a relative tolerance of $10^{-12}$.
- `test_the_fair_estimator_is_unbiased_from_two_members` (parametrised at $M = 2$ and 8; renamed
  in the review from "at any ensemble size"): reference and members are drawn from $N(0, I)$ in
  four dimensions, 20 000 cases. The expected score is $\Gamma(5/2) = 3\sqrt{\pi}/4 = 1.3293$,
  from the mean of a chi distribution with four degrees of freedom. The tolerance is 2% relative.
  The plug-in estimator would give 1.994 at $M = 2$.
- `test_one_member_scores_twice_a_calibrated_ensemble` (added in the review): the same draws with
  one member have expectation $2\Gamma(5/2) = 2.6587$.
- `test_can_move_apart_from_the_mean_crps_without_any_covariation` (added in the review): three
  identical members at $(1,1)$ and at $(2,0)$ against $(0,0)$. Both have a mean CRPS of 1, and
  their energy scores are $\sqrt{2}$ and 2.
- `test_an_imperfect_ensemble_can_reach_the_floor_of_zero`: members $-1, 0, 1$ against 0 give a
  distance term of 2/3 and an ordered-pair sum of 8, and $8/12 = 2/3$, so the score is exactly 0.
- `test_the_fair_score_is_never_negative`: 500 draws with the reference at the ensemble mean,
  where the score is smallest, all non-negative, as the triangle inequality guarantees.
- `test_scales_linearly_with_the_field_units`: scaling every value by 3 scales the score by 3.
- `test_penalises_both_over_and_under_dispersion`: on an exchangeable ensemble, the calibrated
  ensemble beats one with spread scaled by 3 and one scaled by 0.2.
- `test_rejects_an_empty_ensemble`: a zero-member ensemble raises `ValueError`.

Verification after the review round, at commit eb74fac on #27: `agent_verify.sh` exited 0 at every
step for both bundles. pytest gave 1922 passed, 209 skipped, 9 deselected and 2 xfailed, in 244 s
for energy_score and 241 s for variogram_score.

## Bugs and fixes

- **Broken links in the docs build** (2026-10-31). CI's `mkdocs build --strict` failed on #27 with
  five warnings, reported by the orchestrator. There were two causes.
  1. When the idea page was renamed to `ensemble_calibration.md`, the builder searched only the
     README row and the theme page. So `docs/ideas/background.md` (one link) and
     `docs/ideas/evaluation_design.md` (three links) still pointed at
     `distributional/multivariate_proper_scores.md`.
  2. `metrics/energy_score/card.md` linked `../crps/card.md`. `docs/gen_pages.py` rewrites only the
     repository-relative form `../../metrics/<name>/card.md` for the flat site, so that link worked
     on GitHub but broke on the site.

  **Fix**, in commit 5d8bead on #27. The four idea-page links now point at the built cards, and the
  link for the distribution of spectra points at the narrowed page. The card link uses
  `../../metrics/crps/card.md`. A search of `docs`, `metrics`, `degradations`, `issues`,
  `judgements`, `fmeval`, `tests` and `configs` found no other reference to the old page and no
  other card link of the `../<name>/card.md` form. Without `-q`, `mkdocs build --strict` on the
  fixed tree exits 0 with no warning. Why the local check had passed is under Tooling and
  environment problems.
- **The card's fairness claims** (fairness at one member and the comparison with the mean CRPS) were documentation errors, not
  code bugs. They and their regression tests are in research_notes.md, Review round.

## Performance

- The evidence run, `results/energy_score_1793356825`, produced 156 rows in 0.7 s on
  `synthetic_ensemble` (12 frames, 64 analysis grid, 16 members).
- `cost="cheap"` is declared: one evaluation is $M(M+1)/2$ norms of one field each. Nothing was
  done about cost, and none was needed.

## Tooling and environment problems

These are common to both bundles of the launch.

- **No PDF renderer.** The Read tool could not render PDFs (no `pdftoppm` or poppler). The builder
  saved each PDF that WebFetch downloaded and extracted its text by inflating the PDF streams with
  zlib and reading the text operators (a small script, `pdftext.py`, not kept). Equation numbers
  were visible in all four sources read this way. The arXiv PDF of Pacchiardi et al. did not
  extract, so the JMLR PDF was used. The reviewer downloaded the sources with `curl` and converted
  them with `gs -sDEVICE=txtwrite`.
- **The self-check rejected the ensemble ladder's labels.** The orchestrator's `selfcheck.py`
  accepted only labels from `configs/degradation/default.yaml` in a pre-registration. An ensemble
  metric's evidence is the `ensemble_miscalibration` ladder, whose `spread_inflate`,
  `spread_deflate` and `bias` labels are not in `default.yaml`, and the brief itself names those
  axes. The builder declared them anyway and reported the problem without editing the self-check.
  The orchestrator fixed the self-check on 2026-10-31 to accept every ladder's enabled labels, and
  both self-checks then passed.
- **One bundle per agent.** The tooling assumed one bundle and one `PREREGISTRATION.yaml` per
  agent. The second bundle's declaration went into `PREREGISTRATION_variogram_score.yaml`, and the
  orchestrator extended the self-check to read it. Each declaration was pasted unchanged into the
  commit that added that bundle's `metric.py`. The PR's early "Blocked:" line came from these two
  tooling defects and was lifted once they were fixed.
- **`mkdocs build --strict -q` hides the warnings that strict mode counts.** With `-q` MkDocs logs
  only errors, so strict mode never sees a warning to count. The builder reproduced this by
  restoring the three files from eb74fac on #27: the quiet form exited 0 with no output, while the
  plain form exited 1 with "Aborted with 5 warnings in strict mode!". No untracked file or cache
  was involved. The orchestrator's `agent_verify.sh` used the quiet form. Dropping `-q`, or setting
  `DISABLE_MKDOCS_2_WARNING=true` as CI does to quiet only the advisory, would catch it. The
  records do not show this routed to an issue.
- **Scratch scripts imported the wrong `metrics` package.** A script run from the scratch
  directory imported the main checkout's `metrics` package (the editable install). Running it
  through `runpy` from the worktree root fixed this.
- **Sandbox refusals.** Two compound commands were refused, one mixing python and git output and
  one `python -c` containing backticks. They were split into plain commands or done with the Edit
  tool.
- **Lost scratch.** The first round's scratch summary script was not restored when the worktree was
  recreated for the review round, so it was rewritten.
- **`latexmk` absent.** It affects only report compilation, which was not needed.
- **The reviewer did not run `evaluate.py`**, because `results/` was a symlink into the main
  checkout and a run would have written outside its scratch area. It re-analysed the builder's two
  evidence runs instead.

## For the next agent

- The records name no code-level doubt about this bundle. The reviewer's edge-case checks are the
  ones to repeat after a change: an empty ensemble raises `ValueError`, identical members and a
  member equal to the reference give 0, and $M = 1$ returns the L2 distance.
- NaN propagates silently to a NaN result, as in `crps`. The reader's default `nan_policy="error"`
  stops it before a metric is called.
- The reviewer confirmed that float32 and float64 inputs give the same result exactly.
