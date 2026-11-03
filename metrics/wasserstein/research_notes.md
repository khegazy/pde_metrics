# Research notes: wasserstein

This bundle was built by a metric-building agent from the idea page
`docs/ideas/optimal_transport/wasserstein.md`, which the build narrowed to its signed-field
remainder and renamed
[wasserstein_signed_fields.md](../../docs/ideas/optimal_transport/wasserstein_signed_fields.md),
in pull request #32 (built 2026-10-31, merged 2026-11-02). An adversarial review round followed
on 2026-10-31, and a solver speedup round on 2026-11-02. This file holds what the builder and the
reviewer read, tried and concluded that the card does not carry, condensed from their work log
and records. The card is the source of truth for what the metric is; where the two disagree, the
card wins. The coding record is in [code_notes.md](code_notes.md).

## Summary

The bundle registers the quadratic Wasserstein distance between two mass-normalised density
fields on the torus, computed as a continuous distance by solving the periodic Monge-Ampère
equation (card, Definition). Exact transport between cell histograms was rejected, because on
kinet density, whose displacements are below a cell, it measures the grid and not the field. On
the kinet evidence every pre-registered axis followed with direction +1. The main scientific
result is that on kinet density the metric carries the same information as `h_minus_one`: the
largest damages agree to within about one percent, which the first-order relation between the
two predicts, while the metric costs about thirty times as much. Kareem kept both metrics on
2026-11-02. The main caveats are that the large background of density removes the "distance
squared in a shift" property the idea was built for, and that the solver fails, returning NaN,
once a density peaks at about three times its mean, which a strong shock exceeds.

