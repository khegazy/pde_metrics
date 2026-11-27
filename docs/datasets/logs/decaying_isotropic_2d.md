# Log: decaying two-dimensional isotropic turbulence

This log records why the dataset on [`decaying_isotropic_2d.md`](../decaying_isotropic_2d.md)
is in its current form. It follows step 7 of `docs/recipes/add-a-dataset.md`. Append new
entries at the end, and never rewrite an old one; supersede it with a new entry instead.

Where a decision is attributed to Kareem, the source is a dated decision in
`dataset_specs/BUILD_ORDER.md`. Where it is attributed to an agent, no person reviewed it
before it was carried out.

## 1. What the dataset is for

- **Unrelated realisations.** Every metric's damage anchor needs fields from the same physics
  that share no initial condition with the reference. These runs each start from their own
  seed, so any two of them are such a pair (`dataset_specs/01_physical_ensemble.md`, Option C).
- **A reference set of many initial conditions.** Specification 05 uses these runs as the
  references against which degraded solver runs are scored
  (`dataset_specs/05_initial_conditions_and_degraded_solver_runs.md`, Sect. 4.1, Option B).
- **The starting fields for later steps.** Step 20 of `BUILD_ORDER.md` (the coarse-grid,
  wrong-viscosity and plain-BGK candidates), step 22 (forced turbulence) and step 25 (the
  OpenFOAM candidate) start from the step-0 fields of these runs.
- The work is step 2 of `dataset_specs/BUILD_ORDER.md`, which depends on the converter built in
  step 1.

## 2. How it is treated

