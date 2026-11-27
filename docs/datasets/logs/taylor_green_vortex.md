# Log: Taylor–Green vortex

This log covers every configuration on [the Taylor–Green vortex page](../taylor_green_vortex.md).
Since 2026-11-27 there are two, `taylor_green_2d` and `helmholtz_mixture_2d`, both exact
solutions computed on the fly by the reader `TaylorGreen2D` in `fmeval/data/analytic.py`.

## History before this log

This log does not reconstruct how the reader came to exist. That history is recorded in three
places:

- `ANALYTIC_DATASETS_LOG.md` at the repository root (untracked), which records how the reader,
  its pressure sign, its page and its first evaluation were built and checked;
- `issues/094`, which records the time-dependent test bed that `advecting_blobs` and this
  reader share;
- the git log of `fmeval/data/analytic.py`, `configs/dataset/taylor_green_2d.yaml` and
  `docs/datasets/taylor_green_vortex.md`, starting at commit `aaf3199`.

## `taylor_green_2d`

### What it is for

- **A harness check with an answer known in advance.** It is a fixture, not evidence about a
  flow (`docs/decisions.md`, "Analytic fields are fixtures; Sod is an analytic check").
- **Candidates with an exact error at every step.** Build-order step 9
  (`dataset_specs/BUILD_ORDER.md`) asked for Taylor–Green with a wrong viscosity or a phase
  drift, following `dataset_specs/05_initial_conditions_and_degraded_solver_runs.md`,
  Sect. 3.3. The thirteen metrics whose cards report an error per step of a candidate
  trajectory (`mse`, `mae`, `rmse`, `rmse_channel_mean`, `nrmse`, `vrmse`, `max_error`,
  `max_error_channel_mean`, `h1_relative`, `spectrum_l2`, `kinetic_energy`, `enstrophy`,
  `palinstrophy`) then have an exact error-against-step curve to be tested against.

### How it is treated

- **Source.** The closed form of Taylor (1923), translated onto the box $[0, 2\pi)^2$, with a
  pressure derived from the momentum equation. The page gives the equations and citations.
- **Reader and options.** `taylor_green_2d`, with options `nu`, `drift`, `grid`, `n_frames`,
  `t_start`, `t_end` and `candidate`. The defaults are $\nu = 0.01$, no drift, $256^2$ cells and
  10 frames from $t = 0$ to $t = 50$.
- **Fields.** Velocity, pressure and vorticity. Vorticity is the closed form and is recomputed
  from velocity by the harness, as on every dataset.
- **Grid and boundaries.** Cell centres; both axes periodic.
- **Candidates.** The option `candidate` names parameters of the solution to change, for
  example `'+dataset.reader.candidate={nu:0.02}'`. The reader's `predictions()` then returns the
  same solution with those parameters, on the same grid and frames, and `evaluate.py` scores it
  against the reader's frames as it scores a forecast. The page lists the candidates and their
  exact errors.

### What part is evaluated

Decided by the agent on 2026-11-26, under Kareem's rule of the same day (step 3 of
`docs/recipes/add-a-dataset.md`). No default was changed, so no existing result moves: the
choices below are the overrides each experiment is run with, written in
`configs/dataset/taylor_green_2d.yaml`. The reader stores nothing, so no disk is used.

- **The ladder experiment: 3 frames at $256^2$.** Every frame is a scalar multiple of the
  first, so the whole trajectory is one independent sample, and further frames add cost, not
  information. The experiment is run as `dataset=taylor_green_2d dataset.time.reduction=4`,
  which keeps the frames at $t = 0$, $22.2$ and $44.4$, three times at which the same
  ordering can be checked.
  - Why the default of 10 frames stays: `python -m fmeval.cards dynamics taylor_green_2d`
    draws its five snapshots from this selection, and its test requires five frames.
    Changing the selection would also change the committed figures.
  - Why $256^2$ stays: the grid is the reader's default, and a smaller one would change every
    calibrated severity of the ladder.