## Sources

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| Saumier, Agueh & Khouider 2015, IMA J. Appl. Math. 80(1), 135-157 (arXiv:1009.6039v2), doi 10.1093/imamat/hxt032 | Full text: the arXiv v2 LaTeX source, compiled locally to read the equation numbers. The published IMA numbering was not seen | Eq. 3, Eq. 4, Eq. 5, Eq. 6, Eq. 14, Theorem 2.1 and the remark after it, Sect. 3.3, Sect. 4, Sect. 4.2, Sect. 5.1 | For 1-periodic densities $f, g$ the optimal map is $x + \nabla u$; $u$ solves $g(x + \nabla u)\det(I + D^2 u) = f$ (Eq. 4) by a damped Newton iteration (Eq. 6) with linearisation Eq. 5, step $1/\tau$ with $\tau \ge 1$, a mass re-normalisation at each step (Eq. 14), and an FFT solver for the linear step (Sect. 4.2, after Strain). Sect. 3.3 says the full linearisation can "sometimes" be replaced by a simpler equation; Sect. 4 says off-grid values of $g$ are interpolated (they used nearest neighbour; linear is named as the popular choice); Sect. 5.1 reports that $\tau = 1$ sufficed, with the full operator. Theorem 2.1 (after Cordero-Erausquin) states only that the map is additive; the periodicity of $u$ is the remark after it (reviewer) | `metric.py`, card (Definition, Limitations), `refs.bib` |
| Peyré & Cuturi 2019, Found. Trends Mach. Learn. 11(5-6), 355-607 (arXiv:1803.00567), doi 10.1561/2200000073 | Full text: the arXiv LaTeX source, compiled locally for the numbering; the journal numbering was not seen | Prop. 2.3, Eq. 2.18, Eq. 2.36, Remark 2.30, Eq. 8.16, Eq. 8.17 | Eq. 2.18 defines $W_p$, and Prop. 2.3 states it is a distance. Eq. 8.16 is the linearisation $W_2(a, a + \epsilon\rho) = \epsilon\lVert\rho\rVert_{H^{-1}(a)} + o(\epsilon)$; Eq. 8.17 states the bounds $b^{-1/2}\lVert a-b\rVert_{H^{-1}} \le W_2 \le a^{-1/2}\lVert a-b\rVert_{H^{-1}}$, whose upper bound lacks the factor 2 of the primary source (see Corrections). Eq. 2.36 and Remark 2.30 give the monotone map on the line, used in the worked example's derivation | `metric.py`, card (Definition), `refs.bib`, `test_metric.py` |
| Peyré 2018, ESAIM: COCV 24(4), 1489-1501 (arXiv:1104.4631v2), doi 10.1051/cocv/2017050 | Full text: the arXiv v2 LaTeX source, compiled locally for the numbering. Theorems, lemmas, corollaries and remarks share one counter in the author's style file, so a journal class may renumber them (reviewer); refs.bib identifies Corollary 3 and Theorem 5 by content as well | Eq. 5, Theorem 1, Lemma 2, Corollary 3, Theorem 5, Eq. 17 | Eq. 5 is the linearisation $W_2(\mu, \mu + d\mu) = \lVert d\mu\rVert_{H^{-1}(\mu)} + o(d\mu)$. Theorem 1 gives $W_2 \le 2\lVert\mu - \nu\rVert_{H^{-1}(\mu)}$, and Corollary 3 $W_2 \le 2\rho^{-1/2}\lVert\mu-\nu\rVert_{H^{-1}}$ when $\mu \ge \rho$ times the volume measure. Theorem 5 (Eq. 17), on a manifold of nonnegative Ricci curvature such as the flat torus, gives $\lVert\mu-\nu\rVert_{H^{-1}} \le [2(\rho_0^{1/2} - \rho_1^{1/2})/\ln(\rho_0/\rho_1)]\,W_2$, a coefficient no larger than $\max(\rho_0, \rho_1)^{1/2}$. Lemma 2 bounds a weighted $H^{-1}$ norm by the unweighted one | `metric.py`, `test_metric.py`, card (Definition), `refs.bib` |
| Engquist & Froese 2014, Commun. Math. Sci. 12(5), 979-988 (arXiv:1311.4581), doi 10.4310/CMS.2014.v12.n5.a7 | Full text: the arXiv LaTeX source. It would not compile (missing class file), so it is cited by section only | Sect. 1; Sect. 2.1; Sect. 2.2 | Sect. 1 defines $W_2^2$ as the infimum over rearranging maps of $\int \lvert x - T(x)\rvert^2 f$, gives $W_2^2 = s^2$ for a shifted hat function against the saturation of $L^2$, and computes $W_2$ from a Monge-Ampère solution. Sect. 2.1 says adding a positive constant to make signals positive "would distort the optimal transportation map"; Sect. 2.2 says mass balance is achieved most easily "by a simple constant scaling of the densities", the normalisation this bundle uses | `metric.py`, card (Definition), `refs.bib` |
| Yang, Engquist, Sun & Hamfeldt 2018, Geophysics 83(1), R43-R62 (arXiv:1612.05075), doi 10.1190/geo2016-0663.1 | Full text: the arXiv LaTeX source, compiled for the numbering. The journal prints unnumbered section headings (reviewer, medium confidence), so the card cites the heading with the arXiv number in brackets | Section "Data normalization" (Sect. 3.1 in arXiv), Eq. 27; "Compare globally", "Computation of adjoint source" (Sect. 3.3 in arXiv), Eqs. 34-35 | Adding a constant before normalising (the "linear normalisation", Eq. 27) makes the misfit non-convex in shifts. The adjoint source is cited for the metric's differentiability | Card (Definition), decorator comment, `refs.bib` |
| Engquist & Yang 2022, Commun. Pure Appl. Math. 75(10), 2201-2244 (arXiv:2002.00031), doi 10.1002/cpa.21990 | Full text: the arXiv LaTeX source, compiled for the numbering | Sect. 1; Eq. 2, Eq. 3, Eq. 4, Eq. 12, Assumption 4.1, Eq. 19, Theorem 4.2, Theorem 4.6 | Sect. 1: $W_2^2$ of a signal shifted by $s$ is $s^2$ whatever its profile. Theorem 4.6: for a compactly supported one-dimensional density on a background $c$, $W_2^2$ is $O(s^2)$ for $\lvert s\rvert$ below about $1/c + \lvert\mathrm{supp} f\rvert$ and $O(s)$ beyond. Eq. 12 quotes the $W_2$-$H^{-1}$ bounds with $1/c_1$ and $1/c_2$ rather than square roots, a third form. Eqs. 2-4 and Assumption 4.1 (Eq. 19) give the linear, exponential and softplus normalisations and a general class for which $W_2$ is a metric on signed functions (Theorem 4.2) | Card (Definition), `refs.bib`, [proposals/MTR-wasserstein-softplus-normalisation.md](../../proposals/MTR-wasserstein-softplus-normalisation.md) |
| Delon, Salomon & Sobolevski 2010, SIAM J. Appl. Math. 70(7), 2239-2258 (arXiv:0902.3527), doi 10.1137/090772708 | Full text: the arXiv LaTeX source. It would not compile (missing class file), so it is cited by section | Sect. 2 | The transport cost on the circle for a Monge cost: lift both distribution functions to the line with $F(x+1) = F(x) + 1$, couple mass level $v$ with level $v + \theta$, and minimise the convex average cost over $\theta$. The independent check of the solver | `test_metric.py`, card (Definition), `refs.bib` |
| Métivier, Allain, Brossier, Mérigot, Oudet & Virieux 2018, 80th EAGE Conference and Exhibition, 1-5, doi 10.3997/2214-4609.201801031 | Not opened; Crossref confirms the title, year and authors | None | The idea page's reference for graph-space transport, a signed-field formulation. Not cited on the card | The narrowed idea page only |
| Engquist & Yang 2019, Methods Appl. Anal. 26(2), 133-148 (arXiv:1810.08686), doi 10.4310/maa.2019.v26.n2.a3 | Recorded as abstract: only the introduction was read | Sect. 1 | The linear normalisation worked remarkably well in realistic large-scale inversions although it is not convex in shifts, while convex alternatives (positive part, squaring, envelope, absolute value) performed poorly; the paper sets out to explain this | Not cited on the card; a paragraph in [issues/047](../../issues/047-signed-field-transport-has-no-chosen-formulation.md) |
| McCann 2001, Geom. Funct. Anal. 11(3), 589-608 | Not opened, by the builder or the reviewer (the reviewer recalled it from memory) | None | Named by the reviewer as the source for the optimal map on the torus being $\exp_x(-\nabla\psi)$ with $\psi$ a function on the manifold, hence a periodic potential with no uniform drift | Not cited; worth opening if the zero-drift claim is ever questioned |

