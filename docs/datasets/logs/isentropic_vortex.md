# Log: isentropic vortex

The page is `docs/datasets/isentropic_vortex.md`. Two configurations share the fragment
`configs/dataset/_kinet_isentropic_vortex.yaml`.

## `kinet_isentropic_vortex_mu1em5` and `kinet_isentropic_vortex_mu1em7` (2026-11-27)

### What they are for

A smooth compressible solution with an exact answer at every time, run by a solver on a grid
sequence, so that its observed order of accuracy can be read and every metric's response to a
discretisation error that falls as the square of the cell measured
(`dataset_specs/02_grid_refinement_known_solution.md`, Sect. 4.2, ideal (ii); build-order step 18).
It is the compressible companion of the Taylor–Green sequences: density and pressure vary, and the
error is carried by a moving vortex rather than a decaying standing pattern.

### How they are treated

- **Source.** kinet's case `isentropic_vortex/default`, run on 2026-11-27 by the job agent on the
  GPU debug queue (kinet `perf/cleanup` at `d1cd353b83e9`, no uncommitted changes, one A100, torch
  2.15.0): $64^2$, $128^2$, $256^2$ to $t = 10$ at the case's dynamic viscosity $10^{-5}$ (job
  62108080), $512^2$ to $t = 2.5$ at $10^{-5}$ (job 62114361), and $256^2$ and $512^2$ to $t = 2.5$
  at $10^{-7}$ (job 62115657). Records, configurations, commands and the job's checks:
  `docs/datasets/logs/kinet_runs/shocks_2d/` and that README's section on it.
- **Conversion.** `fmeval.data.convert_kinet.convert_kinet_grouped(<rollout>, <dest>, every)` from
  `/pscratch/sd/k/khegazy/kinet_datasets/shocks_2d/isentropic_vortex/isentropic_vortex/default/<key>/tiers/full/rollout.h5`
  to `/global/cfs/cdirs/m4790/Data/kinet/isentropic_vortex/compressible_fluids/Pr-71en2_vuy-1.4_visc-1en5/N64.h5`
  (`b88b17ce`, 0.3 MB), `N128.h5` (`beb1465e`, 1.1 MB), `N256.h5` (`3ef597e9`, 4.2 MB), with
  `every=41`, and `.../Pr-71en2_vuy-1.4_visc-1en7/N256.h5` (`cdbfed4c`, 4.2 MB) and `N512.h5`
  (`67d186ad`, 16.8 MB) with `every=11`: the initial condition and the last frame, nothing else
  (26.6 MB). Fields density, velocity and the absolute pressure (`pressure_convention:
  absolute`); the `mesoscopic/` relaxation-time fields, the temperature and the specific energy are
  not carried. Each file was checked equal to its rollout's slot, field by field, and on the clock.
- **The converter's change.** The PonD solver's step is adaptive, so the saved steps are 1, every
  Nth, and the last step, which lands on the end time and is off the cadence; the converter refused
  such a run ("not evenly spaced"), crashed on the missing `discretization.temporal.resolution`,
  and would have carried `time_convection` ($\sqrt\gamma/10$ times the physical time here) as the
  clock. Now a run with `temporal.type == "adaptive"` keeps its physical `time/time`, skips the
  evenness requirement and the resolution, and `every` keeps the last saved frame and every Nth
  before it (on a fixed-step run, where `every` must divide the count, the same frames as before).
  About eight changed lines, tested on an adaptive fixture.
- **Reader.** A registered format `isentropic_vortex_kinet` (`IsentropicVortexKinet` in
  `fmeval/data/analytic.py`, about 45 lines of code beside its docstring), a `ClosedFormTrajectory`
  in the Taylor–Green pattern: the exact vortex on the run's cells and clock with the run's
  $\gamma$, the run from `predictions()`. No existing reader computes this solution (the
  `advecting_blobs` vortices are incompressible and carry no thermodynamics), so the formula is new.
  The vortex's parameters are a class constant, kinet's default case, checked against the run's
  stored initial condition.
- **Grid and boundaries.** Native $N^2$ on $[0, 10]^2$, cell $i$ at $(i + \tfrac12)\,10/N$, both axes
  `periodic`, as the run's `boundary_conditions` attribute states.

### What part is evaluated

- **Kept:** the last frame of every run, at its native resolution: $t = 10$ on $64^2$ to $256^2$ at
  $\mu = 10^{-5}$, $t = 2.5$ on $256^2$ and $512^2$ at $\mu = 10^{-7}$ (`time: {start: 1}` over the
  two stored frames).
- **Why only the end time.** The solver's adaptive step saves the grids' frames at nearby but
  different times (2.47998 on $64^2$ against 2.47833 on $128^2$), and `observed_order` pairs grids
  at equal times only, so the end time, which every grid lands on, is the one time an order can be
  read (issue 149 holds the alternatives). It is also the time the field reports: the error after
  one period (Spiegel et al. 2015, Fig. 2). Frame 0 is the exact initial condition to
  $4.4 \times 10^{-16}$, an error of round-off with no order to read.
- **Enough for the measurement.** The rows are a deterministic error, not samples; one time gives
  each metric and field one order per pair of grids (two pairs at $\mu = 10^{-5}$, one at
  $10^{-7}$). In the job's check at $\mu = 10^{-5}$ the rms orders lie between 1.84 and 2.12 at
  $t \approx 2.5$ and 5 and between 1.77 and 2.13 at 10 (`checks/check_vortex.txt`), so the end
  time is not an outlier.
- **No analysis grid, exclusion or slow metric.** A remap would add an error of its own; with a
  candidate the ladder is replaced by the clean entry and `mean_field`.
