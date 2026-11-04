# Research notes: tail_index

This bundle was built by a metric-building agent from the idea page
[docs/ideas/distributional/tail_index_estimators.md](../../docs/ideas/distributional/tail_index_estimators.md)
(now narrowed to peaks-over-threshold fits) in pull request #23, worked on 2026-10-30 and merged
on 2026-10-31, with an adversarial review round on 2026-10-30. This file holds what the builder
and the reviewer read, tried and concluded that the card does not carry, condensed from their work
log and records. The card is the source of truth for what the metric is; where the two disagree,
the card wins. The coding record is in [code_notes.md](code_notes.md).

## Summary

The bundle reports the Hill estimate of the tail of the absolute one-cell increments at the fixed
order $k = \lceil\sqrt{n}\rceil$, with the Hill estimate at every $k = \lceil n^\theta\rceil$ as
its curve (card, Definition). The main conclusion is that on the kinet fields the value is not a
tail exponent and not an intermittency score: the largest increments are spatially clustered,
which lowers the value even for a true power-law tail, and on velocity the structure-free
Gaussian impostor scores above the intermittent reference. The declared rise under additive noise
held in direction on density and velocity, though not as a steady rise, and was contradicted on
vorticity, because the declaration was made from two frames that were not representative. What
the estimate means on fields that may have no power-law tail is the open question recorded in
judgement 002.

## Sources

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| Clauset, Shalizi & Newman 2009, *SIAM Review* 51(4), 661–703, doi:10.1137/070710111 | Full text (arXiv PDF 0706.1062v2, text extracted by a script) | Eq. (1.1); Eq. (3.1); Sect. 3.3, Eq. (3.9); Sect. 3.5; Sects. 4 and 5 | Eq. (3.1) is the continuous power-law maximum-likelihood estimator, which the paper calls equivalent to the Hill estimator; Eq. (1.1) defines $\alpha$ as the exponent of the density; Sect. 3.5 names the Hill plot and the rule of keeping the largest $\sqrt{n}$ or $n/10$ observations (attributed there to Farmer et al. 2004, *Quant. Finance* 4, 383); Sect. 3.3 and Eq. (3.9) choose $x_{\min}$ by minimising the Kolmogorov-Smirnov distance | Card (Definition, Reading the output), refs.bib, `metric.py` |
| Boucheron & Thomas 2015, *Electronic Journal of Statistics* 9(2), 2751–2792, doi:10.1214/15-EJS1088 | Full text (arXiv 1503.05077 on ar5iv) | Sect. 1 (the definition is unnumbered in the copy read); Sect. 2.3 | The Hill estimator $\hat\gamma(k) = (1/k)\sum_{i\le k}\ln(X_{(i)}/X_{(k+1)})$ with the sample sorted descending, and the statement that it converges to $\gamma$ for every intermediate sequence ($k\to\infty$, $k/n\to 0$) exactly when the tail is in the max-domain of attraction with $\gamma>0$ (crediting Mason 1982 and de Haan & Ferreira 2006); a Lepski-type rule for $k$; a mention of alternative Hill plots | Card (Definition), refs.bib, `metric.py`, tests |
| Hill 1975, *Ann. Stat.* 3(5), 1163–1174, doi:10.1214/aos/1176343247 | Abstract (Crossref record) | None | Inference about a tail from the conditional likelihood of the most extreme order statistics, singling out Zipf-type tails. The full text was not retrieved, so no equation number is cited and the formula is taken from Boucheron & Thomas | Card, refs.bib, `metric.py` |
| Granero-Belinchón & Cabeza Gallucci 2024, *Mach. Learn.: Sci. Technol.* 5(2), 025032, doi:10.1088/2632-2153/ad43b3 | Abstract | None | The idea page's only reference. It trains a GAN against the variance, skewness and flatness of increments and says nothing about tail indices; it is the reason the quantity whose tail is read is the increment | Card, refs.bib, idea page |
| Drees, de Haan & Resnick 2000, *Ann. Stat.* 28(1), 254–274, doi:10.1214/aos/1016120372 | Not opened (Project Euclid empty; Cornell eCommons technical report TR 1215 rate-limited, then served HTML) | None | The usual source for the alternative Hill plot, known only through Boucheron & Thomas Sect. 2.3 and the R package evmix's documentation | Not cited |
| Resnick & Stărică 1997, *Adv. Appl. Probab.* 29, 271–293 | Secondary (the evmix R documentation, read by the builder and the reviewer) | None | With Drees et al. 2000, attributed by evmix as the origin of the plot of the Hill estimate at $k=\lceil n^\theta\rceil$ against $\theta$, which is exactly this bundle's curve coordinate | Not cited; the card labels $\theta$ the bundle's choice |
| Dekkers, Einmahl & de Haan 1989, *Ann. Stat.* 17(4), 1833–1855, doi:10.1214/aos/1176347397 | Abstract | None | The moment estimator generalises Hill's estimator to the index of any extreme-value distribution, consistent and asymptotically normal | [proposals/MTR-tail_index-moment-estimator.md](../../proposals/MTR-tail_index-moment-estimator.md), judgement 002 |