Every equation number above is from the arXiv copy, compiled locally and read from its `.aux`
file, because no PDF text tool was installed. The builder never saw a journal copy of any of
them; `refs.bib` says so for each. The reviewer compiled the same arXiv sources independently and
confirmed every cited number.

## Method choices

- **A continuous $W_2$ by a Monge-Ampère solve, not discrete transport.** The options weighed
  were exact discrete transport on a coarsened grid (POT), entropic Sinkhorn transport, the
  back-and-forth method, and the periodic Monge-Ampère Newton method. Discrete transport measures
  quantisation here (see Rejected formulations). Sinkhorn transport is a separate idea that waits
  on this one ([issues/067](../../issues/067-sinkhorn-waits-on-wasserstein.md)), and its entropic
  blur would dominate sub-cell displacements. The back-and-forth method needs c-transforms whose
  grid version loses exactly the second-order term $W_2$ is made of when displacements are
  sub-cell; that is the agent's own reasoning, not measured. Saumier et al. (2015) is periodic,
  FFT-based and cited. A prototype converged in 4 to 7 iterations at about 0.08 s per evaluation
  on 256^2 kinet density, with $W_2$ linear in sub-cell shifts.
- **The leading term of the linearised operator in place of the full one, with an adaptive
  damping.** The first version used a plain Laplacian step with $\tau = 1$, on a reading of
  Saumier et al. Sect. 3.3 and 5.1 that the review showed to be wrong. The current step divides
  the residual by $g(x + \nabla u)$ and halves itself until the residual falls (card, Definition).
  The options weighed in the review round were: keep the plain step and document the limit;
  $\tau = \max g$ (slow, and it stalls at a contrast of 100, per the reviewer); divide by $g$
  without damping (diverges for unrelated contrast-10 pairs); divide by $g$ with halving (converges
  for unrelated pairs up to contrast 10 and for the circle profile peaking at 2.33 times its mean
  at every shift); and a full Newton step with GMRES (Saumier Sect. 4.2, the most robust, about 25
  more lines). The agent took divide-and-halve because it fixes the measured failures with little
  code and leaves the converged value unchanged; the full Newton step became a proposal. The
  agent's own choice.
- **Spectral derivatives rather than Saumier et al.'s fourth-order finite differences.** Chosen
  for consistency with `h_minus_one` and the repository's derivative convention; the agent's own.
- **A cubic B-spline to evaluate the candidate at the displaced points.** Saumier et al. use
  nearest neighbour. Measured on kinet density at step 5001, relative to cubic B-splines, the
  value changes by at most 1.6% for nearest neighbour, $5.5 \times 10^{-4}$ for linear and
  $3.4 \times 10^{-5}$ for quintic, so cubic is converged to the size of the quintic difference.
  Nearest neighbour differs most on the blurred candidate, where sub-cell displacements dominate.
  The agent's own choice.
- **Register $W_2$, not $W_2^2$.** $W_2$ is the distance (Peyré & Cuturi Eq. 2.18, Prop. 2.3); the
  seismic misfit is its square. The agent's own choice.
