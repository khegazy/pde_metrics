# Log: supersonic flow past a cylinder

This log covers [the supersonic cylinder page](../supersonic_cylinder.md). No configuration
reads this flow yet.

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
