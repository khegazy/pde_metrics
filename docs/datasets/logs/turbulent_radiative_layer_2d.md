# Log: turbulent radiative mixing layer

This log records why the dataset on
[`turbulent_radiative_layer_2d.md`](../turbulent_radiative_layer_2d.md) is in its current form.
It follows step 7 of `docs/recipes/add-a-dataset.md`. Append new entries at the end, and never
rewrite an old one; supersede it with a new entry instead.

Where a decision is attributed to Kareem, the source is a dated decision in
`dataset_specs/BUILD_ORDER.md` or a message he sent through the coordinating session. Where it
is attributed to an agent, no person reviewed it before it was carried out.

## `well_radiative_layer_tcool0p32`

### What it is for

- **No test of an existing metric needs this dataset** (Kareem, raised after the work below
  was done). It was built as a by-product of the first item of step 27 of
  `dataset_specs/BUILD_ORDER.md`, which comes from specification 11
  (`dataset_specs/11_regime_data.md`, regime data). That specification serves issues 089
  (wall-bounded flow), 090 (variable-density mixing) and 091 (scalar and reacting mixing), all
  for metrics that exist only as ideas under `docs/ideas/regime_specific/`.
- The target of that item was The Well's `rayleigh_benard` set, for no-slip walls and an
  active scalar. Specification 11 Sect. 7 noted that the same reader change also makes
  `turbulent_radiative_layer_2D` readable: periodic in $x$, zero-gradient in $y$, with a
  stored pressure that is not a function of density. Rayleigh–Bénard turned out not to be
  readable on a uniform grid (see the decisions below), so this is the only dataset the item
  produced.
- **Further Well work is paused, and whether the reader change stays is Kareem's call.** The
  dataset is not registered as evidence in `configs/cards/default.yaml`.

### How it is treated

