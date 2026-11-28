# Log: advecting Gaussian blobs

This log covers every configuration on [the advecting blobs page](../advecting_blobs.md): since
build-order step 12 there are two, `advecting_blobs` and `feature_population`, both computed on
the fly by the reader `AdvectingBlobs` in `fmeval/data/analytic.py`.

## History before this log

This log does not reconstruct how the reader came to exist. That history is recorded in three
places:

- `ANALYTIC_DATASETS_LOG.md` at the repository root (untracked), the log of the closed-form
  readers' first build. It covers the shared base class `ClosedFormTrajectory`; it does not
  name this reader, which came later;
- `issues/094`, which records why the reader was added: it is the test bed of the
  time-dependent degradations and of the dynamics family, written with pull request #19;
- the git log of `fmeval/data/analytic.py`, `configs/dataset/advecting_blobs.yaml` and
  `docs/datasets/advecting_blobs.md`, starting at commit `af77e17`.

## `advecting_blobs`

### What it is for

- **The time-dependent test bed** (`issues/094`): degradations with `per_unit_time: true`, and
  the planned dynamics metrics.
- **Advection–diffusion candidates with an exact error.** Build-order step 9
  (`dataset_specs/BUILD_ORDER.md`) asked for linear advection–diffusion with a wrong speed or
  a wrong diffusivity, and for the persistence, climatology and unrelated-realisation
  references, following `dataset_specs/05_initial_conditions_and_degraded_solver_runs.md`,
  Sects. 3.1 and 3.4.
- It is a fixture, not evidence about a flow (`docs/decisions.md`, "Analytic fields are
  fixtures; Sod is an analytic check").

### How it is treated

- **Source.** A closed form: a uniform density of 1 plus one Gaussian bump per velocity, each
  carried at its own constant velocity and, with a diffusivity, widened by the heat kernel.
  The page gives the equation.
- **Reader and options.** `advecting_blobs`, with options `grid`, `n_frames`, `t_start`,
  `t_end`, `velocities`, `width`, `amplitude`, `diffusivity`, `seed` and `candidate`. The
  defaults are three bumps of width 0.06 and height 0.1, no diffusion, $64^2$ cells and 21
  frames from $t = 0$ to $t = 10$.
- **Fields.** Density only.
- **Grid and boundaries.** Cell centres on the unit square; both axes periodic, with the
  minimum-image distance.
- **Candidates.** The option `candidate` names parameters to change, for example
  `'+dataset.reader.candidate={diffusivity:1e-5}'`. The reader's `predictions()` returns the
  same bumps with those parameters, on the same grid and frames, and `evaluate.py` scores them
  against the reader's frames as it scores a forecast. The mechanism is shared with
  `taylor_green_2d`; its decisions are in [the Taylor–Green log](taylor_green_vortex.md),
  decisions 1, 2 and 5.

### What part is evaluated

Decided by the agent on 2026-11-26, under Kareem's rule of the same day (step 3 of
`docs/recipes/add-a-dataset.md`). No default was changed, so no existing result moves: the
choices below are written in `configs/dataset/advecting_blobs.yaml`. The reader stores
nothing, so no disk is used.

- **The ladder experiment: the whole default, 21 frames over $t = 0$ to $10$ on $64^2$.** It
  is small enough to keep whole: the full panel without `persistence_wasserstein` took 75 s
  for all 21 frames. The bumps' relative positions change across the window, and the mean
  squared error under one blur varies by 7.5% across the frames (the page), so the frames are
  not copies of one another. How many independent samples they hold was not measured.
- **The candidate experiments**, named defaults. In each, the ladder is replaced by its clean
  entry, the anchor `mean_field` (climatology) and the candidate.
  1. Wrong speed,
     `'+dataset.reader.candidate={velocities:[[0.15,0.0],[0.0,0.08],[-0.06,0.04]]}'
     +dataset.reader.n_frames=41`. Only the first bump is wrong, by 0.1 along $x$, so the only
     phase error has period $1/0.1 = 10$, the whole default window. Measured: the mean squared
     error is 0 at $t = 0$, rises to $2.26 \times 10^{-4}$, and is 0 again at $t = 10$ when the
     wrong bump has gone once round the domain. The rise lasts about one time unit, and 41
     frames, one every 0.25, put about four points on it, against two with the default 21.
  2. Wrong diffusivity, `'+dataset.reader.candidate={diffusivity:1e-4}'`, on the default
     frames. At $t = 10$ the candidate's variance is $s = 0.0056$, its height has fallen to
     0.64 of the truth's, and the mean squared error is $2.9 \times 10^{-5}$ (measured). The
     minimum-image seam is then $2 \times 10^{-10}$ of the height. The value $10^{-5}$ used by
     the test and the page gives only $5.0 \times 10^{-7}$, a weak signal for an experiment.
  3. Persistence, `'+dataset.reader.candidate={velocities:[[0,0],[0,0],[0,0]]}'`.
  4. Unrelated realisation, `'+dataset.reader.candidate={seed:1}'`.