- **The candidate experiments**, named defaults. In each, the ladder is replaced by its clean
  entry, the anchor and the candidate. The closed forms hold on any grid of at least 3 cells,
  so the grid is left at $256^2$.
  1. Wrong viscosity, `'+dataset.reader.candidate={nu:0.02}'`, on the default 10 frames over
     $t = 0$ to $50$. The error $\lvert 1 - D'/D \rvert = 1 - e^{-0.02 t}$ grows smoothly to
     0.63, and ten points trace it.
  2. Phase drift, `'+dataset.reader.candidate={drift:[0.26,0.13]}' +dataset.reader.n_frames=21`.
     The two phases have periods $2\pi/0.26 = 24.2$ and $2\pi/0.13 = 48.3$, so the window holds
     one full period of the slower phase, and the mean squared error returns to zero once,
     near $t = 48.3$ (measured 0.0022 at $t = 47.5$ on $64^2$). With 21 frames each period of
     the faster phase is sampled about ten times.
  3. Persistence, `'+dataset.reader.candidate={nu:0}'`, on the default frames.
- **Measured costs.** These were measured on a Perlmutter login node under a load of about 20
  to 57, with no Slurm job, and written under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/cost/`. The deterministic panel is every
  metric except the ensemble ones.

  | Run | Cost per $256^2$ frame |
  |---|---|
  | `mse`, 91-level ladder | 7.7 s, almost all in applying the ladder (metric 0.05 s) |
  | `persistence_distance` on vorticity, 91-level ladder | 6.6 s of metric, plus 6.7 s of ladder |
  | Full panel, 91-level ladder | 85 s: `spectral_energy_flux` 22.7 s, `energy_distance` 19.7 s, `persistence_wasserstein` 9.9 s, `persistence_distance` 6.6 s, `increment_w1_by_separation` 6.2 s |
  | Full panel, a candidate (3 entries) | 2.6 s with `persistence_wasserstein`; 3.5 s without it in the drift run, under a heavier load |

  `persistence_distance` costs 72 ms per evaluation here, against the 34 to 142 s per $256^2$
  frame other datasets found. My reading, not checked: the single Fourier mode has very few
  critical points, so its persistence diagrams are tiny.
- **Projected and measured full-panel time.** A run has a fixed cost of about 88 s (start-up,
  the calibration and writing about 30 run folders), measured as the 2-frame run's 259 s wall
  time less its 171 s of per-frame work.
  - The ladder on 3 frames: about $88 + 3 \times 85 \approx 340$ s, 6 minutes (projected).
  - The ladder on all 10 frames: about 940 s, 16 minutes (projected).
  - The phase-drift candidate on 21 frames without `persistence_wasserstein`: 103 s
    (measured).
  - The wrong-viscosity candidate on 10 frames: about 2 minutes (projected).
- **Why this balance.** The dataset is a fixture, not evidence, and its information sits in
  one frame for the ladder and in the shape of a known curve for a candidate. Three ladder
  frames cut the projected time from 16 to 6 minutes at no loss of information. Each candidate
  keeps enough frames to trace its curve, which is cheap because the ladder is not run.
  `persistence_wasserstein` finished on two Taylor–Green frames (9.9 s each), but it stalled on
  `advecting_blobs` (that log), so its cost here beyond two frames is not known.

### Decisions and why

1. **A candidate is an option on the existing reader, not a new reader.**
   - Made by: Kareem, 2026-11-26, as a rule ("an analytic dataset is an option on an existing
     reader before it is a new reader", `BUILD_ORDER.md`, "How code is written for this
     plan"). The form the option takes is the agent's, 2026-11-26.
   - What was built: one generic option on the base class `ClosedFormTrajectory`, a mapping
     `candidate` of solution parameters to change. `predictions()` rebuilds the same class with
     those parameters. It works for every closed-form reader whose solution parameters are
     named as its constructor's keywords, so no reader needs its own candidate code.
   - Alternatives considered: the new reader `analytic_trajectory_pairs` sketched in spec 05,
     Sect. 3.5, which would have duplicated this reader's closed form; or one option per
     candidate (`candidate_nu`, `candidate_drift`), which would need repeating on every reader.
   - To reverse: remove `candidate`, `predictions()` and `frame_columns()` from
     `ClosedFormTrajectory` and the `candidate` keyword from the two readers that accept it.
2. **`evaluate.py` scores `predictions()` on any trajectory that has it.**
   - Made by: the plan's shared candidate hook (`BUILD_ORDER.md`, note under Phase 2); the
     exact line is the agent's, 2026-11-26.
   - The line is `prediction = trajectory.predictions() if hasattr(trajectory, "predictions")
     else None`. `ClosedFormTrajectory.predictions()` returns None when no candidate is set, so
     a reader without one runs the ladder as before. `ForecastPairs` and `fmeval/pipeline.py`
     needed no change, and the forecast tests pass unchanged.
   - Alternative: a default `predictions()` returning None on the base `Trajectory`. It is a few
     more lines for the same effect.
   - To reverse: restore `isinstance(trajectory, ForecastPairs)` and its import.
3. **A `drift` option makes the phase-drift candidate.**
   - Made by: the agent, 2026-11-26.
   - What it does: every field is translated by `drift` times $t$ at unchanged amplitude. With a
     drift the spatial patterns are recomputed each frame; without one they are computed once,
     as before, and the default output is bitwise unchanged (checked against the committed
     reader).
   - Why it is meant for the candidate only: the translated vortex solves the Navier–Stokes
     equations only with the uniform flow `drift` added, by Galilean invariance, so the
     reader's own frames keep the default of zero.
   - Alternative: the existing `translate_subpixel` degradation with `per_unit_time: true`. It
     acts on the analysis grid by interpolation, so its error is not exactly closed-form, and
     with a prediction set the ladder is not run.
   - To reverse: remove `drift` from the reader; nothing else uses it.
4. **Persistence is the candidate `{nu:0}`.**
   - Made by: the agent, 2026-11-26.
   - Reason: with zero viscosity the candidate's decay factor is 1, so it is the first frame at
     every step, which is persistence, provided the window starts at $t = 0$ (the default). It
     needed no code.
   - Caveat: with `t_start > 0` it is the $t = 0$ field, not the first frame of the window.
   - To reverse: nothing to remove; it is a choice of option value.
5. **Rows of a candidate run are labelled as a forecast's rows are.**
   - Made by: the agent, 2026-11-26.
   - What: with a candidate set, `ClosedFormTrajectory.frame_columns` gives every row
     `lead_step` (the frame's index), `lead_time` (its time since the first frame) and
     `param_resolution` (the grid's first extent), the three columns `ForecastPairs` supplies.
     The analysis then treats the rows as a forecast: each step is reported on its own
     (`forecast_by_lead`) and damage is read against the anchor in the same frame.
   - Why `param_resolution` is included: without it `make_report.py` failed in the
     `response_along_time` renderer, which converts that column to integers for the forecast
     figure. With it the report rendered with no errors (run `comparison_1795750322`).
   - To reverse: return `{}` from `frame_columns`; the rows would then be summarised as an
     ordinary probe, one median over every step, which the analysis deliberately avoids for
     forecasts.
6. **The `max_error` closed form of spec 05 holds only when 4 divides N.**
   - Made by: the agent, 2026-11-26 (its own derivation, checked by the test).
   - Spec 05, Sect. 3.3 gives `max_error` $= \cos^2(\pi/N)\,\lvert D - D' \rvert$. The cell
     centres sit at $(i + \tfrac12) \cdot 2\pi/N$. Both peaks of $\lvert\sin x\rvert$ and both
     of $\lvert\cos x\rvert$ fall half a cell from a centre, the factor $\cos(\pi/N)$ per axis,
     only when 4 divides $N$. On 25 cells the nearest centre is a quarter cell from the peak of
     $\sin x$, so that factor is $\cos(\pi/50)$, and one centre sits on the peak of
     $\lvert\cos x\rvert$ at $x = \pi$, so that factor is 1; when $N \equiv 2 \pmod 4$ a centre
     sits on the peak of $\sin x$. The test uses the exact maxima of $\lvert\sin\rvert$ and
     $\lvert\cos\rvert$ over each axis's centres instead. Spec 05 itself was not edited; the
     correction is recorded in step 9's status in `BUILD_ORDER.md`.
   - To reverse: not applicable; the spec's formula is wrong on other grids.
7. **`taylor_green_2d` stays out of `evidence_datasets`.**
   - Made by: the earlier decision recorded in `docs/decisions.md` and
     `configs/cards/default.yaml`, kept by Kareem's rule of 2026-11-26 in `BUILD_ORDER.md`,
     "The task": a dataset whose frames are scalar multiples of one another stays out.
   - Reason: the field is a single Fourier mode that only decays, so every frame is a scalar
     multiple of the first and adds no independent evidence. A candidate does not change
     that, because the truth's frames are what a card would cite.
   - To reverse: Kareem would have to change that rule; then add the configuration to
     `evidence_datasets` with a claim label.

8. **The budget test runs the three bundles through the pipeline, not by calling them.**
   - Made by: the agent, 2026-11-26 (build-order step 6).
   - What: `test_taylor_green_fixes_the_energy_enstrophy_and_palinstrophy_budgets` passes
     `RecomputingTrajectory(TaylorGreen2D(...))` to `fmeval.pipeline.run` with the
     reference-only ladder `build_ladder({})` and reads the values from the result rows, so
     vorticity is the harness's spectral curl of the velocity, as on every dataset, and not the
     reader's stored closed form.
   - Alternative: calling `kinetic_energy`, `enstrophy` and `palinstrophy` directly on
     `TaylorGreen2D.solution(t)`. It is a few lines shorter but would pin the reader's
     vorticity rather than the one a run uses, and `palinstrophy` would need a hand-built
     `FieldContext`, because `make_ctx` in `tests/conftest.py` takes one spacing for every axis.
   - To reverse: replace the `run(...)` call with direct calls; the assertions stay the same.

### Log entries

Entries are dated and newest last. Append a new entry at the end of this section; never
rewrite an old one.

**2026-11-26, agent (build-order step 9).**

- Code:
  - `fmeval/data/analytic.py`: the `candidate` option, `predictions()` and `frame_columns()`
    on `ClosedFormTrajectory`; `drift` and `candidate` on `TaylorGreen2D` (decisions 1, 3
    and 5).
  - `evaluate.py`: the one-line hook (decision 2).
- Tests, in `tests/test_analytic_datasets.py`:
  - wrong viscosity: all thirteen per-step metrics on the grids 48 × 32 and 25 × 64 against
    the closed forms of spec 05, Sect. 3.3, to $10^{-12}$ relative (`h1_relative` to
    $10^{-8}$, because the library adds $10^{-8}$ to its denominator);
  - phase drift: mean squared error $\tfrac12 D^2 (1 - \cos\delta_x \cos\delta_y)$, its root
    and `nrmse` to $10^{-12}$; kinetic energy, enstrophy and palinstrophy equal to the truth's
    to $10^{-12}$, and `spectrum_l2` below $10^{-12}$;
  - one end-to-end `evaluate.py` run, checking that only the clean entry, the anchor and the
    candidate are scored, the lead and resolution labels, and `nrmse` $= \lvert 1 - D'/D \rvert$;
  - refusals of an unknown candidate key and of a drift that is not a pair.
- Configuration: one comment line in `configs/dataset/taylor_green_2d.yaml`; no new file.
  Page: a section "Candidates with a known error".
- Verified:
  - the default `pytest` passed (2725 passed, 0 failed), as did `mkdocs build --strict`;
  - a smoke run of `python evaluate.py dataset=taylor_green_2d` with the thirteen metrics and
    `'+dataset.reader.candidate={nu:0.02}'`, written under
    `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets` (`comparison_1795750322`),
    where `nrmse` matched the closed form to $4 \times 10^{-16}$, and `make_report.py` on it;
  - the overrides `{drift:[0.03,-0.05]}` and `{nu:0}` run through `evaluate.py`;
  - the reader's default output is bitwise equal to the committed version.
- Not verified: persistence (`{nu:0}`) has no test of its own; it is the wrong-viscosity
  closed form with $D' = 1$, which the test covers only for $\nu' > 0$.

**2026-11-26, agent (what part is evaluated).**

- Decided which part of `taylor_green_2d` each experiment evaluates (section "What part is
  evaluated"), and wrote it as a comment block in `configs/dataset/taylor_green_2d.yaml`. No
  default changed.
- Measured with `python evaluate.py dataset=taylor_green_2d dataset.time.max_frames=2` and
  `metrics=[mse]`, `[persistence_distance]` and the full deterministic panel, then the
  wrong-viscosity candidate on 2 frames and the phase-drift candidate on 21 frames. The scripts
  and logs are under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/cost/`
  (`measure.sh`, `measure_named.sh`).
