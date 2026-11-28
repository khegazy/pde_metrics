# Log: double Mach reflection

The page is `docs/datasets/double_mach_reflection.md`.

## `kinet_double_mach_reflection` (2026-11-27)

### What it is for

A two-dimensional pattern of several shocks that meet, from a solver, for the metrics that detect
and compare shocks: a straight incident shock, a curved reflected shock and a short Mach stem at a
triple point, of very different strengths (`dataset_specs/03_two_dimensional_shocks.md`, Sect. 4.2;
build-order step 18; `proposals/EXP-shock_set_distance-2d-shock-dataset.md`, which it narrowed). It
has no exact solution, so it is a reference for the degradation ladder, like
`kinet_supersonic_cylinder`.

### How it is treated

- **Source since 2026-11-28 (decision 7).** `N240_coarse-480-120.h5`: the $960 \times 240$ run
  (job 62134603, kinet `main` at `e67a1136e`) reduced to $480 \times 120$ by kinet's coarse graining,
  a mean over each $2 \times 2$ block with no time reduction, then converted at the saved frames
  nearest the three evaluated times (steps 2050, 4054, 5992; $t = 0.070835$, 0.136744, 0.2). The
  commands are in the entry of 2026-11-28. The bullets below describe the native run, which is now
  the coarser run of the same problem and stays on CFS as `N120.h5`; the reader, window and
  boundaries apply unchanged.
