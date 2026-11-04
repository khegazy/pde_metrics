# Code notes: spectral_energy_flux

This is the coding record of the build in pull request #26, condensed from the builder's and the
reviewer's records. The research record is in [research_notes.md](research_notes.md).

## Summary

`metric.py` holds the metric `spectral_energy_flux` (the relative L2 distance between two flux
curves) and its one-field curve companion `energy_flux_curve` (the flux at the octave
wavenumbers). It reuses `spectrum_l2`'s shells and binning, the repository's spectral derivative
and the degradations' Fourier filter. The build changed two pieces of shared code: `spectrum_l2`
gained an optional co-spectrum argument and a single shell definition, and the contract
blur-ladder test gained a rule for metrics that are NaN on the noise-free field. The review round
rewrote the curve to a conserving form and replaced an exact-zero NaN guard with a round-off
bound. The bundle was merged with every CI check passing.

## Implementation

- **The curve.** `energy_flux_curve` computes
  $\Pi(K) = \langle u^{<K}\cdot\nabla\cdot(uu)\rangle - \tfrac12\langle\lvert u^{<K}\rvert^2\,\nabla\cdot u^{<K}\rangle$
  (Aluie 2013, Sect. 4.1, at uniform density; card, Definition).
  1. The momentum nonlinearity $D_i = \sum_j\partial_j(u_iu_j)$ is formed in physical space, with
     each derivative taken by `fmeval/external/kinet_spectral.py::spectral_derivative` on the
     grid's spacing.
  2. The first term is Parseval's co-spectrum $\mathrm{Re}[\hat u^*\cdot\hat D]/M^2$, binned into
     unit shells by `radial_energy_spectrum(velocity, ctx, other=nonlinear)` and summed
     cumulatively.
  3. The second term is formed per shell, from one real forward transform of the velocity: for
     each $K$ the half-spectrum is masked to `radial_shells(shape) <= K` (Aluie's sharp filter,
     his Eq. 21) and inverted for $u^{<K}$, and the masked $i\mathbf{k}\cdot\hat u$ is inverted
     for its divergence, with the Nyquist wavenumber zeroed on each even axis, as the real part
     of `spectral_derivative`'s inverse transform zeroes it. The code then takes the mean of
     $\lvert u^{<K}\rvert^2$ times that divergence. Until 2026-11-04 this was done per octave
     with `degradations/_shared/filters.py::_apply_filter` and `spectral_derivative`; the two
     agree to $2.4\times10^{-13}$ in the registered number on the evidence trajectory (below).
  4. The curve runs over every shell $K = 1 \dots N/2$, half the smallest grid side. The filter
     keeps the shells up to and including $K$, so $\Pi(K)$ is the flux through
     $\lvert k\rvert = K + \tfrac12$. The companion declares `analysed` at the octaves
     (`spectrum_l2.metric.OCTAVES`), and the metric reads the octaves out of the dense curve.
- **The number.** `spectral_energy_flux` refuses differing shapes. It takes the candidate's curve
  from `ctx.cache[COMPANION_KEY]` when the pipeline has already computed it. It caches the
  reference's curve under `REFERENCE_FLUX` once per frame. It returns
  $\lVert\Pi_{cand} - \Pi_{ref}\rVert/\lVert\Pi_{ref}\rVert$, or NaN when $\lVert\Pi_{ref}\rVert$ is
  at most $\epsilon_{mach}\,\max\lvert u_{ref}\rvert^3\,\pi/\min\Delta x$. That bound is machine
  epsilon times the largest flux the field's own speed and the grid's highest wavenumber allow. It
  is the agent's own, labelled so in the docstring and on the card, and fixed once. It is a
  dimensionless rule in the grid spacing.