- **Source.** The archive is `/global/cfs/cdirs/m4790/Data/neurde/hit_scaling/Re-{12p5k,25k,50k}_Ma-1en1_2d/<key>/`.
  It holds decaying 2D isotropic turbulence from kinet: D2Q9 lattice, entropic BGK collision,
  Mach 0.1, the random-mode initial condition with `k0: 4`, doubly periodic, and one seed per
  run (recorded in each run's `config.yaml`). It was produced on 2026-11-06 to 11-08 from the
  kinet branch `changes_while_running_hit` (`dataset_specs/00_how_to_use_kinet.md`, Section 6c).
  - At Re 12.5k and 25k, a run is 10 000 steps on $256^2$ cells, saved every tenth step, in
    `tiers/full/rollout.h5`.
  - At Re 50k, a run is 20 000 steps on $512^2$ cells. It is archived coarse-grained by two in
    space and in time, in `tiers/256/rollout.h5`, with the root attribute `time_stride: 2`. Its
    step counter counts the coarse-grained steps, so it reads 1, 10, ..., 10000, and its clock
    `time_convection` equals the clock of the other two Reynolds numbers frame for frame.
- **Conversion.** `python -m fmeval.data.convert_kinet SRC DST` (`fmeval/data/convert_kinet.py`,
  step 1) rewrites kinet's grouped layout into the flat layout that the existing `kinet_raw`
  reader opens.
  - The initial condition, stored apart under `initial_conditions/`, becomes frame 0.
  - Only the time slots that were saved (the finite slots) are kept.
  - kinet always saves step 1, so the saved steps are 1, 10, 20, ..., 10000. Step 1 is dropped,
    so that the frames are evenly spaced at steps 0, 10, ..., 10000. The frame stride and
    `dataset.time.reduction` both assume even spacing. Any other uneven spacing is refused.
  - The clock is taken from `time/time_convection`, in units of domain crossings, which is the
    unit of the flat files' `time` dataset.
  - `discretization.temporal` is rewritten to count the frames written. Every root attribute is
    copied, including the identity key and `time_stride`. The step of each frame is written as
    `time_index`, and the source path as `converted_from`.
  - The output is written as `<file>.partial` and renamed only after `KinetRawTrajectory` has
    opened it. An existing file is never overwritten.
- **Reader and fields.** The reader is `kinet_raw` with no options. The fields kept are
  `density`, `velocity` and `vorticity`. Each file holds 1001 frames on $256^2$ cells, periodic
  on both axes, and is 2,099,513,720 bytes (2.10 GB). The part evaluated is set in section 3.
- **Location.** `/global/cfs/cdirs/m4790/Data/kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids/sys_Re-{12p5k,25k,50k}_Ma-1en1/<key>.h5`,
  reached as `${paths.data}/kinet/...`.
- **Configuration.**
  - The fragment `configs/dataset/_decaying_isotropic_2d.yaml` holds what every realisation
    shares: format, fields, family, Mach number, dimension, resolution and notes.
  - There is one option per Reynolds number: `kinet_hit_re12p5k`, `kinet_hit_re25k` and
    `kinet_hit_re50k`. Each states its name, its folder, its rank, its Reynolds number and its
    label. Its default trajectory is the first key drawn at that Reynolds number.
  - Any other realisation is chosen with `dataset.trajectory=<key>`.

## 3. What part is evaluated

This section follows step 3 of `docs/recipes/add-a-dataset.md`.

- **Who decided:** an agent, on 2026-11-26. Kareem's rule of the same day is that the agent
  adding a dataset makes this decision and records it, and that a person may override it.
- **Where it is set:** the `time` block of `configs/dataset/_decaying_isotropic_2d.yaml` and
  the comments in the three options.
- **Section numbers:** sections 4 to 6 of this log were numbered 3 to 5 before this section was
  added. A reference to "section 3" in an entry written before this one means section 4,
  "Decisions and why".

### What is kept

| Selector | Value | Effect |
|---|---|---|
| `dataset.time.start`, `stop` | 150, 600 | Frames 150 to 599, $t = 0.34$ to $1.35$ convective units, the same window at every Reynolds number |
| `dataset.time.reduction` | 25 | 18 frames per trajectory, 250 solver steps apart |
| Trajectories | The first five drawn at each Reynolds number | Swept with `-m dataset.trajectory=<k1>,...,<k5>`; the keys are listed in each option |
| `analysis_grid.resolution` | 128 | Passed on the command line, because it is a top-level key that a dataset config cannot set |

That is 270 evaluated frames over the three Reynolds numbers.

### Why this window

The flow passes through three stages. They were measured on the default trajectory of each
Reynolds number every 50 frames. The integral length is $\ell = L \langle k^{-1} \rangle_E$,
and the turnover time is $\ell / u_{\mathrm{rms}}$, as in spec 05, Sect. 4.1.

1. **Frames 0 to 149: the initial transient. Dropped.**
   - Frame 0 is kinet's random-phase field. It holds no enstrophy above $|k| = 32$ (a fraction
     of $10^{-28}$).
   - The small scales form within about one initial turnover time, which is 115, 127 and
     123 frames at Re 1.25e4, 2.5e4 and 5e4. By frame 150 the enstrophy fraction above
     $|k| = 32$ has reached 0.03 to 0.05. kinet's start-up transient also falls in these
     frames.
   - A random-phase field is close to what the Gaussian impostor imitates, so the canary is
     degenerate there (agent's reasoning, not measured).
2. **Frames 150 to 599: developed decaying turbulence. Kept.**
   - The energy peak moves from $|k| = 4$ towards the box scale.
   - The enstrophy fraction above $|k| = 32$ is at its largest: 0.02 to 0.04 at Re 1.25e4,
     0.05 to 0.07 at Re 2.5e4, and 0.05 to 0.09 at Re 5e4.
   - The turnover time is 170 to 300 frames.
3. **Frames 600 to 1000: a box-scale condensate. Dropped.**
   - The energy peak sits at $|k| = 1$. It stays there from frame 350 at Re 1.25e4 and from
     frame 650 at the other two.
   - The integral length approaches its limit: $\ell / L$ is 0.79 to 0.85 at Re 1.25e4 between
     frames 600 and 1000.
   - The turnover time grows to 270 to 400 frames. The state evolves slowly, so the stretch adds
     few independent states.
   - It also probes a condensate rather than turbulence (spec 05, Sect. 4.1). It remains
     readable with `dataset.time.start=600 dataset.time.stop=null`.

The window is the same at all three Reynolds numbers, so frame $i$ is the same physical time
on every option. This holds although the condensate forms earlier at Re 1.25e4.

### Why this stride

**Method.** I ran `mse` on every frame (reduction 1) of the default trajectory of each Reynolds
number at the 128 grid (the "pilot runs"). From those results I computed the integrated
autocorrelation time of mse's paired step between adjacent severity levels.

- The step is computed on the frame-scaled trace, exactly as M3 of
  `METRIC_EVALUATION_CRITIQUE.md` (finding 2) did, with a Bartlett lag window.
- I also computed the harness's Politis–White block length
  (`fmeval.stats.politis_white_block_length`).
- Each value below is the median over field and axis.

| Window | $\tau$, Bartlett window of 30 frames | $\tau$, Bartlett window of 100 frames | Politis–White block |
|---|---|---|---|
| 0 to 149 | 23.5 to 24.3 | 34.2 to 36.4 | 21 |
| 150 to 599 | 25.9 to 27.7 | 57.0 to 70.2 | 41 |
| 600 to 1000 | 24.2 to 26.8 | 57.1 to 67.6 | 38 to 39 |

**Reading.**

- $\tau$ grows with the lag window, from 30 to 100 frames. So the dependence is longer than
  30 frames, as M3 also found on `kinet_re5e4`.
- Inside the kept window I take $\tau \approx 41$ to $70$ frames. So one trajectory's
  450 frames hold about 450/70 to 450/41, that is 6 to 11, independent samples.

**Choice.** A stride of 25 frames is about half of $\tau$. It keeps those samples at 18 frames
per run.

- A stride of 50 would keep nearly as many independent samples, at half the cost.
- But it would leave 9 frames per run. Each run is analysed alone, and its block bootstrap and
  per-frame medians need more frames than that.

### Why five trajectories

Independent realisations are independent samples outright.

- **Five per Reynolds number** give about 32 to 55 independent samples per Reynolds number, and
  96 to 165 over the three. For comparison, the 161 frames of `kinet_re5e4`'s default window
  hold 7 to 12.
- **Ten per Reynolds number** would double the cost and shrink the standard error of a median
  only by about $\sqrt{2}$.
- The other five converted realisations per Reynolds number stay on disk. Later steps use them
  (step 20 starts its degraded runs from their step-0 fields), and they are spares.
- The harness has no pooling across trajectories (`fmeval.io.combine_runs` combines datasets or
  frame shards, not trajectories). So each trajectory is its own run folder, and pooling them is
  an open point.

### Why the 128 grid

**Fractions lost.** Measured at frames 150, 300, 450 and 600:

| Re | Enstrophy lost at 128 ($\lvert k \rvert > 64$) | Palinstrophy lost at 128 | Palinstrophy lost at 64 ($\lvert k \rvert > 32$) |
|---|---|---|---|
| 1.25e4 | at most 0.3% | 1 to 4% | 24 to 34% |
| 2.5e4 | at most 0.8% | 6 to 8% | 43 to 48% |
| 5e4 | at most 2% | 29 to 34% | 64 to 74% |

**Reasons.**

- The native grid costs three times as much (below).
- The 64 grid loses most of the gradient content.
- 128 is also the grid of the Reynolds-ladder family.

**Cost of the choice.** At Re 5e4, metrics built on gradients (`palinstrophy`, `h1_seminorm`,
`h1_relative`) see a field that is missing about a third of its palinstrophy. A run that
targets small scales at Re 5e4 should use the native grid. Note that the Re 5e4 tier is itself
a 2x coarse-graining of a $512^2$ run.

**Degenerate levels.** In the pilot runs at 128, these strengths changed nothing and the
pipeline excluded them:

- level 1 of `coarsen_bandlimited` on every field;
- level 1 of `box_blur` and `median_blur` on vorticity;
- level 1 of `lowpass_ideal` on vorticity at Re 2.5e4 and 5e4.

### Measured cost

Everything was measured on the login node, in one process per run, on Re 5e4 frames 150, 300
and 450. The per-metric times are the sum of the `wall_time_s` column of `results.csv` divided
by the number of frames.

| What | At 128 | At 256 (native) |
|---|---|---|
| `mse` alone, whole run per frame (mostly the degradations) | 0.62 s | 2.1 s |
| Panel of the 24 metrics that run here, without `persistence_wasserstein`: metric time per frame | 34.1 s | 105 s |
| The same panel, whole run of 3 frames, including about 28 s of calibration and writing | 132 s | 392 s |
| `persistence_distance` (density and vorticity) per frame, in the panel run | 11.4 s | — |
| `energy_distance` per frame | 9.4 s | — |
| `spectral_energy_flux` per frame | 5.1 s | — |
| `wasserstein` (density) per frame, in the panel run | 2.1 s | — |
| `wasserstein` alone, per frame (another run was competing for the CPU) | 1.7 s | 6.3 s |
| `persistence_distance` alone, per frame (same competing run) | 9.0 s | 37 s |
| `persistence_wasserstein` per frame, from issue 144's per-comparison times × 182 comparisons per frame (not run here) | 33 to 530 s | 1000 to 4350 s |

The panel's 24 metrics are every registered metric except the ensemble metrics, the
shock-set metrics that need an absolute pressure, and `persistence_wasserstein`. At the 64 grid,
`persistence_wasserstein` would cost 2.7 to 14 s per frame.

### Projected panel time and disk

**Time, in one process:**

- **The kept part at 128:** 270 frames × 34 s, plus 15 runs × about 30 s of overhead, is about
  2.7 h.
- **Adding `persistence_wasserstein`:** 2.5 to 40 h at 128, or 0.2 to 1.1 h at 64, which is
  issue 144's first option.
- **Comparisons:**
  - the same frames on the native grid: about 8 h;
  - all 1001 frames of all 30 converted trajectories at 128: about 280 h.
- **Spreading the load:** `dataset.time.shards` and the trajectory sweep split the work over
  processes. The login node allows 32 cores per user.

**Disk:**

- The kept part reads 270 frames of about 2.1 MB each, about 0.6 GB, from 15 files of 2.10 GB
  (31.5 GB).
- All 31 converted files, 65.1 GB, stay. Nothing was deleted.
- Converting more than the 30 is not worthwhile for evaluation, since only 5 of the 10 per
  Reynolds number are evaluated. It becomes worthwhile only if a later step needs more starting
  fields, or if pooled statistics across many trajectories are built.

### Why this balance

- The kept part costs about as much as the existing evidence run on `kinet_re5e4`, which is
  161 frames per run.
- It gives about ten times as many independent samples per Reynolds number.
- Doubling the trajectories, halving the stride, or using the native grid would each double or
  triple the time for little gain in precision.
- Halving the stride the other way, to 50, would save half the time but leave too few frames
  per run.

## 4. Decisions and why

### Use the existing reader and convert the data to fit it

- **Who:** Kareem, 2026-11-26 (`BUILD_ORDER.md`, Decisions, item 1, and "How data reaches the
  metrics").
- **Why:** no new reader is written for kinet output. The grouped files are rewritten into the
  flat layout that `kinet_raw` already reads for the shear-layer data.
- **Alternatives:** a new reader for the grouped layout, or the virtual-dataset route in the
  last decision of this section.
- **Reversal:** add a grouped-layout reader in `fmeval/data/` and point the configs at the
  archive. The converted files would then be redundant.

### Drop step 1 when it breaks even spacing

- **Who:** the step-1 agent, while building the converter.
- **Why:** frame selection by stride or reduction assumes evenly spaced frames. Step 1 is the
  only saved step off the ten-step cadence.
- **Alternative:** keep step 1 and refuse strides. That would break `dataset.time.reduction` on
  every file.
- **Reversal:** remove the `np.delete(frame_step, 1)` branch in `convert_kinet.py` and
  reconvert.

### Do not convert the gauge pressure

- **Who:** the converter's rule comes from the plan (`BUILD_ORDER.md`, step 1: "The weakly
  compressible gauge pressure is not carried over (it is not absolute, issue 101)") and from the
  project's rule that pressure is never computed or faked. The step-1 agent implemented it.
- **Why:** this solver stores $(\rho - 1) c_s^2$ (`00_how_to_use_kinet.md`, "Verified by
  running"). That carries no information beyond the density, and it is not an absolute
  pressure, so a pressure metric would read a wrong quantity from it.
- **How it is enforced:** the converter carries `pressure` only when the root attribute
  `pressure_convention` is `"absolute"`.
- **Alternative:** convert it and leave it out of `fields`. That would store about 0.5 GB per
  file for nothing.
- **Reversal:** reconvert with that condition removed and add `pressure` to `fields`. This is
  not advisable.

### Convert 10 runs per Reynolds number first

- **Who:** proposed by the agent that wrote specification 05, which calls it "my choice"
  (Sect. 4.1). It was carried into `BUILD_ORDER.md` step 2 as "30 trajectories first (about
  63 GB)", and the coordinator assigned that step.
- **Why:** it keeps the first pass cheap. All 100 runs can be scored, because no candidate is
  fitted to data, so nothing is held out.
- **Alternative:** convert all 300 runs, about 630 GB.
- **Reversal:** convert more runs with the same command. The draw rule below extends naturally:
  take further entries of the same permutation.

### The draw and its seed

- **Who:** an agent (this step). The coordinator said to use seed 0 unless the repository had a
  convention. No convention exists for drawing subsets: the repository's `seed: 20260807` in
  `configs/config.yaml` seeds evaluation runs, not data selection.
- **Rule:** for each Reynolds number, sort the complete keys alphabetically and take the first
  ten entries of `numpy.random.default_rng(0).permutation(100)` (NumPy 2.5.1).
  - The same ten positions are therefore drawn at each Reynolds number. The runs at different
    Reynolds numbers are unrelated, so this correlates nothing.
  - The drawn keys, in order, are listed on the dataset page.
- **Alternative:** a different seed for each Reynolds number. It was not needed, for the reason
  above.
- **Reversal:** draw again and convert the new keys. The existing files do no harm where they
  are.

### Leave out the long runs and the non-run folders

- **Who:** the plan and specification 05 (Sect. 4.1) keep the long runs aside, for the
  invariant measure (issue 080). The agent applied the rule.
- **How the runs were identified:** a run counted as complete when `kinet_rollout_status ==
  "complete"`, `discretization.temporal.grid == 10000` and 1001 steps were saved. Exactly 100
  runs at each Reynolds number qualified.
- **What was left out:**
  - the long 100 000-step runs, `6f5a2b` (Re 12.5k), `bd2304` (Re 25k) and `bea170` (Re 50k),
    each with 10 001 saved steps;
  - the folders `visualization` (every Reynolds number) and `256_simulation` (Re 50k). Neither
    is a run folder: `256_simulation` holds its own run folders, 377 GB, which were not
    examined.
- **Reversal:** a long run converts with the same command into the same folder. Its 10 001
  frames span ten times the time, so it needs its own config, or a documented trajectory
  override, before frame indices mean the same as in the short runs.

### Folder names

- **Who:** an agent. The step-1 agent named `sys_Re-25k_Ma-1en1`, after the example in
  `BUILD_ORDER.md`. This step followed it with `sys_Re-12p5k_Ma-1en1` and
  `sys_Re-50k_Ma-1en1`, which use the archive's spelling.
- **Alternative:** the shear-layer spelling `sys_Re-5e4_Ma-1en1`. It was not chosen because the
  converted 25k folder and the data test already used `25k`.
- **Reversal:** move the folders and edit the three `path` lines and `HIT_RAW` in
  `tests/test_loader_contract.py`.

### Configuration pattern: one fragment and one option per Reynolds number

- **Who:** an agent. The coordinator asked for the least configuration that the existing code
  supports with no code change.
- **Why it is the least configuration:**
  - The path already ends in `${.trajectory}`, so any realisation is one command-line override.
    Thirty near-identical files are not needed.
  - The family mechanism (`configs/dataset_family/`) sweeps over whole dataset configs, not
    over trajectories. Using it would need one file per realisation.
  - Each Reynolds number needs its own option, because its folder name, rank and label differ.
    The folder name cannot be derived from `complexity.params.reynolds` without a new resolver.
- **Detail:** the default trajectory of each option is the first key drawn at that Reynolds
  number. A key made only of digits, such as `137164`, reads correctly from the command line,
  because the schema types `trajectory` as a string. A key that the override parser would read
  as a float in exponent form, such as `12e345`, would need quoting. None of the drawn keys
  has that form.
- **Alternatives:** one file per realisation, or one family file sweeping them.
- **Reversal:** add per-realisation files that inherit the fragment.

### Delete the step-1 config `kinet_hit_re25k_004ae2`

- **Who:** an agent, as the coordinator directed ("keep or fold ... so there is one source of
  truth").
- **Why:** `kinet_hit_re25k` with `dataset.trajectory=004ae2` reads the same file. Keeping both
  would define the 25k path twice. No test named the config; the data test names the file
  path.
- **Reversal:** restore the file from the step-1 working tree. It was never committed.

### Keep `004ae2` although it was not drawn

- **Who:** the coordinator's instruction, carried out by an agent.
- **Why:** it is the converter's verified test file. The data-marked test
  `test_a_converted_isotropic_rollout_matches_its_grouped_source` compares every one of its
  frames with the source. It is not part of the subset of ten.

### Write smoke-run results to scratch

- **Who:** the coordinator, because the home quota was at 92.5%.
- **What:** the smoke runs wrote to `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets`
  through `paths.results=...`, and Hydra's bookkeeping went to `results/.hydra` under that
  directory. Nothing was written into the repository's `results/`.
- **Caveat:** scratch is purged, so those folders are not durable records.

### Leave 270 runs unconverted, and the virtual-dataset alternative

- **Who:** the plan, through "30 trajectories first".
- **What remains:** 90 complete runs per Reynolds number, about 567 GB if converted the same
  way.
- **Alternative, not tried (agent's reasoning):** an HDF5 virtual dataset (h5py's
  `VirtualLayout`) could present each grouped file in the flat layout without copying it.
  - It would need one small flat file per run, holding `time`, `time_index`, the copied
    attributes, and virtual `density`, `velocity` and `vorticity` datasets.
  - Each of those datasets would map frame 0 to `initial_conditions/observables/<field>` and
    frames 1 to 1000 to every tenth slot of `observables/<field>`, a strided hyperslab, which
    virtual datasets support.
- **What it would save:** the 2.1 GB copy per run.
- **What it would cost:**
  - New code: a second writer in `convert_kinet.py`.
  - A dependency on the archive staying where it is, unchanged.
  - Uncertain reading through `paths.data_url` over HTTP, where the remote reader may not
    resolve the virtual sources.
  - Per-frame reads that cross two groups. Their read speed on CFS was not measured.
- **Reversal:** none needed. Either route produces files that the same reader opens.

## 5. Log entries

### 2026-11-26: step 1, the converter and `004ae2` (step-1 agent)

This entry is reconstructed from step 1's files and its line in `BUILD_ORDER.md`; that agent's
own report was not available to this log's author.

- **Built:** `fmeval/data/convert_kinet.py`, with contract and refusal tests in
  `tests/test_loader_contract.py` and a fixture in `tests/fixtures_h5.py`.
- **Converted:** Re 25k `004ae2` from `tiers/full/rollout.h5` into `sys_Re-25k_Ma-1en1/004ae2.h5`
  (2.10 GB).
- **Verified:** a data-marked test requires every frame and the clock to equal the grouped
  source exactly. The config `kinet_hit_re25k_004ae2` passed a smoke run.
- **Documented:** wrote the dataset page and its row in `docs/datasets/README.md`.
- **Not done:** the `forecast` half of the converter, for candidate pairs, was not built.

### 2026-11-26: step 2, the first 30 realisations (agent)

- **Scan:** read the archive's 307 folders and identified 100 complete 10 000-step runs per
  Reynolds number (section 3).
- **Draw:** drew 10 per Reynolds number with seed 0. `004ae2` was not drawn.
- **Conversion:** converted the 30 drawn runs one at a time on the login node with
  `python -m fmeval.data.convert_kinet`. That wrote 30 files of 2,099,513,720 bytes (63.0 GB) in
  156 s of conversion. Nothing was skipped, refused or overwritten, and no `.partial` file
  remains. CFS had about 9.3 TB free beforehand.
- **Verification:**
  - Every output was opened by `KinetRawTrajectory` before it was renamed (the converter's own
    check).
  - Separately, all 31 files were compared with their sources at frames 0, 1, 500 and 1000 and
    on the whole clock: there were 0 mismatches.
  - Every Re 50k file ends at time 2.2553 and carries `time_stride: 2`.
  - The data test for `004ae2` passes.
- **Configs:** added `_decaying_isotropic_2d.yaml`, `kinet_hit_re12p5k.yaml`,
  `kinet_hit_re25k.yaml` and `kinet_hit_re50k.yaml`, and deleted
  `kinet_hit_re25k_004ae2.yaml`.
- **Smoke runs:** `metrics=[mse]`, `dataset.time.reduction=100`,
  `analysis_grid.resolution=64`, on `3c2c65` (Re 12.5k), `49a8ad` (Re 25k) and `137164`
  (Re 50k). All three exited 0 with 11 of 1001 frames, and each run's recorded data source names
  the requested file. On vorticity, the mildest median-blur strength collapses to no change at
  Re 12.5k and 25k, and the two mildest do at Re 50k. The pipeline excludes those strengths and
  logs a warning.
- **Tests:** the default `pytest` gave 2725 passed, 397 skipped, 4 xfailed and 0 failed. Other
  agents' uncommitted edits were in the tree during that run.
- **Documentation:** updated the dataset page, the index row and the step 2 status.
- **Not verified:** every frame of the 30 new files (only four frames per file and the clock
  were compared), and whether the calibration table is sensible on these fields.

### 2026-11-26: step 1, its own account (step-1 agent)

The step-1 agent wrote this entry after the entries above. It supersedes the reconstructed step-1
entry and corrects section 3 where they differ. Nothing above was rewritten.

**Corrections.**

- **Folder name.** The destination `sys_Re-25k_Ma-1en1/004ae2.h5` was given to the step-1 agent
  in its brief by the coordinator, who took it from the example in `BUILD_ORDER.md`. The agent
  did not choose it. `004ae2` was converted because the brief named the first identity key in
  alphabetical order.
- **Step 1 is dropped only when that makes the spacing even.** The rule was not the step-1
  agent's own idea: `00_how_to_use_kinet.md`, Section 5, item 2, already prescribed it. The
  agent added the condition. A run saved at every step keeps step 1, because its spacing is
  already even.
- **The gauge pressure is dropped, not refused.** A file whose `pressure_convention` is
  `"fluctuation_referenced"` converts without `pressure`. What the converter refuses is a
  `pressure` whose convention is neither `"absolute"` nor `"fluctuation_referenced"`.
- **Where step 1's smoke runs went.** They were written to the repository's `results/` on home,
  as `results/mse_1795748272` (this dataset) and `results/mse_1795748287` (`kinet_re5e4_512`),
  about 2 MB each. The move to scratch described in section 3 came later.
- **How the code was shaped.** Mid-task, Kareem told the agent, through the coordinator, to use
  existing code wherever possible, to write as little new code as it could, to keep the
  converter to one function, and to extend the existing fixtures and contract tests rather than
  add parallel ones. The following choices follow from that:
  - The fixture `write_kinet_grouped` builds the grouped file from the frames of
    `write_kinet_raw`, so a correct conversion must give back the flat fixture exactly.
  - The converted file is one more entry, `kinet_grouped`, in the contract's `LAYOUTS`, so the
    whole reader contract runs on it.
  - Two contract tests now take the format name from `cls.FORMAT` instead of the layout key.

**Reasons that only step 1 knew.**

- **Why a tool and not a reader option.** Kareem ruled out a new reader (section 3, first
  decision). His mid-task instruction also asked whether a small configuration change could make
  `kinet_raw` read the grouped file, and the agent checked that it cannot:
  - `kinet_raw` reads a root dataset named `time`, but a grouped file has a group `time/`.
  - It reads fields at the root (`density`), but a grouped file keeps them under
    `observables/`.
  - It requires `temporal.grid + 1` frames, but a grouped file has `temporal.grid` slots, NaN in
    the unsaved ones, and the initial condition stored apart.

  None of the reader's constructor options changes any of this, so the agent decided on a
  standalone tool.
- **Why kinet's own grouped reader was not imported.** kinet is not installed in this
  repository's `.venv` (`import kinet` raises `ModuleNotFoundError`), and installing anything was
  forbidden. Its reader, `kinet/io/rollout/read/grouped.py`, also imports kinet's config,
  geometry and BP backend modules, so reaching it with a path hack would pull in much of kinet.
  `AGENTS.md` §9 also records that `import kinet` can pull in `mpi4py`, which fails on a login
  node. The agent did not test that for this submodule.
- **Why step 1 is dropped.** kinet always saves step 1 (`00_how_to_use_kinet.md`, "Verified by
  running", check 4). Kept, it gives frames at steps 0, 1, 10, 20, ..., which are unevenly
  spaced. `frame_stride` and `dataset.time.reduction` select every Nth frame, so with that frame
  included "every Nth frame" would not be every 10N steps, and the step-1 frame belongs to no
  cadence. Any other uneven spacing, such as a resume that changed the cadence, is refused,
  because no frame selection would then be uniform.
- **Why the file is validated through `KinetRawTrajectory` before the rename.** Opening the file
  with the reader reuses that reader's own checks: `temporal.grid + 1` equals the length of
  `time`, every field's frame count matches, and the channel counts are right. The converter
  therefore does not re-implement them. The rename is a separate safeguard. Every field dataset
  is allocated at full size before it is filled, and HDF5 returns zeros for chunks never
  written, so an interrupted write would otherwise leave a file that opens normally with
  zero-filled frames. Until the rename, the file is named `<name>.partial`, which no config
  points to, and a rerun refuses to overwrite it.
- **Why the gauge pressure is not converted.** kinet's
  `kinet/io/rollout/attrs.py` (`PRESSURE_CONVENTION_ATTR`) defines `"fluctuation_referenced"` as
  pressure with the lattice background $c_s^2 \rho_0$ subtracted. It notes that this background
  moves with grid resolution and is not archived. On this solver the stored field equals
  $(\rho - 1) c_s^2$, so it carries nothing that the density does not. The project's rule is that a
  dataset that does not store a quantity does not provide it, and pressure is never derived
  from density (`docs/recipes/add-a-dataset.md`, step 1). The agent added the refusal
  of an unknown convention so that a future convention is never guessed.
- **The virtual-dataset alternative.** The step-1 agent raised it in its report to the
  coordinator. It was not built, because the brief asked for a rewritten file chunked one frame
  per chunk, and because a virtual dataset cannot be read over HTTP from `paths.data_url`. That
  last point is the agent's reasoning and was not tested. No decision on it is recorded; it is
  for Kareem.

**What was done and measured.**

- **Conversion:** `004ae2` was converted on the login node in 3.7 s of wall-clock time, at a peak
  memory of 104 MB. The source had probably been cached by earlier reads. The output is
  2,099,513,720 bytes: 1001 frames, with `time` and `time_index` stored as contiguous 1-D
  datasets, `discretization.temporal` equal to `{grid: 1000, resolution: 10.0, length: 10000.0}`,
  and the clock running from 0 to 2.2552744890219754.
- **Verification:** the data-marked test compares every one of the 1001 frames of `density`,
  `velocity` and `vorticity`, and the clock, with the grouped source using `np.array_equal`. It
  passed, so the maximum difference is exactly 0.
- **Smoke run:** `kinet_hit_re25k_004ae2` at `dataset.time.reduction=100` and
  `analysis_grid.resolution=64` ran 11 frames in 9 s.
- **Tests:**
  - `pytest tests/test_loader_contract.py`: 72 passed.
  - Full default `pytest`: 2701 passed, 397 skipped, 4 xfailed, 0 failed.
  - `ruff check .`: clean.
- **Not verified:**
  - Reading a blosc2-compressed source. That needs `hdf5plugin`, which is not installed, and h5py
    would raise when reading such a file.
  - A source with more than one simulation on its leading axis. The converter copies the whole
    axis, but no test covers it.

### 2026-11-26: deciding what part is evaluated (agent)

This entry follows Kareem's new rule of 2026-11-26 that each dataset decides which part of it is
evaluated (recipe step 3). It supersedes the open point in section 6 that said no window had
been chosen.

**Measurements.** All ran on the login node, with results in
`/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets`.

- **Flow stages:** the energy spectrum, integral length, turnover time and the small-scale
  fractions of enstrophy and palinstrophy, measured every 50 frames on `c5ccb2`, `c95586` and
  `cf7333` with a scratch script (not in the repository).
- **Pilot runs:** `mse` on all 1001 frames of each of those trajectories at the 128 grid, run
  as three processes at once. The run folders are `mse_1795753771` (Re 2.5e4), `mse_1795753772`
  (Re 5e4) and `mse_1795753773` (Re 1.25e4). Each took 9.5 to 10.5 minutes, almost all of it
  in the degradations.
- **Autocorrelation:** computed from those results with a scratch script that follows M3 of
  `METRIC_EVALUATION_CRITIQUE.md`, together with `fmeval.stats.politis_white_block_length`.
- **Single-metric costs:** `wasserstein` and `persistence_distance` alone on Re 5e4, at 128 and
  at 256. These ran while the pilot runs were going, so they are slower than an idle node would
  give.
- **Panel costs:** the 24-metric panel on 3 frames of Re 5e4, at 128 (`comparison_1795754464`)
  and at 256 (`comparison_1795754603`), with nothing else running.

**Configuration changed.** The `time` block in `configs/dataset/_decaying_isotropic_2d.yaml`
is now `start: 150`, `stop: 600`, `reduction: 25`, with the reasoning in comments. Each of the
three options names its five evaluated keys and the sweep command. The resolved selection was
checked: the frames are 150, 175, ..., 575 on all three options.

**Log restructured.**

- Section 3 was inserted and the later sections renumbered (see section 3).
- The step-1 agent's own entry, which sat after the open points, was moved unchanged into
  section 5. Its text was checked to be byte-identical.
- In section 2, the sentence on the time selection now points to section 3.

**Not done.**

- No full panel was run on the kept part; the panel time is a projection.
- `persistence_wasserstein` was not run.
- The window was not checked on trajectories other than the three defaults. It assumes the
  stages fall at similar frames in every realisation, which the spec 05 table supports for the
  first run of each Reynolds number.

### 2026-11-27: registered as evidence (registration agent)

- **Registered:** `kinet_hit_re12p5k`, `kinet_hit_re25k` and `kinet_hit_re50k`, each `{periodic:
  true, ensemble: false}`, in `evidence_datasets` and `evidence_dataset_properties` of
  `configs/cards/default.yaml`. Kareem decided the rule on 2026-11-26
  (`dataset_specs/BUILD_ORDER.md`, "The task" and decision 9: every dataset built in that plan
  is an evaluation dataset, admitted to `evidence_datasets` with a label naming the kind of
  claim it supports); the agent chose the label.
- **Label** (completes "n frames of ..." in a card's run summary): `kinet_hit_re12p5k`:
  "decaying two-dimensional isotropic turbulence at Re = 1.25e4, one realisation per run";
  `kinet_hit_re25k`: "decaying two-dimensional isotropic turbulence at Re = 2.5e4, one
  realisation per run"; `kinet_hit_re50k`: "decaying two-dimensional isotropic turbulence at Re
  = 5e4, simulated on 512^2 cells and stored coarse-grained to 256^2, one realisation per run".
- **Window:** the configs' own `time:` selection, frames 150 to 599 every 25th (section 3).
  `evidence_window` is kinet_re5e4's single window and has no key per dataset, so the analysis
  grid of 128 and the five realisations per Reynolds number, which no config can state
  (`BUILD_ORDER.md`, framework limits 2 and 4), are listed in the comment beside
  `evidence_window` and stay command-line settings. The data-marked check that each reader is
  periodic and holds no members passed for all three.
- **Not done:** no metric was run on it for a card; every metric card's *Across the experiments*
  table shows it as *not yet run* or *not applicable* with the reason (`python -m fmeval.cards
  catalog`). Producing that evidence is its own step in `BUILD_ORDER.md` and needs compute.

### 2026-11-27: stride 50, the grid in the config, the trajectories pooled (step-32 agent)

- **What changed.** In `configs/dataset/_decaying_isotropic_2d.yaml`, `time.reduction` went from
  25 to 50: frames 150 to 550 every 50th, 9 frames per trajectory instead of 18. The 128
  analysis grid is now the fragment's own `analysis_resolution: 128`, a dataset key added by
  step 32, and no longer a command-line setting. The five trajectories per Reynolds number are
  still swept with `-m dataset.trajectory=...`, and their folders are now gathered by
  `fmeval.io.combine_runs(<folders>, stamp, across="trajectory")`, which the analysis reads as
  one sample of 45 frames per Reynolds number (`fmeval.analysis.pool_trajectories`): rank
  correlations within each frame, their median over all 45, and resampling blocks that never
  join two trajectories.
- **Why.** Kareem asked why the evidence needs so long. With pooling, the five independent
  realisations supply the samples, and a stride of 50 still keeps about one frame per
  autocorrelation time (57 to 70 frames, section 3), so halving the frames loses few
  independent samples. Nine frames alone would be too few for one trajectory's statistics,
  which is why section 3 kept 25 before pooling existed.
- **Who decided.** The coordinating session made the cut, recorded as decision 17 of
  `dataset_specs/BUILD_ORDER.md`; this agent applied it and built the pooling (step 32).
- **Cost.** About 34 s of metric time per frame at 128 without `persistence_wasserstein`
  (section 3), so the 135 frames of the three Reynolds numbers take about 1.3 h in one process
  (my arithmetic), against 2.7 h before.
- **Verified.** The configurations build with 9 selected frames (150, 200, ..., 550) and an
  analysis grid of 128 (`build_job`, reader opened on `kinet_hit_re25k`). The pooling is tested
  on synthetic rows and through `combine_runs` (`tests/test_analysis.py`,
  `tests/test_pipeline.py`). No metric was run on these data.
- **Supersedes** the stride of section 3, the command-line grid of the registration entry above,
  and the two open points on pooling and on the grid, rewritten below.

### 2026-11-27: where the runs' configurations are kept (dataset agent)

- The configuration and provenance of every converted realisation, the launch scripts and
  case files of the branch that made them, and the command that rebuilds each on the current
  kinet are in `docs/datasets/logs/kinet_runs/` (`kinet_hit_re12p5k/`, `kinet_hit_re25k/`,
  `kinet_hit_re50k/`, `kinet_hit_launch/`, and the README section "Decaying isotropic
  turbulence"), step 31 of `dataset_specs/BUILD_ORDER.md`. On the current kinet a rerun is a
  statistically equivalent realisation only, not a reproduction: the archived runs started from
  equilibrium populations, which the current case refuses (`dataset_specs/00_how_to_use_kinet.md`,
  Section 6c, corrected the same day).

### 2026-11-27: the degraded solver runs as candidates (step-20 dataset agent)

- **What was done.** The 105 kinet reruns of step 20 (`dataset_specs/BUILD_ORDER.md`) were made
  readable as predictions scored against the realisation each started from, through the
  existing `kinet_raw` option `candidate`. New: a converter option `every` (keep every Nth frame;
  `fmeval/data/convert_kinet.py`), a rule that scales a candidate's `cell` to its grid
  (`fmeval/data/kinet_raw.py`), the fragment `configs/dataset/_isotropic_candidates.yaml` and the
  options `kinet_hit_re12p5k_candidates`, `kinet_hit_re25k_candidates`,
  `kinet_hit_re50k_candidates`, registered as evidence. 90 reruns and 15 reference subsets were
  converted to CFS (3.51 GB), and the runs' provenance archived in
  `docs/datasets/logs/kinet_runs/isotropic_candidates/`. Section 7 holds the design, the evaluated
  part with its measured costs, the decisions and the open points.
- **Verified.** Every converted file equals its rollout at every kept frame and field, and every
  `reference.h5` equals the realisation's full file read with `frame_stride=50` (all 105 files).
  The candidates' clocks equal the realisations' bitwise on all three grids before conversion
  (checked on one realisation per Reynolds number). Through `evaluate.py` and in the data-marked
  test `test_the_isotropic_candidates_reproduce_the_jobs_distances`, the job's relative L2
  distances are reproduced: `nrmse` on vorticity and the velocity distance from `mse`, for
  `grid64`, `grid128`, `re0.5` and `bgk` at Re 2.5e4 and the 256^2 rerun at Re 5e4, on each
  candidate's own grid, agree with `candidates_checks.json` to 3.3e-5 relative at worst (the job
  printed five significant figures). The five realisations of one kind gather with
  `combine_runs(..., across="trajectory")`, and `make_report.py` renders the gathered folder.
- **Not verified.** Any metric beyond `mse`, `nrmse`, `rmse`, the 24-metric panel and
  `persistence_wasserstein`, which were run on one kind of one realisation for the cost; any
  kind at Re 1.25e4 through `evaluate.py` (the configuration composes and the files read; the
  job's checks cover the numbers).

## 6. Open points

- The other 270 complete runs are not converted. Section 4 gives the two routes for doing so.
- The evaluated part was chosen by an agent (section 3) and is open to a person's override.
  No metric has been run on it for a card yet.
- No `configs/dataset_family/decaying_isotropic_2d.yaml` exists. A sweep across the three
  Reynolds numbers would need one small file.
- No dynamics figures are drawn on the dataset page.
- The data-marked test covers only `004ae2`.
- The draw relies on NumPy's `default_rng` permutation staying the same across versions. The
  keys are written down, so the subset does not depend on this.
- The Re 50k folder `256_simulation` (377 GB) was not examined. It may be a native $256^2$ run
  set at Re 50k, which would be a resolution comparison for the coarse-grained tier. This is
  unverified.
- At Re 50k, the vorticity median blur has only one usable strength on a 64-cell grid. A run
  that needs a rank correlation on that axis should use a finer analysis grid.
- Five realisations per Reynolds number are each run on their own and pooled afterwards
  (`combine_runs(..., across="trajectory")`); no Hydra callback gathers them at the end of the
  sweep, as `FamilyComparison` does for a family, so the gathering is a one-line Python call.
- `persistence_wasserstein` is not affordable at 128 on the kept part (2.5 to 40 h at stride
  25); issue 144 applies here as on the shear layer. `dataset.slow_metrics` can now give it a
  coarser grid or fewer frames than the rest; no one has chosen them for this dataset.
- The window was chosen from the three default trajectories only.
- The degraded solver runs have open points of their own, in section 7.

## 7. The degraded solver runs (`kinet_hit_re12p5k_candidates`, `kinet_hit_re25k_candidates`, `kinet_hit_re50k_candidates`)

Added on 2026-11-27 by the step-20 dataset agent. Sections 1 to 6 concern the realisations
alone; this section concerns the kinet reruns scored against them, and follows the same
structure.

### What they are for

- **Candidates of known provenance from many initial conditions.** Specification 05
  (`dataset_specs/05_initial_conditions_and_degraded_solver_runs.md`, Options B and C) asks for
  reference trajectories from many starts and, for each, candidate trajectories made by a solver
  degraded in a controlled way, so that a metric's error can be read against the prediction step
  and over the starts. That is how the thirteen per-step metric cards say their fields report
  them (spec 05, Sect. 1). It is step 20 of `dataset_specs/BUILD_ORDER.md`, and the project's own
  protocol (`CLAUDE.md`, "Evaluation protocol", steps 1 and 2): a trusted solver degraded on
  purpose. Nothing here is a machine-learning model.
- **A known answer, which is an ordering.** No exact error curve exists. What is known in advance
  (spec 05, Sects. 4.1 and 4.2, reasoning there) and measured by the job is that the control
  reproduces the realisation, that 64^2 is further off than 128^2, and that the error grows with
  the viscosity error. No analysis in the repository reads that ordering across runs yet
  (issue 147).
- **Two orthogonal degradation axes**, as the protocol asks: the grid (128^2, 64^2) and a wrong
  viscosity (Re times 0.9, 0.75, 0.5), with a third kind, a different collision model (BGK).

### How they are treated

- **Runs.** 105 kinet runs on scratch, 5 realisations times 7 kinds times 3 Reynolds numbers,
  each started from its realisation's stored step-0 fields (block-averaged for a coarser grid)
  with kinet's `initial_state` route and equilibrium populations, as the realisations started.
  Commands, kinet commit, device, jobs, configurations and the job's checks are in
  `docs/datasets/logs/kinet_runs/isotropic_candidates/` (the README there, "Degraded reruns of
  the isotropic realisations").
- **Conversion.** `python -m fmeval.data.convert_kinet <rollout> <file> --every N`, with `N`
  50 for the 256^2 and 128^2 runs and 25 for the 64^2 runs, so every file holds the realisation's
  frames 0, 50, ..., 1000 (21 frames; the realisation's step 500 k at frame k). The realisation
  itself is converted the same way from its archived rollout into `reference.h5` beside its
  reruns, and checked equal to its full file at those frames.
- **Location.** `/global/cfs/cdirs/m4790/Data/kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids/sys_Re-<Re>_Ma-1en1_candidates/<key>/{reference,control,grid128,grid64,re0.9,re0.75,re0.5,bgk}.h5`,
  beside the realisations' folders and named like them; at Re 5e4 only `reference`, `control`,
  `grid128`, `grid64` and `bgk`.
- **Reader.** `kinet_raw` with `cell: 1` and `candidate: <kind>.h5`. With `cell`, the reader reads
  a run in cells and solver steps, and a candidate's cell is scaled by the ratio of the two runs'
  cells along x (4 for a 64^2 rerun), so both span one domain and share one clock: frame k is time
  500 k on every grid, bitwise. Velocity and density keep their lattice values, which kinet's
  acoustic scaling makes comparable across grids (the lattice velocity of a run is the same on
  every grid). Vorticity is recomputed from velocity on the analysis grid, as for the
  realisations. Periodic on both axes (the reader's default, true of the runs). Fields density,
  velocity and vorticity; no pressure (the gauge, not converted).
- **Configuration.** The fragment `_isotropic_candidates.yaml` inherits `_decaying_isotropic_2d`
  and sets the reader options, the frames and the notes; each option inherits its realisations'
  option (`kinet_hit_re<Re>`, for the default realisation, the Reynolds number and the rank) and
  the fragment, and states its name, path and label. The kind is chosen with
  `dataset.reader.candidate=<kind>.h5` (default `grid128.h5`) and the realisation with
  `dataset.trajectory=<key>`. With a candidate, `evaluate.py` replaces the ladder by three levels
  per frame: the clean reference, the anchor `mean_field` and the rerun.

### What part is evaluated

| Selector | Value | Effect |
|---|---|---|
| `dataset.time` | start 3, stop 12, reduction 1 | The realisation's frames 150 to 550 every 50th: 9 frames |
| Realisations | The five evaluated ones of `kinet_hit_re<Re>` | Swept with `-m dataset.trajectory=...` |
| Kinds | 7 at Re 1.25e4 and 2.5e4, 4 at Re 5e4 | Swept with `-m dataset.reader.candidate=...` |
| `analysis_resolution` | 128; 64 for `grid64` | `grid64` needs `dataset.analysis_resolution=64`; at 128 the run stops with "analysis grid 128 is finer than the data (64)" |

That is 90 runs of 9 frames, 810 frames, each scored on three levels.

- **Why this window and stride.** They are the realisations' own (section 3 and the step-32
  entry), so a rerun's frames are the frames the realisations' ladder runs score, and nothing in
  the reruns argued for others: inside the window no rerun has decorrelated from its
  realisation (distance over its decorrelated value, `d / d_sat` in `candidates_checks.txt`, at
  most 0.6 in velocity and 0.85 in vorticity, both `grid64` at frame 550), so every frame
  distinguishes the kinds, while at frame 800 `grid64` has decorrelated in vorticity (1.02 at
  Re 2.5e4, 0.99 at Re 5e4) and stays there. Before frame 150 the realisation is a random-phase field
  (section 3) and the reruns' distances are small: `re0.9` is 0.005 or less in velocity at every
  Reynolds number before frame 150, apart from the grid error at Re 5e4.
- **Why frames are cheap here, and the stride was still kept.** A candidate replaces the ladder,
  so a frame costs three evaluations per metric and field instead of one per level of the default
  ladder, 89 of which a candidate run drops (`evaluate.py`'s log). Measured
  (below), the 24-metric panel costs 0.68 s of metric time per frame here, against 34 s on the
  ladder (section 3), so a finer stride would be affordable in time. It was not taken: a rerun's
  error is one deterministic history per realisation, which grows smoothly between frames 150
  and 550 (the job's table), so finer frames add points on that curve, not independent samples,
  and they would double the disk (a finer `--every`).
- **Independent samples.** The five realisations are independent samples outright; the nine
  frames of one realisation are not.

**Measured cost** on a login node, realisation `c95586` of Re 2.5e4, 9 frames, 128 grid unless
stated (run folders under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/step20_candidates/`):

| What | Measured |
|---|---|
| `mse` and `nrmse`, whole `evaluate.py` run of 9 frames (inside one multirun) | 0.4 to 1.3 s per run; io 0.1 to 0.2 s |
| `mse` metric time per frame (3 fields, 3 levels) | 0.0003 s |
| Panel of the 24 metrics that run here, without `persistence_wasserstein`, `grid128` | 6.2 s of metric time (0.68 s per frame), 9.0 s run, 15.2 s wall with Python start-up |
| The most expensive of them per frame | `persistence_distance` 0.22 s, `energy_distance` 0.15 s, `spectral_energy_flux` 0.11 s |
| `persistence_wasserstein` alone, `grid128` | 4.7 s of metric time (0.52 s per frame), 7.7 s wall; it did not stall |

The panel is every registered metric except the eight ensemble metrics, the six shock-set metrics
(no absolute pressure) and `persistence_wasserstein`, as in section 3. **Projected** (my
arithmetic): 90 runs of about 15 s each for the panel with `persistence_wasserstein`, about 25
minutes in one process.

**Disk.** 105 files, 3,512,431,320 bytes (3.51 GB): 90 reruns (2.85 GB; 44.07 MB per 256^2 file,
11.04 MB per 128^2, 2.78 MB per 64^2) and 15 reference subsets (0.66 GB). The evaluated 9 of the
21 frames are about 1.5 GB of it (my arithmetic). Converting the reruns whole would have taken
about 135 GB (my arithmetic: 60 files of 2.10 GB at 256^2, 15 of 0.53 GB at 128^2 and 15 of
0.066 GB at 64^2). The raw rollouts are 275.7 GB on scratch, which is purged after about eight
weeks; every rerun is reproducible from the archived driver and configuration.

**Why this balance.** The frames are the realisations' and cost little; the disk is 2.6% of whole
conversion; the stored frames outside the window (frame 0, the shared start, and 600 to 1000,
the condensate) cost about 2 GB and keep those stretches readable with `dataset.time.start` and
`stop` without a second conversion.

### Decisions and why

1. **One configuration per Reynolds number, the kind a reader option.** Who: this agent, under
   Kareem's rule to fit the plan to the code (`BUILD_ORDER.md`, "How code is written for this
   plan"). Alternatives: one configuration per kind and Reynolds number (21 files that differ in
   one line); one configuration for all three (the folder names `12p5k`, `25k`, `50k` cannot be
   derived from a value a configuration holds, so the path cannot follow a Reynolds number).
   Reverse: write per-kind options that inherit a per-Reynolds option and set `reader.candidate`.
2. **A copy of each realisation at the reruns' stride, beside them (0.66 GB).** Who: this agent.
   Why: `candidate` is a file name in the reference's folder. Beside the full realisation, the
   name would have to contain the realisation's key, so two realisations' runs would differ in
   `dataset.reader.candidate` and `combine_runs(..., across="trajectory")` would refuse them; and
   the realisation (1001 frames) would have to be read at a stride of 50 while each rerun is read
   at stride 1, which `kinet_raw` cannot do (every option is shared with the candidate). Either
   would have needed a code change; the copy needs none, and is checked equal to the realisation
   at every frame it holds. Alternative: extend `kinet_raw` to read the candidate at its own
   stride and `combine_runs` to ignore a candidate path that names the trajectory. Reverse: point
   `path` at `sys_Re-<Re>_Ma-1en1/<key>.h5` and make those two changes.
3. **Convert every 50th frame of the realisation's clock, not the whole run.** Who: this agent.
   Why: the evaluated frames are every 50th, and whole files would be about 135 GB instead of
   3.51 GB. The converter gained one option, `every` (6 lines of code, a docstring entry and a
   test). Alternative: convert
   only the nine evaluated frames, which needs a frame list rather than a stride and would drop
   frame 0 and the condensate. Reverse: reconvert with `--every 1`; a 64^2 rerun then holds 501
   frames against the realisation's 1001, so the realisation would have to be read at stride 2 and
   the rerun at stride 1, which needs the reader change of decision 2.
4. **`cell: 1`, with a candidate's cell scaled to its grid.** Who: this agent. Why: a coarse
   rerun must lie on the same domain as its realisation remapped, or the pair is refused ("a pair
   must share its grid"); `box` would do it but needs the lattice scales, and the realisations'
   `normalization_plan.lattice` is empty (they predate kinet recording it). The change is 4 lines
   in `KinetRawTrajectory.predictions` and `__init__`, tested on a 16 x 8 run with an 8 x 4
   candidate. Consequence: rows' `time` and `lead_time` are solver steps of the 256^2 run (0 to
   10 000), not the convective units of `kinet_hit_*`'s rows (0 to 2.2553). Alternative: rewrite
   the files' spatial length at conversion, which would put a value in the file that kinet did not
   write. Reverse: drop `cell` and give the realisations' converted files lattice scales.
5. **At Re 5e4, the three wrong-viscosity reruns are left out.** Who: this agent, asked by the
   coordinating session to decide. Evidence (`candidates_checks.txt` and `.json`): the realisation
   is a 512^2 run stored at 256^2, so the 256^2 "control" departs from it by a grid error (velocity
   distance 0.011 at frame 150, 0.155 at 550). The viscosity reruns' own error is smaller than that
   (`re0.9` 0.0115 at frame 150), so in vorticity `re0.9` and `re0.75` fall below the control at
   frame 150, the control lies below every other rerun for 0 to 2 of the five realisations at
   each evaluated frame, and the viscosity ordering holds for 0 to 5. Their known answer is lost,
   and the same axis is tested cleanly at the two lower Reynolds numbers. `bgk`, whose own error
   is about four times the grid error (0.047 against 0.011 at frame 150), and the grid reruns are
   kept: among those four, the 256^2 rerun lies below the other three and `grid64` above `grid128`
   for all five realisations at every evaluated frame in both fields. The `control` file keeps
   its name, and its configuration and label say plainly that it is a grid candidate. Reverse:
   convert `Re-50k/re0.*` from scratch before it is purged (the conversion loop of the kinet_runs
   README), or rerun them from the archived driver, and add them to the kinds.
6. **Analysis grid 128, and 64 for `grid64`.** Who: this agent. Why: 128 is the realisations'
   grid (section 3) and `grid128`'s own, so every kind but `grid64` is scored on one grid; a rerun
   can only be scored on its own grid or coarser. Consequence: the same-grid kinds are not scored
   on their 256^2 grid, so their values differ from the job's distances, which were taken there
   (`re0.5` vorticity `nrmse` 0.092 at 128 against the job's 0.108 at 256, frame 150 of
   `c95586`), and `grid64` is on a grid of its own. Alternatives: 256 for the same-grid kinds,
   affordable at this cost; 64 for every kind, one grid for all but losing most of the gradient
   content (section 3). Reverse: `dataset.analysis_resolution=256` or `64`.
7. **Kinds named as the driver named them** (`re0.9.h5`, not `re0p9.h5`), so one name runs from
   the driver through the scratch folders and the job's checks to the files and the
   configurations. Default kind `grid128.h5`, spec 05's first candidate (Option B).
8. **No ordering analysis built.** Nothing in `fmeval/analysis.py` reads whether a metric's scores
   follow the known order of several candidate runs, and it would be real new code. Written up as
   issue 147, not built.

### Open points

- The ordering across kinds is read by hand until issue 147 is built.
- A card cites one run per dataset, so which kind a card cites for these datasets is open
  (step 30 of `BUILD_ORDER.md`).
- `lead_step` on these rows is the frame index (3 to 11), as for `kinet_shear_layer_refinement`,
  and `lead_time` is in solver steps of the 256^2 grid (decision 4).
- The same-grid kinds are scored at 128, not on their own 256^2 grid (decision 6).
- At Re 5e4 there is no control (decision 5).
- The raw rollouts, the Re 5e4 viscosity reruns and every frame not kept exist only on scratch,
  which is purged after about eight weeks.
- No dynamics figures are drawn for the reruns.
- Not run: any metric on every kind, realisation and Reynolds number; only the cost runs and
  `mse`, `nrmse` and `rmse` on Re 2.5e4.

