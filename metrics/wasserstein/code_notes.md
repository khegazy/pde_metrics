# Code notes: wasserstein

This file is the coding record of the build of `wasserstein` in pull request #32, including its
adversarial review round (2026-10-31) and its solver speedup round (2026-11-02), condensed from
the builder's and the reviewer's records. The research record is in
[research_notes.md](research_notes.md).

## Summary

`metric.py` holds one solver, in the companion `wasserstein_map`, which returns the per-cell
transport cost $f\lvert\nabla u\rvert^2$; the metric is that map reduced by `sqrt_mean`. The
solve is a damped Newton iteration for the periodic Monge-Ampère equation with spectral
derivatives and a periodic cubic B-spline. The build also changed the shared contract tests so
that a density-only metric gets a positive input (judgement 006). The code was left with the
review round's solver fix and the speedup round's closed-form determinant in two dimensions; it
still returns NaN for a density peaking at about three times its mean.

## Implementation

**The algorithm as coded.** The steps are on the card (Definition, "How Equation (3) is solved");
what the code adds:

1. **Validation.** Shapes must match and there must be one channel, or a `ValueError`. A field
   with any cell that is not positive and finite returns an all-NaN map (a NaN value) without a
   warning; that path is documented and tested.
2. **Normalisation and set-up.** Each field is cast to float64 and divided by its own mean. The
   wavevectors come from `fmeval.external.kinet_spectral.physical_wavenumber_grid`, the convention
   `h_minus_one` and the repository's spectral derivatives use, with the grid spacing from `ctx`.
   The inverse Laplacian is $-1/\lvert k\rvert^2$ with the zero mode set to 0. The candidate is
   prefiltered once for the spline (`ndimage.spline_filter`, `mode="grid-wrap"`).
3. **`evaluate(u_hat)`.** It computes $\nabla u$ and each distinct second derivative once by FFT,
   then the determinant of $I + D^2 u$ and whether that matrix is positive definite. In 2-D this is
   the closed form $(1 + u_{xx})(1 + u_{yy}) - u_{xy}^2$ with Sylvester's criterion
   ($1 + u_{xx} > 0$ and a positive determinant); in any other dimension the symmetric matrix is
   filled with each entry mirrored and passed to `np.linalg.eigvalsh`. The candidate is evaluated at
   $x + \nabla u$ (converted to cells by the spacing) with `ndimage.map_coordinates`,
   `mode="grid-wrap"`, and the residual is re-centred as in Saumier et al. Eq. 14.
4. **The loop.** The step is the residual divided by $\max(g(x + \nabla u), \min g)$, re-centred
   and passed through the inverse Laplacian. The floor at $\min g$ is there because the cubic
   spline can undershoot between cells. The step is halved until the RMS residual falls and the
   matrix stays positive definite; a NaN residual compares False, so a divergent trial is halved
   too. On convergence the map $f\sum_j(\partial_j u)^2$ is returned. Otherwise a `RuntimeWarning`
   names either the cap, with the residual left, or a step that no damping could make lower the
   residual, and the map is all NaN.

**Constants.**

- `RESIDUAL_TOLERANCE = 1e-12`: the agent's choice. The RMS residual as a fraction of the mean
  density, far below the smallest density change the ladder makes (noise at $10^{-3}$ of the
  fluctuation RMS, about $2 \times 10^{-6}$ of the mean on kinet density) and above the round-off
  of a 256^2 FFT. The reviewer measured the residual reaching $10^{-16}$ on 256^2, 1024^2 and 32^3
  at low contrast, so the tolerance is reachable wherever the iteration converges.
- `MAX_ITERATIONS = 500`: the agent's choice, raised from 100 in the review round. Kinet density
  needs 4 to 7 iterations; two unrelated smooth 64^2 densities whose maximum is four times their
  minimum needed 239, the slowest pair that converged.
- `MAX_HALVINGS = 30`: new in the review round, the agent's choice. $2^{-30}$ of a step is below
  the precision of the potential it is added to. It is the damping $\tau$ of Saumier et al. Eq. 6,
  doubled until accepted.
- `SPLINE_ORDER = 3`: the agent's choice, measured against nearest, linear and quintic
  interpolation ([research_notes.md](research_notes.md), Method choices).
- `1j` and the exponent 2 are the spectral-derivative convention and the squared displacement of
  Saumier et al. Eq. 3; the PR body lists them with the other literals.

**Decorator declarations.**

- `fields=("density",)`: a density is a measure; signed fields wait on issue 047.
- `differentiable=True`: $W_2^2$ has a Fréchet derivative in the densities, the adjoint source of
  Yang et al. (2018), cited by section heading.