- **Constants**, as listed in the PR body.
  - **2**, used three ways: the exponent in Parseval's normalisation $1/M^2$ of the unnormalised
    FFT (Alexakis & Biferale 2018, Eq. 18, through Parseval); the ½ of the continuity-equation
    term (Aluie 2013, Sect. 4.1), written `/ 2`; and half the smallest grid side, which is also the
    base of the octave sampling $2^n$ (the repository's convention, issue 105).
  - **3**, the cube in the round-off bound, because the flux is cubic in the velocity.
- **Decorator.**
  - `fields=("velocity",)`.
  - `differentiable=True`: the code is smooth away from identical curves, as `spectrum_l2` is.
  - `cost="moderate"`: about 0.1 s per curve. The first definition declared "cheap".
  - `higher_is_better=False`.
  - `symmetric=False`, because the reference's curve sets the scale.
  - `units="dimensionless"`.
  - `requires_periodic=True`, because of the FFTs and spectral derivatives.

  The companion is `kind="curve"` with coordinate `("wavenumber", "cycles per domain")`. The
  decorator's default `mean` reduction is unused.
- **Why octaves for the number and the tables.** The harness analyses each coordinate it is given
  as a metric of its own, at 2.3 to 3.0 s per coordinate and field (CRITIQUE finding 12 of the
  2026-11-03 plan), and renders one table column per coordinate. Since 2026-11-04 a curve can
  store every coordinate for its figure and name the few the analysis reads (`analysed`), so
  the curve is dense and the tables keep the octaves. The number's octave sampling remains a
  convention ([issues/105](../../issues/105-spectral-energy-flux-summary-is-a-convention.md)).
- **Changes outside the bundle.**
  - `metrics/spectrum_l2/metric.py`, under the exception in AGENTS.md §3.2.
    `radial_energy_spectrum` gained an optional `other` argument that bins the co-spectrum
    $\mathrm{Re}[\overline{Fa}\,Fb]$ into the same shells; without it, the code path is the
    unchanged expression. In the review the shells $\mathrm{rint}(\lvert k\rvert)$ were defined
    once, in `radial_shells(shape)`, which both `radial_energy_spectrum` and the flux's filter use.
    Its output is identical to the former inline expression on four grids. The reviewer found the
    default path bitwise identical to main's on $(16,8)$, $(33,20)$ and $(6,5,4)$ grids. The
    orchestrator found `spectrum_l2`'s spectrum and value bitwise identical on 32×32, 2×30×34,
    3×64×16 and 16×16×8. So the card of `spectrum_l2` was not changed, and the PR body carried
    the `[docs-unchanged]` waiver for CI's check that an implementation change carries its card.
  - `tests/test_metric_contract.py::test_monotone_on_synthetic_blur_ladder`: the rule for a
    pairwise metric that is NaN on the noise-free field (Tests).
  - `tests/test_cards.py`: the metric joined the cheap catalog query in the first round, and left
    it when the review made the cost moderate.
  - `docs/catalog.json` was regenerated.

## Tests

`metrics/spectral_energy_flux/test_metric.py`:

- `test_worked_example_matches_the_card`: $u_x = \sin kx + a\sin 2kx$, $u_y = 0$, on an 8 by 4
  grid. With the conserving flux, $\Pi(1) = -ak/2 = -\pi/8$, and halving the short wave gives a
  metric of 0.5. Under the first, advective definition the hand-derived value was
  $\Pi(1) = -ak/4$, with $\Pi(2) = 0$; the reviewer re-derived it by hand from
  $ff' = k[-(a/2)\sin kx + (1/2)\sin 2kx + (3a/2)\sin 3kx + a^2\sin 4kx]$.
- `test_the_nonlinear_term_conserves_energy_on_a_divergence_free_field`: the flux through a
  wavenumber outside every mode of the field is zero.
- `test_the_flux_of_a_divergent_velocity_also_sums_to_zero` (added in the review, parametrised
  over the compressive amplitude): the advective form would end at
  $-\langle\nabla\cdot u\,\lvert u\rvert^2\rangle/2$, while the unsubtracted flux ends at zero.
- `test_on_a_divergence_free_field_the_flux_is_the_advective_form` (added in the review): the curve
  against an independent direct sum of Alexakis & Biferale Eq. 18, written in the test in
  physical space with an explicit sharp filter. They agree to $10^{-12}$.
- `test_the_flux_ignores_translation_and_a_uniform_velocity`: translation and a uniform velocity
  leave the curve unchanged. The review parametrised this and the spacing test over a divergent
  field as well.
- `test_the_curve_carries_an_inverse_length_and_the_number_none`: doubling the cell size halves the
  curve and leaves the number unchanged.
- `test_a_uniform_candidate_scores_one_and_a_uniform_reference_nan`, parametrised over shapes; the
  30 by 34 case was added in the review. A uniform candidate scores 1. A uniform reference is NaN,
  including on 30 by 34, where the floating-point mean of 0.1 is inexact.
- `test_a_reference_whose_flux_is_round_off_scores_nan`: the steady Taylor-Green vortex, whose
  advection is a pure gradient, gives NaN.
- `test_a_velocity_without_one_component_per_axis_is_refused`.

**Choosing a test field.** A random divergence-free velocity band-limited to $\lvert k\rvert \le 2$
on 16 by 16 cells carries zero flux at every shell ($10^{-17}$). By the agent's own reasoning, not
checked against a source, this is because its interacting triads either lie inside one shell or
have two legs of equal magnitude. In a 2D triad that conserves energy and enstrophy, the leg of
different magnitude then gains nothing, leaving only exchanges between legs of one shell. So the
tests use a wider band: $\lvert k\rvert \le 5$ on 32 by 32 gives fluxes of order $10^{-2}$, and zero
beyond the last mode.

**Sanity checks before the tests** (a scratch script, not kept):
- a one-triad compressive velocity reproduced the then-current $\Pi(1) = -ak/4$ to $10^{-16}$;
- a band-limited divergence-free field had zero flux beyond its last mode ($10^{-17}$ against
  $10^{-2}$);
- translation and a uniform velocity changed the curve by $10^{-17}$;
- spacing 2 halved the curve;
- the reviewer matched these outputs in the transcript, including the Taylor-Green values 0.99999,
  56.6 and $1.39\times10^{17}$ (the last being the huge, meaningless score of a round-off
  reference, Bugs and fixes).

**The contract blur-ladder test.** After the review's rewrite this test failed with NaN at every
level. The noise-free synthetic velocity (`tests/conftest.py::synthetic_field` with `noise=0`, 16
by 8, two channels) carries no energy transfer between shells. Its conserving flux is
$-5\times10^{-17}$, $-1\times10^{-17}$ and $-7\times10^{-17}$ at octaves 1, 2 and 4, so the distance
is undefined there. The old, non-conserving flux had passed only through its divergence residual.
Without a NaN guard, the ladder values would have been round-off ratios (1.0007, 0.987, 0.9986,
1.0000), not monotone. The agent did not declare the metric non-monotone, because on fields with
interacting triads it is monotone. Instead the test now starts from the default, mildly noisy
field (noise 0.05, fluxes of order $10^{-3}$ to $10^{-2}$) for any pairwise metric that is NaN on
the noise-free one. On that field the ladder $[0, 0.5, 1, 2, 4]$ gives $[0, 0.65, 0.99, 1.00, 1.00]$
for seed 0, and it is monotone for seeds 0, 1 and 2. The test comment states the rule generally,
and no other registered metric is NaN on that field.

Verification: `agent_verify.sh` exited 0 at every step before the first PR (pytest 1881 passed),
and before the review's evidence commit 8dd88cd on #26 (pytest 1885 passed, 201 skipped, 9
deselected, 2 xfailed). It passed again on 2026-10-31 with the card-coupling check added. The
reviewer ran the bundle's tests, `spectrum_l2`'s, the contract tests, `test_cards.py` and
`test_documentation.py` with no failures.

