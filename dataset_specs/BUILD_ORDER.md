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
`taylor_green_2d` does, unless its claim rests on no per-frame statistic: the kinet
Taylor–Green grid sequences of step 16 are admitted (`docs/decisions.md`).

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
  handles that. **Changed 2026-11-27 (step 19):** a coarse kinet run against a finer one needs no
  forecast file. The `kinet_raw` option `candidate` opens the coarser run beside the reference as
  its prediction, and the pipeline's conservative remap block-averages the reference onto the
  candidate's grid, the configuration's analysis grid. The forecast layout stays for predictions
  that are not kinet runs. Step 20 (2026-11-27) took the same route for the degraded isotropic
  reruns: `convert_kinet --every N` stores only every Nth frame, and under the reader option
  `cell` a coarser candidate's cell is scaled to its grid, for runs that record no lattice scales.
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
- **Every run's configuration is kept here** (decision 13, step 31). Each new run leaves, in
  the same change that adds or updates its dataset and before scratch can purge it, its
  `config.yaml`, `resolved_config.yaml` and `run_provenance.yaml` in
  `docs/datasets/logs/kinet_runs/<dataset>/<run>/`, and a record of the exact command,
  environment, kinet branch and commit (and whether the tree had uncommitted changes), device
  and torch version, Slurm job, and every step after the simulation, as that folder's README
  ("Rule for every new kinet run") says. Run records are plain text (`RUN.txt`), not Markdown.
- **New experiments.** Where a system the tests need is not in kinet, an agent may add one to
  kinet: a case, an initial condition or a forcing law (Kareem, 2026-11-26). Additions go on a
  kinet branch created for this work, never on `perf/cleanup` or `main` directly; kinet's
  plugin route (the `plugins:` list in its `configs/config.yaml`) is an alternative where it is
  simpler. Each is built once its step is approved.

## Framework limits the partition decisions ran into (2026-11-26; fixed in step 32, 2026-11-27)

Each dataset's agent worked around these in its own config comments; they were recorded here so
they could be decided centrally. Kareem approved fixing them on 2026-11-27 (decision 15), and
step 32 fixed all five, except a time limit per evaluation under the first. Every new key
belongs to `DatasetConfig` in `fmeval/config.py`, so a dataset's YAML states it and the command
line overrides it.

1. **The persistence metrics dominate every panel's time.** Measured per frame:
   `persistence_distance` 142 s at 256² on the random fields and 11.4 s at 128² on the
   isotropic data; `persistence_wasserstein` over 30 minutes for one 256² frame (stopped), and
   33 to 530 s at 128² from issue 144. Every other metric together costs tens of seconds per
   frame. It also stalls inside gudhi's `hera` routine on single inputs: on the first frame of a
   21-frame `advecting_blobs` run at 64² (0.4 s per frame on a 1 to 2 frame selection), on
   frame 90 of the radiative layer (over 60 s alone, while every other frame's whole panel takes
   24 to 29 s), and on the first frame of `sedov_taylor`'s default ladder (over 600 s, though
   0.15 s against its candidate); the cause is not diagnosed (issue 144).
   **Fixed for cost:** `slow_metrics: {<metric>: {analysis_resolution: <n>, every: <N>}}` in a
   dataset config, or `'+dataset.slow_metrics.<metric>={analysis_resolution: 64, every: 4}'` on
   the command line. A metric on a coarser grid runs in a pass of the pipeline of its own at that
   grid, with the ladder and its calibration applied there, and is written to a folder of its own
   and left out of the comparison folder, since its ladder is a different experiment; a metric on
   every Nth frame (counted over the whole selection, so frame shards thin it alike) stays in the
   pass and the comparison of its grid. Every row carries its grid in `analysis_grid`, and
   `run_meta.json` records the settings as `slow_metrics`. No dataset sets one yet: which grid or
   stride each dataset's persistence metrics get is open. A thinned metric's frame shards merge
   only among themselves (`combine_runs` refuses metrics covering different frames).
   **Not fixed: a time limit per evaluation.** gudhi's Hera does not return control to Python
   while it runs, so neither a signal nor a thread can stop it; a limit would need each
   evaluation in a child process, which costs a fork and a copy of the fields per call and does
   not fit the one-loop pipeline. A stalled input still hangs a run.
2. **Fixed: a dataset config states its analysis grid**, `analysis_resolution: <n>`
   (`configs/config.yaml` points `analysis_grid.resolution` at it). A family option and
   `analysis_grid.resolution=<n>` on the command line still replace it. The isotropic fragment
   states 128 and `kinet_re5e4_512` 256.
3. **Fixed: a dataset config excludes ladder entries**, `exclude_degradations: {<label>:
   <reason>}`. A run drops each entry present in its ladder, logs it with the reason and records
   it as `excluded_degradations` in `run_meta.json`; the report's provenance table lists it. The
   kinet Sod fragment excludes `median_blur`, whose square window wraps the 5 transverse nodes
   and would take about 11 minutes per frame.
4. **Fixed: statistics pool across trajectories.** Run each trajectory as now
   (`-m dataset.trajectory=<k1>,...`), then gather the folders with
   `fmeval.io.combine_runs(<folders>, stamp, across="trajectory")`; `analyse` (and so the report
   and the cards) reads the rows of several trajectories of one dataset as one sample
   (`fmeval.analysis.pool_trajectories`): rank correlations within each frame, never across
   frames, their median over the frames of every trajectory; the block bootstrap never joins two
   trajectories, and the Politis–White block length sums lag products within each trajectory
   only. No Hydra callback gathers a trajectory sweep at its end, as `FamilyComparison` does for a
   family.
5. **Fixed: the analysis reads a grid sequence.** `fmeval.analysis.observed_order(rows,
   anchor_label=...)` takes the rows of one candidate's runs on several grids (`load_runs`) and
   returns p = ln(L_k / L_{k+1}) / ln r (Roy 2005, Eq. 8) per metric, field and time for each pair
   of successive grids, with `order_change`, the change of p from the coarser pair, so the
   asymptotic range is read rather than assumed. `analyse` still refuses those rows together, now
   with a message naming `observed_order`, because a grid sequence is not one sample. The Burgers
   test of step 5 uses it. The forecast runs of issue 126 still lack their provenance and a
   reader pairing a coarse prediction with the fine target.

## The sequence

