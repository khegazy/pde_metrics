# Log: viscous Burgers' equation (periodic, one-dimensional)

This log records why the `burgers` dataset is in its current form, for the next agent who
changes it. Its public page is `docs/datasets/burgers.md`. Entries are appended, never
rewritten.

## What the dataset is for

The pointwise norms come from numerical analysis, whose standard experiment is a scheme run on
a sequence of refined grids against an exact solution, with the observed order of accuracy
read from the errors (Roy 2005, Eq. 8). Nothing in the repository did this.
`dataset_specs/02_grid_refinement_known_solution.md`, Sect. 4.5, specified Burgers with the
Cole–Hopf solution, and its Sect. 6 put it first because it proves the observed-order path
with no solver. Build-order step 5 built it. Issue 126 holds the analysis-side computation.

## How it is treated

Nothing is stored. The reader `Burgers` (`fmeval/data/analytic.py`, registered as `burgers`)
is a `ClosedFormTrajectory` on the periodic $[0, 2\pi)$, one field, `velocity` (one channel on
a one-dimensional grid, as `sod_shock_tube` stores it). Options: `nu` (default 0.1), `scheme`
(`exact` or `central`), and the generic `grid`, `n_frames`, `t_start`, `t_end`, `candidate`.
The closed form is the Fourier–Bessel series of the page's Equation (2): the Cole–Hopf
transformation from Gesztesy and Holden (1998, Lemma 3.1, read on ar5iv), the Bessel
expansion from DLMF 10.35.2 (read); the series is spec 02's author's derivation, re-derived.
The configuration `configs/dataset/burgers.yaml` states nothing beyond the defaults.

## What part is evaluated

Decided by the agent on 2026-11-27 under step 3 of `docs/recipes/add-a-dataset.md`; Kareem may
override it. The frames are deterministic, so each is one known answer, not a sample.

- **Grid: 256 cells, native analysis grid.** The default ladder's largest translation is 16
  cells, a sixteenth of the domain; on 64 cells it would be a quarter. The grid sequence is not
  the default: it is four runs with `+dataset.reader.grid=[64],[128],[256],[512]`, each at its
  own resolution, since remapping onto a common grid would add a remap error to the order
  (spec 02, Sect. 3, rule 1). `analysis_grid.resolution` is left at its default, the native
  grid.