- **Source.** kinet's case `double_mach_reflection/default`, run on 2026-11-27 by the job agent
  (kinet `perf/cleanup` at `d1cd353b83e9`, one A100, job 62114362): PonD solver, $480 \times 120$
  cells, $t = 0.2$ in 2967 steps saved every 100, dynamic viscosity 0.01 (the case's), Prandtl number
  0.71. Records, the job's checks and its density plot (not archived, see the kinet_runs README):
  `docs/datasets/logs/kinet_runs/shocks_2d/`.
- **Conversion.** `convert_kinet_grouped(<rollout>, <dest>, every=10)` from
  `/pscratch/sd/k/khegazy/kinet_datasets/shocks_2d/double_mach_reflection/double_mach_reflection/default/a90f3f06/tiers/full/rollout.h5`
  to `/global/cfs/cdirs/m4790/Data/kinet/double_mach_reflection/compressible_fluids/Pr-71en2_vuy-1.4_visc-1en2/N120.h5`
  (7.4 MB): the initial condition and steps 1000, 2000, 2967 ($t = 0.0708$, 0.1368, 0.2), density,
  velocity and absolute pressure, the clock `time/time` (the converter's adaptive-run rule,
  `docs/datasets/logs/isentropic_vortex.md`). Checked equal to its source in every field and on the
  clock. The name follows the run's label, `dmr_N120`, the cells across the height.
- **Reader.** `kinet_raw`, no new code: `include_redundant` (the pressure is the solver's absolute
  one), `window: [[0, 384], [0, 120]]`, `boundary: [neumann, neumann]`.
- **Window and boundaries.** Measured: beyond $x = 3.2$ the gas is the pre-shock state at every kept
  frame (to $1.4 \times 10^{-8}$ at $t = 0.2$, exactly before); the first three columns are the
  post-shock inflow to $3 \times 10^{-14}$ (density, velocity) and $5 \times 10^{-13}$ (pressure); the
  wall-normal velocity in the row next to the wall is at most 0.51 against 4.8 anywhere. What the
  mirror does at each face is on the page.

### What part is evaluated

- **Kept:** frames 1 to 3 of the converted file, $t = 0.071$, 0.137, 0.2, on the native
  $384 \times 120$ window, with the default ladder.
- **Why.** The pattern grows about linearly in time (the Mach stem's foot moves at a steady rate in
  the job's check), so the frames hold one pattern at three sizes on the grid, from small to the
  standard final picture; at the first saved frame ($t = 0.009$) the Mach stem's foot is 13 cells from the wall's start, and frames between the
  kept ones would be near copies. The window drops a quarter of the cells, which are a constant
  state. Three frames are three samples of a deterministic pattern, not independent turbulence;
  the shock-set metrics' detector flags 644, 785 and 941 cells in them.
- **Measured cost** (login node, 2026-11-27, `evaluate.py` on the three frames): `rmse` alone
  74.3 s wall (55.8 s of it the ladder); the 27 deterministic metrics other than the persistence
  ones, of which 15 run here (12 need a periodic domain), 99.7 s wall (ladder 55.8 s, metrics 7.0 s,
  the five shock-set distances 0.38 s per frame each); `persistence_distance` on density 21.1 s wall
  for one frame (9.3 s of metric time); `persistence_wasserstein` on density did not finish one frame
  in 900 s and was stopped (issue 144). Projected: the panel without `persistence_wasserstein` about
  2.5 minutes (my arithmetic). Disk 7.4 MB, all read.
- **Calibration** (`data/calibration.csv` of the `rmse` run): characteristic scales 240 (density),
  210 (velocity), 214 (pressure) cells on the window's extension, spread 0.09, 0.24, 0.07 across the
  frames (velocity just below `DRIFT_WARN`, 0.25); the mildest `highpass_ideal` level is a no-op on
  every field and is excluded.

### Decisions and why

1. **What it is called** (agent, on the task's instruction): a viscous solution of this solver at
   $\mu = 0.01$, not the inviscid picture of Woodward and Colella, with its measured lag of the
   incident shock (about 2 cells) and an unexplained thin feature stated on the page and in its
   label.
2. **The window $x < 3.2$** (agent). Still gas adds only a constant region to every statistic, and
   costs a quarter of the evaluation. The cut lies in that gas at every kept frame, so its mirror is
   exact. Alternative: the whole domain (the right face is zero-gradient in still gas, equally
   exact). To reverse: drop `window`.
3. **`neumann` on every face, no new boundary type** (agent). The inflow and the cut are exact
   mirrors; the wall's normal velocity and the imposed top shock are wrong only within a kernel
   width of the face (the page says how). A reflecting-wall type with an odd normal velocity would be
   a new entry of `BOUNDARIES` acting per channel, which the extension does not do today, and it is
   the open question 1 of `dataset_specs/BUILD_ORDER.md`, default `neumann`. Windowing the wall away
   would cut out the Mach stem and the jet, the pattern's point. To reverse: add the type and set it
   on y.
4. **No `slow_metrics` for `persistence_wasserstein`** (agent). Which grid or stride the persistence
   metrics get on each dataset is open (`BUILD_ORDER.md`, framework limit 1), and a coarser grid on a
   non-square window was not tried. Recorded in issue 144.
5. **Registered as evidence** with a label that says it has no exact answer and is not the
   benchmark picture.
6. **The stored field stays the native $480 \times 120$ run; the $960 \times 240$ run did not
   meet the criterion below** (agent, 2026-11-28, under Kareem's rules of 2026-11-27: simulate
   fine enough that artifacts are negligible, and make a finer run the dataset only if the
   stored field is free of numerical artifacts at the stored resolution). The criterion, fixed
   before the full run's numbers were read, is that at the stored resolution, at every evaluated
   time: (a) no value lies more than 1 % below the unshocked state (density 1.4, pressure 1),
   which nothing in the exact solution falls below; (b) the incident shock's foot on the rows
   $y = 0.6$ to $0.9$ is within 0.5 stored cells of Eq. (1) of the page; (c) its 10 %-to-90 %
   density width is at most 1.5 stored cells, since a shock this viscosity resolves (thickness of
   order $\mu / (\rho_1 u_1) \approx 0.01 / (1.4 \times 11.5)$, a tenth of a cell; an
   order-of-magnitude estimate, not a computed profile) gives at most one stored cell once block
   averaged; (d) no feature absent from the exact solution, such as the bands below, exceeds
   1 % of the local state; (e) the relative L2 difference from the next coarser run, block
   averaged to the same grid, is small enough that the finer run's own error, of about that size
   for a first-order method, is negligible. The coarse-grained $960 \times 240$ run passes (a) at
   the three stored frames and fails (b), (c) and (d) clearly; on (e) the difference is 2.5 to
   3.7 % in density. Every one of these numbers is about half the native run's, so the finer run
   is a better field, but not one free of artifacts. Marginal points: (a) holds at the stored
   frames only (12 of the 2997 saved frames of the coarse-grained run fall to 1.23), and stored
   at $240 \times 60$ the run meets (a) at every frame and is borderline on (b) and (c) (0.29 to
   0.62 cells, 0.97 to 1.60 cells) but fails (d) and (e) as at $480 \times 120$. To reverse: point
   `trajectory` at `N240_coarse-480-120` (same reader, window and frames; the test's foot
   positions and times must be remeasured), which the owner may prefer as an interim improvement.
7. **The stored field is the $960 \times 240$ run block-averaged to $480 \times 120$** (coordinator,
   2026-11-28, on Kareem's rule to use the finer run unless the coarse one is known to be clean;
   it supersedes the outcome of decision 6, whose criterion and verdict stand). The file is
   better than the native one on every check of decision 6, and it is still not free of numerical
   artifacts. What remains at the stored resolution, at the three evaluated times: the incident
   shock 0.75 to 1.16 cells behind Eq. (1) and 1.4 to 1.8 cells wide; the two bands of excess
   density, 3.3 % (the one the thin feature belongs to) and 4.8 % (trailing the incident shock)
   above the post-shock 8 at $t = 0.2$; a difference of 2.5 to 4.8 % from the native run (density,
   pressure, velocity); and a field above the unshocked state at the stored times only (12 of the
   2997 saved frames dip, to 1.23). What it affects: a metric that places shocks against the exact
   front reads the lag as about one cell of error, and a detector of features, or any statistic of
   the regions the exact solution holds uniform, may respond to the two bands, which belong to the
   solver and not to the flow. The reader, window, boundaries and evaluated frames are unchanged;
   the frames are those nearest the old times (3.2e-5 and 2.3e-5 later and earlier, one fine step).
   To reverse: set `trajectory: N120` and restore the test's foot positions and times from
   `checks/check_dmr_N120.txt`.

### Log entries

**2026-11-27, dataset agent (build-order step 18).**

- Converted the run (above), checked it against its source.
- Config `kinet_double_mach_reflection`; page; dynamics figures (`python -m fmeval.cards dynamics
  kinet_double_mach_reflection`: density, pressure, both velocity components at the three times).
- Test: `test_the_double_mach_window_reproduces_the_incident_shock_and_leaves_out_still_gas`
  (`data`, `tests/test_loader_contract.py`): the incident shock's foot on rows $y = 0.60$ to $0.90$
  at $t = 0.137$ and 0.2 equals the job's measured values (`checks/check_dmr_N120.txt`) to their four
  decimals, and the columns left out are still gas.
- Runs: `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/shocks2d_dmr_rmse`,
  `shocks2d_dmr_panel`, `shocks2d_dmr_persistence`; `shocks2d_dmr_persistence_w` was stopped.
- Not verified: the cause of the thin feature above the reflected shock; whether the solver's
  pattern converges to the inviscid one on finer grids (not run).

**2026-11-28, dataset agent (a finer run, under Kareem's resolution rule of 2026-11-27).**

- **What was run.** The same case and overrides on $960 \times 240$ cells (same viscosity 0.01,
  Prandtl number 0.71, initial and boundary data, end time 0.2), from a detached worktree of kinet
  `origin/main` at `e67a1136e` (the squash merge of `perf/cleanup`; the case differs only by the
  renamed key `face_pc.max_iterations`, and the composed configuration equals the archived one
  apart from the grid, the save cadence and `io.record_populations`, the new name of
  `io.record_distributions`). A debug test to $t = 0.03$ (job 62133981, 826 steps, 1.08 s per step)
  proved the configuration and the coarse graining; the full run (job 62134603, regular queue,
  one A100) took 5992 steps, 6555 s of stepping (1.094 s per step, the debug rate), 1 h 57 min of
  job time including both coarse grainings (111 s and 76 s), after 2 h 55 min in the queue. It saved
  every second step, 2997 frames, so that a frame lies within one step ($3.4 \times 10^{-5}$) of
  every saved time of the native run: the adaptive step differs between the grids (step 2000 of the
  fine run is at $t = 0.0692$, against 0.0708 at step 1000 of the native one).
- **Coarse graining**, by kinet's own operator as the job's last step: `python -m
  kinet.apps.coarse_grain task=coarse_grain <the run's overrides> '++task.targets_spatial=[480,120]'
  task.temporal_factor=1 task.vorticity=none task.ignore_datasets=[...]`, a block mean over $2 \times 2$
  cells with no time reduction (every saved frame kept as saved), no vorticity (the run stores
  none), and the visualisation copy, the relaxation times, the temperature and the specific
  energy left out; once more to $240 \times 60$ (factor 4). It accepts the adaptive-step file; it
  rewrites `discretization.temporal.length` to the slot count (5992), which no reader here uses,
  and keeps the clock `time/time` as it was.
- **Conversion.** `convert_kinet` gained `times` (`--times`, about ten lines, tested in
  `tests/test_loader_contract.py`): on an adaptive-step run it keeps the saved frame nearest each
  given time, since `--every` counts a fixed stride back from the last frame and could not reach
  both 0.0708 and 0.1368 on a run whose step differs from the native one (its best stride was off by
  $7.6 \times 10^{-4}$ and kept a fourth frame). `python -m fmeval.data.convert_kinet <480-120 tier>
  <dest>/N240_coarse-480-120.h5 --times 0.07080358 0.13676752 0.2` wrote
  `/global/cfs/cdirs/m4790/Data/kinet/double_mach_reflection/compressible_fluids/Pr-71en2_vuy-1.4_visc-1en2/N240_coarse-480-120.h5`
  (7 402 264 bytes): the initial condition and steps 2050, 4054, 5992 at $t = 0.070835$, 0.136744,
  0.2, density, velocity and absolute pressure; checked equal to its source in every kept frame,
  field and clock, all finite. No config reads it.
- **Measured, at the stored resolution** (`checks/check_dmr_N240.txt`, `compare_N120_vs_N240cg_480x120.txt`,
  `compare_N120cg_vs_N240cg_240x60.txt`, `diagnostics_N240_full960x240_at_N120_times.txt` under the
  archive's `shocks_2d/`), native run against the coarse-grained finer run at the three stored
  times:

  | Quantity | native $480 \times 120$ | $960 \times 240$ to $480 \times 120$ | $960 \times 240$ to $240 \times 60$ |
  |---|---|---|---|
  | Smallest density, pressure at the stored frames | 0.837, 0.996 (at $t = 0.137$) | 1.400, 1.000 | 1.400, 1.000 |
  | The same over every saved frame | 0.455, 0.535 (31 frames, 5 below 99 % of ambient) | 1.226, 1.000 (2997 frames, 12 below) | 1.400, 1.000 (none below) |
  | Incident shock behind Eq. (1), rows 0.6 to 0.9, stored cells | 1.39 to 2.21 | 0.75 to 1.16 | 0.29 to 0.62 |
  | Its 10 %-to-90 % width, stored cells | 1.66 to 2.83 | 1.40 to 1.78 | 0.97 to 1.60 |
  | Relative L2 difference from the next coarser run, density / pressure / velocity | — | 3.7, 2.8, 2.5 % / 4.8, 3.6, 3.3 % / 4.1, 3.5, 3.5 % | 3.0, 2.3, 2.1 % / 4.0, 2.9, 2.7 % / 3.4, 2.8, 3.0 % |
  | Band left where the initial shock stood (the thin feature), row $y = 0.6$ at $t = 0.2$: peak above 8, width | 5.6 %, 0.133 | 3.3 %, 0.092 | 3.1 %, 0.100 |
  | Band trailing the incident shock, same row and time | 8.5 %, 0.133 | 4.8 %, 0.100 | 4.6 %, 0.100 |
  | RMS of $\lvert\rho - 8\rvert / 8$ between the reflected and the incident shock, $t = 0.2$ | 1.42 % | 0.77 % | 0.62 % |

  The coarser-run columns at $240 \times 60$ compare the native run block-averaged by 2 with the
  finer run block-averaged by 4. Read on the native $960 \times 240$ grid, the incident shock lags by
  1.5 to 2.4 of its own cells with a width of 1.9 to 2.4 of them, the same count of cells as the
  native $480 \times 120$ run: the lag and the width are set by the cell, a first-order numerical
  error that halves in length with each refinement. On that grid 878 of the 2997 saved frames fall more
  than 1 % below the ambient density or pressure (down to 0.354 and 0.154), 659 of them with one
  to three cells below a density of 1.3, and 81 of a sample of 91 such cells sit within 1.5 cells of the exact incident shock
  (`checks/dip_locations_N240_full960x240.txt`): an intermittent undershoot at the foot of the
  Mach-10 front that refinement does not remove and the block mean dilutes.
- **The thin feature** is the upper end of a band of excess density left where the initial
  discontinuity stood: in the native run's density at $t = 0.024$ to 0.15 a band parallel to the
  incident shock starts at the shock's initial position and moves with the post-shock gas, and
  its top end, cut off by the reflected shock, is the sliver above it at $t = 0.2$ (measured on the
  frames; that it is the start-up error of a shock begun as a sharp discontinuity is my reading,
  not checked against a source). On the finer run it remains, at 0.58 of the amplitude, 0.69 of the
  physical width across the row, so it neither vanished nor thinned in proportion to the cell; at
  the 30 contour levels of the job's plot it no longer shows, because 3.3 % lies within one level
  spacing of 8. The band trailing the incident shock, which meets the top face, behaves alike.
- **Verdict** (decision 6): not free of numerical artifacts at $480 \times 120$, nor at $240 \times 60$;
  the dataset is unchanged, and the native file stays its source.
- **What would meet the criterion, and its cost.** The run already ends at the last time the
  dataset reads ($t = 0.2$), and the regular queue ran at the debug rate, so neither saves time. A
  $1920 \times 480$ run would take about 12 000 steps (the step halves with the cell): 32 GPU-hours
  at the 9.7 s per step of the 31-step throughput run (`checks/timings.txt`, three progress windows,
  rising), or 15 at the per-cell rate this run measured (my arithmetic, not measured). Extrapolating
  the measured halving (an inference), it would bring the lag at $480 \times 120$ to about 0.5 cells
  and the width near 1.3, but the bands only to about 2 % and 3 %, still above (d); bands this
  persistent suggest the set-up (a sharp initial discontinuity, the imposed top shock) rather
  than the resolution (my inference; Kemm (2014) studies how this test's set-up shapes its solution
  and was not read for this point), and changing the set-up changes the problem, so it is the
  owner's call. Recorded in issue 151.
- **Deleted on Kareem's instruction of 2026-11-27** ("after you downsample you should delete the
  fine grid simulation when you are finished with it"), on 2026-11-28 once the checks above were
  saved as text: the $960 \times 240$ rollout `.../double_mach_reflection/default/2d3f49f5/tiers/full/rollout.h5`
  (49 729 181 006 bytes, with its hard link `rollout.vtkhdf`), the debug run's rollout
  (1 402 897 593 bytes, the same twice) and its two trial coarse-grained tiers (1.5 GB, 0.4 GB), and a
  trial coarse-grained file (3.4 GB). The archived configuration and command regenerate every one
  (`docs/datasets/logs/kinet_runs/shocks_2d/dmr_N240_t0p2/`). Kept on scratch until it is purged:
  the run's coarse-grained tiers `tiers/480-120/rollout.h5` (11.0 GB) and `tiers/240-60/rollout.h5`
  (2.8 GB), every saved frame on the stored grids, and the native run block-averaged to
  $240 \times 60$ under the work folder (1.4 GB).
- **The native file is now** the coarser run of a two-grid pair of the same problem, and still the
  dataset's source; `N240_coarse-480-120.h5` is the finer run on the same grid at the same times.
- Not verified: the band's cause; whether $1920 \times 480$ follows the projection; the shock
  thickness estimate in decision 6 against a computed viscous profile.

**2026-11-28, dataset agent (decision 7: the coarse-grained finer run becomes the stored field).**

- Config `kinet_double_mach_reflection`: `trajectory: N240_coarse-480-120`, the header comment
  saying which file is read, how it was made (the coarse-graining and conversion commands) and
  what remains in it, the remeasured face facts, and `complexity.label`; reader, window,
  boundaries and `time.start` unchanged.
- Remeasured on the new file (login node, the repository's `.venv`): the times 0.070835, 0.136744,
  0.2; the incident shock's foot on rows 72, 84, 96, 108 at the last two frames (2.0876, 2.1441,
  2.2003, 2.2582 and 2.8169, 2.8737, 2.9314, 2.9884, equal to `checks/check_dmr_N240.txt`), now pinned by
  `test_the_double_mach_window_reproduces_the_incident_shock_and_leaves_out_still_gas`; beyond
  $x = 3.2$ the pre-shock state to $2.3 \times 10^{-16}$ at every kept frame; the first three columns
  the inflow state to $3.2 \times 10^{-14}$ (density, velocity) and $4.3 \times 10^{-13}$ (pressure);
  the wall-normal velocity in the row next to the wall at most 0.64 against 4.7 in the window; the
  Mach stem's foot at 0.169, 1.079, 2.761 at $t = 0$, 0.071, 0.2.
- Not remeasured: the calibration scales, the shock detector's cell counts and the evaluation
  costs, which need an evaluation run, and every metric card's runs on this dataset. All were
  made on the native file; the page and the cards' config say so, and the owner's evidence step
  will replace them.
- Page rewritten for the new stored field: what it is, the block mean as part of its definition,
  what remains at the stored resolution and which metric readings it affects. Dynamics figures
  redrawn (`python -m fmeval.cards dynamics kinet_double_mach_reflection`); `python -m fmeval.cards
  catalog` rerun, with no change to `docs/catalog.json`. Issue 151 describes the dataset as it now
  is; the comment on this dataset in `configs/cards/default.yaml` says the cards' runs predate the
  change; the datasets index row and the run archive's README say which file is read.
- Deleted from scratch once the dataset read its file from CFS and every comparison was saved as
  text (Kareem's instruction of 2026-11-27): the coarse-grained tiers
  `.../2d3f49f5/tiers/480-120/rollout.h5` (11 048 693 464 bytes) and `tiers/240-60/rollout.h5`
  (2 763 322 264 bytes), and the native run block-averaged to $240 \times 60$ under
  `_work/shocks_2d/dmr_fine/old_to_240x60/` (1 368 640 616 bytes). The archived commands regenerate
  them.

### Open points

- The stored field carries numerical artifacts the finer run halved but did not remove (decisions
  6 and 7; issue 151).
- The calibration scales, the detector's cell counts and the costs above, and every metric card's
  run on this dataset, were measured on the native file; they describe it until the evaluation is
  rerun on the present one (the owner's evidence step).
- Every frame of either run is reproducible from the archived configurations and commands; the
  native raw run is on scratch until about eight weeks after 2026-11-27.
- `persistence_wasserstein` does not finish a frame (issue 144).
- The non-square window makes the spectral degradations' cutoffs anisotropic (issue 046).
