# Log: forced stationary two-dimensional turbulence

The log of the page `docs/datasets/forced_turbulence_2d.md`, for the next agent who updates the
dataset. One configuration exists, `kinet_forced_re40k`. Every number here was measured by the
named command or read from the named file; anything else is labelled as reasoning.

## 1. What the dataset is for

Build-order step 22 (`dataset_specs/BUILD_ORDER.md`), Option B-dc of
`dataset_specs/04_forced_stationary_turbulence.md`. Every other flow in the repository decays,
so no metric could yet be shown reading the statistic its field defines on stationary
turbulence with a scaling range (spec 04, Sect. 1). It serves:

- the eight spectral, increment and tail metrics spec 04 names (`spectrum_l2`,
  `spectral_energy_flux`, `increment_w1`, `increment_w1_by_separation`, `increment_flatness`,
  `energy_distance`, `tail_index`, `tail_exceedance`), each as one more experiment of the
  degradation ladder;
- the data half of `proposals/EXP-tail_exceedance-base-period-climatology.md` (a base period is
  on disk; the harness half is issue 095);
- the forced data that issue 085's two-dimensional cascade checks wait on (the checks are not
  built);
- physical scales in cells for issue 128 (forcing scale 32 cells, integral scale 141 cells,
  native grid);
- the weakly compressible, forced, dual-cascade part of
  `proposals/EXP-spectral_energy_flux-forced-2d-compressible-flux-loop.md`, not its compressible
  Mach 0.3 to 0.5 case.

## 2. How it is treated

- **Source.** One kinet run, identity key `7a817df3`:
  `/pscratch/sd/k/khegazy/kinet_datasets/forced_turbulence/homogeneous_isotropic_turbulence/Re-40k_Ma-1en1_forced_drag_2d/7a817df3/tiers/full/rollout.h5`
  (22 266 408 068 bytes; 441 saved frames: step 1 and every 500th step, plus the initial
  condition apart). D2Q9, plain BGK with the polynomial equilibrium, Mach 0.1, Reynolds number
  40 000, $1024^2$ cells, doubly periodic, `random_modes` forcing in the shell
  $31 \le |\mathbf n| \le 33$ (correlation time 10 steps, variance 2.55e-11, seed 1729), the
  `linear` law at the constant rate -5e-5 (a drag), 220 000 steps. Job 62116382 on the regular
  queue, one A100, kinet branch `datasets/forced-drag` at `55e7edfda` with no uncommitted
  changes, 727.9 s of stepping. Every record, the kinet patches and the command are in
  `docs/datasets/logs/kinet_runs/forced_turbulence_2d/` (its section in that folder's README
  says what was left out).
- **Not reproducible on unmodified kinet.** The run needs a negative rate on the `linear` law
  and the `minimum_mode` key on `random_modes`, both refused by kinet's `perf/cleanup`. They are
  three commits on the local, unpushed branch `datasets/forced-drag`, saved as patches in the
  archive. Without the patches the case file does not even exist on `perf/cleanup`.
- **Reproducing it.** Rebuild the branch (`git checkout -b datasets/forced-drag d1cd353b8 && git am
  docs/datasets/logs/kinet_runs/forced_turbulence_2d/kinet_patches/*.patch` in a kinet checkout),
  make a worktree of it, point `env.sh` at the worktree, and submit the `sbatch` line of
  `sbatch_final.txt` with a fresh data root: case
  `homogeneous_isotropic_turbulence/Re-40k_Ma-1en1_forced_drag_2d`, overrides
  `io.save_every_n=500 io.record_distributions=false io.record_equilibria=false
  runtime_logging.every_n=5000`. Not executed; whether a rerun is bitwise identical is not
  known.
- **Scratch is purged after about eight weeks.** With it go the raw 22.3 GB run (the 385 saved
  frames not converted, at 500-step spacing), the 63.1 GB of the six pilots and the throughput
  run (under `.../forced_turbulence/_pilot/`), the 2.1 GB debug test, the kinet logs and Slurm
  output left out of the archive, and the worktree of the branch. What survives: the converted
  file on CFS, the archive in this repository, and the branch in the kinet checkout on the home
  file system.