- Checked that the drift candidate's error returns to zero once in the window (0.0022 at
  $t = 47.5$ on $64^2$).
- Not verified: the 3-frame and 10-frame ladder times are projections from the 2-frame run,
  not runs; `persistence_wasserstein` beyond two frames.

**2026-11-26, agent (build-order step 6, the budget test).**

- Test: `test_taylor_green_fixes_the_energy_enstrophy_and_palinstrophy_budgets` in
  `tests/test_analytic_datasets.py`, through the real pipeline with `RecomputingTrajectory`
  (decision 8). It pins, with $D = e^{-2\nu t}$, $E = D^2/4$ for `kinetic_energy`,
  $\Omega = D^2/2$ for `enstrophy` and $P = D^2$ for `palinstrophy`, and the two budget
  relations $dE/dt = -2\nu\Omega$ and $d\Omega/dt = -2\nu P$ of Boffetta & Ecke (2012),
  Annu. Rev. Fluid Mech. 44, 427–451, Eqs. 5 and 6, using the exact time derivatives of the
  closed forms against the bundles' values. The derivation is in the test's docstring.
- Grids and times: the non-square grids 48 × 32 and 25 × 64, at $t = 0, 20, 40, 60$ with
  $\nu = 0.01$.
- Tolerance: $10^{-12}$ relative, which is round-off. Both derivatives, the curl and the
  palinstrophy gradient, are spectral, and a spectral derivative is exact for a single
  resolved Fourier mode; the cell-centre means of $\sin^2$ and $\cos^2$ over a whole period
  are exactly 1/2 on any grid of at least 3 cells. The measured error was at most
  $9 \times 10^{-16}$. The centred-difference factor $(\sin h/h)^2$ of spec 05, Sect. 3.3
  does not apply to these bundles.