- **Measured costs.** These were measured on a Perlmutter login node under a load of about 20
  to 57, with no Slurm job, and written under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/cost/`.

  | Run | Cost per $64^2$ frame |
  |---|---|
  | `mse`, 91-level ladder | 0.2 s, almost all in applying the ladder |
  | `persistence_distance`, 91-level ladder | 0.5 s |
  | `wasserstein`, 91-level ladder | 0.7 s, the most expensive metric that finishes |
  | `persistence_wasserstein`, 91-level ladder | 0.4 s with a calibration measured on 1 or 2 frames; with the default 21 frames it stalled inside gudhi's `hera` Wasserstein routine for over 6 minutes on the first frame, twice, and was stopped |
  | Full panel without `persistence_wasserstein`, 91-level ladder | 2.1 s (75 s wall for 21 frames, measured) |
  | Full panel without `persistence_wasserstein`, wrong-speed candidate | 11 s wall for 41 frames, measured |

- **Why this balance.** The whole default costs about a minute, so nothing is gained by
  cutting it. The candidates are cheaper still, so they keep enough frames to trace their
  curves and the full period of the wrong-speed phase.

### Decisions and why

1. **A `diffusivity` option on this reader, not a new class.**
   - Made by: the agent, 2026-11-26, under Kareem's rule that an analytic dataset is an option
     on an existing reader before it is a new reader (`BUILD_ORDER.md`, "How code is written
     for this plan").
   - What it does: each bump's variance grows as $s = w^2 + 2\kappa t$ and its height falls as
     $a w^2 / s$. A Gaussian of variance $w^2$ convolved with the heat kernel of
     $\partial_t \rho = \kappa \nabla^2 \rho$, a Gaussian of variance $2\kappa t$, is a
     Gaussian of variance $s$ with the same mass, so each bump stays an exact solution of
     advection–diffusion. It is about three lines in `solution`, and the default of zero leaves
     the output bitwise unchanged (checked against the committed reader).
   - Why it beat a new class: spec 05, Sect. 3.1 proposed a random-phase Fourier-mode field in
     a new reader. That needs its own field construction and validation, while this reader
     already advects at constant velocity; a wrong speed then needs no code at all, and a wrong
     diffusivity three lines. Both keep an exact answer: for one bump, the mean squared error
     of two Gaussians in closed form (eq. 2 of the page).
   - Limit: the minimum-image seam grows with the bump, to $e^{-1/(8s)}$ of its height
     ($5 \times 10^{-15}$ at $s = 0.0038$, $2 \times 10^{-10}$ at $s = 0.0056$). The reader
     does not refuse a large diffusivity, just as it does not refuse a large width.
   - To reverse: remove `diffusivity` from the reader; the candidates below that do not use it
     are unaffected.
2. **A wrong speed is the candidate with other `velocities`.**
   - Made by: the agent, 2026-11-26.
   - Reason: the same `seed` draws the same starting centres, so the candidate is the same
     bumps carried at other velocities. No code was needed.
   - To reverse: nothing to remove; it is a choice of option value.
3. **Persistence is the candidate with zero velocities.**
   - Made by: the agent, 2026-11-26.
   - Reason: with every velocity zero and no diffusion, the candidate is the first frame at
     every step, provided the window starts at $t = 0$ (the default). With a diffusivity in the
     truth, the candidate must also set `diffusivity` to 0.
   - To reverse: nothing to remove.
4. **An unrelated realisation is the candidate with another `seed`.**
   - Made by: the agent, 2026-11-26.
   - Reason: another seed draws other starting centres with the same number of bumps, heights,
     widths and velocities, a second draw from the same random configuration (spec 05,
     Sect. 3.4).
   - To reverse: nothing to remove.
5. **Climatology is the existing `mean_field` anchor, not a candidate.**
   - Made by: the agent, 2026-11-26.
   - Reason: spec 05, Sect. 3.4 defines climatology here as the spatial mean of the target,
     which is exactly what the `mean_field` degradation does. It is the default damage anchor
     (`judgements/001`), and `evaluate.py` keeps the anchor whenever it scores a candidate, so
     every candidate run already scores climatology beside the candidate. A candidate of the
     reader cannot express a uniform field, since the height must be positive.
   - To reverse: not needed; to drop it from a run, set another `analysis.anchor`.
6. **The upwind and Lax–Friedrichs scheme candidates are left out.**
   - Made by: the agent, 2026-11-26, under Kareem's least-code rule.
   - Reason: spec 05, Sect. 3.2 makes them exact by multiplying each Fourier mode of the
     initial field by the scheme's amplification factor once per step (its Eqs. 4 to 6). This
     reader evaluates the field in physical space and has no notion of a time step, so it would
     need a Fourier transform of the first frame, a Courant number and a number of steps per
     frame: about 20 new lines and three options, more than any other candidate here. It is
     recorded as remaining in step 9's status in `BUILD_ORDER.md`.
   - To reverse: build it, as an option on this reader or with the field of spec 05,
     Sect. 3.1, as a decision of whoever takes up the rest of step 9.
7. **Not in `evidence_datasets`.**
   - Made by: the decision recorded in `docs/decisions.md`; registering this work as evidence
     is a separate step the coordinator holds.
   - To reverse: add the configuration to `evidence_datasets` in `configs/cards/default.yaml`
     with a claim label.

8. **The feature population is options on `AdvectingBlobs`, not a new reader.**
   - Made by: the agent (step 12), 2026-11-26, under Kareem's rule that an analytic dataset is
     an option on an existing reader first (`BUILD_ORDER.md`, "How code is written for this
     plan"), as spec 06, Sect. 3.1 also proposed.
   - What it does: per-feature `kinds`, `centres`, `width`, `amplitude`, `aspect`,
     `orientation` and `directions` (each one value or one per velocity), plus
     `front_thickness` and `background`; `FIELDS` grew to density, velocity, vorticity and
     pressure. The Gaussian is written so that at aspect 1 and orientation 0 it is the blob to
     the bit, and the default output is bitwise equal to HEAD and to step 9 (checked).
   - Alternative: a new `ClosedFormTrajectory` subclass, which would duplicate the advection
     loop, the minimum image and the centre draw.
   - To reverse: move the options into a subclass; `advecting_blobs` is unaffected either way.
9. **Vortices are Gaussian (Lamb–Oseen) with paired signs, and the mean vorticity is removed.**
   - Made by: the agent (step 12), following spec 06, Sect. 3.3 (its answer to catalog
     decision 4).
   - Reason: a Gaussian vorticity whose width grows as $w^2 + 2\nu t$ is the Lamb–Oseen vortex
     (Gallay and Wayne 2005, Commun. Math. Phys. 255, 97–129, Eqs. (7)–(8), viscosity
     restored), so `diffusivity` is the viscosity and the profile has closed-form integrals. A
     torus holds no net circulation, so the stored vorticity is the sum minus its mean and the
     velocity its periodic Biot–Savart inversion; `feature_population` pairs the signs so the
     mean is zero, and a candidate that breaks the balance carries the uniform offset, which
     enters its answer (MSE $4\pi w^2 a^2 - 4\Gamma^2$ for a flip).
   - Alternatives: a Rankine or Lamb–Chaplygin profile (no closed-form Gaussian integrals);
     refusing unpaired signs (it would forbid the flip candidate).
   - To reverse: change the Gaussian branch in `solution` for vortices.
10. **Fronts are tanh profiles of absolute pressure on the level 1.**
    - Made by: the agent (step 12), following spec 06, Sect. 3.3.
    - Reason: the shock detector needs two positive pressures in a ratio of at least 1.805
      (`shock_set_distance` card, Eq. 1); a jump of 1.5 on 1 gives 2.5. A tanh of a quarter cell
      is nearly a step yet closed-form at any sub-cell position, so a front never rings as a
      Fourier-shifted step does. Faces versus centres give the card's two answers,
      $(s - \tfrac12)\Delta x$ and $s\,\Delta x$. Diffusivity is refused with a front, since it
      would not keep the tanh.
    - Alternatives: a sharp step (rings under sub-cell moves); Rankine–Hugoniot states (spec 03,
      not needed for geometry).
    - To reverse: change the front branch in `solution`.
11. **Single-feature candidates use step 9's `candidate` unchanged; removal is amplitude 0.**
    - Made by: the agent (step 12), under the coordinator's instruction to extend the mechanism
      only if needed.
    - Reason: every candidate is one changed per-feature list: `centres` (move), `velocities`
      (wrong speed), `amplitude` (rescale, flip, remove at 0, add from a feature the reference
      holds at 0), `orientation` or `directions` (rotate). Amplitude 0 adds exactly 0.0 to every
      cell, so it is bitwise the field without that feature. No code was added for candidates.
    - To reverse: nothing to remove.
12. **Spec 06's `{feature: j, ...}`, `{remove: j}` and `{add: {...}}` design is dropped.**
    - Made by: the agent (step 12), under "change the plan to fit the code".
    - Reason: it would be a second candidate mechanism beside step 9's, and decision 11 already
      expresses every edit. Its cost: a candidate restates the whole list it changes, which is
      long on the command line for `centres`.
    - To reverse: add those keys to `ClosedFormTrajectory.predictions` for this reader.
13. **The bump of `tests/analytic_fields.py` is built from the reader.**
    - Made by: the agent (step 12), as spec 06, Sect. 5.1 and the build order asked.
    - What changed: `canonical_field("bump")` calls `AdvectingBlobs` with width $w/n_x$ and
      aspect $n_x/n_y$, so the repository has one Gaussian. It uses the minimum image instead of
      a 3 × 3 sum of periodic images; `tests/test_analytic_fields.py` passes unchanged.
    - To reverse: restore the image sum from git history.
14. **Features are placed 20 widths apart in the tests and in `feature_population`.**
    - Made by: the agent (step 12), from a measurement.
    - Reason: at spec 06's isolation of 12 widths a Gaussian's tail at the midpoint is
      $e^{-18} = 1.5 \times 10^{-8}$ of its peak; measured, that broke the exact zero of
      `increment_w1` for a whole-cell move ($1.5 \times 10^{-9}$) and the persistence distance
      ($3.6 \times 10^{-7}$). At 20 widths the tail is $e^{-50}$, below the round-off of a field
      of order 1, and both are exactly 0. The reader refuses no overlap: features are summed.
    - Alternative: an isolation check in the reader, which would refuse the default blobs
      (width 0.06, whose 12 widths exceed the half-domain).
    - To reverse: change the placements.
15. **The background's `rms` is an expected value, not the realised one.**
    - Made by: the agent (step 12), following the build order's shared random-field draw
      (`_apply_filter` on seeded white noise).
    - Reason: scaling the transfer function so that the expected mean square is $\mathrm{rms}^2$
      keeps the field exactly Gaussian with the prescribed covariance; rescaling each draw to
      its realised rms would not. With steep spectra a single draw's rms scatters by tens of
      percent (measured 0.039 to 0.056 for a requested 0.05 at slope 3, $k$ from 2 to 32).
      Spec 06's fixed amplitudes with random phases (an exact spectrum at every seed) was set
      aside for the one shared draw.
    - To reverse: divide each draw by its realised rms.
16. **Later change by step 10: the shared functions `band_transfer` and `biot_savart`.**
    - Made by: the step-10 agent, 2026-11-26, recorded here so the next agent knows the code
      moved.
    - What changed: the background's band power law and the spectral Biot–Savart inversion,
      first written inside `AdvectingBlobs`, are now `band_transfer` and `biot_savart` in
      `fmeval/data/analytic.py`, shared with step 10's random-field reader. The background
      still uses an expected rms (`band_transfer` returns a unit-expected-mean-square transfer).
    - To reverse: not intended; both readers depend on them.
17. **`feature_population` is one configuration, not spec 06's three.**
    - Made by: the agent (step 12), under the least-configuration rule.
    - Reason: bumps, vortices and fronts live in different fields, so they share a domain
      without overlapping; one static frame carries every family's answer.
    - To reverse: split it into three configurations with their own `fields`.
18. **Spec 07's transport pairs are one option, `potential`, not three.**
    - Made by: the agent (step 13), 2026-11-27, under "change the plan to fit the code"
      (`BUILD_ORDER.md`). Spec 07 was written before steps 9, 10 and 12 landed.
    - What changed from spec 07, Sect. 5.1: `amplitude` 0 was already allowed (step 12);
      `reverse` is dropped, because a plain reference with the candidate
      `{potential: [...]}` is the pair the other way round, through step 9's `candidate`;
      `predictions()` and the pairing in `evaluate.py` existed (step 9); and
      `transport_distance(t)` is dropped: the reader exposes `displacement` ($\nabla u$ at the
      cell centres), and a test evaluates eq. (7) of the page on a refined reader in two lines.
      The blob density is evaluated at arbitrary points by evaluating the existing loop at the
      displaced centres, not by a new function. About 20 lines of code in the reader, and its
      docstring.
    - To reverse: delete `potential`, `displacement` and the two lines of `solution` that use them.
19. **Only the density is mapped, and a density background is refused with a potential.**
    - Made by: the agent (step 13).
    - Reason: spec 07 needs density only (its Sect. 2). Bumps are evaluated at
      $\mathbf{x} + \nabla u$ and the density multiplied by $\det(I + D^2 u)$; vortices and
      fronts keep the cell centres, so a population with a potential is still well defined.
      The background is a field on the grid with no closed form at displaced points, so a
      density background would make eq. (6) inexact; it is refused, not interpolated.
    - To reverse: interpolate the background spectrally at the displaced points, losing exactness.
20. **The reader checks the sufficient bound $\sum_j \lvert a_j\rvert < 1$, not exact convexity.**
    - Made by: the agent (step 13), following spec 07, Sect. 3.1.
    - Reason: the bound is deterministic and guarantees $I + D^2 u$ positive definite everywhere,
      not only at the cell centres. Its cost: Saumier's two-mode example is admitted only for
      $\lambda < 1/2$, although it is convex up to $\lambda < 1$ (spec 07); the tests use 0.45.
    - Alternative: check the eigenvalues on a fine grid, which certifies nothing between nodes.
    - To reverse: replace the bound in the constructor's check.
21. **The exact circle solver is `circle_w2` in `tests/analytic_fields.py`, not in `conftest.py`.**
    - Made by: the agent (step 13). Spec 07 proposed `tests/conftest.py`.
    - Reason: `AGENTS.md` §7 and `tests/conftest.py`'s docstring name `analytic_fields` as the
      shared helper module for closed-form targets, where step 10 put `gaussian_mean_square`;
      `conftest.py` holds fixtures. It replaces the quantile-grid solver of
      `metrics/wasserstein/test_metric.py`, which is deleted.
    - What it does: reads each density as constant on its cells, so both quantile functions are
      piecewise linear in the mass level; integrates the squared difference exactly between
      merged knots; minimises the convex cost over the rotation by bounded Brent search. Cells
      lighter than the round-off of a level near 1 count as empty, and the fraction of a cell is
      clipped to [0, 1]; without those two, tails of $10^{-24}$ made the cost $10^{26}$ at some
      rotations (measured while building it).
    - Measured: a periodised Gaussian of width 0.03 moved by 0.1 gives 0.1 to $2 \times
      10^{-15}$ on $2^{14}$ and $2^{16}$ cells (the old solver: 0.1000253); a $\cos^2$ bump of
      width 0.2 keeps $W_2/s = 1$ to $3 \times 10^{-12}$ up to $s = 0.3$ and gives 0.99969 at 0.35, as
      spec 07 states; $1 + a\cos$ against uniform converges as $h^2$ ($4 \times 10^{-10}$ on
      $2^{16}$ cells), 0.4 to 0.7 s per pair there.
    - To reverse: not intended.
22. **One configuration, `transport_pairs`, with the plain blobs as the reference.**
    - Made by: the agent (step 13), under the least-configuration rule. Spec 07 proposed two
      (`transport_manufactured`, `transport_manufactured_contrast`).
    - Reason: the other pairs are overrides on the page. The orientation: with the potential on
      the reference, the config must state `candidate: {potential: null}`, which
      `tests/test_configs.py` reads as restating the reader's default; with the potential on
      the candidate it states nothing redundant, and the distance is the same. The solve then
      runs from the plain side, which is not one step: measured within $7 \times 10^{-7}$ in
      every frame.
    - To reverse: move `potential` to the reader block and teach the config test that a
      candidate's values are changes.
23. **The failure range of the solve is documented, not pinned by a test.**
    - Made by: the agent (step 13), as the coordinator allowed for an unstable threshold.
    - Reason: from the uniform side `wasserstein` returns NaN somewhere between $a = 0.94$ and
      $a = 0.965$, but not monotonically: on $64 \times 48$ along the diagonal it fails at 0.94
      and converges at 0.95 (scan in the log entry of 2026-11-27). A pinned value would encode
      the solver's damping path, and a better solver would fail the test.
    - To reverse: add a test asserting NaN at $a = 0.97$ (NaN on every grid and mode scanned).
24. **No stripe shape, no Gaussians and no signed fields here.**
    - Made by: the agent (step 13), under the least-code rule.
    - Reason: the potential with height 0 already gives one-axis profiles (one axis mode) and
      products (two), with an exact answer through `circle_w2`; a stripe bump shape (spec 07,
      Sect. 3.4) is needed only for the background-ratio sweep, which is left open. The
      Gaussians (Sect. 3.5) and signed fields (Sect. 3.7) serve metrics that are not built.
    - To reverse: add a `stripe` kind to the bump loop when the sweep is wanted.

### Log entries

Entries are dated and newest last. Append a new entry at the end of this section; never
rewrite an old one.

**2026-11-26, agent (build-order step 9).**

- Code: `fmeval/data/analytic.py`, the `diffusivity` and `candidate` options on
  `AdvectingBlobs` (decision 1), using the `candidate` mechanism added to
  `ClosedFormTrajectory` in the same change.
- Tests, in `tests/test_analytic_datasets.py`: one bump on a 64 × 48 grid with a wrong speed, a
  wrong diffusivity and both, through the pipeline's prediction path, against the closed-form
  mean squared error of two Gaussians to $10^{-10}$ relative. The measured error is about
  $2 \times 10^{-12}$, limited by round-off against the background density of 1.
- Configuration: one comment line in `configs/dataset/advecting_blobs.yaml`; no new file.
  Page: eq. (1) with diffusion, a section "Candidates with a known error" and eq. (2).
- Verified:
  - the default `pytest` passed (2725 passed, 0 failed), as did `mkdocs build --strict`;
  - each of the four overrides on the page (wrong speed, wrong diffusivity, persistence,
    unrelated realisation) runs through `evaluate.py` with the default configuration;
  - the reader's default output is bitwise equal to the committed version.
- Not verified:
  - persistence and the unrelated realisation have no closed-form test; they were only run;
  - the mean squared error is asserted for one bump only. With several bumps the cross terms
    between bumps also enter, and no test covers them.

**2026-11-26, agent (what part is evaluated).**

- Decided which part of `advecting_blobs` each experiment evaluates (section "What part is
  evaluated"), and wrote it as a comment block in `configs/dataset/advecting_blobs.yaml`. No
  default changed. The comment line pointing to `feature_population.yaml`, added by another
  agent, was kept.
- Measured with `python evaluate.py dataset=advecting_blobs` on 2 frames with `metrics=[mse]`,
  `[wasserstein]`, `[persistence_distance]` and the full panel; on all 21 frames with the full
  panel without `persistence_wasserstein`; and the wrong-speed candidate on 41 frames. Per-frame
  costs across the window were measured with `measure_frames.py`. Everything is under
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/cost/`.
- `persistence_wasserstein` stalled twice in a 21-frame run: `gdb` showed the process inside
  gudhi's `hera` extension after more than 3 minutes. It took 0.4 s per frame whenever the
  calibration came from 1 or 2 frames.
