# Log: Sod shock tube

This log covers every configuration on [the Sod shock tube page](../sod_shock_tube.md). Each
configuration has its own section.

## `sod_shock_tube` (the exact solution)

This log does not reconstruct the history of the analytic configuration. It is recorded in
three places: `ANALYTIC_DATASETS_LOG.md` at the repository root (untracked), the entry on Sod
in `docs/decisions.md`, and the git log of `fmeval/data/analytic.py`,
`configs/dataset/sod_shock_tube.yaml` and `docs/datasets/sod_shock_tube.md`.

## `kinet_sod_gamma1p4` and `kinet_sod_gamma2` (kinet simulations)

### What they are for

They give the repository a shock produced by a solver, not by a formula. That shock can be
set against the exact solution of the same states, and it can be a reference for the
degradation ladder for metrics that need a shock or an absolute pressure. Build-order step 4
asked for them (`dataset_specs/BUILD_ORDER.md`), following
`dataset_specs/02_grid_refinement_known_solution.md`, Sect. 5.2, which uses the kinet runs
against the exact Riemann solution, and `dataset_specs/03_two_dimensional_shocks.md`,
Sect. 4.7.

### How they are treated

- **Source.** Three kinet lattice-Boltzmann runs under
  `/global/cfs/cdirs/m4790/Data/kinet/sod/compressible_fluids/`, each with its run
  configuration in a `configs/` folder beside it. All are compressible D2Q9 (two populations)
  with entropic BGK collision and Prandtl number 0.71, on 3001 × 5 nodes of unit spacing, for
  1000 solver steps saved every step.
  - `Pr-71en2_vuy-1.4_visc-1en4/D2Q9_shape-3001-5_T-1000_H-d17baf.h5`: $\gamma = 1.4$,
    viscosity $10^{-4}$, left $(\rho, p) = (1, 0.2)$, right $(0.125, 0.02)$.
  - `Pr-71en2_vuy-2_visc-25en3/D2Q9_shape-3001-5_T-1000_H-15aa6b.h5` and `..._H-c76b17.h5`:
    $\gamma = 2$, viscosity 0.025, left $(0.5, 0.1)$, right $(2, 0.05)$.
- **Conversion.** Each file was rewritten by `python -m fmeval.data.convert_kinet` into
  `<run>_flat.h5` in the same folder. The source files were not changed.
- **Reader and options.** The reader is `kinet_raw`, with `include_redundant: true` and
  `boundary: [neumann, periodic]`.
- **Fields.** Kept: density, velocity, and the absolute pressure. Dropped by the converter:
  temperature, energy, the populations and the stability fields. Vorticity is not stored by
  these runs and is not listed, because it is zero to round-off.
- **Grid and boundaries.** The grid is 3001 × 5 with unit spacing. The axis along the tube
  is Neumann and the axis across it is periodic.
- **Time.** There are 1001 frames: the initial condition and steps 1 to 1000. The clock is
  kinet's `time/time`, 0.2 per step, and each frame's solver step is in the file's
  `time_index`. The default window is steps 500 to 1000, every 50th step.
- **Shared settings.** The settings shared by both configurations are in the fragment
  `configs/dataset/_kinet_sod.yaml`. Each configuration states its path, its trajectory and
  its parameters.

### What part is evaluated

Chosen by the agent on 2026-11-26 under step 3 of `docs/recipes/add-a-dataset.md`; it
supersedes the window of decision 7 below. Kareem may override it. Every number here was
measured on the $\gamma = 1.4$ run on the login node, with the median blur skipped, except
where it is marked as arithmetic.

- **Window: steps 450 to 1000** (`time.start: 450`).
  - Frames 0 to 449 are the start-up. Frame 0 is the bare discontinuity. Before step 434, the
    narrowest region between two waves of the $\gamma = 1.4$ run (contact to shock,
    0.369 nodes per step) is under 160 nodes, ten times the default ladder's largest
    translation of 16 cells. That is the rule the exact solution's window uses. At step 450 it
    is 166 nodes.
  - Every stored frame is valid. No wave reaches a wall before step 1914 ($\gamma = 1.4$) or
    2372 ($\gamma = 2$), from the exact wave speeds, so the window runs to the last stored
    step, 1000.
  - The $\gamma = 2$ run's rarefaction is never 160 nodes wide (89 at step 1000). It shares
    the window anyway, so that one fragment serves both runs.
- **Stride: every 50th step** (`time.reduction: 50`), 12 frames.
  - In a dense run over steps 450 to 1000 every 5th step (111 frames, `mse` and
    `shock_set_distance`), the Politis–White block length that the analysis computes
    (`blindness_block_length`) has a median of 17 frames for density, 16 for pressure and 17
    for velocity under `mse`. Seventeen frames of 5 steps is about 85 solver steps, so the
    550-step window holds about 6 to 7 independent samples (arithmetic). Its median for
    `shock_set_distance` is 1, because that trace is nearly constant.
  - A stride of 50 puts one or two frames in each block. A shorter stride adds cost without
    adding samples; a longer one would leave fewer than the 6 to 7 samples the window holds.
  - The run is one self-similar event, so these are samples along one trajectory, not
    independent realisations.