- **Normalise each density by its own mean.** The constant scaling of Engquist & Froese Sect. 2.2.
  It makes the total mass invisible (card, Limitations).
- **NaN outside the domain, not an invented value.** Any value given to a field with a
  non-positive cell would be one of the signed-field formulations that
  [issues/047](../../issues/047-signed-field-transport-has-no-chosen-formulation.md) leaves open.
- **Density only.** Velocity and vorticity take both signs and wait on issue 047; the idea page
  was narrowed to that remainder rather than deleted.
- **Re-run the evidence although the numbers moved only at about $10^{-9}$.** The review round's
  rules say any change re-runs; the fingerprint confirmed that nothing visible changed.
- **Closed form in two dimensions only (speedup round).** The options were closed forms for both
  2-D and 3-D (Sylvester's criterion needs three leading minors in 3-D), or one general cheap
  method (`np.linalg.det` on leading blocks). The agent took the closed form for 2-D, the only
  dimension any dataset has, and kept the eigenvalue path elsewhere, which leaves 3-D bit-for-bit
  unchanged. Recorded in the card's Definition. The agent's own choice.
- **The card's evidence moved to the speedup gate run**, because it is the committed code's run
  and every statistic matched the previous run at three figures. It has since been repinned (see
  Evidence runs).
- **Issue 119 was not used during the build**, because the registered number is the literature's
  $W_2$ itself, not a summary that is a convention.

**Pre-registration.** Committed in ed1970a on #32, before any full-ladder run: every enabled axis
(`translate_x`, `translate_subpixel`, `gaussian_blur`, `box_blur`, `median_blur`,
`lowpass_ideal`, `lowpass_butterworth`, `highpass_ideal`, `highpass_butterworth`, `coarsen`,
`coarsen_bandlimited`, `additive_noise`) follows with direction +1, and nothing is blind;
`fields: ["density"]`, `higher_is_better: false`, `units: "length"`, `reduction: "sqrt_mean"`.
The reasons: a translation preserves the amplitude spectrum and shape but moves mass, so $W_2$ is
not blind to it; blurs and low-pass filters carry mass from peaks into troughs; high-pass filters
remove the large-scale arrangement of mass; coarsening redistributes mass within each block or
below the coarse grid's resolution; and noise adds and removes mass in each cell. No enabled
operator preserves where mass sits.

## Rejected formulations and negative results

- **Exact discrete transport between cell histograms.** One Dirac per cell centre, solved by POT's
  network simplex (`ot.emd2`). It is not affordable at 256 by 256: the cost matrix is 65,536^2
  entries (34 GB). Measured on 2-D periodic test fields, a solve costs 0.37 s at 32^2 and 5 to 11 s
  at 64^2. Worse, on near-uniform densities its $W_2^2$ scales as the relative fluctuation
  $\epsilon$ times the cell size rather than as $\epsilon^2$: at $\epsilon = 0.03$ it halved each
  time the grid doubled ($1.9 \times 10^{-5}$ at 32^2, $1.1 \times 10^{-5}$ at 48^2,
  $8.4 \times 10^{-6}$ at 64^2). The agent's 1-D derivation, checked numerically: between a uniform
  density and $1 + \epsilon\cos(2\pi x)$ on $N$ cells of size $h = 1/N$, the discrete $W_2^2$ is
  about $h\epsilon/\pi^2$ while the continuous one is $\epsilon^2/(8\pi^2)$, a ratio of
  $8h/\epsilon$. Measured at $N = 256$: a ratio of 1.0 at $\epsilon = 0.3$, 1.2 at
  $\epsilon = 0.03$ and 10.4 at $\epsilon = 0.003$. Kinet density's relative fluctuation is 0.2%
  to 0.7%, deep in the regime where quantisation dominates. The reviewer reproduced the derivation
  by hand (a flux $\epsilon/2\pi$ through each edge, each unit crossing one cell at cost $h^2$) and
  noted it holds while $\epsilon/(2\pi) < h$. Kept as
  [proposals/MTR-wasserstein-discrete-coarsened.md](../../proposals/MTR-wasserstein-discrete-coarsened.md)
  so the reason survives; summarised on the card (Definition, "Why a continuous solve").
- **The shift property on density.** The idea page's selling point, that $W_2^2$ of a shifted
  signal is $s^2$ whatever its profile, holds for a signal on a zero background. Density is a
  fluctuation of under 1% on a positive mean. Measured with the prototype on kinet density at step
  2001: a 16-cell shift gives $W_2 = 0.024$ cells, not 16, and $W_2$ is linear in sub-cell shifts
  (0.125 to 2 cells gives $1.92 \times 10^{-4}$ to $3.07 \times 10^{-3}$). The first card explained
  this with Engquist & Yang's Theorem 4.6, which the review showed does not apply (see Review
  round); the card now gives the linearisation instead (card, Definition, "Shift and background").