- No bundle needed changing: all three satisfy the closed forms and the budgets as they are.
- Verified: the new test (2 passed) and the default `pytest` (2703 passed, 0 failed).
- Not verified: the equation number 5 for $dE/dt = -2\nu\Omega$ was taken from
  `FUTURE_EXPERIMENTS_CATALOG.md` (cluster G1) and the enstrophy card, without reading the
  paper; Eq. 6 is the one the palinstrophy card cites from p. 430. The test runs at the native
  grid only; on a coarsened analysis grid the block mean scales the amplitude, so the closed
  forms would not hold exactly.

**2026-11-27, agent (build-order step 14: the reader gained an acoustic part).**

- `TaylorGreen2D` gained the options `amplitude`, `sound_speed`, `longitudinal_viscosity` and
  `acoustic` (section `helmholtz_mixture_2d` below). With the defaults (amplitude 1, no sound
  speed) the output of `taylor_green_2d` is bitwise that of HEAD `97cd481`: 138 arrays compared
  (the default trajectory, a 25 × 64 window from $t = 1$ with $\nu = 0.03$, a drifting 48 × 32
  one, and the wrong-viscosity candidate of each).
- **Its frames are still scalar multiples of one another**, so it stays out of
  `evidence_datasets` (decision 7). The new options do not change that unless set.
