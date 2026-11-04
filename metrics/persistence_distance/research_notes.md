# Research notes: persistence_distance

This bundle was built by a metric-building agent from the idea page
`docs/ideas/topology/persistence_diagrams.md` (since deleted, in the same change) in pull request
#29 (built 2026-10-31, merged as 16c08b1), with an adversarial review round on 2026-10-31. This
file holds what the builder and the reviewer read, tried and concluded that the card does not
carry, condensed from their work log and records. The card is the source of truth for what the
metric is; where the two disagree, the card wins. The coding record, including the shared
point-set companion kind this launch added to the harness, is in [code_notes.md](code_notes.md).

## Summary

The bundle registers the bottleneck distance between the sublevel-set persistence diagrams of two
scalar fields (density, and vorticity in 2-D), taking the largest per-dimension distance over the
homology dimensions, with the T-construction on a cubical complex that wraps the grid's periodic
axes (card, Definition). On the evidence run every pre-registered axis followed with direction +1
on both fields, whole-cell translation was blind as declared, and the sub-pixel translation was
blind too without being declared. On vorticity the per-frame order under smoothing and low-pass
fails mostly by exact ties between neighbouring strengths, while under coarsening the failures are
mostly reversals; the builder's explanation of the ties is an interpretation, not a measurement.
The main caveats are that the review found three of the builder's first citations applied
theorems outside their hypotheses (all re-cited to Skraba & Turner v7), that one source (Martinez
et al. 2026) was read as an abstract only, and that the metric sees only one feature, the worst
mismatch, so it plateaus where a graded response would be wanted.