- **Measured cost** (login node, 2026-11-27, one `evaluate.py` per run): `rmse` and `max_error`
  2.7 to 2.9 s wall on every grid; every deterministic metric but `persistence_wasserstein` (30
  requested, 28 of which run; `enstrophy` and `palinstrophy` need the vorticity these
  configurations do not list), 7.8 s wall on $64^2$ and 25.2 s on $512^2$, of which 13.9 s is metric
  time (`spectral_energy_flux` 5.6 s, `energy_distance` 2.8 s, `wasserstein` 1.6 s,
  `persistence_distance` 1.4 s); `persistence_wasserstein` 1.4 s of metric time on $512^2$ (3.8 s
  wall). The whole panel on both sequences is about two minutes (my arithmetic). Disk 26.6 MB,
  all read.

### Decisions and why

1. **Which runs** (agent). In: $64^2$, $128^2$, $256^2$ at $\mu = 10^{-5}$ (orders 1.7 to 2.4 at
   $t = 10$), and $256^2$, $512^2$ at $\mu = 10^{-7}$ (1.94 to 2.00 at $t = 2.5$). Out: $512^2$ at
   $\mu = 10^{-5}$. Its end time, 2.5, is no saved time of the $256^2$ run at that viscosity, so no
   order can be read with it here; and against that run's frame at 2.47789 its order is 0.9 to 1.6
   (the job's check), the viscous decay of the run against an inviscid exact solution, which the
   $\mu = 10^{-7}$ rerun of the same pair removes. Alternative: keep it as a third configuration of
   one run showing the floor, as the fixed-Mach Taylor–Green sequence shows one; rejected because it
   pairs with nothing. To reverse: convert `51b8cbdc` with `every=11` and pair it by hand.
2. **Two configurations, not one** (agent). The two viscosities have different end times and
   share no time, so they are two sequences, each read by `observed_order` alone.
3. **The exact solution is inviscid** (agent). The literature's exact solution is the translated
   initial field (Spiegel et al. 2015, Sect. IV.B.1); a viscous vortex has no closed form with these
   thermodynamics. The run's viscosity is not read; the $\mu = 10^{-7}$ sequence shows the scheme's
   order where the mismatch is negligible.
4. **The strength convention** (agent). kinet's $\beta$ is in units of the isothermal sound speed
   $\sqrt{p_\infty/\rho_\infty}$, Spiegel et al.'s $\beta_S$ in units of $a_\infty =
   \sqrt{\gamma p_\infty/\rho_\infty}$ multiplying $e^{-r^2/2}$; $\beta_S = \beta e^{1/2}/(2\pi\sqrt\gamma)$
   (my conversion), and their Table 1's Shu row is $\beta = 5$. The reader uses kinet's form, so its
   check against the stored initial condition is direct; the synthetic test writes the run in
   Spiegel's form, so the conversion is tested, not assumed.
5. **Parameters as a class constant, refused if the run differs** (agent). Reader options for the
   strength, radius, centre and flow would add plumbing no run needs; the initial-condition check
   (1e-12) refuses a run of other parameters rather than scoring it against the wrong vortex. To
   reverse: make `VORTEX`'s entries constructor keywords.
6. **Registered as grid sequences** (agent), as the Taylor–Green and Sod sequences are; labels in
   `configs/cards/default.yaml` say one time per run.

### Log entries

**2026-11-27, dataset agent (build-order step 18).**

- Converted the five runs (above), checked each against its source.
- Code: `convert_kinet` (adaptive runs), `IsentropicVortexKinet`; tests
  `test_a_kinet_isentropic_vortex_run_is_read_on_its_cells_and_clock_in_the_case_units`,
  `test_the_isentropic_vortex_solves_the_euler_equations`,
  `test_a_kinet_isentropic_vortex_pairing_refuses_another_run`, the `data` test
  `test_the_kinet_isentropic_vortex_reproduces_the_jobs_errors_and_orders` in
  `tests/test_analytic_datasets.py`, and
  `test_an_adaptive_rollout_keeps_its_physical_clock_and_its_last_step` in
  `tests/test_loader_contract.py`.
- Verified: the reader's exact solution against the run at $t = 10$ on $64^2$ gives the job's rms
  errors (density $7.6375 \times 10^{-4}$, pressure $9.6106 \times 10^{-4}$) and maxima to their
  printed digits; through `evaluate.py` and `observed_order` (runs under
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/shocks2d_vortex_*`), `rmse` orders
  at $t = 10$: density 2.000 and 1.900, pressure 1.964 and 1.774, velocity 2.039 and 1.906; at
  $\mu = 10^{-7}$, $t = 2.5$: 1.958, 1.937, 1.992; `max_error` 1.699 to 2.364 and 1.988 to 1.998. The
  density and pressure orders equal the job's (`check_vortex.txt`, `check_vortex_mu1em7.txt`) to
  three decimals. The Euler residual of the closed form falls by 3.96 to 3.97 when the cells halve.
- Not verified: Shu's report, which kinet cites for its formula, was not opened; the formula is
  checked against Spiegel et al.'s Eqs. 20 to 23 and Table 1 (read 2026-11-27 from the NASA
  technical report server copy) and against the runs' initial conditions.

### Open points

- Only the end time is evaluated (issue 149). The raw runs, with every saved frame, are on scratch
  until it is purged, about eight weeks after 2026-11-27; every run is reproducible from the
  archived configuration and command.
- No dynamics figure: each configuration evaluates one frame per run.
- The drop of the $\mu = 10^{-5}$ order from 2.00 to 1.90 between the two coarser pairs is read as the
  viscous error appearing on $256^2$; not tested by a run at $\mu = 10^{-7}$ on $64^2$ and $128^2$.