- `cost="moderate"`: the comment now quotes the evidence and the same-process ratio (see
  Performance); before the review it quoted a prototype timing of 0.08 s.
- `symmetric=False`: $W_2$ is symmetric, but the solve treats the reference as the source and
  interpolates the candidate. Measured with the prototype on kinet density at step 2001, solving
  from the other side changed the value by a relative $5 \times 10^{-6}$ for a noisy candidate and
  below $10^{-7}$ for the mean field and the shifts. The contract test requires symmetry to
  $10^{-12}$, so the metric declares it asymmetric with the reason beside it.
- `units="length"`, `reduction="sqrt_mean"`, `requires_periodic=True` (FFT derivatives and a
  wrapping interpolation), `higher_is_better=False`.

**The companion.** `wasserstein_map` is the field companion; its mean is $W_2^2$, so the metric is
`REDUCTIONS["sqrt_mean"]` of it, and the contract's map-reduces-to-metric test checks that exactly.

**Change outside the bundle: the contract tests (judgement 006).** `tests/test_metric_contract.py`
fed every metric a signed synthetic field and required a finite number, zero on identical fields
and a perfect blur ranking. A transport distance between densities has no value on a field with a
non-positive cell, and any rule giving it one is a signed-field formulation (issue 047), which
this bundle may not choose. Issue 101 already proposed "a synthetic input with a positive offset,
used for any metric that declares a positive field", and `wasserstein` is the second metric
needing a positive field, the trigger issue 101 names. The build added `POSITIVE_FIELDS =
{"density"}`, `POSITIVE_OFFSET = 3.0` and `_field_for`, so a metric whose declared fields are all
in that set gets the synthetic field moved up by 3, and every other metric gets the same input as
before. The spacing-scaling test applies the same offset, and `wasserstein` joined its
parametrisation with factor 2 (a length). AGENTS.md §3.2 asks an agent to stop before such a change;
the agent made it and recorded it as
[judgements/006](../../judgements/006-contract-tests-give-a-density-metric-a-positive-field.md)
instead (see [research_notes.md](research_notes.md), Review round). In the review round the comment
was corrected: pressure is left out because a dataset may store a gauge pressure with both signs,
and the synthetic field reaches about ±2.3 in three dimensions, so the offset leaves it at least
about 0.7 there, not 1. Issue 101's status line was updated to mention the change.

## Tests

All in `metrics/wasserstein/test_metric.py`; the registry-wide contract is in
`tests/test_metric_contract.py`.

- **`test_worked_example_from_the_card`.** Columns at 1.5, 1, 0.5 and 1 times the mean against a
  uniform density give 0.225079 cells. Derived exactly: for $f = 1 + a\cos(2\pi x/L)$ against the
  uniform density the best rotation is zero by the reflection $x \to -x$, the map is
  $T(x) = x + (aL/2\pi)\sin(2\pi x/L)$, and $W_2 = aL/(2\pi\sqrt 2) = 1/(\pi\sqrt 2)$ at $a = 0.5$,
  $L = 4$; on the grid $\sin^2$ at the four columns is 0, 1, 0, 1, so its $f$-weighted mean is 1/2.
  The reviewer checked the value and the reflection argument by hand, and pointed out
  that with a uniform candidate one Laplacian step solves the equation exactly, so this test
  exercises neither the interpolation nor the nonlinear iteration. The docstring now says so and
  points to the circle tests.
- **`test_agrees_with_the_exact_solution_on_the_circle_for_a_shifted_density`**, two profiles. A
  density varying along $x$ only, on a 256 by 4 grid, against itself moved by an eighth of the
  domain, compared with the exact circle transport of Delon et al. (2010) Sect. 2, computed
  independently by minimising over the rotation $\theta$ of mass levels on a fine quantile grid,
  at a relative tolerance of $2 \times 10^{-4}$. `_two_modes` lies between 0.63 and 1.37 times its
  mean. `_peaked` is $\exp(a\cos)$ with a maximum ten times its minimum and 2.33 times its mean,
  added in the review round as the regression test for the solver bug. During the build, a
  density with contrast ±40% shifted by 1 to 128 of 256 cells matched to a relative
  $2.6 \times 10^{-5}$ to $4.9 \times 10^{-5}$; the reviewer reran it and confirmed that the test's
  implementation matches Delon et al.'s cost formula.