- **The plain Laplacian step with $\tau = 1$.** It overshoots once the candidate density exceeds
  about twice its mean; the measurements and the fix are in
  [code_notes.md](code_notes.md) (Bugs and fixes).

## Evidence runs

1. **Prototype measurements (2026-10-31, scratch scripts, not kept).** On kinet_re5e4 density at
   steps 2001 and 5001, against six candidates (the mean field, 1- and 16-cell shifts, a Gaussian
   blur, noise, another frame), the continuous $W_2$ between the mass-normalised densities equalled
   `h_minus_one` of the mass-normalised densities to within a ratio of 0.9997 to 1.0082. The
   normalised density lies between 0.96 and 1.007 there. The agent first concluded that the two
   would be near-duplicates in the panel because "on this dataset W2 on density is h_minus_one on
   density divided by the mean density, to better than 1%". The shift and interpolation
   measurements of the previous sections come from the same prototype.
2. **Smoke run `results/wasserstein_1793494919`.** kinet_re5e4_dev with `degradation=quick`, before
   the pre-registration: 1000 rows, 111 s, no NaN, about 0.105 s per row. Concluded that the cost
   fits.
3. **First evidence run `results/wasserstein_1793495645`.** The brief's command,
   `python evaluate.py metrics=[wasserstein] dataset=kinet_re5e4 dataset.time.start=2000 dataset.time.reduction=50 paths.data_url=null`,
   at ed1970a on #32, dirty false: 161 frames (2000 to 10000), 9499 rows, 2260 s. All twelve
   pre-registered axes followed with direction +1 and `rho_ci_lo` = 1; no NaN and no convergence
   warning. Against `h_minus_one`'s committed fingerprint for density, the largest damage on every
   axis and probe is 0.9991 to 1.0076 times `h_minus_one`'s, and the elasticities agree to three
   figures, while `wasserstein` cost 0.214 s per evaluation against 0.0022 s. The run's profile
   listed `additive_noise`, `coarsen` and `coarsen_bandlimited` as responses provably below 0.05,
   which is smallness, not invariance; all three follow perfectly. The agent drafted an issue,
   "wasserstein and h_minus_one carry the same information on kinet density", in the PR body
   rather than use issue 119. The first explanation, that Peyré's bounds "require" the agreement,
   was corrected in the review round (see Review round).
4. **Re-run after the solver fix, `results/wasserstein_1793501169`.** The same command at ecf826c on
   #32, from a clean tree: 9499 rows, 2135 s, no convergence warning. Every axis's direction, rho,
   `rho_ci_lo`, largest damage, elasticity, Cliff's delta and monotone fraction were unchanged at
   three figures; only the cost moved (0.214 to 0.193 s in the profile). Compared row by row with
   the first run, the values moved by a relative $5.0 \times 10^{-11}$ in the median and
   $1.37 \times 10^{-6}$ at worst; the orchestrator's own comparison gave 9499 of 9499 rows
   matched, absolute difference at most $1.7 \times 10^{-11}$ and relative at most
   $1.4 \times 10^{-6}$. The agent had first written "the two solvers agree to 4e-9" from a 15-pair
   spot check; the run-level numbers supersede it. The commit message of b6917b4 on #32 keeps the
   spot-check figure, which the PR body flags.
5. **Speedup gate run `results/wasserstein_gate_closed_form/wasserstein_1793647243`.** The same
   command with `paths.results` set to that folder, at 589ff0d on #32, login10, dirty false: 9499
   rows, 957 s, no warning. Every statistic was identical at three figures to the previous run; only
   the cost moved (0.193 to 0.0721 s in the profile). The row-by-row gate is in
   [code_notes.md](code_notes.md) (Performance). The card's evidence was regenerated from this run
   in 1f3c042 on #32.
6. **The run the card cites now is `results/comparison_1793657627`**, repinned in #35 after the
   merge, which runs all kinet metrics together. In it `h_minus_one` correlates with `wasserstein`
   at 0.996 (card, Results, "Compared with the other metrics").

No declared direction was contradicted in any run.

## Corrections to the rest of the repository