The equation numbers of Clauset et al. are those of the arXiv PDF, which numbers equations by
section; the ar5iv HTML of the same paper numbers Eq. (1.1) as (1) and Eq. (3.1) as (9). The
orchestrator asked about this in a feedback round, and the builder confirmed from the extracted
PDF text that "(3.1)" is printed after the estimator and "(3.9)" after the Kolmogorov-Smirnov
distance.

## Method choices

- **Hill estimator, not a peaks-over-threshold fit.** The idea page names both. Hill's is a
  closed form (one sort), the page names it first, and it has a fixed published rule for $k$; a
  generalised Pareto fit needs an iterative optimiser and a threshold choice. The fit stays on
  the idea page. The agent's own reasoning.
- **$k=\lceil\sqrt{n}\rceil$, not $n/10$ nor a data-chosen $k$.** Clauset et al. (2009,
  Sect. 3.5) name both fixed rules. $\sqrt{n}$ satisfies the consistency condition of Boucheron &
  Thomas (2015, Sect. 1); $n/10$ does not. A data-chosen $k$ would read each variant at a
  different order, against the repository's rule of fixing thresholds once. The builder chose
  $\sqrt{n}$ for these reasons before seeing that $\theta = 0.5$ sits where the kinet fields score
  below iid Gaussian increments; that this choice sets the direction of the noise response is one
  reason the curve is stored.
- **Curve coordinate $\theta$, $k=\lceil n^\theta\rceil$, $\theta = 0.1$ to $0.9$.** Fixed across
  grids so the per-coordinate tables are comparable, with $\theta = 0.5$ exactly the registered
  $k$. The spacing is the agent's choice. After the review the coordinate is still labelled the
  bundle's own, because its defining sources (Resnick & Stărică 1997; Drees et al. 2000) could not
  be read.
- **Absolute increments with both signs pooled, a mean over (channel, axis) pairs, pairs with
  $X_{(k+1)} = 0$ left out, NaN when none remain.** All follow `increment_flatness`'s rules, by the
  agent's choice. The reason given for the per-pair mean was replaced in the review round by a
  measured one (see Review round).
- **Single-field arity, `higher_is_better=False`, all fields.** As `increment_flatness`: a
  single-field statistic whose drift from the reference is read.
- **No convention issue for the summary.** The registered number is the curve at a point a source
  names, so the convention issue reserved for a summary no source fixes was not needed.
- **Judgement 002.** Whether a Hill estimate belongs on fields whose increments may have no
  power-law tail is the one question the builder would have asked; it is recorded in
  [judgements/002-hill-estimator-without-a-power-law-tail.md](../../judgements/002-hill-estimator-without-a-power-law-tail.md).
  The choice it records, to build at the fixed order and not to read the value as an exponent,
  was kept after the review; its measurement paragraph was rewritten (see Review round).
- **Pre-registration** (commit 9a1ecfd on #23, before any full-ladder run): `additive_noise` with
  direction +1, because added Gaussian noise pulls the increment distribution toward a Gaussian,
  whose Hill estimate at $\lceil\sqrt{n}\rceil$ (0.095 on one 256 by 256 draw) lay above the
  reference's on every kinet field measured (frames 2000 and 5000: density 0.052 and 0.064,
  velocity 0.070 and 0.037, vorticity 0.082 and 0.092); blind to `translate_x`; all fields;
  `higher_is_better: false`; dimensionless; reduction mean.

## Rejected formulations and negative results

- **The $n/10$ rule** (Clauset et al. 2009, Sect. 3.5) fails the consistency condition
  $k/n \to 0$, and at $\theta = 0.8$ (about $n/10$) the exploration showed it reads the shoulder
  of the increment distribution, where it behaves like flatness.
- **The Kolmogorov-Smirnov threshold** (Clauset et al. 2009, Sect. 3.3 and Eq. (3.9)) chooses
  $k$ per sample, so the reference and every variant would be read at different orders. It is
  kept as [proposals/MTR-tail_index-ks-threshold.md](../../proposals/MTR-tail_index-ks-threshold.md).
