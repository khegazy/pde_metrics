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

Spec 03, Sect. 3.6 and `proposals/EXP-sod_evidence-sod-time-offset.md` ask for the exact solution
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

- The proposal `proposals/EXP-sod_evidence-sod-time-offset.md` is now built as a reader option; it
  is left in place for the coordinator to delete or narrow.