- **Conversion.** `python -m fmeval.data.convert_kinet <rollout> <destination> --every 8`, no code
  change, 8.8 s on a login node. It drops step 1 (uneven spacing), keeps the initial condition and
  every 8th saved frame counted back from the last, so steps 0, 4000, ..., 220 000 (56 frames,
  frame i is step 4000 i), and carries density, velocity and vorticity. The pressure is not
  carried: the run's `pressure_convention` is `fluctuation_referenced`, the gauge
  $(\rho - 1)c_s^2$ (issue 101). The stability fields are dropped.
- **Where.** `/global/cfs/cdirs/m4790/Data/kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids/sys_Re-40k_Ma-1en1_forced_drag/7a817df3.h5`,
  1 879 077 104 bytes.
- **Checked.** Every one of the 56 frames and three fields equal to its slot of the rollout
  (`np.array_equal`), the clock equal to `time/time_convection`, the step index equal to
  4000 i; read back by the `kinet_raw` reader; at step 220 000 the energy, enstrophy, largest
  speed and density range equal the check's row to its printed digits (E 1.54250e-3, Z
  1.81180e-5, max speed 0.19122, density 0.94239 to 1.01707). The data-marked test
  `test_the_forced_run_reproduces_the_jobs_check_on_its_evaluated_frames` in
  `tests/test_loader_contract.py` asserts E, Z and the density range on all 21 evaluated frames
  through the pipeline against `checks/final_220000.txt`.
- **Reader and options.** The existing `kinet_raw` reader with `cell: 1`, so the clock is the
  solver step. Boundaries periodic on both axes (the reader's default). Vorticity is recomputed
  from velocity on the analysis grid, as for every dataset.

## 3. What part is evaluated

**Kept:** steps 140 000 to 220 000, frames 35 to 55 of the converted file, every one (21
frames), on the $256^2$ analysis grid, with the default ladder (91 severity levels over 23
axes), density, velocity and vorticity.

**Why this window.** The check shows the spin-up over by step 50 000: the energy relaxes on
$1/(2\alpha) = 10\,000$ steps, and from step 50 000 on the energy stays between 1.49e-3 and
1.57e-3 with a standard deviation 1.2% of its mean (`checks/final_220000.txt`). Steps 50 000 to
130 000 are proposed as a base period and 140 000 to 220 000 as the evaluation period, the
split of spec 04 (a base and an evaluation period with a gap of a few large-eddy times, 2550
steps here). The mean energies of the two exact windows are 1.5245e-3 and 1.5479e-3 (81 frames
each, every 1000 steps, computed from the check's rows; the check's own "first half" and
"second half", 1.52432e-3 and 1.54637e-3, are the halves of steps 50 000 to 220 000, not these
windows), 1.5% apart. The energy's correlation time on this run is 15 970 steps (the 150 000-step
pilot gave 6 010 steps; the longer record supersedes it, but the figure is itself uncertain), so
an 80 000-step period holds only about five independent samples of the total energy, and a 1.5%
difference is within its slow wander. The velocity field's correlation time is 2 146 steps,
about 37 per period. So the two periods are statistically alike for the velocity field and only
loosely tested alike for the total energy.

**Why every stored frame of it.** Frames 4000 steps apart are about two velocity correlation
times apart (autocorrelation 0.052 at that lag), so the 21 frames are close to independent
samples of the field, which is what the per-frame rank statistics need. Spacing them 8000 steps
apart (11 frames) would halve the cost and the sample.

**Why the 256 grid.** Measured on steps 140 000, 180 000 and 220 000, curl taken spectrally on
each block-averaged grid (script run from the scratchpad on 2026-11-27, numbers here):

| Grid | Energy kept | Enstrophy kept | Palinstrophy kept | Shell energy kept at 32, 40, 64, 96, 120, 128 | Slope 6–28 | Slope 40–120 |
|---|---|---|---|---|---|---|
| 1024 (native) | 1 | 1 | 1 | 1 | −1.507 | −4.482 |
| 512 | 0.997 | 0.975 | 0.832 | 0.99, 0.985, 0.962, 0.916, 0.871, 0.854 | −1.511 | −4.594 |
| 256 | 0.986 | 0.897 | 0.517 | 0.953, 0.927, 0.822, 0.645, 0.570, 0.578 | −1.529 | −4.989 |
| 128 | 0.947 | 0.718 | 0.241 | — | — | — |