## Sources

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| Cohen-Steiner, Edelsbrunner & Harer 2005, Proc. 21st Annu. Symp. Comput. Geom. (SoCG), 263-271, doi 10.1145/1064092.1064133 | Full text: the authors' copy at pub.ista.ac.at/~edels/Papers/2007-01-StabilityPersistenceDiagrams.pdf, text extracted by the builder's own extractor | Sect. 3.1, Main Theorem and Definition of $d_B$; Sect. 1, inequality (1); Sect. 2, Definition of the persistence diagram and the k-Triangle Lemma | The definition of the diagram (points at infinity for classes never killed), of the bottleneck distance, and the stability theorem for continuous tame functions. Despite its file name the PDF is the SoCG 2005 version (footer "SCG'05, June 6-8, 2005, Pisa", nine pages, sections 1-5), established by the reviewer and checked by the builder | Card, `metric.py`, `test_metric.py`, `refs.bib`. After the review it is cited for the diagram and $d_B$, and its Main Theorem only as the precedent for the stability bound, not its proof; the k-Triangle Lemma is no longer cited |
| Cohen-Steiner, Edelsbrunner & Harer 2007, Discrete Comput. Geom. 37(1), 103-120, doi 10.1007/s00454-006-1276-5 | Not opened (paywalled); Crossref record checked | None | The journal version the idea page gave. Every locator the bundle cites comes from the 2005 version, and `refs.bib` says so | `refs.bib`, card, `metric.py` |
| Skraba & Turner 2020, arXiv:2006.16824 (preprint), doi 10.48550/arXiv.2006.16824, pinned to v7 (10 Jul 2025) | Full text. First read through a summarising fetch of the arXiv HTML (first 100000 of 116676 characters); in the review round every cited locator was checked line by line against a text extraction of the full v7 HTML | Eq. 1; Definitions 2.4 and 2.5; Sect. 2 and Theorem 2.3; Theorem 4.6(i); Sect. 5.1 and Theorem 5.1 | Eq. 1 defines the bottleneck distance between graded diagrams as the supremum over dimensions, exactly the registered reduction. Definition 2.5: total p-Wasserstein distance, whose $p \to \infty$ limit is Eq. 1. Theorem 4.6(i), the Cellular Wasserstein Stability Theorem, bounds $W_p$ by $\lVert f - g \rVert_p$ over cells for monotone cell-wise constant functions on a finite CW complex, which covers the T-construction. Definition 2.4: the convention for points at infinity, which gudhi follows. Sect. 2 and Theorem 2.3: the interval decomposition, $b = \inf$, $d = \sup$ of each interval. Sect. 5.1: "Method 1" (pixel as maximal cell, faces take the minimum of cofaces) and "Method 2" (pixel as vertex), which can give very different persistent homology; Theorem 5.1 carries the bound to images with constant $\sum_i 2^{d-i}\binom{d}{i}$ | Card (Equations (2), (4), (5)), `metric.py`, `test_metric.py`, `refs.bib`, the Betti-curve and Wasserstein proposals |
| Bleile, Garin, Heiss, Maggs & Robins 2022, Research in Computational Topology 2, AWM Series vol. 30, Springer, 1-26, doi 10.1007/978-3-030-95519-9_1 | Full text. First through a summarising fetch of the ar5iv HTML of arXiv:2102.11397; in the review round every locator was checked line by line against a text extraction of the full arXiv HTML (v1, the only version) | Definitions 4.3 and 4.4; Sect. 1; Sect. 4.2; Theorems 6.1-6.2 | V-construction (pixel as vertex, four-connectivity in 2-D) against T-construction (pixel as top cube, lower cubes take the minimum of adjacent top cubes, eight-connectivity); the two can give different diagrams. Sect. 4.2: on a periodic domain the two are dual cubical complexes on the d-torus | Card, `metric.py`, `refs.bib` |
| GUDHI User and Reference Manual 3.13, chapters "Bottleneck distance" and "Cubical complex" (Godi; Dlotko; GUDHI Editorial Board), https://gudhi.inria.fr/python/latest/ | Full text | `bottleneck_distance_user.html`; `cubical_complex_user.html` | `bottleneck_distance` uses the sup norm, allows matching to the diagonal, supports points at infinity; with `e=None` it is an additive approximation of the smallest positive double, possibly with the last two or three mantissa bits wrong, and `e=0` is exact and expensive. Its algorithm follows Efrat, Itai & Katz 2001 (Algorithmica 31(1), 1-28), not read. The cubical chapter says filtrations are given on maximal cubes or vertices and a fully periodic complex is a torus; it cites Kaczynski, Mischaikow & Mrozek 2004 and Wagner, Chen & Vucini 2012, not read | `metric.py`, card, `refs.bib` |
| Muszynski, Kashinath, Kurlin, Wehner & Prabhat 2019, Geosci. Model Dev. 12(2), 613-628, doi 10.5194/gmd-12-613-2019 | Full text, through the GMD article page with a summarising fetch tool | Sect. 2.2.1, Eqs. 1-2; Abstract; Acknowledgements | Its topological step is not persistent homology: it tracks connected regions of superlevel sets of integrated water vapour (Eq. 2, four-connected, Union-Find) as the threshold is swept, and feeds the region size against threshold to a support vector machine; the authors call it inspired by persistence. Precedent for threshold sweeps, not diagram distances (see Corrections) | Card, Limitations; `refs.bib` |
| Smith, Fukami, Sedky, Jones & Taira 2024, J. Fluid Mech. 980, A18, doi 10.1017/jfm.2024.16 | Full text, through the Cambridge article page (first 100000 characters) with a summarising fetch tool | Sect. 2.1; Sect. 3.1; Eq. 2.1 | Persistent homology of the flow's trajectory in state space (each 200 x 120 vorticity snapshot one point of $\mathbb{R}^{24000}$, Vietoris-Rips filtration), resting on H1; diagrams read by inspection, no diagram distance; the only persistence quantity is an average-persistence term in an autoencoder loss (Eq. 2.1) | Card, Limitations; `refs.bib` |
| Martinez, Jagadeesh, Manolesos & Omidyeganeh 2026, Comput. Fluids 306, 106931, doi 10.1016/j.compfluid.2025.106931 | Abstract only. The author PDF on City Research Online (openaccess.city.ac.uk/id/eprint/36533) has CID-encoded fonts that no available tool recovered, in the build and again in the review round; the publisher page refused the fetch | None | Vortex-core identification by template matching: persistent homology of sliding windows gives a template-similarity field, used to track the leading-edge vortex of a pitching NACA 63(3)418 aerofoil (template radius 0.04c, down-sampling factor 10). The abstract speaks of a "template-target feature space distance"; whether that is a diagram distance is not known | Card, Limitations (narrowed in the review round); `refs.bib` |
| Tierny, Favelier, Levine, Gueunet & Michaux 2018, IEEE Trans. Vis. Comput. Graph. 24(1), 832-842, doi 10.1109/TVCG.2017.2743938 | Abstract (arXiv:1805.09110) | None | The Topology ToolKit, an open-source topological-analysis platform for scientific visualisation; cited only as an alternative implementation | Card, Limitations; `refs.bib` |
| Tauzin et al. 2021, J. Mach. Learn. Res. 22(39), 1-6 (giotto-tda); only the documentation page of `gtda.diagrams.PairwiseDistance` was read | Secondary (the documentation page; the first record named the source file, which was never fetched, and was corrected in the review round) | `PairwiseDistance`, parameter `order` | Software does not agree on combining per-dimension distances: giotto-tda takes a norm of order `order` (default 2) across dimensions. A 2-norm over $d+1$ dimensions is bounded only by $\sqrt{d+1}\,\lVert f-g \rVert_\infty$, where the maximum keeps the stability bound exactly | Not cited; archive only |
| Edelsbrunner, Morozov & Pascucci 2006, Proc. 22nd Annu. Symp. Comput. Geom., 127-134, doi 10.1145/1137856.1137878 | Abstract (author page) and a search summary | None | An epsilon-simplification of a function on a 2-manifold removes every diagram point within epsilon of the diagonal while staying within epsilon in the sup norm; existence in dimensions 0 and 1 | The topological-simplification degradation proposal |

