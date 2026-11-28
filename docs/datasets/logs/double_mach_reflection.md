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

### Open points

- No grid sequence or resolution candidate: $960 \times 240$ and $1920 \times 480$ would need about 1.8
  and 32 hours of stepping (page). The raw run is on scratch until it is purged, about eight weeks
  after 2026-11-27; every frame of it is reproducible from the archived configuration and command.
- `persistence_wasserstein` does not finish a frame (issue 144).
- The non-square window makes the spectral degradations' cutoffs anisotropic (issue 046).
