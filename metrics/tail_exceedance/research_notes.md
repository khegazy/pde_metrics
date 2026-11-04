# Research notes: tail_exceedance

This bundle was built by a metric-building agent from the idea page
[docs/ideas/distributional/tail_index_estimators.md](../../docs/ideas/distributional/tail_index_estimators.md)
(now narrowed to peaks-over-threshold fits) in pull request #31, worked on 2026-10-31 and merged
on 2026-11-02, with an adversarial review round on 2026-10-31. This file holds what the builder
and the reviewer read, tried and concluded that the card does not carry, condensed from their work
log and records. The card is the source of truth for what the metric is; where the two disagree,
the card wins. The coding record is in [code_notes.md](code_notes.md).

## Summary

The bundle reports the frequency bias of extreme one-cell increments: the prediction's count of
absolute increments at least as large as the reference's $k$-th largest, over the reference's
count, at $k = \lceil\sqrt{n}\rceil$, with the same ratio at every order of `tail_index` as its
curve and a target of 1 (card, Definition). Only the exceedance tier of the idea page was built.
Every pre-registered direction was met when checked from the raw values: noise raises the value,
the three blurs lower it, and `translate_x` leaves it at exactly 1. The main caveat is saturation:
on density and velocity the registered point is 0 from the second blur strength and at every
low-pass strength, so it cannot grade those axes, and the analysis, which orders a target-valued
metric by $\lvert\log(\text{value}/\text{target})\rvert$, withholds or misreports several of its
statistics. Which point of the curve to register is a convention, open as issue 118.