- **Analysis grid: native**, 3001 × 5. Both numbers are prime, so no coarser grid divides
  them. Native is also cheap enough.
- **$\gamma = 2$: evaluated for every metric.** Its shock-set metrics flag nothing and score
  the both-empty 0 (decision 9). They cost about 0.1 s a frame, and no existing selector removes
  a metric for one dataset, so they run, and their rows are read as that null. The run's
  real value is for the non-shock metrics, on a viscous, smeared shock.
- **Median blur.** No dataset-level ladder exclusion exists: `DatasetConfig` has no ladder
  key, and `degradation.skip` belongs to the degradation group, which a dataset configuration
  cannot set. These configurations are therefore run with `degradation.skip=[median_blur]` on
  the command line, as the fragment's comment says.
  - With it on, the cost per frame is about 11 minutes. That is extrapolated from timing
    `median_filter` on the 6002 × 5 extended grid: 17 s at width 287 and 100 s at 669. Those
    are the calibrated widths for density at the first two levels; the third, 1051, scales to
    about 245 s.
- **Measured cost per frame** (5 frames, steps 500 to 1000; the total time over 5):
  - `mse`: 5.8 s (degradations 4.5 s, metric under 0.01 s);
  - `shock_set_distance`: 2.7 s (pressure only);
  - `persistence_distance`: 5.4 s (density only; the metric itself 2.5 s);
  - the 17 metrics that run here: 15.8 s. They are every non-periodic, non-ensemble metric
    whose fields the dataset has: `mae`, `max_error`, `max_error_channel_mean`, `mse`,
    `nrmse`, `rmse`, `rmse_channel_mean`, `vrmse`, `kinetic_energy`, `persistence_distance`,
    `persistence_wasserstein` and the six shock-set metrics.
- **Projected full panel:** 12 frames × 15.8 s ≈ 3.2 minutes, plus about 15 s of start-up, per
  configuration; about 7 minutes for both (arithmetic).
- **Disk:**
  - the three converted files: 481 MB each, 1.44 GB together. They hold all 1001 frames; the
    window reads 12.
  - the grouped sources: 7.8 GB each (populations included). They were left in place, because
    no data is deleted.
  - results: 37 MB for the 17-metric panel on 5 frames, so about 90 MB per configuration at 12
    frames (arithmetic).
- **Why this balance.** The 12 frames hold every independent sample the window has, at
  minutes per configuration. Keeping all 551 frames would cost about 2.4 hours per
  configuration for no further samples, and starting earlier would add frames where the
  ladder's translations can merge waves.

### Decisions and why

1. **The data is converted to fit the existing reader; no new reader is written.**
   - Made by: Kareem, 2026-11-26 (`BUILD_ORDER.md`, "How data reaches the metrics").
   - Alternative: a reader for kinet's grouped layout. Kareem rejected it.
   - To reverse: Kareem's decision would have to change first.
2. **The converter falls back to the clock `time/time`.**
   - Made by: the agent, 2026-11-26.
   - Reason: these files predate kinet's `time/time_convection`, so `time/time` is the only
     clock they hold. In them it is kinet's nondimensional clock, step / 5, not a step count
     as in current kinet files. The converter carries it unchanged and records the clock's
     name in the `source` attribute of the converted `time` dataset.
   - Alternative: rebuild a time in domain crossings. There is no Mach-based crossing time for
     the Sod problem, and any rebuilt time would be invented, not converted.
   - To reverse: delete the fallback in `fmeval/data/convert_kinet.py`. Files without
     `time_convection` would then fail to convert.
3. **Without a `pressure_convention` attribute, the converter checks the pressure.**
   - Made by: the agent, 2026-11-26.
   - Rule: the pressure counts as absolute only if the initial condition satisfies kinet's
     ideal-gas law $p = \rho T$ (relative tolerance $10^{-12}$); otherwise the file is refused.
     A gauge pressure $(\rho - 1) c_s^2$ fails the check.
   - Measured: on all four older files the difference is exactly zero, at the initial
     condition and at later frames.
   - Alternatives considered: a command-line flag declaring the convention, which is an
     assertion the data does not back; or dropping the pressure, which would lose the field
     these runs exist for.
   - To reverse: delete the check. Older files would then be refused, as an unknown convention
     is.
4. **The runs are read as two-dimensional 3001 × 5 grids, not as one row.**
   - Made by: the agent, 2026-11-26.
   - Reason: the `kinet_raw` reader takes its grid from the file. Reading one row would need
     new reader code or a converter that changes the data's shape, and the plan's code rule
     says to fit the data to the existing code. Every field is uniform across the 5 nodes to
     $2 \times 10^{-14}$ and the transverse velocity is below $10^{-15}$, so a mean over the
     grid equals the mean along the tube and nothing is lost.
   - Costs, measured: coarsening and subsampling are dropped at every level because no factor
     divides 5 nodes. `translate_y` is an identity and is excluded. The median blur is slow
     (decision 7).
   - To reverse: add a row-selection option to the reader, or a squeeze to the converter, and
     declare a one-dimensional grid.