- **Window: 4 frames, $t = 0.5$, 1, 1.5, 2** (spec 02's 0.5, 1 and 2, evenly spaced). The front
  at $x = 0$ steepens through the window, and the error of the scheme peaks near $t = 1.5$.
- **Measured costs** on a Perlmutter login node, results under
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/burgers/`:
  - the 20 metrics that produce rows on a one-dimensional velocity, default ladder (86 of 91
    levels; `translate_y` has no y axis), all 4 frames: 14 s wall, 4.2 s of it in the pipeline
    (`ladder.log`); the slowest are `spectral_energy_flux` (1.7 s summed) and `tail_index`
    (0.17 s);
  - `rmse` and `max_error` against the scheme on 64, 128, 256 and 512 cells, one Hydra
    multirun of four jobs: 6.1 s wall (`sequence/run.log`).
  Nothing is stored, so no disk is used. The whole set is cheap, so it is kept whole.

## Decisions and why

1. **A new reader, not an option on an existing one** (agent). The existing one-dimensional
   reader is Sod's, an Euler solution on a bounded domain; none of the readers is a viscous
   scalar equation. The class is the constructor, one closed form and the scheme.
2. **The candidate is a numerical scheme on the reader's own cells, not the exact solution
   sampled differently** (agent; the task offered both). Sampling the exact solution as cell
   averages against point values gives order 2 too, but only the midpoint rule's, and tests no
   solver; a scheme gives numerical analysis's standard figure and is the degraded-solver
   candidate of `dataset_specs/05_initial_conditions_and_degraded_solver_runs.md` in miniature.
   It costs about the same code: one option, a right-hand side of two lines and one call to
   `scipy.integrate.solve_ivp`.
3. **Second-order centred differences in space, time integrated to tolerance** (agent). The
   method of lines with DOP853 at `rtol = 1e-10` makes the time error (7e-12 at $t = 2$ on 512
   cells, against a run at `rtol = 1e-13`) negligible against the spatial one (5e-5), so the
   observed order is the spatial order alone, without tying the time step to the grid.
   A first-order upwind scheme was not added: one known order proves the path, and a second
   scheme is a second option to maintain. It would be a one-line change of the flux.
4. **$\nu = 0.1$, refused below 0.05** (agent; $\nu = 0.1$ is spec 02's choice). The series
   cancels: its round-off grows as $\epsilon\,e^{1/\nu}$. Measured against $-\sin x$ at
   $t = 0$: 1.3e-12 at 0.1, 2.1e-8 at 0.05, 7e-4 at 0.03; against a heat-kernel quadrature of
   the same transformation at $t = 0.5$: 5e-13, 9e-9, 1e-3. Smaller viscosities need the
   integral form instead of the series. Reverse by lowering `MIN_NU` with an integral
   evaluation.
5. **60 Fourier modes** (agent). At $\nu = 0.05$, $I_{60}(10)/I_0(10) = 6 \times 10^{-44}$.
6. **The frames are computed per read** (agent). The scheme is integrated from $t = 0$ at
   every read (0.36 s to $t = 2$ on 512 cells), so `solution(time)` stays a function of time,
   as in every other reader, rather than caching frames.
7. **The observed order is computed in the test, not in the analysis** (agent, by
   instruction). See open point 1.

## Log entries

**2026-11-27, agent (build-order step 5).**

- Code: the reader `Burgers` in `fmeval/data/analytic.py`; `configs/dataset/burgers.yaml`;
  the page `docs/datasets/burgers.md` and its row in `docs/datasets/README.md`; the dynamics
  figure `docs/datasets/_generated/burgers.{png,json}`, drawn by
  `python -m fmeval.cards dynamics burgers`.
- Verified before the tests: Equation (2) against a direct quadrature of the Cole–Hopf
  heat-kernel integral at 16 points and $t = 0.5$, 1, 2 (largest difference 4.8e-13).
- Tests in `tests/test_analytic_datasets.py`: the start is $-\sin x$ (1e-11 at $\nu = 0.1$,
  1e-7 at 0.05); the residual of Equation (1) by centred differences on 512 and 1024 cells falls
  by 4 (measured 3.994 to 3.9995) at $t = 0.5$, 1, 2; the observed order of `rmse` and
  `max_error` through `pipeline.run` on 64 to 512 cells (measured 1.93 to 2.02, then within
  0.006 of 2; asserted 0.1 and 0.01); six refusals.
- Smoke runs, results above: the default-ladder panel and the grid-sequence multirun. Metrics
  without rows: `wasserstein` (density only), `persistence_distance` and
  `persistence_wasserstein` (density and vorticity), `enstrophy` and `palinstrophy`
  (vorticity, which a one-dimensional grid does not have), the six shock metrics (pressure), and
  every ensemble metric (one realisation). `increment_flatness` and `tail_index` give NaN on
  4 and 12 of 344 rows.
- Calibration (`data/calibration.csv` of the ladder run): characteristic scale 208 of 256
  cells, spread 0.11; half the energy at $k = 1$, 90% by 1.5, 99% by 3.9. So the ideal low-pass
  levels 3 and 4 repeat level 2, Butterworth low-pass level 4 repeats 3, both high-pass level 2
  repeats 1, ideal high-pass levels 1 and 2 and `coarsen_bandlimited` levels 1 and 2 change
  nothing. A property of a single steepening sine, not a fault.
- Not verified: Hopf (1950) and Cole (1951).

### 2026-11-27: registered as evidence (registration agent)

- **Registered:** `burgers` (`{periodic: true, ensemble: false}`) in `evidence_datasets` and
  `evidence_dataset_properties` of `configs/cards/default.yaml`. Kareem decided the rule on
  2026-11-26 (`dataset_specs/BUILD_ORDER.md`, "The task" and decision 9: every dataset built in
  that plan is an evaluation dataset, admitted to `evidence_datasets` with a label naming the
  kind of claim it supports); the agent chose the label.
- **Label** (completes "n frames of ..." in a card's run summary): "an analytic check: the exact
  Cole-Hopf solution of one-dimensional viscous Burgers' equation, a steepening front smoothed
  by viscosity, and nothing about turbulence".
- **Window:** the reader's defaults, kept whole: four frames, t = 0.5 to 2, on 256 cells at the
  native resolution. The grid sequence of the observed order is a multirun of overrides and
  stays so; nothing computes the order from rows yet (issue 126).
- **Not done:** no metric was run on it for a card; every metric card's *Across the experiments*
  table shows it as *not yet run* or *not applicable* with the reason (`python -m fmeval.cards
  catalog`). Producing that evidence is its own step in `BUILD_ORDER.md` and needs compute.

### 2026-11-27: the observed order computed by the analysis (step-32 agent)

- **What changed.** `fmeval.analysis.observed_order` takes the rows of the sequence's runs
  (`fmeval.io.load_runs` of the four folders) and returns p of Equation (4) per metric, field
  and time for each pair of successive grids, with `ratio` and `order_change`, the change of p
  from the next coarser pair, so the asymptotic range is read rather than assumed. The test of
  the central scheme now reads the order from it rather than computing it itself. `ROW_KEYS`
  did not gain `param_resolution`: the order is computed from the concatenated rows outside
  `analyse`, which still refuses them, now naming `observed_order`, because a grid sequence is
  not one sample.
- **Why, and who decided.** Framework limit 5 of `dataset_specs/BUILD_ORDER.md`, fixed in step
  32 under Kareem's approval of 2026-11-27 (decision 15); the design is this agent's.
- **Verified.** The test's assertions are unchanged and pass. A smoke multirun under
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/step32_smoke/burgers` read back
  from its four folders gives 1.93 to 2.02 on (64, 128), 1.997 to 2.005 on (128, 256) and 1.995
  to 2.001 on (256, 512), the values recorded above.
- **Supersedes** open point 1 and the line "nothing computes the order from rows yet" of the
  registration entry.

## Open points

1. No report section or card table shows the observed order; it is a function of the analysis
   that a caller reads.
2. A cell-average sampling option (the alternative of decision 2) and an upwind scheme are not
   built.