- **Pooling every pair's increments into one estimate** was weighed in the review round. On kinet
  velocity a single pair supplies all $k$ largest values at frames 2000 and 8000 (shares 0, 1, 0,
  0 and 0, 0, 1, 0), and 76% and 24% from two pairs at frame 5000; pooled values were 0.0304,
  0.0513 and 0.1003 against per-pair means 0.0703, 0.037 and 0.0948. The per-pair mean was kept.
- **Changing the exact-zero rule** (weighting by increment size, a threshold relative to
  `ctx.fluctuation_rms`, or pooling) was not done: none has a source, each changes every
  anisotropic field's number, and the rule is shared with `increment_flatness`. It is
  [issues/103](../../issues/103-exact-zero-axis-rule-is-discontinuous.md).

## Evidence runs

1. **Exploration before the declaration** (a scratch script, not a run of `evaluate.py`, not
   kept): the Hill estimate at $k=n^\theta$ on kinet frames 2000 and 5000, clean, blurred
   ($\sigma$ 1 to 8 cells, wrap) and with Gaussian noise at 0.001 to 0.5 of the fluctuation rms,
   against one iid Gaussian draw. At $\theta = 0.5$ ($k = 256$ of 65536) the values were 0.052 and
   0.064 on density, 0.070 and 0.037 on velocity and 0.082 and 0.092 on vorticity, against 0.095
   for the Gaussian; at $\theta = 0.8$ they were 0.47 to 1.39 against the Gaussian's 0.22. Noise
   raised $\theta = 0.5$ toward the Gaussian value and lowered $\theta = 0.8$; blur moved
   $\theta = 0.5$ down on density and irregularly on velocity and vorticity. The builder first
   read this as "the far tail is lighter than a Gaussian's"; that reading was superseded in the
   review round (see Review round, clustering).
2. **Smoke run** `results/tail_index_1793349654`: `kinet_re5e4_dev` with `degradation=quick`,
   3000 rows. It ran; no conclusion was drawn from dev data.
3. **Evidence run** `results/tail_index_1793350342`: `python evaluate.py metrics=[tail_index]
   dataset=kinet_re5e4 dataset.time.start=2000 dataset.time.reduction=50 paths.data_url=null`,
   frames 2000 to 10000 (161 frames), 256 analysis grid, seed 20260807, at sha 59dce73 on #23,
   clean tree, 28497 rows. The fingerprint showed `additive_noise` direction +1 with
   rho_ci_lo 0.8 on density and velocity, as declared, and direction −1 with rho_ci_lo −0.8 on
   vorticity, against the declaration; `translate_x` blind on all three fields. Reading the
   per-level medians showed why: vorticity's clean median at $\theta = 0.5$ over 161 frames is
   0.131, above the noise-dominated value, whereas the two exploration frames had 0.082 and 0.092;
   at the harshest noise all three fields converge near 0.093 (density 0.0926, velocity 0.0927,
   vorticity 0.102). So the direction of the noise response is set by which side of the Gaussian
   value the reference sits on, and two frames were too few to declare it. The curve tables showed
   noise raising $\theta \le 0.4$ and lowering $\theta \ge 0.6$ on every field. The contradiction
   is reported on the card as the rules require, and the pre-registration was not edited.
4. **After the review round** the evidence was not re-run: the exact-integer orders equal the old
   $k$ at every $\theta$ on the 256 by 256 grid and no other fix touches finite fields, and the
   catalog rebuilt unchanged.

The card's Results now come from `results/comparison_1793657627`, the shared run pinned in #35
(card, Results).

## Corrections to the rest of the repository

- **`increment_flatness` silently drops a non-finite channel.** The builder found while fixing
  the same behaviour in this bundle that `increment_flatness` drops any (channel, axis) pair whose
  flatness is not finite, so one NaN or infinity in one channel returns the other channels' value
  without a warning, and a NaN in a one-channel field returns NaN, indistinguishable from a
  constant field. That bundle was outside this build and was not changed; the orchestrator
  reproduced it and wrote
  [issues/107](../../issues/107-increment-flatness-drops-a-non-finite-channel.md).
- **The exact-zero axis rule is shared with `increment_flatness`.** The round-off discontinuity
  found in this bundle applies to that bundle by the same rule (2.60 to 2.82 under a 1e-12
  perturbation); it is recorded in
  [issues/103](../../issues/103-exact-zero-axis-rule-is-discontinuous.md) for both.