- **The idea page's citations.** It cited Yang et al. as an unpublished 2016 arXiv preprint with
  Froese as fourth author; it is published in Geophysics 83(1), R43-R62 (2018), with the fourth
  author Brittany F. Hamfeldt per Crossref. It cited Engquist & Yang (CPAM) with no year or volume;
  it is 75(10), 2201-2244 (2022). Both corrected on the narrowed page in #32.
- **The idea page itself.** Narrowed in #32 to its signed-field remainder and renamed
  [wasserstein_signed_fields.md](../../docs/ideas/optimal_transport/wasserstein_signed_fields.md),
  because `tests/test_documentation.py` forbids an idea page named after a built metric. Its
  references and pitfalls were carried as follows. Engquist & Froese 2014, Yang et al. 2018 and
  Engquist & Yang 2022 are in `refs.bib` and on the card; Métivier et al. 2018 concerns signed
  fields only and stays on the narrowed page. The pitfall "it accepts the wrong amplitude in the
  right place" is on the card's Limitations (total mass invisible) and pinned by
  `test_total_mass_is_normalised_away`. The pitfall "the horizontal-shift reading is less clean in
  2-D" is on the card's Limitations, with the stronger point that a background removes the shift
  reading altogether. Its row in `docs/ideas/README.md` and its bullet on the theme page were
  narrowed, and the theme page lists `wasserstein` as built.
- **Issue 066** was narrowed to the signed remainder and renamed from
  `066-wasserstein-needs-a-transport-library.md` to
  [066-wasserstein-for-signed-fields-waits-on-047.md](../../issues/066-wasserstein-for-signed-fields-waits-on-047.md)
  in #32.
- **Links.** Every link to the renamed page or issue was rewritten in #32. Links that meant the
  built distance now point to the card (the idea pages on sliced Wasserstein, Sinkhorn,
  mollification split, negative Sobolev norms and metric-geometry curvature, `evaluation_design.md`,
  `background.md` and the ideas README). In issues 047, 048, 050, 054 and 067 the sentences
  calling the distance "unbuilt" now say it is built for density.
- **Peyré & Cuturi's Eq. (8.17).** It states $W_2 \le a^{-1/2}\lVert a - b\rVert_{H^{-1}}$ and
  attributes the equivalence to Peyré (2018), whose upper bound (Corollary 3) carries a factor 2.
  The agent did not find the factor-free upper bound in the primary source, so the bundle cites
  Peyré 2018 for both bounds. The agent first cited Eq. (8.17) itself and corrected that before the
  pull request. `h_minus_one` cites Peyré 2018 directly, so its card has no defect. Anyone quoting
  the $W_2$-$H^{-1}$ equivalence should take it from Peyré 2018.
- **Issue 047** gained a paragraph on Engquist & Yang 2019 (a lead read to its introduction), in
  the routing after the build.
- **Issue 101's status line** was updated by #32 to mention the contract-test change; the change
  itself is described in [code_notes.md](code_notes.md) (Implementation).

## Review round

The reviewer wrote 11 critiques at 215945d on #32; the fixes are in ecf826c, with a `refs.bib`
note following in the evidence commit because the tree had to stay clean during the run. The code
critiques (the solver step, the non-convergence warning, the two weak tests, the Nyquist mode and the
cost figures) are in [code_notes.md](code_notes.md). The rest:

- **The bounds do not "require" the agreement with `h_minus_one`.** With the
  normalised kinet density between $a = 0.96$ and $b = 1.007$, the bounds
  $b^{-1/2}H \le W_2 \le 2a^{-1/2}H$ allow a ratio from about 0.996 to 2.04, because the factor 2
  of Corollary 3 is not close to 1. What explains the agreement is the linearisation (Peyré Eq. 5)
  with Lemma 2 applied both ways, which to first order gives $[b^{-1/2}, a^{-1/2}]$, that is
  [0.996, 1.021] on kinet. This combination is the agent's (and the reviewer's) reading, not a
  theorem Peyré states. The reviewer also showed that "agree to two significant figures" fails for
  `coarsen` (0.04868 against 0.04831, which round to 0.049 and 0.048, a ratio of 1.0076), so the
  wording became "within about one percent". **Fixed:** the card's Definition, Limitations and
  comparison now credit the first-order relation, labelled as the agent's reading; the module
  docstring, issue 066 and the PR body's draft issue were changed to match.