- **Source.** `${paths.data}/well/datasets/turbulent_radiative_layer_2D/data/test/turbulent_radiative_layer_tcool_0.32.hdf5`,
  that is `/global/cfs/cdirs/m4790/Data/well/datasets/...`, read in place and never converted
  or copied. It is the published test split of The Well (Ohana et al. 2024,
  <https://arxiv.org/abs/2412.00568>). The Well's page for the set
  (<https://polymathic-ai.org/the_well/datasets/turbulent_radiative_layer_2D/>, read
  2026-11-26) states the solver, Athena++; the source paper, Fielding et al. (2020),
  *Astrophys. J. Lett.* 894, L24; the compressible Euler equations with the energy sink
  $-E/t_\mathrm{cool}$ and $\gamma = 5/3$; the domain $[-0.5, 0.5] \times [-1, 2]$; periodic
  $x$ and zero-gradient $y$; and nine cooling times from 0.03 to 3.16 with ten seeds each.
  The test-split file holds one trajectory.
- **Reader.** The existing `well` reader (`fmeval/data/well.py`), with
  `include_redundant: true` and `coordinates_span_domain: true`.
- **Fields.** `density`, `velocity` and `pressure` are kept. The pressure is the solver's own,
  so the default that drops it (written for the isothermal kinet pressure) is turned off.
  `vorticity` is dropped because the spectral curl refuses a grid that is not periodic.
- **Grid.** $128 \times 384$ cells of size $1/128$ on both axes, float32 cast to float64 on read.
- **Boundaries.** $x$ is `periodic`. $y$ is declared `OPEN` in the file and read as `neumann`.
- **Time.** 101 frames from $t = 0$ to 159.7, saved every 1.597. The window starts at frame 50,
  with stride 1 (the schema's default).

### Decisions and why

#### Wall and open boundaries become `neumann`, and an unknown type is refused

- **Decision.** The reader reads the `bc_type` and `associated_dims` attributes of every
  `boundary_conditions/*` group and maps `PERIODIC` to `periodic`, and both `WALL` and `OPEN`
  to `neumann`, through the module constant `BOUNDARY_MAP`. A type the map lacks, or an axis no
  group names, raises `ValueError`. Before this change the reader refused every axis without a
  `<dim>_periodic` group.
- **Who.** The mapping was proposed by specification 11 (Sect. 3.6 and 10). Mapping no-slip
  walls to `neumann` with no odd extension is the default of open decision 1 in
  `dataset_specs/BUILD_ORDER.md`, which Kareem has not yet settled. An agent implemented it.
- **Why.** `fmeval/data/base.py` `BOUNDARIES` holds only `periodic` and `neumann`, and an open
  (zero-gradient outflow) face is exactly the even extension `neumann` describes. Refusing an
  unknown type keeps the reader from guessing.
- **Alternatives.** A per-field odd extension of the velocity at a no-slip wall (about 15 lines
  in `GridSpec.extend` and `fmeval/ladder.py`, spec 11 Sect. 3.6). It matters only for walls,
  not for this dataset's open faces, and it changes what a boundary type means, so it is
  Kareem's decision.
- **To reverse.** Remove `WALL` and `OPEN` from `BOUNDARY_MAP`. This dataset then becomes
  unreadable.

#### The `coordinates_span_domain` option, off by default

- **Finding.** In both `turbulent_radiative_layer_2D` and `rayleigh_benard`, the coordinate
  arrays run from each domain bound to the other inclusive. For example, $x$ holds 128 points
  from $-0.5$ to $0.5$. The last periodic column is not a copy of the first: the difference
  between them is the size of an ordinary neighbour difference (checked on frames 50 and 100
  of this file, and frames 0, 100 and 199 of a Rayleigh–Bénard file). So $N$ cells span the
  length $c_{N-1} - c_0$, and the cell size is $(c_{N-1} - c_0)/N$. Here that gives square cells
  of $1/128$ on both axes, against the unequal $1/127$ and $3/383$ that the step between
  coordinates gives.
- **Decision.** A reader option `coordinates_span_domain` takes the cell size as span / $N$. It
  is off by default, so the default takes the step between coordinates. The reader also now
  refuses a coordinate array whose steps are not uniform to a relative $10^{-4}$.
- **Who.** An agent.
- **Why off by default.** The repository's own Well-format file (`well_re5e4`) stores
  coordinates $0, 1, \ldots, N-1$, whose step is the true cell size. Turning the new rule on for
  every file would change that dataset's spacing. No attribute in either kind of file tells the
  two conventions apart, so the configuration states it.
- **Alternatives.** Changing the default (breaks `well_re5e4` and its tests), or leaving the
  0.8% error in $x$ and 0.3% in $y$ (the cells would not be square, and every wavenumber would
  be slightly off).
- **To reverse.** Remove the option from the configuration; the spacing then follows the step.

#### Cooling time 0.32

- **Decision.** The one configuration reads the file at $t_\mathrm{cool} = 0.32$.
- **Who.** An agent.
- **Why.** It is the middle of the nine published values, which are evenly spaced in the
  logarithm. Nothing in the repository yet asks for a particular cooling time.
- **To reverse or extend.** Every other published value is reached with
  `dataset.trajectory=turbulent_radiative_layer_tcool_<value>` plus the matching `complexity`
  parameter. A second configuration would justify a shared fragment.

#### The window starts at frame 50, awaiting Kareem's confirmation

- **Decision.** `time.start: 50` ($t \approx 80$).
- **Who.** An agent proposed it. Step 3 of `docs/recipes/add-a-dataset.md` makes the window a
  person's decision, and **Kareem has not yet confirmed it**.
- **Why.** Up to frame 50 the fraction of cells at intermediate density ($2 < \rho < 50$) grows
  from 0.003 to 0.045, and the rms vertical velocity from 0.005 to 0.030. After frame 50 both
  fluctuate, about 0.03 and 0.025, with no trend to the end of the run. These two numbers were
  measured every fifth frame of this one file.
- **To reverse.** Change or remove `time.start` in the configuration.

#### Rayleigh–Bénard was refused, because its rows lie on Chebyshev nodes

- **Finding.** The `rayleigh_benard` file has a uniform `y` array from 0 to 1, but its rows lie
  on the Gauss–Chebyshev nodes $y_j = \tfrac12\big(1 - \cos(\pi(j + \tfrac12)/128)\big)$,
  interior points only. The Well's page says so ("Sampled at Chebyshev nodes along the y axis").
  Two measurements on the files confirm it. Near the walls the mean vertical heat flux, which
  must be the same at every height, is constant to 0.3% over the first thirteen rows on those
  nodes, but varies by a factor of 13 on the stored uniform coordinate (Ra $10^6$, Pr 1). The
  first row's mean buoyancy is not the wall value 1, as a wall row would be, but exactly what
  the wall gradient gives at the first Gauss node. Spec 11 Sect. 3.3 has the full numbers.
- **Decision.** No `rayleigh_benard` configuration was built.
- **Who.** An agent, following the task brief's instruction to report a Chebyshev grid rather
  than hide it.
- **Why.** `GridSpec` holds one spacing per axis. Reading the rows as uniform would misplace
  every row, and most of all those inside the thin wall layers the set was chosen for.
- **The two ways forward.** (1) Use The Well's `rayleigh_benard_uniform` set, which its page
  describes as the same data resampled to a uniform grid; it is not on disk, and its size and
  its resampling method were not checked. (2) Write a conversion that interpolates the
  Chebyshev rows onto a uniform grid and records the interpolant, as spec 11 Sect. 2 requires.
- **Pinned.** The data-marked test
  `test_well_rayleigh_benard_rows_are_not_on_its_uniform_y_coordinate` checks the near-wall
  signature, so the finding cannot be lost silently.

#### Buoyancy is not mapped to `temperature` yet

- **Decision.** The Rayleigh–Bénard `buoyancy` field is not mapped, and no `scalar` entry was
  added to the field vocabulary.
- **Who.** An agent.
- **Why.** In this Boussinesq set, buoyancy is the nondimensional temperature: 1 on the hot
  bottom wall and 0 on the cold top one. The existing `temperature` entry would therefore fit,
  without a new `scalar` entry. But the Well reader excludes `temperature` by name as
  degenerate (constant in isothermal runs), and the field is useless until the grid is
  resolved, so the choice was left for then.
- **To reverse.** Map `buoyancy` when Rayleigh–Bénard becomes readable, and decide then between
  `temperature` (which needs the degenerate-field exclusion to allow it) and a new entry.

#### The tests live in `tests/test_loader_contract.py`

- **Decision.** The reader's tests sit with the other Well-reader tests in
  `tests/test_loader_contract.py`. The fixture writer `write_well` in `tests/fixtures_h5.py`
  gained an argument `bc_types`, the `bc_type` of each axis, or None to leave an axis undeclared.
- **Who.** Kareem's rule that tests extend existing files rather than add parallel ones,
  applied by the coordinating session once step 4 released those two files.
- **Why.** At first the tests were written in a separate file, `tests/test_well_boundaries.py`,
  because another agent was editing both files. That file was deleted when they were moved.

### What part is evaluated

This section supersedes the window and stride stated under "How it is treated". The rule is
step 3 of `docs/recipes/add-a-dataset.md` (Kareem, 2026-11-26). An agent made the choices below,
using only the existing selectors, and a person may override them. No test of an existing metric
needs this dataset, so the choice was kept light.

- **Window: frames 50 to 100** ($t = 80$ to 159.7). This is the developed part of the run, by the
  two measurements under "The window starts at frame 50". The transient before it is dropped.
  Kareem has still to confirm the start.
- **Stride: 5** (`time.reduction: 5`), giving 11 frames: 50, 55, ..., 100. The integrated
  autocorrelation time of the per-frame `mse` values, over all 51 frames of the window and
  every non-degenerate degradation and severity level, has a median of 5.1 frames with a
  Bartlett window of 10 (quartiles 2.9 and 6.7), and 5.5 with a window of 20. The step between
  neighbouring severity levels gives 4.7 with either window. By field the medians are 4.0 for
  density, 2.9 for velocity and 6.8 for pressure. So the 51 frames hold about 10 independent
  samples, and a stride of 5 keeps about all of them.
- **Trajectories: one**, the only one on disk. The test split holds one run per cooling time;
  the other seeds are in The Well's training and validation splits, which are not on disk.
- **Analysis grid: the native $128 \times 384$**, the schema's default, so nothing is set. The
  analysis grid is a top-level key, so a dataset config cannot set it anyway. The full panel
  costs about 4.5 times more per frame here than at $64 \times 192$, but the whole run stays a
  few minutes. Coarsening by two would halve the resolution of the small cold clumps and
  filaments that the mixing layer is about; on the coarse grid the calibrated scale of the
  pressure is only 7 cells.
- **Costs**, measured on the login node with no Slurm job and results in
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets`. These are the evaluation
  times that `evaluate.py` reports, which leave out about 2 to 3 s of start-up.

  | Run | Grid | Frames | Time | Per frame |
  |---|---|---|---|---|
  | `mse` | 64 | 51 | 26.3 s (23.5 s degrading) | 0.52 s |
  | `mse` | 128 | 51 | 71.6 s (67.1 s degrading) | 1.40 s |
  | `mse` | 128 | 11 (the chosen part) | 17.8 s | 1.6 s |
  | `persistence_distance` (density only) | 64 | 3 | 7.2 s (5.3 s in the metric) | 2.4 s |
  | `persistence_distance` (density only) | 128 | 3 | 22.9 s (19.7 s in the metric) | 7.6 s |
  | full non-ensemble panel | 64 | 2 | 12.4 s (10.0 s in metrics) | 6.2 s |
  | full non-ensemble panel | 128 | 2 | 53.4 s (48.0 s in metrics) | 26.7 s |

  The full non-ensemble panel is the 31 metrics with pairwise or single arity. Thirteen of them
  need a periodic domain and produce no rows here; the ensemble metrics do not apply. From these
  costs, the full panel on the 11 chosen frames at the native grid comes to about
  $11 \times 27 \approx 300$ s, or 5 minutes. Adding `mse` and the two persistence metrics
  alone gives about 15 s per frame, so the remaining cheap metrics and their overheads make up
  the other half of the measured 27 s.
- **Disk.** Nothing is stored; the file is read in place. A frame of density, pressure and both
  velocity components in float32 is $128 \times 384 \times 4 \times 4$ bytes, 0.79 MB, so the 11
  frames read 8.7 MB of the 79 MB file.

### Log entries

#### 2026-11-26: reader change and the first configuration (agent)

- **Done.**
  - `fmeval/data/well.py`: `BOUNDARY_MAP`, the boundary reading and refusals, the
    uniform-spacing check and the `coordinates_span_domain` option (+33 and −9 lines, about 18
    of them code).
  - `configs/dataset/well_radiative_layer_tcool0p32.yaml`; the page
    `docs/datasets/turbulent_radiative_layer_2d.md` and its row in `docs/datasets/README.md`;
    figures from `python -m fmeval.cards dynamics well_radiative_layer_tcool0p32` in
    `docs/datasets/_generated/`.
  - Spec 11 Sect. 3.3 records the two coordinate checks, and step 27's status in
    `dataset_specs/BUILD_ORDER.md` was updated.
  - Tests: Well files with a `WALL` or `OPEN` axis read as `neumann`; an unmapped
    (`SYMMETRIC`) or undeclared axis is refused; the coordinate option; a non-uniform
    coordinate is refused; and two data-marked tests that read the first frames of each real
    file. They were first written in `tests/test_well_boundaries.py` and later moved into
    `tests/test_loader_contract.py` (decision above).
- **Verified.**
  - A smoke run, `python evaluate.py 'metrics=[mse,spectrum_l2,wasserstein]' dataset=well_radiative_layer_tcool0p32 dataset.time.reduction=25 analysis_grid.resolution=64 paths.results=/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets`.
    The analysis grid of 64 works on this non-square grid (it becomes $64 \times 192$). `mse`
    ran on every degradation of the default ladder. `spectrum_l2` and `wasserstein` were
    skipped because they need a periodic domain.
  - The calibration resolved characteristic scales of 20 cells for density, 18 for velocity
    and 7 for pressure. Some severity levels were flagged as degenerate: the density high-pass
    and low-pass filters, and several smoothing levels on pressure.
  - After the move, `pytest tests/test_loader_contract.py` gave 80 passed;
    `pytest -m data -k well` gave 3 passed; the default `pytest` gave 2853 passed, 405 skipped
    and 4 expected failures.
- **Not verified.**
  - Whether the coordinate convention holds for Well sets other than these two.
  - The origin is still taken as the first coordinate. Whether Athena++ stores cell centres,
    which would put the true origin half a cell inward, was not checked; no metric reads the
    origin.
  - The window was measured on one file only.

#### 2026-11-26: what part is evaluated (agent)

- **Done.** Under the new step 3 of `docs/recipes/add-a-dataset.md`, chose frames 50 to 100,
  stride 5 (11 frames), one trajectory and the native grid. Added `time.reduction: 5` and the
  reasoning as comments in `configs/dataset/well_radiative_layer_tcool0p32.yaml`, and the
  section "What part is evaluated" above.
- **Verified.** Every number in that section was measured on the login node, as stated there.
  `python evaluate.py 'metrics=[mse]' dataset=well_radiative_layer_tcool0p32` selects 11 of
  101 frames.
- **Not verified.** The autocorrelation time was measured with `mse` only, on one file. The
  full-panel total for the 11 frames is a projection from a 2-frame run (see the next entries
  if it was measured).

#### 2026-11-26: stale test references fixed (coordinator)

The references to the deleted `tests/test_well_boundaries.py` in
`dataset_specs/11_regime_data.md` Sect. 3.3 and in step 27's status in
`dataset_specs/BUILD_ORDER.md`, listed under "Open points", were fixed by the coordinating
session on 2026-11-26. The tests are in `tests/test_loader_contract.py`.

### Open points

- Whether the reader change stays is Kareem's call, since no existing metric needs this dataset.
- The frame-50 window awaits Kareem's confirmation.
- Rayleigh–Bénard needs `rayleigh_benard_uniform` or an interpolating conversion before it can
  be configured. The buoyancy mapping waits on that.
- The odd extension of velocity at no-slip walls (open decision 1 in `BUILD_ORDER.md`) is
  unsettled. It does not affect this dataset, whose $y$ faces are open.
- The dataset is not registered as evidence, and it has no claim label.
- `dataset_specs/11_regime_data.md` Sect. 3.3 and step 27's status in
  `dataset_specs/BUILD_ORDER.md` still name the deleted `tests/test_well_boundaries.py`; the
  tests are now in `tests/test_loader_contract.py`.