- **The idea page's only reference concerns flatness, not tail indices**, so the primary sources
  for the estimator and its choice of $k$ had to be found. The idea page was narrowed to the tiers
  not built, keeping that reference and adding the two sources this bundle read; its row in
  `docs/ideas/README.md`, its build-next item and its bullet in
  `docs/ideas/distributional/README.md` were narrowed to match.
- **Later, from another bundle's review.** The adversarial review of `tail_exceedance` found that
  this card says Clauset et al. "name" the $\sqrt{n}$ rule without saying that they call it an
  alternative common in quantitative finance and prefer their Kolmogorov-Smirnov method. It was
  routed to an issue; the card has since been reworded and the issue deleted.

## Review round

The reviewer wrote 11 critiques; the builder re-measured each before answering. The four about
code are in [code_notes.md](code_notes.md) under Bugs and fixes.

- **"A heavier tail scores higher" runs against intermittency on this data** (documentation,
  fixed). Clean medians at $\theta = 0.5$ are density 0.0695, velocity 0.0542 and vorticity 0.131;
  an iid Gaussian 256 by 256 field scores 0.0916 ± 0.0054 over 8 draws; the Gaussian impostor
  scores 0.0500, 0.0807 and 0.0923, and on velocity it scores above the reference in 84.5% of
  frames (6.2% on density, 28% on vorticity), although `increment_flatness` rates the reference
  strongly intermittent (15.2, 9.23, 9.34) and the impostor not (2.86 to 3.00). The Intuition,
  Reading the output and trap-test reading were rewritten to say that a heavier tail scores higher
  only for independent power-law values, and that a higher value on these fields is not a more
  intermittent field. `test_a_heavier_tail_scores_higher` was kept, since it is true on independent
  fields.
- **Spatial clustering, not tail weight, explains the low values** (theory, fixed). Over eight
  seeds on 256 by 256, Gaussian blurs of $\sigma$ = 0, 0.5, 1, 2 and 4 cells take an iid
  Pareto($\alpha=1$) field from a mean of 1.015 to 0.994, 0.879, 0.741 and 0.532, and a
  Pareto($\alpha=2$) field from 0.535 to 0.302, while blurred iid Gaussian fields stay at 0.091 to
  0.096. On one seed the drop is smaller (1.005 to 0.766 at $\sigma = 4$). On kinet frames 2000,
  5000 and 8000, 87% to 100% of the top-256 cells of every pair have another top-256 cell among
  their 8 neighbours. So a value below iid Gaussian noise shows clustering or a light tail, not
  which. The card's Limitations and Noise reading, and judgement 002's measurement paragraph and
  its alternative (the moment estimator would not remove the clustering), were rewritten; the
  judgement's choice stands. The reviewer's statement that a finite linear combination of iid
  regularly varying variables keeps their index was made from memory; the builder did not check
  it and does not rely on it.
- **The noise response overshoots and turns back** (documentation, fixed). Medians at noise
  levels 1 to 4: density 0.0696, 0.0808, 0.0983, 0.0926; velocity 0.054, 0.0798, 0.0958, 0.0927;
  vorticity 0.1312, 0.1316, 0.1294, 0.1021. Level 3 exceeds level 4 in 86% of density frames and
  73% of velocity frames, which explains the rank correlation of exactly 0.8. The same overshoot
  holds at $\theta = 0.4$ on density (0.084 against 0.0779, Gaussian 0.0774). The builder corrected
  the reviewer on vorticity: there the direction is −1, so level 3 above level 4 is in order, and
  the 0.8 comes from the two mildest strengths, which leave the value above clean in about half the
  frames (0.503 and 0.528). The card now says the declared rise holds in direction on density and
  velocity but not as a steady rise. The pre-registration was not edited.
- **The Intuition described Equation (2) wrongly** (documentation, fixed). It compared each value
  with the next one down, which on the card's own sawtooth gives $\ln 3/4$, not $\ln 3$. The
  Intuition, the sawtooth sentence, the Definition and judgement 002's Choice paragraph now compare
  each kept value with one threshold.
- **The equivalence to Clauset et al. Eq. (3.1) used $\alpha$ in another sense** (citation,
  fixed). Clauset's $\alpha$ is the density exponent (their Eq. (1.1), confirmed in the PDF), so
  $\hat\alpha_C - 1 = 1/H(k)$ with the $k$ values above $x_{\min} = X_{(k+1)}$, and
  $(k+1)/(kH(k))$ if $x_{\min}$ itself is counted. The card's Definition and the refs.bib note now
  state the map. `card.yaml` and the catalog ("estimates 1/alpha", with the survival exponent)
  were correct and unchanged.
