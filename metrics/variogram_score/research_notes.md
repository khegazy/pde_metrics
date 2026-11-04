# Research notes: variogram_score

This bundle was built by the metric-building agent that built [energy_score](../energy_score/card.md),
in the same launch and the same pull request, #27. It was built on 2026-10-30, reworked in an
adversarial review round on 2026-10-30 (the work log heads it 2026-10-31), and merged on
2026-10-31. It came from the idea page `docs/ideas/distributional/multivariate_proper_scores.md`,
which that build narrowed and renamed to
[ensemble_calibration.md](../../docs/ideas/distributional/ensemble_calibration.md). What the two
bundles share is recorded once in [energy_score's research notes](../energy_score/research_notes.md):
the common sources (Scheuerer & Hamill 2015, Pacchiardi et al. 2024, Ferro 2014 and the rest), the
decision to build two bundles, the evidence ladder, how the idea page was narrowed, the
mildest-inflation dip, the profile-row fault (issue 111) and the review critiques about both
bundles. This file holds only what is specific to the variogram score, condensed from the work
log and records. The card is the source of truth for what the metric is, and where the two
disagree the card wins. The coding record is in [code_notes.md](code_notes.md).

## Summary

The bundle is the variogram score of order 0.5 with inverse-distance weights (Scheuerer & Hamill
2015, Eq. 3), estimated fairly from the ensemble, with a per-cell companion map (card,
Definition). The first round registered Scheuerer and Hamill's plug-in estimate and measured
distances in a straight line, never wrapping round a periodic axis. The review round showed that
the plug-in estimate rewards an overconfident ensemble at small ensemble sizes. It also showed
that unwrapped distances put a false dome in the map. The score now uses the fair kernel-score
estimate ([judgements/004](../../judgements/004-variogram-score-uses-the-fair-estimator.md)) and
the shorter distance round periodic axes. On `synthetic_ensemble` both spread axes follow with
rank correlation 1 and `bias` is measured as blind, as declared, before and after the rework. The
evidence cannot show that the score detects a wrong spatial correlation, because no experiment in
the repository changes one. The score costs $O(Md^2)$ for $d$ cells and $M$ members.

## Sources

The sources this bundle shares with energy_score, Scheuerer & Hamill 2015 above all, are in the
[energy_score table](../energy_score/research_notes.md#sources). Two sources are specific to this
bundle; both were found in the review round.

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| Allen, Ginsbourger & Ziegel 2023, SIAM/ASA Journal on Uncertainty Quantification 11(3), 906-940, DOI 10.1137/22M1532184 | Full text (the arXiv v1 HTML, arXiv:2202.12732, whose numbering may differ from the journal version) | Definition 1, Eq. 3; Sect. 4.1 (unnumbered) | The kernel score of a conditionally negative definite kernel, $S(P,y) = \mathbb{E}\rho(X,y) - \tfrac12\mathbb{E}\rho(X,X') - \tfrac12\rho(y,y)$ (Definition 1, Eq. 3). The variogram score is the kernel score of $\rho(x,x') = \sum_{ij} h_{ij}(\lvert x_i-x_j\rvert^p - \lvert x'_i-x'_j\rvert^p)^2$ (Sect. 4.1). This is what makes the fair estimate an unbiased estimate of the same score. The paper gives no ensemble estimator for the variogram score. | `metric.py`, card, `refs.bib`, judgement 004 |
| The `scoringrules` Python package (Zanetta & Allen), `scoringrules/core/variogram/_score.py`, function `vs_ensemble`, https://github.com/frazane/scoringrules | Full text (the source code, fetched after the reviewer pointed to it) | `vs_ensemble`, the `estimator='fair'` branch | The package implements `estimator='nrg'`, the plug-in of Scheuerer & Hamill Eq. 4 and its default, and `estimator='fair'`, which is $E_1 - \tfrac12 E_2$ with the pair term over the $M(M-1)$ distinct member pairs. That expands to $(\bar u - v)^2 - s^2/M$, the estimator this bundle now uses. The code cites no paper for it. | Judgement 004 |

The review narrowed the reading of Scheuerer & Hamill on the order $p$: $p = 0.5$ discriminates
best in their Sects. 3a, 3c and 3d, equally with $p = 1$ in 3b, and is the only order used in 3e
(Review round, below).

## Method choices

- **Order $p = 0.5$**, from Scheuerer & Hamill 2015, read as corrected in the review (card,
  Definition).
- **Weights $w_{ij} = 1/r_{ij}$**, from Scheuerer & Hamill Sect. 2 and 3e. The distance is in the
  grid's physical units, following their wind example, which uses km. That is the agent's own
  reading. The score therefore carries an inverse length.
- **Channels scored separately and summed.** This is the agent's own choice, from Scheuerer &
  Hamill's Sect. 2 remark that a score across variables of different type is doubtful.
- **Every ordered pair**, as Eq. 3 is written, with no neighbourhood cut-off. Scheuerer & Hamill
  reserve a cut-off for prior knowledge of the correlations (Sect. 3e).
- **The estimator.** The first round registered the plug-in estimate of Eq. 4, the published
  estimator, with its ensemble-size bias stated and tested rather than corrected. The agent then
  believed no source gave a fair variant. It wrote the fair form, which subtracts each pair's
  ensemble sample variance of $\lvert x_i - x_j\rvert^p$ divided by $M$ from the squared mismatch,
  as its own proposal. The review showed that the plug-in rewards overconfidence (Rejected
  formulations) and that the fair form is established (Review round). The fair form was
  therefore built, and recorded as
  [judgements/004](../../judgements/004-variogram-score-uses-the-fair-estimator.md) because it
  departs from the defining paper's Eq. 4. The options were to keep the published estimator and
  document that it rewards overconfidence at small $M$, or to use the unbiased kernel-score
  estimate. The fair estimate scores the same quantity (Allen et al. 2023, Sect. 4.1;
  Pacchiardi et al. 2024, App. C.1.2), `scoringrules` implements it, and it matches `crps` and
  `energy_score`. The proposal for it was deleted once it was built.
- **Distance on the domain's own geometry.** The first round never wrapped pairs, so that no
  periodic assumption was made; this was the agent's own choice. The review changed it to the
  shorter way round on periodic axes and the straight line inside the domain on bounded axes
  (Review round, the point about never wrapping). The new rule matches the repository's increment metrics and
  Pacchiardi et al.'s distance on the globe (App. E.4.1). The agent did not write a judgement
  record for it, because a published precedent exists.
- **The raw score is registered.** It grows as the number of cells to the power 3/2 at fixed
  spacing, and as the square of it when the same domain is refined (card, Reading the output).
- **`monotone_under_smoothing`.** The first round declared it False, because the contract blur
  ladder was not monotone (109, 97, 349, ...). The review showed that the dip was the plug-in bias
  itself. With the fair estimate the ladder reads 90.9, 91.7, 403.5, 1195.8, 2431.4, so the
  declaration returned to the default, True. With a noisy reference the plug-in ladder was already
  monotone (206.9, 226.6, 470.2, 1149.7, 2221.4), as the decorator comment then explained.
- **Pre-registration** (in commit d2464fb on #27, which added `metric.py`, before the evidence
  run). Declared as follows: `spread_deflate` +1 (narrowing shrinks the members' mean pairwise
  difference to the power one half below the reference's, so the squared mismatch of Eq. 3
  grows); `spread_inflate` +1 (widening raises it above the reference's). Blind: `bias`. Fields
  `*`, lower is better, units "field/length", reduction "sum". The pre-registration was not edited
  after the rework.

## Rejected formulations and negative results

- **The plug-in estimate of Scheuerer & Hamill's Eq. 4, inside Eq. 3.** Squaring the ensemble
  mean of $\lvert x_{ki} - x_{kj}\rvert^p$ adds $\mathrm{Var}_F(\lvert X_i - X_j\rvert^p)/M$ to
  every term in expectation. This follows from
  $\mathbb{E}(v - \bar u)^2 = (v - \mathbb{E}u)^2 + \mathrm{Var}(u)/M$; it is the agent's own
  derivation, which the reviewer re-derived. The extra term shrinks as the forecast's pairwise
  differences become less variable, so at a fixed small $M$ the plug-in score rewards
  underdispersion. That is consistent with Scheuerer & Hamill's observation (Sect. 3a) that the
  score improves with ensemble size, and with their remark (Sect. 2, p. 1324) that the ensemble
  approximation has "effects on the score's propriety". Pacchiardi et al. (2024, App. C.1.3) call
  this estimate unbiased; for the reason above it is not, and the card says so.
  - **Measured** with the reviewer's script, later re-run by the agent at $M = 2$ with identical
    output. The setup was a 12 by 12 field and 200 paired draws, with the members scaled about the
    true base so that the sample-mean effect described in energy_score's notes is excluded. A 20%
    narrower ensemble beat the calibrated one by $66.4 \pm 1.4$ at $M = 2$ and $21.5 \pm 1.2$ at
    $M = 4$, which is 49 and 18 standard errors. It lost by $12.3 \pm 1.1$ at $M = 16$. At
    $M = 2$ a 10% narrower ensemble won by $37.57 \pm 0.71$, and a 10% wider one lost by
    $46.87 \pm 0.75$.
  - **Measured across ensemble sizes.** The plug-in expectation is proportional to $(1 + 1/M)$ for
    an exchangeable reference. That predicts a ratio of 1.176 between $M = 4$ and $M = 16$,
    against $1138.7/971.0 = 1.173$ measured, a gap of about 12.6 standard errors (standard errors
    10.5 and 8.1).

  Rejected in favour of the fair estimate (judgement 004).
- **Straight-line distances on a periodic grid.** Unwrapped pairs give a central cell about twice
  the inverse-distance weight of a corner cell: $\int 1/r$ over the square is
  $2L\ln(1+\sqrt2) \approx 3.53L$ at the centre against $1.76L$ at a corner. On a spatially
  uniform calibrated ensemble the map was about 1.5 times larger at the centre. The reviewer
  measured a centre to corner ratio of 1.54 on a 32 by 32 grid with $M = 8$ and 20 draws. After the
  change the same draws gave 21.91 at the centre against 22.46 at the corner, a ratio of 0.975.
- **A neighbourhood cut-off** would change what the score sees, and it is not implemented (card,
  Limitations).

## Evidence runs

1. **First run**, `results/variogram_score_1793357351`, at commit d2464fb on #27 with a clean
   tree, four seconds after the commit. It used the plug-in estimate, on `synthetic_ensemble`
   frames 0-11 with `degradation=ensemble_miscalibration`, and produced 156 rows in 115.8 s. Both
   spread axes follow with $\rho = 1$, and `bias` is a blind axis with change 0, as declared. The
   harshest relative changes were 0.154 (deflation) and 1.90 (inflation). This run is superseded.
2. **Re-run after the review**, `results/variogram_score_1793396098`, at commit b88d490 on #27 with
   a clean tree, 156 rows in 234.1 s, run as `python evaluate.py metrics=[variogram_score]
   dataset=synthetic_ensemble degradation=ensemble_miscalibration paths.data_url=null`. Both spread
   axes still follow with $\rho = 1$ and `rho_frame_min` = 1 at direction +1, and `bias` is still
   blind, so the pre-registration is met as before. The harshest relative changes are now 0.216
   and 1.71. The mildest inflation now sits below clean, as energy_score's does and for the same
   reason (energy_score's notes, Evidence runs). The card cites this run.

## Corrections to the rest of the repository

The corrections found by this launch that touch other parts of the repository are in
[energy_score's notes](../energy_score/research_notes.md#corrections-to-the-rest-of-the-repository).
The one specific to this bundle concerns a shared contract test and is in
[code_notes.md](code_notes.md#tests) ([issues/113](../../issues/113-not-monotone-declaration-passes-on-round-off.md)).

## Review round

These are the critiques specific to this bundle, seven of the twelve. The critiques about
both bundles are in energy_score's notes. The critique on cost and on the map being computed
twice is in [code_notes.md](code_notes.md#performance). The code changes these critiques caused,
and their regression tests, are in code_notes.md under Bugs and fixes.

- **The plug-in rewards an underdispersed ensemble at small $M$** (theory). The card
  called the score proper and reported the bias only across ensemble sizes, not at a fixed size.
  The agent had derived the bias but had not stated its consequence at fixed $M$ on the card.
  **Fixed**, beyond documentation, by switching to the fair estimate (Method choices; numbers
  under Rejected formulations).
- **"A fair variant no source gives" was wrong** (citation). `scoringrules` implements
  the fair variogram score. The agent had read only the rendered documentation page, which lists
  the `estimator` option without its values. The reviewer found no peer-reviewed paper for the
  estimator, and suspected without verifying that Allen et al. treat the variogram score as a
  kernel score. The agent confirmed that Allen et al. do (Sect. 4.1). That makes the fair form the
  standard kernel-score U-statistic, although they give no ensemble estimator for it. **Fixed**:
  the PR body, the proposal and the records were corrected, and the estimator was built.
- **The map has a built-in dome** (documentation). This is the geometry artefact under
  Rejected formulations. **Fixed** by the change to periodic distances, below. The card now says that along a
  non-periodic axis cells near the edge have smaller weight sums, so a smaller map value there is
  partly geometry (card, Boundary handling and Reading the output).
- **Never wrapping on periodic grids** (theory; medium confidence). The repository's
  structure-function metrics (`increment_flatness`, `increment_w1`, `increment_w1_by_separation`)
  take increments with periodic wrap and declare `requires_periodic=True`. The first round's
  straight lines did the opposite on the same periodic data. Scheuerer & Hamill do not address
  periodic domains, so this had been an unrecorded choice of the agent's. **Fixed** (Method
  choices).
- **"$p = 0.5$ is best in every one of their experiments (Sections 3a to 3e)"** (citation). Section 3e compares no orders ("We restrict our attention to the VS-0.5"), and 3b
  rates 0.5 and 1 equally ("for p = 0.5 and p = 1 it discriminates well"). Only 3a, 3c and 3d
  support the claim. The builder's own source record had said 3a-3d, and the card had widened it.
  **Fixed** in the card, the comment on `ORDER`, the `refs.bib` note and the PR body.
- **The sign-flip blindness was missing** (documentation). Every term depends on
  $\lvert x_i - x_j\rvert$, so the mirrored members $c - x$ score the same as $x$. Pacchiardi et
  al. (2024, Sect. 3.2.1, below Eq. 11) state this invariance next to the shift invariance.
  **Fixed**: the Definition, Intuition and Limitations state it, and a test pins it.
- **The weight sum and the growth rate** (documentation). The card said that the
  weights per cell add up to "roughly the side length" and that the score grows as $N^{3/2}$. On
  the unwrapped first version the reviewer measured 186.4, which is 2.91 times the side at
  $n = 64$. The $N^{3/2}$ growth holds only at fixed spacing: refining the same domain gives $N^2$
  (ratios 8.59 and 7.97 per doubling at unit spacing, and 17.56 and 16.79 at spacing $1/n$). On the
  fixed, periodic metric the agent measured a weight sum of 221.7 per cell, 3.46 times the side;
  on a torus it tends to $4\ln(1+\sqrt2) \approx 3.53$ times the side. The ratios were 8.60 and
  8.05 at unit spacing and 17.21 and 16.10 at spacing $1/n$. **Fixed**: Reading the output gives
  the measured values.

The reviewer also checked and found sound: the displacement loop and the per-cell map against a
literal double sum on 1-D, 3-D, length-1-axis and single-cell grids with unequal spacing and two
channels (largest map difference $3.6\times10^{-15}$); the worked example (9, and the map
2.25/4.5/2.25, on the first version); the units (field per length) and the spacing factor of 0.5;
how the pipeline passes the context; and the Scheuerer & Hamill citations of Eq. 3 and 4, the
weights, the variable-type remark, and the cancellations in Sects. 3a and 3d.

## Open questions and follow-ups

- **Scores of the transformed difference vector.** Up to $1/d^2$, the variogram score is the mean
  squared error of the members' mean of the vector $g(y)_{ij} = w_{ij}^{1/p}\lvert y_i - y_j\rvert^p$.
  Applying the mean CRPS or the energy score to that vector instead gives other proper scores. All
  of them separate correct from wrong correlation models in Scheuerer & Hamill's Fig. 6 (Sect. 2
  end, Sect. 3f), so the transformation carries the sensitivity. The proposal is
  [MTR-energy_score-transformed-difference-scores](../../proposals/MTR-energy_score-transformed-difference-scores.md),
  corrected by the orchestrator after the review.
- **The estimator choice**: [judgements/004](../../judgements/004-variogram-score-uses-the-fair-estimator.md).
- **The cost guard and the duplicated map computation**:
  [issues/114](../../issues/114-cost-warning-ignores-grid-and-maps-are-computed-twice.md).
- **The round-off pass of a "not monotone" declaration**:
  [issues/113](../../issues/113-not-monotone-declaration-passes-on-round-off.md).
- **The profile row on ensemble axes**, shared with energy_score:
  [issues/111](../../issues/111-damage-per-change-divides-by-round-off-on-ensemble-axes.md).
- **Detecting a wrong spatial correlation** needs the experiment proposed in
  [EXP-energy_score-correlated-synthetic-ensemble](../../proposals/EXP-energy_score-correlated-synthetic-ensemble.md).

## For the next agent

- The builder was least sure of the choices that are its own, each of which changes the number:
  distance in physical units and channels scored separately and summed. The third such choice, not
  wrapping on a periodic grid, was reversed in the review.
- The builder's first check would be the displacement loop in `metric.py` against the double-sum
  test. The reviewer and the agent have both done it since, on wider grids (code_notes.md, Bugs
  and fixes).
- The fair estimate can fall slightly below zero on a single draw (card, Reading the output).
- Nothing in the evidence shows the score detecting a wrong correlation. Its main reason to exist,
  sensitivity to correlation structure, rests on Scheuerer & Hamill's simulations until the
  correlated synthetic ensemble exists.
