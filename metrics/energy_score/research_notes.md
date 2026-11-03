# Research notes: energy_score

This bundle was built by a metric-building agent from the idea page
`docs/ideas/distributional/multivariate_proper_scores.md`, which the same build narrowed and
renamed to [ensemble_calibration.md](../../docs/ideas/distributional/ensemble_calibration.md).
The work is pull request #27, built on 2026-10-30 and merged on 2026-10-31. An adversarial review
round followed on 2026-10-30 (the work log heads it 2026-10-31), and a fix for a docs-build
failure in CI came on 2026-10-31. The same launch also built
[variogram_score](../variogram_score/card.md). What the two bundles share (the common sources,
the choices and the problems common to both, and the review critiques about both) is recorded
here once; [variogram_score's notes](../variogram_score/research_notes.md) hold only what is
specific to it. This file holds what the builder and the reviewer read, tried and concluded that
the card does not carry, condensed from their work log and records. The card is the source of
truth for what the metric is, and where the two disagree the card wins. The coding record is in
[code_notes.md](code_notes.md).

## Summary

The bundle is the fair ensemble energy score of a whole field. Its index is $\beta = 1$, and it
treats every channel of every cell as one vector (card, Definition). It reduces exactly to `crps`
on one cell. On `synthetic_ensemble` all three declared axes (`spread_deflate`, `spread_inflate`,
`bias`) followed with rank correlation 1 in every frame. The main conclusion from that run is
that the estimator computes what it claims. The run cannot show that the score sees spatial
correlation, because the synthetic ensemble's noise is independent from cell to cell. The review
round found no wrong number in the code. It corrected two card claims: that the score is fair
"at any ensemble size", which holds only from two members, and that a move without a move in the
mean CRPS must come from covariation, which is false. It also found a shared-analysis fault that
makes the generated profile row meaningless on the ensemble axes (issue 111).

## Sources

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| Gneiting & Raftery 2007, Journal of the American Statistical Association 102(477), 359-378, DOI 10.1198/016214506000001437 | Full text (the published JASA PDF on the authors' site, text extracted from the PDF streams, equation numbers visible) | Sect. 4.2 Eq. 20-21; Sect. 4.3 Eq. 22-24 | The energy score, Eq. 22. It is positively oriented there and strictly proper for $\beta \in (0,2)$ by Székely (2003) Theorem 1. At $\beta = 1$ and one dimension it reduces to the CRPS kernel form, Eq. 21. At $\beta = 2$ it degenerates to the negative squared error of the mean (Eq. 23) and is only proper. The orchestrator checked Eq. 22 in the agent's copy. | `metric.py`, card, `refs.bib` |
| Gneiting & Raftery 2007, same paper | Full text | Sect. 6.2 Eq. 43; Sect. 8 Eq. 58, Fig. 4 | The negatively oriented interval score for a central $(1-\alpha)$ prediction interval (Eq. 43). It is proper, rewards narrow intervals and penalises misses. Sect. 8 reports it beside empirical coverage as a function of the inflation factor. It is the score that goes with the interval-coverage item left on the narrowed idea page. | The narrowed idea page |
| Scheuerer & Hamill 2015, Monthly Weather Review 143(4), 1321-1334, DOI 10.1175/MWR-D-14-00269.1 | Full text (NOAA repository PDF, text extracted from the PDF streams) | Sect. 2 Eq. 2-4; Sect. 3a, 3b, 3e; Sect. 4 Table 1 | The variogram score of order $p$ (Eq. 3) and its ensemble approximation (Eq. 4). Weights proportional to inverse distance are a pragmatic ad hoc choice (Sect. 2) and a good compromise without prior knowledge of the correlations (Sect. 3e). The score is proper but not strictly proper, and it is blind to a bias common to all components (Sect. 2). The energy score hardly separates forecasts that differ only in correlation (Sect. 3b, citing Pinson & Tastu 2013). The review narrowed which sections support $p = 0.5$ (see variogram_score's notes). | Both bundles' cards and `refs.bib`; `variogram_score/metric.py` |
| Pacchiardi, Adewoyin, Dueben & Dutta 2024, Journal of Machine Learning Research 25(45), 1-64, https://jmlr.org/papers/v25/23-0038.html | Full text (the JMLR PDF, text extracted from the PDF streams; the arXiv PDF did not extract) | App. B.2.1 Eq. 33; App. C.1.1; Sect. 3.2.1 Eq. 11; App. C.1.3 | The energy score as $2\mathbb{E}\lVert X-y\rVert^\beta - \mathbb{E}\lVert X-X'\rVert^\beta$ (Eq. 33), which is twice Gneiting and Raftery's form with the sign reversed. Its unbiased ensemble estimate, unnumbered, in App. C.1.1, is the citation for the fair estimator. App. C.1.3 calls the plug-in variogram estimate unbiased, which it is not (variogram_score's notes). The review added Sect. 3.2.1 (the sign-flip invariance), App. C.1.2 (the unbiased kernel-score estimate) and App. E.4.1 (distance on the globe) for variogram_score. | Both bundles' `metric.py`, cards and `refs.bib` |
| Ferro 2014, Quarterly Journal of the Royal Meteorological Society 140(683), 1917-1923, DOI 10.1002/qj.2270 | Full text (the author's early-view copy with a 2013 header, so page numbers are not those of the issue) | Sect. 2.1 Definition 1; Sect. 2.3 Eq. 4-5 | The definition of a fair score for random-sample ensembles (Definition 1). Fair scores for continuous outcomes come from integrating fair binary scores over thresholds (Eq. 5), which recovers the adjusted CRPS of Ferro et al. (2008). The paper treats only univariate outcomes and gives no fair energy score. The reviewer noted that Definition 1 is not restricted to one dimension, so "fair in Ferro's sense" applies to the energy score at two or more members. | Card, `refs.bib` |
| Pinson & Tastu 2013, Discrimination ability of the energy score, DTU Informatics technical report 2013-15 | Secondary (through Scheuerer & Hamill Sect. 1 and 3b) | none | The finding that the energy score can hardly discriminate multivariate forecasts that differ only in correlation. Not opened (no free copy). The cards cite the pitfall through Scheuerer & Hamill, who reproduce it in their Fig. 2. | Not cited |
| Gneiting, Stanberry, Grimit, Held & Johnson 2008, TEST 17(2), 211-235, DOI 10.1007/s11749-008-0114-x | Not opened (described by the scoringRules documentation and arXiv 1202.3956) | none | The ensemble energy score in its plug-in form, and the multivariate rank histogram (minimum spanning tree and multivariate ranks), a calibration check for whole fields that the narrowed idea page could take up. No free copy was found. | Not cited |

The sources specific to `variogram_score` (Allen, Ginsbourger & Ziegel 2023 and the
`scoringrules` package) are in [its notes](../variogram_score/research_notes.md).

## Method choices

- **Fair estimator, not the plug-in.** The plug-in estimate, which divides the pair sum by $2M^2$,
  is biased by ensemble size and favours underdispersion. The fair form is unbiased (Pacchiardi
  et al. 2024, App. C.1.1) and equals `metrics/crps` on one cell, which keeps the two scores
  consistent. Sources: Pacchiardi 2024 and Ferro 2014. The review limited "unbiased" to
  ensembles of two or more members (Review round).
- **Index $\beta = 1$, fixed.** At this value the score is the CRPS in one dimension (Gneiting &
  Raftery 2007, Sect. 4.3), and Scheuerer & Hamill use it too.
- **The whole field, all channels, as one vector.** This is the natural norm of a vector field.
  It is the agent's own routine choice.
- **The raw score is registered.** The raw score grows with $\sqrt{d}$ for $d$ values, and the
  agent chose not to divide by $\sqrt{d}$. The literature reports the raw score, and no source
  fixes a normalisation. This is the agent's own choice, stated on the card (Reading the output).
- **No companion.** A norm has no per-cell decomposition. A per-member distance list would be a
  point-set companion, a kind the harness does not have.
- **Two bundles, not one.** The energy score is the idea page's first item. The variogram score is
  the score the literature recommends for the correlation structure the energy score misses. It
  has published defaults and an exact blindness (bias) that the ensemble ladder can test. It
  became its own bundle because it is a different score with a different number. The reliability
  diagram, interval coverage and the distribution of spectra stay on the idea page, because no
  bundle name was reserved for them.
- **Evidence ladder.** The axes that change an ensemble's spread (`spread_inflate`,
  `spread_deflate`) and the `bias` axis exist only in
  `configs/degradation/ensemble_miscalibration.yaml`, not in `default.yaml`. So the evidence run
  used `degradation=ensemble_miscalibration`, as the four earlier ensemble cards did.
- **Pre-registration** (in the commit that added `metric.py`, 394c34c on #27, before the evidence
  run). Declared as follows: `spread_deflate` +1 (by strict propriety, a narrowed ensemble scores
  worse in expectation); `spread_inflate` +1 (by the same propriety; the agent noted that scaling
  about the sample mean puts the expected minimum slightly above the calibrated width at 16
  members); `bias` +1 (a uniform offset raises the distance term and leaves the pair term
  unchanged). Blind: none. Fields `*`, lower is better, units "field", reduction "mean".
- **No judgement record.** In the first round the agent found no question that lacked a
  standard answer. The one judgement of this launch,
  [judgements/004](../../judgements/004-variogram-score-uses-the-fair-estimator.md), belongs to
  variogram_score.
- **Renaming the idea page.** The agent renamed the page rather than keep a file named after built
  scores, so that the filename says what remains. This is the agent's own choice.

## Rejected formulations and negative results

- **A negative fair score.** The agent first wrote on the card that the fair energy score can be
  negative. A brute-force search over small integer ensembles found no negative value, and the
  triangle inequality, summed over ordered member pairs, proves a floor of zero. The score reaches
  zero for imperfect ensembles whose reference lies on the segment between every pair of members,
  for example members $-1, 0, 1$ against $0$, or two members either side of the truth. So with few
  members the floor does not single out the perfect forecast. The card, `card.yaml` and the tests
  were corrected before the first commit (card, Definition and Reading the output).
- **The Dawid-Sebastiani score** (Scheuerer & Hamill 2015, Sect. 1 and 3a-3d, Figs. 1-4) is
  $\log\det\Sigma_F + (y-\mu_F)^\top\Sigma_F^{-1}(y-\mu_F)$, which needs the ensemble covariance
  and its inverse. With an ensemble small relative to the dimension, the sampling error makes it
  rank an overdispersed ensemble above a calibrated one at 20 members. For fields of thousands of
  cells and tens of members it is unusable, so it was neither built nor proposed.

## Evidence runs

1. **Smoke run** `results/energy_score_1793356567`, on `synthetic_ensemble` with
   `degradation=quick`. No smoke run on `kinet_re5e4_dev` would have been useful, because an
   ensemble metric is skipped on a dataset without members. The clean mean was 6.82, against the
   agent's closed form of 6.79. The reviewer confirmed that the `quick` ladder has no ensemble
   axes, so this run could not have informed the declaration.
2. **Evidence run** `results/energy_score_1793356825`, run as `python evaluate.py
   metrics=[energy_score] dataset=synthetic_ensemble degradation=ensemble_miscalibration
   paths.data_url=null`. It covered frames 0-11 (12 frames) on the 64 analysis grid, at commit
   394c34c on #27 with a clean tree, four seconds after the commit, and produced 156 rows in 0.7 s.
   - All three declared axes follow with $\rho = 1$ in every frame and direction +1, so the
     declaration is met with no contradiction.
   - The clean median, 6.85, agrees with the closed form for exchangeable Gaussian members,
     $\sigma\,\Gamma((d+1)/2)/\Gamma(d/2) = 6.79$ at $\sigma = 0.15$ and $d = 4096$, within the
     frame scatter. The reviewer measured the clean mean as $6.821 \pm 0.021$ (standard error
     over 12 frames) against 6.788.
   - **The mildest inflation sits below clean.** Its median energy score is 6.831, against 6.851
     clean, in 12 of 12 frames; the rank correlation stays 1 because the ordering is of
     departures from clean. The agent derived the cause before the run (the reviewer confirmed it
     in the transcript at 10:35 UTC, before the 10:40 run). `spread_inflate` and `spread_deflate`
     scale the members about their sample mean, which carries error variance $\sigma^2/M$. For
     exchangeable Gaussian members the expected fair CRPS or energy score is then proportional to
     $\sqrt{1 + 1/M + a^2(1 - 1/M)} - a/\sqrt{2}$ for spread factor $a$. That is minimised at
     $a^2 = M(M+1)/((M-1)(M-2))$, which is $a = 1.138$ at $M = 16$, not $a = 1$. The reviewer
     re-derived it. The predicted relative changes, $-0.17\%$, $+5.5\%$ and $+66.8\%$ at
     $a = 1.25$, 1.75 and 4, agree with the measured medians, $-0.29\%$, $+5.1\%$ and $+65.5\%$.
     The card states the reading (card, Results, Ensemble dispersion).
   - **The dataset cannot test correlation.** The synthetic ensemble draws independent noise in
     every cell for the reference and for every member. On its dispersion axes the energy score
     and the mean CRPS therefore depend on the spread factor in the same way up to a constant: the
     relative changes at the harshest strengths are 0.284 and 0.655 for energy_score, against
     0.282 and 0.655 on the crps card. The reviewer showed this is exact in expectation for
     isotropic Gaussian noise. The run validates the estimator and cannot show that it sees
     correlation structure. The experiment that would is the EXP proposal under Open questions.
   - On `bias` the harshest relative change is 2.08, against 2.53 for `crps` (from each bundle's
     fingerprint).
3. energy_score's numbers did not change in the review round, so its evidence was not re-run. The
   card still cites `results/energy_score_1793356825`.

## Corrections to the rest of the repository

- **The idea page, narrowed and renamed.** `multivariate_proper_scores.md` became
  [ensemble_calibration.md](../../docs/ideas/distributional/ensemble_calibration.md), which keeps
  the reliability diagram, interval coverage and the distribution of spectra. Its references went
  as follows: Gneiting & Raftery 2007 to `metrics/energy_score/refs.bib` and the narrowed page;
  Scheuerer & Hamill 2015 to both new bundles' `refs.bib`. Its pitfalls went as follows:
  - "the energy score is weak on correlation" went to energy_score's card, Limitations;
  - "the variogram score is blind to a common constant, pair it with crps" went to
    variogram_score's card (Definition, Intuition and Limitations) and to a test;
  - "$N^2$ terms and declared weights" went to variogram_score's card, Definition and
    Limitations;
  - "needs an ensemble" went to both cards' Reading the output and to the narrowed page.

  The orchestrator confirmed this against the narrowed page. The overview row in
  `docs/ideas/README.md` and the theme page were updated. Links in `docs/ideas/background.md` and
  `docs/ideas/evaluation_design.md` were missed and broke the docs build; see code_notes.md, Bugs
  and fixes.
- **The crps card overclaims at one member.** `metrics/crps/card.md` says that comparisons across
  ensemble sizes are meaningful because the fair estimator is used. That fails at one member. The
  pair term is dropped, so for a calibrated forecast the expected score is twice its value at two
  or more members, and the one-member score is not proper. Ferro (2014, Sect. 2.1, after
  Definition 1) states that the only fair scores for one-member ensembles are trivial. Measured
  for energy_score, whose one-cell case is crps, on $N(0, I)$ in four dimensions: the mean is
  $2.6634 \pm 0.0068$ at $M = 1$, against 1.3338 at $M = 2$ and 1.3272 at $M = 8$. The crps card
  was not edited, being another bundle. The orchestrator wrote this up as
  [issues/112](../../issues/112-crps-card-overclaims-comparison-at-one-member.md) and reproduced
  it.

## Review round

The reviewer raised twelve critiques across the two bundles and found no wrong number from the
code as written. The ones about energy_score, or about both bundles, are here. Seven concern
variogram_score only (the plug-in estimator, the fair variant, the map's dome, periodic distances,
the order $p$, the sign flip and the growth rate) and are in
[its notes](../variogram_score/research_notes.md); the one on cost and duplicated map computation is in
[variogram_score's code notes](../variogram_score/code_notes.md). No critique was a code bug in
energy_score.

- **Not fair at one member** (theory). The card and docstring said the score is
  unbiased and fair "at any ensemble size", and a test was named that way but ran only at $M = 2$
  and 8. At $M = 1$ the pair term is dropped, so the expectation is $\mathbb{E}\lVert X-y\rVert$.
  That is about twice ES($F$), and it is not proper, since it is minimised by a point mass at the
  spatial median. The reviewer measured, on $N(0, I)$ in four dimensions with 20 000 cases against
  the target $\Gamma(5/2) = 1.3293$, means of $2.6634 \pm 0.0068$, $1.3338 \pm 0.0054$ and
  $1.3272 \pm 0.0038$ at $M = 1$, 2 and 8. The agent confirmed that 2.6634 equals
  $2\Gamma(5/2) = 2.6587$ within error. **Fixed** in commit b88d490 on #27: the card and docstring
  say "from two members", state the factor of two and the loss of propriety, and cite Ferro. The
  test was renamed and a one-member test added. No number changed. The same overclaim on the crps
  card became issue 112 (Corrections, above).
- **The CRPS comparison** (documentation). The card said that when the energy score
  moves and the mean CRPS does not, the change is in how the members vary together. That is
  false: the two weigh the same per-cell errors differently, a Euclidean norm across cells
  against a mean of absolute values. The reviewer's counterexample uses three identical members
  against the reference $(0, 0)$. Members at $(1, 1)$ give a mean CRPS of 1 and an energy score of
  1.414; members at $(2, 0)$ give a mean CRPS of 1 and an energy score of 2. **Fixed** in b88d490:
  the card states the correct reason with this example (card, Reading the output), and a test
  pins the literals. The separate Results claim, that on this dataset the two scores depend on the
  spread factor in the same way, was confirmed and kept.
- **The profile row divides by round-off** (likely future bug in shared code). On the
  dispersion axes the ensemble mean is preserved, so `field_change_max` is round-off ($10^{-32}$
  to $10^{-31}$). `fmeval/analysis.py` divides by it, guarded only by a test that it is positive,
  so `damage_per_change` is about $10^{30}$. The profile's selectivity and its "charges most for"
  and "charges least for" entries are then set by which round-off is smaller, on every ensemble
  card (energy_score, variogram_score, crps, rank_histogram). For example, energy_score's
  `spread_deflate` has `field_change_max` $1.39\times10^{-32}$ and `damage_per_change`
  $9.74\times10^{30}$. The energy card's table said it charges least for `bias`, the axis with
  its largest relative change (2.08). The variogram card's table said it charges most for
  `spread_deflate`, while its prose said inflation costs far more. **Not fixed in the branch**,
  because the code is shared. It was written up as
  [issues/111](../../issues/111-damage-per-change-divides-by-round-off-on-ensemble-axes.md)
  (commit b88d490), and both cards' Results now say the profile ranking is not meaningful on these
  axes and link the issue.
- **The work log was stale** (minor). The work log still called the self-check
  problem unresolved after the orchestrator had fixed it. **Fixed**: the work log was updated.

The reviewer also checked and found sound, for energy_score: the reshape of members and
reference; the pair sum as half of Pacchiardi et al.'s App. C.1.1 estimator (which uses
$\lVert\cdot\rVert_2^\beta$, so halving is right); the worked example (3 against 2 for crps); the
floor of zero; $M = 1$ returning the L2 distance; the closed form, re-derived; the pre-registration
in its commit; both evidence runs at matching commits with a clean tree; and the work log's
numbers against the result tables. Both bundle test suites and the contract tests gave 39 passed
and 16 skipped, and the card checker gave 0 errors for both bundles.

## Open questions and follow-ups

- **An experiment that changes spatial correlation.** No existing experiment changes an
  ensemble's spatial correlation (Evidence runs). The proposal is
  [EXP-energy_score-correlated-synthetic-ensemble](../../proposals/EXP-energy_score-correlated-synthetic-ensemble.md).
- **The patched energy score.** It sums the energy score over overlapping patches (Pacchiardi et
  al. 2024, App. B.2.3 Eq. 35). It is proper but not strictly so, and it becomes strictly proper
  when the whole-field energy score is added (Sect. 3.2.2-3.2.3, Lemma 4). Pacchiardi et al. used
  it with patches of 8 and 16 points as a training loss for a generative WeatherBench model
  (App. C.1.4, E.4.2). The proposal is
  [MTR-energy_score-patched-energy-score](../../proposals/MTR-energy_score-patched-energy-score.md).
- **The profile row on ensemble axes**: [issues/111](../../issues/111-damage-per-change-divides-by-round-off-on-ensemble-axes.md).
- **The crps card at one member**: [issues/112](../../issues/112-crps-card-overclaims-comparison-at-one-member.md).
- **The multivariate rank histogram** (Gneiting et al. 2008, not opened) is a whole-field
  calibration check the narrowed idea page could take up. It was not routed beyond the
  archive, because the routing rule puts only sources read in full text onto a page.

## For the next agent

- The builder was least sure whether citing Pacchiardi et al. 2024 for the fair energy-score
  estimator is acceptable. It is the only primary source found that writes the unbiased
  U-statistic form for the energy score (App. C.1.1, unnumbered, for twice the score); Ferro 2014
  does not treat the multivariate case. The reviewer read the passage and confirmed the factor of
  one half.
- Pinson & Tastu 2013 and Gneiting et al. 2008 were never opened.
- The first things the builder would check: the evidence fingerprints' directions against the
  pre-registration, and the derivation of the minimum at $a^2 = M(M+1)/((M-1)(M-2))$, on which
  the card's reading of the mildest inflation rests. The reviewer has since checked both.
- The run shows nothing about spatial correlation. Until the correlated synthetic ensemble exists,
  the card's Limitations (weak on correlation, after Scheuerer & Hamill Sect. 3b) rests on the
  literature alone.
