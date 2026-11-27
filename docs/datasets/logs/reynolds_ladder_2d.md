# Log: doubly periodic weakly compressible flow

This log records why the configurations on [`reynolds_ladder_2d.md`](../reynolds_ladder_2d.md)
are in their current form. It follows step 7 of `docs/recipes/add-a-dataset.md`. Append new
entries at the end, and never rewrite an old one; supersede it with a new entry instead.

## Configurations that existed before this log

`kinet_re5e4`, `kinet_re5e4_dev`, `well_re5e4`, `kinet_re1e6` and `forecast_re5e4` predate this
log, and their history is not repeated here. It is recorded in these places:

- the dataset page, `docs/datasets/reynolds_ladder_2d.md`;
- `issues/011-cross-dataset-comparison.md`, on the ladder members that cannot be read;
- `judgements/009-reynolds-ladder-members-are-the-readable-runs.md`, on why the ladder runs on
  Re 5e4 and Re 1e6;
- the git log of `configs/dataset/` and of the page.

## `kinet_re5e4_512`

### 1. What it is for

It is the reference shear layer of `kinet_re5e4` at twice the resolution, the second level of a
solver refinement comparison of the reference (`dataset_specs/BUILD_ORDER.md`, step 3;
`dataset_specs/02_grid_refinement_known_solution.md`, Sect. 5.1). It lets a metric be read
against grid refinement of the same flow. No test or card uses it yet.

### 2. How it is treated

- **Source.** The file is
  `${paths.data}/kinet/doubly_periodic/weakly_compressible_isoT_fluids/sys_Re-5e4_Ma-1en1/D2Q9_shape-512-512_T-20000_H-56d32e.h5`.
  It is already in the flat layout, so no conversion was needed. It holds 20 000 steps of D2Q9
  entropic BGK at Re $5 \times 10^4$ and Ma 0.1, from the same double shear layer, as 20 001
  frames. It is 1.43 TB and stores the populations as well.
- **Configuration.** `configs/dataset/kinet_re5e4_512.yaml` inherits `_re5e4_simulation`. It
  takes from that fragment the path pattern, the fields (`density`, `velocity`, `vorticity`), the
  time selection (start 1, reduction 50), the family `reynolds_ladder_2d`, rank 0 and the label.
  It states only its name, format and trajectory, `reader.frame_stride: 2`,
  `complexity.params.resolution: 512`, and its notes.
- **Clock.** At a fixed Mach number the solver step halves with the cell size, and the run ends
  at the same time as the 256² run (2.2552744890219754, as read). `frame_stride: 2` therefore
  puts frame $i$ at the time of frame $i$ of `kinet_re5e4`, so one `dataset.time` selection
  serves both. This is the pattern `kinet_re1e6` uses with stride 4.
- **Grid and boundaries.** The grid is 512 × 512 with spacing 1, periodic on both axes, which is
  the reader's default.

### 3. Decisions and why

- **Inherit the 256² fragment instead of writing a new one.** An agent (step 3) made this
  choice. The run is the same simulation as `kinet_re5e4` at another resolution, so the
  fragment's path, fields, time selection and family all apply unchanged. Kareem's instruction
  to write the least new code favoured it.
- **Rank 0, the same as `kinet_re5e4`.** An agent left the inherited rank in place. Rank orders
  the members of a family sweep, and the configuration is not in the sweep of
  `configs/dataset_family/reynolds_ladder_2d.yaml`. If it is ever added, it needs a distinct
  rank, because `tests/test_configs.py` refuses two members that share one.
- **Not registered as evidence.** This follows the coordinator's brief: neither
  `configs/cards/default.yaml` nor `docs/decisions.md` was touched. Kareem's rule that every
  dataset built here becomes evidence (`BUILD_ORDER.md`, Decisions, item 9) still applies once
  its window is chosen.

### 4. Log entries

#### 2026-11-26: the configuration added (step-1 agent, as step 3)

- **Added:** `configs/dataset/kinet_re5e4_512.yaml`, a row on `docs/datasets/reynolds_ladder_2d.md`,
  and the configuration's name in the row of `docs/datasets/README.md`.
- **Checked with the existing reader:** `KinetRawTrajectory` opened the file in 7 s and gave a
  512 × 512 grid with spacing 1, periodic on both axes, 20 001 frames with a clock from 0 to
  2.2552744890219754, and the fields `density`, `velocity`, `vorticity` and `distribution`.