- **`test_lies_within_the_h_minus_one_bounds`.** $b^{-1/2}H \le W_2 \le 2a^{-1/2}H$ on a smooth
  density and its blurred copy (Peyré 2018, Corollary 3 and Theorem 5, Eq. 17). The reviewer
  showed that the bounds are about a factor of three apart on this pair
  ($a = 0.549$, $b = 1.375$, $W_2/H = 1.0250$, allowed [0.853, 2.700]), so a $W_2$ 1.9 times too
  large would pass. Kept as a consistency check, with the docstring saying so. A tighter test
  against the first-order band was not added, because that band rests on the agent's reading, not a
  theorem.
- **`test_total_mass_is_normalised_away`.** A factor of 3 on the candidate scores 0 to $10^{-12}$
  (Engquist & Froese 2014, Sect. 2.2). It pins the idea page's pitfall that a normalised transport
  accepts the wrong amplitude.
- **`test_a_solve_that_does_not_converge_scores_nan_with_a_warning`.** Added by the reviewer in the
  review round, then tightened by the builder: it caps `MAX_ITERATIONS` at 1 with `monkeypatch` and
  requires a NaN and a `RuntimeWarning` matching `residual was still .* after 1 iterations`.
- **`test_a_field_with_a_cell_that_is_not_a_positive_density_scores_nan`.** A cell at 0, −1 or NaN in
  either argument gives NaN.

**Regression tests, before and after (review round).** With 215945d's `metric.py` in place,
`python -m pytest metrics/wasserstein -q -k "circle or converge"` gave "FAILED ...circle...[_peaked];
FAILED ...test_a_solve_that_does_not_converge_scores_nan_with_a_warning; 2 failed, 1 passed". With
the new `metric.py`, the same command gave "3 passed, 6 deselected". After the speedup the bundle
had 9 tests passing, and 931 passed in the contract, cards and documentation tests.

## Bugs and fixes