Status values: `spec written` (the specification exists; nothing built), `spec to write`,
`blocked` (with the reason), `in progress`, `done`.

### Phase 1: bring existing kinet data into the existing readers (no simulation)

| Step | What | Specification | Depends on | Route and cost | Status |
|---|---|---|---|---|---|
| 1 | A conversion script from kinet's grouped layout to the existing readers' layouts (`kinet_raw` for references, `forecast` for candidate pairs) | this file, "How data reaches the metrics"; 00, Section 5 | approval | Standalone tool; checked by reading a converted file with the existing reader. The weakly compressible gauge pressure is not carried over (it is not absolute, issue 101). Small | in progress: the `kinet_raw` half is built and tested (`fmeval/data/convert_kinet.py`, `python -m fmeval.data.convert_kinet SRC DST`; contract and refusal tests in `tests/test_loader_contract.py`); the `forecast` half for candidate pairs is not built |
| 2 | Convert the decaying 2D isotropic realisations at `/global/cfs/cdirs/m4790/Data/neurde/hit_scaling/` (100 complete runs at each of Re 12.5k, 25k, 50k, own seeds, 1001 frames at 256²) into `datasets/kinet/homogeneous_isotropic_turbulence/...` and add their dataset configs | 01, Option C; 05, Option B | 1 | 30 trajectories first (about 63 GB). They are the unrelated realisations for every metric's damage anchor and the reference set of many initial conditions | first 30 done: 10 complete runs per Reynolds number drawn with `numpy.random.default_rng(0)` (keys and rule in `docs/datasets/decaying_isotropic_2d.md`) and converted, 30 files of 2.10 GB (63.0 GB, 156 s on the login node), each read back by the `kinet_raw` reader and equal to its source at frames 0, 1, 500, 1000 and on its clock; `004ae2` (not drawn) stays converted. Configs: fragment `_decaying_isotropic_2d` plus `kinet_hit_re12p5k`, `kinet_hit_re25k`, `kinet_hit_re50k`, the realisation chosen by `dataset.trajectory=<key>`; `kinet_hit_re25k_004ae2` folded into them. One smoke run per Reynolds number passes. The other 270 runs are not converted; registered as evidence in step 29 |
| 3 | Add a dataset config for the 512² run of the reference shear layer beside `kinet_re5e4` | 02, Sect. 5.1 | approval | Already in the flat layout and already in place; a config only. A two-level solver comparison of the reference | done as a config: `kinet_re5e4_512` (`frame_stride: 2`, 20001 frames) passes a smoke run; registered as evidence in step 29; the node-placement check of 02, Sect. 5.1 was made in step 19 (2026-11-27): not nested, both runs used nodes at i/(N − 1) |
| 4 | Convert the kinet Sod runs and the Mach 1.8 obstacle flow already on disk | 02, Sect. 5.2; 03, Sect. 4.7 | 1; issue 046 for the non-square Sod grid | Grouped layout with absolute pressure, converted keeping `pressure`. Solver shocks in 1D and a bow shock in 2D | Sod done, obstacle blocked. `convert_kinet` now reads kinet's older grouped layout (clock `time/time`; no `pressure_convention`, so pressure is taken as absolute only where the initial p = rho T). The three Sod runs are converted to `<run>_flat.h5` beside each (481 MB, 5 to 10 s each) and read back equal to the source at all 1001 frames and on the clock (a `-m data` test pins `d17baf`). Configs: fragment `_kinet_sod` plus `kinet_sod_gamma1p4` and `kinet_sod_gamma2` (`c76b17` default, `15aa6b` by `dataset.trajectory`), read as 2D 3001 x 5, Neumann along the tube, periodic across it; every field is uniform across it, so issue 046 changes nothing here. Smoke runs with `mse` and `shock_set_distance` pass; spectral metrics are not run, coarsening is dropped (5 nodes), the median blur is skipped for cost, and the detector flags no shock in the gamma 2 run. The obstacle run is refused: it stopped at step 155 of 1000 (`interrupted`); it needs finishing, a boundary type for its inlet and a cylinder mask (`docs/datasets/supersonic_cylinder.md`). Both Sod runs registered as evidence in step 29; scoring the Sod runs against the exact solution (02, Sect. 5.2) is not built |

### Phase 2: analytic readers, computed on the fly (no data to make)