5. **The axis across the tube is declared periodic.**
   - Made by: the agent, 2026-11-26.
   - Reason: the run configurations give Neumann faces only on dimension 0. That they name no
     face on the y axis, and that this older kinet layout therefore streams y periodically, is
     the agent's reading of the configuration, not something checked in kinet's code. It does
     not change any result: the fields are uniform across y, so a periodic extension and a
     mirror extension are identical. Periodic also avoids doubling the y axis in the
     extension.
   - Alternative: `neumann` on y, which gives the same values.
   - To reverse: set `reader.boundary` to `[neumann, neumann]` in `_kinet_sod.yaml`.
6. **`include_redundant: true`.**
   - Made by: the agent, 2026-11-26.
   - Reason: `kinet_raw` drops pressure by default because in the isothermal runs it is
     density times $c_s^2$. Here it is the absolute $p = \rho T$ with a varying temperature, so
     it carries information that density does not, and the shock metrics need it.
   - To reverse: remove the option. The reader then drops pressure, and the shock metrics do
     not run.
7. **The window is steps 500 to 1000, every 50th step.**
   - Made by: the agent, 2026-11-26.
   - Reason: this follows the rule of the exact solution's window: the narrowest region
     between two waves should be more than ten times the ladder's largest translation
     (16 cells). For $\gamma = 1.4$ that region is 184 nodes at step 500. The $\gamma = 2$
     run's rarefaction is only 45 nodes wide at step 500 and 89 at step 1000, so no window of
     that run meets the rule. The same window was kept for both runs, to keep one fragment.
     The stride of 50 gives 11 frames, close to the exact solution's 10.
   - Alternative: a later start for $\gamma = 2$ alone. Step 751 meets the rule for the
     contact-to-shock region, but the rarefaction would still be too narrow.
   - To reverse: override `time.start` and `time.reduction` in either configuration.
8. **The median blur was turned off in the smoke runs only; it stays on in the default
   ladder.**
   - Made by: the agent, 2026-11-26.
   - Reason: its window is square, and a calibrated width of hundreds of nodes wraps the 5
     transverse nodes many times. The cost grows with the square of the width: measured on
     this grid, 0.7 s at width 51, 2.2 s at 101 and 8.8 s at 201 per field. The answer is still
     correct, because on a field uniform across y the median over the wrapped square equals
     the median along the row. With the median blur on, a run of 6 frames had not finished
     after about four minutes; with it off, the run took 36 s. The analytic Sod page already
     reports the median blur as degenerate on a step.
   - The fragment documents the override `degradation.ladder.median_blur.enabled=false`. A
     dataset configuration cannot turn off a degradation.
   - To reverse: run with the default ladder and accept the cost.
9. **On the $\gamma = 2$ run, the shock metrics score 0.**
   - Made by: no one; it is a measured property, recorded so that no one mistakes it for a
     bug.
   - Measured: with viscosity 0.025 the shock is spread over many nodes. The largest ratio of
     neighbouring pressures is 1.044 at step 500 and 1.047 at step 1000, below the detector's
     ratio for a Mach 1.3 shock. `shock_set_distance` therefore flags no cell in either the
     reference or any candidate, and every score is the both-empty value 0. On the
     $\gamma = 1.4$ run it flags one column of 5 nodes.
   - Not changed: thresholds are fixed once in the evaluator and never tuned per dataset
     (`CLAUDE.md`).
10. **`c76b17` is the default of `kinet_sod_gamma2`, and `15aa6b` stays selectable.**
    - Made by: the agent, 2026-11-26.
    - Reason: both have the same configuration. `c76b17` was resumed at step 930
      (`kinet_segment_pred_length` is 70) and is kinet's `latest.h5`. The two agree to
      $8 \times 10^{-14}$ in density, and their clocks differ by $3 \times 10^{-14}$ from step
      930 on.
    - Alternative: the uninterrupted `15aa6b` as the default.
    - To reverse: change `trajectory` in `kinet_sod_gamma2.yaml`, or pass
      `dataset.trajectory=D2Q9_shape-3001-5_T-1000_H-15aa6b`.
11. **Not registered as evidence.**
    - Made by: the coordinator's instruction for step 4.
    - To reverse: add the configurations to `evidence_datasets` in
      `configs/cards/default.yaml` with a claim label.

### Log entries

**2026-11-26, agent (build-order step 4).**

- Code: extended `fmeval/data/convert_kinet.py` by about 11 lines (decisions 2 and 3).
- Tests, in `tests/test_loader_contract.py`:
  - the round-trip test also runs on an "older" fixture, with no convention and its clock in
    `time/time`;
  - a refusal case for an older file whose pressure is not $\rho T$;
  - the `-m data` test now also runs on the converted `d17baf`.
- Data written: `D2Q9_shape-3001-5_T-1000_H-{d17baf,15aa6b,c76b17}_flat.h5`, beside their
  sources, 481 MB each, 5 to 10 s each on the login node.
- Configurations: `_kinet_sod`, `kinet_sod_gamma1p4` and `kinet_sod_gamma2`. The Sod page's
  table and a section on the kinet runs were updated, as was the index row.