- **Engquist & Yang's Theorem 4.6 does not describe a periodic density.** The theorem
  is one-dimensional, needs compact support and gives big-O bounds; kinet density fills the torus,
  so its $O(s^2)$ branch covers every shift on the ladder, and the authors' own remark after the
  proof says the higher-dimensional case is not worked out. An elasticity of 1 in the shift also
  holds for $W_2 = s$ on an empty background, so it cannot distinguish the two cases; the magnitude
  does (a 16-cell shift costs 0.0746 cells, the median at level 5 of `translate_x` in
  `results/wasserstein_1793495645`). The card's "fluctuation of a few percent" disagreed with the
  measured 0.2% to 0.7%, and the narrowed idea page's sentence that the density build "shows the
  same thing" (non-convexity) overstated the run, which shows a linear response of small size.
  **Fixed:** the card applies Theorem 4.6 only to what it states, and derives the shift's cost from
  the linearisation instead: $W_2 \approx s\,(\sum_{\mathbf k}(k_x/\lvert\mathbf k\rvert)^2\lvert\hat f_{\mathbf k}\rvert^2)^{1/2}$,
  at most $s$ times the RMS relative fluctuation (the agent's derivation; the reviewer reached the
  same estimate). "A few percent" became "well under a percent of its mean in root mean square";
  the idea page now says "shows a related effect in size"; issue 066 and the module docstring now
  say "for a compactly supported 1-D signal". The `refs.bib` note was corrected in the evidence
  commit.
- **Judgement 006 changes shared tests where AGENTS.md §3.2 says stop, and leaves out pressure.**
  The reviewer confirmed that the change reaches only `wasserstein` (every other
  `fields=` declaration is `("*",)`, velocity, vorticity, pressure, or density with vorticity),
  that no other metric's test became weaker, and that the offset leaves a contrast of about 4.5 so
  the identity and blur tests are not vacuous. On process, AGENTS.md §3.2 and the brief both point
  to stopping, and the brief reserves the judgement record for a method question with a literature
  standard. On scope, issue 101 asks for a positive input "for any metric that declares a positive
  field" and was written for `shock_set_distance`'s pressure. **Partly accepted:** the omission of
  pressure is deliberate (a dataset may store a gauge pressure with both signs), and the test
  comment and judgement 006 now say so; the 3-D bound in the comment was corrected (see
  [code_notes.md](code_notes.md)). The process objection was left to Kareem, since judgement 006
  already records the choice and its reversal.
- **"u periodic" is not what Saumier et al.'s Theorem 2.1 states.** The theorem states
  additivity, $\nabla\Psi(x + p) = \nabla\Psi(x) + p$, which alone allows a uniform displacement;
  the periodicity is the authors' remark after the theorem. The reviewer named McCann (2001) as a
  source for the conclusion, from memory, and noted that the circle test supports it, since it
  matches at shifts where the optimal rotation is non-zero ($\theta = 0.0296$ at 32 cells).
  **Fixed:** the card, docstring and `refs.bib` cite the theorem for additivity and the remark for
  periodicity, and name the circle test as the empirical check. McCann was not cited, because
  neither opened it.
- **Journal versus arXiv numbering.** Yang et al.'s "Sect. 3.1" and "Sect. 3.3" are
  arXiv numbers, and Geophysics prints unnumbered headings (the reviewer's belief, medium
  confidence); Peyré's Corollary 3 and Theorem 5 come from a style file in which theorem-like
  environments share one counter, so a journal class may renumber them (medium-low confidence);
  Saumier et al., Engquist & Yang 2022 and Peyré & Cuturi are low risk. **Fixed:** Yang et al. is
  cited by section heading with the arXiv number in brackets, and `refs.bib` notes Peyré's shared
  counter and identifies the results by content. The low-risk sources were left as they are.

**What the reviewer checked and found sound.** The formula and normalisation ($W_2^2$ as the mean
of $f\lvert\nabla u\rvert^2$, the step sign and the Eq. 14 re-centring against Saumier et al.
Sect. 3.1 and 4); the conventions (identity exactly 0, float32 against float64 to
$2 \times 10^{-8}$, spacing scaling along the varying axis only, a z-constant 3-D field giving the
2-D value); the round-off floor (the residual reaches $10^{-16}$ on 256^2, 1024^2 and 32^3 at low
contrast); the symmetry declaration (asymmetry $1.4 \times 10^{-5}$ and $3.1 \times 10^{-5}$ on two
synthetic pairs); the evidence run's provenance (sha ed1970a, dirty false, the pre-registration
commit at 18:13:59 before the run id at 18:14:05); the circle agreement and the `h_minus_one`
ratios, rerun; the test's implementation of Delon et al. Sect. 2; every number typed in the Results
prose; and every cited equation in the compiled arXiv sources, including that the scaling of
Peyré's integral-normalised bounds to `h_minus_one`'s RMS normalisation is correct. Findings that
needed the CFS data or POT timings (the discrete-transport, quantisation, prototype ratio,
interpolation and asymmetry measurements) were not rerun.

