# Log: supersonic flow past a cylinder

This log covers [the supersonic cylinder page](../supersonic_cylinder.md). One configuration,
`kinet_supersonic_cylinder`, reads this flow (its section is the last).

## The kinet run `a92b16`

### What it is for

It is the planned test of a shock detector on a real curved front. The bow shock is normal
to the stream at the nose (Mach 1.8, a pressure ratio of 3.61) and weakens along its arc, so
the length of front that a detector flags depends on its threshold
(`dataset_specs/03_two_dimensional_shocks.md`, Sect. 4.7). Build-order step 4 asked for it to
be converted. Completing it is now build-order step 28.

### How it is treated

- **Source.** `/global/cfs/cdirs/m4790/Data/kinet/flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2/D2Q9_shape-500-300_T-1000_H-a92b16.h5`
  (12 GB), with its run configuration in `configs/a92b16.yaml` and two simulation checkpoints,
  at steps 133 and 156, beside it.
- **Solver.** kinet, compressible D2Q9 with entropic BGK collision; $\gamma = 1.4$, Prandtl
  number 0.71, Reynolds number 300, on 500 × 300 nodes. It starts from a uniform stream with
  $\rho = 1$, $T = 0.2$ and Mach 1.8.
- **Obstacle.** A cylinder of radius 20 nodes, centred at (166, 150).
- **Boundaries.** The run configuration has an inlet on the low-x face and Neumann on the
  other three faces.
- **Layout.** It is kinet's older grouped layout, as the Sod runs are: no `pressure_convention`
  and no `time_convection`; its clock is `time/time`, 1/300 per step. Pressure equals
  $\rho T$ exactly.
- **Not converted.** No configuration reads it.

### What part will be evaluated (planned for the rerun, build-order step 28)

This is a plan written before the rerun exists. The agent made it on 2026-11-26, and the
measurements after the rerun confirm or replace it.

