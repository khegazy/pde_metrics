# How to use kinet to produce datasets for this repository

**Date:** 2026-11-26. **Author:** research sub-agent, from reading the kinet checkout at
`/global/u2/k/khegazy/projects/pde/kinet` (branch `main` plus the `changes_while_running_hit`
branch where noted), the kinet outputs on CFS and scratch, and this repository's readers. Every
claim names the file it was read in; "not found" means a search of the places named did not turn
it up, not that it does not exist.

**Verified by running on 2026-11-26** (second pass, same day): small examples were run with
kinet's own environment (`.venv`, unchanged) on the checkout as it stood, branch `perf/cleanup`
at commit `d1cd353b8`, on a Perlmutter login node (CPU, plus the node's A100 for a few runs).
Nothing was installed and the kinet tree was not modified. Every command in this guide is now
marked **executed (worked)**, **executed (failed: reason)** or **not executed**, all as of
2026-11-26, and every corrected claim cites the run directory under
`/pscratch/sd/k/khegazy/kinet_examples/` (written `$EX/` below) that shows it. The runs are
examples for understanding, not datasets. The table of checks is in "Verified by running
(2026-11-26)" before "Confidence".

**Scope.** kinet is used here only to simulate reference and candidate data for the metric
tests. Nothing in this guide trains or runs a machine-learning model.

**Every dataset run saves only the macroscopic observables:** add
`io.record_distributions=false io.record_equilibria=false` to every command (Kareem,
2026-11-26). Examples below that omit them were exploratory runs, not datasets.

## Read this first: three facts that decide what to do next

1. **The current kinet writes a different HDF5 layout from the one this repository reads.**
   `fmeval/data/kinet_raw.py` reads a *flat* file: datasets `density`, `velocity`, `F`, `time`
   at the root, each field `(N_sim, C, T+1, X, Y)` with the initial condition as frame 0. The
   kinet in the tree writes a *grouped* file: `observables/density`, `observables/velocity`,
   `mesoscopic/dists/F`, `time/time`, each field `(1, C, T, X, Y)` with the initial condition
   under `initial_conditions/` (`kinet/io/rollout/layout.py`, `kinet/io/rollout/contract.py`;
   verified on `/global/cfs/cdirs/m4790/Data/neurde/hit_scaling/Re-50k_Ma-1en1_2d/0171ae/tiers/256/rollout.h5`).
   The Sod and obstacle files already under `datasets/kinet/` are in the grouped layout too
   (Section 5). **Any new kinet run must be converted to the flat layout before a metric can
   read it**, because Kareem's decision (2026-11-26) is to keep the existing readers and fit the
   data to them (`BUILD_ORDER.md`, "How data reaches the metrics"). The conversion puts the
   fields back at the root, takes the clock from `time/time_convection`, and restores the initial
   condition from `initial_conditions/` as frame 0.
   *Verified by running:* a fresh run writes exactly this grouped layout (`$EX/c1/`, tree in
   Section 5), and `fmeval/data/kinet_raw.py` would refuse it because it looks for a root
   `time` dataset.
2. **About 300 independent realisations of decaying two-dimensional isotropic turbulence
   already exist**, at `/global/cfs/cdirs/m4790/Data/neurde/hit_scaling/`: 102, 102 and 103
   runs at Re 12.5k, 25k and 50k (Ma 0.1, `k0: 4`), every run with its own random seed, archived
   as a 256² tier of 1001 frames (every 10th coarse step) holding density, pressure, velocity and
   vorticity, 2.6 GB each, plus one long run per Reynolds number (Section 6c and Section 8 list
   what is and is not there). They were produced on 2026-11-06 to 11-08 with scripts that live
   only on the `changes_while_running_hit` branch (`REASONS_FOR_CHANGES.md` on that branch,
   "Context: what the campaign did"). This is the "unrelated realisations" data that
   `dataset_specs/01_physical_ensemble.md` asks for, already on disk.
3. **Three things the specs ask for are not in kinet as config:** a hook that perturbs an
   initial condition or starts a run from a stored frame, a large-scale linear drag or
   hypoviscosity for stationary two-dimensional turbulence, and a manufactured-solution source
   term (Section 8). The first is nevertheless possible **without changing kinet**: a short
   Python script outside the repository started a run from a stored frame plus a solenoidal
   perturbation and wrote a normal rollout file, and handing over the stored populations as
   well made the continuation bit-for-bit identical to the uninterrupted run (Section 6a,
   `$EX/c7/`).

## 1. What kinet is and what it can simulate

kinet is a PyTorch framework for kinetic-theory solvers (`README.md`, "What it is"). This
guide covers only its simulation apps, which are all that dataset creation uses. The acronyms used below:

- **LBM**, the lattice Boltzmann method: a collide-and-stream scheme on a fixed velocity set.
- **BGK**, the Bhatnagar–Gross–Krook collision: relaxation of the populations to an
  equilibrium at one rate; "entropic BGK" chooses that rate per cell to keep the entropy
  non-decreasing (`configs/collision/entropic_bgk.yaml`).
- **D2Q9, D3Q27, D1Q3, D2Q16, D3Q64**: velocity sets with D dimensions and Q discrete
  velocities (`configs/lattice/`).
- **DUGKS**, the discrete unified gas kinetic scheme, and **PonD**, Particles on Demand: the
  finite-volume family, where populations sit in a per-cell frame and move across faces by DUGKS
  fluxes or along characteristics (`README.md`, "Solvers"; `docs/particles-on-demand/ponds.qmd`).

### Physics (`configs/physics/`, `kinet/physics/`)

| `physics.type` | What it solves | Solvers and lattices | Source |
|---|---|---|---|
| `weakly_compressible_isothermal_fluids` | Weakly compressible isothermal Navier–Stokes, one population `F`; pressure is `rho * c_s^2` with `c_s^2 = 1/3` (`reference_temperature` attribute of every file) | LBM on D2Q9 and D3Q27; PonD finite volume | `README.md` "Physics" table; `docs/kinetic-theory/weakly-compressible.qmd` |
| `compressible_fluids` | Ideal gas with an energy population `G`, Prandtl number, heat transfer; stores a real pressure, temperature and energy | LBM on D1Q3 and D2Q9; PonD on D2Q16 and D3Q64 | same table; `configs/physics/compressible_fluids.yaml` |
| `acoustic` | Linear acoustics with multipole sources in a layered medium | LBM on D2Q9 | same table |
| `shallow_water` | Depth-averaged flow | LBM on D1Q3 and D2Q9; PonD | same table |
| `mhd` | Isothermal magnetohydrodynamics (Dellar 2002) | LBM on D2Q9 and D3Q27 | same table |
| `compressible_mhd` | Ideal compressible MHD | LBM on D2Q9; PonD on D2Q16 | same table |

### Solvers (`configs/solver/`)

`lbm` (collide and stream), `pond_dugks`, `pond_semi_lagrangian`, `pond_semi_lagrangian_tvd`
(finite volume with a CFL-chosen step). A PonD run states `solver.cfl` and runs to a
physical end time with an adaptive step (`simulations/README.md`, "Simulate entry point";
`kinet/simulation/run_from_config.py`, `_rollout_length`).

### Dimensions

2D and 3D for the LBM weakly compressible physics (`simulations/homogeneous_isotropic_turbulence/Re-50k_Ma-1en1_3d.yaml`,
`simulations/taylor_green_vortex/Re-1600_Ma-1en1_3d.yaml`);
1D and 2D for the LBM compressible physics (`simulations/sod/lbm_1d.yaml`,
`simulations/flow_around_objects/cylinder.yaml`); 1D, 2D and 3D for PonD
(`simulations/sod/default.yaml`, `oblique_riemann/default.yaml`, `sod/pond_3d.yaml`).

### Boundary conditions

The face types are the `type` literals in `kinet/config/common/boundary_conditions.py`:
`periodic`, `neuman` (spelled with one n in kinet), `wall`, `outflow`, `reflective`, `inlet`,
`convective_outflow`, `characteristic_outflow` (LODI and CBC variants), `riemann_outflow`,
`pressure_outlet`, `robin`, `fixed_state`, `fixed_velocity`, `fixed_strip`, `split`,
`moving_mach_shock`. An LBM face can carry an `absorbing` sponge of `width` cells and peak damping
`sigma_max` (same file, class `AbsorbingSponge`, line 91). Presets: `configs/boundary_conditions/`
(`periodic_1d/2d/3d`, `open_2d/3d`, `open_ends`, `inlet_neuman_2d`, `neuman_outflow`,
`dmr_pond`, `rmi_pond`, `sod_3d`). Obstacles: Bouzidi link walls, ghost-node walls, a continuum
immersed boundary shared by LBM and PonD, triangle meshes, moving bodies and a homogenized porous
medium (`README.md`, "Boundaries, obstacles and moving bodies"; `kinet/obstacles/`, `kinet/ibm/`).

### Forcing laws (`kinet/forcing/laws/`, registry in `kinet/forcing/registry.py`)

| `forcing_term.type` | What it is | File |
|---|---|---|
| `constant` | A uniform body force per unit mass, one component per axis | `laws/constant.py` |
| `linear` | Lundgren linear forcing `carrier * rate * (u - mean u)`; `rate_policy` in `constant`, `k_feedback`, `bassenne`, `component_bassenne`; `solenoidal: true` projects the force onto divergence-free modes each step; `rate` must be positive (`Field(gt=0.0)`) | `laws/linear.py`; `kinet/config/components/forcing.py` lines 50 to 116 |
| `random_modes` | Ornstein–Uhlenbeck random acceleration in the Fourier modes with integer index radius at most `maximum_mode`, projected solenoidal; keys `seed`, `correlation_time`, `variance`, `maximum_mode`; stateful, so it checkpoints | `laws/random_modes.py`; same config file |
| `uniform_energy` | A constant energy source, PonD compressible only | `laws/uniform_energy.py` |
| `darcy_forchheimer` | The drag of a homogenized porous medium on the porosity field of the case; the drag vanishes where the porosity is 1 | `laws/darcy_forchheimer.py` |
| `multipole_sources` | Time-harmonic mass, force and stress sources (acoustics) | `laws/multipole.py` |
| `sum` | Several of the above added | `laws/sum.py` |

**Not found:** a sinusoidal Kolmogorov body force, a linear large-scale drag (a negative linear
rate is refused by the config validator) and a hypoviscosity. The `kolmogorov` case group is the
double shear layer with `lambda: 30`, not a Kolmogorov flow
(`simulations/kolmogorov/initialize.py` registers `paint_double_shear_layer`). The LBM takes
`random_modes` only on the weakly compressible physics with the `polynomial` or `entropic`
equilibrium; the shipped forced cases
are 3D and the docs say they "do not claim ... 2D turbulence" (`docs/lattice-boltzmann/forcing.qmd`,
"Limits"; `docs/kinetic-theory/forcing-laws.qmd`, "Random low-mode forcing law").

### Initial conditions

A case's initial state is painted by a function registered with `@initializer("<case id>",
initial_conditions=<Model>)` in `simulations/<group>/initialize.py`; the model declares the
`initial_conditions` keys the case may state, and every block can also state the library scalars
`density`, `temperature`, `pressure`, `velocity`, `height`
(`kinet/initialization/hooks.py`; `kinet/config/components/initial_conditions.py`).

| Initial state | Keys | Defined in | Serves |
|---|---|---|---|
| Double shear layer: `u_x = U tanh(lambda (y - 1/4))` below `y = 1/2`, `U tanh(lambda (3/4 - y))` above, `u_y = epsilon U sin(2 pi (x + 1/4))`, on the unit square, Brown and Minion (1995) | `lambda` (steepness), `epsilon` | `kinet/initialization/shear_layer.py` | `doubly_periodic/shear_layer`, `kolmogorov/Re-50k_Ma-1en1` |
| Homogeneous isotropic turbulence: divergence-free velocity with a Passot–Pouquet spectrum `E(k) ∝ (k/k0)^4 exp(-2 (k/k0)^2)` by Rogallo random-phase synthesis, Poisson pressure, isothermal density, Skordos non-equilibrium seed | `k0` (peak mode, default 4), `random_seed` (default 42), optional `density`, `velocity` (total rms speed) | `simulations/homogeneous_isotropic_turbulence/initialize.py`, classes `HitIC`, `init_hit`, `fneq_hit` | `homogeneous_isotropic_turbulence/*`, and `hit_scaling/*` on the branch |
| Taylor–Green vortex, 2D and 3D, analytic velocity, pressure and non-equilibrium seed | `k` (mode number) | `simulations/taylor_green_vortex/initialize.py`, `init_tgv` | `taylor_green_vortex/*`, `testing/minimal_weakly`. Measured (`$EX/c10/`): `u_x = U sin x cos y`, `u_y = -U cos x sin y` on `[0, 2 pi)` cell centres with `U = Ma c_s` |
| Riemann problem (Sod, Lax, Shu–Osher, Leblanc, strong shock, double rarefaction, oblique and boosted) | `interface`, `left`, `right` states, optional `normal`, `boost` | `kinet/initialization/riemann.py`, `kinet/config/components/riemann.py` | `sod/*`, `lax/*`, `oblique_riemann/*`, ... |
| Isentropic vortex (Shu 1998), exact solution at `t = 0` | `strength`, `radius`, `center`, `boost`, `density`, `pressure` | `kinet/initialization/vortex.py`, `kinet/reference/vortex.py` | `isentropic_vortex/*` |
| Sedov blast (planar, 1D) with an ExactPack reference | none beyond the physics | `simulations/sedov/initialize.py`, `reference.py` | `sedov/default`, `sedov/kallikounis_2022` |
| Ambient gas plus a body in a freestream | the physics' `reference` and `mach` | `kinet/initialization/ambient.py`, `simulations/flow_around_objects/initialize.py` | `flow_around_objects/*`, `ibm/*` |
| Random compressible MHD plasma of stated regime numbers, one seed per member | `sonic_mach`, `alfven_mach`, `seed`, ... | `simulations/compressible_mhd/initialize.py` | `compressible_mhd/random_turbulence` |

The library path for a state written in Python is `initial_state(simulator, run, macros)` where
`macros(x, y[, z])` returns the fields by name on the cell centres
(`kinet/initialization/state.py`). Cell `i` is centred at `(i + 1/2) dx`
(`docs/tutorials/config-case-blocks.qmd`, "Where things are"). *Verified by running*
(`$EX/c7/`): for the weakly compressible physics the function must also return
`"temperature": 1/3` (the pinned `c_s^2` in lattice units); without it the entropic equilibrium
fails with `KeyError: 'temperature'`. Section 6a has the working script.

### Cases shipped under `simulations/` that matter here

| Case (`case=`) | Physics, solver | Grid, steps | Parameters | What it is for |
|---|---|---|---|---|
| `doubly_periodic/shear_layer` | weakly compressible, LBM D2Q9, entropic BGK | 512², 20000 | Re 50000, Ma 0.1, `lambda: 80`, `epsilon: 0.05` | the reference shear layer of this repository; the file header says what to override for other Re and grids (`simulations/doubly_periodic/shear_layer.yaml`) |
| `homogeneous_isotropic_turbulence/Re-50k_Ma-1en1` | same | 128², 5000 | Re 50000, Ma 0.1, `k0: 4`, `random_seed: 42`, `initialization_policy: analytic` | decaying 2D isotropic turbulence (the case Kareem likes) |
| `homogeneous_isotropic_turbulence/Re-50k_Ma-1en1_3d` | same on D3Q27 | 128³, 5000 | same | its 3D form |
| `homogeneous_isotropic_turbulence/Re-1k_Ma-1en1_linear_forced_3d` | weakly compressible, BGK, polynomial equilibrium | 128³, 5000 | Re 1000, `linear` forcing, `rate_policy: bassenne`, `target_u_rms: 0.0333`, `solenoidal: true` | stationary forced 3D turbulence |
| `homogeneous_isotropic_turbulence/Re-1k_Ma-1en1_random_modes_forced_3d` | same | 128³, 5000 | `random_modes`, `seed: 1729`, `correlation_time: 4.0`, `variance: 1.4e-9`, `maximum_mode: 2.0` | stationary forced 3D turbulence |
| `kolmogorov/Re-50k_Ma-1en1` | same as shear layer | 256², 5000 | `lambda: 30`, `epsilon: 0.05` | a thicker shear layer, not a forced flow |
| `taylor_green_vortex/Re-50k_Ma-1en1` | same | 512², 20000 | `k: 1` | decaying vortex with an analytic start |
| `sod/subsonic`, `sod/transonic`, `sod/lbm_1d` | compressible LBM, D2Q9 thin strip (3001 by 5) or D1Q3 | 1000 steps | `specific_heat_ratio: 2` (subsonic), `dynamic_viscosity: 0.025`, shifted lattice | the Sod runs on disk under `datasets/kinet/sod/` |
| `sod/default`, `lax/default`, `shu_osher/default`, `leblanc/default`, `strong_shock/default`, `double_rarefaction/*` | compressible, PonD DUGKS D2Q16, 1D | 600 to 1600 cells, to a physical end time | `specific_heat_ratio: 1.4` | 1D Riemann problems with the exact solution (`kinet/reference/riemann/`) |
| `oblique_riemann/default`, `boosted`, `strong_shock` | compressible, PonD, 2D | 200², to `t = 0.2` | interface at 30° (`normal: [0.866, 0.5]`) or 45° | a straight shock oblique to the grid with an exact answer (dataset 03, need (a)). The case header points at `simulations/oblique_riemann/verify.py`, **which does not exist on `perf/cleanup`** (Section 3c) |
| `double_mach_reflection/default` | compressible, PonD, 2D | 1000 by 250, to `t = 0.2` | gamma 1.4 | curved and interacting shocks (dataset 03) |
| `sedov/default`, `sedov/kallikounis_2022` | compressible, PonD, **1D planar** | 800 or 1600 cells | gamma 1.4 | Sedov with an ExactPack reference; **no 2D Sedov case was found** |
| `isentropic_vortex/default`, `fast`, `pond_3d` | compressible, PonD | 100², `t = 10` | Mach 1.2 or 3 carrier | smooth exact solution for a refinement study (dataset 02) |
| `flow_around_objects/cylinder` | compressible LBM D2Q9, inlet plus Neumann faces, link-wall cylinder | 500 by 300, 1000 | Ma 1.8, Re 300, gamma 1.4, Pr 0.71 | the supersonic obstacle run on disk |
| `compressible_mhd/random_turbulence` | compressible MHD, LBM D2Q9 | 128², 2000 | `sonic_mach: 0.5`, `alfven_mach: 1.5`, one seed per member | decaying compressible turbulence with pressure, but magnetised |
| `testing/minimal_weakly`, `testing/minimal_random_modes`, `testing/control_forcing_pulse` | weakly compressible, 48², 40 steps | | | smoke cases; the last two are the only 2D forced cases in the tree |

The full list of groups is `ls simulations/` (acoustic, compressible_mhd, double_mach_reflection,
double_rarefaction, doubly_periodic, engines, flow_around_objects,
homogeneous_isotropic_turbulence, ibm, isentropic_vortex, kolmogorov, lax, leblanc, li, lodi, mhd,
motion, oblique_riemann, poiseuille, porosity, rmi_heavy_to_light, sedov, shallow_water,
shu_osher, sod, strong_shock, taylor_green_vortex, testing).

## 2. Environment and installation

**What was actually used on 2026-11-26 (executed, worked).** The existing environment of the
checkout, unchanged: `/global/u2/k/khegazy/projects/pde/kinet/.venv` with Python 3.12.13,
torch 2.15.0+cu132, h5py 3.16.0 and hdf5plugin 7.1.0. No module had to be loaded:
`scripts/dependencies/perlmutter/export_env.sh` was not sourced, and both CPU and the login
node's A100 (`launch.device=cuda`) worked. The environment script of the examples is
`$EX/_meta/env.sh`:

```bash
source /global/u2/k/khegazy/projects/pde/kinet/.venv/bin/activate
export KINET_PROJECT=/global/u2/k/khegazy/projects/pde/kinet   # required outside the checkout
export PYTHONDONTWRITEBYTECODE=1        # keeps __pycache__ out of the kinet tree
export TORCHINDUCTOR_CACHE_DIR=$EX/_cache/inductor TRITON_CACHE_DIR=$EX/_cache/triton
export XDG_CACHE_HOME=$EX/_cache/xdg MPLCONFIGDIR=$EX/_cache/mpl WANDB_MODE=disabled
cd $EX/<run folder>                     # Hydra writes outputs/ relative to this directory
```

`KINET_PROJECT` is required when the working directory is outside the checkout. Without it
every app fails with `ProjectNotFoundError: no kinet project: there is no configs/config.yaml
in <cwd> or above, and $KINET_PROJECT is not set` (executed, `$EX/misc/log_noproj.txt`).
Running from outside the checkout is what keeps the Hydra run directory and any
`__pycache__` out of the kinet tree; with the settings above the tree stayed clean, ignored
files included. The home file system was at 92% of its quota, so the caches above point to
scratch. Experiment tracking is off by default (`launch.tracker.enabled: false` in
`configs/launch/cuda.yaml`), and no run contacted a service.

The installation commands below were **not executed** (installing was out of scope).

- **uv** (preferred): `uv sync --extra nvidia` (CUDA torch; `--extra amd` for ROCm; no extra for
  CPU), then `source .venv/bin/activate` and `uv pip install -e .`; the lockfile is `uv.lock`
  (`README.md`, "Install"; `CLAUDE.md`, "Environment Setup"). Extras: `tracking` (Weights &
  Biases and MLflow), `hyperopt`, `scaling`, `dev`, `docs`, `spectral` (`mpi4py-fft`, needed only
  by the distributed HIT initial condition). The Sedov reference needs an ExactPack fork from git
  (`pyproject.toml`, `[dependency-groups] sedov`).
- **conda/mamba**: `mamba env create -f environment.yaml -y`, `mamba activate kinet`,
  `pip install -e .` (`environment.yaml`). The `.envrc` activates a micromamba env named `kinet`.
- **Makefile** targets: `install` (uv venv plus docs extras), `test`, `test-cov`, `test-slow`,
  `docs*` (`Makefile`).
- **Python** 3.12 to 3.15; torch 2.14 disables `torch.compile` on 3.15
  (`docs/tutorials/quickstart.qmd`, "Install").
- **Device**: the root default is `launch: cuda` with `device: cuda`, `compile: true`,
  `seed: 2025` (`configs/launch/cuda.yaml`); add `launch.device=cpu` for a CPU run
  (executed, worked). `launch.compile=false` skips the `torch.compile` warm-up, which took
  23 s at 128² on the A100 (executed, `$EX/tput/`); it pays off only on runs much longer than
  that. Domain
  decomposition over several GPUs is `domain_decomposition.enabled=true
  domain_decomposition.mesh_shape=[2,2]` with `distributed=torchrun`, for `simulate` only
  (`docs/tutorials/quickstart.qmd`, "Multi-GPU on SLURM").
- **Perlmutter**: `bash slurm_scripts/submit_perlmutter.sh simulate --nodes 1 --gpus-per-node 1
  --time 04:00:00 --qos regular -- case=...` submits an `sbatch` job (account `m4790`, constraint
  `gpu`, 32 CPUs per task) that sources `scripts/dependencies/perlmutter/export_env.sh`: it loads
  `PrgEnv-gnu`, `gcc-native/14`, `cudatoolkit/13.0`, `cray-hdf5-parallel/1.14.3.9`,
  `cray-mpich/9.0.1`, activates `.venv` and puts an ADIOS2 build from `$PSCRATCH/adios2` on the
  path (`slurm_scripts/submit_perlmutter.sh`; `scripts/dependencies/perlmutter/load_modules.sh`,
  `set_vars.sh`). One GPU per node runs a single rank; more runs `srun` with one task per GPU.
  `--dry-run` prints the `sbatch` line. A long simulate is resumed by resubmitting the same
  command (Section 3, "Restart"). The submit script and domain decomposition were **not
  executed** (no batch jobs were allowed).
- The kinet checkout's `datasets/` is a symlink to `/global/cfs/cdirs/m4790/Data/neurde/`, and its
  `outputs/` to `/pscratch/sd/k/khegazy/projects/pde/kinet/outputs` (`ls -la` of the checkout).
  This repository's `datasets/` is `/global/cfs/cdirs/m4790/Data`, so kinet's data root is
  `datasets/neurde/` seen from here.

## 3. Running a simulation, step by step

**Command.** `python -m kinet.apps.simulate case=<group>/<case_id> [overrides]`
(`CLAUDE.md`, "Simulate"; `kinet/apps/simulate.py`). `task=simulate` is the default. Check the
composition first with `python -m kinet.apps.check case=<group>/<case_id> task=simulate
check_yes=true`, or print it with `--cfg job` and `--info defaults` (`configs/README.md`, "Seeing
what a run is made of"). *Status:* `simulate` executed (worked) for every case in this guide;
`check ... check_yes=true` executed (worked, it writes a run directory with
`resolved_config.yaml` and asks nothing, `$EX/misc/log_check.txt`); `--cfg job` executed
(worked, `$EX/misc/log_cfg.txt`); `--info defaults` not executed.

The smallest command that works, measured (`$EX/c1/`; 100 steps of 64² in 14 s of rollout,
24 s wall clock including start-up, on CPU):

```bash
python -m kinet.apps.simulate case=doubly_periodic/shear_layer \
    case.discretization.spatial.grid=[64,64] case.discretization.temporal.grid=100 \
    launch.device=cpu launch.compile=false paths.data_root=$EX/c1/data
```

Python start-up and composition cost about 8 to 10 s per invocation whatever the size
(`$EX/c3/`: 10-step runs took 10 to 11 s of wall clock).

**Config structure.** Hydra starts from `configs/config.yaml`, adds the `task`, the `case`
(`simulations/<group>/<id>.yaml`), and the command line goes on top. A case's `defaults:` list picks its `physics`, `collision`, `lattice`,
`equilibrium_closure`, `collision/stabilizer`, `boundary_conditions` and `io` presets
from `configs/` (`configs/README.md`, "The groups"). Case keys are overridden with the `case.`
prefix, which the CLI rewrites to `++case.<key>`; a preset group the case already selects is
replaced with `collision@case.collision=bgk`; a group the case does not have is appended with a
leading `+`, for example `+forcing@case.physics.forcing_term=random_modes`
(`docs/tutorials/config.qmd`, "Override mechanics", and its table). The table also says the root
spellings `io.save_every_n=5` and `runtime_logging.every_n=10` are rewritten to `case.` keys.
*Verified:* the logged override list shows `io.save_every_n=10` arriving as
`++case.io.save_every_n=10`, and `case.io.save_every_n=5` works as well (`$EX/c4/log_o6.txt`).
A preset that brings a sub-preset with it must be removed explicitly when the new choice refuses
it: `collision@case.collision=bgk` on an entropic case also needs
`~collision/stabilizer@case.collision.stabilizer` (Section 7).

**Where the resolved config goes.** *Corrected by running* (`$EX/c1/outputs/`): the run
directory is `outputs/<group>/<case_id>/simulate/job_<STAMP>/` **relative to the working
directory**, and it holds `resolved_config.yaml`, `run_provenance.yaml`, `simulate.log` and
`metrics/trial_result.json`. There is no `.hydra/` and no `logs/` directory on this branch.
The rollout goes under `paths.data_root` (default `./datasets`, also relative to the working
directory) at `{data_root}/{group}/{case_id}/{identity_key}/tiers/full/rollout.h5` (verified),
with `config.yaml` (the saved run config), `manifest.yaml` and `sim_checkpoints/` beside
`tiers/` (verified), and a ParaView hard link `rollout.vtkhdf` beside `rollout.h5`.

**The identity key** is an **eight**-hex-character digest (for example `0e8839ca`, not six as
first written), and the file records its parts as the root attributes `identity_physics`,
`identity_numerics`, `identity_generator`, `identity_representation` and `identity_control`
(`kinet/context/identity.py`). Measured on pairs of runs that differ in one setting
(`$EX/c3/`, `$EX/c4/`, `$EX/c5/`):

| Changes the identity key | Does not change it |
|---|---|
| grid, `temporal.grid`, `random_seed`, `precision.dtype`, `output_variables`, `N_simulations` | every `io.*` setting (`save_every_n`, `save_burst`, `record_*`, compression), `launch.seed`, `launch.device` |

Two consequences. A run on CPU and a run on GPU of the same HIT seed share one directory although
their initial fields differ (Section 6c). And runs that differ only in output cadence or
compression overwrite one another under one `data_root`. **The simulate app does not skip a
complete run**: rerunning the identical command after it finished ran all 300 steps again and
rewrote the file (`$EX/c6/log_ref2.txt`). Only a grid campaign skips a point whose dataset is
complete (`campaigns/grid/simulate.yaml` header; not executed).

**The knobs.**

| What | Key | Notes and source |
|---|---|---|
| Grid | `case.discretization.spatial.grid=[256,256]` | `resolution: 1` cell; `length` is derived (`kinet/config/common/discretization.py`, `SpatialDiscretizationConfig`) |
| Steps | `case.discretization.temporal.grid=10000` | LBM: the number of lattice steps; PonD: `temporal.type: adaptive` runs to `temporal.length` and `grid` caps the steps (`kinet/simulation/run_from_config.py`, `_rollout_length`) |
| Reynolds, Mach | `case.physics.parameters.reynolds=50000`, `case.physics.parameters.mach=0.1` | weakly compressible only; see Section 4 for how they set the viscosity (`kinet/config/physics/weakly_compressible_isothermal_fluids.py`) |
| Viscosity directly | `case.physics.parameters.dynamic_viscosity=0.025` | compressible physics only (`simulations/sod/subsonic.yaml`); the weakly compressible model has no viscosity key, Re sets it |
| Random seed of the HIT phases | `case.initial_conditions.random_seed=42` | its own `torch.Generator` on the run's device; `launch.seed` (torch and numpy, default 2025) does not touch it (verified, Section 6c; `simulations/homogeneous_isotropic_turbulence/initialize.py`, `_rogallo_velocity_synthesis_2d`) |
| Seed of random forcing | `case.physics.forcing_term.seed` | draws key on `(seed, step, batch)` (`kinet/config/components/forcing.py`, `RandomModesForcingTermConfig`); not varied in the runs |
| Output cadence | `io.save_every_n=10`, `io.save_burst=1` | *verified* (`$EX/c4/`): step 1 is always saved, then every multiple of n, and the last step; `save_burst=k` saves the k consecutive steps ending on each multiple (n = 5, k = 2 saved steps 1, 4, 5, 9, 10, ..., 19, 20) |
| Output fields | `case.physics.output_variables=[vorticity]` or `[vorticity, dilatation]` | *corrected* (`$EX/c4/`): `[vorticity, dilatation]` works; `mach` is **refused** on the weakly compressible physics ("the 'mach' output needs a gas's specific heat ratio"); `[all]` records **no** derived field at all (vorticity disappears). The macros of the physics are always recorded |
| Populations on disk | `io.record_distributions=false`, `io.record_equilibria=false` | *verified*: leaves out `F` and `Feq`; the stability fields stay (Section 5, bytes) |
| Compression | `io=hdf5_async_compression` or `io.compression=blosc2 io.blosc2_cname=zstd io.compression_level=1` | *verified* (`$EX/c4/data_o4/`): blosc2/zstd level 1; reading it needs `import hdf5plugin` before `h5py` opens the data, or h5py fails with "can't open directory (/usr/local/lib/plugin)" |
| Precision | `precision.dtype=torch.float64` (default) | *verified* (`$EX/c4/data_o3/`): `torch.float32` computes in single precision but the file is **still float64**, so it saves no disk; after 20 steps at 64² the velocity differed from the float64 run by 1.7e-5 (3e-4 of its maximum) |
| Members per run | `case.N_simulations=4` | *verified*: on the shear layer, two members are identical; on the HIT case with `initialization_policy: analytic` it **fails** (Section 6c) |
| Logging | `runtime_logging.every_n=500` | console cadence (`configs/config.yaml`); not varied |

**Restart or resume.** A simulate job writes `simulation_checkpoint_step-<N>.pt` into
`<simulation_dir>/sim_checkpoints/` on SIGTERM, SIGUSR1 or walltime drain; resubmitting the *same*
command with the same case, overrides and data root detects the file and continues the rollout,
appending to the same HDF5 file; there is no CLI flag, and a distributed run needs a checkpoint on
every rank (`docs/tutorials/quickstart.qmd`, "C. Resume a long simulation";
`kinet/simulation/run_from_config.py`, `generate_data_from_run_config`;
`kinet/checkpoints/simulation.py`). There is no `sim_checkpoints` config key; the directory name is the
constant `SIMULATION_CHECKPOINT_DIR` in `kinet/io/dataset/layout.py`.

*Verified by running* (`$EX/c6/`, 64², 300 steps on CPU):

1. **Interrupt.** `timeout -s TERM 20 python -m kinet.apps.simulate ...` stopped the run at step
   114 with `stop_reason=shutdown` and wrote `sim_checkpoints/simulation_checkpoint_step-114.pt`
   (1.2 MB at 64² without populations on disk; the checkpoint holds the populations whatever
   the IO settings).
2. **Resume.** The identical command printed `Resuming from simulation checkpoint ...`, reopened
   the same `rollout.h5`, took the remaining 186 steps, and deleted the checkpoint. Every saved
   frame equals the uninterrupted run's bit for bit (`$EX/c6/data_A` against `data_ref`).
3. **What triggers a resume.** Only the presence of a checkpoint file in
   `{data_root}/{group}/{case_id}/{identity_key}/sim_checkpoints/`
   (`kinet/simulation/run_from_config.py`, `generate_data_from_run_config`). A completed run
   leaves no checkpoint, so the same command afterwards is a fresh run that rewrites the file.
   A longer `temporal.grid` changes the identity key, so it is a new run in a new directory, not
   an extension of the finished one.
4. **Changed IO on resume.** `io.*` is in the "warn only" part of the simulate resume policy
   (`kinet/runtime/resume.py`, `DEFAULT_SIMULATE_POLICY`), and a resume with
   `io.save_every_n=10` after an interrupted `io.save_every_n=1` segment worked without a
   warning in the log (`$EX/c6/data_B`). The saved steps were 1 to 38 (dense), then 47, 57, ...,
   297 and the final 300: **the cadence restarts at the resume** (step 37 + 10), it is not
   aligned to multiples of 10 of the whole run.

### Worked example (a): the Re 5e4 shear layer as on disk

The stored config `datasets/kinet/doubly_periodic/weakly_compressible_isoT_fluids/sys_Re-5e4_Ma-1en1/configs/dc804f.yaml`
is a resolved run config of an older kinet (keys `units: dimensionless`, `solver.type`,
`system_parameters`, `pred_length: 10000`, `stability.type: entropic`, `io.save_every_n: 1`). Its
physics is: 256² cells, 10000 steps, D2Q9, entropic BGK with an entropic stability model, Re 5e4,
Ma 0.1, density 1, `lambda: 80`, `epsilon: 0.05`, periodic in both axes, output `vorticity`,
float64. The shipped case `simulations/doubly_periodic/shear_layer.yaml` has the same physics at
512² and 20000 steps, so the on-disk run is reproduced by

```bash
python -m kinet.apps.simulate case=doubly_periodic/shear_layer \
    case.discretization.spatial.grid=[256,256] case.discretization.temporal.grid=10000 \
    case.physics.parameters.reynolds=50000 \
    paths.data_root=$SCRATCH/kinet_datasets
```

*Status:* not executed at this size; the same command at 64² and 100 steps executed and worked
(`$EX/c1/`). With `paths.data_root=$SCRATCH/kinet_datasets` it also needs `KINET_PROJECT` set
when run outside the checkout (Section 2). At the CPU rate measured below the full 256² by
10000 steps would take hours on a login node; it is a GPU job (see the throughput table in
"Verified by running").

with the physics controlled by `case.physics.parameters.{reynolds,mach}` and
`case.initial_conditions.{lambda,epsilon}`. The case header says the step count scales with the
grid at fixed Mach number, about 39 N steps (`simulations/doubly_periodic/shear_layer.yaml`,
header); the 512² and 1024² runs on disk used 20000 and 40000 steps (`configs/56d32e.yaml`,
`configs/85db0e.yaml` beside the data). The old run stored `F`, `F_collided`, `Feq`, density,
pressure, velocity, vorticity, `stability_scale`, `stabilized_time_scale` (34 float64 channels,
272 bytes per cell per frame, 167 GiB). *Corrected by running* (`$EX/c4/`): the current default
records 25 float64 channels, 200 bytes per cell per frame (`F`, `Feq`, density, pressure, two
velocity components, vorticity, `stability_scale`, `momentum_time_scale`; no `F_collided`), and
`io.record_distributions=false io.record_equilibria=false` leaves 7 channels, **56** bytes per
cell per frame, not 40, because the two entropic stability fields are still written. The new run will be in the grouped
layout (Section 5), and bit-for-bit agreement with the old file is not promised: the old config
has `lattice.use_static_weights: false` where the shipped `configs/lattice/d2q9.yaml` has `true`.

### Worked example (b): decaying 2D isotropic turbulence from random modes

`simulations/homogeneous_isotropic_turbulence/Re-50k_Ma-1en1.yaml` as shipped: 128², 5000 steps,
`k0: 4`, `random_seed: 42`, Re 5e4, Ma 0.1, entropic BGK, `initialization_policy: analytic` (the
Skordos non-equilibrium seed, `fneq_hit`). The archived ensemble used the same initial condition
at 256² and 512² (Section 6c). To make one run at 256² over the same physical time as the
reference shear layer:

```bash
python -m kinet.apps.simulate case=homogeneous_isotropic_turbulence/Re-50k_Ma-1en1 \
    case.discretization.spatial.grid=[256,256] case.discretization.temporal.grid=10000 \
    case.initial_conditions.random_seed=7 \
    io.save_every_n=10 io.record_distributions=false io.record_equilibria=false \
    paths.data_root=$SCRATCH/kinet_datasets
```

*Status:* not executed at this size; the same case and keys executed and worked at 64² and 32²
for 10 steps (`$EX/c3/`). Two cautions from those runs. The seed's field depends on the
device, so a CPU run does not reproduce a GPU run of the same seed (Section 6c). And the first
frames carry an acoustic transient: the mean kinetic energy oscillates from step to step,
0.934, 0.992, 0.946, ... of its initial value at 64², and 0.78, 0.91, 0.86, ... at 32²
(`$EX/c3/data_a`, `data_d`). This was observed, not investigated; its size at 256² was not
measured.

Physics knobs: `case.physics.parameters.{reynolds,mach}`, `case.initial_conditions.{k0,
random_seed, density, velocity}`. `velocity` sets the total rms speed in the case's units; when
it is unset the amplitude is `Ma * c_s`, and the docstring of `init_hit` warns that a stated
`velocity` changes the effective Reynolds number to `Re * U / (Ma c_s)` because the viscosity is
still derived from `Ma c_s` (`simulations/homogeneous_isotropic_turbulence/initialize.py`,
`_state_scales`, `init_hit`).

### Worked example (c): a compressible case

The Sod run on disk, `datasets/kinet/sod/compressible_fluids/Pr-71en2_vuy-1.4_visc-1en4/configs/`,
is the LBM shock tube: `simulations/sod/subsonic.yaml` runs 3001 by 5 cells for 1000 steps with a
shifted D2Q9 lattice (`shifts: [0.057, 0.0]`), Levermore `G` and extended `F` closures, piecewise
stabilizer, `specific_heat_ratio: 2`, `dynamic_viscosity: 0.025`, `prandtl: 0.71`, open ends, and
the states `left: {density: 0.5, temperature: 0.2}`, `right: {density: 1.8, temperature: 0.025}`
at `interface: 0.5`:

```bash
python -m kinet.apps.simulate case=sod/subsonic
```

*Status:* not executed at full size; executed (worked) at `case.discretization.spatial.grid=[301,5]
case.discretization.temporal.grid=100 io.save_every_n=10 launch.device=cpu launch.compile=false`,
13 s of rollout (`$EX/c8/data_sod/`). The file holds `observables/{density, pressure,
specific_energy, temperature, velocity}` (the energy field is named `specific_energy`), the four
populations `F`, `Feq`, `G`, `Geq`, and six mesoscopic fields; 418 bytes per cell per frame.
Pressure is stored as an absolute ideal-gas pressure, `p = rho T` to round-off
(`pressure_convention: absolute`), and the boundary attribute records the Neumann ends.

For a two-dimensional shock with an exact answer, the PonD oblique tube
(`simulations/oblique_riemann/default.yaml`: 200², gamma 1.4, `dynamic_viscosity: 1e-5`,
interface normal at 30°, `t_end = 0.2`, CFL 0.2 from `configs/solver/pond_dugks.yaml`):

```bash
python -m kinet.apps.simulate case=oblique_riemann/default launch.device=cuda
python -m kinet.apps.verify   case=oblique_riemann/default      # scores it against the exact 1D solution
```

*Status:* the simulate line was not executed at 200²; it executed (worked) at
`case.discretization.spatial.grid=[32,32] launch.device=cpu launch.compile=false` (40 adaptive
steps to `t = 0.2` in 296 s, `$EX/c8/data_obl/`) and at 64² on the GPU (84 steps in 105 s,
`$EX/c8/data_obl_gpu/`). The PonD IO preset compresses with blosc2/zstd by default, so the
file needs `import hdf5plugin` to read; it stores density, pressure, specific energy,
temperature and velocity, no populations. **The verify line fails** (executed, failed:
`FileNotFoundError: simulations/oblique_riemann has no verify.py`, `$EX/c8/log_verify.txt`).
On `perf/cleanup` the only `verify.py` under `simulations/` is `simulations/ibm/verify.py`,
although the oblique case's header names one. An exact-solution comparison for this case has
to be written outside kinet, from `kinet/reference/riemann/`.

Physics knobs for the compressible physics: `case.physics.parameters.{specific_heat_ratio,
dynamic_viscosity, prandtl, mach, reynolds, freestream_hold}` and the Riemann states in
`case.initial_conditions` (`configs/physics/compressible_fluids.yaml` header;
`kinet/config/components/riemann.py`). These runs store a thermodynamic pressure, temperature and
energy (Section 5).

## 4. Units and nondimensionalisation

- **Unit systems.** `units: lattice` (the persisted name of the former `dimensionless`) says the
  authored numbers are already in lattice units: cell size 1, step 1, reference density 1; `SI`,
  `CGS` and `custom` are converted to that frame by one multiply per variable
  (`docs/units/index.qmd`, opening notes). Every case that matters here is `units: lattice`.
- **Re and Ma.** For the weakly compressible physics, `U = Ma * c_s` with `c_s = 1/sqrt(3)`
  (so `U = 0.057735` at Ma 0.1), and the lattice viscosity is `nu_l = U L / Re` where `L` is
  `parameters.reference.length` or, when unset, **the first length of the domain in cells**
  (`kinet/config/physics/weakly_compressible_isothermal_fluids.py`, class
  `WeaklyCompressibleReferenceSpec`; `kinet/physics/weakly_compressible_isothermal_fluids/parameters.py`,
  `resolve_kinematic_viscosity`). The relaxation time follows from
  `tau - 1/2 = nu_l / c_s^2 = u_l N / (Re theta)` with `theta = 1/3` (`docs/units/discretization.qmd`,
  "The two degrees of freedom and the master relation"). For 256², Re 5e4, Ma 0.1:
  `nu_l = 2.956e-4`, `tau - 1/2 = 8.87e-4`. The Reynolds number is therefore defined on the box
  side, not on `L/2pi` as the Taylor–Green benchmarks do, a difference of `2pi` that
  `docs/notes/issues/tgv_case_reynolds_definition.md` records. *Verified from the files*: the
  root attribute `normalization_plan` records `lattice.nu_l` and `lattice.tau1`; at 64², Re 5e4
  they are `7.390e-5` and `0.5002217` (`$EX/c1/`), at 32² `3.695e-5` (`$EX/c5/`), and at 64²,
  Re 100 `0.036950` (`$EX/c10/`), each equal to `Ma c_s N / Re` and `1/2 + 3 nu_l`.
- **End-to-end check with the Taylor–Green vortex** (`$EX/c10/`; executed, worked):
  `case=taylor_green_vortex/Re-50k_Ma-1en1 case.discretization.spatial.grid=[64,64]
  case.discretization.temporal.grid=500 case.physics.parameters.reynolds=100`. The rms velocity
  decays as `exp(-2 nu_l k^2 t)` with `nu_l = Ma c_s N / Re`, `k = 2 pi / N` and `t` the lattice
  step count: the stored amplitude falls short of the exact one by `2.0e-3` at step 1 (a
  one-step start-up loss), by `1.2e-3` at step 50 and by `5.6e-4` at step 500 (`0.69999`
  against `0.70038` of the initial amplitude), and the decay rate between steps 50 and 500
  agrees with the exact one to `6e-4`. This confirms in one run the viscosity rule, that one stored
  frame is one lattice step, and that the clock `time/time` counts lattice steps.
- **Time scaling across grids.** kinet keeps `u_l = Ma c_s` fixed when the grid changes, so the
  physical time per step scales as `1/N`: this is the **acoustic** scaling (`dt ∝ dx` at fixed
  `u_l`; steps for a fixed physical duration scale as `N`), as opposed to diffusive scaling
  (`dt ∝ dx²` at fixed `tau`), both described in `docs/units/discretization.qmd`, "Time-step
  scaling laws" (after Latt 2008). The Reynolds number is invariant under either. Nothing rescales
  `temporal.grid` for you: a 512² run of the same flow over the same physical time needs twice the
  steps of a 256² run, which is what the on-disk 256, 512 and 1024 runs did (Section 3a).
  *Verified* (`$EX/c5/`): 32² for 100 steps and 64² for 200 steps both end at
  `time/time_convection = 0.180422`, with `0.0018042` and `0.00090211` per step.
- **Physical time per step.** The grouped file records two clocks: `time/time` is the lattice
  clock (`Sum dt` over accepted steps, exactly the step count for the LBM) and
  `time/time_convection` is `time / convection_time_ref` with `convection_time_ref = L / U_ref`,
  `L` the longest side of the grid in cells and `U_ref` the freestream `Ma c_s`
  (`docs/units/time-channels.qmd`, table and "One clock, on the carrier";
  `kinet/solver/base/convection_reference.py`, `refresh`). For 256² at Ma 0.1 that is
  `0.057735 / 256 = 2.2553e-4` per step and `2.2553` at step 10000: exactly the "physical time"
  this repository's reader takes from the old flat file's `time` dataset
  (`fmeval/data/kinet_raw.py`, comment in `__init__`; `docs/datasets/reynolds_ladder_2d.md`,
  "The Reynolds ladder"). So the old `time` is the new `time/time_convection`, and the old
  `time_index` is the new `time/time`. *Verified* at 64²: `0.057735 / 64 = 9.0211e-4` per step
  (`$EX/c1/`). In a full tier `time/time` and `time/time_index` are both the step count (units
  `step` and `-`). In a coarse-grained tier they differ: `time/time_index` is renumbered
  1, 2, ... over the coarse frames while `time/time` keeps the fine step count (Section 5,
  tiers). Read `time/time` or `time/time_convection`, never `time_index`, as the clock.
- **Vorticity is in lattice units.** The `vorticity` calculator is the curl of the velocity by
  the host's spatial derivative, which for the LBM is the lattice stencil at a spacing of one cell
  (`kinet/calculators/macroscopic.py`, class `Curl`, lines 160 to 190; `CLAUDE.md`, "Calculators"
  row). A stored vorticity is therefore per lattice step per cell, and a coarse-grained tier
  recomputes it on the coarse grid (`docs/utils/coarse-graining.qmd`, `datasets` row: "Kinet drops
  vorticity from the inputs and recomputes it"). This is the gotcha this repository already
  handles by recomputing vorticity from velocity on the analysis grid. *Verified* (`$EX/c5/`,
  32² and 64²): the stored vorticity (units attribute `1/step`) equals, to `3e-16` relative,
  the curl `d u_y/dx - d u_x/dy` (axis 0 is x) taken with the isotropic D2Q9 stencil
  `d/dx a = 3 sum_i w_i c_ix a(x + c_i)`, with weights 1/9 on the axis neighbours and 1/36 on the
  diagonals (`kinet/calculators/macroscopic.py`, `Curl`, which cites Ramadugu et al. 2013,
  Eq. 11). It differs from a second-order central difference by `1e-3` to `3e-3` and from a
  spectral curl by about `0.2` of its maximum on that under-resolved shear layer.
- **Pressure.** *Corrected by running* (`$EX/c1/`): for the weakly compressible physics the
  stored `pressure` is the fluctuation `(density - 1) c_s^2`, to `5e-20`, not
  `density * c_s^2`; that is what the attribute `pressure_convention: fluctuation_referenced`
  means (the old flat files stored `density * c_s^2`). It is still a function of density and
  carries no information; this repository's reader excludes it either way. Compressible LBM and
  PonD: an absolute thermodynamic pressure (`pressure_convention: absolute`), `p = rho T` in
  lattice units, beside temperature and `specific_energy` (Section 3c, `$EX/c8/`).

## 5. Output format

**Grouped HDF5 rollout** (`kinet/io/rollout/contract.py`, `kinet/io/rollout/layout.py`;
verified with `h5py` on the files named, and again on fresh runs on 2026-11-26; the full tree
of a 64² shear-layer run is printed by `python $EX/_meta/h5tree.py
$EX/c1/data/doubly_periodic/shear_layer/0e8839ca/tiers/full/rollout.h5`):

```text
rollout.h5
├── observables/<name>        (1, C, T, X, Y) float64, chunk (1, C, 1, X, Y)   density, velocity, pressure, vorticity, ...
├── mesoscopic/dists/<pop>    (1, Q, T, X, Y)                                 F, Feq, F_collided, G, Geq, G_collided (when recorded)
├── mesoscopic/<name>         (1, 1, T, X, Y) or (T,)                         stability_scale, time_scale, tau_thermal, ...
├── time/time                 (T,)   the lattice clock (step count for the LBM)
├── time/time_convection      (T,)   domain crossings, L / (Ma c_s)
├── time/time_index           (T,)   accepted-step count; NaN at a slot that was not saved
├── initial_conditions/...    the same tree with a length-1 time axis: the state before step 1
├── geometry/masks/{fluid,solid,blanked}   (X, Y) uint8
└── VTKHDF/{CellData,Steps}   a ParaView view of the same data (also hard-linked as rollout.vtkhdf)
```

*Measured on a fresh weakly compressible run* (`$EX/c1/`, entropic BGK, 64², 100 steps, default
IO), every dataset float64 with its unit in a `units` attribute:

| Path | Shape | Units |
|---|---|---|
| `observables/density` | `(1, 1, 100, 64, 64)` | `m0/cell^2` |
| `observables/velocity` | `(1, 2, 100, 64, 64)`, channel 0 is x (axis 3) | `cell/step` |
| `observables/vorticity` | `(1, 1, 100, 64, 64)` | `1/step` |
| `observables/pressure` | `(1, 1, 100, 64, 64)`, equal to `(density - 1)/3` | `p0` |
| `observables/temperature` | `(1, 1, 100, 1, 1)`, constant 1/3 | `T0` |
| `mesoscopic/dists/F`, `Feq` | `(1, 9, 100, 64, 64)` | `m0/cell^2` |
| `mesoscopic/stability_scale`, `momentum_time_scale` | `(1, 1, 100, 64, 64)` | `-` |
| `mesoscopic/viscous_time_F` | `(100,)` | `step` |
| `time/time`, `time/time_index` | `(100,)`, values 1 to 100 | `step`, `-` |
| `time/time_convection` | `(100,)`, `9.0211e-4` per step | `-` |
| `initial_conditions/observables/*`, `.../mesoscopic/dists/{F,Feq}`, `.../stability_scale` | the above with a time axis of length 1 | same |
| `initial_conditions/time/*` | `(1,)`, all zero | same |

The compressible runs differ as Section 3c says (`specific_energy`, `G`, `Geq`, more mesoscopic
fields, absolute pressure). A run with `io.save_every_n = n` leaves NaN at every unsaved slot of
`time/time`, `time/time_convection` and `time/time_index` alike (`$EX/c5/`).

The leading axis is `N_simulations`. The time axis has exactly `temporal.grid` slots; solver
step `s` is slot `s - 1`, and the initial condition is only under `initial_conditions/`
(`CLAUDE.md`, "Grouped HDF5 layout"). With `io.save_every_n = n`, the unsaved slots stay at the
NaN fill and cost no storage, and `time/time_index` is finite exactly at the saved slots
(`docs/utils/io.qmd`, "Rollouts of another solver", "Time axis"); a reader must select the finite
slots. The archived 256 tier of the Re 50k ensemble member `0171ae` holds 1001 finite slots of
10000 (slots 0, 9, 19, ..., 9999).

Root attributes (JSON strings where structured; `kinet/io/rollout/attrs.py`,
`kinet/io/rollout/run_attributes.py`): `discretization` (`{"spatial": {"grid", "length",
"resolution", "type", "unit"}, "temporal": {...}}`), `units`, `characteristic_scales`,
`normalization_plan`, `lattice`, `boundary_conditions`, `case`, `case_id`, `dimension`,
`kinet_solver` (`kinet_integrator` in the file read), `identity_key` and the `identity_*`
digests, `schema_version`, `pressure_convention`, `reference_sound_speed`,
`reference_temperature`, `kinet_rollout_status`, `kinet_last_completed_step`,
`kinet_rollout_total_pred_length`, `time_stride` (set on a coarse-grained tier). The boundary
conditions are recorded, unlike in the old flat file. *Measured on a fresh file* (`$EX/c1/`):
there are **five** `identity_*` digests (`physics`, `numerics`, `generator`, `representation`,
`control`), plus `group` and `kinet_segment_pred_length` (the steps of the last segment, which
is smaller than the total after a resume); `kinet_solver` is `lbm`; `normalization_plan` holds
`lattice.{nu_l, tau1, u_l, L_l}` and `similarity.{reynolds, mach}`, which is where a reader
should take the viscosity from.

**Fields stored.** The physics' macros always: density, velocity, and for the compressible
physics pressure, temperature, energy; derived fields from `output_variables` (vorticity, mach,
dilatation); the weakly compressible `pressure` and a spatially degenerate `temperature`
`(1, 1, T, 1, 1)` are stored too. Populations under `mesoscopic/dists/` when
`io.record_distributions` (default true) and the equilibria when `io.record_equilibria` (default
true). **Pressure for compressible cases is stored**: the obstacle file
`datasets/kinet/flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2/D2Q9_shape-500-300_T-1000_H-a92b16.h5`
holds `observables/{density, energy, mach, pressure, temperature, velocity}` and six populations
`(1, 9, 1000, 500, 300)`; the Sod file
`datasets/kinet/sod/compressible_fluids/Pr-71en2_vuy-1.4_visc-1en4/D2Q9_shape-3001-5_T-1000_H-d17baf.h5`
holds the same minus `mach`. Both are already grouped, which is why no reader here opens them.

**Bytes per cell per frame** (float64, uncompressed): 8 bytes per channel. *Corrected by
running* (`$EX/c4/`, `$EX/c8/`; the measured file sizes include the initial condition and
metadata, so they sit a little above the channel count on these tiny files):

| Run | Channels written | Bytes per cell per frame |
|---|---|---|
| weakly compressible, entropic, default IO | `F`, `Feq` (18), density, pressure, velocity (2), vorticity, two stability fields | 200 (219 measured) |
| same, `io.record_distributions=false io.record_equilibria=false` | 7 | **56** (68 measured), not 40 |
| same as the default, blosc2/zstd level 1 | 25, compressed | 135 measured on a 64² shear layer; the ratio depends on the flow |
| compressible LBM Sod, default IO | `F`, `Feq`, `G`, `Geq` (36), six observables channels, six mesoscopic fields | 418 measured |
| PonD oblique Riemann, its preset (blosc2 compressed) | six observables channels (density, pressure, specific energy, temperature, velocity) and three mesoscopic fields, no populations | 72 uncompressed, 47 measured |

The old default with `F`, `F_collided`, `Feq` and two stability fields was 272 bytes (the
167 GiB of `D2Q9_shape-256-256_T-10000_H-dc804f.h5`). Sizing at 56 bytes: a 256² run with
10000 saved frames is 37 GB; a 512² run with 20000 saved frames is 294 GB. Only saved frames
cost disk, so `io.save_every_n=10` divides these by ten. `blosc2`/`zstd` level 1 is the
compression the paper pipelines used (`configs/io/hdf5_async_compression.yaml`).

**Tiers, downsampled copies and shards.** `python -m kinet.apps.coarse_grain case=<group>/<case>
task=coarse_grain task.targets_spatial=[128,128]` box-filters the full tier in space (and in time
by the same factor when asked, `time_method`) into `tiers/<N>/rollout.h5` beside `tiers/full/`,
recomputing vorticity and stamping `time_stride` (`docs/utils/coarse-graining.qmd`). *Executed* (`$EX/misc/log_cg*.txt`, on the 64² run of `$EX/c5/data_n64` saved
every 10th step): `task.targets_spatial=[32,32]` alone **failed** ("coarse frames [0, 1, 2, 3,
5] have no recorded step to read with time_method='last' (temporal_factor=2); use a
temporal_factor that is a multiple of io.save_every_n"); adding `task.temporal_factor=10`
**worked** and wrote `tiers/32/rollout.h5` with `time_stride: 10`, the stability field the
case lists under `coarse_grain.ignore_datasets` dropped, `time/time` = 10, 20, ... (fine steps),
`time/time_index` = 1, 2, ... (coarse frames) and an `initial_conditions/` group. The command
needs the same case overrides as the simulate run so that it finds the same identity key. The `_downsampled-128-128`, `_shards` and `_well-format` directories under
`datasets/kinet/doubly_periodic/` were made with tools that are **not in the current kinet tree**
(not found under `kinet/`, `scripts/` or `docs/`). The `topology/dd_topology.json` files are the
domain-decomposition map that the old `domain_decomposition.topology_json_path` key wrote
(`configs/dc804f.yaml` beside the data); the current config has no such key.

**The old flat layout** (`fmeval/data/kinet_raw.py` module docstring; verified on
`D2Q9_shape-256-256_T-100_H-04a8a1.h5`): root datasets `density (1,1,T+1,X,Y)`, `velocity
(1,2,T+1,X,Y)`, `F`, `F_collided`, `Feq (1,9,T+1,X,Y)`, `pressure`, `vorticity`,
`stability_scale`, `stabilized_time_scale`, `temperature (1,1,T+1,1,1)`, `time`, `time_index`,
`time_scale (T+1,)`; attributes `discretization`, `units`, `characteristic_scales`,
`kinet_*` status. No reader for this layout was found in the current kinet
(`kinet/io/rollout/read/`), so these files are read-only legacy on both sides.

**What this repository's reader needs from a new run.** Density and velocity with the shapes
above, a per-frame clock, the grid shape and length from `discretization`, and (optional)
pressure that is not a function of density (`fmeval/data/kinet_raw.py`, `__init__`;
`fmeval/data/base.py`). A conversion to the flat layout must (1) strip the prefixes the names with `observables/`
and `mesoscopic/dists/`, (2) read the clock from `time/time_convection` (or `time/time` times the
constant above), (3) drop the NaN slots of a thinned run, (4) take frame 0 from
`initial_conditions/` if the initial condition is wanted, and (5) read `boundary_conditions`
from the attribute instead of assuming periodic. *Checked against fresh files*, the conversion
must in addition:

1. **Count frames differently.** The flat reader requires `len(time) == temporal.grid + 1`
   (frame 0 is the initial condition). A grouped file has `temporal.grid` slots and no frame 0,
   so the converted file's `temporal.grid` must be set to the number of frames it holds minus
   one: the finite entries of `time/time_index`, plus one for the prepended initial condition.
2. **Select saved slots by `np.isfinite(time/time_index)`.** Step 1 is always saved, so a run
   with `save_every_n = 10` has saved steps 1, 10, 20, ...: the spacing of the first two frames
   is 9 steps, not 10. The conversion drops step 1 to keep a uniform clock (the
   flat reader's `frame_stride` then works on the steps 10, 20, ...). After a resume with a changed cadence the spacing
   restarts at the resume step (Section 3, "Restart").
3. **Read the clock from `time/time_convection`**, never `time_index` (renumbered in tiers).
4. **Treat `pressure` as redundant** for the weakly compressible physics (it is
   `(density - 1) c_s^2`), and as a real field when `pressure_convention` is `absolute`.
5. **Import `hdf5plugin`** before reading any blosc2-compressed file (the PonD preset and
   `io=hdf5_async_compression`). Whether this repository's environment has `hdf5plugin` was
   not checked; it is not named in its `pyproject.toml`.
6. **Recompute vorticity** from velocity, as now: the stored one is the D2Q9 stencil curl in
   `1/step` (Section 4).
7. **Ignore the `VTKHDF` group** and the `rollout.vtkhdf` hard link beside the file.

## 6. Ensembles, perturbations, seeds and refinement

**(a) Start a run from a stored frame or checkpoint.** A simulate run resumes only from its own
`sim_checkpoints/simulation_checkpoint_step-<N>.pt`, found by `find_simulation_checkpoint` next to
the rollout (`kinet/simulation/run_from_config.py`, `generate_data_from_run_config`;
`kinet/checkpoints/simulation.py`). That continues the same rollout; it does not branch. **No
config key that starts a simulate run from a frame of a rollout file was found** (searched
`kinet/initialization/`, `kinet/simulation/run_from_config.py`, `kinet/config/case_models.py`,
`docs/tutorials/config-case-blocks.qmd`). The read-side accessor
`KinetDataset.load_initial_condition()` exists (`CLAUDE.md`, "Grouped HDF5 layout") but only
reads; it does not start a simulation. The least-code route to a branch is Python: open a rollout with
`h5py`, take a frame, and hand it to `initial_state(simulator, run, macros)` with a `macros`
function that returns those arrays (`kinet/initialization/state.py`; `docs/tutorials/library.qmd`
for the `Simulator` API, not read in full). The populations are then re-seeded from the macros
(equilibrium plus the group's `population_corrector` if any), so the first steps carry a small
kinetic transient that the stored run did not have.

*Demonstrated without modifying kinet* (executed, worked; script
`$EX/_meta/branch_from_frame.py`, outputs `$EX/c7/`). The script, run from outside the
repository with `KINET_PROJECT` set, does:

1. **Compose.** `run = compose_run_config(["case=doubly_periodic/shear_layer",
   "++case.discretization.spatial.grid=[64,64]", "++case.discretization.temporal.grid=10",
   "++launch.device=cpu", "++launch.compile=false", "task=simulate", ...])`
   (`kinet/runtime/hydra/compose.py`).
2. **Build.** `simulator = kinet.build_simulator(run, logger=KinetProcessLog.null("branch"),
   process_config=single_process_config(device="cpu"))`.
3. **Paint.** `fields = initial_state(simulator, run, macros)`, where `macros(x, y)` returns
   `density` `(X, Y)`, `velocity` `(X, Y, 2)` (stored frame plus perturbation) and
   `temperature: 1/3`.
4. **Optionally hand over the stored populations.** `fields.dists["F"] = torch.as_tensor(F[None])`
   with `F` the `(9, X, Y)` populations of that frame. A carrier that already holds every
   population is not re-seeded (`KineticSolver.is_macro_only_ic`).
5. **Step and write.** `simulator(fields, control=RolloutControl(pred_length=10,
   save_results=True, record_forecast=True, save_dir=<dir>, output_path=<dir>/rollout.h5))`
   (`kinet/simulation/rollout_control.py`) writes a normal grouped rollout.

Results, branching from step 100 of the 64² shear layer (`$EX/c1/`) and comparing with an
uninterrupted run to step 110 (`$EX/c7/data_ref110/`):

| Variant | Stored initial condition against the source frame | Velocity after 1 step against the uninterrupted run |
|---|---|---|
| macros only, no perturbation (`branch_macros_amp0`) | identical (difference 0) | differs by up to 4.4e-3 (8% of `U = 0.0577`) |
| macros only, solenoidal perturbation of peak 1e-3 (`branch_macros_amp1e-3`) | differs by exactly the perturbation | differs by up to 5.3e-3 |
| macros plus the stored `F`, no perturbation (`branch_F_amp0`) | identical | **identical to the bit**, also after 10 steps |

So the "small kinetic transient" of a macro-only start is not small on this under-resolved
64² shear layer: re-seeding the populations at equilibrium discards their non-equilibrium
part, which is large across a layer only about a cell thick. Handing over the stored `F` removes
it entirely, so a branching source run should record `F` at the branch frames. A perturbed
start that keeps the non-equilibrium part would add the perturbation to `F` as the difference
of two equilibria, `F + feq(rho, u + u') - feq(rho, u)`, using kinet's own equilibrium; this
was not tried. Two more things a user of this route must know: the new file's clock restarts
at zero (`time/time` = 1, 2, ...), and the script writes only `rollout.h5` (no `config.yaml`,
`manifest.yaml` or identity directory), while the file's `identity_key` attribute is that of
the unperturbed case. The perturbation used was `psi = A sin(k x) sin(k y)`, `u' = d psi/dy`,
`v' = -d psi/dx` with `k = 2 pi 2 / N`, which is divergence-free in the continuum and to
second order on the grid.

**(b) Add a perturbation to an initial condition.** No perturbation hook exists (search of
`kinet/initialization/*.py`, `simulations/*/initialize.py` and `docs/tutorials/*.qmd` for
"perturb" finds only the shear layer's `epsilon`, the RMI interface and a shallow-water bump).
Two routes:
1. A new initializer in the group's `initialize.py`: subclass `HitIC` (or
   `DoubleShearLayerIC`) with fields such as `perturbation_amplitude: float = 0.0` and
   `perturbation_seed: int = 0`, call the existing painter, and add the noise to the returned
   macros before `paint_macros`; register it with `@initializer("<new case id>",
   initial_conditions=<Subclass>)` and add a case YAML with that id (`kinet/initialization/hooks.py`;
   `simulations/README.md`, "Initializers"). The perturbation then enters the identity key, so
   each member gets its own directory.
2. The Python route of (a), adding noise to the frame before `initial_state`. *This route was
   executed and works unmodified* (Section 6a); route 1 was not tried. Route 2 needs no change
   to kinet, but the run it writes has no identity directory or manifest of its own, so the
   script must name a distinct output path per member.

Note the ensemble spec's exchangeability argument: for the ensemble use the perturbation must be
drawn the same way for every member including the one called truth (`dataset_specs/01_physical_ensemble.md`, Section 3).

**(c) Seeds of the random-mode initial condition.** `initial_conditions.random_seed` seeds a
`torch.Generator` that draws one uniform phase per Fourier mode on the `(nx, ny)` grid
(`simulations/homogeneous_isotropic_turbulence/initialize.py`, `_rogallo_velocity_synthesis_2d`,
`theta = 2 pi * torch.rand(nx, ny, generator=generator)`). The draw is per grid cell in Fourier
space, so **the same seed gives a different field on a different grid**, which is what the
catalog measured (`FUTURE_EXPERIMENTS_CATALOG.md`, Section 1.3, correlation 0.12 and 0.005
between grids). *Verified by running* (`$EX/c3/`, script `$EX/_meta/compare_ic.py`, stored
initial velocity of 64² runs on CPU unless noted):

| Pair | Correlation | Max difference | Identity keys |
|---|---|---|---|
| seed 42 and seed 42, two separate runs | 1.0000 | 0 (bitwise) | equal |
| seed 42 and seed 7 | -0.10 | 0.24 | differ |
| seed 42 at 64² (2 by 2 cell average) and seed 42 at 32² | -0.014 | 0.18 | differ |
| seed 42 with `launch.seed=2025` (default) and `launch.seed=1` | 1.0000 | 0 | equal |
| seed 42 on CPU and seed 42 on the GPU (`launch.device=cuda`) | **0.11** | 0.22 | **equal** |

The last row is new: the generator is created on the run's device
(`torch.Generator(device=device)` in `_rogallo_velocity_synthesis_2d`), and CPU and CUDA
generators give different streams for one seed. **A seed reproduces its field only on the same
kind of device.** The archived `hit_scaling` ensemble was run on GPUs, so a CPU rerun of one of
its seeds would not reproduce it, and, since the device is not in the identity key, would be
filed under the same directory name. Whether two GPU runs of one seed agree bitwise was not
checked (one GPU run was made). The rms speed of the field is `Ma c_s = 0.057735` exactly. To get one flow at several resolutions, synthesise the field once on the finest
grid and restrict it (route (a) or (b)), or build the initial condition from a fixed set of modes
below the coarsest Nyquist index (a change to `_rogallo_velocity_synthesis_2d`; the 2/3
dealiasing mask already zeroes modes above `N/3`). `launch.seed` (default 2025) seeds torch and
numpy globally and does not enter this generator. With `N_simulations > 1`, `paint_macros`
repeats the one painted field for every member (`kinet/initialization/primitives.py`,
`field_axes`, line 100), so the HIT initializer would give identical members. *Corrected by
running* (`$EX/c3/log_g.txt`, `log_h.txt`): on the HIT case `case.N_simulations=2` **fails**
before the first step: with the case's `initialization_policy: analytic` the non-equilibrium
corrector returns one member ("the initial population corrector returned a 'F' correction of
shape (1, 9, 64, 64), but the equilibrium is (2, 9, 64, 64)"), and with
`case.physics.parameters.initialization_policy=equilibrium` the seed refuses the corrector that
the case still registers ("initialization_policy='equilibrium' but an initial population
corrector was supplied"). On the shear layer, which has no corrector, `N_simulations=2` runs and
the two members are identical (`$EX/c3/data_sl_nsim2`). For HIT ensembles, one run per seed is
the only route. The compressible MHD
case draws `seed, seed + 1, ...` per member instead (`simulations/compressible_mhd/random_turbulence.yaml`
header). A `random_modes` forcing does differ per member (its draw keys on the batch index).

*What already exists.* On 2026-11-06 to 11-08 Kareem ran, from the `changes_while_running_hit`
branch, 100 runs each of `hit_scaling/Re-12p5k_Ma-1en1_2d` and `Re-25k_Ma-1en1_2d` at 256²
(saving every 10th step, macroscopic fields only) and 100 runs of `Re-50k_Ma-1en1_2d` at 512² by
20000 steps (saving every step, then coarse-grained by 2 in space and time and thinned to every
10th coarse step), each run with its own random seed taken from the wall clock, plus one long run
per Reynolds number (256² by 100000 steps at 12.5k and 25k; 512² by 200000 steps at 50k, archived
as a 256 tier of 26 GB under `.../Re-50k_Ma-1en1_2d/bea170/`). The archive is
`/global/cfs/cdirs/m4790/Data/neurde/hit_scaling/<case>/<identity_key>/{config.yaml,
manifest.yaml, tiers/256/rollout.h5}` (102, 102 and 103 directories); `tiers/full/` was deleted
after downsampling, so the manifest's `full:` entry points at nothing. The seeds are in
`config.yaml` of each directory and in
`/pscratch/sd/k/khegazy/projects/pde/kinet/outputs/hit_scaling/ensemble512_ledger/seeds.txt`
(97 lines). Sources: `REASONS_FOR_CHANGES.md` and `slurm_scripts/submit_hit_ensemble.sh`,
`downsample_hit_ensemble.sh` on the branch; `outputs/hit_scaling/*_ledger/`. The branch's case
files use the pre-rename keys (`scheme:` for `physics:`, `experiment:` for `group:`,
`/closure/analytic@simulate_closure.F`), so they do not compose on `main` as they stand; the
`main` case `homogeneous_isotropic_turbulence/Re-50k_Ma-1en1` with the overrides of Section 3b is
the same physics. The branch also carries `Re-*_Ma-1en1_linear_forced_2d.yaml`, a 2D linearly
forced case with `rate_policy: k_feedback`, `target_u_rms: 0.0333`, `solenoidal: true` and an
`application: edm` key that `main`'s config model does not have; whether it ran is not recorded
in the ledgers read.

**(d) The same configuration at 64², 128², 256², 512² with matched physical time.** Hold Re and
Ma fixed (kinet re-derives `nu_l` from the grid, Section 4) and scale `temporal.grid` with `N`
(acoustic scaling): for the shear layer, 2500, 5000, 10000, 20000 steps reach the physical time
2.2553. The initial condition is a function of the cell centres, so the shear layer and the
Taylor–Green vortex are the same continuum field on every grid (`kinet/initialization/shear_layer.py`,
`box_fractions`; `simulations/taylor_green_vortex/initialize.py`, `_build_coordinate_grid`), but
the random-mode field is not (c). Frames at the same physical time have stored index
`i * N / 256` on the N grid; this repository's `frame_stride` option does that alignment for the
old layout (`fmeval/data/kinet_raw.py`, `frame_stride`). A campaign over the four grids is one
`kinet.campaigns.grid.run` spec with a `zip` axis over `case.discretization.spatial.grid` and
`case.discretization.temporal.grid` (`campaigns/grid/simulate.yaml` header; `docs/tutorials/grids.qmd`;
not executed). The matched physical time itself was verified at 32² and 64² (Section 4).
The compressibility error `O(Ma²)` is the same on every grid under acoustic scaling, so a
refinement study of the incompressible limit needs diffusive scaling instead
(`docs/units/discretization.qmd`, "Time-step scaling laws"); kinet exposes that choice only
through the `optimize_grid` app (`OptimalDerivationConfig.scaling`, `kinet/config/common/discretization.py`,
line 88), not as a rescaling of a provided grid.

**(e) Every step for a window and every Nth step after.** `io.save_every_n` and `io.save_burst`
are constants for the run (`kinet/config/components/io.py`). The way to get a dense window is to
run the first segment with `save_every_n=1` and resume with a changed cadence. *Verified by
running* (`$EX/c6/data_B`): the resume accepts the changed cadence (`io` is "warn only" in
`DEFAULT_SIMULATE_POLICY`), and the file holds every step up to the interruption and every tenth
step after it, counted from the resume step. The first segment has to be stopped by a signal
(SIGTERM, SIGUSR1) or the walltime drain, because a segment that runs to completion leaves no
checkpoint to resume from. `save_burst: k` records `k` consecutive steps at every
`save_every_n`-th step, which gives short dense windows at a regular spacing without a resume
(`configs/io/hdf5_async.yaml`, `save_burst` comment; verified, `$EX/c4/data_o5`: n = 5, k = 2
saved steps 1, 4, 5, 9, 10, 14, 15, 19, 20). A runtime-control track can ramp a forcing
knob or an inlet during the run, but no track binds to the IO cadence in the cases read
(`simulations/testing/control_forcing_pulse.yaml`; `docs/utils/runtime-control.qmd`, not read).

## 7. Forcing and stationarity

A statistically steady forced run is possible with the `linear` law (Lundgren; Rosales and
Meneveau 2005; Bassenne et al. 2016) or the `random_modes` law (Eswaran and Pope 1988), on the
weakly compressible physics; both were run to a stationary state on 128³ D3Q27 BGK for 30000
steps, and the docs record that the projected linear law reaches `l/L = 0.166` against the
published 0.19, that there is no inertial range at Re 1000, and that the shipped cases "do not
claim a stationary inertial range, 2D turbulence, isotropy on a rectangular domain or
prescribed-power forcing" (`docs/kinetic-theory/forcing-laws.qmd`, "Turbulence validation";
`docs/lattice-boltzmann/forcing.qmd`, "Limits"). Two cautions from the same pages: an unprojected
linear law amplifies acoustic modes (`solenoidal: true` is mandatory for long runs), and entropic
BGK with a body force is about 100 times slower per step than BGK and its stabilizer "measures
the size of the force" (`docs/lattice-boltzmann/forcing.qmd`, table under "What the collision
does with it"); the shipped forced cases use plain BGK with the polynomial equilibrium. For a 2D
forced run the config is the HIT 2D case plus
`+forcing@case.physics.forcing_term=linear case.physics.forcing_term.solenoidal=true
case.physics.forcing_term.rate_policy=bassenne case.physics.forcing_term.target_u_rms=<u'>` or
`+forcing@case.physics.forcing_term=random_modes`, with `collision@case.collision=bgk` and
`equilibrium_closure/numeric@case.simulate_equilibrium_closure.F=polynomial`
(`docs/tutorials/config.qmd`, "Attaching a preset group to a case").

*Corrected by running* (`$EX/c9/`, 64², 300 steps). The overrides above **fail** as written
(executed, failed: "The BGK collision relaxes with the physics' time scale and discards a
stabilizer ('entropic')"), because the HIT case also selects an entropic stabilizer. Removing
it makes both laws compose and run (executed, worked):

```bash
python -m kinet.apps.simulate case=homogeneous_isotropic_turbulence/Re-50k_Ma-1en1 \
    case.discretization.spatial.grid=[64,64] case.discretization.temporal.grid=300 \
    collision@case.collision=bgk '~collision/stabilizer@case.collision.stabilizer' \
    equilibrium_closure/numeric@case.simulate_equilibrium_closure.F=polynomial \
    +forcing@case.physics.forcing_term=random_modes \
    io.save_every_n=10 io.record_distributions=false io.record_equilibria=false \
    launch.device=cpu launch.compile=false paths.data_root=$EX/c9/data_rm
# the linear law: replace the forcing line with
#   +forcing@case.physics.forcing_term=linear case.physics.forcing_term.solenoidal=true \
#   case.physics.forcing_term.rate_policy=bassenne case.physics.forcing_term.target_u_rms=<u'>
```

What the short runs showed (mean kinetic energy `K` over its initial value `K0`; an unforced BGK
run of the same case is `data_unforced`):

| Run | `K/K0` at steps 1, 100, 200, 300 | Comment |
|---|---|---|
| unforced | 0.934, 0.965, 0.963, 0.962 | decays slowly after the start-up transient |
| `random_modes`, preset values (`variance: 1e-8`, `maximum_mode: 2`) | 0.935, 1.018, 0.989, 1.039 | bounded over 300 steps, 43 ms per step on CPU |
| `linear`, `bassenne`, `target_u_rms=0.0333` | identical to the unforced run | **the force is inactive**: the 2D initial field already has a per-component rms of `0.0577/sqrt(2) = 0.041`, above the target, so this target (copied from the 3D case) does nothing in 2D at Ma 0.1. It also cost 0.66 to 0.77 s per step on CPU |
| `linear`, `bassenne`, `target_u_rms=0.05`, on the GPU (`data_lin05_gpu`) | rises from 0.936 to 0.998 by step 300 | bounded, approaching the target `K = 0.0025 = 1.5 K0` slowly; 300 steps in 3.4 s |

Three hundred steps is about one large-eddy turnover (an estimate: an eddy of `N / k0 = 16`
cells crossed at `0.058` cells per step takes about 280 steps), so these runs show that the
configuration composes and stays bounded at first, not that it reaches a stationary state.
The missing drag was confirmed by trying: `case.physics.forcing_term.rate=-1e-3` on the linear
law is refused by validation at `case.physics.forcing_term.linear.rate` (the `gt=0` bound), and
`+case.physics.forcing_term.minimum_mode=1.0` on `random_modes` is refused with "Extra inputs are
not permitted", so there is no key to keep the forcing off the lowest modes
(`$EX/c9/log_neg.txt`, `log_min.txt`). The HIT case keeps `initialization_policy: analytic`
under forcing and was not refused. A compressible forced run
with shocklets is not supported: the energy source is not mapped into the thermal `F`/`G`
populations (`docs/kinetic-theory/forcing-laws.qmd`, "Compressible turbulence and shocklets").

**No large-scale drag or hypoviscosity** (grep of `kinet/forcing`, `kinet/subgrid`, `kinet/physics`
and the two forcing pages for "drag", "hypovisc", "friction": only the porous-medium
Darcy–Forchheimer drag, which needs a porosity field, and a passing mention of "a linear drag" in
`kinet/physics/base/moment_source.py` line 89). Without it a forced 2D run condenses energy at the
box scale (the inverse cascade), so a stationary 2D inertial range is not available as shipped.

**Adding a forcing law.** Copy `kinet/forcing/laws/constant.py` (102 lines): a config class in
`kinet/config/components/forcing.py` with a new `type` literal, added to the `LeafForcingTermConfig`
and `ForcingTermConfig` unions; a `ForcingLaw[YourConfig]` subclass decorated
`@register_forcing("your_name")` whose `calculate_sources` returns
`{"momentum": carrier * acceleration}` of shape `(B, D, *spatial)`; an import line in
`kinet/forcing/plugins.py`; and a preset `configs/forcing/your_name.yaml` with a header comment
(not tried; it changes kinet)
(`kinet/forcing/registry.py`; `kinet/forcing/law.py`, class `ForcingLaw` docstring;
`configs/README.md`, "What a preset looks like"). A linear drag `-alpha (u - mean u)` is the
`linear` law with a negative rate and the `gt=0.0` validator removed, about ten lines, and a
hypoviscosity `-nu_h (-Laplacian)^{-p} u` is a Fourier-space law of the same shape as the
solenoidal projection in `laws/linear.py`. The host also has an `implicit_stepping` flag for a
drag that is stiff on one step (`kinet/forcing/law.py`, attribute list). A project can register a
law without editing kinet through the `plugins:` list of `configs/config.yaml`
(`docs/tutorials/plugins.qmd`, not read in full).

## 8. What kinet cannot do (as far as found)

- **Start a simulation from a stored frame, or perturb a stored state**: no config key or hook
  (Section 6a, 6b). Python route only, and that route works without changing kinet (executed,
  `$EX/c7/`; bit-for-bit continuation when the stored `F` is handed over).
- **Score the oblique Riemann case with `kinet.apps.verify`**: the case header names a
  `verify.py` that is not in `simulations/oblique_riemann/` on `perf/cleanup` (executed,
  failed; Section 3c).
- **An ensemble of HIT members in one run**: `N_simulations > 1` fails on the HIT case
  (Section 6c).
- **A manufactured-solution source term** for the weakly compressible or compressible physics:
  not found (grep "manufactured" over `kinet/`, `docs/`, `simulations/` hits only two acoustic
  research notes). The `constant` and `multipole_sources` laws are the only spatially prescribed
  sources, and `constant` is uniform.
- **A linear drag, friction or hypoviscosity** for stationary 2D turbulence: not found
  (Section 7); the `linear` law refuses a negative rate.
- **A sinusoidal Kolmogorov force**: not found; the `kolmogorov` group is a shear layer.
- **A 2D Sedov–Taylor or Noh case**: the shipped Sedov is 1D planar (`simulations/sedov/default.yaml`,
  `grid: [800]`); the 2D PonD shock cases are the oblique Riemann tubes, the double Mach reflection,
  the Richtmyer–Meshkov case (`rmi_heavy_to_light/default.yaml`, not read) and the isentropic
  vortex. A 2D Sedov would be a new case with the Riemann painter or a new initializer; the
  ExactPack reference wraps the planar solution only (`simulations/sedov/reference.py`, header of
  `kallikounis_2022.yaml`).
- **Forced compressible turbulence with shocklets**: the energy source is not applied to the
  thermal populations (`docs/kinetic-theory/forcing-laws.qmd`, last section). Decaying
  compressible turbulence with a real pressure exists only as the magnetised
  `compressible_mhd/random_turbulence` case; an unmagnetised `compressible_fluids` random
  initial condition was not found.
- **A dense-then-sparse output cadence in one run**: not without a resume or `save_burst`
  (Section 6e); the resume route was verified.
- **Reading the old flat files, or writing them**: no reader or writer in the current tree
  (Section 5); the `_shards`, `_downsampled-*` and `_well-format` copies were made by tools not
  in the tree.
- **The HIT 2D data the catalog cites** at `datasets/kinet/homogeneous_isotropic_turbulence/`
  (1.6 TB, 128², 256², 512²; `FUTURE_EXPERIMENTS_CATALOG.md`, Section 1.3) is **no longer at that
  path** (`ls datasets/kinet/` on 2026-11-26 shows no such directory; the parent changed on
  2026-11-06). The `hit_scaling` archive above is its successor.
- **The 512² and 20000-step full tiers of the Re 50k ensemble** were deleted after downsampling;
  only the 256 tiers remain (Section 6c).

## 9. Quick reference

| Key (YAML path) | Where | Meaning |
|---|---|---|
| `case=<group>/<id>` | CLI | the case file `simulations/<group>/<id>.yaml` |
| `case.discretization.spatial.grid` | case | cells per axis; `length` is derived at `resolution: 1` |
| `case.discretization.temporal.grid` | case | LBM steps; PonD cap on accepted steps |
| `case.discretization.temporal.length`, `.type: adaptive` | case | PonD end time and adaptive step |
| `case.physics.type` | case `defaults: /physics:` | the physics |
| `case.physics.parameters.reynolds`, `.mach` | case | set `nu_l = Ma c_s N_x / Re` (weakly compressible) |
| `case.physics.parameters.reference.density`, `.length` | case | reference density; the length Re is measured on (default `N_x`) |
| `case.physics.parameters.specific_heat_ratio`, `.dynamic_viscosity`, `.prandtl`, `.freestream_hold` | case | compressible physics |
| `case.physics.parameters.initialization_policy: analytic` | case | apply the group's non-equilibrium seed (`fneq_*`) |
| `case.physics.output_variables` | case | derived fields recorded: `vorticity`, `dilatation` (verified); `mach` only for a gas with a specific heat ratio; `all` records none (verified) |
| `case.physics.forcing_term.{type, rate, rate_policy, target_u_rms, solenoidal, seed, correlation_time, variance, maximum_mode, force, terms}` | case | the forcing law and its knobs |
| `case.initial_conditions.{lambda, epsilon}` | case | shear layer |
| `case.initial_conditions.{k0, random_seed, density, velocity}` | case | isotropic turbulence |
| `case.initial_conditions.{k}` | case | Taylor–Green |
| `case.initial_conditions.{interface, left, right, normal, boost}` | case | Riemann problem |
| `case.boundary_conditions` | case | `Periodic: {axes: [x, y]}` or per-face `x: {low: {type: inlet}, high: {type: neuman}}` |
| `case.N_simulations` | case | members stepped as a batch (leading HDF5 axis) |
| `case.lattice.{type, shifts, use_static_weights}` | case | velocity set |
| `case.collision.type`, `case.collision.stabilizer` | case | collision and its relaxation scale; switching an entropic case to BGK is `collision@case.collision=bgk '~collision/stabilizer@case.collision.stabilizer'` (verified) |
| `case.simulate_equilibrium_closure.F` | case | the numeric equilibrium (`entropic`, `polynomial`, ...) |
| `case.units` | case | `lattice`, `SI`, `CGS`, `custom` |
| `solver=pond_dugks`, `solver.cfl` | CLI/case | the finite-volume family and its CFL number |
| `io.save_every_n`, `io.save_burst` | io preset or `io.` override | output cadence |
| `io.record_distributions`, `io.record_equilibria` | same | populations on disk |
| `io.compression`, `io.blosc2_cname`, `io.compression_level` | same | `null`, `gzip`, `lzf`, `blosc2` |
| `io.async_writer`, `io.async_queue_memory_fraction` | same | background writer |
| `io.save_results=false` | same | run without writing a rollout |
| `precision.dtype` | root | `torch.float64` default; `torch.float32` computes in single precision but still writes float64 (verified) |
| `launch.device`, `launch.seed`, `launch.compile` | root `launch` preset | device (changes the HIT field of a seed, not the identity key), global torch/numpy seed (no effect on the HIT field), `torch.compile` (verified) |
| `KINET_PROJECT` | environment | the kinet checkout; required when running from outside it (verified) |
| `launch.tracker.enabled` | same | Weights & Biases logging (on in `perlmutter_*` presets) |
| `paths.data_root` | root | where `{group}/{case_id}/{identity_key}/tiers/full/rollout.h5` goes; default `./datasets`, relative to the working directory; the key is 8 hex characters and leaves out every `io.*` setting (verified) |
| `paths.run_dir`, `paths.resume_from`, `hydra.run.dir` | root | run directory |
| `runtime_logging.every_n` | root | console cadence |
| `domain_decomposition.enabled`, `.mesh_shape`, `distributed=torchrun` | root | multi-GPU simulate |
| `task=coarse_grain task.targets_spatial=[N,N] task.temporal_factor=<multiple of save_every_n>` | CLI | make a tier (verified; without the temporal factor it fails on a thinned run) |

## Verified by running (2026-11-26)

Every run used kinet's `.venv` as it is, branch `perf/cleanup` at `d1cd353b8`, the environment
script `$EX/_meta/env.sh` (Section 2), and a working directory under
`$EX = /pscratch/sd/k/khegazy/kinet_examples`. Each run folder holds the Hydra `outputs/`, the
`data*/` roots and a `log_*.txt` per run.

| # | Check | Command (abridged; all with `launch.compile=false` unless noted) | Result | Output |
|---|---|---|---|---|
| 1 | The command composes | `simulate case=doubly_periodic/shear_layer case.discretization.spatial.grid=[64,64] case.discretization.temporal.grid=100 launch.device=cpu paths.data_root=$EX/c1/data` | worked; 14 s rollout, 7.2 steps/s; key `0e8839ca` (8 hex characters); run directory relative to the working directory, no `.hydra/` | `$EX/c1/` |
| 2 | Output layout | `python $EX/_meta/h5tree.py <rollout.h5>` | grouped layout as in Section 5; pressure is `(rho - 1)/3`; extra `VTKHDF` group; five identity digests | `$EX/c1/` |
| 3 | HIT seeds | `simulate case=homogeneous_isotropic_turbulence/Re-50k_Ma-1en1` at 64² and 32², 10 steps, seeds 42 and 7, `launch.seed=1`, `launch.device=cuda`, `case.N_simulations=2` | same seed and grid: bitwise equal; other seed or grid: uncorrelated; `launch.seed`: no effect; **CPU and GPU differ** under one key; `N_simulations=2` fails (two attempts) | `$EX/c3/` |
| 4 | Output controls | `io.save_every_n=5`, `io.save_burst=2`, `io.record_distributions=false io.record_equilibria=false`, `io=hdf5_async_compression`, `precision.dtype=torch.float32`, `case.physics.output_variables=[...]` | all names work; step 1 always saved; 56 not 40 bytes per cell without populations; float32 still stored as float64; `mach` refused, `all` drops vorticity; blosc2 needs `hdf5plugin` | `$EX/c4/` |
| 5 | Units | shear layer 32² by 100 steps and 64² by 200 steps, `io.save_every_n=10` | `nu_l = Ma c_s N / Re` confirmed; equal `time_convection` at the end (0.180422); vorticity is the D2Q9 stencil curl in `1/step` | `$EX/c5/` |
| 6 | Resume | 64² by 300 steps under `timeout -s TERM 20`, then the same command; also a resume with `io.save_every_n=10` | resumed from `simulation_checkpoint_step-114.pt`, bitwise equal to an uninterrupted run; cadence change accepted and restarts at the resume; a finished run is rerun from scratch | `$EX/c6/` |
| 7 | Python `initial_state` route | `python $EX/_meta/branch_from_frame.py <src> <out> <amp> <macros\|F>` | works unmodified; needs `temperature: 1/3`; macro-only start has a 4.4e-3 velocity jump at step 1; with stored `F` the continuation is bitwise | `$EX/c7/` |
| 8 | Compressible with pressure, and `verify` | `simulate case=sod/subsonic case.discretization.spatial.grid=[301,5] case.discretization.temporal.grid=100`; `simulate case=oblique_riemann/default` at 32² (CPU) and 64² (GPU); `verify case=oblique_riemann/default ... task.steps=2` | Sod and PonD store absolute pressure `p = rho T`; **verify failed**: no `simulations/oblique_riemann/verify.py` | `$EX/c8/` |
| 9 | Forcing | HIT 64² by 300 steps with BGK, polynomial equilibrium, `~collision/stabilizer@...`, and `random_modes` or `linear` (`solenoidal=true`, `bassenne`) | the guide's overrides fail without removing the stabilizer; with it both run and stay bounded; `target_u_rms=0.0333` leaves the linear law inactive in 2D; a negative rate and a `minimum_mode` key are refused | `$EX/c9/` |
| 10 | Taylor–Green | `simulate case=taylor_green_vortex/Re-50k_Ma-1en1 case.discretization.spatial.grid=[64,64] case.discretization.temporal.grid=500 case.physics.parameters.reynolds=100` | rms decay matches `exp(-2 nu_l k^2 t)` to 6e-4 in rate | `$EX/c10/` |
| – | Extras | `check ... check_yes=true`; `--cfg job`; `coarse_grain task.targets_spatial=[32,32]` with and without `task.temporal_factor=10`; composing without `KINET_PROJECT` | check and `--cfg job` work; coarse-grain needs the temporal factor; no project fails | `$EX/misc/` |

**Measured throughput** (rollout time only, after start-up; a cell-step is one cell advanced
one step). The CPU figures are from a shared login node, on which one run used about 20 cores,
so they are rough. The GPU is the login node's A100.

| Case, grid | Collision | Device | ms per step | Cell-steps per second | Output |
|---|---|---|---|---|---|
| shear layer, 64², default IO | entropic BGK | CPU | 138 | 3.0e4 | `$EX/c1/` |
| shear layer, 128², no populations | entropic BGK | CPU | 189 | 8.7e4 | `$EX/tput/` |
| shear layer, 128², no populations | BGK, polynomial | CPU | 49 | 3.3e5 | `$EX/tput/` |
| HIT, 64², `random_modes` | BGK, polynomial | CPU | 43 | 9.6e4 | `$EX/c9/` |
| HIT, 64², `linear` solenoidal | BGK, polynomial | CPU | 660 to 770 | 6e3 | `$EX/c9/` |
| Sod LBM, 301 by 5 | entropic, compressible | CPU | 130 | 1.2e4 | `$EX/c8/` |
| oblique Riemann PonD, 32² | DUGKS, D2Q16 | CPU | 7400 | 1.4e2 | `$EX/c8/` |
| shear layer, 128², no populations | entropic BGK | GPU, no compile | 16.8 | 9.8e5 | `$EX/tput/` |
| shear layer, 128², no populations | entropic BGK | GPU, `torch.compile` (23 s warm-up) | 3.6 | 4.6e6 | `$EX/tput/` |
| shear layer, 128², no populations | BGK, polynomial | GPU, no compile | 2.2 | 7.6e6 | `$EX/tput/` |
| HIT, 64², `linear` solenoidal | BGK, polynomial | GPU, no compile | 11 | 3.6e5 | `$EX/c9/` |
| oblique Riemann PonD, 64² | DUGKS, D2Q16 | GPU, no compile | 1250 | 3.3e3 | `$EX/c8/` |

For sizing: the entropic shear layer at 256² by 10000 steps is about 2 hours on this CPU and,
at the compiled GPU rate, about 2.5 minutes, if the rate per cell holds at the larger grid.
That last step is a conjecture: at 128² the GPU is probably limited by kernel launches rather
than arithmetic, so the rate per cell at 256² and above is likely higher, not lower. The PonD
solver is slow on both devices without compilation; a 200² oblique Riemann run to `t = 0.2` was
not attempted.

**What is on scratch.** `$EX` holds about 0.58 GB in the folders `c1`, `c3` to `c10`, `misc`,
`tput` and `_meta` (scripts, environment, and the before and after listings of the kinet
tree's ignored files). None of it is a dataset; it may be deleted.

## Confidence

- **Sure, verified by running on 2026-11-26** (the table above): the grouped layout, its
  shapes, attributes, units and clocks; the viscosity rule, the convective time and the acoustic
  scaling of steps; that stored vorticity is the D2Q9 stencil curl; the HIT seed behaviour,
  including its dependence on the device and the failure of `N_simulations > 1`; the identity
  key's length and what enters it; the resume mechanism and the cadence change across a resume;
  the output controls; the Python branching route; the forcing composition; the bytes per cell.
- **Sure, read in code and verified on existing files** (first pass): the list of forcing laws,
  initializers, boundary types and cases; the existence, layout, count and cadence of the
  `hit_scaling` archive; the stored fields of the Sod and obstacle files.
- **Measured, but only on tiny runs**: throughput, compression ratio, the size of the HIT
  start-up transient and of the macro-only branching transient. Each may change at production
  grids.
- **Reasoning, not verified by running**: the bit-level agreement of a rerun with the old files
  (one lattice flag differs); that a perturbation added to `F` as a difference of equilibria
  avoids the branching transient; that GPU throughput per cell improves above 128².
- **Not executed**: installation, Slurm submission, domain decomposition, grid campaigns, the
  full-size worked examples, `--info defaults`.
- **Not checked**: `docs/tutorials/library.qmd`, `plugins.qmd`, `runtime-control.qmd`,
  `rmi_heavy_to_light/default.yaml`, the `changes_while_running_hit`
  branch beyond the files cited, and whether the branch's 2D linearly forced case ever ran.