- The new options are candidate parameters too, so `'+dataset.reader.candidate={amplitude:0.9}'`
  is a wrong vortex amplitude; it was not needed by any test and is not pinned.

### Open points

- No mean and spread over many initial conditions: this reader has one initial condition,
  and the harness scores one seed per run (spec 05, Sects. 2 and 3.1).
- The skill score of spec 05, Sect. 3.4 is an analysis, not built.
- `lead_step` counts from the trajectory's first frame, not from the first frame a run
  selects with `dataset.time.start`, as a forecast's lead counts from its file's start.

## `helmholtz_mixture_2d`

### What it is for

- **Fields whose solenoidal and dilatational parts are known in closed form.** Build-order
  step 14 (`dataset_specs/BUILD_ORDER.md`), following
  `dataset_specs/10_acoustic_and_helmholtz_fields.md`, Sect. 3 (Option A). The only stored
  field with a compressive part, `kinet_re5e4`, holds 1e-6 to 1e-5 of its velocity's
  fluctuation energy in it (spec 10, Sect. 1), so no metric's response to that part could be
  told from round-off.
- **The blind-axis test for curl-based metrics**, and the reference for the degradation
  `scale_dilatational`, which issue 057 named as the missing experiment for the planned
  Helmholtz-split metric (the proposal `EXP-orchestrator-20261023-dilatational-scaling.md`,
  deleted in this change because it is now built).