- Checked that the wrong-speed error is 0 at $t = 0$ and $t = 10$ and peaks at
  $2.26 \times 10^{-4}$, and the wrong-diffusivity error at $t = 10$ for $\kappa' = 10^{-5}$ and
  $10^{-4}$.
- Not verified: why `persistence_wasserstein` stalls under the 21-frame calibration; the
  number of independent samples among the 21 frames.

**2026-11-26, agent (build-order step 12, the feature population).**

- Code: the population options on `AdvectingBlobs` in `fmeval/data/analytic.py` (decisions 8
  to 11, 15); the bump of `tests/analytic_fields.py` built from the reader (decision 13).
- Tests, in `tests/test_analytic_datasets.py`, through the pipeline on non-square grids:
  defaults bit for bit; the Biot–Savart round trip to $10^{-12}$ of the peak; the
  double-penalty crossover at $1.665\,w$ (MSE of move and removal to $10^{-12}$); persistence
  $h/2$ for removal and addition and 0 for a whole-cell move; `increment_w1` exactly 0 for a
  whole-cell move, 0 to $10^{-15}$ for a centred vortex flip, and its discrete removal value;
  a straight front's ASSD $(s - \tfrac12)\Delta x$ on faces and $s\,\Delta x$ through
  centres, Hausdorff $s\,\Delta x$; the background's band, rms and cancellation; refusals.