- **Smoke run:** `python evaluate.py 'metrics=[mse]' dataset=kinet_re5e4_512
  dataset.time.reduction=1000 analysis_grid.resolution=64` ran 10 of 10 001 frames and exited 0
  in 9 s. Its output is in `results/mse_1795748287`.
- **Tests:** the full default `pytest` gave 2701 passed, 397 skipped, 4 xfailed and 0 failed.
- **Not verified:**
  - that frame $i$ with stride 2 equals the clock of frame $i$ of `kinet_re5e4` at every $i$
    (only the end times were compared);
  - any physical comparison with the 256² run.

### 5. Open points

- **Node placement (spec 02, Sect. 5.1), unchecked.** kinet's current shear-layer initialiser
  places its nodes at $x_i = i/(N-1)$. If these runs were initialised that way, the 256² and 512²
  initial fields are not samples of one continuous field on nested grids. They would differ by a
  stretch of 256/255 against 512/511, which would cap any observed order of convergence at 1.
  Spec 02 says the runs may predate that code. Until this is checked, `kinet_re5e4_512` must not
  be read as a nested refinement of `kinet_re5e4`. Spec 02 proposes rerunning 128², 256² and 512²
  with nodes at $i L/N$ (`BUILD_ORDER.md`, step 19).
- No dynamics figures are drawn on the page.
- The rank collision described in section 3 must be resolved before the configuration joins the
  family sweep.

### What part is evaluated (added 2026-11-26)

This section was added after the sections above, when step 3 of `docs/recipes/add-a-dataset.md`
became "Decide what part of the dataset is evaluated". The step-1 agent made the choice, and a
person may override it.

- **Window and stride.** Frames 2000 to 10000 on the 256² clock, every 50th, give 161 frames.
  `time.start: 2000` is set in the configuration, and the reduction of 50 is inherited from
  `_re5e4_simulation`. With `frame_stride: 2`, these are the same physical times as the frames
  of `kinet_re5e4`'s developed-flow window (`evidence_window` in `configs/cards/default.yaml`),
  so the two runs can be compared frame for frame.
- **Independent samples.** On `kinet_re5e4` the same 161 frames hold 7 to 12 independent
  samples, at an integrated autocorrelation time of 13 to 23 frames
  (`METRIC_EVALUATION_CRITIQUE.md`, finding 2). The agent's conjecture is that the 512² run is
  similar, because it is the same flow at the same times. This was not measured.
- **Analysis grid.** For the metric ladder, runs pass `analysis_grid.resolution=256`, the grid
  shared with `kinet_re5e4`. A dataset configuration cannot set it, because `analysis_grid` is a
  top-level key. The native 512² grid is only for the refinement comparison of spec 02,
  Sect. 5.1, which needs each grid's own cells.