## Method choices

- **Bottleneck rather than a Wasserstein distance between diagrams.** The options were the
  bottleneck distance (the idea page's first named distance, with the stability theorem of its
  first reference) and $W_p$ (sensitive to the number of small features). The bottleneck was
  chosen because it is the one with a theorem tying it to the pointwise $L^\infty$ error the
  repository already reports (`max_error`). The agent's own choice within the literature's
  options; the Wasserstein variant is a proposal (see Rejected formulations).
- **Maximum over homology dimensions.** The builder first believed no source fixed this (giotto-tda
  defaults to a 2-norm over dimensions) and drafted an issue under the reserved number 115. While
  the evidence run was going it found Skraba & Turner 2020, Eq. 1, which defines the bottleneck
  distance between graded diagrams exactly so and keeps the stability bound, and withdrew the
  draft in commit 601bc27 on #29 before anything reached main. Issue number 115 was later used by
  the routing for a different item (see Open questions).
- **Points that never die are kept and matched among themselves**, gudhi's default. On the torus
  their number is fixed by topology (1, 2, 1), so both diagrams always have the same count and the
  distance stays finite; their births are the global minimum, the levels at which the torus's two
  loops close, and the global maximum, so they carry the field's range (card, Limitations, "The
  extremes always count"). First attributed to Cohen-Steiner et al.'s points at infinity; after
  the review it is cited to Skraba & Turner, Definition 2.4.
- **T-construction rather than V-construction.** The data are cell averages, so a value belongs to
  a cell (Bleile et al. 2022). The agent's choice, sourced.
- **Sublevel filtration of the signed field rather than of |vorticity|.** Minima are born in H0
  and, on the torus, maxima close loops in H1 by duality, so both signs of vortex enter the
  diagram. The agent's own reasoning.
- **Fields density and vorticity only.** Any one-channel scalar field would do, but only these two
  are on the evidence dataset; pressure can be added when a dataset tests it.
- **`differentiable=False`.** The bottleneck distance is Lipschitz with a gradient almost
  everywhere, but that gradient moves one pair of points, none is computed here, and the
  literature's training losses use Wasserstein-type distances. The agent's own reasoning.
- **`cost="expensive"`** from the measured 0.4 s per comparison at 256 x 256 (code_notes.md,
  Performance).