- Configuration `configs/dataset/feature_population.yaml`; page section "The feature
  population"; one row in `docs/datasets/README.md`.
- Verified: the default `pytest` (2853 passed, 0 failed); `evaluate.py` on the four named
  candidates (section "What part is evaluated" of `feature_population`), each matching its
  closed form.
- Then, for what part is evaluated: the widths of `feature_population` went from 0.03 to 0.025
  and the stripe was moved so its fronts lie on cell faces, so that every named candidate has
  an exact answer at 20 widths of separation (decision 14). Costs measured with
  `evaluate.py`, under
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/cost_feature_population/`.
- Not verified: `persistence_wasserstein` on this configuration; that step 10's move to
  `band_transfer` and `biot_savart` left the outputs bitwise unchanged (its agent's change,
  not re-checked here beyond the tests passing).

**2026-11-27, agent (build-order step 13, the transport pairs).**

- Code: the `potential` option and the `displacement` attribute of `AdvectingBlobs`
  (decisions 18 to 20); `circle_w2` in `tests/analytic_fields.py` (decision 21), replacing the
  quantile-grid solver of `metrics/wasserstein/test_metric.py`, whose circle test now compares
  with the smooth profile on $2^{16}$ sub-cells at $10^{-8}$ (measured $1.7 \times 10^{-9}$ and
  $3.8 \times 10^{-10}$; it was $2 \times 10^{-4}$).
- Configuration `configs/dataset/transport_pairs.yaml` (decision 22); page section "Transport
  pairs with a known distance"; the row in `docs/datasets/README.md`; a note in
  `metrics/wasserstein/code_notes.md`.
- Tests, in `tests/test_analytic_datasets.py`, through the pipeline on $64 \times 48$ (and
  $128 \times 96$ for the convergence check): one mode both ways (eq. 8; $10^{-12}$ from the
  deformed side up to $a = 0.998$, $10^{-5}$ and a tenfold fall from the uniform side,
  `h_minus_one` $10^{-12}$ both ways); Saumier's map with $g = 1$ and with the blobs at height
  3, both ways (eq. 7; $10^{-12}$ and $10^{-5}$); a product pair both ways (eq. 9, $10^{-5}$);
  a translated product ($10^{-5}$) and the translated blobs inside their bracket; five refusals.
- Measured, all through `fmeval.pipeline.run` with scratch scripts that were not kept:

  | Pair (relative error of `wasserstein`) | $64 \times 48$ | $128 \times 96$ |
  |---|---|---|
  | One mode, deformed side, $a$ from 0.3 to 0.998, axis and oblique | $\le 4.4 \times 10^{-16}$ | $\le 4.4 \times 10^{-16}$ |
  | One mode, uniform side, $a = 0.3$, axis / oblique | $1.3 \times 10^{-7}$ / $2.3 \times 10^{-6}$ | $8.1 \times 10^{-9}$ / $1.5 \times 10^{-7}$ |
  | One mode, uniform side, $a = 0.9$, axis / oblique | $1.2 \times 10^{-5}$ / $2.3 \times 10^{-2}$ | $3.1 \times 10^{-5}$ / $3.9 \times 10^{-3}$ |
  | Saumier, $\lambda = 0.45$, $g = 1$, forward / reverse | $8.6 \times 10^{-14}$ / $5.5 \times 10^{-7}$ | $8.6 \times 10^{-14}$ / $3.5 \times 10^{-8}$ |
  | Saumier, blobs at height 1, forward / reverse (3 frames, max) | $3.8 \times 10^{-7}$ / $7.0 \times 10^{-7}$ | $8.6 \times 10^{-9}$ / $4.7 \times 10^{-8}$ |
  | Saumier, blobs at height 3, forward / reverse (3 frames, max) | $1.0 \times 10^{-6}$ / $9.6 \times 10^{-7}$ | $2.3 \times 10^{-8}$ / $6.8 \times 10^{-8}$ |
  | Product pair, forward / swapped | $8.0 \times 10^{-8}$ / $5.3 \times 10^{-7}$ | $1.1 \times 10^{-8}$ / $2.8 \times 10^{-8}$ |
  | Translated product, 1 to 16 cells along $x$ (the $y$ move was not measured apart from the test) | $3.7$ to $6.9 \times 10^{-8}$ | $1.9$ to $3.9 \times 10^{-9}$ |

  `h_minus_one` was exact to $3 \times 10^{-16}$ on every one-mode pair, and on Saumier's map
  with $g = 1$ it reads 1.013 times $W_2$ (1.09 to 1.10 and 1.28 to 1.30 with blobs at height 1
  and 3). The
  translated blobs at height 0.1 and 3 sat 23% to 99% above the marginal lower bound and far
  below the shift.
- NaN scan, uniform side, phase 0.4 (`ok` converged, `NaN` returned NaN with its warning):

  | Grid, mode | 0.90 | 0.92 | 0.94 | 0.95 | 0.96 | 0.965 | 0.97 |
  |---|---|---|---|---|---|---|---|
  | $64 \times 48$, (1, 0) | ok | ok | ok | NaN | NaN | NaN | NaN |
  | $64 \times 48$, (2, 1) | ok | ok | NaN | ok | NaN | NaN | NaN |
  | $64^2$, (1, 0) | ok | ok | ok | NaN | NaN | NaN | NaN |
  | $64^2$, (2, 1) | ok | ok | NaN | NaN | NaN | NaN | NaN |
  | $128 \times 96$, (1, 0) | ok | ok | NaN | ok | ok | NaN | NaN |
  | $128 \times 96$, (2, 1) | ok | ok | NaN | ok | NaN | NaN | NaN |
  | $128^2$, (1, 0) | ok | ok | NaN | ok | ok | NaN | NaN |
  | $128^2$, (2, 1) | ok | ok | NaN | ok | NaN | NaN | NaN |

  From the deformed side nothing failed up to $a = 0.998$. Spec 07's "NaN at $a \ge 0.97$" holds;
  its single threshold does not.
- Verified: the reader's output with every option at its default, and `feature_population`,
  bitwise equal to HEAD (`61f27e3`) on seven option sets over three grids, every frame and field
  (592 arrays); the
  `evaluate.py` smoke runs and costs of section `transport_pairs` below; the page's three
  override rows each run through `evaluate.py` and match their closed form (uniform side
  $2.1 \times 10^{-6}$, deformed side $7 \times 10^{-16}$, product $7.5 \times 10^{-8}$). Test results: the default `pytest` exit 0 (2905 passed, 405
  skipped, 4 xfailed); `pytest metrics/wasserstein metrics/h_minus_one` exit 0 (15 passed).
- Not verified: the optimality argument of spec 07, Sect. 3.1 (McCann; Cordero-Erausquin) was
  taken from the spec, not re-read; the tolerance argument of `circle_w2`'s search interval
  ($\lvert\theta\rvert < 1$) is mine and only checked on the cases above.

**2026-11-27, step-32 agent: registered as evidence.**

- **Registered:** `advecting_blobs` (`{periodic: true, ensemble: false}`) in `evidence_datasets`
  and `evidence_dataset_properties` of `configs/cards/default.yaml`, under the label "an
  analytic check: three Gaussian density bumps carried at different constant velocities, their
  exact solution known at every time, and nothing about turbulence".
- **Why, and who decided.** Decision 16 of `dataset_specs/BUILD_ORDER.md` (the smaller calls
  Kareem left to the agents, made on 2026-11-27): it is the reader of the registered
  `feature_population` and `transport_pairs`, its blobs move at different velocities so its
  frames are not scalar multiples of one another, and the candidates built on it in step 9 are
  evaluation experiments. This supersedes "not in evidence_datasets" in the configuration's
  comments and on the dataset page, both rewritten.
- **Window:** the configuration's 21 frames on $64^2$ (section "What part is evaluated");
  nothing needs a command-line setting.
- **Not done:** no metric was run on it for a card; `python -m fmeval.cards catalog` added its
  *not yet run* or *not applicable* row to every metric card. The `persistence_wasserstein`
  stall on its first frame (open points) is unchanged; `dataset.slow_metrics` can now give that
  metric fewer frames or a coarser grid, but a stall on one input is not avoided that way.

### Open points

- The upwind and Lax–Friedrichs candidates (decision 6).
- The mean and spread over many initial conditions: the harness scores one seed per run, so
  a set of seeds is not aggregated (spec 05, Sects. 2 and 3.1).
- The skill score of spec 05, Sect. 3.4 is an analysis, not built.
- `persistence_wasserstein` stalls on this dataset under the default 21-frame selection
  (section "What part is evaluated"); its cause, and so the full panel's cost with it, is
  unknown.
- From spec 06, Sect. 3.5, not yet pinned by a test: the ellipse rotation $(a - b)\delta\phi$,
  the circle's discrete ASSD values, the pooled-average dilution as a formula, the spectrum
  changes of moving one feature, the velocity error of its Eq. (6), the `wasserstein` bounds,
  sub-cell and rescale persistence, a width change, and the firing limit at 45°.
- Spec 06's time-dependent variants, the background-ratio sweep configurations and Option B
  (a kinet run seeded with a vortex population) are not built.
- From spec 07 (step 13), not built: the exact background-ratio sweep (Sects. 3.3 and 3.4,
  which needs a stripe bump on a background reaching 0, decision 24); the Gaussian pairs and
  their sliced and entropic answers (Sect. 3.5) and the signed-field answers (Sect. 3.7), for
  metrics not yet built; Option B (a discrete solver, POT not installed); the two
  findings for the `wasserstein` card (Sect. 3.6), which this log measures but no card states.

## `feature_population`

### What it is for

The feature population of `dataset_specs/06_feature_population_generator.md` (build-order
step 12): fields whose features are listed in advance, so that a single-feature candidate has a
known answer for the pointwise norms, the increment family, the persistence pair and the shock
metrics. Decisions 8 to 17 above cover how it is built.

### How it is treated

One static frame of the `advecting_blobs` reader on $128^2$, both axes periodic, with density
(four bumps), vorticity and velocity (four paired vortices) and pressure (a circle, an ellipse
at 30°, a stripe along $y$), all features on cell centres or, for the stripe, cell faces. The
configuration file lists every option.

### What part is evaluated

Decided by the agent on 2026-11-26 (step 3 of `docs/recipes/add-a-dataset.md`); the choice is
also written as comments in `configs/dataset/feature_population.yaml`. Nothing is stored.

- **One frame.** The fields are deterministic and static, so a second frame repeats the first
  exactly and adds cost without information. The frame is one sample per metric, field and
  axis; the dataset checks known answers rather than estimating statistics.
- **$128^2$.** Each Gaussian is 3.2 cells wide, so its cell-centre integrals and its spectral
  Biot–Savart inversion are exact to round-off ($e^{-\pi^2 (w/h)^2} = e^{-101}$ and
  $e^{-50}$), and four features fit 20 widths apart on each field (decision 14). A finer grid
  costs several times more and adds no answer; a coarser one under-resolves the Gaussians.
- **The named experiments**: the default 91-level ladder, and four single-feature candidates,
  each matching its closed form (measured, $w = 0.025$):

  | Candidate | Known answer | Measured |
  |---|---|---|
  | Remove the bump of height 0.3 | MSE $\pi w^2 a^2 = 1.767 \times 10^{-4}$; persistence $a/2 = 0.15$ | equal; 0.15 |
  | Move it 8 cells along $x$ ($2.5\,w$) | MSE $2\pi w^2 a^2 (1 - e^{-s^2/4w^2}) = 2.793 \times 10^{-4}$, above the removal's; persistence and `increment_w1` 0 | equal; exactly 0 and 0 |
  | Flip the vortex of peak $-0.5$ | MSE on vorticity $4\pi w^2 a^2 - 4\Gamma^2 = 1.948 \times 10^{-3}$; `increment_w1` 0; persistence $\lvert a\rvert/2$ | equal; $8 \times 10^{-15}$ (recomputed vorticity); 0.25 |
  | Move the stripe 2 cells along $x$ | `shock_set_hausdorff` $2/128$; `shock_set_distance` $(2 - \tfrac12)/128$ for the stripe, pooled with the unmoved fronts | 0.015625; 0.00777 |

  The overrides are in the configuration's comments.
- **Measured costs**, on a Perlmutter login node under a load of 37 to 46, with no Slurm job:

  | Run | Pipeline time for the one $128^2$ frame |
  |---|---|
  | `mse`, 91-level ladder | 2.9 s (6.6 s wall) |
  | `shock_set_distance`, 91-level ladder | 2.9 s (6.0 s wall) |
  | `wasserstein`, 91-level ladder | 16.4 s (21.4 s wall) |
  | `persistence_distance`, 91-level ladder | 16.9 s (26.4 s wall) |
  | Full panel without `persistence_wasserstein`, 91-level ladder | 34 s (80 s wall) |
  | Full panel without `persistence_wasserstein`, each candidate | about 2 s (10 s wall) |

  `persistence_wasserstein` was not run: other agents found it stalls or takes over 15 minutes
  per frame. The projected default set, the ladder and the four candidates, is about two
  minutes of wall time.
- **Why this balance.** The whole dataset is one frame and costs about two minutes, so nothing
  is gained by cutting it; adding frames or resolution would add cost and no answer.

### Log entries

#### 2026-11-27: registered as evidence (registration agent)

- **Registered:** `feature_population` (`{periodic: true, ensemble: false}`) in
  `evidence_datasets` and `evidence_dataset_properties` of `configs/cards/default.yaml`. Kareem
  decided the rule on 2026-11-26 (`dataset_specs/BUILD_ORDER.md`, "The task" and decision 9:
  every dataset built in that plan is an evaluation dataset, admitted to `evidence_datasets`
  with a label naming the kind of claim it supports); the agent chose the label.
- **Label** (completes "n frames of ..." in a card's run summary): "an analytic check: one
  static field of isolated bumps, vortices and pressure fronts with known answers, and nothing
  about turbulence".
- **Window:** the one static frame on 128^2 under the default ladder (section "What part is
  evaluated" above). Its four single-feature candidates are overrides of the same configuration,
  so a run of one is cited under the same name and label; they are listed beside
  `evidence_window`, since no config key names a set of candidate runs.
- **Single frame.** The rule that keeps out a dataset whose frames are scalar multiples of one
  another does not bite: there is one frame, the per-frame rank statistics need only one, and
  its features are not one pattern rescaled. A card citing it says "1 frames of", the
  generator's wording.
- **Not done:** no metric was run on it for a card; every metric card's *Across the experiments*
  table shows it as *not yet run* or *not applicable* with the reason (`python -m fmeval.cards
  catalog`). Producing that evidence is its own step in `BUILD_ORDER.md` and needs compute.

## `transport_pairs`

### What it is for

Build-order step 13 and `dataset_specs/07_transport_known_answer_pairs.md`: density pairs whose
quadratic Wasserstein distance is known exactly, so that `wasserstein` (and later the planned
sliced and Sinkhorn transport metrics, issues 048 and 067) can be checked against the true
distance rather than another approximation, and its reach in contrast measured. It builds the
known-answer transport proposal in full, which was therefore deleted on 2026-11-27. Decisions 18
to 24 above cover how it is built.

### How it is treated

The `advecting_blobs` reader with its default blobs at height 3 as the reference, and as the
candidate the same blobs pulled back through Saumier et al.'s (2015, Sect. 5.1) potential at
$\lambda = 0.45$, `candidate: {potential: [...]}` (page, eqs. (5) to (7)). Density only, on the
default $64^2$ cells and 21 frames from $t = 0$ to 10, both axes periodic. The exact distance is
eq. (7) of the page, from the candidate's `displacement`, 0.0497 to 0.0515 across the frames; the
candidate's density ranges over a factor of 25.

### What part is evaluated

Decided by the agent on 2026-11-27 (step 3 of `docs/recipes/add-a-dataset.md`); also written in
`configs/dataset/transport_pairs.yaml`. Nothing is stored.

- **The default 21 frames on $64^2$, kept whole.** The candidate replaces the ladder, so a frame
  is one pair (plus the clean entry and the `mean_field` anchor). The frames are deterministic:
  21 known answers that change as the blobs move, not 21 statistical samples.
- **$64^2$ rather than $128^2$.** `wasserstein` is within $7 \times 10^{-7}$ of the exact distance
  in every frame at $64^2$ and within $5$ to $7 \times 10^{-8}$ on three frames at
  $128 \times 96$ (both measured, solving from the plain blobs), and one pair costs 0.10 s at $64^2$ against 0.32 s at $128^2$.
- **Measured costs**, on a Perlmutter login node under a load of 33 to 51, results under
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/transport_pairs/`:

  | Run, all 21 frames | Cost |
  |---|---|
  | `mse`, `wasserstein`, `h_minus_one` | 10 s wall; `wasserstein` 0.10 s per pair, 0.24 s against the anchor |
  | Every deterministic density metric but `persistence_wasserstein` | 8.0 s of metric time, 13 s wall; `wasserstein` is 90% of it |
  | `persistence_wasserstein` alone | 3 s wall; it did not stall here |
  | `wasserstein` on $128^2$ | 0.32 s per pair, 0.79 s against the anchor |

