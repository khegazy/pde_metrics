# Build order for the datasets

## The task

Build the reference and candidate data that the metric tests need, as listed in
`FUTURE_EXPERIMENTS_CATALOG.md` and specified in `dataset_specs/0N_*.md`. Every dataset is one
of three kinds:

1. **Analytic.** A system with a closed-form solution is not stored. It is a reader that
   computes the fields on the fly when metrics are compared, in the `ClosedFormTrajectory`
   pattern of `fmeval/data/analytic.py`, as `sod_shock_tube` and `taylor_green_2d` do today.
2. **Simulated.** Produced by a numerical solver: kinet first (`00_how_to_use_kinet.md`), and
   OpenFOAM or another established solver where kinet cannot run the system. OpenFOAM is
   available on Perlmutter as Shifter container images (`shifterimg images` lists
   `opencfd/openfoam-default:2406` and `:2112`, checked 2026-11-26).
3. **Public simulation data.** A published simulation database (Johns Hopkins, The Well,
   PDEBench) used as reference data.

**Every dataset built here is an evaluation dataset** (Kareem, 2026-11-26): the metrics are
evaluated on it, and their behaviour on it measures how sensitive each metric is. So each one,
analytic readers included, is admitted to `evidence_datasets` in `configs/cards/default.yaml`
with a label naming the kind of claim it supports, as `sod_shock_tube` is labelled an "analytic
check". This replaces, for these datasets, the rule in `docs/decisions.md` ("Analytic fields are
fixtures; Sod is an analytic check"); that file was updated, and the datasets registered, in
step 29 (2026-11-27). A
dataset whose frames are scalar multiples of one another stays out, for the reason
`taylor_green_2d` does.

Candidate fields, the things a metric scores against a reference, are made in two ways: by the
repository's degradation operators applied to a reference, or by a solver run degraded in a
controlled way (a coarser grid, a wrong viscosity, a more diffusive scheme, a different
solver), which is the project's own protocol (`CLAUDE.md`, "Evaluation protocol", steps 1
and 2). Nothing in this work trains, runs or evaluates a machine-learning model.

Within each phase the order is value per unit of work, my judgement.

## How code is written for this plan (Kareem, 2026-11-26)

Use as much existing code as possible and write as little new code as possible. No aliases and
no functions that do very little. **When the plan and the current code's framework disagree,
change the plan to fit the code, not the code to fit the plan.** Concretely:

- a candidate that an existing degradation operator can make is made by that operator;
- an analytic dataset is an option on an existing reader (`fmeval/data/analytic.py`,
  `fmeval/data/synthetic_ensemble.py`) before it is a new reader;
- kinet output is fitted to the existing `kinet_raw` and `forecast` readers, not the reverse.

Every specification ends with a section "Existing code reused and new code needed", giving for
each piece the file it extends and a rough count of new lines.

**Every dataset keeps a log (Kareem, 2026-11-26).** The agent that adds or changes a dataset
writes or appends to `docs/datasets/logs/<page>.md`, one per dataset page: what the dataset is
for, how it is treated, every decision with its reason and alternatives, a dated entry for what
was done and verified, and the open points. The format is step 7 of
`docs/recipes/add-a-dataset.md`. Its reader is a future agent updating the dataset, who must
understand why it is in its current form. The logs are tracked in git.

**Every dataset decides what part of it is evaluated (Kareem, 2026-11-26).** Running every
metric on all of every dataset is too slow. For each dataset the agent chooses the windows,
stride, trajectories and analysis grid that balance enough independent evaluations for a good
measurement, the most distinguishing parts of the data, and evaluation time and disk; a small
dataset may be kept whole. The criteria and selectors are step 3 of
`docs/recipes/add-a-dataset.md`; the choice, the measured costs and the reasons go in the
dataset's YAML comments and in its log.

## How to use this file

This is the one record of the order in which the datasets are made. Any agent given a dataset
task reads this file first, takes the next step whose "Depends on" steps are done and whose
gate is open, and updates the Status column in the same change that completes the step. A new
step is appended with a new number.

**Gate: no agent creates a dataset, submits a job, runs a solver, or edits code until Kareem
approves the step.** As of 2026-11-26 only specifications exist, and Kareem has said not to
start launching jobs yet. His decisions so far, and the ones still open, are at the end of the
sequence.

## How data reaches the metrics (Kareem, 2026-11-26)

**Use the existing readers; move and convert the data to fit them.** No new reader is written
for kinet output. The metrics repository already reads kinet's shear-layer data through two
readers, and every new kinet dataset is brought into one of their layouts:

- **References go to the `kinet_raw` layout** (`fmeval/data/kinet_raw.py`). A flat HDF5 file
  with no groups: `density`, `velocity`, `vorticity` as `(N_sim, C, T, X, Y)` float64, a 1-D
  `time` dataset holding the physical time of every frame, and a root attribute
  `discretization`, a JSON string whose `spatial.grid`, `spatial.length` and `temporal.grid` the
  reader checks (`temporal.grid + 1` must equal the number of frames). The current kinet writes
  a grouped layout instead (`observables/<field>` of shape `(1, C, T, X, Y)`, the initial
  condition under `initial_conditions/`, the clock in `time/time_convection`;
  `00_how_to_use_kinet.md`, Section 5). So a move alone is not enough: a conversion script
  rewrites each grouped file into the flat layout, putting the initial condition back as frame
  0, keeping only the finite (stored) steps, and setting `temporal.grid` to the number of
  stored frames minus one when the run was saved every Nth step.
- **Candidates scored against a reference go to the `forecast` layout**
  (`fmeval/data/forecast.py`). One file per start, `forecast_t0-<start>.h5`, with one group per
  field (`rho`, `u`, `vorticity`) holding `pred_<step>` and `target_<step>` as `(C, X, Y)`, and
  groups `t` (physical time) and `t_index` (absolute solver step). For a coarse-grid candidate
  the target is the reference block-averaged to the candidate's grid, which is what the
  repository's conservative remap would do. Each run may sit on its own grid; the reader
  handles that.
- **Where the files go.** Under the repository's data root, `datasets/kinet/...`
  (`paths.data`, which is `/global/cfs/cdirs/m4790/Data`), in folders named like the existing
  ones, for example `kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids/sys_Re-25k_Ma-1en1/`,
  so a dataset config is a copy of `configs/dataset/_re5e4_simulation.yaml` with a new path.
  The project directory had about 9 TB free on 2026-11-26 (52 of 61 TB used); a converted
  256² trajectory of 1001 frames with density, velocity and vorticity is about 2.1 GB (my
  arithmetic), so 30 trajectories are about 63 GB and all 300 about 630 GB.
- **The conversion script is the one piece of new code Phase 1 needs.** It is a standalone
  tool, not a reader, so the readers stay exactly as they are. It is checked by reading one
  converted file with the existing reader and comparing every frame with the grouped original.

## How jobs are run (Kareem, 2026-11-26)

Jobs may be submitted to the **debug queue**, because the regular queue is too slow. A
simulation too long for one debug job may be submitted as one longer job on the regular
queue, **after the same configuration has been tested on the debug queue** (a short run of the
same case, grid and settings that completes and writes a readable file). Not yet: no job is
launched until Kareem says so. On Perlmutter the GPU debug queue allows at most
30 minutes of wall time per job, 2 running jobs and 5 submitted per user (`sacctmgr show qos`,
2026-11-26); the account `m4790` has access through its GPU association. kinet's own script
submits with `bash slurm_scripts/submit_perlmutter.sh simulate --nodes 1 --gpus-per-node 1
--time 00:30:00 --qos debug -- case=...` (`00_how_to_use_kinet.md`, Section 2, with the queue
changed). What fits, from the measured throughput (Phase 3 header):

