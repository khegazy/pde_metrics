# Research notes: shock_mask_overlap

This bundle was built by a metric-building agent from the idea page
`docs/ideas/shock_geometry/shock_mask_overlap.md`, which the build narrowed and renamed to
[shock_boundary_f_score.md](../../docs/ideas/shock_geometry/shock_boundary_f_score.md), in pull
request #30 (built 2026-10-31, merged 2026-11-02), with an adversarial review round on
2026-10-31. This file holds what the builder and the reviewer read, tried and concluded that the
card does not carry, condensed from their work log and records. The card is the source of truth
for what the metric is; where the two disagree, the card wins. The coding record is in
[code_notes.md](code_notes.md).

## Summary

The bundle registers the Dice coefficient of the shocked cells that the detector of
`shock_set_distance` marks in two pressure fields (card, Definition). The Jaccard index was not
registered because it ranks every candidate identically, and the boundary F-score was not built
because its matching tolerance could not be sourced from a primary paper. On the Sod shock tube
all three declared axes moved in the declared direction, and the metric is not listed blind to
any axis, which contradicted a prediction in issue 104. The main caveats are that a shock moved
by two cells or more scores the same 0 as one moved across the domain, that anything which
lowers the pressure ratio across a shock (a smear, an offset, a high-pass filter) erases it, and
that the score for two empty sets (1) is the builder's own convention and is never reached on
the Sod evidence. The review round found the card's reading of the high-pass filters and of the
half-cell shift to be wrong mechanisms, and found the same two errors on `shock_set_distance`'s
card, where they are still open.