- **Why this balance.** The whole set costs under 20 s, so nothing is gained by cutting frames,
  and a finer grid would triple the dominant cost to shrink an error far below anything the
  ladder or a candidate changes.

### Log entries

#### 2026-11-27: registered as evidence (registration agent)

- **Registered:** `transport_pairs` (`{periodic: true, ensemble: false}`) in `evidence_datasets`
  and `evidence_dataset_properties` of `configs/cards/default.yaml`. Kareem decided the rule on
  2026-11-26 (`dataset_specs/BUILD_ORDER.md`, "The task" and decision 9: every dataset built in
  that plan is an evaluation dataset, admitted to `evidence_datasets` with a label naming the
  kind of claim it supports); the agent chose the label.
- **Label** (completes "n frames of ..." in a card's run summary): "an analytic check: density
  pairs at an exactly known quadratic Wasserstein distance, and nothing about turbulence".
- **Window:** the reader's 21 frames on 64^2, kept whole, each one pair of the reference and its
  candidate (section "What part is evaluated" above); nothing needs a command-line setting.
- **Frames not scalar multiples:** the blobs move at distinct velocities, so the pair changes
  from frame to frame (the exact distance runs from 0.0497 to 0.0515).
- **Not done:** no metric was run on it for a card; every metric card's *Across the experiments*
  table shows it as *not yet run* or *not applicable* with the reason (`python -m fmeval.cards
  catalog`). Producing that evidence is its own step in `BUILD_ORDER.md` and needs compute.