- **The $\theta$ coordinate is the published alternative Hill plot, and Boucheron & Thomas do not
  say $k$ is on a log scale** (citation, fixed in part). The card had said Boucheron & Thomas
  "read $k$ off" a log-scale plot; their Sect. 2.3 only mentions alternative Hill plots and their
  Figure 2 plots against $k$. The card and the refs.bib note were corrected. Attributing the
  coordinate to Resnick & Stărică or Drees et al. was not done, because neither paper was read and
  an R manual is a secondary source.
- **The reason for the per-pair mean was borrowed from flatness** (theory, fixed). Flatness
  averages per pair because a mixture of unequal-variance Gaussians is leptokurtic; the reviewer
  argued, as their own reasoning, that this does not carry over to a scale-invariant tail index.
  Within one frame the four velocity pairs read 0.071, 0.018, 0.121 and 0.070 (frame 2000) and
  0.154, 0.037, 0.033 and 0.155 (frame 8000). The builder kept the per-pair mean for the measured
  reason that pooling lets one pair supply all $k$ largest values (see Rejected formulations), and
  the card and docstring now say the mean mixes pairs whose estimates differ by a factor of 4 to 7.

The reviewer also checked and found sound: the citations of Boucheron & Thomas Sect. 1 and of
Clauset et al. Sect. 3.5; the reading that $\sqrt{n}$ satisfies the consistency condition and
$n/10$ does not; every Results reading against the tables and the run's CSV files at that time;
the order of the pre-registration commit before the evidence run (pre-registration 08:52:10Z,
run start 08:52:19Z); the frame values quoted in the pre-registration; and the narrowed idea page
and README edits.

## Open questions and follow-ups

- **Whether a Hill estimate at a fixed order is useful on fields with no power-law tail**:
  [judgements/002-hill-estimator-without-a-power-law-tail.md](../../judgements/002-hill-estimator-without-a-power-law-tail.md).
- **The moment estimator** of Dekkers, Einmahl & de Haan (1989), defined for any extreme-value
  index: [proposals/MTR-tail_index-moment-estimator.md](../../proposals/MTR-tail_index-moment-estimator.md).
  Its formula there is written from memory and flagged as unchecked.
- **A Hill estimate at every octave separation**, reusing `increment_flatness`'s increments and
  `increment_w1_by_separation`'s octaves, to read how the tail changes with scale:
  [proposals/MTR-tail_index-hill-by-separation.md](../../proposals/MTR-tail_index-hill-by-separation.md).
- **A degradation with a known tail index.** No enabled degradation moves the increment tail
  toward a known index; sparse spikes with Pareto($\alpha$) amplitudes would give a target of
  $1/\alpha$: [proposals/EXP-tail_index-pareto-spike-injection.md](../../proposals/EXP-tail_index-pareto-spike-injection.md).
- **The Kolmogorov-Smirnov threshold variant**:
  [proposals/MTR-tail_index-ks-threshold.md](../../proposals/MTR-tail_index-ks-threshold.md).
- **Attributing the $\theta$ coordinate.** Reading Resnick & Stărică (1997) or Drees, de Haan &
  Resnick (2000) would let the card attribute it. Not routed.
- **The exact-zero axis rule**:
  [issues/103](../../issues/103-exact-zero-axis-rule-is-discontinuous.md) (details in
  [code_notes.md](code_notes.md)).
- **The card's wording on Clauset et al. and $\sqrt{n}$**: since reworded on the card.

## For the next agent

- The builder was least sure whether a Hill estimate at one fixed order is useful on fields whose
  increments may have no power-law tail. Its direction under noise depends on the field and on
  $k$; under blur and low-pass filtering it falls at every order on density and velocity, which
  is its most usable behaviour.
- Not verified: Hill (1975) beyond its abstract; Drees, de Haan & Resnick (2000) and Resnick &
  Stărică (1997) not opened; the moment-estimator formula in the proposal; the reviewer's
  statement about linear combinations of regularly varying variables.
- The first checks the builder would make: that Sect. 3.5 of Clauset et al. really names "the
  largest $\sqrt{n}$ or $n/10$ observations" (it is on the page after the Hill-plot sentence in
  the arXiv v2 PDF, attributed to Farmer et al. 2004); every number in the card's Results against
  the generated tables and `fingerprint.json`; and the code checks listed in
  [code_notes.md](code_notes.md).