## Sources

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| Taha & Hanbury 2015, BMC Medical Imaging 15, 29, doi 10.1186/s12880-015-0068-x | Full text, in the PMC copy PMC4533825 through a fetch tool quoting it; the orchestrator confirmed Eqs. 6-8 in the same full text | Eqs. 6-9, Table 1; the discussion of small segments ("Segment size") | Eq. 6 $\mathrm{DICE} = 2\lvert S_g \cap S_t\rvert/(\lvert S_g\rvert+\lvert S_t\rvert) = 2TP/(2TP+FP+FN)$, called the most used metric for medical volume segmentation; Eq. 7 $\mathrm{JAC} = TP/(TP+FP+FN)$; Eqs. 8-9 $\mathrm{JAC} = \mathrm{DICE}/(2-\mathrm{DICE})$ and $\mathrm{DICE} = 2\mathrm{JAC}/(1+\mathrm{JAC})$, with the statement that both "measure the same aspects and provide the same system ranking"; Table 1 row "F-Measure (F1-Measure=Dice)"; overlap metrics "provide the same value regardless of how far the segments are from each other" (the reviewer notes the source adds "once the overlap is zero") | `metric.py`, card (Definition, Limitations), `refs.bib`, the tests |
| Maier-Hein et al. 2024, Nature Methods 21, 195-212, doi 10.1038/s41592-023-02151-z (Metrics Reloaded) | Secondary: the arXiv HTML copy 2206.01653v8, in pieces, through a summarising fetch tool; the PDF fetch failed on its size limit and characters 300000-396482 were never read. First recorded as full text, corrected to secondary in the review round | Main-text Results ("Semantic segmentation (SemS)", step 1; "Step 2 - Metric Selection"); Suppl. Note 2.3 | Main text: "the DSC or IoU (default recommendation)" and "the concrete choice typically boils down to a simple user or community preference". Suppl. Note 2.3: "our default recommendation is the DSC ..., which is almost identical to the IoU", and "We recommend handling of NaN by setting the corresponding metric value to the worst possible value". No rule was found for reference and prediction both empty. The reviewer reports that the published version, PMC11182665, uses the same supplementary numbering; the builder did not open it | Card (Definition, Empty sets), `refs.bib`, [issue 120](../../issues/120-shock-mask-overlap-both-empty-convention.md) |
| Dice 1945, Ecology 26(3), 297-302, doi 10.2307/1932409 | Not opened (the JSTOR page would not load); bibliographic data checked against Crossref | None | Only the title, "Measures of the amount of ecologic association between species"; cited as the origin of the coefficient | Card (Definition), `refs.bib` |
| Jaccard 1912, New Phytologist 11, 37-50, doi 10.1111/j.1469-8137.1912.tb05611.x | Not opened (the Wiley page returned 403); bibliographic data checked against Crossref | None | Cited as the origin of the Jaccard index | Card (Definition), `refs.bib` |
| Schaal & Springel 2015, MNRAS 446, 3992, doi 10.1093/mnras/stu2386 | Read by the agent that built `shock_set_distance`, not in this build; the reviewer rechecked the constant | Sect. 2.3.2, Eq. 2 | The detector's pressure-ratio threshold, 1.805 for Mach 1.3 at $\gamma = 1.4$; Sod's ratio 3.031 and shock speed 1.75216 were rechecked by the reviewer | Card (Definition, through the imported detector), `refs.bib` |
| Martin, Fowlkes & Malik 2004, IEEE TPAMI 26(5), 530-549, doi 10.1109/TPAMI.2004.1273918 | Not opened: the Berkeley PDF downloaded, but the environment had no PDF text tool | None | Nothing; it remains the source of the boundary F-score | The narrowed idea page only |
| Berkeley Segmentation Dataset benchmark code, `boundaryBench.m` and `correspondPixels.m` | Full text of the scripts (fetched) | `correspondPixels.m` header comment | `boundaryBench.m` shows no tolerance default. `correspondPixels.m` computes a "minimum-cost correspondance between two boundary maps" and gives "[maxDist=0.01] Maximum distance allowed between matched pixels, as a fraction of the image diagonal"; the reviewer read "minimum-cost correspondance" and "assignment edges" as pointing to one-to-one matching (a reading of the header, not of Martin et al.) | The narrowed idea page |
| MathWorks `bfscore` documentation, https://www.mathworks.com/help/images/ref/bfscore.html | Secondary. At build time the figure came only from a web-search summary; the page itself was fetched in the review round | The default-tolerance sentence | "The default value is 0.75% of the length of the image diagonal", not attributed to the benchmark: 15.4 cells on Sod's 2048 cells and 2.7 cells on a 256 by 256 grid | The narrowed idea page |
| arXiv 1808.01992 | Search result only (reviewer) | None | Says that BSDS evaluation uses 0.0075 of the diagonal | Not used |
| Antonio & Aitchison 2025, Mon. Weather Rev. 153(6), 1021-1033 (arXiv 2311.11985v3) | Secondary: the arXiv HTML copy through a fetch tool; the reviewer checked the equations in the same copy | Eqs. 1, 2, 5, 21 | The fractions skill score $\mathrm{FSS}(n) = 2\langle o(n) f(n)\rangle / (\langle f(n)^2\rangle + \langle o(n)^2\rangle)$ over a window of width $2n+1$ ($n$ a half-width), Eq. 5 | [proposals/MTR-shock_mask_overlap-fractions-skill-score.md](../../proposals/MTR-shock_mask_overlap-fractions-skill-score.md) |
| Roberts & Lean 2008, Mon. Weather Rev. 136(1), 78-97, doi 10.1175/2007MWR2123.1 | Not opened | None | The original fractions skill score | The proposal above |
| Cheng, Girshick, Dollar, Berg & Kirillov 2021, CVPR (arXiv 2103.16562) | Abstract | None | Boundary IoU, a segmentation measure "focused on boundary quality" | Not used (rejected, below) |
| Gilbert 1884; Schaefer 1990, Weather Forecast. 5(4), 570-575 | Not opened; named as the usual citations for the critical success index | None | Nothing read | Not used (rejected, below) |

## Method choices

- **The registered score is the Dice coefficient** (card, Definition). The options were the
  Jaccard index, the Dice coefficient and the boundary F-score. Jaccard and Dice are monotone
  transforms of each other (Taha & Hanbury 2015, Eqs. 8-9) and rank every candidate alike, and
  Metrics Reloaded calls the choice a community preference. Dice was taken because Taha and
  Hanbury call it the most used, and because it is the boundary F-score at zero tolerance, which
  ties the bundle to the rest of the idea. That identity is the builder's derivation; the
  reviewer checked it (the harmonic mean of $I/\lvert B\rvert$ and $I/\lvert A\rvert$ is
  $2I/(\lvert A\rvert+\lvert B\rvert)$).