- **A candidate whose error is purely dilatational**: a wrong sound speed.

### How it is treated

- **Source.** The vortex of `taylor_green_2d` at amplitude $U$, plus the exact solution of the
  linearised isothermal equations about rest (the page's eqs. (7) and (8), spec 10's Eqs. (2)
  and (3), whose derivation is its author's; the split into uncoupled vorticity and sound modes
  is Chu and Kovásznay 1958, abstract).
- **Reader and options.** `taylor_green_2d` with `sound_speed: 2.0`, `acoustic:
  [{kind: potential, mode: [1, 1], amplitude: 1.0}]` (the vortex's mirror image), `grid:
  [64, 64]`, `n_frames: 9`, `t_end: 1.1`; $\nu = 0.01$ and $\nu_L = 2\nu$ by default.
- **Fields.** Velocity (both parts), pressure (the vortex's plus $c^2\rho'$) and vorticity (the
  vortex's alone). No density (decision 3).
- **Grid and boundaries.** Cell centres, both axes periodic.

### What part is evaluated

Decided by the agent on 2026-11-27, under Kareem's rule of 2026-11-26. The whole configured
trajectory is evaluated; the reader stores nothing.

- **Half an acoustic period, 9 frames.** Every frame is $D(t)\,\mathbf{u}_s + f(t)\,\mathbf{u}_d$
  for two fixed patterns, and with the default $\nu_L = 2\nu$ the two factors decay at the same
  rate $0.02$, so the velocity one period $2\pi/\Omega$ later is exactly a scalar multiple of
  the earlier one (my derivation from eq. (8): $\cos$ and $\sin$ return, and both envelopes
  fall by $e^{-0.02 \cdot 2\pi/\Omega}$); the pressure nearly is, its vortex term falling at
  twice that rate. Half a period, $\pi/\Omega = 1.11$, takes $f$ from 1 to
  $-1$, so the dilatational fraction runs from 1/2 to nearly 0 ($f = 0.008$ at $t = 0.55$) and
  back with the mirror image's sign reversed: every state the trajectory reaches, once.
  Spec 10 proposed 41 frames over $t = 0$ to 10, about nine periods of near-repeats.
- **The frames are not scalar multiples of one another** in velocity or pressure, since two
  patterns combine with a changing ratio; vorticity, the vortex's alone, is. So by
  `BUILD_ORDER.md`, "The task", it may be registered as evidence; it is not registered
  (instruction for this step), and `configs/cards/default.yaml` is untouched.
- **$64^2$.** Both parts are single Fourier modes, so every closed form holds on any grid of at
  least 3 cells; $256^2$ would cost about 16 times as much for no further answer.
- **Measured costs**, on a Perlmutter login node under a load of 35 to 50, results and
  `measure.sh` under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/helmholtz_mixture/`:

  | Run (all 9 frames) | Wall time |
  |---|---|
  | `mse`, `kinetic_energy`, `enstrophy`; default ladder with both dilatational entries on | 6.6 s (3.0 s applying the ladder) |
  | Every deterministic metric, same ladder | 90 s; 34 s of metric time, 3.8 s per frame (`spectral_energy_flux` 0.62 s, `energy_distance` 0.54 s, `persistence_wasserstein` 0.41 s); no stall |
  | Every deterministic metric, the candidate `{sound_speed: 2.5}` | 9.6 s |

  About 36 s of each run is fixed (start-up, calibration, writing folders). No disk.
- **Why this balance.** The whole set of distinct states costs a minute and a half for the
  full panel, so nothing is dropped; more frames or a finer grid would repeat answers.

### Decisions and why

Spec 10 was written before build-order steps 10 and 13 landed. Decisions 1 to 6 fit its design
to the code as it is now; all are the agent's, 2026-11-27.

1. **Options on `TaylorGreen2D`, no new reader.** By the plan's rule. The acoustic velocity is a
   spectral gradient of $\phi$, so neither step 10's `biot_savart` (velocity from vorticity) nor
   step 13's `potential` option on `AdvectingBlobs` (a transport map that displaces a density)
   applies; nothing of either was reused, and nothing duplicates them. The options are recorded
   in `params`, so step 9's `candidate` makes `{sound_speed: c'}` with no new code.
   - To reverse: remove the four options and the acoustic branch of `solution`.
2. **`scale_dilatational` acts on velocity alone (`fields=("velocity",)`), not as a
   `whole_frame=True` operator as spec 10 and the proposal wrote.** It needs only the velocity
   array. The ladder already passes a field the operator does not accept through unchanged,
   which is exactly what vorticity, density and pressure need; a whole-frame operator is refused
   on a non-periodic grid, is switched off on ensemble frames, and is called with a mapping, which
   every generic contract check would have had to special-case. The severity is the magnitude
   $s \in [0, 1]$ with the option `amplify` (spec 10's correction of the catalog's signed
   severity, kept), `preserves=("spatial_mean",)`, family `spectral`, not calibrated.
   - Consequence: the generic checks in `tests/test_degradation_contract.py` now hand every
     operator a two-channel field (`CHANNELS = 2`), since a velocity operator cannot take one
     channel; all 28 existing operators pass unchanged.
   - To reverse: declare `whole_frame=True` and return the other fields from the operator.
3. **No `density` field.** Spec 10 added $\rho = 1 + p/c^2$. That is an equation of state written
   by the reader, which the repository keeps out of readers; the pressure already carries the
   exact $c^2\rho'$, and no test needs density. The kinet comparison of spec 10, Sect. 4 (a job,
   not built) would need it; add it then.
4. **A standing plane wave is not an option**: it is two travelling waves with opposite modes,
   `{kind: plane}` twice.
5. **Overdamped modes are refused** ($\nu_L k \ge 2c$ anywhere on the grid), not computed with a
   complex $\Omega$, whose $e^{-\gamma t}\cosh(\beta t)$ overflows to NaN at long times. At the
   default $\nu_L = 2\nu = 0.02$ on $256^2$ this needs $c > 1.81$; the pulse override on the
   page uses $\nu = 10^{-4}$.
6. **`helmholtz_split(velocity, grid)` in `fmeval/derived.py`**, returning both parts, as spec 10
   proposed. No projection existed (`fmeval/derived.py`, `fmeval/external/kinet_spectral.py` and
   `biot_savart` were searched; issue 024 asked for one). Its callers are the operator and the
   tests; issues 024 and 057 now point at it.
7. **One configuration instead of spec 10's three.** `acoustic_pulse_2d` and
   `vortex_and_pulse_2d` are overrides; the page gives the pulse alone as an example.
8. **Both ladder entries are disabled by default** (`configs/degradation/default.yaml`): on an
   incompressible field every level would be flagged as doing nothing, and on `kinet_re5e4` the
   change is a few thousandths of the velocity's RMS. Enable them on the command line.
9. **The candidate's error with a travelling plane wave is not zero at $t = 0$**: its starting
   potential $\varepsilon c/k\,\sin(\mathbf{k}\cdot\mathbf{x})$ depends on $c$. It is still
   purely dilatational. The potential and the pulse start the same at any $c$, which is why the
   test uses the potential.

### Log entries

**2026-11-27, agent (build-order step 14).**

- Code: `fmeval/data/analytic.py` (`TaylorGreen2D`: `amplitude`, `sound_speed`,
  `longitudinal_viscosity`, `acoustic`, the per-mode propagator); `fmeval/derived.py`
  (`helmholtz_split`); the bundle `degradations/scale_dilatational/` (scaffolded by
  `python -m fmeval.cards new`, no exemplar panel generated; `python -m fmeval.cards check`
  passes); its entries in `configs/degradation/default.yaml`, `TEST_DESCRIPTION.md` and `LADDERS`;
  `docs/catalog.json` regenerated. Config `configs/dataset/helmholtz_mixture_2d.yaml`; page
  section "An acoustic part".
- Tests, in `tests/test_analytic_datasets.py`, through `pipeline.run` where the answer is a
  metric value, on 48 × 32 and 25 × 64 unless stated:
  - eq. (7) satisfied by a potential, an oblique plane wave and a pulse together (96 × 64), with
    fourth-order time differences, to 1e-9 of the largest term (measured 5e-11), at
    $\nu_L = 0.03$ and 0; zero curl (1e-12; measured 7e-15); acoustic energy constant at
    $\nu_L = 0$ to 1e-12 relative (measured 1.3e-15);
  - the travelling plane wave against its closed form, to 1e-13 (measured 2.5e-15);
  - `enstrophy` and `palinstrophy` below 1e-24 on the mirror image alone; `kinetic_energy`
    $E_d$ alone and $E_s + E_d$ with the vortex, `enstrophy` the vortex's, to 1e-12 relative;
    `helmholtz_split` returning each part to 1e-14 (measured 9e-16);
  - `scale_dilatational` at $s = 0.5, 1$ and amplified 0.5: `kinetic_energy`
    $E_s + \lambda^2E_d$ and velocity `mse` $(\lambda - 1)^2E_d$ to 1e-12, vorticity `mse`
    exactly 0, `enstrophy` unchanged;
  - the wrong sound speed: velocity `mse` $A^2(f_c - f_{c'})^2/4$ to 1e-12, vorticity `mse`
    below 1e-28, `enstrophy` equal to the truth's, no solenoidal part in the error (1e-14);
  - five refusals.
- Verified: the default output of `taylor_green_2d` is bitwise unchanged (entry above); the
  smoke and cost runs of "What part is evaluated", where at $t = 0$ the run read kinetic energy
  0.25 with the part removed and 1.25 with it doubled, and velocity `mse` $0.25\,s^2$.
- Not verified: spec 10's pulse against the free-space Bessel integral (its Eq. 4), the
  `h1_seminorm`, `spectrum_l2` and `spectral_energy_flux` answers of its Sect. 3.6, and the
  dilatational fractions it derived for `additive_noise` and `gaussian_impostor`: none is
  pinned by a test.

### Open points

- Spec 10's Option B, a kinet pulse run scored against this reader, is a job and not built; it
  needs the `forecast` half of step 1's conversion and the density field (decision 3).
- Not registered in `evidence_datasets` (instruction); its frames qualify (see above).
- The answers of spec 10, Sect. 3.6 listed under "Not verified".
- A broadband dilatational random field (spec 10, Sect. 5, a proposal for `random_field`) is
  not built.
