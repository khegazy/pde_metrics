# Research notes: energy_distance

This bundle was built by a metric-building agent from the idea page
`docs/ideas/distributional/energy_distance.md` (since deleted, because the idea is built) in pull
request #24, worked on 2026-10-30 and merged on 2026-10-31, with an adversarial review round on
2026-10-30 and 2026-10-31. This file holds what the builder and the reviewer read, tried and
concluded that the card does not carry, condensed from their work log and records. The card is
the source of truth for what the metric is; where the two disagree, the card wins. The coding
record is in [code_notes.md](code_notes.md).

## Summary

The bundle reports the energy distance, in its square-root form, between the one-cell increment
distributions of the reference and the prediction, averaged over channels and axes, so that it
reads exactly the samples `increment_w1` transports (card, Definition). Every pre-registered
direction held on every field, with `translate_x` blind as declared. The review round corrected
the builder's central quantitative claim: the energy distance suppresses a change confined to the
tails relative to `increment_w1`, but it also suppresses small broad changes, so the honest
statement is a ratio against an equal-cost broad change, about 9% to 3% in the registered number
on a 256 by 256 axis with a Gaussian bulk, not "a few parts in a hundred thousand". Why the
spectrum-matched impostor fools the metric on velocity but not on vorticity is unexplained.

## Sources

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| Székely & Rizzo 2013, *J. Stat. Plann. Inference* 143(8), 1249–1272, doi:10.1016/j.jspi.2013.03.018 | Full text (the authors' copy on pages.stat.wisc.edu, which shows the journal's equation numbers) | Definition 1, Eq. (2.4); the unnumbered display before Eq. (2.3); the text after Eq. (2.7); Eq. (6.1); Sect. 1; Proposition 2, Eqs. (5.1)–(5.2) | The squared form $2E\lvert X-Y\rvert - E\lvert X-X'\rvert - E\lvert Y-Y'\rvert$, called the energy distance there; on the line it is twice the integral of $(F-G)^2$; its square root is a metric; the two-sample V-statistic with $1/n^2$ normalisation; the authors use V-statistics throughout because they are nonnegative; the exponent generalises to $\alpha \in (0,2)$ | Card, refs.bib, `metric.py`, tests |
| Rizzo & Székely 2016, *WIREs Comput. Stat.* 8(1), 27–38, doi:10.1002/wics.1375 | Full text (a copy on pages.stat.wisc.edu) | p. 27 (no equation numbers in that passage); "Testing for equal distributions", p. 28 | The energy distance $D$ is the square root of $D^2$ and satisfies all metric axioms; on the line $D^2$ is twice Cramér's distance; the E-statistic is a V-statistic; the equivalence with Cramér's distance holds only on the line (p. 28) | Card, refs.bib, `metric.py`, the (Q, R) idea page |
| Gretton, Borgwardt, Rasch, Schölkopf & Smola 2012, *J. Mach. Learn. Res.* 13, 723–773, https://jmlr.org/papers/v13/gretton12a.html | Full text (JMLR PDF) | Definition 2, Eq. (1); Lemma 6; Eqs. (3) and (5) | The maximum mean discrepancy (MMD) as an integral probability metric; its squared population form (the deleted idea page's Eq. (1) is Lemma 6); the unbiased U-statistic estimate, which can be negative (Eq. (3)); the biased V-statistic estimate (Eq. (5)). The paper does not mention the energy distance | Card, refs.bib, `metric.py` |
| Sejdinovic, Sriperumbudur, Gretton & Fukumizu 2013, *Ann. Statist.* 41(5), 2263–2291, doi:10.1214/13-AOS1140 | Full text (arXiv 1207.6076v3) | Eq. (2.3); Definition 13, Eq. (4.1); Example 15, Eq. (4.2); Theorem 22; Eq. (7.1) | The squared-form energy distance is twice the squared MMD for a kernel generating the distance (Theorem 22); the distance-induced kernel $(\lvert z\rvert+\lvert z'\rvert-\lvert z-z'\rvert)/2$ has no bandwidth (Eq. (4.2)); the V-statistic (Eq. (7.1)); other members of the family $\lvert x-y\rvert^q$ can give more powerful tests than $q=1$ | Card, refs.bib, `metric.py` |
| Müller 1997, *Adv. Appl. Probab.* 29(2), 429–443, doi:10.2307/1428011 | Abstract (Crossref) | None | The definition of an integral probability metric | Card (definition only, no equation number), refs.bib |
| SciPy documentation and source of `scipy.stats.energy_distance` (version 1.18.0 installed), https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.energy_distance.html | Full text (docstring and source in the installed package) | Notes; `scipy.stats._stats_py._cdf_distance` | Returns the square-root form, $\sqrt{2}$ times the root of the integrated squared CDF gap, computed exactly; the Notes say only the square root satisfies the metric axioms. The algorithm is in the source, not the Notes | `metric.py`, card, refs.bib |
| Bellemare, Danihelka, Dabney, Mohamed, Lakshminarayanan, Hoyer & Munos 2017, arXiv:1705.10743, doi:10.48550/arXiv.1705.10743 | Abstract | None | A divergence used for learning should have unbiased sample gradients; the Wasserstein metric lacks this and the Cramér distance (half the squared one-dimensional energy distance) has it | Not cited on the card; [proposals/MTR-energy_distance-cramer-loss.md](../../proposals/MTR-energy_distance-cramer-loss.md) |