- **Two empty sets score 1.** This is the builder's convention, recorded in
  [issue 120](../../issues/120-shock-mask-overlap-both-empty-convention.md). The options were 1,
  0 (Metrics Reloaded's worst-value rule for undefined values, Suppl. Note 2.3), NaN, or NaN with
  a separate detection count. The reason given is that 1 matches `shock_set_distance`'s "both
  empty is perfect", and that 0 would charge a smooth prediction of a smooth reference as a total
  failure.
- **Channels are averaged, and a non-finite field scores NaN**, both as `shock_set_distance`
  does. Without the NaN rule, a NaN candidate against a smooth reference would flag nothing and
  score a perfect 1.
- **No companion.** The object behind the number is a map of three classes (cells both fields
  flag, cells only the reference flags, cells only the candidate flags), and none of the
  registry's reductions turns it into the ratio; the build rules forbid a new companion kind
  (card, Definition).
- **Category geometric**, as for `shock_set_distance`.
- **The idea page was narrowed and renamed, not deleted.** The metric covers Jaccard and Dice but
  not the boundary F-score, so the page was narrowed (the add-a-metric recipe's step 7.3) and
  renamed to `shock_boundary_f_score.md`, because `tests/test_documentation.py` fails on an idea
  page named after a built metric. Dice 1945 and Jaccard 1912 moved to the bundle's `refs.bib`
  and card. Martin et al. 2004 stayed on the narrowed page and is not in `refs.bib`, since the
  card cites no claim from it. The thin-object pitfall (an intersection over union of one third
  for a one-cell shift, zero for two cells) is on the card's Limitations and in the tests in its
  Dice form (one half, then zero). The team's medium-priority rationale stayed on the narrowed
  page. Every link to the old page name was updated (the ideas README row, the theme README,
  `docs/ideas/evaluation_design.md`, issue 102 and two proposals).
- **`scale_dependent: false` was kept** after the review (critique below). A negative constant
  does not rescale a pressure, the detector's own bundle declares the same, and the schema's
  wording does not say whether the constant may be negative. The `card.yaml` comment now states
  the restriction to a positive constant.
- **Pre-registration** (commit b63f93a on #30, before the evidence run). Declared to follow,
  each with direction $-1$: `translate_x` (an integer translation moves both detected cells by
  the shift, so the pairs share one cell at a shift of one and none from two), `translate_subpixel`
  (the detected cells follow the shift in whole-cell steps), and `additive_noise` (noise whose
  cell-to-cell ratio reaches that of a Mach 1.3 shock is flagged away from the true shock).
  Declared blind: none. `coarsen` was not declared, because where the shock moves to a block edge
  depends on where the block boundaries fall, so its direction per frame could not be stated with
  confidence. The smoothing and spectral axes were not declared, because they remove the shock at
  the mildest strength and the value ties at 0. The declared mechanism for `translate_subpixel`
  turned out wrong at half a cell, although its direction held (Evidence runs).

## Rejected formulations and negative results

- **The Jaccard index** (Taha & Hanbury 2015, Eq. 7). It equals $\mathrm{DICE}/(2-\mathrm{DICE})$
  (their Eq. 8), a strictly increasing function of the Dice coefficient, so every rank statistic
  the harness computes would be identical and it would be a redundant panel member. Its one
  advantage, that one minus it satisfies the triangle inequality on finite sets, was called a
  standard result and not checked in a source; it matters for a loss rather than for ranking. A
  sibling bundle importing this one would take two lines if it is wanted.
- **The boundary F-score.** Its matching tolerance is a threshold that could not be sourced from
  a primary paper, since Martin et al. 2004 could not be read. The defaults found in code, 0.75%
  of the image diagonal in MathWorks' `bfscore` and 0.01 in the Berkeley `correspondPixels.m`,
  are 15.4 and 20.5 cells on the Sod tube (2.7 and 3.6 cells on a 256 by 256 grid), which would
  make the score blind to every `translate_x` shift below 16 cells. Left on the narrowed idea
  page.
- **Boundary IoU** (Cheng et al. 2021). Not proposed. The builder's reasoning, from the abstract
  and Metrics Reloaded's table entry rather than the paper's definition: a detected shock is
  already a layer two cells thick, so its boundary region is the whole mask, and Boundary IoU
  reduces to the mask intersection over union that this bundle already ranks identically.
- **The critical success index (threat score)** of weather verification, hits over hits plus
  misses plus false alarms. It has the form of the Jaccard index of the forecast and observed
  event sets (the builder's identification from the definitions, not read in a primary source),
  so it is not a new metric here. Recorded so that a later agent does not propose it.
- **Metrics Reloaded's worst-value rule for the both-empty case** (0) was rejected for the reason
  given under Method choices.

## Evidence runs

1. **Contract-test blur ladder, off-run.** On the contract test's synthetic blur ladder, 37 of 128
   reference cells were flagged and the values were 1, 0.815, 0.641, 0.5 and 0.525, a Spearman
   correlation of $-0.9$, so the declaration `monotone_under_smoothing=False` is true (the
   response is not a perfect $-1$); float32 and float64 agree.
2. **Smoke run, before the pre-registration:** `results/shock_mask_overlap_1793493559`,
   `sod_shock_tube` with `degradation=quick`. Identity scored 1 and `mean_field` 0 in all ten
   frames, so every reference frame holds a shock; `translate_subpixel` scored 0.667 at half a
   cell and 0 at two cells; `gaussian_blur` 0 at both strengths; the impostor 0. No conclusion was
   drawn beyond the pipeline running the metric.
3. **Evidence run:** `results/shock_mask_overlap_1793494245`, from the clean pre-registration
   commit b63f93a on #30, `python evaluate.py metrics=[shock_mask_overlap] dataset=sod_shock_tube
   paths.data_url=null`: the reader's ten frames, the 2048-cell analysis grid, the default
   ladder, 590 rows. All three declared axes followed with direction $-1$: `rho_frame_min` 0.707
   for `translate_x` (below the 0.90 advisory threshold, from the ties at 0 from a two-cell
   shift), 0.971 for `translate_subpixel` and 0.949 for `additive_noise`. `blind_axes` is empty,
   as declared. The identity scored 1 and the `mean_field` anchor 0 in all ten frames, so the
   both-empty convention is used by no row; the reviewer confirmed that the opposite convention
   would change no reported number. The readings per family are on the card (Results).
4. **Off-run half-cell check.** The half-cell value, 2/3 in every frame, disagreed with
   `shock_set_distance`'s card. On the exact Sod pressure at $t = 0.1$ with a periodic Fourier
   shift, only cell 1383 is flagged, and the shift rings: at a quarter- and half-cell shift the
   states beside the jump overshoot and undershoot (0.331 and 0.288 on a post-shock plateau of
   0.303, 0.072 on a pre-shock plateau of 0.1). The reviewer reproduced this through the
   pipeline's own path (`apply_severity_level`, wall extension rather than a periodic grid),
   frames 0, 5 and 9: at half a cell one cell is flagged ([1383], [1582], [1742]) with neighbours
   0.3309 / 0.2016 / 0.0722 and a Dice of 0.6667; at one cell two cells and 0.5. The declared
   mechanism for `translate_subpixel` ("whole-cell steps") is therefore wrong at half a cell,
   though its direction held; the pre-registration was not edited. The scripts (`halfcell.py`,
   the reviewer's `pipeline_masks.py`) were not kept in the repository.
5. **Review-round measurements** (off-run, no `evaluate.py` run): the high-pass operators applied
   as the pipeline applies them, the pressure offset, cell-averaged shocks and the Taylor-Green
   gauge pressure; each is described under Review round. None changed a number on the evidence
   path, so the evidence was not re-run.
6. **Orchestrator checks.** A Sod smoke run (`shock_mask_overlap_1793495529`) gave no
   periodic-domain warning, and a quick Sod run at the post-review head, commit 82b10b7 on #30
   (`shock_mask_overlap_1793497736`), was identical to the evidence on all 100 matched rows. Both
   folders are kept in the launch's log archive, not under `results/`.

The card currently cites `results/shock_mask_overlap_1793494245`.

## Corrections to the rest of the repository

- **`shock_set_distance`'s card, the half-cell shift** (card, Results, Displacement). It says a
  half-cell sub-pixel shift "flags three cells instead of two and scores a third of a cell". The
  score is right and the count is wrong: one cell is flagged, and the average symmetric distance
  of {1382, 1383} against {1383} is $(1 + 0 + 0)/3 = 1/3$; three flagged cells would give $1/5$.
  The cause is the Fourier ringing described under Evidence runs. Found by the builder, reproduced
  independently by the reviewer through the pipeline's path. Routed to
  an issue; the `shock_set_distance` card has since been corrected and the issue deleted.
- **`shock_set_distance`'s card, the high-pass reading.** It reads its spectral-filter results
  as "shock kept" or "shock lost". The high-pass filters keep the jump (0.20 of 0.203) but raise
  the pre-shock plateau to 0.24-0.51, so the ratio across the intact shock falls to 1.84, 1.80 or
  1.40 against the threshold 1.805; a uniform offset of 0.2 does the same (ratio 1.68, Dice 0).
  Any future bias degradation on Sod should be checked against this mechanism. Routed to
  an issue; the `shock_set_distance` card has since been corrected and the issue deleted.
- **Issue 104's prediction.** [Issue 104](../../issues/104-equivalence-test-misreads-a-flag-valued-anchor.md)
  predicted that a shock-mask overlap would, like `shock_set_distance`, be listed blind to
  `translate_x` because its no-feature value is a worst-case flag. Measured on the evidence run,
  it is not: the anchor scores 0 and a lost overlap also scores 0, so `translate_x` reaches damage
  1 from a two-cell shift. The problem is specific to a metric whose flag value lies far beyond
  its ordinary values. Issue 104 now carries a paragraph narrowing the prediction.
- **The Sod dataset page and sub-pixel shifts.** `translate_subpixel` is a Fourier phase shift,
  so it rings beside Sod's sharp shock, and any shock metric's sub-pixel readings on Sod mix the
  shift with this artefact. The record was written about `docs/datasets/sod_shock_tube.md` but
  routed to this card, where it now stands (card, Results, Displacement); the dataset page was not
  changed.
- **The narrowed idea page's tolerance attribution** was corrected in the review round; see
  Review round, critique on the boundary F-score tolerance.

## Review round

The reviewer raised 16 critiques; the builder reproduced each before answering it. Fourteen were
fixed, one was accepted in part, and one was outside the bundle and routed. Two were coding
defects (a field without its channel axis scoring 1, and a Sod test that accepted a wrong value);
they are in [code_notes.md](code_notes.md) under Bugs and fixes. The others:

- **The high-pass zeros were misread.** The card said the high-pass filters remove the shock.
  They keep the jump and raise the pressure level, so the ratio falls below the threshold;
  whether frame 0 scores 1 and frame 1 scores 0 at the mildest Butterworth strength is decided by
  ratios of 1.835 and 1.797, within 2% of the threshold, and `highpass_ideal`'s one usable
  strength gives a ratio of 1.40 with the jump intact. The builder reproduced it with the
  reviewer's script. Fixed: the Spectral filtering reading was rewritten (commit 82b10b7 on #30).
  The builder's error was inferring "shock removed" from a 0 without looking at the filtered
  field.
- **An additive pressure bias erases a perfectly placed shock** (an unstated limitation). Offsets
  of 0, 0.1 and 0.15 leave the score at 1; 0.2 drops the ratio from 3.03 to $0.503/0.3 = 1.68$
  and the score to 0. The repository's `bias` degradation is not on the Sod ladder, so the
  evidence never exercised this. Fixed: a Limitations bullet and a regression test.
- **"Two cells whatever the cell size" is false for cell-averaged data.** A finite-volume solver
  or the `block_mean` remap gives the cell holding the shock an intermediate value, which marks a
  shock as one, two or three cells. For Sod's ratio of 3.03, below $1.805^2$, at most two cells
  are marked; a ratio of at least 3.26 can mark three. The evidence shows both: 0.667 at half a
  cell is one marked cell, and 0.8 under `coarsen_bandlimited` is three. The reviewer found one
  marked cell in frames 4, 6 and 8 at a block factor of 16; the builder found two cells at block
  factors 2-32 at $t = 0.1$ and did not repeat those frames. Fixed: Reading the output now says
  one to three cells, with a test.
- **The Metrics Reloaded locators were wrong, and "full text" overstated what was read.** The
  card had placed "the DSC or IoU" and "community preference" in Suppl. Note 2.3; both are in the
  main-text Results. The summarising fetch tool had attached the supplement's section label to a
  main-text sentence before the supplement was reached, and the builder missed that its next
  fetch said the supplement was cut off. The builder re-fetched characters 200000-300000 of the
  arXiv HTML copy. Fixed: the card and `refs.bib` cite the main text for those two claims and
  Suppl. Note 2.3 for the DSC default and the worst-value rule; the source record was corrected to
  secondary. Lesson recorded: a summarising fetch can attach a section label to text from another
  section.
- **The median blur was omitted** from "every calibrated blur smears the shock". `median_blur` was
  a no-op on Sod at all three levels (value 1 in every frame) and was excluded as degenerate.
  Fixed: the Smoothing reading says both linear blurs remove the shock and the median blur leaves
  it unchanged.
- **The reason for "charges most for `coarsen_bandlimited`" was wrong.** Both coarsenings reach
  full damage; what separates them is the field change: `coarsen_bandlimited` has
  `field_change_max` 2.78e-4 and `damage_per_change` 3603, `coarsen` 5.30e-4 and 1889. Fixed in
  the Resolution loss reading.
- **The Displacement prose skipped the two grading sub-pixel levels** (0.667 at half a cell, 0.5
  at one cell) and the ringing that produces the first. Fixed; the PR body states that the
  pre-registered mechanism was wrong at half a cell.
- **"Spread over more than about four cells" is Sod-specific.** The cut-off is
  $2 \ln R / \ln 1.805$ cells: 3.8 for Sod's $R = 3.03$, 7.8 for $R = 10$. Fixed in Limitations.
- **A gauge pressure gets plausible-looking numbers.** On `taylor_green_2d` frame 0 (a zero-mean
  pressure, range $\pm 0.4998$) the detector flags 2860 of 65536 cells along the zero contours of
  a field with no shock, and the metric scores 0.113 against a three-cell roll, 1.0 against
  $0.9p$ and 0.0 against $-p$. Fixed: a Limitations bullet linking issue 101; the measurement was
  added to [issue 101](../../issues/101-a-metric-cannot-declare-it-needs-an-absolute-positive-field.md).
- **`scale_dependent: false` fails for a negative constant.** Multiplying both fields by $-1$
  empties both masks and scores 1. The builder's own check gave 1.0 against 0.5 for the step and
  its one-cell shift (the reviewer's 0.333 was a different pair). Accepted in part: the flag was
  kept false and the comment states the restriction (Method choices); the schema question went to
  [issue 122](../../issues/122-scale-dependent-does-not-say-which-constants.md). If the schema
  means any constant, both shock bundles should flip together.
- **The Dice 1945 sentence claimed more than its unopened title.** The card had said Dice
  introduced the coefficient "to measure how often two species occur together". Fixed: it now
  claims only the title. The zero-tolerance identity on the idea page was labelled a derivation.
- **Two corrections to other documents were not routed.** These are the half-cell count on
  `shock_set_distance`'s card and issue 104's prediction (Corrections to the rest of the
  repository). The builder did not edit them, because a bundle may not edit another (AGENTS.md
  §3.2); they went through the routing to issues 121 and 104.
- **The boundary F-score tolerance on the idea page: right number, wrong attribution.** The 0.75%
  figure came from a web-search summary, not a fetched page, and was described as "the benchmark
  convention", which MathWorks does not say; the Berkeley code's own default is 0.01. Fixed: the
  builder fetched both pages, and the narrowed idea page now gives both defaults with their
  sources and the one-to-one hint from the benchmark code.
- **The PR body linked a page the PR renames.** Fixed: the Idea line pins commit 16c08b1 and names
  the renamed page.

The reviewer also checked and found sound: the Dice arithmetic and the `triangle_inequality: false`
counterexample ($A = \{1\}$, $B = \{1,2\}$, $C = \{2\}$ gives $1 > 1/3 + 1/3$); every
hand-derived test literal; every number in the Results readings against `results.csv` and the
fingerprint, with the Spearman values recomputed from the tie patterns (0.707 for
$(0,1,1,1,1)$, 0.971 for $(0,0,1/3,1/2,1,1)$, 0.949 for $(0,0,x,y)$, 0.775 for $(0,1,1,1)$);
the process (the pre-registration commit carries the declaration verbatim, and the evidence run
started two seconds later from a clean tree); Taha and Hanbury's Table 1 and near-miss
quotation; and the fractions-skill-score algebra.

## Open questions and follow-ups

- **The both-empty convention**, 1 against Metrics Reloaded's 0, has no evidence row on Sod:
  [issue 120](../../issues/120-shock-mask-overlap-both-empty-convention.md), open.
- **The two readings on `shock_set_distance`'s card** (half-cell count, high-pass mechanism):
  routed to an issue; the card has since been corrected and the issue deleted.
- **Whether `scale_dependent` means a positive constant or any constant**:
  [issue 122](../../issues/122-scale-dependent-does-not-say-which-constants.md), open.
- **A metric cannot declare that it needs an absolute, positive field** (the Taylor-Green gauge
  pressure): evidence added to
  [issue 101](../../issues/101-a-metric-cannot-declare-it-needs-an-absolute-positive-field.md).
- **A fractions skill score of shock masks over neighbourhood width**, the generalisation that
  removes the near-miss saturation. For binary fields at $n = 0$ the fractions are the indicators
  and $o^2 = o$, so $\mathrm{FSS}(0) = 2\lvert A\cap B\rvert/(\lvert A\rvert+\lvert B\rvert)$,
  this bundle's Dice coefficient (the builder's algebra, checked by the reviewer; the paper does
  not name it):
  [proposals/MTR-shock_mask_overlap-fractions-skill-score.md](../../proposals/MTR-shock_mask_overlap-fractions-skill-score.md).
- **The boundary F-score with a sourced tolerance**, including whether a fraction of the domain
  diagonal means anything for a shock, and whether its matching is one-to-one:
  [docs/ideas/shock_geometry/shock_boundary_f_score.md](../../docs/ideas/shock_geometry/shock_boundary_f_score.md).
- **Many shocklets in two or three dimensions are untested**:
  [issue 002](../../issues/002-shocklet-dataset.md).
- No judgement file was written; the reserved judgement number was released unused.

## For the next agent

- The builder was least sure of the Dice choice over the Jaccard index, which is a preference
  since the two rank identically, and of the both-empty convention, which is the builder's own and
  untested by evidence.
- The formulas were read in Taha and Hanbury and in Metrics Reloaded through a fetch tool that
  quotes or summarises the page, not by paging the PDF; the equation numbers 6, 7 and 8 come from
  the PMC copy (confirmed there by the orchestrator). Metrics Reloaded's published version was not
  opened by the builder. Dice 1945, Jaccard 1912 and Martin et al. 2004 were not opened.
- The boundary F-score tolerance defaults come from MathWorks' documentation and the Berkeley
  code header only, never from Martin et al. 2004.
- The first things the builder would check: that nothing in `metrics/shock_set_distance` changed
  in #30; the half-cell reading against `shock_set_distance`'s card (now issue 121); and that the
  narrowed idea page still carries every reference and pitfall that is not on this card.
- Every sub-pixel reading of a shock metric on Sod mixes the shift with Fourier ringing; read
  such a value against the filtered field, not only against the score.