- **On a 3-D dataset the metric keeps raising on three-component vorticity** rather than
  returning NaN, because a vector has no sublevel sets and NaN would hide the misuse; the card
  says to pass `fields=[density]`. Decided in the review round; the agent's own choice.
- **No judgement file was written**: the builder judged no choice to be one it would have stopped
  to ask about. The reserved judgement 005 was released and later used by another bundle.

**Pre-registration**, committed verbatim in the message of commit 3f9d2b6 on #29 before any
full-ladder run on the evidence dataset: fields density and vorticity, `higher_is_better: false`,
units `field`, reduction `mean`; declared to follow with direction +1: `gaussian_blur`,
`box_blur`, `median_blur`, `lowpass_ideal`, `lowpass_butterworth`, `highpass_ideal`,
`highpass_butterworth`, `coarsen`, `coarsen_bandlimited` and `additive_noise`; declared blind:
`translate_x`. The stated reasons: smoothing and low-pass flatten extrema and erase the shallowest
features, so diagram points move toward the diagonal; high-pass changes the depth of every large
feature and the global extrema, which the essential and long-lived points record; coarsening
erases features smaller than a block; noise moves every birth and death and adds short-lived
features whose lifetimes grow with the amplitude.

## Rejected formulations and negative results

- **Wasserstein distance between diagrams.** On a synthetic 64 x 64 field, $W_1$ on H1 grew
  380-fold between noise 0.001 and 0.5 against 250-fold for the bottleneck, at about eight times
  the cost. Not registered because the bottleneck is the distance with the $L^\infty$ stability
  theorem of the idea page's first reference; written up as
  [proposals/MTR-persistence_distance-wasserstein-diagram-distance.md](../../proposals/MTR-persistence_distance-wasserstein-diagram-distance.md).
  The vorticity ties on the evidence run (below) argue for it where a graded response matters.
