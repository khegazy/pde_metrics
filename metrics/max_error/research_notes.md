# Research notes: max_error

This bundle was built by a metric-building agent from the idea page
`docs/ideas/norms/maximum_error.md`, which the build deleted. The work is pull request #25,
built on 2026-10-30 and merged on 2026-10-31, with an adversarial review round on 2026-10-30. This
file holds what the builder and the reviewer read, tried and concluded that the card does not
carry, condensed from their work log and records. The card is the source of truth for what the
metric is, and where the two disagree the card wins. The coding record is in
[code_notes.md](code_notes.md).

## Summary

The bundle is the pointwise $L^\infty$ control: the largest absolute error over every channel and
cell pooled, with a per-cell map reduced by a new `max` reduction (card, Definition). On
`kinet_re5e4` all seven pre-registered axes followed on every field. The review round corrected
the card's central pitfall: a displaced jump scores its full height only when its face sits on a
cell boundary and the shift does not wrap. It also measured why the Gaussian impostor scores near
the anchor on density. Density's largest departure from its mean is one deep minimum on the
strongest vortex core, so both the metric and its anchor are set by that one cell. Why the
harness's median over 161 frames (0.955) sits below the per-frame medians measured separately
(about 1.02) is still unexplained.

## Sources

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| Takamoto et al. 2022, Advances in Neural Information Processing Systems 35 (Datasets and Benchmarks Track), 1596-1611, DOI 10.52202/068431-0117 | Full text (the NeurIPS proceedings PDF, decoded by the agent's own stream decoder; Appendix B through the ar5iv rendering of arXiv:2210.07182, because the arXiv PDF arrived truncated) | Sect. 3.3 | PDEBench reports a "max error" among its data-view metrics beside RMSE and nRMSE: the maximum error, "local worst case; also proxy for stability of time-stepping". Appendix B says only that it measures the model's worst prediction, and gives no equation and no channel reduction. The reviewer confirmed the quoted row. | `metric.py`, card, `refs.bib` |
| Takamoto et al. 2022, the same paper read as a benchmark | Full text | Sect. 3.3 | The metric table splits a data view (RMSE, nRMSE, max error) from a physics view: cRMSE of conserved quantities, bRMSE on the boundary, and fRMSE in low, middle and high Fourier bands. PDEBench is already a benchmark on [evaluation_design.md](../../docs/ideas/evaluation_design.md), and its fRMSE is on [spectral_band_error.md](../../docs/ideas/basis_decompositions/spectral_band_error.md), so no new EXP document was written. | Not used |
| PDEBench code, `pdebench/models/metrics.py`, function `metric_func`, https://github.com/pdebench/PDEBench/blob/main/pdebench/models/metrics.py | Full text | none | The code takes the maximum of the absolute error over space separately for each channel and time step, then the maximum over the batch, and then (with `if_mean`) the mean over channels and time steps. Its channel reduction is a mean of per-channel maxima, not this bundle's pooled maximum. The two agree on every one-channel field (density, vorticity) and differ only on velocity. The reviewer confirmed the order of reductions. | Card |
| Roy 2005, Journal of Computational Physics 205(1), 131-156, DOI 10.1016/j.jcp.2004.10.036 | Full text (the published PDF, decoded by the agent's own stream decoder) | Sect. 2.5 Eq. 7; Eq. 8 | The discrete $L^\infty$ norm of the global discretisation error, the maximum over all mesh nodes of $\lvert f_{k,n} - f_{\mathrm{exact},n}\rvert$, defined under one number with the discrete L2 norm (Eq. 7). The observed order of accuracy is read from either (Eq. 8). The decoder rendered the infinity subscript as "L1", but the "max" beside it fixes which norm it is. The reviewer re-read the paper with its own decoder and confirmed Eq. 7 in Sect. 2.5 ("Method of manufactured solutions") on journal page 139; the "L1" is the symbol font's infinity glyph. The orchestrator also confirmed Eq. 7 in the agent's copy. | `metric.py`, card, `refs.bib` |
| Roy 2005, the same paper | Full text | Sect. 3.5.6 (the agent first wrote Sect. 3.5; the reviewer located the subsection) | Flows with shock waves are rarely resolved into the asymptotic range, and for the Euler equations shock-capturing simulations reduce to first-order accuracy whatever the formal order (citing Carpenter and Casper 1999, not opened). This was the starting point of the card's double-penalty pitfall (Review round, the displaced-jump claim). | Card |
| LeVeque 2007, Finite Difference Methods for Ordinary and Partial Differential Equations, SIAM, Appendix A, DOI 10.1137/1.9780898717839 | Not opened | none | A common reference for grid-function norms, including the max norm. No readable copy was reachable: SIAM returned 403, and the course copies returned 404 or a portal page. Not cited. | Not cited |

The agent checked both cited DOIs against their Crossref records (title, year, first author,
pages), and the reviewer confirmed them on title, author list and order, venue, volume, issue,
pages and year.

## Method choices

- **Channel reduction on velocity.** Four options were weighed.
  1. The maximum over channels and cells pooled. This was built, because the repository's
     controls pool channels the same way into their means, so `mae`, `rmse` and `max_error` read
     one consistent norm of the flattened vector (L1, L2, $L^\infty$). This is the agent's own
     choice, recorded on the card and in the docstring.
  2. PDEBench's mean of per-channel maxima, written up as a variant (Open questions).
  3. The maximum over cells of the Euclidean length of the error vector, which is rotation
     invariant, also written up as a variant.
  4. The maximum of the channel-summed absolute error, which would have reused `mae_map`
     directly. It was rejected as a mixed norm with no source.
- **A companion map with a new `max` reduction**, rather than no companion. The map shows where
  the worst cell is, which is the point of the metric. This is the agent's own choice under the
  rule in AGENTS.md §3.3 that allows adding a reduction.
- **`differentiable=True`.** The metric is piecewise linear, with a subgradient at ties. The card
  says its gradient reaches one cell only (Review round, the point about differentiability).
- **Pre-registration** (in commit 6efd5c3 on #25, which added `metric.py`, before any full-ladder
  run). Seven axes were declared to follow with direction +1: `gaussian_blur`, `box_blur`,
  `lowpass_butterworth`, `translate_x`, `translate_subpixel`, `coarsen` and `additive_noise`.
  These are the axes that damage pointwise values by construction and whose ordering the controls
  already show on all three fields. The agent left out `median_blur`, `lowpass_ideal`, the
  high-pass pair and `coarsen_bandlimited`. On those, the sharp filters' few distinct levels on
  density, or [issues/039](../../issues/039-h1-seminorm-is-not-monotone-under-coarsening.md), make
  the ordering doubtful for any pointwise metric. Blind: none, since no operator preserves
  pointwise values. Fields `*`, lower is better, units "field", reduction "max".
- **No convention issue and no judgement record.** The registered number is the standard discrete
  $L^\infty$ norm (Roy 2005, Eq. 7), not a convention. No choice here was one the agent would have
  stopped to ask about.
- **Two comparison subsections.** The agent first deleted the card's "Compared with the other
  metrics" and "Damage beside the other metrics" subsections, because a single-metric run cannot
  fill them and the brief asks for one metric per evaluation. The review reversed this (Review round, the deleted comparison
  subsections).

## Rejected formulations and negative results

The one formulation rejected outright, the maximum of the channel-summed absolute error, is
under Method choices with the options it was weighed against. The card's first jump claim, later
corrected, is under Review round (the displaced-jump claim).

## Evidence runs

1. **Smoke run** `results/max_error_1793354376`, on `kinet_re5e4_dev` with `degradation=quick`.
   It produced 3000 rows in 20 s and showed only that the metric runs end to end.
2. **Evidence run** `results/max_error_1793355020`, run as `python evaluate.py
   metrics=[max_error] dataset=kinet_re5e4 dataset.time.start=2000 dataset.time.reduction=50
   paths.data_url=null`. It covered frames 2000 to 10000 (161 frames) on the 256 analysis grid
   with seed 20260807. It ran at commit e4da8d3 on #25 with a clean tree; that commit descends from
   the declaration commit and adds only a `.gitkeep`. It produced 28497 rows in 907.7 s. The
   reviewer decoded the run id as 10:10:20 UTC, 15 s after the declaration commit, and confirmed
   that no full-ladder run predates it.
   - **The declaration is met.** All seven declared axes have direction +1 and `rho_ci_lo` = 1.0 on
     density, velocity and vorticity, with no contradiction. The only rank correlation below 1 is
     on the undeclared `highpass_ideal` on vorticity: 0.8, in order in 0.478 of frames, with a
     weakest gap of 0.489. That axis was left out of the declaration because the sharp high-pass
     is squeezed on these spectra.
   - **The trap test.** The Gaussian impostor scores damage 0.955 on density, and the far-moved
     reference 0.959, both slightly below the mean-field anchor. On velocity and vorticity the
     impostor scores 1.6 and 1.2. The first card reading said only that by its worst cell the
     metric rates a phase-scrambled density about as close as the mean, without explaining why.
     The orchestrator filed this as
     [issues/106](../../issues/106-max-error-scores-the-density-impostor-under-the-anchor.md), and
     the review round measured the cause (Review round, the density impostor).
3. **No re-run after the review.** No fix changed a number. Regenerating the card's evidence from
   `results/max_error_1793355020` left `_generated/` byte-identical.

The card now cites `results/comparison_1793657627` (card, Results), a later multi-metric refresh
that is outside this build's records and that filled the two comparison subsections. The numbers
above are those of the build's own run.

## Corrections to the rest of the repository

- **The idea page had no references.** Its Rationale said only that it comes from the field guide.
  The card's references (Takamoto et al. 2022, Roy 2005) were found by this agent, so no reference
  had to be carried from the page. Its three pitfalls went into the card's Limitations, which the
  orchestrator and the reviewer confirmed. The page was deleted, its row in `docs/ideas/README.md`
  and its bullet in `docs/ideas/norms/README.md` were removed, the theme page's "built already"
  sentence names `max_error`, and the pointwise row of the table in
  [background.md](../../docs/ideas/background.md) links the card. The reviewer found no stale link
  to `maximum_error.md` left in `docs/`, `mkdocs.yml` or the code.
- **Issue 106's conjecture was wrong.** The issue attributed the density impostor result to
  density's energy sitting in a few large-scale modes. The review's measurement contradicts this
  (Review round, the density impostor). The orchestrator rewrote issue 106 with the measured cause.
- **AGENTS.md said maps are summed over channels**, which the new `max` reduction contradicts.
  This is fixed; see code_notes.md, Bugs and fixes.

## Review round

The reviewer raised nine critiques: no present bug, one likely future bug, two on theory or
citation, three on documentation and three minor. The agent reproduced each with the reviewer's
scripts before answering. The fixes are in commit 9a211e0 on #25. The critiques about the `max`
reduction untested on two channels, about AGENTS.md and the documentation test, and about input
validation concern code and are in code_notes.md under Bugs and fixes.

- **The displaced-jump claim** (theory; high confidence). The card said that a jump of
  height $h$ moved by one cell or more gives $\mathrm{MaxE} = h$ whatever the displacement. The
  agent had derived this from Roy's shock remark: for a pointwise maximum, a jump displaced by one
  cell or more gives an error equal to the jump height, so the error does not shrink with
  displacement at all. The claim holds only for a face on a cell boundary and a shift that does not
  wrap a periodic domain. The reviewer's exact counterexamples:
  - a face inside a cell holding the fraction $a$ of the high state scores $\max(a, 1-a)h$ at a
    one-cell shift (0.70 at $a = 0.3$ and 0.50 at $a = 0.5$), and $h$ only from two cells;
  - a jump on a smooth background scores 1.000, 1.030 and 1.070 at shifts 1, 4 and 8, above $h$
    and growing;
  - a square rolled by its 4-cell period scores 0.

  The test behind the claim passed only because the "two-cell" shift wrapped a 4-cell periodic
  axis. The Limitations sentence "as much as a prediction that has no front at all" also held only
  for a front-less prediction at the low state; the mean-field anchor of a half-high step scores
  $h/2$. **Fixed**: the card states the cell-face condition and the periodic exception, adds
  Equation (4), and says that a varying background pushes the value above $h$ (card, Definition
  and Limitations). The tests were replaced (code_notes.md, Tests). A search
  (`grep -rln "full height\|whatever the size" metrics/*/card.md`) found the claim on no other
  card.
- **The density impostor has a measurable cause** (theory; medium-high confidence).
  - **Where the extreme sits.** Density's largest departure from its mean is always one deep
    minimum, 5.5 to 7.3 standard deviations deep, on the strongest vortex core. On 17 frames from
    2000 to 10000, density skewness was $-1.45$ to $-3.76$ and flatness 5.9 to 20.6, the extreme
    was negative in 17 of 17 frames, and the median of its depth over the standard deviation was
    5.70. Velocity was close to Gaussian: skewness about 0, flatness 1.8 to 2.2, and a median depth
    of 2.37 standard deviations. At the density minimum the vorticity was $+5.24\sigma$,
    $-6.24\sigma$, $+7.28\sigma$ and $+7.59\sigma$ in frames 2500, 5000, 8000 and 10000, against
    field maxima of $5.47\sigma$, $6.38\sigma$, $7.46\sigma$ and $7.63\sigma$.
  - **What that does to the trap test.** Any field unrelated to the reference that lacks the
    minimum scores damage near 1, about $1 \pm \sigma/A \approx 1 \pm 0.17$ for a minimum of depth
    $A$. Over 300 impostor seeds per frame the median damage was 1.017, 1.015 and 1.024 on frames
    3000, 5000 and 8000 (10-90%: 0.80-1.19, 0.78-1.22, 0.77-1.23), with minimum depths of 6.51,
    5.85 and 5.46 standard deviations. For 300 large shifts it was 1.042, 1.045 and 1.053. An
    earlier 3-seed sample, which gave 0.82 to 0.90, was unrepresentative: the minimum stays near
    the same cells across frames, so a fixed seed lands on the same impostor value there.
  - **The conjecture it replaces.** Issue 106 guessed that density's energy sits in a few
    large-scale modes. By the reviewer's argument, which is reasoning and not a measurement, that
    mechanism predicts damage near $4/\pi \approx 1.27$: the difference of two copies of one wave
    with a random phase difference has a mean amplitude of $4a/\pi$. The measured values near 1
    contradict it. On velocity the difference of two uncorrelated copies has $\sqrt2$ times the
    standard deviation, which gives the measured damage of about 1.6.
  - **Physical attribution.** That the minimum is low pressure in a vortex core, with pressure
    proportional to density in a weakly compressible isothermal flow, is the reviewer's reasoning
    from the measured co-location, not a cited source.

  **Answered on the card, not closed.** The trap-test reading no longer calls 0.955 "slightly
  better than the mean". A Limitations paragraph says that on this density both the metric and its
  anchor are set by one minimum on the strongest vortex core. The spread figures are not in the
  Results prose, because they do not come from the evidence run. The orchestrator rewrote issue 106
  with the measured cause. **Still open:** why the harness's median over 161 frames, 0.955, sits
  below every per-frame median above, although it lies inside their 10-90% ranges.
- **The field gallery saturates the worst cell** (documentation; high confidence on the
  clipping, a judgement on the caption). `fmeval/report/plots.py::field_gallery` clips colour at
  the 0.995 quantile of all panels of one metric, and captions each map "Per-cell contribution to
  the metric", as `TEST_DESCRIPTION.md` also describes it. For a maximum map the worst cell, which
  is the metric, is saturated in 9 of the 30 panels of `results/max_error_1793355020` (3 per
  field; for example, max/vmax 2.55 on vorticity `gaussian_impostor_l1` and 2.23 on
  `translate_x_l5`). Every cell except one contributes nothing. **Fixed on the card**, which now
  warns readers to read the value from the stored map (card, Reading the output). The renderer is
  shared code, so it went to
  [issues/108](../../issues/108-field-gallery-hides-the-cell-a-maximum-map-is-about.md), with the
  options of marking each panel's maximum, captioning by the declared reduction, or leaving it
  with the card's warning.
- **"Differentiable on the same footing as mae"** (minor; medium confidence). The
  comment in `tests/test_cards.py` claimed this. The subgradient of `mae` is $\mathrm{sign}(e_j)/N$
  at every cell, while that of `max_error` is one-hot at the argmax. **Fixed**: the comment and
  the PR body say the gradient reaches one entry only. `differentiable=True` stays, as the
  registry defines it ("could this be a training loss?").
- **The deleted comparison subsections** (documentation). The evidence generator
  (`fmeval/cards/evidence.py`) skips a missing block without warning, so a later multi-metric
  refresh would never fill them. The generator already writes a one-line note for a single-metric
  run. The cross-metric correlation is step 5 of the evaluation protocol in CLAUDE.md. **Fixed**:
  both subsections were restored with their generated markers, and the later refresh filled them.
  The four ensemble cards that also lack the blocks were not this branch's to change.
- **"Equation (1) holds unchanged on a non-uniform grid"** (minor). The formula is
  unchanged, but on a non-uniform grid of cell averages a peak inside a coarse cell is averaged
  down more than one inside a fine cell, so the value depends on where the grid is refined.
  **Fixed** on the card (card, Definition). This is reasoning from the definition of a cell
  average, the reviewer's and the agent's alike, with no source and no measurement.

The reviewer also checked and found sound: Eq. (3), $\mathrm{MaxE} \approx \delta\max\lvert\partial_x f\rvert$,
to five digits on a smooth periodic field shifted by 0.05 and 0.1 cells; the exact $\sqrt2$
orientation factor for pooled velocity; the triangle inequality; the anchor values against the
fingerprint's `mean_field_value` (0.0386, 0.0937 and 0.0169); the decorator; the pre-registration
in its commit; the evidence provenance; and every number in the Results prose against the
generated tables.

## Open questions and follow-ups

- **The rollout use of the maximum error.** PDEBench takes the worst case over the batch of
  samples, while this harness scores one frame at a time and summarises frames by medians. The idea
  page's use as a stability diagnostic, its growth along a rollout, needs a rollout input the
  harness does not have. That gap is already
  [issues/094](../../issues/094-dynamics-family-has-a-test-bed-but-no-rollout-input.md), item 4.
- **The density impostor gap**:
  [issues/106](../../issues/106-max-error-scores-the-density-impostor-under-the-anchor.md).
- **The gallery clipping**:
  [issues/108](../../issues/108-field-gallery-hides-the-cell-a-maximum-map-is-about.md).
- **PDEBench's channel reduction**, the mean of per-channel maxima:
  [MTR-max_error-mean-of-channel-maxima](../../proposals/MTR-max_error-mean-of-channel-maxima.md).
- **The maximum of the error vector's length**:
  [MTR-max_error-vector-magnitude](../../proposals/MTR-max_error-vector-magnitude.md) (the agent's
  own).
- **A high quantile of the pointwise error**, for example the 99th percentile. It would sit
  between `mae` and `max_error` and address the maximum's single-cell noise and grid dependence.
  It is by analogy with the 95th-percentile Hausdorff distance recorded on the shock-set-distance
  idea page, since deleted because that metric is built as
  [shock_set_distance](../shock_set_distance/card.md). No source applying it to field errors was
  found. The proposal is
  [MTR-max_error-high-quantile-error](../../proposals/MTR-max_error-high-quantile-error.md).

## For the next agent

- The builder was least sure of the Roy (2005) equation number, which came from its own decoder.
  The reviewer and the orchestrator have both since confirmed Eq. 7.
- LeVeque's Appendix A, the textbook reference, could not be verified.
- The open scientific question is the gap between the harness's median of 0.955 and the per-frame
  medians near 1.02 on density (issue 106).
- The builder's first checks were whether the pooled-channel choice is stated identically in the
  docstring, the card and the PR, and whether the Results readings quote only numbers present in
  the generated tables. The reviewer found the second true for the build's run.