- Verified:
  - every one of the 1001 frames of density, velocity and pressure, and the clock, read back
    through `kinet_raw` equal to the source, value for value, for all three files;
  - smoke runs of `python evaluate.py 'metrics=[mse,shock_set_distance,spectrum_l2]'
    dataset=<name> dataset.time.reduction=100 degradation.ladder.median_blur.enabled=false
    paths.data_url=null` under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets`
    (comparisons `1795751644` and `1795751680`). `spectrum_l2` is not run because the domain
    is not periodic, and 12 coarsening and subsampling levels are dropped;
  - the default `pytest` passed.
- Not verified:
  - kinet's code for its default on an unnamed face (decision 5);
  - a run with the median blur on, to completion;
  - any comparison with the exact solution.

**2026-11-26, agent (what part is evaluated, step 3 of the dataset recipe).**

- The window changed from steps 500 to 1000 (decision 7) to steps 450 to 1000, still every
  50th step, in `configs/dataset/_kinet_sod.yaml`. Comments in it and in both configurations
  record the choice. Section "What part is evaluated" above gives the reasons and the
  measurements.
- The median blur is now skipped with `degradation.skip=[median_blur]`, rather than the
  `degradation.ladder.median_blur.enabled=false` that decision 8 names. Both work; `skip` is
  the ladder's own exclusion list.
- Runs, all under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets` with logs
  `measure_{mse,shock,persist,panel,dense}.log`:
  - three single-metric runs and one 17-metric run on 5 frames;
  - one dense run on 111 frames (stamp `1795753920`, 643 s);
  - a direct timing of `median_filter` at two widths.
  The block lengths were read with `fmeval.analysis.analyse` on the dense run's
  `results.csv`.
- Not verified:
  - the block length of the $\gamma = 2$ run, which is assumed to be similar;
  - a full panel run at the new default window;
  - the median blur's cost end to end (only extrapolated).

#### 2026-11-27: registered as evidence (registration agent)

- **Registered:** `kinet_sod_gamma1p4` and `kinet_sod_gamma2`, each `{periodic: false, ensemble:
  false}` (Neumann ends), in `evidence_datasets` and `evidence_dataset_properties` of
  `configs/cards/default.yaml`. Kareem decided the rule on 2026-11-26
  (`dataset_specs/BUILD_ORDER.md`, "The task" and decision 9: every dataset built in that plan
  is an evaluation dataset, admitted to `evidence_datasets` with a label naming the kind of
  claim it supports); the agent chose the label.