- **Fits one job:** every 256² lattice-Boltzmann run (10 000 steps is about 2.5 minutes);
  several ensemble members or degraded runs per job; Taylor–Green and Sod refinement levels.
  A 512² run of 20 000 steps is about 19 minutes of stepping at 4.6e6 cell-steps per second,
  close to the limit once start-up is counted (my arithmetic).
- **Needs a longer job:** the forced 1024² run of step 22 (220 000 steps, about 8 hours at
  7.6e6 cell-steps per second, my arithmetic). It is tested first with a short debug run of the
  same configuration, then submitted as one regular job. Chaining debug jobs is the fallback;
  resume was verified to be bitwise exact.
- **Unknown until measured:** the PonD shock cases of step 18. Their 3.3e3 cell-steps per second
  was measured on a tiny grid; at the double Mach reflection's 1920 × 480 for about 4 000 steps
  that rate would take days, so their throughput must be measured at size before they are
  planned.

## How kinet runs are configured (Kareem, 2026-11-26)

- **Save only the macroscopic observables.** Every kinet run sets
  `io.record_distributions=false io.record_equilibria=false` (and leaves `io.record_iter_maps`
  at its default, false). The file then holds density, velocity, pressure (absolute only on the
  compressible physics), temperature, and the derived fields named in
  `case.physics.output_variables` (vorticity, dilatation). kinet still writes two scalar
  stability fields of the entropic collision, `stability_scale` and `momentum_time_scale`; no
  setting turns them off (`kinet/config/components/io.py` has only the three `record_*` flags),
  and the conversion drops them.
- **Checkpoints.** A resumable run also writes a simulation checkpoint
  (`sim_checkpoints/*.pt`), which holds the populations because a resume needs them
  (`00_how_to_use_kinet.md`, Section 3). It is not data and is deleted when the run completes.
- **Starting from a stored state.** New runs start from macroscopic fields through kinet's
  `initial_state` route. Where an exact continuation is wanted, the populations are read from
  data already on disk, never recorded anew: `kinet_re5e4` stores them at every step.
- **New experiments.** Where a system the tests need is not in kinet, an agent may add one to
  kinet: a case, an initial condition or a forcing law (Kareem, 2026-11-26). Additions go on a
  kinet branch created for this work, never on `perf/cleanup` or `main` directly; kinet's
  plugin route (the `plugins:` list in its `configs/config.yaml`) is an alternative where it is
  simpler. Each is built once its step is approved.

## Framework limits the partition decisions ran into (2026-11-26)

Each dataset's agent worked around these in its own config comments; they are recorded once
here so they are decided centrally. None is fixed.

1. **The persistence metrics dominate every panel's time.** Measured per frame:
   `persistence_distance` 142 s at 256² on the random fields and 11.4 s at 128² on the
   isotropic data; `persistence_wasserstein` over 30 minutes for one 256² frame (stopped), and
   33 to 530 s at 128² from issue 144. Every other metric together costs tens of seconds per
   frame. Options: run the persistence metrics on a coarser analysis grid, or on fewer frames,
   than the rest. The framework cannot do either per metric today.
   Separately, `persistence_wasserstein` stalled twice inside gudhi's `hera` routine on the
   first frame of a 21-frame `advecting_blobs` run at 64², yet took 0.4 s per frame on a 1 to 2
   frame selection; the cause is not diagnosed (`docs/datasets/logs/advecting_blobs.md`, open
   points). It also stalls on frame 90 of the radiative layer, alone on that frame for over 60 s
   while every other frame's whole panel takes 24 to 29 s
   (`docs/datasets/logs/turbulent_radiative_layer_2d.md`), and does not finish the first frame of
   `sedov_taylor`'s default ladder in 600 s, though it scores that frame against its candidate in
   0.15 s (`docs/datasets/logs/sedov_taylor.md`). Both bear on issue 144: the stall is
   input-dependent, not only a matter of grid size.
2. **A dataset config cannot set its analysis grid**, so a grid chosen for a dataset (128² for
   the isotropic data) is given on the command line and recorded only in comments.
3. **A degradation cannot be excluded per dataset**, so the kinet Sod configs must be run with
   `degradation.skip=[median_blur]`, whose square window wraps the 5 transverse nodes and would
   take about 11 minutes per frame.
4. **Nothing combines statistics across trajectories.** A dataset of many trajectories (the 5
   isotropic runs per Reynolds number) is evaluated as separate runs, one per trajectory, and no
   analysis pools their per-frame results into one measurement yet.

5. **The analysis cannot read a grid sequence.** `analyse` refuses the rows of several runs at
   different grids together, because their keys collide when `param_resolution` is not part of
   `ROW_KEYS`, and nothing computes an observed order of accuracy from successive grids (issue
   126). The Burgers test of step 5 computes the order from the rows itself.

## The sequence

Status values: `spec written` (the specification exists; nothing built), `spec to write`,
`blocked` (with the reason), `in progress`, `done`.

### Phase 1: bring existing kinet data into the existing readers (no simulation)

| Step | What | Specification | Depends on | Route and cost | Status |
|---|---|---|---|---|---|
| 1 | A conversion script from kinet's grouped layout to the existing readers' layouts (`kinet_raw` for references, `forecast` for candidate pairs) | this file, "How data reaches the metrics"; 00, Section 5 | approval | Standalone tool; checked by reading a converted file with the existing reader. The weakly compressible gauge pressure is not carried over (it is not absolute, issue 101). Small | in progress: the `kinet_raw` half is built and tested (`fmeval/data/convert_kinet.py`, `python -m fmeval.data.convert_kinet SRC DST`; contract and refusal tests in `tests/test_loader_contract.py`); the `forecast` half for candidate pairs is not built |
| 2 | Convert the decaying 2D isotropic realisations at `/global/cfs/cdirs/m4790/Data/neurde/hit_scaling/` (100 complete runs at each of Re 12.5k, 25k, 50k, own seeds, 1001 frames at 256²) into `datasets/kinet/homogeneous_isotropic_turbulence/...` and add their dataset configs | 01, Option C; 05, Option B | 1 | 30 trajectories first (about 63 GB). They are the unrelated realisations for every metric's damage anchor and the reference set of many initial conditions | first 30 done: 10 complete runs per Reynolds number drawn with `numpy.random.default_rng(0)` (keys and rule in `docs/datasets/decaying_isotropic_2d.md`) and converted, 30 files of 2.10 GB (63.0 GB, 156 s on the login node), each read back by the `kinet_raw` reader and equal to its source at frames 0, 1, 500, 1000 and on its clock; `004ae2` (not drawn) stays converted. Configs: fragment `_decaying_isotropic_2d` plus `kinet_hit_re12p5k`, `kinet_hit_re25k`, `kinet_hit_re50k`, the realisation chosen by `dataset.trajectory=<key>`; `kinet_hit_re25k_004ae2` folded into them. One smoke run per Reynolds number passes. The other 270 runs are not converted; registered as evidence in step 29 |
| 3 | Add a dataset config for the 512² run of the reference shear layer beside `kinet_re5e4` | 02, Sect. 5.1 | approval | Already in the flat layout and already in place; a config only. A two-level solver comparison of the reference | done as a config: `kinet_re5e4_512` (`frame_stride: 2`, 20001 frames) passes a smoke run; registered as evidence in step 29; the node-placement check of 02, Sect. 5.1 is still open |
| 4 | Convert the kinet Sod runs and the Mach 1.8 obstacle flow already on disk | 02, Sect. 5.2; 03, Sect. 4.7 | 1; issue 046 for the non-square Sod grid | Grouped layout with absolute pressure, converted keeping `pressure`. Solver shocks in 1D and a bow shock in 2D | Sod done, obstacle blocked. `convert_kinet` now reads kinet's older grouped layout (clock `time/time`; no `pressure_convention`, so pressure is taken as absolute only where the initial p = rho T). The three Sod runs are converted to `<run>_flat.h5` beside each (481 MB, 5 to 10 s each) and read back equal to the source at all 1001 frames and on the clock (a `-m data` test pins `d17baf`). Configs: fragment `_kinet_sod` plus `kinet_sod_gamma1p4` and `kinet_sod_gamma2` (`c76b17` default, `15aa6b` by `dataset.trajectory`), read as 2D 3001 x 5, Neumann along the tube, periodic across it; every field is uniform across it, so issue 046 changes nothing here. Smoke runs with `mse` and `shock_set_distance` pass; spectral metrics are not run, coarsening is dropped (5 nodes), the median blur is skipped for cost, and the detector flags no shock in the gamma 2 run. The obstacle run is refused: it stopped at step 155 of 1000 (`interrupted`); it needs finishing, a boundary type for its inlet and a cylinder mask (`docs/datasets/supersonic_cylinder.md`). Both Sod runs registered as evidence in step 29; scoring the Sod runs against the exact solution (02, Sect. 5.2) is not built |