A second agent's measurement over all 21 evaluated frames agrees (energy 0.997 / 0.986 / 0.947,
enstrophy 0.975 / 0.897 / 0.718, palinstrophy 0.831 / 0.515 / 0.240 on 512 / 256 / 128;
`scratchpad/grid_retention.py`, reported by the coordinator). The 256 grid keeps every shell to
128: the inverse range (6 to 28) and the forcing shell (32) almost whole, and the direct range
to the grid's last shell, attenuated by the block average above shell 64, which steepens its
measured slope from −4.48 to −4.99. The 128 grid would put the forcing shell at a quarter of the
way to its last shell (64) and lose 28% of the enstrophy. The 512 grid keeps the direct range
nearly whole (slope −4.59) at 4.3 times the cost.

**Measured cost** (one frame, step 140 000, default ladder, a shared login node, metric time
summed from `wall_time_s` in `results.csv`; runs under
`/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/forced_cost/`, `log256.txt`,
`log512.txt`, `logpd512.txt`):

| Metric | 256 grid | 512 grid |
|---|---|---|
| `mse` | 0.04 s | 0.14 s |
| `wasserstein` | 6.1 s | 27.2 s |
| `increment_w1_by_separation` | 6.5 s | 31.0 s |
| `spectral_energy_flux` | 14.3 s | 121.8 s |
| `energy_distance` | 26.6 s | 106.9 s |
| `persistence_distance` | 60.2 s | 204.1 s |
| every other metric of the panel (18) | 7.4 s in all | 30.5 s in all |
| **panel without `persistence_wasserstein`** | **121.2 s** | **521.6 s** |
| whole run, wall | 146 s | 420 s without `persistence_distance` |

The panel is every pairwise and single-field metric that runs on these fields (24 bundles);
the shock metrics need pressure and the ensemble metrics members, so neither runs. The second
agent's runs agree: at 512 `persistence_distance` 199 s, `spectral_energy_flux` 122 s,
`energy_distance` 108 s, `increment_w1_by_separation` 31 s, `wasserstein` 27 s; with `mse` alone
the whole run takes 5.8 s at 256, 13.9 s at 512 and 74.9 s on the native grid (`mse256.log`,
`mse512.log`, `mse1024.log`, `exp512.log` in the same folder, reported by the coordinator).

**`persistence_wasserstein` is not run.** On one frame (step 140 000) with the default ladder,
density and vorticity, it did not finish within 900 s on the 64 grid (`logpw64.txt` in the
folder above) nor within 900 s on the 128 grid (`logpw128.txt`); both were stopped by `timeout`
(exit 124). A second run at 64, made while the first was still going and so sharing the login
node with it, was stopped after 560 s, also unfinished (`logpw64b.txt`). The ladder asks for 91 comparisons per field, 182 in all, so 900 s is at least 4.9 s per
comparison, far above the 0.015 to 0.08 s issue 144 measured per comparison at 64 on
`kinet_re5e4`; whether this is the stall inside Hera that issue 144 records or a uniformly slow
diagram was not diagnosed. The 64 grid is already the coarsest that holds the forcing shell
(at its last shell, 32), so no `slow_metrics` grid or stride brings it within a frame's budget,
and none is set. Not measured at 256. Issue 144 records it.

**Projected panel time:** about 45 minutes for the 21 frames at 256 in one process without
`persistence_wasserstein` (121 s each plus reading and calibration); about 3 hours at 512.
`dataset.time.shards` splits it across processes.

**Disk:** 1.88 GB on CFS for all 56 frames, of which 21 are evaluated and 20 form the base
period; the initial condition and 14 spin-up and gap frames ride along because the converter
keeps every Nth frame from the start.