- **Label** (completes "n frames of ..." in a card's run summary): `kinet_sod_gamma1p4`: "a
  lattice-Boltzmann solver's Sod shock tube at gamma = 1.4, a simulated shock rather than the
  exact one, and nothing about turbulence"; `kinet_sod_gamma2`: "a lattice-Boltzmann solver's
  Sod shock tube at gamma = 2, whose viscous shock is too spread for the shock detector to flag,
  so every shock-set metric scores 0 on it; nothing about turbulence". The gamma = 2 run was
  registered rather than left out because Kareem's rule admits every built dataset and the zero
  is itself a measurement of the detector; its label says the zero comes from no shock being
  flagged, so a shock-set card citing it cannot be read as a perfect score.
- **Window:** the fragment's `time:` selection, steps 450 to 1000 every 50th (12 frames).
  `degradation.skip=[median_blur]` cannot be stated in a config (`BUILD_ORDER.md`, framework
  limit 3) and is listed beside `evidence_window`.
- **Supersedes** decision 11, "Not registered as evidence".
- **Not done:** no metric was run on it for a card; every metric card's *Across the experiments*
  table shows it as *not yet run* or *not applicable* with the reason (`python -m fmeval.cards
  catalog`). Producing that evidence is its own step in `BUILD_ORDER.md` and needs compute.

#### 2026-11-27: the median blur excluded in the config (step-32 agent)

- **What changed.** `configs/dataset/_kinet_sod.yaml` now states
  `exclude_degradations: {median_blur: ...}`, a dataset key added by step 32. A run drops the
  entry, logs it with the reason and records it as `excluded_degradations` in `run_meta.json`;
  the report's provenance table lists it. `degradation.skip=[median_blur]` is no longer needed on
  the command line, and no longer listed beside `evidence_window`.
- **Why.** The median blur's square window wraps the 5 transverse nodes and costs about 11
  minutes per frame here ("What part is evaluated" and decision 8 above); an exclusion in the config is recorded with its
  reason, where a command-line skip was recorded only as an override.
- **Who decided.** Kareem approved fixing the framework limits, this one among them, on
  2026-11-27 (decision 15 of `dataset_specs/BUILD_ORDER.md`, step 32); the coordinating session
  asked for the exclusion on these configurations; this agent applied it.
- **Verified.** Both configurations build with the exclusion; a test runs an exclusion end to end
  on another dataset and checks the log line, `run_meta.json` and the missing rows
  (`tests/test_configs.py`). No metric was run on these runs.

#### 2026-11-27: where the runs' configurations are kept (dataset agent)

- The configurations of the two kinet Sod runs, with the command that rebuilds each on the
  current kinet and what stands in the way of an exact reproduction, are in
  `docs/datasets/logs/kinet_runs/kinet_sod_gamma1p4/` and `kinet_sod_gamma2/` (README sections
  of the same names), step 31 of `dataset_specs/BUILD_ORDER.md`. The nested-resolution runs of
  step 17 are archived in `kinet_sod_refinement/` there; no configuration reads them yet.

#### 2026-11-27: the refinement sequence scored against the exact solution (dataset agent, batch 2)

- The first two open points below are now built, as a configuration of its own,
  `kinet_sod_refinement`, in the section of that name at the end of this log. These two
  configurations are unchanged and stay the ladder's references (decision 1 of that section).
- Measured: `d17baf`'s first right-state node is 1501, while the new 3001-node run's is 1500, and
  at step 1000 the two differ by up to 0.09 in density even after a shift of one node, so the new
  run is not a copy of `d17baf`.

### Open points

- Scoring each run against the exact solution, frame by frame on the same nodes, is not
  built (spec 02, Sect. 5.2). The repository's exact solver covers both runs' states through
  its reader overrides.
- The refinement sequence of spec 02, Sect. 5.2 (reruns at 1501 and 751 nodes) does not
  exist.
- The $\gamma = 2$ run gives the shock metrics nothing to detect (decision 9).
- Neither run has a dynamics figure, and no metric has been run on either for a card.

## `sod_shock_tube`: the exact solution at a shifted time (2026-11-27)

### What it is for

Spec 03, Sect. 3.6 asks for the exact solution
at $t + \delta t$ scored against the one at $t$: every jump keeps its exact size and each wave is
displaced by its own speed times $\delta t$, so a metric that tracks the shock can be checked
against $S_R\,\delta t$, and a pointwise metric's saturation at the jump size is exposed.
Build-order step 7.

### How it is treated

- **One reader option, no new reader** (agent). The reader had no `candidate` and no time
  parameter. It gained `time_offset`, which evaluates every frame at $t + \delta t$ (the
  diaphragm bursts at $-\delta t$), and the generic `candidate` of `ClosedFormTrajectory`, so the
  shifted solution is `candidate={time_offset: dt}` through the existing `predictions()` route and
  `evaluate.py`'s existing hook. About ten changed lines. With the default offset of 0 every frame
  is bitwise what it was. The proposal's alternative, a paired-time degradation operator, was not
  needed.
- **Refusals.** `t_start + time_offset` must be positive and `t_end + time_offset` before the
  first wave reaches a wall; a candidate is validated by the same constructor.
- **Configuration.** None added: the candidate is an override on the page,
  `'+dataset.reader.candidate={time_offset:0.01}'`, and `configs/dataset/sod_shock_tube.yaml` is
  unchanged.

### What part is evaluated

The configuration's own window and grid (10 frames, 2048 cells), unchanged. The candidate only
replaces the ladder by one forecast row per frame, which costs one more exact evaluation per
frame, 0.3 ms. Measured run: see the log entry below.

### Log entries

**2026-11-27, agent (build-order step 7).**

- Code: `time_offset` and `candidate` on `SodShockTube` in `fmeval/data/analytic.py`; a section
  "The exact solution at a shifted time" on the page.
- Tests in `tests/test_analytic_datasets.py`: at $\delta t = 0.001$, 0.003 and 0.01 (3.6, 10.8 and
  35.9 cells) and four times each, through `fmeval.pipeline.run`, `shock_set_distance` equals
  $(s - \tfrac12)\Delta x$ and `shock_set_hausdorff` $s\Delta x$ to 1e-12, with $s$ the whole-cell
  move of the flagged pair and $|s\Delta x - S_R\,\delta t| \le \Delta x$; `max_error` equals
  $p_* - p_R$ in pressure and $u_*$ in velocity to 1e-12 at every offset (the fan differs by at
  most 0.101 and 0.089, measured); four refusal cases.
- Smoke run: `python evaluate.py dataset=sod_shock_tube 'metrics=[max_error,<the six shock
  metrics>]' '+dataset.reader.candidate={time_offset:0.01}'`, 3.4 s wall, results under
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/blast_waves/runs/comparison_1795772808`:
  `shock_set_distance` 0.01685 to 0.01733 against $S_R\,\delta t = 0.01752$; `max_error` 0.20313
  (pressure), 0.92745 (velocity) and 0.16075 (density, the contact's jump) in every frame.
- Not verified: a Rankine–Hugoniot residual metric (issue 051) does not exist, so "the jumps are
  unchanged" is read through `max_error`, not through a residual.

### Open points

- No evidence run with the shifted-time candidate has been made for the shock cards yet. The
  experiment proposal it came from was deleted on 2026-11-27, since this option builds all of it.

## `kinet_sod_refinement` (kinet's tube on three grids against the exact solution, 2026-11-27)

### What it is for

The solver's error against the exact Riemann solution on a grid sequence, with its observed order
(`dataset_specs/02_grid_refinement_known_solution.md`, Sect. 5.2; build-order step 17). It is the
shock case of the grid sequences: an error concentrated at discontinuities, whose order is below
one, beside the smooth Taylor–Green sequences of order two.

### How it is treated

- **Source.** Three kinet runs made on 2026-11-27 by the job agent (case `sod/transonic` on
  `[N, 5]`, `N` = 751, 1501, 3001; 250, 500, 1000 steps saved every 1, 2, 4 steps; dynamic
  viscosity $2.5 \times 10^{-5}$, $5 \times 10^{-5}$, $10^{-4}$; kinet `perf/cleanup` at
  `d1cd353b8`, one A100 per job). Configurations, provenance, commands and jobs:
  `docs/datasets/logs/kinet_runs/kinet_sod_refinement/` and that README's section "Runs of the
  second batch".
- **Conversion.** `python -m fmeval.data.convert_kinet <rollout.h5> <dest>` from
  `/pscratch/sd/k/khegazy/kinet_datasets/sod_refinement/sod/transonic/{aee3fbb1,dd337542,d1cac664}/tiers/full/rollout.h5`
  to `/global/cfs/cdirs/m4790/Data/kinet/sod/compressible_fluids/Pr-71en2_vuy-1.4_refinement/N751.h5`,
  `N1501.h5`, `N3001.h5` (30.3, 60.4 and 120.6 MB; under a second each). The converter dropped
  step 1 of the two finer runs, which kinet saves whatever the cadence, so each file holds 251
  evenly spaced frames. Each was read back with `KinetRawTrajectory` and found equal to its source
  at every frame and on its clock (`time_convection`, step × 0.6831 / N). Fields: density,
  velocity and the absolute pressure (`pressure_convention: absolute`).
- **Reader.** A registered format, `sod_kinet` (`SodKinet` in `fmeval/data/analytic.py`, a
  subclass of `SodShockTube`, about 50 lines), in the Taylor–Green pattern: the exact solution
  on the run's cells and clock, the run from `predictions()`. It reads the run's states and
  $\gamma$ from the file, checks that the initial density is one jump at the face $(N-1)/2$, and
  reads the run with a new `kinet_raw` option `cell` (about 8 lines) set to $1/(N-1)$.
- **Units.** With `cell = 1/(N-1)`, a cell and a solver step both last $1/(N-1)$: spacing and clock
  rescale, velocity, density and pressure keep their lattice values, and the clock is the solver
  step (`time_index`) over $N - 1$. The diaphragm is at 0.5, cell centres at
  $(i + \tfrac12)/(N-1)$, frame $k$ at $t = k/750$ on every grid (bitwise equal clocks, checked),
  and the coarse cells are unions of two fine ones. The physical viscosity is then the same on
  every grid, $\nu_\text{lattice}/(N-1) = 3.3 \times 10^{-8}$.
- **Grid and boundaries.** $N \times 5$, `neumann` along the tube (kinet's `neuman` faces), periodic
  across it (no face named; every field uniform across it), as in `_kinet_sod.yaml`.

### What part is evaluated

- **Kept:** all three grids at native resolution (an order needs each run on its own cells), at
  frames 175, 200, 225, 250 (`time: {start: 175, reduction: 25}`): $t = 0.233$ to $0.333$, steps
  700 to 1000 of the 3001-node run, the times spec 02 names (its 850 is not a saved step of the
  coarsest grid; 800 and 900 are).
- **Why these.** The rows are a deterministic error, not samples, so a few times suffice to show
  whether the order holds. Before frame 100 the per-time L1 orders scatter (density 0.09 to
  0.74, velocity 0.43 to 1.09, pressure −0.5 to 0.84; cause not diagnosed); from frame 100 to 250
  they are steady (density 0.65 to 0.69, pressure 0.76 to 0.83, velocity 0.69 to 0.94), and the
  kept four lie in that stretch (measured with `mae` on every frame, 2026-11-27).
- **No analysis grid, exclusion or slow metric.** A remap would add an error of its own; with a
  candidate the ladder is replaced except the clean entry and `mean_field`; the persistence
  metrics are cheap here.
- **Measured cost** (login node, 2026-11-27, `evaluate.py` per grid on the kept four frames):
  the 29 deterministic metrics other than the two persistence ones, of which 15 run on a
  non-periodic domain, 4.7 to 4.8 s wall per grid (0.1 s of metric time);
  `persistence_distance` and `persistence_wasserstein` 2.7 s (751) and 3.2 s (3001) wall. The
  whole panel on the sequence is under half a minute. Disk 211 MB, all read.
- **What the panel shows** (that run): `shock_set_distance` is 0 or half a cell
  ($6.7 \times 10^{-4}$, $3.3 \times 10^{-4}$, $1.7 \times 10^{-4}$), so the solver's shock lies
  within a cell of the exact one on every grid; `max_error` does not fall with the grid (density
  0.082 to 0.089 on all three), the pointwise error at a smeared jump.

### Decisions and why

1. **Beside `kinet_sod_gamma1p4`, not replacing it** (agent). That configuration is a
   reference for the ladder (the solver's field degraded), and this one a candidate against the
   exact solution with no ladder: two experiments. `d17baf` is also a different run (its jump is
   one face to the right and its later frames differ). To reverse: delete this configuration.
2. **Units of $N - 1$ cells, through a `cell` option on `kinet_raw`** (agent). The job agent's
   units (tube length $N$ cells) put the levels' frames at times differing by $10^{-3}$
   (250/751 against 500/1501), and `observed_order` pairs grids only at equal times. In units of
   $N - 1$ cells the same frames share one time exactly, the diaphragm is at the exact reader's
   0.5, and the grids nest. The errors are the same numbers in either units (each is the run
   against the exact solution at its own step); only the time label differs. `box`, the
   Taylor–Green option, could not serve: it needs the run's reference length and speed, which a
   Sod rollout does not record (`normalization_plan.lattice` is empty). Alternatives: match times
   with a tolerance in `observed_order` (a change to the analysis's pairing rule for every
   sequence), or relabel the run's private clock inside the reader (reaching into another
   class's state). To reverse: delete `cell` and `SodKinet`.
3. **The diaphragm is read from the stored initial density, not stated in the config**
   (agent). It is exact, needs no second statement of a value the file holds, and refuses a run
   painted otherwise.
4. **`param_resolution` is $N$, so `observed_order` uses $r = N_f/N_c$ = 1.9987 and 1.9993**,
   as the job's table does, while the cell ratio in these units is exactly 2. The order is then
   0.1% larger than with $r = 2$ (my arithmetic, $\ln 2/\ln 1.9987$); not corrected, because a
   row's resolution is its cell count everywhere else.
5. **Registered as a grid sequence** (agent), as the Taylor–Green sequences are
   (`docs/decisions.md`): its frames are not scalar multiples of one another, and its claim is
   the error's fall across grids. Label in `configs/cards/default.yaml`.

### Log entries

**2026-11-27, dataset agent (batch 2, build-order step 17).**

- Converted the three runs (above) and checked every frame against the source.
- Code: `cell` and `candidate` options and `predictions()`/`frame_columns()` on
  `KinetRawTrajectory`; `Trajectory._candidate_columns`, now shared by `ClosedFormTrajectory`;
  `SodKinet`. Config `kinet_sod_refinement`; page section "The kinet grid sequence against the
  exact solution".
- Verified: the job's L1 and L2 per field at every saved frame of every level
  (`_scripts_batch2/sod_refinement_errors.json`) reproduced by the reader to $2 \times 10^{-13}$,
  and through the pipeline at the kept frames to 1e-9 (a `data` test); the orders through
  `observed_order` at the kept frames: `mae` density 0.664 to 0.679, pressure 0.779 to 0.825,
  velocity 0.717 to 0.931; `rmse` density 0.323 to 0.404, pressure 0.563 to 0.711, velocity 0.078
  to 0.912; at step 1000 they equal the job's (`mae` density 0.676 and 0.668, `rmse` 0.383 and
  0.323). A synthetic test checks the cells, clock, diaphragm and Toro's star state on frozen
  41- and 81-node runs, and three refusals.
- Smoke runs under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/batch2_smoke`.
- Not verified: the Banks, Aslam and Rider (2008) rate quoted on the page was recalled, not read.

### Open points

- The L2 order of velocity scatters (0.08 to 0.91 at the kept times); not diagnosed.
- No dynamics figure.

## `kinet_oblique_riemann_30deg` and `kinet_oblique_riemann_45deg` (the tube rotated in a square, 2026-11-27)

### What they are for

Straight shocks, contacts and rarefactions oblique to the grid, run by a solver and scored against
their exact solution, so that the shock-set metrics, whose detector takes jumps along each grid
axis, meet an oblique front with a known answer (`dataset_specs/03_two_dimensional_shocks.md`,
Sect. 4.1; `proposals/EXP-shock_set_distance-2d-shock-dataset.md`, which this narrowed; build-order
step 18). Two grids give an observed order.

### How they are treated

- **Source.** kinet's case `oblique_riemann/default`, run on 2026-11-27 by the job agent with its
  finite-volume PonD solver (kinet `perf/cleanup` at `d1cd353b83e9`, one A100), normal
  $(\cos 30°, \sin 30°)$ (the case's default) and $(1, 1)$, on $200^2$ (job 62114361) and $400^2$
  (job 62108197), to $t = 0.2$. Records and the job's checks: `docs/datasets/logs/kinet_runs/shocks_2d/`.
- **Conversion.** `convert_kinet_grouped(<rollout>, <dest>, every)` to
  `/global/cfs/cdirs/m4790/Data/kinet/oblique_riemann/compressible_fluids/Pr-71en2_vuy-1.4_visc-1en5_normal-30deg/N200.h5`
  (`b5150399`, 2.6 MB), `N400.h5` (`024f7fdf`, 10.3 MB), with `every=21`, and
  `.../normal-45deg/N200.h5` (`5d9db066`, 2.6 MB), `N400.h5` (`83a3bce9`, 10.3 MB), with `every=19`:
  the initial condition and $t = 0.2$ (25.8 MB). Clock `time/time`, the case's time (the converter's
  adaptive-run rule, `docs/datasets/logs/isentropic_vortex.md`). Each checked equal to its source.
- **Reader.** `sod_kinet` with a new option `normal` (about 25 changed lines in `SodKinet`): the
  states are read from the run's two extreme cells along the normal, the uncut cells of the
  initial condition must hold them on the right sides of the line (kinet paints the cut cells with
  each state's share), the solution is the tube's at $s = \boldsymbol n \cdot (\boldsymbol x -
  (\tfrac12, \tfrac12))$ with velocity $u\,\boldsymbol n$, and the run is read through a window
  computed from the solution's fastest signal (below). The tube's path is unchanged: its
  coordinate along $(1, 0)$ is $x$ itself, bitwise, and its `data` test still reproduces the job's
  errors to 1e-9. These are Sod's states with both pressures times 0.15, an exact rescaling of
  Sod's problem, and a rotation of it, so they belong on the Sod page and need no second solver.
- **Window and boundaries.** Cells farther than $(u^* + c^*_R)\,t_\text{end} = 0.849 \times 0.2$
  from every face: 34 to 165 of 200, 68 to 331 of 400, on both axes; every face `neumann`, which
  in the window is no boundary of the flow.

### What part is evaluated

- **Kept:** $t = 0.2$, the last frame, of each run at its native resolution in the window.
- **Why.** The waves are widest apart then, so the most cells lie in the star regions and the
  fronts are longest in the window; and with the adaptive step it is the only time after the start
  the two grids share (issue 149). The rows are a deterministic error.
- **Measured cost** (login node, 2026-11-27): `rmse`, `mae`, `max_error`, `shock_set_distance`
  3.0 to 3.1 s wall per run; every deterministic metric but `persistence_wasserstein`, 16 of which
  run on these fields on this non-periodic grid, 5.0 s ($200^2$) and 5.5 s ($400^2$) wall, 0.5 s of it metric time
  (`persistence_distance` 0.45 s); `persistence_wasserstein` 0.4 s of metric time (2.7 s wall) on
  $400^2$. Disk 25.8 MB, all read.

### Decisions and why

1. **On the Sod page, through the Sod reader** (agent): the same problem rotated and rescaled
   (above). Alternative: a page of its own for two-dimensional Riemann problems, for when the
   four-quadrant configurations exist. To reverse: move the section and the configs' family.
2. **The window from the domain of dependence, computed by the reader** (agent). A margin in the
   config would be a number to keep in step with the states and the end time, and in cells it
   would differ between the two grids of one configuration. Measured on the $45°$, $200^2$ run, the
   rms pressure error rises only within 0.05 of the faces ($1.4 \times 10^{-3}$, against 0.8 to
   $1.0 \times 10^{-3}$ elsewhere outside the waves' band), so the margin of 0.17 is conservative.
   The job's interior box, margin 0.2, lies inside it. To reverse: pass `window` to `SodKinet`.
3. **`param_resolution` is the run's whole grid**, 200 or 400, not the window's 132 or 264, so the
   rows name the run; the ratio is 2 either way.
4. **One time per run** (agent; issue 149), as for the vortex sequences.
5. **No ladder dataset of these runs** (agent). The shock-set metrics' known answer here is the
   exact front; a ladder on the run would repeat what `kinet_supersonic_cylinder` and
   `kinet_double_mach_reflection` already give on solver shocks. To add one: a `kinet_raw` config
   of a converted file with `window` and `boundary: [neumann, neumann]`.

### Log entries

**2026-11-27, dataset agent (build-order step 18).**

- Converted the four runs, checked each against its source.
- Code: `normal` on `SodKinet`, with `frame_columns`; fixture `write_kinet_oblique_riemann`; tests
  `test_a_kinet_oblique_run_is_read_along_its_normal_in_a_window_clear_of_the_faces`,
  `test_a_kinet_oblique_pairing_refuses_another_run` and the `data` test
  `test_the_kinet_oblique_pairing_reproduces_the_jobs_interior_errors`.
- Verified: on the job's interior box the run minus the reader's solution has the job's rms and
  maximum errors of density and pressure at $t = 0.2$ on all four runs to four digits (45°,
  $200^2$: density rms $1.058 \times 10^{-2}$, max $7.901 \times 10^{-2}$; pressure $1.198 \times
  10^{-3}$, $6.398 \times 10^{-3}$); the reader's star state is the job's ($p^* = 0.0454695$,
  $u^* = 0.359201$). Through `evaluate.py` and `observed_order` (runs under
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/shocks2d_oblique_*`), 30°: `mae`
  density 0.61, pressure 0.78, velocity 0.84, `rmse` 0.32, 0.54, 0.46, `shock_set_distance` 0.96;
  45°: `mae` 0.59, 0.74, 0.66, `rmse` 0.28, 0.36, −0.22, `shock_set_distance` undefined (0 on
  $200^2$, the detector flagging the same 187 cells in both); `max_error` does not fall.
- Not verified: why the 45° velocity `rmse` rises from $200^2$ to $400^2$ ($6.4 \times 10^{-3}$ to
  $7.4 \times 10^{-3}$) while its `mae` falls.

### Open points

- Only $t = 0.2$ is evaluated (issue 149); the raw runs are on scratch until it is purged, about
  eight weeks after 2026-11-27, and are reproducible from the archived configurations.
- No dynamics figure: each configuration evaluates one frame per run.