## Bugs and fixes

- **The flux form was not conservative for a divergent velocity.** The research side is in
  research_notes.md, Review round. The code fix, in commit c33f769 on #26, changed
  `energy_flux_curve` from the advective form to Aluie's unsubtracted flux and added
  `radial_shells`. With the old `metric.py` restored by
  `git show HEAD:metrics/spectral_energy_flux/metric.py > metrics/spectral_energy_flux/metric.py`,
  `python -m pytest -q metrics/spectral_energy_flux -p no:cacheprovider` gave "3 failed, 7 passed".
  The failures were the worked example, the divergent-field conservation test at amplitude 0.5,
  and the uniform reference on 30 by 34. With the fix it gave "10 passed".
- **The NaN guard needed an exact floating-point mean** (likely future bug; high confidence). The
  first guard returned NaN only when the reference curve's norm was exactly 0.0. The fluctuation
  subtracts the mean, and on most grids the mean of a non-dyadic constant is inexact. So a uniform
  reference $(0.1, 0.7)$ gave NaN on 32 by 32 but $3.59\times10^{48}$ on 30 by 34; the old test
  passed only because it used 0.5 on 32 by 32. The first round had seen a related symptom: the
  Taylor-Green vortex has zero flux in theory and about $10^{-19}$ in floating point (measured on
  16 by 16 and 32 by 32), so as a reference it gave a huge, meaningless value. The agent had then
  kept the exact-zero guard, judging that a round-off threshold would be a tuned literal, and
  stated it as a limitation on the card. **Fix** in c33f769: the round-off bound under
  Implementation, which catches both cases and removed the card's former first Limitation. Its
  regression test is the 30 by 34 case.