| Step | What | Specification | Depends on | Route and cost | Status |
|---|---|---|---|---|---|
| 5 | Burgers with the Cole–Hopf solution | 02, Sect. 4.5 | approval | The observed-order code path in one dimension. A day | done as a reader and tests; the analysis side is not built. One new reader `Burgers` (`burgers`, a `ClosedFormTrajectory` in `fmeval/data/analytic.py`; no existing reader is a viscous scalar equation): u_t + u u_x = ν u_xx on the periodic [0, 2π) from u = −sin x, field `velocity` (one channel, as Sod's), the Fourier–Bessel series of spec 02's Eq. in Sect. 4.5 (Cole–Hopf from Gesztesy & Holden 1998, Lemma 3.1; DLMF 10.35.2; re-derived), checked against a heat-kernel quadrature of the same transformation (4.8e-13) and by the tests. Options `nu` (default 0.1, refused below 0.05, where the series' round-off, ε e^{1/ν}, reaches 2e-8) and `scheme` (`exact`, `central`). The candidate with a known order is `candidate={scheme: central}`: second-order centred differences of u²/2 and u_xx on the reader's own cells, integrated by `solve_ivp` (DOP853, time error 7e-12 against a spatial 5e-5 on 512 cells); chosen over sampling the exact solution as cell averages, which also gives order 2 but tests no solver; spec 05's degraded-solver candidate in miniature. Asserted in `tests/test_analytic_datasets.py`: the start −sin x; the residual of the equation by centred differences falls by 4 ± 0.1 when h and dt halve (3.994 to 3.9995); the observed order p = ln(L_k/L_{k+1})/ln 2 (Roy 2005, Eq. 8) of `rmse` and `max_error` through `pipeline.run` on 64, 128, 256, 512 cells at four times, 1.93 to 2.02 on (64, 128) and within 0.006 of 2 on the finer pairs (asserted 0.1 and 0.01); six refusals. Config `burgers` (256 cells, t = 0.5 to 2 in 4 frames, kept whole: the 20 metrics that run on a 1D velocity with the default ladder 14 s wall; the grid sequence as one multirun, `'+dataset.reader.grid=[64],[128],[256],[512]'`, 6.1 s); page `docs/datasets/burgers.md` with its figure, log `docs/datasets/logs/burgers.md`. The analysis side was built in step 32: `fmeval.analysis.observed_order` computes p from the rows of the four runs (`fmeval.io.load_runs`), and the test above now reads it from there. Registered as evidence in step 29 |
| 6 | A unit test pinning `kinetic_energy`, `enstrophy` and `palinstrophy` on `taylor_green_2d`, where dE/dt = −2νΩ holds exactly | catalog G1; 02, Sect. 4.1 | approval | Reader exists. Hours | done: `test_taylor_green_fixes_the_energy_enstrophy_and_palinstrophy_budgets` in `tests/test_analytic_datasets.py` runs the three bundles through the pipeline on the reader's frames (vorticity recomputed spectrally from velocity) on the non-square grids 48×32 and 25×64 at four times, and asserts E = D²/4, Ω = D²/2, P = D² (D = e^(−2νt)) and both budgets dE/dt = −2νΩ, dΩ/dt = −2νP to 1e-12 relative; the bundles satisfy them unchanged (measured error below 1e-15, since both derivatives are spectral). `taylor_green_2d` stays out of `evidence_datasets`, its frames being scalar multiples of one another ("The task") |
| 7 | Closed-form shock fields: Sod at a shifted time, then cylindrical Sedov–Taylor and Noh. The tilted stripe and geometric ellipses are fronts of the feature-population generator (step 12), built only there | 03, Sects. 3.1 to 3.8; 06 | approval; a decision on admitting closed-form fields as evidence | Every geometric error with a known answer, and frames with no shock. Seconds per run | in progress: built; `sedov_taylor` and `noh` registered as evidence in step 29. **Sod at a shifted time**: no new reader; `SodShockTube` gained `time_offset` (every frame at t + dt) and the generic `candidate`, so the candidate is `'+dataset.reader.candidate={time_offset:dt}'` (defaults bitwise unchanged; no config added; override and known answers on `docs/datasets/sod_shock_tube.md`). **Sedov–Taylor** (`sedov_taylor`) and **Noh** (`noh`): two new `ClosedFormTrajectory` readers in `fmeval/data/analytic.py` (no existing reader is a radial Euler solution), sharing one function `polar`, each on [0, 2)² with the axis at the centre, Neumann on both axes, a positive ambient pressure 1e-6 for the detector (the closed forms have 0; no pressure from density), `time_offset` and `candidate`. Sedov is the full similarity solution, not a front with a stand-in interior: Kamm & Timmes's parametric profiles specialised to j = 2, ω = 0 (from Timmes's public `sedov_library_qp.f90`, read; the LA-UR PDF could not be rendered, so equation numbers are the code's), inverted by bisection in log s, with α = 0.9840740 integrated (Gauss–Legendre; the same integral at j = 3 gives their spherical 0.851072); their printed E = 0.311357 then puts the front at 0.749994 at t = 1, not 0.75 (α implied 0.98404, 3.3e-5 lower), recorded in the log. γ restricted to (1, 2). Noh from Sutherland (2010, Table 9, read on ar5iv; Noh 1987 not opened), generalised to any γ, ρ₀, u₀ by our derivation (D = (γ − 1)u₀/2, ρ₂ = ρ₀((γ + 1)/(γ − 1))², p₂ = ρ₂Du₀), checked by the tests; the detector's γ = 1.4 is an override. Asserted in `tests/test_analytic_datasets.py` (all through `fmeval.pipeline.run` where a metric is involved): Sod at dt = 0.001, 0.003, 0.01, `shock_set_distance` = (s − ½)dx and `shock_set_hausdorff` = s dx to 1e-12 with \|s dx − S_R dt\| ≤ dx, and `max_error` = p* − p_R and u* at every offset (the jumps unchanged); Sedov's Euler equations behind the front (residual 3e-7, tol 1e-5), mass (3e-8, tol 1e-6), strong-shock flux balance at u_s = dr₂/dt (1e-8, tol 1e-6), r₂(1) = 0.75 to 1e-5; Noh's published values exactly, jump balance at γ = 5/3 and 1.4 (1.4e-9, tol 1e-7), continuity ahead of the shock, no shock flagged at t = 0; time-offset and energy candidates on 128×96 and 96×160: ASSD and Hausdorff within one cell of Δr at four times, every flagged cell within one cell of its circle, every point between Δr − 2dx and Δr + dx; 15 refusals. Configs `sedov_taylor` and `noh` (reader defaults: 4 frames on 128², Sedov t 0.25–1, Noh t 0.5–2), pages `docs/datasets/sedov_taylor.md`, `noh.md` with dynamics figures, logs `docs/datasets/logs/{sedov_taylor,noh}.md`, Sod log appended. Evaluated part: each dataset kept whole (4 deterministic frames, known answers, not samples); measured: every deterministic non-persistence metric on the default ladder 21 s (Sedov) and 31 s (Noh) wall, `persistence_distance` 6 s per frame, `persistence_wasserstein` 5.2 s per frame on Noh but over 600 s on one Sedov frame (stopped; 0.15 s on the candidate pair), another instance of framework limit 1; candidate runs 3 to 6 s. Left out: the tilted stripe and ellipses (step 12 built them as `advecting_blobs` fronts); Sect. 3.8's displaced (not enlarged) circle with ASSD near (2/π)s, and the Schaal–Springel flagged-count check, not pinned; a Rankine–Hugoniot residual metric (issue 051) does not exist, so 'jumps unchanged' is read through `max_error`; the proposal for Sod at a shifted time is built and was deleted on 2026-11-27 |
| 8 | The stochastic advection–diffusion ensemble | 01, Option A | approval | An exchangeable ensemble along a lead-time axis with closed-form spread, error, rank histogram and CRPS | spec written |
| 9 | Analytic candidate trajectories: advection–diffusion with a wrong speed or diffusivity, upwind and Lax–Friedrichs schemes on advection, Taylor–Green with a wrong viscosity or a phase drift, and the persistence, climatology and unrelated-realisation references | 05, Option A | approval | Exact error-against-step curves for the thirteen per-step metrics. A day | in progress: built as options on the existing readers, no new reader. Every `ClosedFormTrajectory` takes a reader option `candidate`, parameters of its solution to change; `predictions()` rebuilds the reader with them on the same grid and frames, and `frame_columns` labels the rows as a forecast's (`lead_step`, `lead_time`, `param_resolution`), so the forecast analysis and figure apply unchanged. `taylor_green_2d` gained `drift` (a translation growing linearly in time) and `advecting_blobs` `diffusivity` (exact Gaussian spreading); defaults leave both bitwise unchanged. Built: Taylor–Green with a wrong viscosity (`candidate={nu:...}`), a phase drift (`{drift:[...]}`) and persistence (`{nu:0}`); advection–diffusion on `advecting_blobs` with a wrong speed (`{velocities:...}`), a wrong diffusivity (`{diffusivity:...}`), persistence (zero velocities) and an unrelated realisation (`{seed:...}`); climatology is the anchor `mean_field`, which every candidate run already keeps. `tests/test_analytic_datasets.py` asserts all thirteen per-step metrics on Taylor–Green against spec 05, Sect. 3.3 on 48×32 and 25×64 to 1e-12 (`h1_relative` 1e-8, its 1e-8 epsilon), the blob MSE of two Gaussians (wrong speed, diffusivity, both) to 1e-10, and one end-to-end `evaluate.py` run. Correction to 05, Sect. 3.3: `max_error` = cos²(π/N)\|D − D′\| only when 4 divides N; the test uses the per-axis maxima. Remaining: (1) the upwind and Lax–Friedrichs scheme candidates (Eqs. 4–6), which need the field as Fourier modes times an amplification factor per step, which neither reader has (about 20 lines on `advecting_blobs` plus a Courant number and a steps-per-frame option); (2) the random-phase multi-mode field of Sect. 3.1 and the many-seed mean and spread over initial conditions, which the harness does not aggregate over seeds (one seed per run); (3) Sect. 3.4's skill score, an analysis, not a dataset. Not registered as evidence |
| 10 | Random fields with known statistics: Gaussian fields of prescribed spectrum (power law, broken power law, Matérn), anisotropic Gaussian fields, g² − 1 (increment flatness exactly 9), log-normal and multifractal fields with exact flatness at every separation, Pareto-spiked fields, and the stationary Ornstein–Uhlenbeck time series of spec 04 A3 | 09; 04, Option A3 | approval; the shared random-field draw (below); issue 044, closed with no change by decision 14 | A `ClosedFormTrajectory` subclass in `fmeval/data/analytic.py` (an ensemble reader would score the member mean, so not an option on `synthetic_ensemble`). About 140 lines in the reader, 45 of closed-form targets in `tests/analytic_fields.py`, 90 of tests. The light-tail checkerboard fixture belongs to the future moment-estimator bundle's tests | in progress: built as one new reader, `RandomField` (`random_field`, a `ClosedFormTrajectory` in `fmeval/data/analytic.py`), not an option on `advecting_blobs` (no per-frame draw, time correlation or transforms, and a pressure field these fields must not have; `docs/datasets/logs/random_field.md`, decision 1). Reused: the draw is `_apply_filter` on `derive_rng` white noise; `AdvectingBlobs`'s inline background spectrum and its Biot–Savart inversion became the module functions `band_transfer` and `biot_savart`, which both readers call (`advecting_blobs` bitwise unchanged, its tests pass); the anisotropic stretch is a new optional argument of `wavenumber_magnitude`; candidates use step 9's `candidate`. Families built, as reader options: Gaussian with one smoothly broken power law that is also a pure power law and exactly the Matérn density (Porcu et al. 2023, Eq. 23); anisotropic; `hermite2` (g² − 1) and `exp` (log-normal) density; multifractal velocity and vorticity (Lakhal et al. 2025); Pareto spikes on density (a reader option, since X4 is not built; to be deleted when it is); per-mode Ornstein–Uhlenbeck frames (`tau`; `tau = inf` is the persistence candidate). One spectrum serves density and velocity (Eqs. 8, 9, 11 are exact for any spectrum). Dropped from spec 09: `density_mean`, `multifractal_scale` (the box), `length`. Asserted through `pipeline.run` in `tests/test_analytic_datasets.py` (9 tests, 13 cases, non-square grids except the Hill value): spectrum shapes and curl/divergence to 1e-12; S₂ along each axis, isotropic and anisotropic (a = 2), within 4 exact standard errors; flatness 3 on all fields within 0.08; W1 = |σ₁ − σ₂|√(2/π) within 6%; Hill 0.0928 on 256² within 0.004; Pareto 1/α (α = 2, 4; fraction 2/√n) within 7%; Hermite 9, log-normal Eq. 9 and multifractal Eq. 11 flatness at every separation within 8%, 12%, 8% of 48-frame means; OU lag correlation within 4 standard errors per frame; flatness 3 on every level of the default ladder's 12 linear operators. Tolerances measured over seeds and stated in each docstring. Config: one, `random_field` (Gaussian null, 12 frames on 256²; other families as override lines on its page `docs/datasets/random_field.md`); log `docs/datasets/logs/random_field.md` with the evaluated-part decision and measured costs. `evaluate.py` smoke runs pass (default ladder, 33 frames, 4 metrics, 6 min; intermittent override, quick ladder, 38 s). Remaining: (1) one config per family with its own `evidence_datasets` label, if the other families are to be cited (the Gaussian null `random_field` is registered in step 29); (2) spec 09's Eq. 6 (`energy_distance`), the `tail_exceedance` bias and the `spectrum_l2` null floor, derived but not asserted; (3) moving the spikes to X4 when built; (4) the dynamics figures |
| 11 | Synthetic-ensemble extensions: the Gneiting forecasters, flow-dependent spread, spatially correlated members, Student-t and two-piece-normal members, a wrong-centre ensemble, a positive-density variant | 08 | approval; issue 044, closed with no change by decision 14 (the reader keeps its own seed) | Options on the existing `synthetic_ensemble` reader and three operators in the existing ensemble registry; about 80 new lines. Defaults leave today's output bitwise unchanged | in progress: the reader options and operators are built and tested; nothing is registered as evidence. `synthetic_ensemble` takes `base` (`two_scale`, `case_means`, `zero`), `sigma_ratio`, `noise_length`, `noise_covariance` (`exponential`, `rational`; drawn by `_apply_filter` on seeded white noise, with a positive-definiteness check), `member_noise_length`, `member_noise_covariance`, `member_offset` and `log_amplitude`; the defaults reproduce HEAD bitwise (checked on three grids, including a two-field and a 3D one). Three bundles in the ensemble registry: `gneiting_forecaster` (probe, `ordinal=False`, stochastic, kinds `climatological`, `unfocused`, `hamill`), `flow_dependence` (`direction` `damp`/`amplify`, through `scale_spread`, which now takes a per-cell factor) and `member_shape` (`family` `student_t`/`two_piece`); `flow_dependence` and `member_shape` declare `preserves: [ensemble_mean]`. Ladders: `configs/degradation/gneiting_forecasters.yaml` (new, three probes and the anchor) and four enabled entries in `ensemble_miscalibration.yaml` (`flow_dependence_damp`, `flow_dependence_amplify`, `heavy_tails`, `skew`). Known answers asserted through the metrics in `tests/test_synthetic_ensemble.py`: the four Gneiting CRPS values (0.5642, 0.6144, 0.6319, 0.7979) within four frame standard errors (about 0.0025) on 12 frames of 64²; `spread_skill` and `ensemble_mean_rmse` unchanged to 1e-12 under both mean-preserving operators; the binned spread-error slope divided by a for damp 0.5 and 2 and amplify 1 to 1% and a uniform spread at damp 1; `variogram_score` rising under independent member noise (paired t 7.0 over 12 frames of 32²) while `crps` and `ensemble_mean_rmse` stay within |t| < 3; the Student-t CRPS closed form (Jordan et al. 2019, App. A.2.5) at nu = 5 and 2.5 within four standard errors; and reader checks of the sigma profile, the exponential covariance, the unchanged ranks under `log_amplitude` and the member offset. Both new mean-preserving operators trigger issue 111 (damage per change about 1e29 to 1e30, measured), as `spread_inflate` does; not fixed here. Remaining: (1) issue 044's `seed: ${seed}` is not added, by decision 14; (2) the five dataset configs of spec 08, Sect. 6.1, and their `evidence_datasets` entries; (3) the exemplar panels of the three bundles (not generated; no test requires them); (4) Eq. 6 (deflation under bias) and Eq. 7 (log-normal CRPS) are not asserted by a test; (5) the binned spread-error figure is a separate change to `spread_skill` |
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
| 15 | Time one 256² shear-layer run of 5 000 steps in one debug job, to size every later job | 00, Section 3, example (a) | approval to submit jobs | Minutes | done (2026-11-27, job 62100814, one A100, kinet `perf/cleanup` at `d1cd353b8`, a cold `torch.compile` cache): 265 s wall for the run, of which 157 s start-up before the first step, 74 s for the first step (compilation), then 3.92 ms per step (1.67e7 cell-steps per second, 3.6 times the 4.6e6 measured before on a small grid) and 104 s of rollout; record in `docs/datasets/logs/kinet_runs/kinet_re5e4_timing/`. The rollout (1.8 GB, `shear_layer_re5e4/` on scratch) is a timing run, not a dataset. **Two sizing facts for every later job**, from this and the eight runs of step 16: each run costs a start-up of 1 to 5 minutes (64 to 325 s measured) plus about a minute of compilation (21 to 86 s for the first step) before it steps, so several short runs per job pay that each time; and kinet's walltime guard (`io.async_drain.walltime_preempt`, margin 240 s) stops a run early, with exit code 0, when the time left in the job is less than one step plus 240 s, and its first estimate of a step counts the compilation, so a job must leave that margin or the run ends unfinished while reporting success (two runs of step 16 stopped this way, the fixed-Mach 512² run in job 62100815 and the diffusive 256² run in job 62101127, `stop_reason=shutdown` with exit code 0, and were rerun; their folders are `_work/preempted_*` on scratch) |
| 16 | Taylor–Green at Re 50 on 64², 128², 256², 512² under diffusive scaling, with a fixed-Mach companion sequence | 02, Sect. 4.1 | 1, 15 | `taylor_green_vortex` case, grid and `temporal.grid` rescaled per level. Minutes per level | done (2026-11-27). Eight runs (jobs 62100815, 62101127, 62101400, 62101401 and 62101725 on the debug queue; records in `docs/datasets/logs/kinet_runs/taylor_green_re50/`), each to 1.0029 t_d: diffusive scaling Ma = 0.08·64/N with 880 to 56 320 steps and 40 saved times, fixed Ma = 0.1 with 704 to 5 632 steps and 32 saved times; 133 to 552 s wall per run, 2.5 to 4.3 ms per step. Converted unchanged by `convert_kinet` to `kinet/taylor_green_vortex/weakly_compressible_isoT_fluids/sys_Re-50_diffusive/` and `sys_Re-50_Ma-1en1/` (`N64.h5` to `N512.h5`, 787 MB). Read by a new registered reader `taylor_green_kinet` (`fmeval/data/analytic.py`, about 30 lines: the exact solution of `TaylorGreen2D` on the run's cells and clock, the run as its candidate) and a `box` option of `KinetRawTrajectory` that reads a run with the box 2π and u_l = 1. kinet places node i at (i + ½)·2π/N, the cell centres the reader samples (initial error below 1e-14). Measured: the time-averaged velocity L2 error falls at order 2.00, 1.98, 2.09 under diffusive scaling and stays at a floor at fixed Mach (−0.09, −0.06, 0.01); through `observed_order` at the four evaluated times, vorticity 1.99 to 2.01, velocity 1.60 to 2.64 (an oscillating dilatational part of its error), and at fixed Mach −0.14 to 0.01 on the two finer pairs. Configs `kinet_taylor_green_diffusive` and `kinet_taylor_green_fixed_mach` (fragment `_kinet_taylor_green`), page and log `taylor_green_vortex`, registered as evidence of a grid sequence; tests in `tests/test_analytic_datasets.py` |
| 17 | Sod at nested resolutions (751, 1501, 3001 nodes) against the exact solution, at γ = 1.4: the γ = 2 configuration on disk has a pressure ratio of only 1.05 between neighbouring cells, so the shock detector flags nothing and its shock-metric scores are all 0 (step 4) | 02, Sect. 5.2 | 1, 4, 15 | `sod/subsonic` with the grid overridden. Minutes | done (2026-11-27). Three runs of `sod/transonic` (γ = 1.4) on 751, 1501, 3001 × 5 nodes, 250/500/1000 steps saved every 1/2/4 steps, viscosity rescaled per level (job 62102238; records in `docs/datasets/logs/kinet_runs/kinet_sod_refinement/`), converted unchanged by `convert_kinet` to `kinet/sod/compressible_fluids/Pr-71en2_vuy-1.4_refinement/N751.h5`, `N1501.h5`, `N3001.h5` (211 MB). A registered reader `sod_kinet` (`SodKinet` in `fmeval/data/analytic.py`, about 50 lines, the Taylor–Green pattern: the exact solution on the run's cells and clock, the run from `predictions()`) reads the states and γ from the run and checks its diaphragm, the face (N − 1)/2, in the stored initial density; a new `kinet_raw` option `cell` (about 8 lines) reads each run in units where N − 1 cells and steps are one, so the diaphragm is at 0.5, the grids nest and frame k is t = k/750 on every grid, which `observed_order` needs to pair them. The job's L1 and L2 errors reproduced to 2e-13; through `observed_order` at the four kept times (steps 700 to 1000 of the finest run) `mae` density 0.66 to 0.68 and `rmse` density 0.32 to 0.40 (pressure 0.78 to 0.83 and 0.56 to 0.71). Config `kinet_sod_refinement` (grid by `dataset.trajectory`), beside `kinet_sod_gamma1p4`, not replacing it (that is the ladder's reference, and a different run); full panel about 5 s wall per grid; registered as a grid sequence; log `docs/datasets/logs/sod_shock_tube.md` |
| 18 | The shipped 2D shock cases with exact answers: oblique Riemann at 30° and 45°, double Mach reflection, isentropic vortex | 03, Sects. 4.1, 4.2; 02, Sect. 4.2 | 1, 15; a GPU | PonD cases shipped in kinet. kinet's `verify` fails for the oblique Riemann case (its `verify.py` is missing), so the exact-answer comparison is done on the metrics side. Minutes to an hour | spec written |
| 19 | The shear-layer refinement sequence: 128², 256² and 512² rerun for 0.45 time units with nodes at iL/N | 02, Sect. 5.1 | 3, 15 | The shipped initialiser places nodes at i/(N−1), so the on-disk pair may not be nested; check first. Minutes | done (2026-11-27). Checked: the on-disk `kinet_re5e4` and `kinet_re5e4_512` were initialised with nodes at i/(N − 1) (match 1e-14; cell centres miss by 8% and 4% of the stream speed), so they are not nested (block-averaged initial velocities differ by 7.3e-3 of the rms velocity); `kinet_re5e4_512`'s label now says so. Three reruns on 128², 256², 512² to t = 0.451 (job 62102236, cell centres (i + ½)/N, 101 frames each, bitwise equal clocks), converted to `kinet/doubly_periodic/weakly_compressible_isoT_fluids/sys_Re-5e4_Ma-1en1_refinement/N128.h5`, `N256.h5`, `N512.h5` (1.1 GB). A new `kinet_raw` option `candidate` (about 20 lines with `predictions()` and `frame_columns()`) scores the coarser run against the 512² run, which the pipeline's conservative remap block-averages onto the candidate's grid (no forecast files written; `box: 1` puts both on one grid). Config `kinet_shear_layer_refinement` (`dataset.trajectory=256` or `128` sets the candidate and the analysis grid); the job's differences reproduced to 2e-14; not an observed order (three-grid order 2.0 at t = 0 rising to 3.7), and the label says so; 10 frames, 12 s (128) and 31 s (256) wall for the panel without the persistence metrics; registered; log `docs/datasets/logs/reynolds_ladder_2d.md` |
| 20 | Degraded solver runs on the isotropic reference set: a coarse grid (64², 128²), a wrong viscosity (Re × 0.9, 0.75, 0.5), and plain BGK instead of entropic BGK, each started from the archive's own step-0 fields | 05, Options B and C | 2, 15 | Python `initial_state` route on unmodified kinet (verified). Must start from the archive's fields, because the isotropic initial condition differs between CPU and GPU and between grids for the same seed. Minutes per run; about 29 GB for the coarse grids on 30 trajectories | done (2026-11-27). 105 runs (jobs 62104552 to 62104556 and 62105660 on the debug queue, kinet `perf/cleanup` at `d1cd353b8`, one A100): the five evaluated realisations of each Reynolds number times `control`, `grid128`, `grid64`, `re0.9`, `re0.75`, `re0.5`, `bgk`, each from its realisation's stored step-0 fields (block-averaged for a coarser grid) with equilibrium populations; all reached their last step; raw 275.7 GB on scratch. Checked by the job (`candidates_checks.txt`): at Re 1.25e4 and 2.5e4 the control matches its realisation to round-off (velocity relative L2 1.3e-11 to 1.8e-11 at frame 150) and three orderings hold for 5 of 5 realisations at every evaluated frame (control below every rerun, 64² above 128², error growing with the viscosity error); BGK was stable in all 15 runs. At Re 5e4 the realisations are 512² runs stored at 256², so the 256² control is a grid candidate (0.011 at frame 150, 0.155 at 550) and the viscosity reruns are hidden under that grid error; those three kinds are not converted, and the four kept order fully. Brought to the metrics with the existing `kinet_raw` option `candidate` (no new reader, no forecast files): `convert_kinet` gained `--every` (keep every Nth frame; 6 lines), and a candidate under `cell` gets its cell scaled to its grid so a coarser run spans the same domain and clock (4 lines); 90 reruns and a copy of each realisation at the same stride (frames 0, 50, ..., 1000) converted to `kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids/sys_Re-<Re>_Ma-1en1_candidates/<key>/{reference,<kind>}.h5` (105 files, 3.51 GB, each checked against its source). Configs: fragment `_isotropic_candidates` plus `kinet_hit_re12p5k_candidates`, `kinet_hit_re25k_candidates`, `kinet_hit_re50k_candidates`, the kind chosen by `dataset.reader.candidate=<kind>.h5` and the realisation by `dataset.trajectory`; evaluated part the realisations' frames 150 to 550 every 50th on the 128 grid (64 for `grid64`); a candidate replaces the ladder, so the 24-metric panel costs 0.68 s per frame and `persistence_wasserstein` 0.52 s (measured), about 25 min for all 90 runs (my arithmetic). Registered as evidence; data-marked test reproduces the job's distances to 3.3e-5. No analysis reads the expected ordering across kinds (issue 147). Records in `docs/datasets/logs/kinet_runs/isotropic_candidates/`; log `docs/datasets/logs/decaying_isotropic_2d.md`, section 7 |
| 21 | The perturbed-initial-condition ensemble on the shear layer: 17 runs from each of 3 start states, every run perturbed, each the truth in turn, stored every 10th step, macroscopic observables only | 01, Option B | 1, 15 | Python `initial_state` route (verified). Start states are frames of `kinet_re5e4`, which already stores the populations at every step, so each member continues exactly apart from its perturbation; no new run records populations. Starting from macroscopic fields alone gives a velocity jump of about 8% of the flow speed at step 1, the same in every member, so the members stay exchangeable either way. 51 runs of 5 000 steps at 256² | done (2026-11-27). **Corrected: "each the truth in turn" tests nothing.** Pooled over the 17 choices of truth, the ratio of the ensemble mean's squared error to the members' variance is 17/16 identically, for any data (x_j − mean_{−j} = (M/(M − 1))(x_j − mean), M = 17; derivation in spec 01, Section 3, correction), and the pooled rank histogram is exactly flat; single truths scatter (velocity 1.02 to 1.12 at short leads, 0.46 to 1.93 at lead 5 000). The runs (jobs 62103496, 62103586 to 62103588, all members perturbed at 10⁻³ u_rms on 1 ≤ \|k\| ≤ 16, saved every 10th step; records and findings in `docs/datasets/logs/kinet_runs/shear_layer_ensemble/`) are converted unchanged by `convert_kinet` to `kinet/doubly_periodic/weakly_compressible_isoT_fluids/sys_Re-5e4_Ma-1en1_ensemble/start_<step>/member_<i>_amp1e-03.h5` (51 files, 53.6 GB, 501 frames each, 113 s; the 10⁻² amplitude run is not converted). A new `kinet_raw` option `members` (a glob of run files beside the truth; about 25 lines with `close` and `frame_columns`) makes the reader an ensemble with one fixed truth, `member_00`, and the other 16 as `Frame.members`; rows carry `lead_time`, not `lead_step`. `RecomputingTrajectory` dropped the members of any frame with a derived field; fixed (`fmeval/derived.py`, each member recomputed from its own velocity). Config `kinet_shear_layer_ensemble` (start by `dataset.trajectory`, three starts pooled as trajectories), leads 500 to 5 000 every 500 steps (30 frames), `variogram_score` on 64² every 5th frame; registered as a physical ensemble of three cases; log `docs/datasets/logs/reynolds_ladder_2d.md` |
| 22 | Forced stationary 2D turbulence with drag: 1024², forcing shell at 31 ≤ \|n\| ≤ 33, 220 000 steps, after a pilot run to calibrate the drag | 04, Option B | 15; two kinet additions | `random_modes` forcing plus a drag (the `linear` law with a negative rate allowed, about ten lines) and a `minimum_mode` key (about five lines); both are refused today (verified), so both are added to kinet. Tested on the debug queue, then one regular job of about 8 hours. About 15 GB | spec written; the two additions to be built |
| 23 | ~~Decaying compressible turbulence at Mach about 0.6, for shocklets~~ | 03, Sect. 4.4 | — | — | **skipped for now** (Kareem, 2026-11-26: shocklets will not work) |
| 28 | Rerun the Mach 1.8 flow around a cylinder to completion (`flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2`, 500 × 300, 1000 steps) with macroscopic observables only, then convert it | 03, Sect. 4.7; step 4 | 1, 15; an inlet boundary type and a cylinder mask for the reader | The run on disk stopped at step 155 of 1000 (`kinet_rollout_status: interrupted`), so step 4 could not convert it. It is the only two-dimensional solver shock on disk | done (2026-11-27). Rerun to 2000 steps (job 62103249; stand-off steady at 37 cells from step 1200) and converted to `kinet/flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2/D2Q9_shape-500-300_T-2000_H-33f78849.h5` (965 MB, 201 frames). The inlet needs no new boundary type (the first 60 columns are uniform to 2e-13). The body is left out by the coordinator's option 1, a spatial window: a new `kinet_raw` option `window` (cells `[start, stop)` per axis; the grid's shape and origin are the window's; about 10 lines) reads x 0 to 143, y 6 to 293, upstream of the body, where the shock detector flags only the bow shock (45 to 56 cells at x 107 to 111, at least 38 nodes from the body; on the whole domain 178 of about 230 flagged nodes lie on the body outline). Every face `neumann`, three of them cuts (the config says what the mirror does there). Config `kinet_supersonic_cylinder`, frames 120, 160, 200 (one settled state with a slow drift); the wake is excluded; registered; log `docs/datasets/logs/supersonic_cylinder.md` |
| 31 | Keep every kinet run's configuration in this repository: the solver config, the kinet commit where recorded, and the command that reproduces it, for the runs on disk and for every new run | decision 13 | — | A tracked folder beside the dataset logs; no simulation | done (2026-11-27): `docs/datasets/logs/kinet_runs/`, one subfolder per dataset, byte-identical copies of every configuration and provenance file found for the runs a dataset reads (137 files, plus 8 launch scripts and case files of the isotropic runs), and a README section per dataset with the command that reproduces each run on the current kinet. It established: no old configuration loads on the current kinet (renamed case keys), so every old run is rebuilt from a case and overrides, and each such command composes in kinet's check app but none was executed; the kinet commit, device and job are unknown for the shear-layer, Sod and cylinder runs; the isotropic runs depended on case files of a branch that were uncommitted at the time, and on the current kinet they give a statistically equivalent run only (00, Section 6c). The rule for new runs is under "How kinet runs are configured". The runs of steps 15 and 16 are archived in `kinet_re5e4_timing/` and `taylor_green_re50/`, each with a `RUN.txt` (command, commit, device, job, wall time) |
| 32 | Fix the five framework limits: per-metric analysis grid or frame selection for slow metrics; a dataset-level analysis grid; a dataset-level degradation exclusion; pooling per-frame results across trajectories; reading a grid sequence and computing the observed order (issue 126). Close issue 044 with no change, and apply decision 17's cuts | "Framework limits the partition decisions ran into"; decisions 14, 15, 17 | — | Harness changes in `fmeval/`; each with tests; existing results must not move | done (2026-11-27), as "Framework limits" above now describes: `DatasetConfig` gained `analysis_resolution` (`analysis_grid.resolution` interpolates it in `configs/config.yaml`, whose `_self_` moved before the family option so a family's grid still wins), `exclude_degradations` (dropped, logged, recorded in `run_meta.json` and the report's provenance table) and `slow_metrics` (a coarser grid as a pipeline pass of its own, written to its own folder and left out of the comparison; every Nth frame through `pipeline.run(every=...)`, kept in the comparison); `fmeval.analysis.pool_trajectories` with `combine_runs(..., across="trajectory")`, and a `segments` argument on `stats.block_bootstrap` and `stats.politis_white_block_length` so no resampling block joins two trajectories; `fmeval.analysis.observed_order`, which the Burgers test now uses (1.93 to 2.02, 1.997 to 2.005 and 1.995 to 2.001 on the three pairs, as before). No time limit per evaluation (limit 1 says why). Issue 044 deleted with no code change (decision 14) and every reference rewritten; issue 126 narrowed to the forecast runs' provenance; issue 144 says how to state its options 1 and 4. Decision 17 applied: `kinet_re5e4_512` every 400th frame (21) on its own 256 grid, the isotropic data stride 50 (9 frames per run) on its own 128 grid, the kinet Sod runs excluding `median_blur`; `evidence_window`'s comment, the three logs and the pages updated. `advecting_blobs` registered as an analytic check (decision 16) and `python -m fmeval.cards catalog` rerun. Tests in `tests/test_configs.py`, `test_pipeline.py`, `test_analysis.py`, `test_stats.py`, `test_cards.py`, `test_analytic_datasets.py`. Smoke runs under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/step32_smoke`: a kinet Sod run (median blur excluded and recorded), three isotropic trajectories pooled into one folder of 9 frames and reported, the 512² run on 256, the Burgers grid sequence read by `observed_order` from its four folders, and `persistence_distance` on 64 every 2nd frame beside `mse` on 128. Refactor gate (`docs/recipes/verify-a-refactor.md`, baseline from a worktree at `2e98831`): run 1 (3822 rows), run 3 (1440 rows) and run 2 without `persistence_wasserstein` (16653 rows, every other registered metric) agree bitwise in every result, map, calibration, configuration leaf and provenance leaf, once the new keys (`dataset.analysis_resolution`, `exclude_degradations`, `slow_metrics`) are ignored; the only other difference is the copied `TEST_DESCRIPTION.md`, edited on purpose; the registry listings are identical. The recipe's full run 2 did not finish its baseline in 43 minutes (`persistence_wasserstein` on `kinet_re5e4_dev`, limit 1) and was stopped. Default `pytest` exit 0 (3056 passed, 406 skipped, 4 xfailed) |

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
| 30 | Produce the evidence: run every metric on every registered dataset of step 29 on its evaluated part, then `python -m fmeval.cards evidence` and `catalog` | `docs/recipes/add-a-dataset.md`, step 5; `docs/recipes/refresh-the-evidence.md` | 29; approval to use compute | From the costs measured in the logs, without the two persistence metrics, in one process on a login node, after decision 17's cuts: about 52 min for the isotropic data (135 frames at 128, about 23 s each), 31 min for `kinet_re5e4_512` (21 frames, about 88 s each), 25 min for `random_field`, and about 15 min for the rest together; about 2 h in all (my arithmetic, from 3.9 h and 1.8 h before the cuts); the degraded isotropic reruns of step 20, registered after this estimate, add about 25 min with both persistence metrics (90 runs of 9 frames, a candidate in place of the ladder; my arithmetic from the measured 0.68 s and 0.52 s per frame), split by `dataset.time.shards` and the trajectory sweep. `persistence_distance` adds about 30 min on the isotropic data, 12 min on the 512² run and 30 min on `random_field`; `persistence_wasserstein` needs a coarser grid or fewer frames on the large ones, now stated per dataset with `slow_metrics` (framework limit 1), which no dataset has chosen yet. A card shows one primary run, and each further run in its own subsection | not started |

### Specifications still to write, in order

06 feature-population generator; 07 transport pairs; 08 synthetic-ensemble extensions; 09
random fields with known statistics; 10 acoustic and Helmholtz fields; 11 regime data, last.
Up to four agents run at once, on the opus model at high effort; spec agents do not edit
`README.md`, whose index rows are added by the coordinating session.

### Decisions

Taken by Kareem on 2026-11-26:

1. **Data and readers:** use the existing readers; convert and move data to fit them (section
   "How data reaches the metrics").
2. **Jobs:** may be submitted, to the debug queue (section "How jobs are run"); started on 2026-11-27, decision 12.
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

Taken by Kareem on 2026-11-27:

12. **Jobs may start**, on the debug queue first; step 15 is the first.
13. **Every kinet run's configuration is kept in this repository**, for the runs already made
    and for every new one, so each can be reproduced from scratch (step 31).
14. **A reader does not need to know the run's seed** ("The reader does not need to know the
    seed used to generate the data"). So issue 044 is closed with no change: a generated
    dataset keeps its own `seed` reader option, and nothing waits on it.
15. **The five framework limits may be fixed** (step 32).
16. **The smaller calls are the agent's to make.** Made on 2026-11-27, each reversible:
    - The synthetic ensemble keeps its default of 16 members, 12 frames and 64². A 32² default
      would save about 7 minutes per panel and change every number on four cards; the cost is
      `variogram_score` alone, which the per-metric grid of step 32 addresses at its source.
    - `well_radiative_layer_tcool0p32` stays unregistered and no further work is done on The
      Well: no test of an existing metric needs it.
    - The Well reader change stays: about 18 lines, tested, and it leaves the existing
      `well_re5e4` dataset's output unchanged.
    - `advecting_blobs` is registered as an analytic check. It is the same reader as the
      registered `feature_population` and `transport_pairs`, its blobs move at different
      velocities so its frames are not scalar multiples, and the candidates built on it in
      step 9 are evaluation experiments.
17. **The evaluated parts of the two costliest datasets are cut**, after Kareem asked why the
    evidence needs so long. `kinet_re5e4_512` goes from 161 frames to 21 (every 400th): its 161
    frames hold only 7 to 12 independent samples, and it had matched `kinet_re5e4` frame for
    frame for no statistical reason. The isotropic data goes from stride 25 to 50 (9 frames per
    run): pooling across the 5 runs per Reynolds number (step 32) supplies the samples.

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