- **Measured cost.** All runs were on a shared login node on 2026-11-26, with other agents' runs
  active, so the times are approximate. Costs are per frame at 256², with every severity level
  of the default ladder (91 levels across density, velocity and vorticity):

  | Part | Seconds per frame | Run |
  |---|---|---|
  | degrading the fields (shared by every metric in a run) | 5.5 to 5.9 | `mse_1795754894`, `comparison_1795755697` |
  | `mse` | 0.04 | `mse_1795754894` (9 frames) |
  | `wasserstein` (density) | 5.6 | `comparison_1795755697` (3 frames) |
  | `increment_w1_by_separation` | 16.4 | one frame, run alone |
  | `energy_distance` | 27.4 | one frame, run alone |
  | `spectral_energy_flux` (velocity) | 32.1 | one frame, run alone |
  | `persistence_distance` (density, vorticity) | 34.0 | `comparison_1795755697` (3 frames) |
  | `persistence_wasserstein` | more than 880; it did not finish one frame in 900 s | stopped |

  The four one-frame runs ran at the same time as each other. All results are under
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets`, which scratch purges.
- **Projected full panel.**
  - The panel is the 25 deterministic metrics that apply to a dataset without ensembles or
    pressure. `persistence_wasserstein` is left out, as it is on `kinet_re5e4`: its card records
    that its degradation ladders on the turbulence datasets did not finish in about ten hours.
  - The roughly 19 cheap metrics are assumed to cost about what `mse` costs, about 1 s per
    frame together. This is a conjecture.
  - The sum is about 122 s per frame, or 5.5 h for the 161 frames in one process.
    `dataset.time.shards` splits that across processes.
  - With `persistence_wasserstein` included, the cost would be more than 44 h.
  - At the native 512² grid, degrading the fields alone took 76.5 s per frame (`mse_1795754969`,
    9 frames, 763 s), which is 3.4 h for the window before any metric runs.
- **Disk.** The file stays where it is (1.43 TB, not copied). A run reads one chunk per field per
  frame: 4 channels × 512² × 8 bytes = 8.4 MB per frame, so 1.35 GB for the window. The
  calibration rereads a few of those frames.
- **Why this balance.** Keeping `kinet_re5e4`'s frames exactly makes every per-frame statistic
  of the two runs come from the same physical times, and that comparison is what this
  configuration exists for. `dataset.time.reduction=200` would keep 41 of those frames, at about
  1.4 h. Since its spacing is still shorter than the autocorrelation time, it would probably keep
  most of the independent samples (conjecture). It was not taken because 5.5 h is affordable when
  sharded. Taking it later is a one-line change that keeps the frames a subset of
  `kinet_re5e4`'s.

#### 2026-11-26: the evaluated part decided and measured (step-1 agent)

- **Changed:** `configs/dataset/kinet_re5e4_512.yaml` gained `time.start: 2000` and a comment
  recording the choice and the costs.
- **Commands:** `python evaluate.py` with `dataset=kinet_re5e4_512 dataset.time.start=2000` and
  `paths.results=/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets`:
  - `mse` at reduction 1000 (9 frames), on grids 256 and 512;
  - `mse,wasserstein,persistence_distance` at reduction 4000 (3 frames), on grid 256;
  - each of `persistence_wasserstein`, `energy_distance`, `increment_w1_by_separation` and
    `spectral_energy_flux` alone, on frame 6000 at grid 256, with a 900 s limit.

  Every run exited 0 except `persistence_wasserstein`, which hit the limit. A first attempt
  running those four metrics together on 3 frames was stopped after about 44 minutes.
- **Not verified:** the autocorrelation time on this run, the cost of the cheap metrics other
  than `mse`, and the times on an idle node.

#### 2026-11-27: registered as evidence (registration agent)

- **Registered:** `kinet_re5e4_512` (`{periodic: true, ensemble: false}`) in
  `evidence_datasets` and `evidence_dataset_properties` of `configs/cards/default.yaml`. Kareem
  decided the rule on 2026-11-26 (`dataset_specs/BUILD_ORDER.md`, "The task" and decision 9:
  every dataset built in that plan is an evaluation dataset, admitted to `evidence_datasets`
  with a label naming the kind of claim it supports); the agent chose the label.
- **Label** (completes "n frames of ..." in a card's run summary): "the developed flow of
  kinet_re5e4 simulated on 512^2 cells, at the same times; not yet shown to be a nested
  refinement of it". It says the nested refinement is unchecked, because the node-placement
  point of section 5 is open.
- **Window:** kinet_re5e4's developed-flow window, frames 2000 to 10000 every 50th, which
  `evidence_window` already states and `frame_stride: 2` maps onto the same times;
  `analysis_grid.resolution=256` stays a command-line setting, listed beside `evidence_window`.
- **Supersedes** the line "Not registered as evidence" of section 3 and the open point that no
  window was chosen and the configuration is not evidence.
- **Not done:** no metric was run on it for a card; every metric card's *Across the experiments*
  table shows it as *not yet run* or *not applicable* with the reason (`python -m fmeval.cards
  catalog`). Producing that evidence is its own step in `BUILD_ORDER.md` and needs compute.

#### 2026-11-27: the evaluated part cut to 21 frames, its grid stated in the config (step-32 agent)

- **What changed.** `time.reduction` went from the inherited 50 to 400 in
  `configs/dataset/kinet_re5e4_512.yaml`: frames 2000 to 10000 every 400th, 21 frames instead
  of 161, still at times of kinet_re5e4's frames. The 256 analysis grid is now the config's own
  `analysis_resolution: 256`, a dataset key added by step 32; it is no longer a command-line
  setting, and `analysis_grid.resolution=null` reads the native 512 for the refinement
  comparison.
- **Why.** Kareem asked why the evidence needs so long. The 161 frames held only 7 to 12
  independent samples (METRIC_EVALUATION_CRITIQUE.md, finding 2), and matching kinet_re5e4 frame
  for frame had no statistical reason. 21 frames keep one or two frames per independent sample.
- **Who decided.** The coordinating session made the cut, recorded as decision 17 of
  `dataset_specs/BUILD_ORDER.md`; this agent applied it.
- **Cost.** About 122 s per frame at 256 for the panel without `persistence_wasserstein`
  (measured 2026-11-26, above), so about 43 minutes for the 21 frames in one process (my
  arithmetic).
- **Verified.** The configuration builds into the schema with 21 selected frames (2000, 2400,
  ..., 10000) of the reader's 10001 and an analysis grid of 256. No metric was run.
- **Supersedes** the 161-frame window and the command-line grid of "What part is evaluated" and
  of the registration entry above.

#### 2026-11-27: where the runs' configurations are kept (dataset agent)

- The solver configuration of every shear-layer run these configurations read, with the command
  that rebuilds each on the current kinet and what stands in the way of an exact reproduction,
  is in `docs/datasets/logs/kinet_runs/` (`kinet_re5e4/`, `kinet_re5e4_dev/`,
  `kinet_re5e4_512/`, `kinet_re1e6/`, `shear_layer_prev_256/`, and the README section "The
  shear layer"), step 31 of `dataset_specs/BUILD_ORDER.md`. The refinement reruns of step 19
  are archived in `shear_layer_refinement/` there and the timing run of step 15 in
  `kinet_re5e4_timing/`; neither is read by a configuration yet.

#### 2026-11-27: the node placement checked, the pair is not nested (dataset agent, batch 2)

- **Supersedes** the open point "Node placement (spec 02, Sect. 5.1), unchecked" of section 5
  and the label's "not yet shown to be a nested refinement".
- **Measured.** Frame 0 velocity of `D2Q9_shape-256-256_T-10000_H-dc804f.h5` (`kinet_re5e4`) and
  `D2Q9_shape-512-512_T-20000_H-56d32e.h5` (`kinet_re5e4_512`), against kinet's shear-layer
  profile (`kinet/initialization/shear_layer.py`, $\lambda = 80$, $\epsilon = 0.05$, $U$ the
  file's largest $|u_x|$) at two placements: nodes at $i/(N-1)$ match to $4.6 \times 10^{-15}$
  (256) and $1.1 \times 10^{-14}$ (512) of $U$; cell centres $(i + \tfrac12)/N$ miss by 0.077
  and 0.039 of $U$. The new refinement runs are the reverse (centres to $3.8 \times 10^{-15}$).
  Block-averaged, the old $512^2$ initial velocity differs from the old $256^2$ by
  $2.93 \times 10^{-4}$ rms, $7.3 \times 10^{-3}$ of the rms velocity (0.0398); the new pair by
  $2.03 \times 10^{-5}$. Density is uniform to round-off in all four. So the job agent's
  suspicion holds: the 7e-3 starting gap is the old placement.
- **Consequence.** `kinet_re5e4_512` stays what its configuration says, the same flow on a finer
  grid at the same times, but it is not a nested refinement of `kinet_re5e4`. Its label in
  `configs/cards/default.yaml` now says so ("not a nested refinement of it, since both runs place
  their nodes at i / (N - 1)"), and the page says so. The nested sequence is
  `kinet_shear_layer_refinement` (next section).

## `kinet_shear_layer_refinement` (three nested grids, the finest as reference, 2026-11-27)

### What it is for

The shear layer's discretisation error, measured as a coarser run's departure from a finer run of
itself on nested cells (`dataset_specs/02_grid_refinement_known_solution.md`, Sect. 5.1;
build-order step 19). At $256^2$ it is the error of the grid `kinet_re5e4` runs on; at $128^2$ a
coarse solver as a candidate, a solver-made degradation beside the ladder's operators.

### How it is treated

- **Source.** Three kinet runs made on 2026-11-27 by the job agent (case
  `doubly_periodic/shear_layer`, Re 5e4, on $N^2$, $N$ = 128, 256, 512; 1000, 2000, 4000 steps,
  saved every 10, 20, 40 steps; kinet `perf/cleanup` at `d1cd353b8`, one A100). Records in
  `docs/datasets/logs/kinet_runs/shear_layer_refinement/` and that README's section "Runs of the
  second batch".
- **Conversion.** `python -m fmeval.data.convert_kinet` from
  `/pscratch/sd/k/khegazy/kinet_datasets/shear_layer_refinement/doubly_periodic/shear_layer/{046744f0,2686f5c9,2b86fad7}/tiers/full/rollout.h5`
  to `/global/cfs/cdirs/m4790/Data/kinet/doubly_periodic/weakly_compressible_isoT_fluids/sys_Re-5e4_Ma-1en1_refinement/N128.h5`,
  `N256.h5`, `N512.h5` (53.0, 211.9 and 847.3 MB, 0.6 to 1.5 s each). Step 1 dropped by the
  converter; 101 frames each; density, velocity, vorticity (the gauge pressure is not carried,
  issue 101). Every frame and the clock read back equal to the source; the three clocks are
  bitwise equal.
- **Reader.** `kinet_raw` on the $512^2$ run with two options: `box: 1.0` (the Taylor–Green
  option: cell $1/N$, velocity over $u_l$, clock `time_convection`) and `candidate: N<n>.h5`, a
  new option (about 20 lines with `predictions()` and `frame_columns()`) that opens the coarser
  run in the same folder with the same options as the prediction and labels the rows with its
  resolution, as a forecast's. The pipeline remaps the reference by block averages onto the
  analysis grid, which the configuration sets to the candidate's ($128$ or $256$, from
  `dataset.trajectory`). With `box` the two sides share their `GridSpec` exactly (spacing
  $4/512 = 1/128$), which the pairing requires.
- **Fields.** Density, velocity, vorticity; vorticity is recomputed from the remapped velocity
  on the analysis grid (`recompute_derived`), on both sides.

### What part is evaluated

- **Kept:** frames 10 to 100, every 10th: $t = 0.045$ to $0.451$, 10 times, each candidate on its
  own grid. Both candidates are run (`-m dataset.trajectory=256,128`).
- **Why.** The frames are one deterministic error history, not samples; ten of them show the error
  growing from the start of the roll-up, where the three-grid order is 2.3 to 2.5 (frame 10), to
  the end, where it is 3.6 to 3.8 (the job's table). Frame 0 (the initial condition) is left out: its departure is a point value
  against a cell average.
- **Not set:** an exclusion (the ladder is replaced by the candidate, keeping the clean entry and
  `mean_field`) or a slow metric (the persistence metrics take seconds here).
- **Measured cost** (login node, 2026-11-27, `evaluate.py`, the 10 kept frames): the 29
  deterministic metrics other than the two persistence ones, 12.3 s wall at 128 (4.0 s of metric
  time) and 31.0 s at 256 (18.3 s); `persistence_distance` and `persistence_wasserstein`
  together 6.9 s and 14.5 s wall. The whole panel on both candidates is about a minute. Disk
  1.1 GB, all read (the $512^2$ reference 847 MB).

### Decisions and why

1. **A `candidate` option on `kinet_raw`, not forecast files and not a new reader** (agent).
   `BUILD_ORDER.md` planned the converter's unbuilt `forecast` half for candidates, writing the
   block-averaged reference beside each coarse run. The pipeline's conservative remap already
   computes that block average on the analysis grid, so a pairing of two existing files does it
   with no second copy of the data and no new conversion: `predictions()` was already the route
   (`evaluate.py`, `ForecastPairs`, `ClosedFormTrajectory`). `ForecastPairs` itself needs both
   sides in one file. To reverse: delete the option and the configuration.
2. **The candidate is named by its cell count, `trajectory: "256"`**, so that one value sets both
   the file name (`N` followed by the trajectory) and the analysis grid (an interpolation of the
   trajectory); a name like `N256` would have needed the grid stated twice. A pair on the
   wrong grid is refused by the pipeline ("a pair must share its grid").
3. **The candidate file is resolved beside the reference**, so the published copy at
   `paths.data_url` reads the same pair. To reverse: take a full path.
4. **Registered as evidence** with a label that says the reference is the finest grid and the
   grids are not in the asymptotic range (`configs/cards/default.yaml`).

### Log entries

**2026-11-27, dataset agent (batch 2, build-order step 19).**

- Converted the three runs (above); checked every frame and the clocks.
- Code: `candidate` on `KinetRawTrajectory`, `Trajectory._candidate_columns`; config
  `kinet_shear_layer_refinement`; page section "The shear layer on three nested grids".
- Verified: through the pipeline with derived fields recomputed, `rmse` equals the job's
  $E_{128}$ and $E_{256}$ (`_scripts_batch2/shear_layer_refinement_differences.json`) at all 101
  frames to $2 \times 10^{-14}$ relative (density as is, velocity times $\sqrt2\,u_l$, vorticity
  times $u_l$), and at the kept frames in a `data` test; a synthetic test checks the pairing
  against a block average computed in the test.
- Smoke runs under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/batch2_smoke`.

### Open points

- No dynamics figure.
- The sequence is not an observed order; a three-grid order would need a reading of the
  $128^2$ run against the $256^2$ one, which `observed_order` does not take.