## Sources

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| WWRP/WCRP Joint Working Group on Forecast Verification Research (JWGFVR), *Forecast verification: methods, issues and FAQ*, web page, https://jwgfvr.github.io/forecastverification | Full text of the cited section (the fetch covered the first 100,000 of the page's 141,777 characters, which hold it) | Section "Frequency bias (bias score)" (the page numbers no equations) | Frequency bias = (hits + false alarms)/(hits + misses), forecast over observed event frequency, range 0 to infinity, perfect 1, below 1 under-forecast and above 1 over-forecast; it measures only relative frequencies. A section on quantile-based categorical statistics says fixing the marginal totals by quantiles calibrates the problem | Card, refs.bib, `metric.py` |
| DTC/NCAR, *MET User's Guide* v9.1.2, Appendix C, https://metplus.readthedocs.io/projects/met/en/v9.1.2/Users_Guide/appendixC.html | Full text | Sect. 29.2.5 | The same definition, citing no source | Not cited; confirms the JWGFVR definition |
| ETCCDI, *Definitions of the 27 core indices*, web page, last updated 2009-09-15, https://etccdi.pacificclimate.org/list_27_indices.shtml | Full text | Items 10 (TN10p) and 13 (TX90p) | TX90p counts days above the calendar-day 90th percentile of a base period, with a bootstrap inside the base period (citing Zhang et al. 2005): an exceedance frequency against a percentile threshold set by a reference sample. The indices use a strict inequality | Card, refs.bib, `metric.py` |
| Zhang, Hegerl, Zwiers & Kenyon 2005, *J. Climate* 18(11), 1641–1651, doi:10.1175/JCLI3366.1 | Abstract (Crossref; the AMS site refused the fetch) | Abstract | Percentile indices jump at the base-period boundary because sampling error in the thresholds makes out-of-base exceedance rates differ from in-base ones (inflating them); a bootstrap removes it | Card, refs.bib, `metric.py`, judgement 005 |
| Ferro & Stephenson 2011, *Weather and Forecasting* 26(5), 699–713, doi:10.1175/WAF-D-10-05030.1 | Not opened (the Exeter repository and the AMS page refused) | None | The extremal dependence indices EDI and SEDI for rare binary events, described by search summaries as base-rate independent; they need hits paired cell by cell | Not cited; [proposals/MTR-tail_exceedance-paired-extreme-events.md](../../proposals/MTR-tail_exceedance-paired-extreme-events.md) |
| Stephenson, Casati, Ferro & Wilson 2008, *Meteorol. Appl.* 15(1), 41–50, doi:10.1002/met.53 | Not opened (the Wiley page refused) | None | The extreme dependency score paper, a candidate primary source for the frequency bias of rare events | Not cited |
| Clauset, Shalizi & Newman 2009, *SIAM Review* 51(4), 661–703, doi:10.1137/070710111 | Full text of the cited sections (the HTML of arXiv 0706.1062: the first 100,000 characters, Sects. 3.3 to 4; re-fetched as arxiv.org/html/0706.1062v2 in the review round) | Sect. 3.5; Sect. 4 | Sect. 3.5 calls keeping the largest $\sqrt{n}$ or $n/10$ observations "an alternative approach, quite common in the quantitative finance literature", attributed to its reference [17], and says the KS method of Sect. 3.3 gives estimates "at least as good while being simple to implement". Sect. 4 says the fitting tools do not tell whether a power law is plausible, which concerns a fitted tail parameter and stays on the idea page. Whether the HTML numbering matches the journal was not checked | Card, refs.bib, `metric.py` |
| Boucheron & Thomas 2015, *Electronic Journal of Statistics* 9(2), 2751–2792, doi:10.1214/15-EJS1088 | Secondary (through `tail_index`'s card and refs.bib) | Sect. 1 | The Hill estimator is consistent exactly when the tail has a positive index. This bundle estimates no tail parameter, so the reference stays on the narrowed idea page for the peaks-over-threshold tier and is not in this bundle's refs.bib | Idea page |
| Granero-Belinchón & Cabeza Gallucci 2024, *Mach. Learn.: Sci. Technol.* 5(2), 025032, doi:10.1088/2632-2153/ad43b3 | Abstract (Crossref) | Abstract | A GAN trained against the variance, skewness and flatness of increments; nothing about exceedance probabilities. Cited, as in `tail_index`, only as the reason the quantity read is the increment | Card, refs.bib |

The EUMETRAIN page on categorical verification was also read and agrees with the JWGFVR and MET
definitions. A WIREs paper's publisher page refused the fetch.

## Method choices

- **Only the exceedance tier.** The peaks-over-threshold tier would be a second bundle under a
  name not reserved for this build, and no ladder axis moves a fitted generalised Pareto shape in a
  known direction (`tail_index`'s noise declaration failed on vorticity for a related reason). The
  idea page was narrowed to that tier.
- **The comparison is the frequency bias, a ratio of counts with target 1**, rather than a
  difference of probabilities or a log ratio. Source: JWGFVR. The ratio is dimensionless with a
  fixed perfect value, and reporting it raw with `target=1.0` follows the repository's rule of
  reporting a metric in its standard form; the analysis orders it by $\lvert\log\rvert$.
- **The threshold is the reference's own $k$-th largest increment per pair**, not a multiple of the
  increment rms or of `ctx.fluctuation_rms`, which the brief had pointed at. Measured reasons are
  under Rejected formulations; the precedent is the ETCCDI percentile indices, and transferring that
  construction to increments is the agent's own. Recorded in
  [judgements/005-tail-exceedance-threshold-is-a-reference-percentile.md](../../judgements/005-tail-exceedance-threshold-is-a-reference-percentile.md),
  which also answers the old idea page's two open questions (the threshold and the comparison).
- **The $k$-th largest with $\ge$, not the $(k+1)$-th with $>$.** The agent's own derivation
  (card, Equation (5)): with $n$ independent reference values, $F(X_{(k)})$ is
  $\mathrm{Beta}(n-k+1, k)$, so an independent candidate from the same distribution has expected
  bias $n/(n+1)$; the other convention gives $n(k+1)/((n+1)k)$, about $(k+1)/k$, 1.25 at $k = 4$
  ($\theta = 0.1$ on 256 by 256). Zhang et al. (2005) describe the in-sample against out-of-sample
  effect for percentile indices, but they correct it with a bootstrap; the order-statistic choice
  is a different remedy, not theirs.
- **Registered $\theta = 1/2$**, the order `tail_index` reads. It is a convention with no source,
  [issues/118](../../issues/118-tail-exceedance-registered-threshold-is-a-convention.md). The builder
  kept it although the exploration showed it saturates under blur, because choosing $\theta$ from
  the exploration's dynamic range would be tuning a threshold to the data.
- **Counts summed over pairs before the ratio**, as a contingency table is summed; with no ties at
  the threshold this equals the mean of per-pair ratios. The agent's own.
- **Pairs with a zero reference threshold left out** and **non-finite input refused**, both as
  `tail_index` does (issues 103 and 107 are the lessons behind them).
- **Pre-registration** (in the message of commit d981914 on #31, before the evidence run):
  `additive_noise` +1 (noise spreads the increment bulk past the reference's $\sqrt{n}$-th largest;
  medians 0.994 to 1.003 at the mildest and 32.6 to 216 at the harshest strength on 9 exploration
  frames); `gaussian_blur`, `box_blur` and `median_blur` −1 (blur lowers the largest increments
  below the threshold; Gaussian 0.021 to 0.232 and box 0.045 to 0.266 at the first strength and 0
  thereafter, median 0.63 to 0.86, 0.12 to 0.30 and 0 to 0.23 at its three strengths); blind to
  `translate_x`; all fields; target 1.0; dimensionless; reduction mean. The low-pass axes were not
  declared, because the exploration showed them at 0 at every strength on density and velocity.

## Rejected formulations and negative results

- **A threshold in units of `ctx.fluctuation_rms`.** On kinet frames 2000, 6000 and 10000 the
  one-cell increment rms is 0.027 to 0.038 of the fluctuation rms on density and velocity and 0.16
  to 0.29 on vorticity, so such a threshold means a different event on each field.
- **A fixed multiple of the increment rms.** The reference's own rate of increments at least 3
  increment-rms in size is 0.0145 to 0.0315 across fields and frames (0.0027 for a Gaussian), so a
  fixed multiple is a different percentile everywhere. It is kept as a variant (Open questions).
- **The $(k+1)$-th largest with a strict inequality**, rejected by the derivation above.
- **Extremal dependence indices** (Ferro & Stephenson 2011) need hits paired cell by cell, which
  a position-blind count does not have; they could not be read and are a proposal.

## Evidence runs

1. **Exploration before the declaration** (a scratch script with the real ladder operators, not a
   run of `evaluate.py`, not kept), on 9 frames of `kinet_re5e4`, 2000 to 10000 every 1000, with
   calibration measured on those frames. At $\theta = 1/2$: the Gaussian and box blurs gave a
   median of 0.02 to 0.27 at their first strength and exactly 0 from the second on every field; both
   low-pass filters gave 0 at every strength on density and velocity; noise raised the value; the
   median blur lowered it; `coarsen` raised it far above 1 (medians 3.7 to 6.9 on density, 5.5 to
   10.3 on velocity, 4.8 falling to 0.63 on vorticity), because the staircase concentrates the
   change between blocks into one-cell jumps at block edges, which is not "more intermittency"; and
   the Gaussian impostor scored a median of 0 on density and velocity and 0.002 on vorticity,
   almost no increment as large as the reference's $\sqrt{n}$-th largest, where `tail_index` had
   scored the impostor above the reference on velocity. The saturation is issue 118's evidence.
2. **Smoke run** `results/tail_exceedance_1793494695`: `kinet_re5e4_dev`, `degradation=quick`. It
   ran and rendered; no physical reading was drawn.
3. **Evidence run** `results/tail_exceedance_1793494833`: `python evaluate.py
   metrics=[tail_exceedance] dataset=kinet_re5e4 dataset.time.start=2000
   dataset.time.reduction=50 paths.data_url=null`, frames 2000 to 10000 (161 frames), 256 grid,
   seed 20260807, at d981914 on #31 with a clean tree, 28497 rows. `additive_noise` was followed on
   every field (raw direction +1, rho 1, rho_ci_lo 1); `median_blur` had rho 1 on every field;
   `gaussian_blur` and `box_blur` fell to 0, with rho withheld on density and velocity and 0.949 on
   vorticity; `translate_x` was exactly 1 at every level and frame; the impostor's median value was 0
   (damage 1) on every field; `coarsen` raised the registered point by 5.44 and 9.3 times its clean
   value of 1 on density and velocity (a change from clean; the values are 6.44 and 10.3);
   `translate_subpixel` had rho −0.638 to −0.725, because fractional shifts move the count and
   whole-cell shifts return it to within 0.00195 of 1. The analysis reported every direction as +1
   and listed no blind axis, because of how it handles a target-valued metric (see
   [code_notes.md](code_notes.md), Bugs and fixes); the orchestrator therefore checked the
   declaration from the raw values and accepted it as met, including by hand the four (blur, field)
   entries whose ordering statistic the analysis withheld.
4. **After the review round** the evidence was not re-run: only documentation, comments, docstrings
   and test assertions changed.

The card's Results now come from `results/comparison_1793657627`, the shared run pinned in #35
(card, Results).

## Corrections to the rest of the repository

- **`tail_index`'s card overstates Clauset et al. on the $\sqrt{n}$ rule.** It says they "name" it
  as one of two fixed rules, which omits that they call it a common alternative and prefer their
  Kolmogorov-Smirnov method. This bundle's card was corrected; `tail_index`'s wording was left for
  its owner and routed to an issue; the `tail_index` card has since been reworded and the
  issue deleted.
- **The idea page** was narrowed to the peaks-over-threshold tier, with its row in
  `docs/ideas/README.md`, its build-next entry and its bullet and built list in
  `docs/ideas/distributional/README.md`. Granero-Belinchón & Cabeza Gallucci (2024) left the page
  with the flatness tier it was cited for; Boucheron & Thomas (2015) and Clauset et al. Sects. 4
  and 5 stay on it. The reviewer checked that every reference and pitfall of the old page was kept
  or carried.
- **Shared harness and test defects** found during this build (the analysis's handling of a
  target-valued metric, the name-keyed reference cache, the contract blur test accepting ties) are
  in [code_notes.md](code_notes.md), with the issues they went to.

## Review round

The reviewer wrote 16 critiques, edited no tracked file, and found no coding bug in the bundle or
the contract-test change. The fixes are in commit 9cf70cb on #31. Critiques on the spike test, the
analysis, the reference cache, the contract tests, the checker and the fingerprint size are in
[code_notes.md](code_notes.md).

- **The median blur does not take the value to 0 on vorticity** (documentation, fixed). The
  fingerprint gives a change from clean of −0.818 there (raw median 0.1816 at level 3, maximum
  0.8242, only 28% of frames at 0). The Smoothing reading, the Limitations and the PR outcome were
  corrected; the low-pass claim was checked against the raw values and stands.
- **`coarsen` was stated as a multiple of the clean value** (documentation, fixed): 5.44 and 9.3
  are changes from clean; the values are 6.44 and 10.3.
- **The vorticity rank correlation of 0.949 rests on a minority of frames and is fixed by ties**
  (documentation, fixed). It is defined only in frames with at least two nonzero levels, 39 of 161
  for `gaussian_blur`, 43 for `box_blur`, 9 for `lowpass_ideal` and 5 for `lowpass_butterworth`,
  and in each the oriented values are (finite, finite, inf, inf), whose Spearman correlation is
  0.9487 whatever the finite values. The Smoothing reading now says so; the frame counts are not in
  the generated tables, so the card gives the fact without them.
- **Equation (5)'s stated scope was wider than the derivation** (theory, fixed). The algebra was
  confirmed. The reviewer noted that the alternative is exactly $n(k+1)/((n+1)k)$ (1.4985 at $k = 2$,
  $n = 1024$), that Reading the output had dropped the assumption that the reference's values are
  independent, and that centred random-walk steps are exchangeable, not independent. The card,
  docstrings, judgement 005 and the twin test's docstring were corrected. The test separates the two
  conventions: 1.0150 ± 0.0516 for this one over 400 seeds, 1.5625 ± 0.064 for the alternative.
- **Citation precision** (citation, fixed). Clauset Sect. 3.5 mentions the $\sqrt{n}$ rule without
  recommending it; ETCCDI items 10 and 13 use a strict inequality, so the non-strict one is this
  bundle's choice; Zhang et al. describe inflation of out-of-base rates and a bootstrap remedy, so
  "describe the same effect" does not support the order-statistic remedy (the reviewer was
  medium-confident here, having seen only the abstract). The card, docstrings and refs.bib now say
  each.
- **"Read in full" overstated how two web sources were read** (records, fixed). The JWGFVR and
  ar5iv fetches returned at most the first 100,000 characters (of 141,777 and 155,538); the cited
  sections are inside them, and the claim that the ar5iv numbering matches the journal was the fetch
  tool's, unchecked. The refs.bib notes and findings now say the fetch was partial.
- **The pre-registration was measured on a subset of the evidence frames** (process, disclosed).
  The 9 exploration frames are among the 161 evidence frames, with the same seed and operators, so
  the declared numbers are in-sample. The brief forbids only a full-ladder `evaluate.py` run before
  the declaration, and the commit preceded the run (01:00:21Z against 01:00:31Z). The PR body says
  so.
- **Saturation was stated less plainly than the data show** (documentation, fixed). On density and
  velocity the Gaussian and box blurs are 0 from the second strength in every frame, the Gaussian
  blur is already 0 at the first strength in 49% of velocity frames, and both low-pass filters are 0
  at every strength. Issue 118 had also said the low-pass filters are graded again from
  $\theta = 0.6$ or 0.7, but the companion tables show them graded only at 0.8 and 0.9, and not
  consistently. Limitations and issue 118 were corrected.

The reviewer also checked and found sound: every other Results number against the tables and raw
data at that time; the worked example and the bound $n/k = 256$; that on real kinet frames 2000,
6000 and 10000 there are no ties at any threshold and every threshold is positive; the source
quotations from JWGFVR and ETCCDI; and the narrowed idea page.

## Open questions and follow-ups

- **Which point of the curve to register**, or a summary of the whole curve:
  [issues/118](../../issues/118-tail-exceedance-registered-threshold-is-a-convention.md). One
  candidate is the mean over $\theta$ of $\lvert\log B(\theta)\rvert$ with a floor for a zero count,
  the floor being a second convention:
  [proposals/MTR-tail_exceedance-curve-summary.md](../../proposals/MTR-tail_exceedance-curve-summary.md).
- **A threshold at a multiple of the reference's increment rms**, the idea page's example, whose
  reference event rate is itself an intermittency diagnostic:
  [proposals/MTR-tail_exceedance-sigma-threshold.md](../../proposals/MTR-tail_exceedance-sigma-threshold.md).
- **Paired extreme events**: pairing the events cell by cell gives a contingency table a rare-event
  score such as the (symmetric) extremal dependence index summarises, the position-sensitive
  companion of this position-blind ratio; Ferro & Stephenson (2011) could not be opened, so no
  formula is given:
  [proposals/MTR-tail_exceedance-paired-extreme-events.md](../../proposals/MTR-tail_exceedance-paired-extreme-events.md).
- **Two existing proposals would test this metric directly**: spike injection
  ([proposals/EXP-tail_index-pareto-spike-injection.md](../../proposals/EXP-tail_index-pareto-spike-injection.md))
  should raise the value above 1 with the spike fraction, and a tail-only degradation
  ([proposals/EXP-energy_distance-tail-only-degradation.md](../../proposals/EXP-energy_distance-tail-only-degradation.md))
  should lower it with a known answer when the damped quantile is at or below the $\sqrt{n}$-th
  largest. No new document was written.
- **The analysis could not read a target-valued metric** (direction, damage, blindness and a
  zero); fixed in the shared harness, details in [code_notes.md](code_notes.md).

## For the next agent

- The builder was least sure whether the analysis's withholding of the blur axes should be read as
  a defect of the analysis or as the honest consequence of the metric saturating. The analysis
  part was a defect and is fixed (a value of 0 is now the finite furthest point from the target),
  but the saturation itself is real (issue 118).
- Not verified: Ferro & Stephenson (2011) and Stephenson et al. (2008) could not be opened; the
  frequency bias is cited from the JWGFVR web page, not a paper; Zhang et al. (2005) only through
  its abstract.
- Equation (5) is the builder's derivation and assumes independent reference values; the one-cell
  increments of a real field are not independent, which is why its unit test uses a periodic random
  walk.