**Calibration** (from the cost runs' `data/calibration.csv` and warnings). On the 256 grid the
characteristic scales are 17.8 cells (density), 19.5 (velocity) and 7.6 (vorticity); on 512,
35.3, 38.2 and 13.3. On the 256 grid the mildest smoothing levels collapse: vorticity
`box_blur` and `median_blur` levels 1 and 2 and `gaussian_blur`, `disk_blur` and
`epanechnikov_blur` level 1 leave the field unchanged, `box_blur` levels 2 and 4 repeat 1 and
3, `median_blur` level 2 repeats 1; on density and velocity `box_blur` and `median_blur` level
1 leave the field unchanged. On 512 only vorticity collapses (`box_blur`, `disk_blur`,
`epanechnikov_blur` and `median_blur` level 1 do nothing; `box_blur` and `median_blur` level 3
repeat level 2); on the native grid nothing collapses (the second agent's `mse1024.log`). These
are facts about the fields: the smoothing widths are fractions of a characteristic scale of a
few cells, which a window of whole cells cannot resolve. The harness excludes them; no severity
list was changed.

## 4. Decisions and why

1. **The plan's viscosity and drag were changed (the job agent, from the pilots).** Spec 04
   designed Re 2700 and a drag of 2.26e-4 per step for an arrest scale of 256 cells. On a
   60 000-step pilot at those settings viscosity removed 77% of the injected energy (drag 0.233
   of it), the spectrum peaked at shell 32, the forcing shell, and the inverse-range fit read
   +1.50: no cascade formed, because the viscous scale was too close to the forcing scale. Re
   20 000 at the same drag still peaked at 32. Lowering the drag to 1e-4, 7e-5 and 5e-5 at Re
   40 000 moved the peak to shell 9 and then 4 and the inverse slope to −0.78, −1.37 and −1.53;
   5e-5 was chosen (`calibration_summary.txt`). The cost: the arrest-scale estimate
   $\ell_\alpha \simeq \epsilon_\alpha^{1/2}\alpha^{-3/2}$ is 1108 cells, above the box, so the
   box, not the drag, bounds the inverse range; the lowest shells do not grow over the record.
   To reverse: a larger box (spec 04 suggests $2048^2$) with the plan's arrest scale inside it.
2. **The existing converter and reader, no new code (the agent, under the build order's rule).**
   `convert_kinet --every 8` and `kinet_raw` with `cell: 1` do everything; nothing in `fmeval/`
   changed. The only new code is the data-marked test.
3. **Keep every 8th saved frame of the whole run (the agent).** 4000 steps is about two velocity
   correlation times, so neighbouring frames are near-independent; both periods stay on disk for
   1.88 GB. Alternatives: `--every 4` (2000 steps, 111 frames, about 3.7 GB), which adds frames
   correlated at 0.14 with their neighbours; a window option in the converter (new code, refused
   by the rule) to drop the 15 spin-up and gap frames, 0.5 GB. To reverse: reconvert from the raw
   run while scratch holds it.
4. **`cell: 1` (the agent).** It changes only the clock, to solver steps, the unit of every
   rate and time scale of this run. Without it the clock is in domain crossings,
   $5.64 \times 10^{-5}$ per step, and spacing and velocity are the same. To reverse: delete the
   `reader` block.
5. **The 256 analysis grid and every frame of the evaluation period (the agent).** Section 3.
   To reverse: `dataset.analysis_resolution=512` (about 3 hours) or `dataset.time.reduction=2`.
6. **The base period is kept but not evaluated (the agent).** A threshold set from it needs a
   path the harness does not have (issue 095). Evaluating it as a second window would only
   double the cost of the same experiment.
7. **Not built, by the build order's rule ("change the plan to fit the code").** (a) The
   base-period threshold of the `tail_exceedance` proposal: issue 095 updated, proposal narrowed.
   (b) A known-answer check of the flux plateau against the injection and drag rates: the run's
   rates are not dataset metadata and no analysis reads a companion curve against a value; issue
   150, with what the real run gave. (c) The spectral constants, $S_3$ and the viscous scale:
   not measured.
8. **Folder name `sys_Re-40k_Ma-1en1_forced_drag` (the agent),** after the `sys_Re-<Re>_Ma-1en1`
   folders beside it, with the forcing named; the file is the eight-character identity key kinet
   now writes.

## 5. Log entries

### 2026-11-27: the dataset added (dataset agent, step 22)

- Converted the run to CFS (section 2) and checked every frame. Archived 88 provenance files
  byte for byte into `docs/datasets/logs/kinet_runs/forced_turbulence_2d/` and screened them for
  addresses and credentials; checked each kinet patch against its commit.
- Measured the cost at 256 and 512 and what each grid keeps (section 3); chose the evaluated part.
- Added `configs/dataset/kinet_forced_re40k.yaml`, this log, the page and its dynamics figures
  (`python -m fmeval.cards dynamics kinet_forced_re40k`), the registration in
  `configs/cards/default.yaml`, the data-marked test, rows in `docs/datasets/README.md` and
  `AGENTS.md` §1, step 22 of `dataset_specs/BUILD_ORDER.md`; updated issues 085, 095, 128 and 144,
  wrote issue 150, and narrowed three proposals.
- kinet's own tests on the branch (`kinet_tests_pytest.txt`, 737 passed) ran at `ef76ae40b`, not
  at the final `55e7edfda`, which changes only the case file, one initialiser list and one
  smoke-test list (`git show --stat 55e7edfda`).

### 2026-11-27: two real evaluations of the evaluated part (dataset agent)

Both on the configuration as committed (21 frames, steps 140 000 to 220 000, $256^2$, default
ladder), results under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/`, read with
`fmeval.analysis.analyse`. Each was run twice, by two agents started on the same task, and the
two runs agree value for value (`rmse_1795830083` and `rmse_1795830548`;
`spectral_energy_flux_1795830149` and `spectral_energy_flux_1795830583`, 316.1 s).

- **`rmse`** (`rmse_1795830083`, 25.7 s for the run: reading 4.8 s, degradations 16.6 s, metric
  0.6 s). Calibration over the 21 frames: characteristic scales 17.4, 19.7 and 7.6 cells for
  density, velocity and vorticity, spread over the frames 2%, 1% and 0%, far below the 25% at
  which the run warns, as a stationary flow should give. The anchor (the field's spatial mean)
  scores a median 0.00561 on density, 0.0390 on velocity and 0.00576 on vorticity. Every
  ordinal axis has a per-frame rank correlation `rho` of 1 on every field except vorticity
  `box_blur` and `median_blur`, which have too few distinct levels left (section 3,
  calibration) and read NaN; vorticity `translate_x` and `translate_y` are fully ordered in 81%
  and 76% of frames. The Gaussian impostor scores a damage of 1.39 (density), 1.43 (velocity)
  and 1.42 (vorticity), close to $\sqrt 2$, the value for a field uncorrelated with the
  reference. `multiplicative_noise` on density reaches a damage of 89, the known effect of
  multiplying a field of mean 1 (issue 139).
- **`spectral_energy_flux`** (`spectral_energy_flux_1795830149`, 310.9 s: metric 299.1 s, 14.2 s
  per frame). The reference's own flux curve is negative below the forcing shell in every frame
  at $K = 8$ and 16 (median $-5.9 \times 10^{-8}$ and $-1.15 \times 10^{-7}$ per step), changes
  sign at the forcing shell (median $-4.0 \times 10^{-9}$ at $K = 32$, negative in 67% of
  frames) and is small and positive above it ($1.08 \times 10^{-8}$ at 64, $1.6 \times 10^{-9}$
  at 128, positive in every frame). Beside the check's rates over the same steps, drag
  $\epsilon_\alpha = 1.548 \times 10^{-7}$ and injection $\epsilon_I \approx 2.1 \times 10^{-7}$:
  the median at $K = 16$ is 0.74 of $\epsilon_\alpha$, and on the last frame, whose whole curve is
  stored, the flux is most negative at $K = 29$, $-1.48 \times 10^{-7}$ (0.96 of
  $\epsilon_\alpha$), and averages $-1.01 \times 10^{-7}$ over shells 6 to 28. So the sign and the size are those of the
  inverse cascade removed by the drag, but the magnitude grows up to the forcing shell rather
  than standing on a plateau. This is an observation, not a pinned known answer (issue 150).
  The registered number: `rho` 1 on 14 of the 20 ordinal axes, 0.8 on `lowpass_butterworth`,
  0.4 on `lowpass_ideal`, $-0.71$ on `translate_subpixel` (a small response: its largest damage
  is 0.009), and NaN on `bias`, `translate_x` and `translate_y`, which leave
  the flux unchanged, as does the `uncorrelated` probe (a large translation, damage 6e-16); the Gaussian impostor scores 1.15, so the flux, unlike an energy
  spectrum, sees the randomised phases.

## 6. Open points

- Whether 256 or 512 should be the grid of record: 256 attenuates the direct range above shell
  64 (slope −4.99 against −4.48), 512 costs four times as much.
- The arrest scale exceeds the box; a larger box would give the inverse range room to end on the
  drag rather than the box.
- The total energy's correlation time (15 970 steps here, 6 010 on a shorter pilot) is
  uncertain, so the number of independent energy samples per period is roughly five, not known.
- No second realisation (spec 04 suggests a second forcing seed).
- The effect of the weak compressibility (local Mach up to 0.37) on the incompressible scaling
  laws is not quantified.
- Issues 095 and 150 (the two known-answer tests the harness cannot run), 144
  (`persistence_wasserstein`).