### Phase 2: analytic readers, computed on the fly (no data to make)

| Step | What | Specification | Depends on | Route and cost | Status |
|---|---|---|---|---|---|
| 5 | Burgers with the Cole–Hopf solution | 02, Sect. 4.5 | approval | The observed-order code path in one dimension. A day | done as a reader and tests; the analysis side is not built. One new reader `Burgers` (`burgers`, a `ClosedFormTrajectory` in `fmeval/data/analytic.py`; no existing reader is a viscous scalar equation): u_t + u u_x = ν u_xx on the periodic [0, 2π) from u = −sin x, field `velocity` (one channel, as Sod's), the Fourier–Bessel series of spec 02's Eq. in Sect. 4.5 (Cole–Hopf from Gesztesy & Holden 1998, Lemma 3.1; DLMF 10.35.2; re-derived), checked against a heat-kernel quadrature of the same transformation (4.8e-13) and by the tests. Options `nu` (default 0.1, refused below 0.05, where the series' round-off, ε e^{1/ν}, reaches 2e-8) and `scheme` (`exact`, `central`). The candidate with a known order is `candidate={scheme: central}`: second-order centred differences of u²/2 and u_xx on the reader's own cells, integrated by `solve_ivp` (DOP853, time error 7e-12 against a spatial 5e-5 on 512 cells); chosen over sampling the exact solution as cell averages, which also gives order 2 but tests no solver; spec 05's degraded-solver candidate in miniature. Asserted in `tests/test_analytic_datasets.py`: the start −sin x; the residual of the equation by centred differences falls by 4 ± 0.1 when h and dt halve (3.994 to 3.9995); the observed order p = ln(L_k/L_{k+1})/ln 2 (Roy 2005, Eq. 8) of `rmse` and `max_error` through `pipeline.run` on 64, 128, 256, 512 cells at four times, 1.93 to 2.02 on (64, 128) and within 0.006 of 2 on the finer pairs (asserted 0.1 and 0.01); six refusals. Config `burgers` (256 cells, t = 0.5 to 2 in 4 frames, kept whole: the 20 metrics that run on a 1D velocity with the default ladder 14 s wall; the grid sequence as one multirun, `'+dataset.reader.grid=[64],[128],[256],[512]'`, 6.1 s); page `docs/datasets/burgers.md` with its figure, log `docs/datasets/logs/burgers.md`. **Still unbuilt (issue 126):** nothing in `fmeval/analysis.py` or the report computes p from rows at several resolutions; it needs a function over several run folders grouped by metric, field and time and ordered by `param_resolution`, and `analyse` refuses the concatenated rows today because `param_resolution` is not in `ROW_KEYS`. Registered as evidence in step 29 |
| 6 | A unit test pinning `kinetic_energy`, `enstrophy` and `palinstrophy` on `taylor_green_2d`, where dE/dt = −2νΩ holds exactly | catalog G1; 02, Sect. 4.1 | approval | Reader exists. Hours | done: `test_taylor_green_fixes_the_energy_enstrophy_and_palinstrophy_budgets` in `tests/test_analytic_datasets.py` runs the three bundles through the pipeline on the reader's frames (vorticity recomputed spectrally from velocity) on the non-square grids 48×32 and 25×64 at four times, and asserts E = D²/4, Ω = D²/2, P = D² (D = e^(−2νt)) and both budgets dE/dt = −2νΩ, dΩ/dt = −2νP to 1e-12 relative; the bundles satisfy them unchanged (measured error below 1e-15, since both derivatives are spectral). `taylor_green_2d` stays out of `evidence_datasets`, its frames being scalar multiples of one another ("The task") |
| 7 | Closed-form shock fields: Sod at a shifted time, then cylindrical Sedov–Taylor and Noh. The tilted stripe and geometric ellipses are fronts of the feature-population generator (step 12), built only there | 03, Sects. 3.1 to 3.8; 06 | approval; a decision on admitting closed-form fields as evidence | Every geometric error with a known answer, and frames with no shock. Seconds per run | in progress: built; `sedov_taylor` and `noh` registered as evidence in step 29. **Sod at a shifted time**: no new reader; `SodShockTube` gained `time_offset` (every frame at t + dt) and the generic `candidate`, so the candidate is `'+dataset.reader.candidate={time_offset:dt}'` (defaults bitwise unchanged; no config added; override and known answers on `docs/datasets/sod_shock_tube.md`). **Sedov–Taylor** (`sedov_taylor`) and **Noh** (`noh`): two new `ClosedFormTrajectory` readers in `fmeval/data/analytic.py` (no existing reader is a radial Euler solution), sharing one function `polar`, each on [0, 2)² with the axis at the centre, Neumann on both axes, a positive ambient pressure 1e-6 for the detector (the closed forms have 0; no pressure from density), `time_offset` and `candidate`. Sedov is the full similarity solution, not a front with a stand-in interior: Kamm & Timmes's parametric profiles specialised to j = 2, ω = 0 (from Timmes's public `sedov_library_qp.f90`, read; the LA-UR PDF could not be rendered, so equation numbers are the code's), inverted by bisection in log s, with α = 0.9840740 integrated (Gauss–Legendre; the same integral at j = 3 gives their spherical 0.851072); their printed E = 0.311357 then puts the front at 0.749994 at t = 1, not 0.75 (α implied 0.98404, 3.3e-5 lower), recorded in the log. γ restricted to (1, 2). Noh from Sutherland (2010, Table 9, read on ar5iv; Noh 1987 not opened), generalised to any γ, ρ₀, u₀ by our derivation (D = (γ − 1)u₀/2, ρ₂ = ρ₀((γ + 1)/(γ − 1))², p₂ = ρ₂Du₀), checked by the tests; the detector's γ = 1.4 is an override. Asserted in `tests/test_analytic_datasets.py` (all through `fmeval.pipeline.run` where a metric is involved): Sod at dt = 0.001, 0.003, 0.01, `shock_set_distance` = (s − ½)dx and `shock_set_hausdorff` = s dx to 1e-12 with \|s dx − S_R dt\| ≤ dx, and `max_error` = p* − p_R and u* at every offset (the jumps unchanged); Sedov's Euler equations behind the front (residual 3e-7, tol 1e-5), mass (3e-8, tol 1e-6), strong-shock flux balance at u_s = dr₂/dt (1e-8, tol 1e-6), r₂(1) = 0.75 to 1e-5; Noh's published values exactly, jump balance at γ = 5/3 and 1.4 (1.4e-9, tol 1e-7), continuity ahead of the shock, no shock flagged at t = 0; time-offset and energy candidates on 128×96 and 96×160: ASSD and Hausdorff within one cell of Δr at four times, every flagged cell within one cell of its circle, every point between Δr − 2dx and Δr + dx; 15 refusals. Configs `sedov_taylor` and `noh` (reader defaults: 4 frames on 128², Sedov t 0.25–1, Noh t 0.5–2), pages `docs/datasets/sedov_taylor.md`, `noh.md` with dynamics figures, logs `docs/datasets/logs/{sedov_taylor,noh}.md`, Sod log appended. Evaluated part: each dataset kept whole (4 deterministic frames, known answers, not samples); measured: every deterministic non-persistence metric on the default ladder 21 s (Sedov) and 31 s (Noh) wall, `persistence_distance` 6 s per frame, `persistence_wasserstein` 5.2 s per frame on Noh but over 600 s on one Sedov frame (stopped; 0.15 s on the candidate pair), another instance of framework limit 1; candidate runs 3 to 6 s. Left out: the tilted stripe and ellipses (step 12 built them as `advecting_blobs` fronts); Sect. 3.8's displaced (not enlarged) circle with ASSD near (2/π)s, and the Schaal–Springel flagged-count check, not pinned; a Rankine–Hugoniot residual metric (issue 051) does not exist, so 'jumps unchanged' is read through `max_error`; `proposals/EXP-sod_evidence-sod-time-offset.md` is now built and left for the coordinator to delete |
| 8 | The stochastic advection–diffusion ensemble | 01, Option A | approval | An exchangeable ensemble along a lead-time axis with closed-form spread, error, rank histogram and CRPS | spec written |
| 9 | Analytic candidate trajectories: advection–diffusion with a wrong speed or diffusivity, upwind and Lax–Friedrichs schemes on advection, Taylor–Green with a wrong viscosity or a phase drift, and the persistence, climatology and unrelated-realisation references | 05, Option A | approval | Exact error-against-step curves for the thirteen per-step metrics. A day | in progress: built as options on the existing readers, no new reader. Every `ClosedFormTrajectory` takes a reader option `candidate`, parameters of its solution to change; `predictions()` rebuilds the reader with them on the same grid and frames, and `frame_columns` labels the rows as a forecast's (`lead_step`, `lead_time`, `param_resolution`), so the forecast analysis and figure apply unchanged. `taylor_green_2d` gained `drift` (a translation growing linearly in time) and `advecting_blobs` `diffusivity` (exact Gaussian spreading); defaults leave both bitwise unchanged. Built: Taylor–Green with a wrong viscosity (`candidate={nu:...}`), a phase drift (`{drift:[...]}`) and persistence (`{nu:0}`); advection–diffusion on `advecting_blobs` with a wrong speed (`{velocities:...}`), a wrong diffusivity (`{diffusivity:...}`), persistence (zero velocities) and an unrelated realisation (`{seed:...}`); climatology is the anchor `mean_field`, which every candidate run already keeps. `tests/test_analytic_datasets.py` asserts all thirteen per-step metrics on Taylor–Green against spec 05, Sect. 3.3 on 48×32 and 25×64 to 1e-12 (`h1_relative` 1e-8, its 1e-8 epsilon), the blob MSE of two Gaussians (wrong speed, diffusivity, both) to 1e-10, and one end-to-end `evaluate.py` run. Correction to 05, Sect. 3.3: `max_error` = cos²(π/N)\|D − D′\| only when 4 divides N; the test uses the per-axis maxima. Remaining: (1) the upwind and Lax–Friedrichs scheme candidates (Eqs. 4–6), which need the field as Fourier modes times an amplification factor per step, which neither reader has (about 20 lines on `advecting_blobs` plus a Courant number and a steps-per-frame option); (2) the random-phase multi-mode field of Sect. 3.1 and the many-seed mean and spread over initial conditions, which the harness does not aggregate over seeds (one seed per run); (3) Sect. 3.4's skill score, an analysis, not a dataset. Not registered as evidence |
| 10 | Random fields with known statistics: Gaussian fields of prescribed spectrum (power law, broken power law, Matérn), anisotropic Gaussian fields, g² − 1 (increment flatness exactly 9), log-normal and multifractal fields with exact flatness at every separation, Pareto-spiked fields, and the stationary Ornstein–Uhlenbeck time series of spec 04 A3 | 09; 04, Option A3 | approval; the shared random-field draw (below); issue 044 before the configs are registered | A `ClosedFormTrajectory` subclass in `fmeval/data/analytic.py` (an ensemble reader would score the member mean, so not an option on `synthetic_ensemble`). About 140 lines in the reader, 45 of closed-form targets in `tests/analytic_fields.py`, 90 of tests. The light-tail checkerboard fixture belongs to the future moment-estimator bundle's tests | in progress: built as one new reader, `RandomField` (`random_field`, a `ClosedFormTrajectory` in `fmeval/data/analytic.py`), not an option on `advecting_blobs` (no per-frame draw, time correlation or transforms, and a pressure field these fields must not have; `docs/datasets/logs/random_field.md`, decision 1). Reused: the draw is `_apply_filter` on `derive_rng` white noise; `AdvectingBlobs`'s inline background spectrum and its Biot–Savart inversion became the module functions `band_transfer` and `biot_savart`, which both readers call (`advecting_blobs` bitwise unchanged, its tests pass); the anisotropic stretch is a new optional argument of `wavenumber_magnitude`; candidates use step 9's `candidate`. Families built, as reader options: Gaussian with one smoothly broken power law that is also a pure power law and exactly the Matérn density (Porcu et al. 2023, Eq. 23); anisotropic; `hermite2` (g² − 1) and `exp` (log-normal) density; multifractal velocity and vorticity (Lakhal et al. 2025); Pareto spikes on density (a reader option, since X4 is not built; to be deleted when it is); per-mode Ornstein–Uhlenbeck frames (`tau`; `tau = inf` is the persistence candidate). One spectrum serves density and velocity (Eqs. 8, 9, 11 are exact for any spectrum). Dropped from spec 09: `density_mean`, `multifractal_scale` (the box), `length`. Asserted through `pipeline.run` in `tests/test_analytic_datasets.py` (9 tests, 13 cases, non-square grids except the Hill value): spectrum shapes and curl/divergence to 1e-12; S₂ along each axis, isotropic and anisotropic (a = 2), within 4 exact standard errors; flatness 3 on all fields within 0.08; W1 = |σ₁ − σ₂|√(2/π) within 6%; Hill 0.0928 on 256² within 0.004; Pareto 1/α (α = 2, 4; fraction 2/√n) within 7%; Hermite 9, log-normal Eq. 9 and multifractal Eq. 11 flatness at every separation within 8%, 12%, 8% of 48-frame means; OU lag correlation within 4 standard errors per frame; flatness 3 on every level of the default ladder's 12 linear operators. Tolerances measured over seeds and stated in each docstring. Config: one, `random_field` (Gaussian null, 12 frames on 256²; other families as override lines on its page `docs/datasets/random_field.md`); log `docs/datasets/logs/random_field.md` with the evaluated-part decision and measured costs. `evaluate.py` smoke runs pass (default ladder, 33 frames, 4 metrics, 6 min; intermittent override, quick ladder, 38 s). Remaining: (1) one config per family with its own `evidence_datasets` label, if the other families are to be cited (the Gaussian null `random_field` is registered in step 29; issue 044 is to be decided before its evidence is produced); (2) spec 09's Eq. 6 (`energy_distance`), the `tail_exceedance` bias and the `spectrum_l2` null floor, derived but not asserted; (3) moving the spikes to X4 when built; (4) the dynamics figures |
| 11 | Synthetic-ensemble extensions: the Gneiting forecasters, flow-dependent spread, spatially correlated members, Student-t and two-piece-normal members, a wrong-centre ensemble, a positive-density variant | 08 | approval; Kareem's decision on issue 044 (passing the run seed to the reader changes every number on the four ensemble cards) | Options on the existing `synthetic_ensemble` reader and three operators in the existing ensemble registry; about 80 new lines. Defaults leave today's output bitwise unchanged | in progress: the reader options and operators are built and tested; nothing is registered as evidence. `synthetic_ensemble` takes `base` (`two_scale`, `case_means`, `zero`), `sigma_ratio`, `noise_length`, `noise_covariance` (`exponential`, `rational`; drawn by `_apply_filter` on seeded white noise, with a positive-definiteness check), `member_noise_length`, `member_noise_covariance`, `member_offset` and `log_amplitude`; the defaults reproduce HEAD bitwise (checked on three grids, including a two-field and a 3D one). Three bundles in the ensemble registry: `gneiting_forecaster` (probe, `ordinal=False`, stochastic, kinds `climatological`, `unfocused`, `hamill`), `flow_dependence` (`direction` `damp`/`amplify`, through `scale_spread`, which now takes a per-cell factor) and `member_shape` (`family` `student_t`/`two_piece`); `flow_dependence` and `member_shape` declare `preserves: [ensemble_mean]`. Ladders: `configs/degradation/gneiting_forecasters.yaml` (new, three probes and the anchor) and four enabled entries in `ensemble_miscalibration.yaml` (`flow_dependence_damp`, `flow_dependence_amplify`, `heavy_tails`, `skew`). Known answers asserted through the metrics in `tests/test_synthetic_ensemble.py`: the four Gneiting CRPS values (0.5642, 0.6144, 0.6319, 0.7979) within four frame standard errors (about 0.0025) on 12 frames of 64²; `spread_skill` and `ensemble_mean_rmse` unchanged to 1e-12 under both mean-preserving operators; the binned spread-error slope divided by a for damp 0.5 and 2 and amplify 1 to 1% and a uniform spread at damp 1; `variogram_score` rising under independent member noise (paired t 7.0 over 12 frames of 32²) while `crps` and `ensemble_mean_rmse` stay within |t| < 3; the Student-t CRPS closed form (Jordan et al. 2019, App. A.2.5) at nu = 5 and 2.5 within four standard errors; and reader checks of the sigma profile, the exponential covariance, the unchanged ranks under `log_amplitude` and the member offset. Both new mean-preserving operators trigger issue 111 (damage per change about 1e29 to 1e30, measured), as `spread_inflate` does; not fixed here. Remaining: (1) issue 044's `seed: ${seed}` is not added, pending Kareem's decision; (2) the five dataset configs of spec 08, Sect. 6.1, and their `evidence_datasets` entries; (3) the exemplar panels of the three bundles (not generated; no test requires them); (4) Eq. 6 (deflation under bias) and Eq. 7 (log-normal CRPS) are not asserted by a test; (5) the binned spread-error figure is a separate change to `spread_skill` |
| 12 | The feature-population generator: vortices (Gaussian, the Lamb–Oseen vortex at a fixed time), fronts (straight stripe or ellipse, tanh profile, absolute pressure) and positive bumps on an optional random background, with single-feature candidates (move, rescale, remove, add, flip sign, rotate) | 06 | approval | Options on the existing `advecting_blobs` reader, not a new reader; global candidates by existing degradation operators. About 90 to 120 new lines in the reader plus tests and configs. The duplicate Gaussian bump in `tests/analytic_fields.py` is merged with the reader's when this is built | in progress: Option A built as options on `AdvectingBlobs`, no new reader and no second candidate mechanism. `FIELDS` is now density, velocity, vorticity, pressure; per-feature `kinds` (`bump` to density, `vortex` to vorticity with its velocity by spectral Biot–Savart, mean removed; `front` to pressure, a tanh of `front_thickness` cells of the finer axis), `centres`, `width`, `amplitude`, `aspect`, `orientation`, `directions` (coprime (p, q) for a straight stripe, (0, 0) for an ellipse); `background` draws `_apply_filter` on white noise from `derive_rng(seed, "background", 0, field)`, so it is exactly Gaussian with the band's power law and its rms is the expected one, not the realised one (spec 06's fixed-amplitude draw is replaced, per the shared prerequisite). Defaults are bitwise those of HEAD and of step 9 (checked on three grids and two diffusivities). Single-feature candidates are step 9's `candidate` with one per-feature list changed: move (`centres`), wrong speed (`velocities`), rescale or flip sign (`amplitude`), remove (amplitude 0, which adds exactly 0.0), add (a feature the reference holds at amplitude 0), rotate (`orientation`, `directions`); spec 06's `{feature: j}`, `{remove}`, `{add}` design is dropped. `tests/analytic_fields.py`'s bump is now built from the reader (minimum image instead of 3 × 3 images; its tests pass unchanged). Config `feature_population` (one static 128² frame: four bumps, four paired vortices, a circle, an ellipse at 30° and a stripe) replaces spec 06's three; `evaluate.py` smoke run of removing its weakest bump gives MSE = πw²a² and persistence 0.15, every other field 0. `tests/test_analytic_datasets.py` asserts through the pipeline on non-square grids: defaults bit for bit; Biot–Savart round trip to 1e-12 of the peak; the double-penalty crossover at 1.665 w (MSE of move and removal to 1e-12); persistence h/2 for removal and addition and 0 for a whole-cell move (1e-12); `increment_w1` exactly 0 for a whole-cell move, 0 to 1e-15 for a centred vortex's sign flip (whose MSE 4πw²a² − 4Γ² holds to 1e-12), and the exact discrete removal value; a straight front's ASSD (s − ½)Δx on faces and sΔx through centres with Hausdorff sΔx (1e-12); the background's band, rms and cancellation; nine refusals. Finding: at spec 06's isolation of 12 widths the Gaussian tails overlap at 1.5e-8 and measurably break the exact increment and persistence answers; the tests place features 20 widths apart, and the reader refuses no overlap (features are summed). Remaining: spec 06's answers not yet pinned (ellipse rotation (a − b)δφ, circle ASSD values, pooled dilution, spectrum changes, the velocity error of Eq. 6, `wasserstein` bounds, sub-cell and rescale persistence, the 45° detector limit); time-dependent and background-sweep configurations; Option B (kinet run, needs jobs); step 7's ellipses and tilted stripe are these fronts |
| 13 | Known-answer transport pairs: a manufactured Monge–Ampère map with an exact W₂ (one mode against a uniform density gives W₂ = H⁻¹ = a/(√2\|k\|)), circle profiles and their products (the torus W₂² of p(x)q(y) is the sum of two circle W₂²), translations, Gaussians for planned sliced and Sinkhorn metrics, a signed single mode | 07 | approval; the shared candidate hook (below) | Three options on the existing `advecting_blobs` reader; other candidates are existing degradations; the inaccurate circle oracle in `metrics/wasserstein/test_metric.py` (0.1000253 for an exact 0.1 on near-empty densities) is replaced by an exact one in `tests/conftest.py`. About 200 new lines | in progress: built as one option on `AdvectingBlobs`, `potential` (modes `[m_x, m_y, a, phi]` of spec 07's Eq. 4, refused unless sum \|a\| < 1 and integer m), which maps the density to f = g(x + grad u) det(I + D²u) and exposes `displacement` (grad u) for Eq. 3; nothing else in the reader. Fitted to the current code: `amplitude` 0 existed (step 12); `reverse` dropped, since a plain reference with `candidate={potential:[...]}` is the pair the other way round (step 9's `candidate`); `predictions()` and the `evaluate.py` hook existed; `transport_distance(t)` dropped for Eq. 3 in the test on a refined reader; no stripe shape (one or two axis modes at height 0 give stripes and products). Defaults and `feature_population` bitwise unchanged (592 arrays against HEAD). The circle oracle is `circle_w2` in `tests/analytic_fields.py` (the repository's helper module for closed-form targets, not `conftest.py`): exact piecewise integration of the quantile functions, 0.1 to 2e-15 where the old solver gave 0.1000253; the `wasserstein` circle test now uses it at 1e-8 (was 2e-4; measured 1.7e-9). Tests in `tests/test_analytic_datasets.py` through the pipeline: one mode (W₂ = H⁻¹ = a/(√2\|k\|)) to 1e-12 from the deformed side up to a = 0.998 and 1e-5 with a tenfold fall on refinement from the uniform side; Saumier's map (λ = 0.45) with g = 1 (Eq. 6, 1e-12) and with the blobs at height 3 (Eq. 3, 1e-5), both ways; a product pair (Eq. 8, 1e-5) both ways; a translated product at its circle distance (1e-5) and translated blobs inside the marginal bracket; five refusals. The NaN threshold (uniform side, between a = 0.94 and 0.965, not monotone) is documented in the log, not pinned. Config `transport_pairs` (blobs at height 3 against their pull-back, 21 frames on 64², exact W₂ 0.0497 to 0.0515; whole panel 13 s wall, `persistence_wasserstein` 3 s); other pairs are overrides on the page. Log: `docs/datasets/logs/advecting_blobs.md`, decisions 18 to 24. Remaining: the background-ratio sweep (Sects. 3.3 and 3.4, needs a stripe bump), the Gaussians (3.5) and signed fields (3.7) for unbuilt metrics, Option B (POT), the Sect. 3.6 findings on the `wasserstein` card. `feature_population` (step 12) and `transport_pairs` registered as evidence in step 29 |
| 14 | Acoustic and Helmholtz fields: Taylor–Green (solenoidal) plus an exact linear acoustic part per Fourier mode (plane wave, potential field, Gaussian pulse) with a chosen energy split; and the `scale_dilatational` degradation | 10 | approval; step 9 (it extends the same `TaylorGreen2D` reader and its candidate mechanism) | About 65 lines in `TaylorGreen2D`, a 15-line `helmholtz_split` in `fmeval/derived.py`, a 15-line degradation bundle, 120 lines of tests. A kinet pulse run (256², 2000 steps, about 17 s, one debug job) has a predicted distance from the exact solution of 0.77% at 200 steps and 7.2% at 2000 | in progress: Option A built as options on `TaylorGreen2D`, no new reader: `amplitude` (U), `sound_speed` (c; None keeps the reader as it was), `longitudinal_viscosity` (default 2ν) and `acoustic`, a list of starting conditions `plane` (a travelling wave; a standing one is two), `potential` (φ = A cos mx cos ny, the vortex's mirror image at (1, 1)) and `pulse`, each propagated mode by mode with spec 10's Eq. 3, translated by `drift`, all candidate parameters. Defaults bitwise those of HEAD (138 arrays). Fitted to the current code: `scale_dilatational` acts on velocity alone (`fields=("velocity",)`) instead of `whole_frame=True`, since the ladder already passes other fields through and a whole-frame operator is refused on walls and called with a mapping; the generic contract checks now use two-channel fields (`CHANNELS = 2`), all 28 existing operators passing unchanged; no density field (ρ = 1 + p/c² would be an equation of state in the reader; the pressure carries c²ρ'); overdamped modes (ν_L|k| ≥ 2c) refused rather than computed; nothing of steps 10 or 13 applies (the velocity is a gradient of φ). `helmholtz_split` (Fourier projection, both parts) is new in `fmeval/derived.py`; no projection existed. Operator: magnitude severity in [0, 1], `amplify` option, `preserves=("spatial_mean",)`, family `spectral`, uncalibrated; `LADDERS`, `TEST_DESCRIPTION.md`, and `scale_dilatational_down`/`_up` in `configs/degradation/default.yaml` at 0.25 to 1, disabled. No exemplar panel. The built proposal `EXP-orchestrator-20261023-dilatational-scaling.md` is deleted; issues 057 and 024 point at the projection. Asserted through the pipeline on 48×32 and 25×64 in `tests/test_analytic_datasets.py`: Eq. 1 of spec 10 by fourth-order time differences to 1e-9 of its terms (96×64), zero curl, acoustic energy constant at ν_L = 0 to 1e-12, a travelling plane wave to 1e-13; enstrophy and palinstrophy below 1e-24 on a pure dilatational field, kinetic energy E_s + E_d and each part recovered by the split (1e-12, 1e-14); `scale_dilatational`: kinetic energy E_s + λ²E_d, velocity mse δ²E_d, vorticity mse exactly 0; a wrong sound speed with velocity mse A²(f_c − f_c')²/4, vorticity unchanged and no solenoidal error; five refusals. Config `helmholtz_mixture_2d` (vortex plus mirror image, c = 2, 9 frames over half an acoustic period on 64², whole trajectory evaluated: full deterministic panel with the dilatational ladder 90 s wall, candidate 9.6 s); its velocity and pressure frames are not scalar multiples of one another. Log: `docs/datasets/logs/taylor_green_vortex.md`. Remaining: the kinet pulse run (Option B, a job), spec 10's Sect. 3.6 answers for `h1_seminorm`, `spectrum_l2`, `spectral_energy_flux`, the pulse against its Bessel integral (Eq. 4). Registered as evidence in step 29 |

**Shared prerequisite of steps 9, 12 and 13: one candidate hook.** Specs 05, 06 and 07 each
need an analytic reader to supply its own candidate trajectory. The existing route is the one
`forecast_re5e4` uses: `evaluate.py` scores a dataset's `predictions()` against its frames. The
change is to call `predictions()` on any trajectory that has it, not only on `ForecastPairs`
(`evaluate.py`, near line 106; about one line). It is made once, with the first of those readers.
**Done** with step 9: `evaluate.py` now reads `prediction = trajectory.predictions() if
hasattr(trajectory, "predictions") else None`, and `ClosedFormTrajectory.predictions()` returns
None without a candidate; `ForecastPairs` and `fmeval/pipeline.py` needed no change, and the
forecast tests pass unchanged.

**Shared prerequisite of steps 10, 11, 12 and X1: one random-field draw.** Specs 06, 08 and 09
each proposed their own way to draw a Gaussian random field. There is one: the existing
`_apply_filter(white, transfer)` (`degradations/_shared/filters.py`) applied to seeded white
noise with `transfer` the square root of the target spectral density draws an exactly Gaussian
field with that covariance on the grid. No new function is written, and nothing is moved:
`fmeval` already imports from `degradations/` (`fmeval/ladder.py`, `fmeval/io.py`), so a
reader imports `_apply_filter` where it is. `gaussian_impostor` keeps its own draw,
because its job differs: it randomises the phases of a given field and keeps that field's
amplitudes exactly.

### Phase 3: kinet runs, cheapest first

Measured throughput (`00_how_to_use_kinet.md`, "Verified by running"), in cell-steps per second
on one A100: 4.6e6 entropic lattice Boltzmann with `torch.compile`, 7.6e6 plain BGK, 3.3e3 PonD.
On a shared login-node CPU: about 3e4 to 9e4 entropic and 140 PonD, so PonD cases need a GPU. A
logged isotropic run of 10 000 steps at 256² took 95.6 s on one GPU.

| Step | What | Specification | Depends on | Route and cost | Status |
|---|---|---|---|---|---|
| 15 | Time one 256² shear-layer run of 5 000 steps in one debug job, to size every later job | 00, Section 3, example (a) | approval to submit jobs | Minutes | spec written |
| 16 | Taylor–Green at Re 50 on 64², 128², 256², 512² under diffusive scaling, with a fixed-Mach companion sequence | 02, Sect. 4.1 | 1, 15 | `taylor_green_vortex` case, grid and `temporal.grid` rescaled per level. Minutes per level | spec written |
| 17 | Sod at nested resolutions (751, 1501, 3001 nodes) against the exact solution, at γ = 1.4: the γ = 2 configuration on disk has a pressure ratio of only 1.05 between neighbouring cells, so the shock detector flags nothing and its shock-metric scores are all 0 (step 4) | 02, Sect. 5.2 | 1, 4, 15 | `sod/subsonic` with the grid overridden. Minutes | spec written |
| 18 | The shipped 2D shock cases with exact answers: oblique Riemann at 30° and 45°, double Mach reflection, isentropic vortex | 03, Sects. 4.1, 4.2; 02, Sect. 4.2 | 1, 15; a GPU | PonD cases shipped in kinet. kinet's `verify` fails for the oblique Riemann case (its `verify.py` is missing), so the exact-answer comparison is done on the metrics side. Minutes to an hour | spec written |
| 19 | The shear-layer refinement sequence: 128², 256² and 512² rerun for 0.45 time units with nodes at iL/N | 02, Sect. 5.1 | 3, 15 | The shipped initialiser places nodes at i/(N−1), so the on-disk pair may not be nested; check first. Minutes | spec written |
| 20 | Degraded solver runs on the isotropic reference set: a coarse grid (64², 128²), a wrong viscosity (Re × 0.9, 0.75, 0.5), and plain BGK instead of entropic BGK, each started from the archive's own step-0 fields | 05, Options B and C | 2, 15 | Python `initial_state` route on unmodified kinet (verified). Must start from the archive's fields, because the isotropic initial condition differs between CPU and GPU and between grids for the same seed. Minutes per run; about 29 GB for the coarse grids on 30 trajectories | spec written |
| 21 | The perturbed-initial-condition ensemble on the shear layer: 17 runs from each of 3 start states, every run perturbed, each the truth in turn, stored every 10th step, macroscopic observables only | 01, Option B | 1, 15 | Python `initial_state` route (verified). Start states are frames of `kinet_re5e4`, which already stores the populations at every step, so each member continues exactly apart from its perturbation; no new run records populations. Starting from macroscopic fields alone gives a velocity jump of about 8% of the flow speed at step 1, the same in every member, so the members stay exchangeable either way. 51 runs of 5 000 steps at 256² | spec written; needs approval of the job size |
| 22 | Forced stationary 2D turbulence with drag: 1024², forcing shell at 31 ≤ \|n\| ≤ 33, 220 000 steps, after a pilot run to calibrate the drag | 04, Option B | 15; two kinet additions | `random_modes` forcing plus a drag (the `linear` law with a negative rate allowed, about ten lines) and a `minimum_mode` key (about five lines); both are refused today (verified), so both are added to kinet. Tested on the debug queue, then one regular job of about 8 hours. About 15 GB | spec written; the two additions to be built |
| 23 | ~~Decaying compressible turbulence at Mach about 0.6, for shocklets~~ | 03, Sect. 4.4 | — | — | **skipped for now** (Kareem, 2026-11-26: shocklets will not work) |
| 28 | Rerun the Mach 1.8 flow around a cylinder to completion (`flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2`, 500 × 300, 1000 steps) with macroscopic observables only, then convert it | 03, Sect. 4.7; step 4 | 1, 15; an inlet boundary type and a cylinder mask for the reader | The run on disk stopped at step 155 of 1000 (`kinet_rollout_status: interrupted`), so step 4 could not convert it. It is the only two-dimensional solver shock on disk | spec written |

### Phase 4: other solvers or public data

| Step | What | Specification | Depends on | Route and cost | Status |
|---|---|---|---|---|---|
| 24 | Johns Hopkins forced isotropic turbulence as doubly periodic 1024² z-planes | 04, Option D | a reader; the database's access terms | 12.6 MB per plane. The record spans about 5 integral times, but a 2018 notice reports corrupted boundary planes for t > 2.048 | spec written |
| 25 | An independent-solver candidate: the isotropic reference set's initial velocity run in OpenFOAM (incompressible, `cyclic` patches, `pisoFoam` or `icoFoam`) at the same viscosity | 05, Option C | 2; the OpenFOAM case setup | Shifter image on Perlmutter. A solver-to-solver discrepancy no degradation operator imitates. Not tried | spec written |
| 26 | ~~Forced compressible turbulence with shocklets~~ | 04, Option C | — | — | **skipped for now** (Kareem, 2026-11-26: shocklets will not work) |
| 27 | Regime data, in spec 11's ranking: (1) the Well reader maps wall and open boundaries to `neumann` and reads a named scalar, then The Well's `rayleigh_benard` (on disk; wall-bounded flow and scalar mixing; also makes `turbulent_radiative_layer_2D`, which stores pressure, readable); (2) analytic wall layers (start-up Poiseuille, Stokes layer) and a strained mixing layer; (3) kinet's shipped `poiseuille/channel` case (one debug job); (4) Rayleigh–Taylor as 2D slices of The Well's 3D set, then an OpenFOAM `twoLiquidMixingFoam` run that stores the volume fraction; (5) Johns Hopkins channel planes; (6) line-of-sight projections; (7) an OpenFOAM counterflow flame | 11 | approval; Kareem's three regime decisions (below) | About 240 production lines and 130 test lines in all; the first item is about 20 lines in `fmeval/data/well.py` plus a `scalar` field-vocabulary entry | first item partly done (2026-11-26): the Well reader maps each axis's `bc_type` (`PERIODIC` to `periodic`, `WALL` and `OPEN` to `neumann`, anything else or an undeclared axis refused), refuses non-uniform coordinates, and takes `coordinates_span_domain` (cell = span / N) because the published files' coordinates include both endpoints and their periodic axes repeat no column. `turbulent_radiative_layer_2D` is readable: config `well_radiative_layer_tcool0p32` (window from frame 50 proposed, not confirmed), page `docs/datasets/turbulent_radiative_layer_2d.md`, smoke run passes at `analysis_grid.resolution=64`. **`rayleigh_benard` is not built**: its rows lie on Gauss–Chebyshev nodes under a uniform `y` array (spec 11 Sect. 3.3), so it needs the `rayleigh_benard_uniform` files or an interpolating conversion; no `scalar` entry was added (buoyancy would map to `temperature`). Tests in `tests/test_loader_contract.py`, two of them data-marked. Not registered as evidence. Items (2) to (7) not started |

### Phase 5: registering the datasets as evidence, then producing it

| Step | What | Specification | Depends on | Route and cost | Status |
|---|---|---|---|---|---|
| 29 | Register every dataset built in this plan in `evidence_datasets`, with its claim label, its properties and its evaluated part ("The task"; decision 9) | `docs/recipes/add-a-dataset.md`, step 4 | the datasets' steps | Config and documentation only; no data read beyond the reader check of each dataset's properties | done (2026-11-27): 13 configurations registered in `configs/cards/default.yaml`, each with a label naming its claim and its periodic and ensemble properties: `kinet_hit_re12p5k`, `kinet_hit_re25k`, `kinet_hit_re50k`, `kinet_re5e4_512`, `kinet_sod_gamma1p4`, `kinet_sod_gamma2` (its label says the detector flags no shock, so its shock-set metrics score 0), `burgers`, `sedov_taylor`, `noh`, `feature_population`, `transport_pairs`, `random_field` (the Gaussian null; issue 044 open) and `helmholtz_mixture_2d` (its label says its vorticity is one pattern scaled in time). Out: `taylor_green_2d` (frames scalar multiples), `advecting_blobs` (a harness fixture from before this plan) and `well_radiative_layer_tcool0p32` (Kareem's call). `evidence_window` stays kinet_re5e4's one window; each other dataset's evaluated part is its own config's `time:` selection, and what no config can state (the 128 analysis grid and five realisations of the isotropic data, the 256 grid of the 512² run, `degradation.skip=[median_blur]` on the kinet Sod runs, the dilatational ladder entries of `helmholtz_mixture_2d`, the feature-population candidates) is listed in the comment beside it. `docs/decisions.md` ("Every evaluation dataset is evidence, under its label"), `docs/datasets/README.md`, `AGENTS.md` §1 and each dataset's page and log updated; `python -m fmeval.cards catalog` added a *not yet run* or *not applicable* row per dataset to every metric card |
| 30 | Produce the evidence: run every metric on every registered dataset of step 29 on its evaluated part, then `python -m fmeval.cards evidence` and `catalog` | `docs/recipes/add-a-dataset.md`, step 5; `docs/recipes/refresh-the-evidence.md` | 29; issue 044 for `random_field`; approval to use compute | From the costs measured in the logs, without the two persistence metrics, in one process on a login node: about 1.8 h for the isotropic data (270 frames at 128, about 23 s each), 3.9 h for `kinet_re5e4_512` (161 frames, about 88 s each), 25 min for `random_field`, and about 15 min for the rest together; about 6.5 h in all, split by `dataset.time.shards` and the trajectory sweep. `persistence_distance` adds about 1 h on the isotropic data, 1.5 h on the 512² run and 30 min on `random_field`; `persistence_wasserstein` is unaffordable on the large ones (framework limit 1). A card shows one primary run, and each further run in its own subsection | not started |

### Specifications still to write, in order

06 feature-population generator; 07 transport pairs; 08 synthetic-ensemble extensions; 09
random fields with known statistics; 10 acoustic and Helmholtz fields; 11 regime data, last.
Up to four agents run at once, on the opus model at high effort; spec agents do not edit
`README.md`, whose index rows are added by the coordinating session.

### Decisions

Taken by Kareem on 2026-11-26:

1. **Data and readers:** use the existing readers; convert and move data to fit them (section
   "How data reaches the metrics").
2. **Jobs:** may be submitted, to the debug queue, but not yet (section "How jobs are run").
3. **Scope:** analytic readers and solver simulations only; nothing trains or runs an ML model.

4. **kinet runs** save only the macroscopic observables (section "How kinet runs are
   configured").
5. **Agents may add to kinet** where it lacks a system the tests need (same section).
6. **Branch:** all work in the metrics repository for this project goes on `build_datasets`.
7. **Shocklets are skipped for now** (steps 23 and 26, and the supersonic part of step 27).
8. **Long simulations** may go to a longer job after a test on the debug queue (section "How
   jobs are run").

9. **Evaluation datasets:** every dataset built here is admitted as evidence with its claim
   label (section "The task").
10. **Agents:** up to four at a time, on the opus model at high effort. The order is mine.
11. **Specification 11** (regime data) is written now, but last.

Open (from spec 11, none blocking the first regime item):

1. Whether velocity gets an odd extension at no-slip walls. The framework's `neumann` rule
   works as it is, but smoothing then puts a small slip velocity on the wall. The default is
   `neumann`, because it fits the existing code.
2. Whether a mixing metric may turn density into a volume fraction. The repository's rule
   against constitutive relations in readers suggests only datasets that store a volume
   fraction should count; that is the default.
3. Whether to fix the channel count of a projected position-position-velocity cube (32
   proposed). Only needed for line-of-sight projections, the sixth regime item.

## What running kinet showed (2026-11-26)

An agent ran ten small examples (32² to 128², tens to hundreds of steps) on kinet branch
`perf/cleanup` and corrected `00_how_to_use_kinet.md` in place; its section "Verified by
running" has the commands and run folders. The findings that set the routes above:

- **Starting from a stored or perturbed frame needs no kinet change** (steps 20, 21). An exact
  restart needs populations: `kinet_re5e4` holds them at every step, the archived isotropic runs
  do not.
- **Seeds are device-dependent** for the isotropic initial condition: the same seed gives a
  different field on CPU and GPU (correlation 0.11). Same seed, same grid, same device is
  bitwise identical.
- **`N_simulations > 1` does not give an ensemble**: it fails on the isotropic case and gives
  identical members on the shear layer. Members are separate runs.
- **Weakly compressible runs store a gauge pressure**, (ρ − 1)c_s², not an absolute one;
  compressible runs store absolute p = ρT. No weakly compressible run can feed a shock metric.
- **Forcing composes only with one more override** than the guide first gave, and the linear
  law stays inactive if its target rms is below the initial rms.
- **Float32 runs still write float64**, and switching off the populations leaves 56 bytes per
  cell per frame.
- **Resume is exact**: a run interrupted and resumed is bitwise identical to an uninterrupted
  one. A finished run that is launched again is rerun and overwritten, not skipped.
- **The 1.6 TB isotropic folder the catalog cited under `datasets/kinet/` is gone**; the CFS
  archive of step 2 is its successor.

## What this order means for the shear layer and the isotropic flow

Kareem's two favoured flows carry the plan. The isotropic flow supplies the unrelated
realisations and the reference set of many initial conditions (step 2), the starting fields for
every degraded solver run (steps 20 and 25), and the base flow for forced turbulence (22). The shear layer supplies the refinement
comparison (steps 3 and 19) and the perturbed ensemble (21), where its thin filaments between
the two vortices are the small-scale tails that a metric must weigh against the vortices that
dominate it; the ensemble's spread will show whether those filaments decorrelate before the
vortex pair does, which no single run can show.