- **What to save.** Save only the macroscopic observables: `io.record_distributions=false
  io.record_equilibria=false` (`BUILD_ORDER.md`, "How kinet runs are configured"). The stored
  file then holds density, velocity, pressure, temperature, energy and Mach number, plus the
  two stability fields kinet always writes. That is about 9 channels, or 72 bytes per node per
  saved frame: 10.8 MB per frame on 500 × 300 nodes. The converter keeps density, velocity and
  pressure, which is 4.8 MB per frame (the agent's arithmetic).
- **How often.** Save every 10th step (`io.save_every_n=10`) for the 1000 steps of step 28:
  101 frames, about 1.1 GB stored and 0.5 GB converted. The inflow moves at
  $1.8 \sqrt{1.4 \times 0.2} = 0.95$ nodes per step, so the stream crosses the cylinder's
  diameter of 40 nodes in about 42 steps. Saving every 10th step resolves that time, and
  saving every step, as the interrupted run did, multiplies the disk by ten without adding
  independent frames.
- **Which part is evaluated.** Steps 550 to 1000. The run starts from a uniform stream with
  the cylinder already in place, so a starting disturbance must leave the domain before the
  bow shock and the wake represent the flow. One pass of the stream through the 500 nodes
  takes about 525 steps, so the first 550 steps are treated as transient. This estimate is
  reasoning, not a measurement: after the rerun, measure the bow shock's stand-off distance on
  the centre line against time, and start the window where it has settled to within one node.
- **Stride.** Every 50th step to start with, which gives 10 frames. The bow shock should be
  nearly steady, so its frames will be close to duplicates, and the independent information
  comes from the unsteady wake at Reynolds number 300. The stride should then be set from the
  measured Politis–White block length of a dense run, as was done for the Sod runs
  (`logs/sod_shock_tube.md`, "What part is evaluated").
- **Length.** If the settled window turns out shorter than one wake period, or holds fewer than
  about five independent frames, run to 2000 steps rather than 1000. At 1.5e5 nodes that is
  still minutes of GPU time (not measured for this solver).

### Decisions and why

1. **The run is not converted.**
   - Made by: the agent, 2026-11-26, applying the converter's existing rule that only a
     complete rollout is converted. The coordinator's brief for step 4 also said to refuse
     what cannot be converted exactly.
   - Reason: the root attribute `kinet_rollout_status` is `interrupted`. The file holds steps
     1 to 155, and the other 845 time slots are NaN. Its metadata also disagree with each
     other: `kinet_completed_sim_steps_global` is 156 and `kinet_last_completed_step` is 23.
   - Alternative: convert the 155 stored steps. That would be exact for those frames, but it
     needs a converter option to accept an unfinished run, and it would only give the shock
     while it is still forming.
   - To reverse: add such an option to `fmeval/data/convert_kinet.py` and convert the stored
     steps.
2. **What completing it needs (build-order step 28).**
   - **A finished run.** Rerun it to step 1000, saving only the macroscopic observables
     (`BUILD_ORDER.md`, "How kinet runs are configured"), or resume it from its step-156
     checkpoint. Then convert it as the Sod runs were.
   - **An inlet boundary type.** `BOUNDARIES` in `fmeval/data/base.py` has only `periodic`
     and `neumann`. An inlet is not a zero-gradient face, so the low-x face needs a new type
     whose extension is continuous across its seam. The other three faces can be declared
     `neumann`.
   - **A cylinder mask.** The file stores no mask. Inside the cylinder the solver holds the
     fluid at rest with $\rho = 1$, so a metric would score those nodes as flow. The mask has
     to be built from the centre and radius in `configs/a92b16.yaml`, or recorded in a rerun.
   - Made by: the agent, 2026-11-26; Kareem's build order lists the same three needs at
     step 28.

### Log entries

**2026-11-26, agent (build-order step 4).**

- Inspected the file's HDF5 tree and attributes, and its run configuration.
- Ran `python -m fmeval.data.convert_kinet` on it. It was refused with "kinet_rollout_status
  is 'interrupted', not 'complete'", and nothing was written.
- Measured inside the cylinder at step 155: $\rho = 1$ and speed below $10^{-16}$.
- Wrote `docs/datasets/supersonic_cylinder.md` and its row in `docs/datasets/README.md`.
- Not verified: whether resuming from the step-156 checkpoint works with the current kinet.

**2026-11-26, agent (planned evaluation for build-order step 28).**

- Added the section "What part will be evaluated". It plans macroscopic observables only,
  saved every 10th step for 1000 steps, with steps 550 to 1000 evaluated every 50th step.
- The transient length and the stride are estimates from the flow speed. They are to be
  measured on the rerun, as described in that section.
- Nothing was run.

**2026-11-27, dataset agent (where the run's configuration is kept).**

- The configuration of the run `a92b16`, with the command that rebuilds it on the current kinet
  and why that is not an exact reproduction, is in
  `docs/datasets/logs/kinet_runs/supersonic_cylinder/` (README section "Supersonic cylinder"),
  step 31 of `dataset_specs/BUILD_ORDER.md`. The rerun of step 28 is archived in
  `supersonic_cylinder_rerun/` there; it is not converted or read yet.

**2026-11-27, dataset agent (batch 2, build-order step 28): the rerun converted, not configured.**

- **Converted.** The 2000-step rerun `cyl_m1p8_re300_T2000` (kinet `perf/cleanup` at `d1cd353b8`,
  job 62103249; record in `docs/datasets/logs/kinet_runs/supersonic_cylinder_rerun/`) by
  `python -m fmeval.data.convert_kinet /pscratch/sd/k/khegazy/kinet_datasets/supersonic_cylinder/flow_around_objects/cylinder/33f78849/tiers/full/rollout.h5 /global/cfs/cdirs/m4790/Data/kinet/flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2/D2Q9_shape-500-300_T-2000_H-33f78849.h5`
  (965 MB, 2.1 s): 201 frames (step 1 dropped, then every 10th step), density, velocity and the
  absolute pressure (`pressure_convention: absolute`); the run stores no vorticity. Every frame
  and the clock (`time_convection`, 0.0019 per step) read back equal to the source. The old
  `a92b16` file is untouched.
- **The inlet.** Measured in frames 120 and 200: every field uniform over the first 60 columns
  to $1.7 \times 10^{-13}$ (density), and over 90 columns to $1.7 \times 10^{-9}$. A `neumann`
  declaration extends the field by a mirror image, which here is the stream itself, so no inlet
  type is needed in `BOUNDARIES`. This supersedes the "inlet boundary type" need of decision 2.
- **The cylinder.** Inside it the run holds $\rho = 1$, $p = 0.2$, $|u| < 10^{-16}$ (the solid mask
  `geometry/masks/solid` of the rollout, 1257 nodes, x 146 to 186, y 130 to 170; the converter
  does not carry it). On the whole domain, `shock_mask` (the detector of `shock_set_distance`,
  default threshold) flags 229, 234 and 227 nodes in frames 120, 160, 200; 178 of them within two
  nodes of the body (90 inside), about 50 on the bow shock (x 107 to 145, y 125 to 175), one
  behind the body, none on the outer faces.
- **Stopped, as the brief says to when neither an existing selector nor an existing mask
  leaves the body out with little code.** The harness has no spatial selector or mask
  (`DatasetConfig` in `fmeval/config.py`; searched `fmeval/` for a crop, window or mask). The
  options and what each costs are on the page ("What stands in the way"): a spatial window on
  `kinet_raw` (about 10 lines; upstream of x = 146 it holds the detected shock and none of the
  body), the whole domain (no code; the body dominates the shock-set metrics), or a pipeline
  mask (largest). The choice is left to the coordinator.
- **Evaluated part, if the window is built** (proposal, not decided): frames 120 to 200, the
  settled flow; the stand-off is constant at 37 cells there (the job's
  `_scripts_batch2/cylinder_settling_T2000.txt`), so a few frames, every 40th, would suffice.

### Open points

- No configuration: the choice among the three options of the 2026-11-27 entry (a spatial
  window, the whole domain, a pipeline mask) is open.
- The rerun's start-up transient and wake period were measured only through the stand-off and one
  wake probe (`_scripts_batch2/cylinder_settling_T2000.txt`); the wake's period is not measured.
- Spectral metrics on its non-square, non-periodic grid are not run (they need a periodic
  domain); issue 046 concerns the wavenumber magnitude on non-square grids.

## `kinet_supersonic_cylinder` (the bow shock in a window upstream of the body, 2026-11-27)

### What it is for

The repository's only two-dimensional solver shock: the bow shock of a steady Mach 1.8 flow, a
real curved front for the shock detector and the shock-set metrics
(`dataset_specs/03_two_dimensional_shocks.md`, Sect. 4.7; build-order step 28). It supersedes the
open point of the batch-2 entry above: the coordinator chose option 1 of the three, a spatial
window.

### How it is treated

- **Source.** The converted rerun
  `/global/cfs/cdirs/m4790/Data/kinet/flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2/D2Q9_shape-500-300_T-2000_H-33f78849.h5`
  (batch-2 entry above; run record in `docs/datasets/logs/kinet_runs/supersonic_cylinder_rerun/`).
- **Reader.** `kinet_raw` with `include_redundant: true` (the pressure is the absolute $p = \rho T$),
  and a new option `window: [[0, 144], [6, 294]]`: cells `[start, stop)` per axis, read as the
  spatial part of every field read (the time position stays an integer); the grid's shape is
  the window's, $144 \times 288$, and its origin the window's first cell, $(0, 6)$, so a position
  keeps the run's coordinate; `run_meta.json` records the window among the reader options.
- **Fields.** Density, velocity, pressure. The run stores no vorticity.
- **Boundaries.** `neumann` on every face; the low-x face is the inlet, the other three are cuts
  (decision 2).

### What part is evaluated

- **Kept:** frames 120, 160 and 200 (steps 1200, 1600, 2000), on the native $144 \times 288$ grid.
- **Why.** The stand-off on the centre line is 37 cells from step 1200 on (the job's
  `_scripts_batch2/cylinder_settling_T2000.txt`), so frames before 120 are the start-up. The
  settled frames are not identical: measured against frame 200 in the window, the rms difference
  over the spatial standard deviation is, for pressure, 9.1e-2 at frame 120, 5.1e-2 at 140,
  2.5e-2 at 160 and 9.7e-3 at 180 (density alike, velocity a quarter of that), and the flagged
  cells move from x 108 to 110 (frame 120) to x 107 to 109 (frame 200): the shock creeps upstream
  by about one cell. So the 81 settled frames hold one state with a slow drift; three frames
  sample it, and each added frame is a near copy. A per-frame rank statistic here is a median of
  three nearly equal frames, not three independent samples.
- **Not set:** an exclusion (every default-ladder level runs, decision 3), an analysis grid (native),
  or a slow metric.
- **Measured cost** (login node, 2026-11-27, `evaluate.py`, the three frames, default ladder of 91
  levels): the 15 deterministic metrics that run here (12 need a periodic domain and are not run),
  30.9 s in the pipeline and 52.7 s wall; `persistence_distance` 41.1 s (about 11 s of metric time a
  frame). `persistence_wasserstein` not measured. Disk: the 965 MB file, of which the window reads
  28% of each frame.

### Decisions and why

1. **A window option on `kinet_raw`** (the coordinator chose it among the three options above;
   the agent built it). About 10 lines: a pair of cell bounds per axis, applied to the spatial part
   of each read, the grid's shape and origin set from it. Alternatives: the whole domain (no code;
   the shock-set metrics would mostly score the body's outline), a mask carried through the
   pipeline (a change to every metric and degradation). To reverse: remove `window` from the
   configuration (and the option, if nothing else uses it).
2. **Every face declared `neumann`, three of them cuts** (agent). A cut is not a boundary of the
   flow, and the vocabulary (`BOUNDARIES` in `fmeval/data/base.py`) has only `periodic` and
   `neumann`. At the high-x cut the mirror makes the field continuous but reflected: a degradation
   whose kernel reaches the cut mixes the field with its mirror image instead of the flow beyond,
   so within a kernel width of it a degraded field differs from the same degradation of the whole
   domain. `periodic` would join the shock layer (p up to 0.93) to the inflow (p 0.2), a jump that
   the FFT-based degradations would smear into a false shock across the seam. At the y cuts and the
   inlet the flow is uniform to 3e-5 (y faces, frames 120 to 200) and 2e-13 (inlet), so the mirror
   is the flow. The detector pads by repeating the edge value, never wrapping, so the declaration
   does not change what it flags. To reverse: a boundary type for an open face, with an extension
   continuous across its seam, would be a new `BOUNDARIES` entry.
3. **The window is $144 \times 288$, not $146 \times 300$** (agent). The first window, x below 146
   (the page's suggestion) and all of y, dropped the four default-ladder levels of factors 8 and 16
   of `coarsen`, `coarsen_bandlimited` and `subsample`, because the mirror-extended grid
   ($292 \times 600$) is not divisible by 8 along x or by 16 along y. Ending two columns earlier and
   six rows inside each y face keeps every level and moves the cuts into uniform flow (y) or two
   nodes ahead of the body (x). The flagged cells are the same in both windows.
4. **Three frames** (agent): the reason is under "What part is evaluated". To reverse: lower
   `time.reduction`.
5. **The wake is not evaluated** (follows from decision 1): it is downstream of the body. A
   dataset of the wake would need a window behind the body, where the cylinder's outline is again
   a cut, and its unsteady shedding at Re 300 would supply the independent frames this window
   lacks. Not built.
6. **Registered as evidence** with a label that says it is the bow shock of a steady flow in a
   window upstream of the body, with cuts declared Neumann (`configs/cards/default.yaml`).

### Log entries

**2026-11-27, dataset agent (build-order step 28 completed).**

- Code: `window` on `KinetRawTrajectory` (`fmeval/data/kinet_raw.py`); configuration
  `configs/dataset/kinet_supersonic_cylinder.yaml`; page sections "The window upstream of the
  body"; registration and `python -m fmeval.cards catalog`.
- Measured with `shock_mask` (the detector of `shock_set_distance`, default threshold) in the
  window at frames 100 to 200: 45 to 56 flagged cells per frame, x 107 to 111, y 125 to 175, at
  least 38 nodes from the cylinder (centre (166.5, 150.5), radius 20); none at the cut.
- Tests: `test_window_keeps_a_block_of_cells_at_the_runs_coordinates` (synthetic, non-square;
  shape, origin, values, refusals) and the `data` test
  `test_the_cylinder_window_holds_the_bow_shock_and_none_of_the_body`, both in
  `tests/test_loader_contract.py`.
- Smoke runs under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/cylinder_smoke`
  (the deterministic panel on the three frames; `persistence_distance`).
- Not verified: what each degradation does within a kernel width of the high-x cut, compared with
  the same degradation of the whole domain (decision 2 states it, no run measures it).

**2026-11-27, dataset agent (the resolution rule and the full entropic solver: this dataset is
exempt).**

Kareem set two rules for every simulation on 2026-11-27: run fine enough that the run is stable and
its artifacts are small to negligible, and use the full entropic solver (the `entropic` stabiliser,
a Newton solve, rather than the `piecewise` lookup table). For this case he then decided, in two
sentences quoted verbatim: "For the supersonic cylinder, use the config that currently exists. You
can use the piecewise stabiliser here." and "For the supersonic cylinder, the 500×300 grid is
sufficient". **So `kinet_supersonic_cylinder` keeps the 500 × 300 run `33f78849` with the `piecewise`
stabiliser, its file, configuration, window and frames unchanged.** What was measured before the
decision is recorded here so that nobody repeats it.

*The full entropic stabiliser does not run this case.* Every run below used kinet `origin/main` at
`e67a1136e` (the 500 × 300 run used `perf/cleanup` at `d1cd353b8`), the case's settings otherwise
(Mach 1.8, Re 300, T 0.2), `collision/stabilizer@case.collision.stabilizer=entropic`, on one A100.
Each stopped with `ERROR: rollout aborted: stop_reason='solver_stopped:nonfinite_observables'`:

| Grid | Shift | Step at which values went non-finite | Job |
|---|---|---|---|
| 1000 × 600 | 0.4 (the run's value) | 31 | 62134009 |
| 1000 × 600 | 0.2 | 20 | 62134336 |
| 1000 × 600 | 0.3 | 53 | 62134336 |
| 1000 × 600 | 0.55 (kinet's shipped value) | 34 | 62134182 |
| 500 × 300 | 0.4 | 49 | 62134604 |
| 500 × 300 | 0.55 | 32 | 62134604 |

- **Why it falls back almost everywhere.** The shift is kinet's moving frame for the lattice. On it
  the product-form equilibrium is non-negative only where $|v| \le T + v^2 \le 1$ along x, with
  $v = u - s$ (kinet, `docs/notes/research/lattice_shift_dissipation.md`). Measured with the
  populations recorded: at shift 0.4 on 1000 × 600, the equilibrium `Feq` has a negative entry in
  100% of the inflow cells and in 89 to 100% of all cells over steps 1 to 600; at shift 0.55 on
  500 × 300, 98 to 99% of the fluid cells over steps 1 to 40. In such a cell the stabiliser skips
  its Newton solve and relaxes straight to `Feq`:
  `kinet/solver/lbm/collisions/entropic/numeric/stabilizer.py` lines 145 and 146,
  `failed = (F < -self.numeric.eps).any(...) | (Feq < -self.numeric.eps).any(...)`, and line 160,
  `alpha = torch.where(failed, 2.0 * tau, root.alpha)`, which `entropic.py` line 120 turns into a
  relaxation rate of 1.
- **Why it still fails where the equilibrium is positive.** At shift 0.2 on 1000 × 600 only 146
  cells beside the body had a negative entry at step 1 (0.02%), and the run stopped at step 20.
  In the cells that do take the Newton root, the root is bounded below by 1 and above only by
  population positivity: in a run saved at every step (500 × 300, shift 0.55, job 62135325) it
  reached $\alpha = 13$ at step 2 and 86 at step 4, a relaxation rate $\alpha/(2\tau)$ of up to about
  38 against 0.88 for plain BGK. kinet's own docstring (`entropic.py`, `state_equilibrium_inertia`)
  says $\alpha = 2$ at $f = f^{eq}$ holds only where $f^{eq}$ is the maximum of the entropy at the
  moments. *Inference:* the shifted product-form equilibrium is not that maximum for the entropy
  the stabiliser evaluates, so the root is unconstrained.
- **Other settings tried, before Kareem's decision ended the attempts.** Lattice temperatures that
  keep the inflow, post-shock and stagnation equilibria non-negative (`_work/positivity_windows.py`:
  shifts 0.20 to 0.77 at T 0.25, 0.33 to 0.71 at T 0.3, 0.41 to 0.67 at T 1/3, which overlap the
  stable 0.5 to 0.6; 0.64 to 0.71 at T 0.15 and 0.68 to 0.82 at T 0.2, where the cross-stream
  condition also fails in the shoulder flow), each on 500 × 300, stopped sooner: T 0.25 shift 0.5
  at step 5, T 1/3 shift 0.55 at 5, T 0.3 shift 0.52 at 6, T 0.15 shift 0.67 at 8, T 0.2 shift
  0.75 at 13, with 0.01 to 0.06% of fluid cells falling back at step 1. A ramped start is not
  available without a code change: the cylinder's initial state is always the uniform stream
  (`simulations/flow_around_objects/initialize.py`, `init_cylinder`), so an inlet ramp
  (`boundary.x.low.velocity.x`) has nothing to ramp from.
- **Cost.** `piecewise` steps 1000 × 600 at 0.024 s per step (4000 steps in 174 s of rollout, job
  62134182). The entropic stabiliser took 0.6 to 1.6 s per step on 1000 × 600 and 0.7 to 0.9 s on
  500 × 300 over the steps it ran, warm-up included, so these are not steady rates.

*How far the 500 × 300 run is from a finer one.* The same problem was run on 1000 × 600 with
`piecewise` (every length in cells doubled: radius 40, centre (333, 301); 4000 steps saved every
20th, since the step scales with the cell; Re stays 300 because kinet takes it on the diameter;
kinet run `38f0cc92`, job 62134182), coarse-grained by kinet to 500 × 300 (2 × 2 block mean,
`temporal_factor=20` with `time_method=last`, so the stored frames are the old frames' physical
times, verified on the convective clock, 0.019049 per frame), and compared with the old file at
frames 120, 160 and 200:

| Check | 500 × 300 run | 1000 × 600 run coarse-grained to 500 × 300 |
|---|---|---|
| Stand-off on the centre line | 37 cells, steady from step 1200 | 36, 36, 37 cells (74 fine cells), within one cell of final from frame 110 |
| Density jump at the nose, $\rho_2/\rho_1$ against 2.3592 | 2.334, 2.332, 2.328 (−1.1 to −1.3%) | 2.348, 2.342, 2.342 (−0.5 to −0.7%) |
| Shock width, steepest slope, stored cells | 3.91, 3.88, 3.82 | 2.73, 2.82, 2.90 |
| Shock width, 10% to 90% of the jump, stored cells | 3.2, 3.7, 2.9 | 2.7, 2.4, 2.6 |
| Overshoot behind the shock, over the jump | 0.0021 to 0.0025 | 0.0011 to 0.0015 |
| Grid-scale ripple in the shock layer, x and y, over the jump | 5.8e-5, 1.3e-4 | 5.0e-5, 1.2e-4 |
| Non-finite values, all frames | 0 | 0 |

- The ratio 2.3592 is the normal-shock relation, from conserving mass, momentum and energy across
  a stationary normal shock in a perfect gas:
  $\rho_2/\rho_1 = (\gamma+1)M^2/((\gamma-1)M^2+2) = 2.4 \times 3.24/(0.4 \times 3.24 + 2) = 2.3592$
  for $\gamma = 1.4$, $M = 1.8$. The post-shock density is the line fitted to the profile behind
  the shock (where the subsonic flow keeps compressing toward the body), evaluated at the point of
  steepest rise.
- Relative L2 difference of the two in the window, at each of the three frames: density 2.6%,
  pressure 3.7 to 3.8%, velocity 1.7% of the field's norm (7.1 to 7.3%, 6.7 to 6.8% and 7.9 to
  8.1% of its departure from the inflow), of which 97 to 99% lies in the shock band. In the smooth
  layer behind the shock (x 120 to 133, rows 135 to 165): density 0.06%, pressure 0.15%, velocity
  1.9%.
- On the 1000 × 600 grid itself the shock was 5.3 fine cells wide; block-averaged further to
  250 × 150 it was 1.6 to 1.8 cells, against 2.1 to 2.3 for the 500 × 300 run averaged the same
  way, and the smooth-layer velocity difference stayed 1.9%.
- With `piecewise`, 2000 × 1200 does not run: shift 0.4 stopped at step 80, shift 0.55 at step 5
  (also at T = 20/121).
- *Inference:* the width shrank by a factor of 0.68 when the cell was halved, so it is mostly
  numerical. One known source is the shift's interpolation viscosity, 0.12 in lattice units (kinet
  note above), about as large as the physical viscosity on 500 × 300.

*Disk.* On Kareem's instruction the fine-grid output was deleted once the checks were saved: the
1000 × 600 rollout (12.6 GB; its `.vtkhdf` is a hard link to it), its 500 × 300 coarse-graining
(3.1 GB), a scratch conversion (0.96 GB), the test rollouts of the 1000 × 600, 2000 × 1200 and
entropic attempts (6.7 GB) and the compile cache (0.38 GB). The commands in `_work/runs_*.txt` regenerate them. The scripts, the
resolved configurations and the text and JSON check outputs remain under
`/pscratch/sd/k/khegazy/kinet_datasets/supersonic_cylinder_fine/` (`_work/` and `checks/`); scratch
is purged after about eight weeks. Before the decision, the coarse-grained run was also converted
to CFS, beside the file this dataset reads:
`.../Pr-71en2_vuy-1.4_Re-3e2/D2Q9_shape-1000-600_T-4000_H-38f0cc92_cg-500-300.h5` (965 MB). No
configuration reads it.

### Open points

- No dynamics figure.
- `persistence_wasserstein`'s cost here is not measured.
- The wake, behind the body, is not a dataset (decision 5).