- **A 2-norm over homology dimensions** (giotto-tda's default) was weighed against the maximum and
  not used: it is bounded only by $\sqrt{d+1}$ times the pointwise maximum error, where the maximum
  keeps the bound exactly.
- **The V-construction** (pixels as vertices) was not used: on the same field, corner-touching
  minima stay separate there, where the T-construction connects them, and the data are cell
  averages.
- **Negative result on vorticity order.** On the evidence run `results/persistence_distance_1793439285`,
  the per-frame order of neighbouring strengths on vorticity fails often under smoothing and
  low-pass, almost never by a reversal but by exact ties. Under `box_blur` the two harshest
  strengths give exactly the same value in 0.602 of frames and levels 2 and 3 in 0.13 (the
  reviewer's tie fractions for its three transitions were 0.019, 0.130 and 0.602), and no harsher strength ever scores below a milder one; similar ties occur under
  `gaussian_blur` (0.186, 0.13), `lowpass_butterworth` (0.422) and `lowpass_ideal` (0.348, beside
  0.025 reversals). Under coarsening the failures are mostly reversals, not ties: vorticity
  `coarsen` 2->3 reverses in 0.230 of frames and ties in 0.006; vorticity `coarsen_bandlimited`
  3->4 ties in 0.180 and reverses in 0.193; density `coarsen_bandlimited` 1->2 reverses in 0.286
  and ties in 0.025. Density shows ties only where the harness already flags repeated severities.
  The first record generalised "ties, not reversals" to coarsening, which the builder's own counts
  contradicted; that was corrected in the review round. The builder's explanation, not verified
  point by point: once both strengths have erased the feature that sets the bottleneck, its cost is
  half its lifetime at either, so the value plateaus. The card carries the reading (card, Results,
  Smoothing and Resolution loss).

## Evidence runs

1. **Smoke run**, before the pre-registration commit: `results/persistence_distance_1793437904`,
   `kinet_re5e4_dev` with `degradation=quick`, 2000 rows, 386 s. `make_report` rendered the new
   `companion_points` figure on both fields.
2. **Evidence run**: `results/persistence_distance_1793439285`, from
   `python evaluate.py metrics=[persistence_distance,kinetic_energy] dataset=kinet_re5e4 dataset.time.start=2000 dataset.time.reduction=50 paths.data_url=null`,
   started 11 s after the pre-registration commit 3f9d2b6. `kinetic_energy` rode along only so
   that velocity is read and vorticity recomputed from it
   ([issues/099](../../issues/099-derived-field-read-without-its-inputs.md)). 161 frames (2000 to
   10000), 18998 rows for this metric, default ladder; wall time 7684 s for the whole run
   (metrics 6718 s). It recorded `git.sha` 125c9a5 and `git.dirty` false, although it ran 3f9d2b6:
   `run_meta.json` takes the git state at the end of a run, and the three commits made during the
   run (601bc27, baffa0f, 125c9a5 on #29) changed only docstrings, the card, `refs.bib` and the
   report's colour scale, which `evaluate.py` does not run. The reviewer confirmed with
   `git diff 3f9d2b6 125c9a5` that no executed line differs. Outcome: every declared axis followed
   on both fields with direction +1 and `rho_ci_lo` > 0 (1.0 everywhere except vorticity
   `box_blur`, `coarsen_bandlimited`, `lowpass_butterworth` and `lowpass_ideal`, each 0.949);
   `translate_x` was blind on both fields as declared; `translate_subpixel`, not declared, was
   also listed blind on both. No rank correlation fell below the 0.90 advisory threshold.
   Impostor damage 0.585 on density and 0.502 on vorticity. No declared direction was
   contradicted. The review round changed no number the metric produces, so this run was not
   repeated.
3. **Reviewer's smoke comparison**: `metrics=[mse,persistence_distance]` on `kinet_re5e4_dev`
   with `degradation=quick`, written to the reviewer's scratch folder (`comparison_1793448635`,
   not kept); `make_report` finished "ok 26 · skipped 3", with `field_gallery` drawing mse's maps
   and `companion_points` drawing both diagrams.
4. **The run the card cites now** is `comparison_1793657627`, the pinned evidence refreshed over
   all kinet metrics in #35, not the bundle's own evidence run.

## Corrections to the rest of the repository

- **The idea page overstated Muszynski et al. 2019** as precedent for persistence diagrams; its
  method is a threshold sweep of connected regions that the authors call inspired by persistence.
  The card says so, and the correction reached `docs/ideas/README.md` in #29.
- **The builder's brief said** that `proposals/EXP-orchestrator-20261023-anisotropic-blur.md`
  names persistence among the metrics it would test. It does not (it names the two-point
  correlation, Reynolds-stress anisotropy, equivariance and Minkowski tensors), and a scalar
  diagram is not built to see anisotropy, so persistence was not added to it.
- **Where the deleted idea page's content went** (recorded so nothing was lost): its five
  references are all in `refs.bib` and cited on the card; its one pitfall (a diagram does not see
  position, so it belongs in a panel) is the card's first Limitation; its remark that the stability
  bound does not protect against a shift while periodic translation invariance does is in Reading
  the output and is tested; its Betti and Euler-curve definitions are the card's Equation (2) and
  the exported `betti_curves` and `euler_characteristic_curve`, and
  [docs/ideas/topology/minkowski_functionals.md](../../docs/ideas/topology/minkowski_functionals.md)
  now points to them. The issue that waited on a topology library (issues/074) was resolved and
  deleted in #29, and every link to the idea page was repointed at the built metric.

## Review round

The reviewer wrote 16 critiques (0 bugs, 3 likely future bugs, 4 theory or citation, 6
documentation, 3 minor) and edited no tracked file. The builder fixed 13, rejected 2 as code
changes with issues drafted, and handled 1 by documentation. The critiques about code behaviour,
shared docstrings and tests (critiques on the ensemble clean level, the reused context, the 3-D
refusal, the axis and stability tests, the `COMPANION_KEY` docstrings, the panel order and the
two-field companion) are in code_notes.md under Bugs and fixes and Tests. The rest:

- **The stability bound was cited to a theorem whose hypotheses the T-construction does not meet.**
  Cohen-Steiner et al.'s Main Theorem is stated for continuous tame functions, and a cell-wise
  constant field is not continuous. Fixed in commit 8b6b608 on #29: Equation (5) is now cited to
  Skraba & Turner v7, Theorem 4.6(i), taken to $p \to \infty$, with the limit and the
  minimum-over-cofaces step labelled the bundle's own; the 2005 Main Theorem is kept as the
  precedent only. The builder noted that Theorem 4.6 itself names no range of $p$ (their Sect. 1
  gives $1 \le p \le \infty$), so the card states the limit instead of leaning on Sect. 1. The
  reviewer's confidence that Theorem 4.6(i) holds at $p = \infty$ was medium; it did not read the
  proof of their Lemma 4.2 for that case. A search found the same mistake nowhere else in the
  repository.
- **The Betti-curve count was cited to the k-Triangle Lemma outside its hypotheses.** The lemma
  needs $x < y$, both away from critical values, so it cannot be taken at $x = y = t$, and its
  closed quadrant would count a point with $d = t$, the opposite of the code's $t < d$. The code
  was right. Fixed in 8b6b608: cited to Skraba & Turner v7, Sect. 2 and Theorem 2.3, with the
  half-open $[b, d)$ step labelled the bundle's own. The Betti-curve proposal carried the same
  citation and was corrected the same way.
- **The convention for points at infinity was attributed to a paper that does not state it.**
  Cohen-Steiner et al. 2005 give no rule for the distance between two points at infinity
  ($\infty - \infty$ is undefined); Skraba & Turner v7, Definition 2.4, state it, and the reviewer
  measured that gudhi follows it ($[[0, \infty]]$ against $[[0.3, \infty]]$ gives 0.3; unequal
  counts give $\infty$; the optimal pairing between two such points is chosen, 0.2). Fixed in
  8b6b608.
- **The card claimed more about Martinez et al. 2026 than its abstract supports** ("none compared
  two fields by a diagram distance"). Fixed in 8b6b608: the Limitations now say Martinez et al.
  may be the nearest precedent and that whether their distance is between diagrams is not known.
  A second attempt to read the PDF failed (CID-encoded fonts).
- **Two sources were recorded as read in full but were read through a summarising fetch, and the
  Skraba & Turner version was not pinned.** The reviewer checked every locator itself against
  the full arXiv HTML and found all correct. The builder re-read them line by line, so the
  "full text" reading now rests on that check, and `refs.bib` pins arXiv v7 (10 Jul 2025).
- **The giotto-tda record named a source file that was never fetched.** Only the documentation
  page was fetched; the record was corrected. Nothing depended on it.
- **The tie reading was over-generalised to coarsening.** See Rejected formulations and negative
  results; the card's Resolution-loss reading now says those failures are mostly reversals at the
  mildest strengths.
- **The card's recorded commit is not the code that produced the numbers.** Confirmed harmless
  here (see Evidence runs). Rejected as a card edit, since the run block is generated; the
  mechanism, which would hide a real mid-run code change from the pre-registration check, was
  drafted as an issue and is now
  [issues/115](../../issues/115-run-meta-records-the-git-state-at-the-end.md).
- **The coarsening prose could be read as contradicting the Profile table.** "Far less" was true
  of damage at the harshest strength (`coarsen_bandlimited` 0.0848 against 0.325 for `coarsen` on
  density) while the Profile table ranks `coarsen_bandlimited` highest per unit of field change
  (31.3 against 5.2). Fixed in 8b6b608 by saying which normalisation each statement uses.

The reviewer also answered the orchestrator's question on the Cohen-Steiner copy (it is the SoCG
2005 version, and every cited location exists under that name and number), and checked and found
sound: the essential-point counts, (1, 2, 1) on the torus, (1, 1) on a periodic 1-D grid and
(1, 3, 3, 1) on a 3-torus, so the distance is never infinite; the mean-field anchor, where on a
constant candidate the metric equals `max_error` exactly (0.33823... both ways), because the
points that never die are born at the global extremes; the explanation of the `translate_subpixel`
non-monotonicity (the three largest severities, 1.0, 2.0 and 4.0 cells, are whole cells, and the
reversal at 0.5 -> 1.0 occurs in every frame on both fields); the pre-registration against the
outcome; and all nine numbers in the Results prose (0.398, 0.949, 1.04, -0.698, 0.627, 0.652,
0.584, 0.585, 0.502) against the generated tables. It did not check the builder's readings of
Muszynski 2019 or Smith 2024 against their full texts.

## Open questions and follow-ups

- **Wasserstein distance between diagrams**:
  [proposals/MTR-persistence_distance-wasserstein-diagram-distance.md](../../proposals/MTR-persistence_distance-wasserstein-diagram-distance.md).
- **Betti-curve distance**, an $L^1$ distance between Betti curves over thresholds, a pairing-free
  summary of the same diagrams (the Euler-characteristic version belongs to the
  Minkowski-functionals idea; `betti_curves` and `euler_characteristic_curve` are exported for it):
  [proposals/MTR-persistence_distance-betti-curve-distance.md](../../proposals/MTR-persistence_distance-betti-curve-distance.md).
- **Signed vortex census**: on 2-D vorticity, the H0 diagram of $\omega$ records one sign of
  vortex core and that of $-\omega$ the other, so reporting each separately would say which sign a
  model gets wrong, which the registered maximum hides; also a threshold-free detector for the
  eddy census ([issues/073](../../issues/073-eddy-census-waits-on-a-detector.md)):
  [proposals/MTR-persistence_distance-signed-vortex-census.md](../../proposals/MTR-persistence_distance-signed-vortex-census.md).
- **Topological simplification as a degradation** (Edelsbrunner, Morozov & Pascucci 2006), which
  would remove the weakest features by a known amount and give the metric a known value, the
  largest removed half-lifetime:
  [proposals/EXP-persistence_distance-topological-simplification.md](../../proposals/EXP-persistence_distance-topological-simplification.md).
- **Spurious-feature injection**: no current degradation adds a few strong spurious features;
  isolated wells of known depth $h$ would test the metric directly, with the bottleneck expected
  near $h/2$ where a well lands on flat ground (the builder's reasoning, to be measured):
  [proposals/EXP-persistence_distance-spurious-feature-injection.md](../../proposals/EXP-persistence_distance-spurious-feature-injection.md).
- **The run records the git state at its end**:
  [issues/115](../../issues/115-run-meta-records-the-git-state-at-the-end.md).
- **Two harness gaps found in the review round**, the context cache that trusts one context per
  frame and the metric error that stops the whole run: [issues/116](../../issues/116-context-cache-trusts-one-context-per-frame.md)
  and [issues/117](../../issues/117-one-metric-error-stops-the-run.md), described in
  code_notes.md.
- **The cause of the vorticity ties** is not routed; recording which point pair attains the
  bottleneck would test it.

## For the next agent

- The equation and section numbers of Bleile et al. 2022 and Skraba & Turner 2020 were first seen
  through a summarising fetch; they were then checked line by line against text extractions of the
  full arXiv HTML, not against a PDF. The Cohen-Steiner locators come from a text extraction of the
  SoCG 2005 author copy; the DCG 2007 journal version was never opened.
- The $p \to \infty$ limit of Theorem 4.6(i) and the step from cells of the complex to grid cells
  are the bundle's own; the reviewer was only of medium confidence that the theorem covers
  $p = \infty$.
- Martinez et al. 2026 is read as an abstract only; it may be the nearest precedent for comparing
  two fields by persistence.
- The explanation of the vorticity ties (the bottleneck set by a feature both strengths erased) is
  an interpretation. The first check would be to record which point pair attains the bottleneck
  on a tied frame.
- The builder's reading that the coefficient field does not change any 2-D diagram was by
  reasoning (subcomplexes of the torus have torsion-free homology); the reviewer then tested it
  on 200 random 2-D and 3-D fields over $\mathbb{Z}/2$, $\mathbb{Z}/3$ and $\mathbb{Z}/11$ and found identical diagrams.