The reviewer confirmed from its own download that arXiv 1207.6076v3 is the IMS electronic reprint
of the Annals article, differing only in pagination and typographic detail, so the equation and
theorem numbers cited from it are the journal's. The reviewer also re-read every equation number
cited from Székely & Rizzo (2013), Rizzo & Székely (2016) and Gretton et al. (2012) in its own
downloads and found them correct.

## Method choices

- **The feature compared is the one-cell increment**, the samples of `increment_w1`, averaged
  over channel and axis the same way. The options were the one-point distribution of field
  values, gradients, or increments at several separations. One-cell increments make the
  comparison with `increment_w1` exact (same samples, different distance), which is what the
  idea page's rationale asks for. The agent's own choice, following the idea page's pitfall about
  interpretable features. Issue 047 (signed fields in transport) does not arise, because
  increments are compared as one-dimensional samples, not as measures; issue 095 (pooling frames)
  does not arise, because one frame holds 65536 increments per axis.
- **The registered number is the square root $D$, not the squared form.** The literature uses
  the name for two numbers: Székely & Rizzo (2013) and Sejdinovic et al. (2013) give it to the
  squared form, Rizzo & Székely (2016) and SciPy to the square root. The builder first wrote the
  metric with the squared form and switched before committing, because the square root is the
  later, consolidated definition by the same authors, is what SciPy returns, satisfies the
  triangle inequality, and equals $\sqrt{2}$ times the MMD of the idea page. The cost is units of
  the square root of the field, so raw values cannot be compared with `increment_w1` (card,
  Reading the output). This was treated as an implementation choice under the rules (which of the
  literature's summaries to register), so no judgement file was written.
- **V-statistic, not U-statistic** (Székely & Rizzo 2013, Sect. 1); see Rejected formulations.
- **Exponent 1, no bandwidth.** Székely & Rizzo (2013, Proposition 2) allow any exponent in
  $(0, 2)$, which still characterises equality of distributions below 2 and reduces to a
  comparison of means at 2; it is the only free parameter, the analogue of the bandwidth the idea
  page warned about. Definition 1 fixes it at 1, and Sejdinovic et al. (2013, Eq. (4.2)) show the
  induced kernel has no bandwidth.
- **No convention issue for the summary.** The registered number is not a summary of a curve, and
  the mean over (channel, axis) is the rule `increment_w1` uses, with the same reason.
- **No companion.** The gap between the two cumulative functions has a coordinate in field units
  that moves from frame to frame, so it is not a curve at fixed coordinates (card, Reading the
  output).
- **How the deleted idea page's three pitfalls were carried.** Weakness on heavy tails went into
  the card's Definition (a derivation pinned by a test) and Limitations; the fixed and declared
  kernel into the Definition, with Sejdinovic Eq. (4.2) and Székely & Rizzo Proposition 2; the
  warning that one number hides which physics failed into the choice of increments as the feature.
  Both of the page's references (Gretton 2012, Müller 1997) are in refs.bib and cited. The page's
  contrast with f-divergences was not carried, since it concerns metrics this bundle does not
  implement and `docs/ideas/evaluation_design.md` already states it.
- **Pre-registration** (in the message of commit 4dbecc3 on #24, before the evidence run):
  direction +1 on `gaussian_blur`, `box_blur`, `median_blur`, `lowpass_ideal`,
  `lowpass_butterworth`, `coarsen`, `coarsen_bandlimited` and `additive_noise`, each because the
  degradation narrows or widens the one-cell increment distribution further at each larger
  strength (for `coarsen`, a growing fraction $(f-1)/f$ of increments become exact zeros); blind
  to `translate_x`; fields density, velocity and vorticity; `higher_is_better: false`; units
  `field^(1/2)`. The high-pass filters and `translate_subpixel` were left out because neither
  changes the increment distribution in a direction the builder could state in advance. The
  declaration lists the evaluated fields while the decorator accepts every field; the
  orchestrator accepted this, since the decorator did not change after the declaration.

## Rejected formulations and negative results

- **The unbiased U-statistic** (Gretton et al. 2012, Eq. (3), diagonal pairs excluded). For two
  identical samples it equals $2S(1/n^2 - 1/(n(n-1))) < 0$, where $S$ is the off-diagonal sum, so
  it fails the repository's rule that a distance is zero on identical fields and can be negative,
  which a square root cannot take. Unbiasedness also has no meaning here, because the increments
  of one frame are the whole population compared, not a random sample. The V-statistic
  (Székely & Rizzo 2013, Eq. (6.1); Gretton et al. 2012, Eq. (5)) is used.
- **The squared form as the registered number** was written first and replaced (see Method
  choices).
- **The first tail statement** ("a factor of order $1/N$ less than `increment_w1` ... a few parts
  in a hundred thousand") was withdrawn in the review round (see Review round).
- **The first explanation of the velocity impostor score** was removed, not replaced, because no
  test in the run separates the candidate causes (see Review round).

## Evidence runs

1. **Smoke run** `results/energy_distance_1793349238`: `kinet_re5e4_dev`, `degradation=quick`,
   3000 rows. Values were finite, zero at identity, exactly zero on the uncorrelated (large integer
   translation) probe, and rose under blur. Not evidence.
2. **Evidence run** `results/energy_distance_1793350409`: `python evaluate.py
   metrics=[energy_distance] dataset=kinet_re5e4 dataset.time.start=2000
   dataset.time.reduction=50 paths.data_url=null`, frames 2000 to 10000 every 50 (161 frames),
   256 analysis grid, seed 20260807, 59 severity levels, 28497 rows, at sha 4dbecc34 on #24 with
   a clean tree. The reviewer confirmed the run started 5 s after the pre-registration commit.
   All 24 declared (degradation, field) entries had direction +1 and rho_ci_lo 1, and
   `translate_x` was blind on all three fields, so the declaration held in full. Not declared
   but measured: `coarsen_bandlimited` on density is also listed as provably small (largest
   damage 0.0487, upper bound below the 0.05 margin) while perfectly ordered; the two statements
   are compatible and the declaration was left as it was. The impostor scored damage 0.613,
   0.289 and 0.871 on density, velocity and vorticity, so velocity is largely fooled. The
   comparison with `increment_w1` was not in this one-metric run, and the two cross-metric
   subsections of the card were removed for that reason.
3. **After the review round** the evidence was not re-run: only a docstring, the cost
   declaration and prose changed, so no number the metric computes changed.

The card's Results now come from `results/comparison_1793657627`, the shared run pinned in #35
(card, Results).

## Corrections to the rest of the repository

- **The deleted idea page said the energy distance "is in fact the maximum mean discrepancy with
  a particular kernel".** Precisely, the squared form equals twice the squared MMD for a kernel
  generating $\lvert x-y\rvert$ (Sejdinovic et al. 2013, Theorem 22), so the square-root form is
  $\sqrt{2}$ times the MMD; the card states the factor. The page's reference to Müller (1997)
  also omitted the issue number, 29(2); refs.bib carries it.
- **Links to the deleted page** in `docs/ideas/background.md`, `docs/ideas/evaluation_design.md`,
  `docs/ideas/optimal_transport/sinkhorn.md` and `docs/ideas/turbulence_statistics/qr_invariants.md`
  were repointed at the built metric; the idea's row in `docs/ideas/README.md` and its bullet in
  `docs/ideas/distributional/README.md` were removed.
- **The (Q, R) idea page.** The repointed link at first offered this one-dimensional increment
  metric for comparing two-dimensional joint densities (a review critique). The sentence in
  [qr_invariants.md](../../docs/ideas/turbulence_statistics/qr_invariants.md) now names the energy
  distance as a concept and says the built bundle is the one-dimensional case, which does not
  apply to (Q, R) as it stands, because its exact evaluation uses the one-dimensional identity,
  which does not extend to higher dimensions (Rizzo & Székely 2016, p. 28). A two-dimensional
  energy distance needs the all-pairs V-statistic, of order $N^2$ on 65536 cells per frame, or a
  subsample. The orchestrator also routed this as a labelled Pitfalls bullet on that page, with
  Rizzo & Székely 2016 added to its references. The builder's first record gave the page as
  p. 27; the review corrected it to p. 28. The other three repointed links were checked and
  promise no multidimensional comparison.

## Review round

The reviewer wrote 8 critiques (two theory or citation, one documentation, five minor) and found
no bug in the computation; the builder confirmed all eight by re-running the reviewer's scripts or
its own, and fixed all eight in commit aa900f8 on #24. The one cost critique is in
[code_notes.md](code_notes.md) under Performance.

- **The tail-suppression factor was wrong** (theory, fixed). The card had compared $D$, in the
  square root of field units, with `increment_w1`'s $W_1$, in field units; applied the squared
  form's $2/N$ result to the registered root; and treated a broad change as unsuppressed. On the
  x-increments of a 256 by 256 Student-t(4) field, with a broad change (every increment scaled by
  $1+\epsilon$) and a tail change (the two most extreme atoms pushed out) of exactly equal $W_1$,
  the reviewer measured $D^2/W_1 = 3.05\times10^{-5} = 2/N$ for the tail change, confirming that
  half, but $D$ charging the tail change 0.102 of the broad change at $\epsilon = 0.01$ and 0.0328
  at $\epsilon = 0.1$ ($D^2$: 0.0103 and 0.00108). The builder derived, as its own work, that a
  stretch by $1+\epsilon$ gives $D^2 \approx 2\epsilon^2\int x^2 f^2\,dx$ against
  $W_1 = \epsilon E\lvert X\rvert$, so for a Gaussian $D^2/W_1 = \epsilon/(2\sqrt2)$, and the tail
  change at equal transport cost costs $4\sqrt2/(N\epsilon)$ of the broad change in $D^2$ and the
  square root of that in $D$. Measured on $N = 1024$ Gaussian quantiles at $\epsilon = 0.05$:
  $D^2/W_1 = 0.01731$ against 0.01768 predicted, and a ratio of 0.1128 against 0.1105, with
  agreement within 7% at $N$ = 512, 1024 and 4096 and $\epsilon$ = 0.02, 0.05 and 0.1. The card's
  Definition, Intuition ("counts in full" removed) and Limitations, the first tail test's
  docstring and the EXP proposal were corrected (card, Definition, "How it differs from the
  transport distance"). The regression test is described in [code_notes.md](code_notes.md).
- **The explanations of the impostor's low damage on velocity were contradicted by the
  repository's own flatness evidence** (theory, fixed). The card had said the impostor lacks the
  reference's heavy-tailed increments, or that velocity's increments may be closer to Gaussian.
  But `increment_flatness`'s fingerprint (run `comparison_1793302178`) gives the reference's
  one-cell increment flatness as 15.2, 9.23 and 9.34 on density, velocity and vorticity, and the
  impostor's as 2.86 to 3.00 (the builder read at most 3.69, 3.22 and 3.13), and the impostor keeps
  the increment variance because it keeps the amplitude spectrum. Weak tail weighting is common to
  all fields, and velocity and vorticity have the same flatness, so neither explains a threefold
  gap. The explanation was removed; the card now says the run does not show why, without typing
  numbers from another card. The reviewer's candidate causes are listed under Open questions.
- **The (Q, R) link** (documentation, fixed); see Corrections.
- **A numerical check was misreported** (process, fixed where editable). SciPy's squared value
  matched the all-pairs V-statistic to 2.7e-16 absolute, 1.9e-14 relative, but the records said
  "2e-16 relative". Fixed in the findings, the work log and the PR body; the message of the pushed
  commit 4dbecc3 keeps the wrong figure, because it was not rewritten (no force-push), and the PR
  body says so.
- **"Strength 2.14 of 4" mislabelled a calibrated cutoff wavenumber** (minor, fixed). 2.14 is the
  calibrated cutoff `k_energy_90` for velocity in
  `results/energy_distance_1793350409/data/calibration.csv`, the third of four levels (configured
  severities 0.45, 0.70, 0.90 and 0.97; on velocity levels 1 and 2 both resolve to a cutoff of 1.0
  and level 4 to 4.02). The trap-test reading now names the level by its cutoff.
- **Rank invariance between the two forms holds per term, not for the mean** (minor, fixed).
  Squaring is monotone for one (channel, axis) term, but a mean of square roots is not a monotone
  function of a mean of squares: per-axis squared distances (1, 0) and (0.3, 0.3) average 0.5
  against 0.548 in roots and 0.5 against 0.3 in squares. The reviewer conjectured, without
  measuring, that on this ladder the axes move together and the practical effect is nil. Reading
  the output and the records now state the caveat.
- **Two loose attributions** (minor, fixed). The Noise reading said the anchor's distance is set
  "only by the spread"; the reviewer showed $D^2$ to a point mass at zero equals
  $2E\lvert X\rvert - E\lvert X-X'\rvert$ (0.66330176461135 both ways), which depends on the
  whole distribution, and the reading now says the anchor's distance is fixed by the reference's
  increment distribution while noise widens it without bound. The docstring and refs.bib had cited
  SciPy's Notes for the algorithm, which is in the source and is sorts and binary searches rather
  than "one merge"; the card, docstring and refs.bib now attribute each to its place.

The reviewer also checked and found sound: the MMD factor ($D/\mathrm{MMD}_b = 1.41421356237310$
numerically); every cited equation number; that Székely & Rizzo (2013) was fetched and read
although absent from the fetch log; the pre-registration text and the order of commit and run; all
Results prose numbers and qualitative claims against the tables and fingerprint at that time; the
worked example; and the carry-over of the idea page's references and pitfalls, with no stale link
to the deleted page left.

## Open questions and follow-ups

- **Why the impostor scores damage 0.289 on velocity against 0.871 on vorticity.** Not tail weight,
  on the flatness evidence. Untested candidates: the skewness or bulk shape of the increment
  distribution, the two-channel average on velocity, or how the anchor's distance scales the
  damage. A per-channel and per-axis breakdown of the impostor's distance would settle it. Not
  routed to an issue.
- **A joint run with `increment_w1`**, the point of building this metric, was named in the PR as
  the natural follow-up.
- **A tail-only degradation** (quantile-thresholded local smoothing of the most intense
  increments), since no enabled degradation changes the tails of the increment distribution
  without its bulk: [proposals/EXP-energy_distance-tail-only-degradation.md](../../proposals/EXP-energy_distance-tail-only-degradation.md),
  corrected in the review round and marked "see also" with
  [proposals/EXP-tail_index-pareto-spike-injection.md](../../proposals/EXP-tail_index-pareto-spike-injection.md).
- **An energy distance at every octave separation**, the averaging counterpart of
  `increment_w1_by_separation`; its registered summary would be another convention:
  [proposals/MTR-energy_distance-by-separation.md](../../proposals/MTR-energy_distance-by-separation.md).
- **Another exponent $\alpha$**, which Sejdinovic et al. report can give more powerful tests; only
  $\alpha = 1$ has the one-dimensional cumulative form evaluated by a sort, so another would cost
  order $N^2$ or an approximation:
  [proposals/MTR-energy_distance-alpha-exponent.md](../../proposals/MTR-energy_distance-alpha-exponent.md).
- **The Cramér distance as a training loss**, whose sample gradients are unbiased where the
  Wasserstein metric's are not (Bellemare et al. 2017, abstract):
  [proposals/MTR-energy_distance-cramer-loss.md](../../proposals/MTR-energy_distance-cramer-loss.md).
- **A faster evaluation that sorts the reference once per frame**: see
  [code_notes.md](code_notes.md), Performance. Not routed.

## For the next agent

- The builder was least sure of the choice of the square-root form, which changes the damage and
  elasticity numbers relative to the squared form.
- Müller (1997) and Bellemare et al. (2017) were read only as abstracts; neither is used for an
  equation number.
- The tail-versus-broad ratio is the builder's own derivation for a Gaussian bulk, pinned by a
  test; it depends on the shape of the bulk and holds for one (channel, axis) term.
- The first checks the builder would make: that the one-dimensional identity and the V-statistic
  agree with SciPy; the worked example's 0.25 and the tail derivations in `test_metric.py`; and
  that the pre-registration in commit 4dbecc3 matches the declared file and that the evidence run
  postdates it (the reviewer confirmed all three).