## Open questions and follow-ups

- **Does `wasserstein` duplicate `h_minus_one`?** The draft issue in the PR body was held for
  Kareem's decision and then dropped: on 2026-11-02 Kareem kept both metrics. The card states the
  agreement on kinet, and the experiment that would separate them is
  [proposals/EXP-wasserstein-background-ratio-sweep.md](../../proposals/EXP-wasserstein-background-ratio-sweep.md):
  sweep the bump height of the existing `advecting_blobs` reader over decades against its
  background of 1, moving $W_2$ from the large-background $O(s)$ regime to the empty-background
  $O(s^2)$ regime of Engquist & Yang's Theorem 4.6, with no new code.
- **A solver that converges at high contrast.**
  [proposals/MTR-wasserstein-full-newton-gmres.md](../../proposals/MTR-wasserstein-full-newton-gmres.md):
  solve the linearised operator of Saumier et al. Eq. (5) by GMRES preconditioned with the
  averaged operator, as in their Sect. 4.2; it would give the same $W_2$ wherever the present solver
  converges and extend it to the densities behind strong shocks.
- **Known-answer transport problems.**
  [proposals/EXP-wasserstein-known-answer-transport.md](../../proposals/EXP-wasserstein-known-answer-transport.md):
  a manufactured map (Saumier et al. Sect. 5.1) and one-dimensional circle profiles (Delon et al.
  Sect. 2), for validating any transport metric; issues 048 and 067 both need such a reference.
  `test_metric.py` already uses the second family.
- **A fifth family of signed-field formulations.**
  [proposals/MTR-wasserstein-softplus-normalisation.md](../../proposals/MTR-wasserstein-softplus-normalisation.md):
  Engquist & Yang's exponential, softplus and general $(\sigma(f) + c)/\int$ normalisations
  (Eqs. 3, 4, 19, Theorem 4.2), absent from the four that issue 047 lists.
- **The largest displacement.**
  [proposals/MTR-wasserstein-largest-displacement.md](../../proposals/MTR-wasserstein-largest-displacement.md):
  the maximum of $\lvert\nabla u\rvert$ from the potential the solve already returns, a worst-case
  companion to $W_2$'s root mean square, as `max_error` is to `rmse`, at no extra cost. It is not
  the infinity-Wasserstein distance, whose optimal plan differs.
- **Signed fields** wait on
  [issues/047](../../issues/047-signed-field-transport-has-no-chosen-formulation.md) and
  [issues/066](../../issues/066-wasserstein-for-signed-fields-waits-on-047.md).
- **The contract-test change** is
  [judgements/006](../../judgements/006-contract-tests-give-a-density-metric-a-positive-field.md);
  the records leave its process question with Kareem and do not record a decision, beyond the merge
  of #32 with the change in place.
- **The refactor gate and the cost comparison** from the speedup round are
  [issues/119](../../issues/119-refactor-gate-fails-on-ill-conditioned-small-values.md) and
  [issues/125](../../issues/125-costs-from-different-runs-are-not-comparable.md); see
  [code_notes.md](code_notes.md) (Performance).

## For the next agent

- **Least sure of:** whether the arXiv equation and theorem numbers match the journals' (Saumier et
  al. in IMA, Yang et al. in Geophysics, Engquist & Yang in CPAM, Peyré in ESAIM, Peyré & Cuturi in
  FnTML). No journal copy was seen.
- **Not verified:** Saumier et al.'s claim, via Cordero-Erausquin, that the optimal map on the torus
  has zero mean displacement for positive densities. The circle test is consistent with it in 1-D;
  McCann (2001) would settle it and was not opened.
- **The first-order explanation of the agreement with `h_minus_one`** (Peyré Eq. 5 with Lemma 2) is
  the agent's and the reviewer's reading, not a stated theorem; so is the estimate that a small
  shift costs $s$ times at most the RMS relative fluctuation.
- **The first three things the builder would check:** rerun the circle test and the bound test,
  which together pin the solver against an independent exact answer; recompute the `h_minus_one`
  ratio from the two fingerprints, the main scientific result; and read the card's Definition
  against Saumier et al. Sect. 3-4 to confirm the step and the Eq. 14 renormalisation are as
  described.