- **The same guard elsewhere.** Both `spectrum_l2` and `nrmse` guard with an exact comparison of a
  scale taken about the spatial mean. On a uniform 0.7 reference against a standard-normal
  candidate, `spectrum_l2` returns $1.92\times10^{31}$ on 32 by 32 and $2.21\times10^{31}$ on 30 by
  34, and `nrmse` returns $1.10\times10^{16}$ on 30 by 34; both promise NaN. Neither is this
  bundle's code, so they were recorded as
  [issues/110](../../issues/110-uniform-reference-nan-guard-needs-round-off-bound.md), not fixed.

## Performance

- **Per curve:** 0.096 s on a 256 by 256 random field (mean of 5 calls) after the review, against
  about 0.01 s for the first definition. The extra cost is a filter and a divergence per octave.
  This is why `cost` became "moderate".
- **Evidence runs on 161 frames of the 256 grid:**
  - the first full run, `results/spectral_energy_flux_1793354140`, took 1096 s (recorded dirty,
    unused);
  - the first clean run, `results/spectral_energy_flux_1793355291`, produced 9499 rows in 777 s,
    with 108 s of metric time;
  - the run after the review, `results/spectral_energy_flux_1793391588`, produced 9499 rows in
    1312 s, of which 640 s was the metric and 662 s the degradations.
- **Smoke run** `results/spectral_energy_flux_1793354039`: 1000 rows in 36 s.

- **Dense curve (2026-11-04).** One curve on a 256 by 256 kinet frame (frames 2000, 6000 and
  10000 of `kinet_re5e4`, a shared login node): 0.161 s for the octave version, 0.341 s for the
  dense one. Median per row in the refactor-gate runs on `kinet_re5e4_dev` at 256 by 256: 0.065 s
  before, 0.153 s after. A dense curve with the octave code's filter (`_apply_filter` and
  `spectral_derivative` per shell) took 0.91 s on a random 256 by 256 field, against 0.15 s for
  the real-transform form kept.

## Tooling and environment problems

- **No PDF reader.** There was no pdftotext, pypdf or poppler. Every source was first read as HTML
  on ar5iv through the fetch tool, which answers through a summarising model and reads at most
  100,000 characters per call. In the review the arXiv TeX sources were downloaded and unpacked,
  and no code from them was run.
- **Scratch scripts imported the wrong `metrics` package.** A scratch script run with plain
  `python` imported the main checkout's package. Running scripts through `runpy` from the worktree root put
  the worktree first on `sys.path`.
- **A sandbox refusal.** A compound shell command that wrote several findings files through
  heredocs was refused, so each file was written with the file tool.
- **A dirty evidence run.** `evaluate.py` reads the git status when it writes `run_meta` at the
  end of the run. Editing tracked files while the first full run ran made it dirty. It was
  committed and re-run on a clean tree, and the dirty folder was named as unused.
- **CI's card-coupling check.** On 2026-10-31 CI's "an implementation change carries its card"
  check failed, because the branch changed `metrics/spectrum_l2/metric.py` without its card. The
  agent chose the `[docs-unchanged]` waiver in the PR body over a card edit (Implementation). CI
  does not run on a body edit, so the agent pushed an empty commit, e979558 on #26, without force.
  On that commit the card-coupling, ruff, pytest and mkdocs checks succeeded, and the Pages
  publish was skipped, as it is off main.
- **An interrupted session.** After the orchestrator session was interrupted, the agent lost track
  of edits it had made itself and took them for another agent's. The orchestrator confirmed from
  the transcript (20:10-20:13 UTC) that every edit was its own, and the agent re-read `git status`
  and the diffs before going on.
- **Lost scratch.** The recreated worktree had lost a scratch script, `peek.py`, which reads a
  run's clean companion rows; it was rewritten and not kept.
- **No `agent-metric` label** existed on GitHub, and `latexmk` was absent, which was not needed.

## For the next agent

- The aliasing is real: with exact products on a doubled grid, the noise score roughly halves at
  amplitude 0.5. Dealiasing was not added, because it would change the metric's definition
  (research_notes.md, Method choices).
- The Nyquist mode's derivative is zero through the vendored spectral derivative. Its effect was
  not measured in isolation.
- The corner shells beyond $N/2$ enter only through the flux out of the last shell, $N/2$. Their weight
  on noisy fields was not measured.
- The round-off bound is the agent's own. A reference whose genuine flux lies below it is treated
  as carrying none (card, Limitations).