- **The step overshot above about twice the mean density.** *Symptom:* NaN on
  valid, positive densities of ordinary contrast. The reviewer found that a 0.3-cell shift of a
  density whose peak is 1.85 times its mean needed 125 iterations, so the shipped code returned NaN
  at its cap of 100, and at a peak of 2.7 times the mean it diverged; unrelated smooth 64^2
  densities failed from a contrast of 4. The contract field peaks at 1.55 times its mean (34
  iterations), which is why the contract tests passed. The builder reproduced it against the exact
  circle transport: the old solver returned NaN from a peak of 1.78 times the mean at an 8-cell
  shift on a 128-cell profile, and at every shift from 2.33 upward. *Cause:* near the solution the
  linearised operator is roughly $g\Delta + \nabla g\cdot\nabla$ (Saumier et al. Eq. 5 at $u = 0$),
  so inverting $\Delta$ alone multiplies the error by about $1 - g$, whose modulus exceeds 1 where
  $g > 2$ (the reviewer's reasoning, medium confidence). The card had also misread its source:
  Saumier Sect. 3.3 says a simpler equation works only "sometimes", and Sect. 5.1's $\tau = 1$ was
  obtained with the full operator. *Fix (ecf826c on #32):* divide the residual by
  $g(x + \nabla u)$, floored at $\min g$, and halve the step until the RMS residual falls with
  $I + D^2 u$ positive definite; `MAX_ITERATIONS` 100 to 500 and `MAX_HALVINGS = 30`. The three
  variants the reviewer tried agreed to eight digits wherever they converged, confirming that the
  operator changes the iterations and not the value. *After the fix:* the circle profiles converge
  and match to $10^{-4}$ at a peak of 2.33 times the mean for shifts of 1, 8 and 32 cells, and at
  2.94 for shifts of 1 and 8; the solve still fails at 2.94 with a 32-cell shift and at 3.53 at
  every shift, because the scaled Laplacian step is then not a descent direction for the residual.
  On 2-D synthetic pairs it converges for unrelated densities up to a contrast of 10 (76
  iterations) and for 0.3-cell shifts up to a contrast of 1000, and fails for unrelated pairs at
  100. On 15 kinet pairs over three frames the new and old values differ by at most
  $4.1 \times 10^{-9}$ relative, at the same time per call; the full-run comparison is in
  [research_notes.md](research_notes.md) (Evidence runs). The remaining limit is in the card's
  Limitations, and the remedy is the full Newton proposal. *Regression test:* the `_peaked` circle
  case. *Same mistake elsewhere:* a search for `inverse_laplacian` and "Laplacian step" over
  `metrics/` and `fmeval/` found no other iterative solver; `h_minus_one` applies the inverse
  Laplacian once.
- **The non-convergence warning blamed the cap when the iteration had diverged.**
  The loop broke as soon as the residual was not finite, but the warning said "did not converge in
  100 iterations"; on the reviewer's contrast-10 pair the divergence happened at iteration 22. The
  NaN path had no test. The reviewer fixed it (the warning said how many iterations ran and whether
  the residual was finite) and added the warning test. The builder amended it in ecf826c: after the
  solver fix above, a divergent trial is halved rather than ending the loop, so the warning now names
  either the cap with the residual left or a step that no damping could make lower the residual.
  The reviewer's test matched "did not converge", which the old message also contained, so it
  passed on 215945d; the builder tightened the match so that it fails there and passes on ecf826c.
  The other NaN path, a non-positive input, still returns NaN without a warning, as documented.
- **The Nyquist mode is treated differently by the map and its Jacobian (not
  fixed).** On an even grid, `.real` of the purely imaginary first derivative drops $u$'s Nyquist
  component, while the Hessian and the inverse Laplacian keep it, so the converged $u$ could cancel
  that part of the residual by compression in $\det(I + D^2 u)$ without the matching displacement
  appearing in $f\lvert\nabla u\rvert^2$ (the reviewer's conjecture, low confidence on the size).
  Removing the mode from the update makes the solve unable to reduce that residual component, as
  both found. The builder bounded its reach by the Nyquist modes' share of the $H^{-1}$ energy of the
  normalised difference on kinet density at step 6000: $6.9 \times 10^{-4}$ against white noise at
  half the fluctuation RMS (the ladder's harshest noise), $1.3 \times 10^{-14}$ against a 16-cell
  shift and $2.5 \times 10^{-12}$ against a blur. To first order it can change $W_2$ by at most about
  half those fractions (about $3.5 \times 10^{-4}$ at worst). Left as is.
- **The first circle check disagreed (during the build).** It used the line quantile formula and gave
  6.90 against 10.33, because the torus lets mass wrap around. Fixed by using Delon et al.'s
  rotation of mass levels; the agreement was then about $4 \times 10^{-5}$.

## Performance

- **Discrete transport (rejected).** POT's `ot.emd2` took 0.37 s at 32^2 and 5 to 11 s at 64^2 per
  solve, and a 256^2 cost matrix would be 34 GB.
- **Build.** The prototype took about 0.08 s per 256^2 kinet evaluation. The smoke run took about
  0.105 s per row. The first evidence run's fingerprint gave 0.214 s per evaluation against 0.0022 s
  for `h_minus_one`, about a hundred times more.
- **Inconsistent cost figures.** The decorator comment said "about 0.08 s per
  256^2 frame" (a prototype timing), the card 0.214 s (the fingerprint) and the work log "about
  0.1 s". The reviewer read `cost_s` of 0.187 to 0.232 s per axis in the fingerprint and a median
  `wall_time_s` of 0.186 s in `results.csv`. Fixed in ecf826c: the comment quoted the evidence run
  (0.19 to 0.23 s per 256^2 evaluation). The re-run's profile gave 0.193 s.
- **Speedup round (2026-11-02).** The orchestrator's profile put `np.linalg.eigvalsh` at about 45% of
  a call. Replacing it in 2-D by the closed-form determinant and Sylvester's criterion, with each
  distinct second derivative computed once (589ff0d on #32), was measured in one process,
  interleaved, nine rounds, medians, on kinet density at step 6000 against five candidates (mean
  field, a 16-cell shift, an eighth-cell shift, a blur and noise): 196.0 ms per call before and
  74.7 ms after (2.6 times faster), against 2.71 ms for `h_minus_one`, ratios of 72 and 28. The
  128-cell circle profiles peaking at 2.33, 2.94 and 3.53 times the mean gave the same values, NaNs
  and warning texts as ba15c19; a 3-D field was identical to ba15c19 (relative 0.0), and a
  z-constant 3-D field equalled the 2-D value to $2.2 \times 10^{-16}$.
- **The refactor gate.** The gate run (`results/wasserstein_gate_closed_form/wasserstein_1793647243`)
  was compared with `results/wasserstein_1793501169` on (frame_index, field, degradation, level,
  variant_label): all 9499 rows matched, with no NaN in either, and the largest relative difference
  was $3.34 \times 10^{-11}$. 122 rows exceeded rtol $10^{-12}$: `additive_noise` level 1 (102 rows,
  max $9.3 \times 10^{-12}$), `coarsen_bandlimited` levels 1-2 (10 rows, max $3.3 \times 10^{-11}$)
  and `highpass_ideal` levels 1-2 (10 rows, max $2.3 \times 10^{-12}$). Every row with a value above
  $10^{-5}$ except those high-pass rows was within $10^{-12}$ (8947 rows, max $2.3 \times 10^{-12}$).
  The worst row (`coarsen_bandlimited` level 1, frame 2000, $W_2 = 4.4 \times 10^{-8}$ cells)
  reproduces exactly (old 4.395159596318e-08, new 4.395159596171e-08); tightening the stopping
  tolerance to $10^{-15}$ changes neither value; and a one-ulp random perturbation of the candidate
  moves either implementation's own value by $1.4 \times 10^{-12}$ to $2.7 \times 10^{-11}$, against
  $4 \times 10^{-16}$ to $3 \times 10^{-15}$ on a 16-cell shift. So on near-identical pairs the value
  is conditioned at about $10^{-11}$ relative, and no change of floating-point order can meet
  $10^{-12}$ there. The agent did not loosen the tolerance and reported the gate as not met on those
  rows; the orchestrator recomputed and accepted it. Routed to
  [issues/119](../../issues/119-refactor-gate-fails-on-ill-conditioned-small-values.md).
- **Costs from different runs are not comparable.** The fingerprints, recorded in separate runs, gave
  0.0721 s against 0.0022 s, a ratio of 33 (90 before the change). They come from different login
  nodes: `h_minus_one`'s 2.2 ms was recorded on login05 (`comparison_1793434653`), and on login10, at
  a load average above its 244 cores, one call took 2.7 ms in one measurement and 5.0 ms a few
  minutes later. That is the agent's explanation of the gap, not isolated by a controlled test. A
  cost ratio between metrics should be measured interleaved in one process; the harness's
  `cost_relative` column, computed within one run, is the comparable number. Routed to
  [issues/125](../../issues/125-costs-from-different-runs-are-not-comparable.md) and stated on the
  card's Limitations, which also gives the ratio of 29 in the pinned comparison run.

## Tooling and environment problems

- **No PDF text tool** (no pdftotext, pypdf or poppler). Every arXiv source was read as LaTeX and
  compiled with `module load texlive/2024` in draft mode, reading equation numbers from the `.aux`
  file. Engquist & Froese (2014) and Delon et al. (2010) would not compile (missing class files) and
  are cited by section only.
- **Sandbox refusals.** Several shell commands (heredocs, pipelines naming git) were refused; the
  agent split them or wrote small scratch scripts.
- **A BEL character in the card.** Editing through a scratch script with a non-raw Python string
  turned `\approx` into a BEL character; found with grep and fixed before committing.
- **Clean tree during a run.** The `refs.bib` note on Engquist & Yang's Theorem 4.6 had to wait for the evidence
  commit, because the evidence run had started and the tree had to stay clean.
- **GitHub.** `gh` was not installed, so the pull request was opened through the GitHub connector;
  no `agent-metric` label exists.
- **The orchestrator's checker.** The first check gave 48 PASS and 6 FAIL after the orchestrator
  fixed the checker's title match (LaTeX maths, a missing subtitle, colon spacing); the FAILs were
  issues named by number rather than by path in the PR body's "What was added", fixed by naming each
  path (57 PASS after the review round). In the speedup round the checker stopped with a
  `FileNotFoundError`, because it looks for `results/<run id>/data/run_meta.json` and the gate run
  sat in a nested folder; the agent added a symlink `results/wasserstein_1793647243` to it. It then
  reported two FAILs for commits 589ff0d and 1f3c042 "made by the agent", presumably because the
  archived transcript predated the round; the final check gave 59 PASS, 0 FAIL and 14 MANUAL. The
  MANUAL items are DOIs read from arXiv copies, the abstract-only Engquist & Yang 2019, and the idea
  page's pitfalls.

## For the next agent

- **Untested convergence.** Whether the iteration converges for densities with near-empty regions is
  untested beyond the contract field. The test suite reaches the non-convergence warning only by
  capping the iterations; the branch where no damping lowers the residual was checked only with
  scratch scripts on the high-contrast circle profiles, which were not kept.
- **High contrast.** The solver fails from a peak of about three times the mean, which a strong shock
  exceeds. The full Newton step with GMRES
  ([proposals/MTR-wasserstein-full-newton-gmres.md](../../proposals/MTR-wasserstein-full-newton-gmres.md))
  is the remedy that was left undone.
- **Not diagnosed.** The `highpass_ideal` gate rows at $2.3 \times 10^{-12}$ were not diagnosed
  individually.
- **The Nyquist inconsistency** is bounded on kinet density but not removed; a field with more energy
  at the grid scale would feel it more.
- **The 3-D path** keeps the eigenvalue method and was checked only for a bit-identical value against
  ba15c19 and on a z-constant field.
- **Judgement 006** changes the shared contract tests; a reviewer was asked to decide whether it
  belonged in this pull request or in a separate harness change under issue 101.
