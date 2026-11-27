# kinet run configurations

This folder keeps the solver configuration of every kinet run that a dataset of this
repository reads, so that each run can be reproduced from scratch without the scratch file
system, which is purged. It is step 31 of `dataset_specs/BUILD_ORDER.md`, made on 2026-11-27
after Kareem's decision 13 ("Make sure you have the config files for all kinet runs (even
those that are already done) so that you can reproduce them in the future from scratch").

Each dataset has a subfolder, and each run in it a subfolder named by its identity key (the
short hexadecimal digest that kinet puts in the run's directory and file name). The files are
byte-identical copies of what was found; none was reformatted. A section below covers each
dataset: where its data is, which files were copied, the kinet commit and device where they are
recorded, the command that reproduces the run, and what stands in the way of an exact
reproduction.

## Rule for every new kinet run

Every kinet run made for this plan leaves the following here, in
`docs/datasets/logs/kinet_runs/<dataset>/<identity key>/`, in the same change that adds or
updates the dataset, and before the run's scratch folders can be purged:

1. **`config.yaml`**, the saved run configuration from beside the data
   (`<data_root>/<group>/<case_id>/<identity key>/config.yaml`).
2. **`resolved_config.yaml`** and **`run_provenance.yaml`** from the run directory
   (`outputs/<group>/<case_id>/simulate/job_<stamp>/`, relative to the working directory the
   command was started in). The provenance file records the Hydra overrides, the kinet commit
   (`git_sha`), the host and the Slurm job id. A run that is post-processed by another kinet
   app (`coarse_grain`, for example) also leaves that app's two files, in a subfolder named
   after the app.
3. **A section in this README** that states, in full sentences:
   - the exact command, with the environment variables and the working directory;
   - the kinet branch, the commit, and whether the kinet tree had uncommitted changes
     (`git -C <kinet> status --short`). The provenance file records only the commit, and the
     isotropic archive below shows why that is not enough: those runs depended on case files
     that were not committed at the time;
   - the device (CPU, or the GPU model) and the torch version
     (`python -c "import torch; print(torch.__version__)"`), because the isotropic initial
     condition differs between CPU and GPU for the same seed;
   - the Slurm job id;
   - every step after the simulation (coarse-graining, thinning, `python -m
     fmeval.data.convert_kinet`), with its command;
   - any launch script that is not committed to kinet, copied into the dataset's folder.

The commands below assume this environment, from `dataset_specs/00_how_to_use_kinet.md`,
Section 2:

```bash
source /global/u2/k/khegazy/projects/pde/kinet/.venv/bin/activate
export KINET_PROJECT=/global/u2/k/khegazy/projects/pde/kinet   # required outside the checkout
export PYTHONDONTWRITEBYTECODE=1 WANDB_MODE=disabled
cd $PSCRATCH/kinet_runs   # any working directory outside the kinet checkout
```

A finished run is overwritten, not skipped, when the same command is launched again with the
same `paths.data_root` (`00_how_to_use_kinet.md`, Section 3). Use a fresh data root for a
reproduction.

## How these files were made and checked (2026-11-27)

- **Copies.** 137 configuration and provenance files were copied with `shutil.copyfile` and
  compared byte for byte with their sources. Eight more files are launch scripts and case
  files of the isotropic runs (`kinet_hit_launch/`); the six from the kinet branch were
  written with `git show` and the two from scratch with `cp`, and each was compared with its
  source. With this README, the folder holds 146 files. No file contains an email address, a
  token, a password or another credential (searched with a regular expression before copying).
- **Safe read.** Every YAML file was read with `yaml.safe_load`. The 13 configurations written
  by the kinet of April and May 2026 (the shear layer, Sod and cylinder runs) fail with
  `ConstructorError: could not determine a constructor for the tag
  'tag:yaml.org,2002:python/object/apply:kinet.config.common.collision.CollisionType'`. They
  were not read with an unsafe loader. The other 127 parse.
- **The current kinet's case model.** The case block of an isotropic `config.yaml` was
  validated against `kinet.config.case_models.CaseConfig` on the current kinet (branch
  `perf/cleanup`, commit `d1cd353b8`). It is refused: `physics` is missing, and `experiment`,
  `scheme`, `simulate_closure` and `simulate_stability` are not permitted. These are the keys
  that were renamed later (`group`, `physics`, `simulate_equilibrium_closure`,
  `collision.stabilizer`). So no old configuration loads on the current kinet as it stands.
  Each run is reproduced instead by a case and overrides, below.
- **Composition.** Each command marked *composes* was run through kinet's own check app,
  `python -m kinet.apps.check <same overrides> task=<task> check_yes=true`, which validates the
  run configuration and writes only a `resolved_config.yaml` into the working directory. It was
  run from a scratch folder outside the kinet tree. **No simulation was run**, so every
  reproduction command below is *not executed*.
- **The branch that made the isotropic runs** was exported with `git archive
  changes_while_running_hit kinet configs experiments pyproject.toml` into a scratch folder,
  which reads the repository and changes nothing in it, and the check app was run on that
  export with `KINET_PROJECT` and `PYTHONPATH` pointing at it. The kinet repository was not
  checked out or modified.

## The shear layer (`kinet_re5e4`, `kinet_re5e4_dev`, `kinet_re5e4_512`, `kinet_re1e6`)

These runs share one physics: the doubly periodic double shear layer (`lambda: 80`,
`epsilon: 0.05`, density 1), weakly compressible and isothermal, Mach 0.1, D2Q9, entropic BGK
with the entropic stabilizer (`max_iterations: 50`), the entropic equilibrium closure for F,
`use_static_weights: false`, float64, recording vorticity. They differ in Reynolds number,
grid and step count. They were made by an older kinet (configuration keys
`spatiotemporal_grid`, `solver.system_parameters`, `neurde`, `stability`, `pred_length`,
`units: dimensionless`) and stored in the flat layout with the populations F, F_collided and
Feq at every step.

**What is recorded.** Only the configuration. No kinet commit, branch, device, Slurm job id or
command is recorded: not in the configuration, not in the files' root attributes (which hold
only `characteristic_scales`, `discretization`, `units` and the `kinet_*` status counters),
and not in the `slurm_logs/` folders beside the data, which are empty. No run directory of these
runs was found under kinet's `outputs/` on scratch.

**The current kinet's route.** The shipped case `doubly_periodic/shear_layer` has this physics
at 512² and 20 000 steps with `use_static_weights: true` (from `configs/lattice/d2q9.yaml`).
With the overrides below, the composed configuration matches the old one in every physical
setting listed above (compared by eye, key by key). The commands follow decision 4 of
`BUILD_ORDER.md` and store the macroscopic observables only. The old runs stored the
populations as well; removing the two `io.record_*` overrides stores F and Feq again, and
F_collided can no longer be recorded.

**Obstacles to an exact reproduction, common to these runs:**

1. The old configurations do not load (above), so the run is rebuilt from a case and overrides.
2. The kinet commit is not recorded, so the code that made them is unknown. Two old runs of
   the same configuration already differ at round-off: `kinet_re5e4_dev` (`04a8a1`, file dated
   2026-05-07) equals `kinet_re5e4` (`dc804f`, 2026-04-26) exactly at step 0, differs by
   2.2e-16 in density at step 1, and by 9.0e-10 in density and 7.9e-10 in velocity at step 50
   (measured 2026-11-27 on the stored frames). The cause (a code change or another device) is
   not recorded.
3. The old `collision.enforce_positive: false` has no key in the composed configuration, and
   the current closure computes the non-equilibrium part of F for the stabilizer
   (`output_dists: neq`). Whether the stabilizer's algorithm is unchanged since the spring of
   2026 was not checked.
4. Whether the current initialiser places the nodes as the old one did is open
   (`docs/datasets/logs/reynolds_ladder_2d.md`, open points; spec 02, Sect. 5.1).
5. The device is not recorded.

**What would be reproduced instead:** the same flow, up to round-off at first; the flow is
chaotic, so the trajectories would decorrelate over time. Statistical equivalence is expected
but not verified (my reasoning). Bit-identity is not expected.

### `kinet_re5e4`: `dc804f`

- **Data:** `/global/cfs/cdirs/m4790/Data/kinet/doubly_periodic/weakly_compressible_isoT_fluids/sys_Re-5e4_Ma-1en1/D2Q9_shape-256-256_T-10000_H-dc804f.h5`
  (256², 10 000 steps, Re 5e4, 167 GiB, dated 2026-04-26). Files of the same name sit in
  `sim_test/` (8 KB larger) and `single_sim/` (the same size) beside it; they were not compared
  with it.
- **Copied:** `kinet_re5e4/dc804f/dc804f.yaml`, from `configs/dc804f.yaml` beside the data.
- **Derived copies with no configuration of their own:** the Well-format files `well_re5e4`
  reads (`..._H-dc804f_well-format.h5` and the `_well-format/data/{train,valid,test}/` folder,
  float32, macroscopic fields only), and `_first_half_well-format` and `_testing_well-format`.
  The tool that made them is not in the current kinet tree and its command is not recorded.
  kinet commit `149041184` (2026-06-25) deleted `kinet/data/generators/TheWell/`; whether that
  was the tool was not checked. A regenerated Well copy can be verified against `dc804f` by the
  data-marked test `test_raw_and_well_readers_agree_on_the_same_simulation`.
- **Command** (composes; not executed):

  ```bash
  python -m kinet.apps.simulate case=doubly_periodic/shear_layer \
      'case.discretization.spatial.grid=[256,256]' case.discretization.temporal.grid=10000 \
      case.physics.parameters.reynolds=50000 case.lattice.use_static_weights=false \
      io.record_distributions=false io.record_equilibria=false \
      paths.data_root=$PSCRATCH/kinet_datasets
  ```

  The output is in kinet's grouped layout; `python -m fmeval.data.convert_kinet SRC DST`
  turns it into the flat layout the `kinet_raw` reader opens.
- **Reproducible exactly:** no, for the common obstacles above.

### `kinet_re5e4_dev`: `04a8a1`

- **Data:** `.../sys_Re-5e4_Ma-1en1/D2Q9_shape-256-256_T-100_H-04a8a1.h5` (100 steps, dated
  2026-05-07). It is its own run, not a slice of `dc804f`, although `latest.h5` points at it.
- **Copied:** `kinet_re5e4_dev/04a8a1/04a8a1.yaml`. It differs from `dc804f.yaml` only in the
  step count.
- **Command** (composes; not executed): the `dc804f` command with
  `case.discretization.temporal.grid=100`.
- **Reproducible exactly:** no; see the round-off comparison above.

### `kinet_re5e4_512`: `56d32e`

- **Data:** `.../sys_Re-5e4_Ma-1en1/D2Q9_shape-512-512_T-20000_H-56d32e.h5` (512², 20 000
  steps, 1.43 TB, dated 2026-04-26), with downsampled copies to 128², 64², 32² and 16² and their
  `_shards` folders beside it (made by a tool not in the current kinet tree).
- **Copied:** `kinet_re5e4_512/56d32e/56d32e.yaml`. It differs from `dc804f.yaml` only in the
  grid and the step count.
- **Resumed:** the root attributes give `kinet_segment_pred_length` 6254 of 20 000, so the
  run was resumed at least once. The guide verified that a resume on the current kinet is
  bitwise exact (`00_how_to_use_kinet.md`, Section 3), so this is no obstacle in itself.
- **Command** (composes; not executed): the `dc804f` command with
  `'case.discretization.spatial.grid=[512,512]' case.discretization.temporal.grid=20000`.
  About 19 minutes of stepping on one A100 (`BUILD_ORDER.md`, "How jobs are run"), so one
  30-minute debug job.
- **Reproducible exactly:** no, for the common obstacles above.

### `kinet_re1e6`: `85db0e`

- **Data:** `/global/cfs/cdirs/m4790/Data/kinet/doubly_periodic/weakly_compressible_isoT_fluids/sys_Re-1e6_Ma-1en1/D2Q9_shape-1024-1024_T-40000_H-85db0e.h5`
  (1024², 40 000 steps, 11.4 TB, dated 2026-04-26). Resumed (last segment 964 steps).
- **Copied:** `kinet_re1e6/85db0e/85db0e.yaml`. It differs from `dc804f.yaml` only in the
  Reynolds number, the grid and the step count.
- **Command** (composes; not executed):

  ```bash
  python -m kinet.apps.simulate case=doubly_periodic/shear_layer \
      'case.discretization.spatial.grid=[1024,1024]' case.discretization.temporal.grid=40000 \
      case.physics.parameters.reynolds=1000000 case.lattice.use_static_weights=false \
      io.record_distributions=false io.record_equilibria=false \
      paths.data_root=$PSCRATCH/kinet_datasets
  ```

  It needs a longer job than the debug queue allows, after a short debug test of the same
  configuration (`BUILD_ORDER.md`, "How jobs are run").
- **Reproducible exactly:** no, for the common obstacles above.

### Other 256² runs under `prev_256/`

None of these is read by a dataset configuration; their configurations are kept because the
data is on disk.

| Key | Steps | Data under `.../sys_Re-5e4_Ma-1en1/prev_256/` | Differs from `dc804f.yaml` in |
|---|---|---|---|
| `131010` | 20 000 | `D2Q9_shape-256-256_T-20000_H-131010.h5` (357 GB, 2026-04-19) | the step count, and IO keys of an older schema |
| `b6e704` | 10 000 | `..._H-b6e704.h5` (178 GB, 2026-04-07), its Well copy and 128², 64² downsampled copies | an older schema (`density_init`, no `io` block) |
| `bd9b55` | 10 | `..._H-bd9b55.h5` and its Well copy | the same older schema, and the step count |
| `7677fc` | 12 500 | `..._H-7677fc.h5` (223 GB) | the step count |
| `90ef41` | 100 000 | `..._T-100000_H-90ef41.h5`, plus partial files `T-96840` and `T-97598` | the step count |

`131010` is the same trajectory as `kinet_re5e4`, continued to twice the time: its velocity
equals `dc804f`'s bit for bit at steps 0, 100 and 10 000 (measured 2026-11-27). Its command is
the `dc804f` command with `case.discretization.temporal.grid=20000` (composes; not executed);
the other four follow the same pattern with their step counts (not checked). The four
`..._T-999[6-9]_H-dc804f.h5` files and the 12.8 MB `..._T-10000_H-dc804f.h5` in `prev_256/`
are small files that carry the key `dc804f`; they were not opened.

The `configs/` folder beside the data holds eight more configurations with no data file in it
(`1fd039`, `35ce29`, `41910e`, `6a4b73`, `7ee857`, `88db66`, `9735aa`, `9fe003`); they were
not copied.

## `forecast_re5e4`: predictions with no solver configuration

- **Data:** `/global/cfs/cdirs/m4790/Data/results/entropic_D2Q9/` holds three folders,
  `F-906861_64`, `F-906861_64_Re_50k_from_256_to128` and `F-906861_64_Re_50k_from_256_to_64`,
  each with two files `forecast_t0-<start>.h5` (52.5 MB, 13.2 MB and 3.3 MB each), all dated
  2026-01-27 and owned by another project member's account. Nothing else is in the folders.
- **Copied:** nothing. There is no configuration, log, command or commit on disk, and the
  files carry no attributes (`docs/datasets/reynolds_ladder_2d.md`, "Forecast pairs").
- **What kinet's history shows** (found 2026-11-27; it identifies a lead, not the producer):
  - kinet commit `cb7224a45` (2026-05-07) has training configurations whose
    `from_pretrain` checkpoints sit under
    `.../EntropyRootDEQ_h64_i18/132b16_64/entropic_LatticeType.D2Q9/F-906861_64/...`, for
    example in `experiments/homogeneous_isotropic_turbulence/Re-50k_Ma-1en1/configs/train_128.yaml`.
    So `F-906861_64` names a directory of trained-model checkpoints.
  - The remote branch `origin/train_solver_from_256_to_128_64`, last commit 2026-01-25, two
    days before the files, adds "entropy root DEQ training configs for 256, 128 and 64
    resolutions".
  - **Conjecture (mine), not verified:** the predictions were made by a trained model
    (`EntropyRootDEQ`) from that run, at 256² and carried to 128² and 64², not by a plain
    solver run. The person who made the files can confirm it.
- **Command:** none. **Cannot be reproduced: no solver configuration, checkpoint path or
  command is recorded for these files.** If the conjecture holds, reproduction would need the
  model checkpoint and the inference command, which are outside this plan's scope (no
  machine-learning model is run here).

## Decaying isotropic turbulence (`kinet_hit_re12p5k`, `kinet_hit_re25k`, `kinet_hit_re50k`)

- **Data:** the archive `/global/cfs/cdirs/m4790/Data/neurde/hit_scaling/Re-{12p5k,25k,50k}_Ma-1en1_2d/<key>/`
  (`config.yaml`, `manifest.yaml`, `tiers/<tier>/rollout.h5`), and the 31 converted files under
  `/global/cfs/cdirs/m4790/Data/kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids/sys_Re-*_Ma-1en1/<key>.h5`
  (`docs/datasets/logs/decaying_isotropic_2d.md`).
- **Copied:** for each of the 31 converted runs and the long run of each Reynolds number, the
  archive's `config.yaml`, and the `resolved_config.yaml` and `run_provenance.yaml` of the run
  directory on scratch, found under
  `/pscratch/sd/k/khegazy/projects/pde/kinet/outputs/hit_scaling/<case>/simulate/ensemble/<job>_gpu<g>_<k>_seed<seed>/`
  by the seed in the directory name and the identity key in `simulation_subdir`. At Re 5e4 the
  simulation's two files are in `simulate/`, and those of the coarse-graining run (from
  `.../hit_scaling/{ensemble512,long512}_ledger/downsample/hydra/<seed>/`) are in
  `coarse_grain/`. The launch material is in `kinet_hit_launch/`: the branch's
  `slurm_scripts/submit_hit_ensemble.sh` and `downsample_hit_ensemble.sh`, its three decaying
  case files and `initialize.py` (`experiments_hit_scaling/`), and two scripts that exist only
  on scratch, `launch_after_ensemble.sh` (it launched the Re 5e4 long run) and
  `thin_every10.py` (it thinned the Re 5e4 tiers).
- **Configurations differ only in the seed.** Verified by comparing the files after removing
  the lines `random_seed`, `simulation_subdir` and `run_dir`: within each Reynolds number every
  `config.yaml`, `resolved_config.yaml` and coarse-graining `resolved_config.yaml` of the
  standard runs is identical, and the long run differs from them only in the step count
  (100 000, or 200 000 at Re 5e4).
- **kinet commit and branch:** every `run_provenance.yaml` records `git_sha:
  6ccfafc73829fbde3be2dd628ca1835da2c1715a` (kinet `main` of 2026-11-05). That is not the whole
  code: the case files `experiments/hit_scaling/*` were uncommitted in the working tree, and the
  coarse-graining changes were made in it during the campaign (`REASONS_FOR_CHANGES.md` on the
  branch, sections 2, 3 and 7). All of it was committed afterwards on the branch
  `changes_while_running_hit` (tip `37861b9fc`, 2026-11-16; also on `origin`). The branch's
  changes after `6ccfafc73` touch coarse-graining, video rendering, three type annotations in the
  MHD initializer, documentation and tests; none touches the simulation of these cases (read
  from `git diff --stat`). The branch tip is therefore the code to reproduce with.
- **Device:** GPU for every simulation (`++launch.device=cuda`, on Perlmutter GPU nodes, whose
  GPUs are A100s; the log of `c5ccb2` reports a 39.5 GB device), `torch.compile` on. The coarse-graining ran
  on CPU (`++launch.device=cpu`). The torch version is not recorded.
- **Initial populations:** the `hit_scaling` cases register `init_hit_forced`, the isotropic
  initializer without the non-equilibrium correction, so these runs started from the
  equilibrium populations of the random-phase field (the branch's `experiments/hit_scaling/initialize.py`).
  This corrects `00_how_to_use_kinet.md`, Section 6c, which calls the current case
  `homogeneous_isotropic_turbulence/Re-50k_Ma-1en1` "the same physics": that case uses
  `initialization_policy: analytic`, which adds the Skordos correction.

### Exact route: the branch's code, with each run's recorded overrides

This composes for all 34 runs: on the exported branch, the check app's resolved configuration
equals the archived `resolved_config.yaml` in every key except `paths.data_root` and
`paths.run_dir`, for all 34 simulations and all 11 coarse-graining runs (checked 2026-11-27).
Not executed.

```bash
git -C /global/u2/k/khegazy/projects/pde/kinet archive 37861b9fc kinet configs experiments pyproject.toml \
    | tar -x -C $PSCRATCH/kinet_hit_branch          # an empty folder; nothing is checked out
export KINET_PROJECT=$PSCRATCH/kinet_hit_branch PYTHONPATH=$PSCRATCH/kinet_hit_branch
# Re 1.25e4 and 2.5e4 (256^2, 10 000 steps; 100 000 for 6f5a2b and bd2304):
python -m kinet.apps.simulate case=hit_scaling/Re-12p5k_Ma-1en1_2d task=simulate \
    ++launch.device=cuda ++distributed.is_distributed=false \
    ++case.initial_conditions.random_seed=<seed> ++case.io.save_every_n=10 \
    ++case.io.record_distributions=false ++case.io.record_equilibria=false \
    ++paths.data_root=$PSCRATCH/kinet_datasets
# the long runs add ++case.discretization.temporal.grid=100000
# Re 5e4 (512^2, 20 000 steps, every step saved), then coarse-grained to 256^2:
python -m kinet.apps.simulate case=hit_scaling/Re-50k_Ma-1en1_2d task=simulate \
    ++launch.device=cuda ++distributed.is_distributed=false \
    ++case.initial_conditions.random_seed=<seed> ++case.io.save_every_n=1 \
    ++case.io.record_distributions=false ++case.io.record_equilibria=false \
    '++case.discretization.spatial.grid=[512,512]' ++case.discretization.temporal.grid=20000 \
    ++paths.data_root=$PSCRATCH/kinet_datasets
python -m kinet.apps.coarse_grain case=hit_scaling/Re-50k_Ma-1en1_2d task=coarse_grain \
    '++task.targets_spatial=[256,256]' \
    '++task.ignore_datasets=[mesoscopic/momentum_time_scale,mesoscopic/stability_scale]' \
    ++case.initial_conditions.random_seed=<seed> ++case.io.save_every_n=1 \
    ++case.io.record_distributions=false ++case.io.record_equilibria=false ++launch.device=cpu \
    '++case.discretization.spatial.grid=[512,512]' ++case.discretization.temporal.grid=20000 \
    ++paths.data_root=$PSCRATCH/kinet_datasets
python <this repository>/docs/datasets/logs/kinet_runs/kinet_hit_launch/thin_every10.py \
    $PSCRATCH/kinet_datasets/hit_scaling/Re-50k_Ma-1en1_2d/<key>/tiers/256/rollout.h5
# the long run bea170 uses 200000 steps in both commands
```

Then `python -m fmeval.data.convert_kinet <tier rollout.h5> <key>.h5` converts each run, as
`docs/datasets/decaying_isotropic_2d.md` describes. The original runs used `hydra.run.dir` to
name the run directory and were launched by `submit_hit_ensemble.sh` (four runs per GPU node,
debug queue) from the kinet checkout; the 12.5k and 25k runs wrote straight to the archive
(`data_root: datasets`, the checkout's link to `/global/cfs/cdirs/m4790/Data/neurde/`), and the
Re 5e4 runs went through `downsample_hit_ensemble.sh` (coarse-grain, check, copy to the archive
without `tiers/full/`, delete the scratch copy). The recorded overrides are in each
`run_provenance.yaml` (`hydra_overrides`); the seeds are below.

**Obstacles to an exact reproduction:**

1. **The device.** The seed reproduces its field only on the same kind of device; a CPU run
   gives an unrelated field under the same identity key (`00_how_to_use_kinet.md`, Section 6c).
   Whether two GPU runs of one seed agree bit for bit was not checked.
2. **The software.** The torch version and the state of `.venv` on 2026-11-06 are not recorded,
   and `torch.compile` was on.
3. **The branch-only code.** The case files and launch scripts exist only on
   `changes_while_running_hit`; the recorded commit `6ccfafc73` alone does not contain them.
4. **The Re 5e4 post-processing** depends on the branch's coarse-graining code and on
   `thin_every10.py`, which existed only on scratch and is now copied here.

**What would be reproduced:** on the branch's code and a GPU, the same run is expected to be
reproduced to round-off at least (my expectation; not verified). On a CPU, only a statistically
equivalent realisation.

### Current kinet: a statistically equivalent route

On the current kinet (`perf/cleanup`), the case that comes closest is
`homogeneous_isotropic_turbulence/Re-50k_Ma-1en1`. Its random-phase velocity synthesis
(`_rogallo_velocity_synthesis_2d`, `_passot_pouquet_spectrum`, `_build_wavenumber_grid`,
`_enforce_hermitian`, `_pressure_poisson_solve`) is identical to the branch's, comments and
docstrings aside (compared 2026-11-27); `init_hit` itself was refactored. This composes for
`c5ccb2` (simulate) and for `cf7333` (simulate and coarse-grain); not executed:

```bash
python -m kinet.apps.simulate case=homogeneous_isotropic_turbulence/Re-50k_Ma-1en1 \
    'case.discretization.spatial.grid=[256,256]' case.discretization.temporal.grid=10000 \
    case.physics.parameters.reynolds=12500 case.initial_conditions.random_seed=<seed> \
    case.initial_conditions.density=1.0 io.save_every_n=10 \
    io.record_distributions=false io.record_equilibria=false launch.device=cuda \
    paths.data_root=$PSCRATCH/kinet_datasets
```

**Cannot be reproduced exactly on the current kinet:** this case applies the Skordos
non-equilibrium correction to the initial populations (`initialization_policy: analytic`), and
setting `initialization_policy=equilibrium` is refused at run time because the case still
registers its corrector (`00_how_to_use_kinet.md`, Section 6c). The macroscopic initial field
of a seed should be the same on the same kind of device (my reasoning from the identical
synthesis code; not verified), but the first steps differ, and the identity key and folder
differ (`homogeneous_isotropic_turbulence/Re-50k_Ma-1en1/<8 hex characters>`). A kinet
addition that registers `init_hit_forced` for a 2D case would remove the first difference.

### The runs

`config.yaml` holds the seed under `case.initial_conditions.random_seed`. "Simulate" and
"coarse-grain" are the Slurm job ids recorded in the provenance files. The long runs are
`6f5a2b`, `bd2304` and `bea170`; `004ae2` is the converter's test file; the other 30 are the
drawn subset.

| Dataset | Key | Seed | Simulate | Coarse-grain |
|---|---|---|---|---|
| `kinet_hit_re12p5k` | `10383c` | 17940266470754760 | 60946934 | — |
| `kinet_hit_re12p5k` | `3519ce` | 17940256824018223 | 60946932 | — |
| `kinet_hit_re12p5k` | `3c2c65` | 17940261623340812 | 60946934 | — |
| `kinet_hit_re12p5k` | `6f3450` | 17940258615763301 | 60946933 | — |
| `kinet_hit_re12p5k` | `6f5a2b` (long) | 17940946168385530 | 60974403 | — |
| `kinet_hit_re12p5k` | `8a91f8` | 17940257272959581 | 60946933 | — |
| `kinet_hit_re12p5k` | `ad4dde` | 17940259570165601 | 60946932 | — |
| `kinet_hit_re12p5k` | `c5ccb2` | 17940260069416453 | 60946933 | — |
| `kinet_hit_re12p5k` | `e81d9c` | 17940266248824243 | 60946934 | — |
| `kinet_hit_re12p5k` | `f151b4` | 17940257265977533 | 60946933 | — |
| `kinet_hit_re12p5k` | `f3e96c` | 17940269563785333 | 60946935 | — |
| `kinet_hit_re25k` | `004ae2` | 17940275975826582 | 60947514 | — |
| `kinet_hit_re25k` | `0789a4` | 17940279376953770 | 60947550 | — |
| `kinet_hit_re25k` | `264498` | 17940288486064033 | 60948363 | — |
| `kinet_hit_re25k` | `2bf18d` | 17940289878432062 | 60948442 | — |
| `kinet_hit_re25k` | `49a8ad` | 17940286699580500 | 60948321 | — |
| `kinet_hit_re25k` | `6dd7f2` | 17940289878428443 | 60948442 | — |
| `kinet_hit_re25k` | `a9446b` | 17940287988170361 | 60948321 | — |
| `kinet_hit_re25k` | `bd2304` (long) | 17940947915032710 | 60974406 | — |
| `kinet_hit_re25k` | `c95586` | 17940287203678161 | 60948363 | — |
| `kinet_hit_re25k` | `d89acb` | 17940289748750340 | 60948363 | — |
| `kinet_hit_re25k` | `e72a16` | 17940282181166400 | 60948321 | — |
| `kinet_hit_re25k` | `eec89d` | 17940277342974211 | 60947514 | — |
| `kinet_hit_re50k` | `137164` | 17940306146763871 | 60991321 | 60992642 |
| `kinet_hit_re50k` | `32651c` | 17940307471378873 | 60992622 | 60994231 |
| `kinet_hit_re50k` | `3cf779` | 17940295416961021 | 60984315 | 60987207 |
| `kinet_hit_re50k` | `6729a8` | 17940296670884601 | 60985038 | 60987481 |
| `kinet_hit_re50k` | `85bd60` | 17940310189284001 | 60992643 | 60994232 |
| `kinet_hit_re50k` | `b73884` | 17940294136542090 | 60984265 | 60986991 |
| `kinet_hit_re50k` | `bea170` (long) | 17940954423728020 | 60995637 | 61006887 |
| `kinet_hit_re50k` | `cf7333` | 17940292529233901 | 60983733 | 60985583 |
| `kinet_hit_re50k` | `e47e04` | 17940294356203301 | 60984315 | 60987207 |
| `kinet_hit_re50k` | `f19e41` | 17940303312321230 | 60989908 | 60991791 |
| `kinet_hit_re50k` | `f2f9a7` | 17940293126804493 | 60983736 | 60985835 |

Each Re 5e4 seed was also run once at 256² for 10 000 steps in an earlier job (for `cf7333`,
job 60948847, identity key `1e3eea`); those runs are not the archived ones, and whether they
are the archive's `256_simulation` folder was not checked.

## `kinet_sod_gamma1p4`: `d17baf`

- **Data:** `/global/cfs/cdirs/m4790/Data/kinet/sod/compressible_fluids/Pr-71en2_vuy-1.4_visc-1en4/D2Q9_shape-3001-5_T-1000_H-d17baf.h5`
  (dated 2026-05-21) and its conversion `..._flat.h5`.
- **Copied:** `kinet_sod_gamma1p4/d17baf/d17baf.yaml` from `configs/` beside the data.
- **Recorded:** the configuration only; no commit, device, job id or command. The
  configuration does not record the initial states; they were read from the file's
  `initial_conditions/observables/` (density 1 and temperature 0.2 on the left, 0.125 and 0.16
  on the right, the jump between cells 1500 and 1501 of 3001).
- **Command** (composes; not executed):

  ```bash
  python -m kinet.apps.simulate case=sod/transonic \
      io.record_distributions=false io.record_equilibria=false \
      paths.data_root=$PSCRATCH/kinet_datasets
  ```

  The shipped case `sod/transonic` matches every recorded setting (3001 × 5 cells, 1000 steps,
  shifts 0.4, `use_static_weights: false`, extended closure for F and Levermore for G, entropic
  BGK with the piecewise stabilizer at scales 2.0, 1.851, 1.835, 1.818 and tolerances 0.001,
  0.01, 0.1, 1.0, γ = 1.4, viscosity 1e-4, Prandtl 0.71, Neumann at both ends of the tube)
  and the measured initial states.
- **Obstacles:** the configuration does not load (python tags, older keys) and the code and
  device are not recorded. The two γ = 2 runs below, made from one configuration by two kinet
  versions, agree to 7.6e-14 in density at step 1000, which suggests that this solver
  reproduces to round-off across versions (one comparison, not a guarantee).

## `kinet_sod_gamma2`: `c76b17` (default) and `15aa6b`

- **Data:** `/global/cfs/cdirs/m4790/Data/kinet/sod/compressible_fluids/Pr-71en2_vuy-2_visc-25en3/D2Q9_shape-3001-5_T-1000_H-{c76b17,15aa6b}.h5`
  (dated 2026-05-29 and 2026-05-21) and their `_flat.h5` conversions.
- **Copied:** `kinet_sod_gamma2/c76b17/c76b17.yaml` and `kinet_sod_gamma2/15aa6b/15aa6b.yaml`.
  They differ only in schema (`scheme:` and `solver: {type: lbm}` against `solver:`, and two
  `unit` lines), not in physics: the same run made by two kinet versions. `c76b17` was resumed
  (last segment 70 steps). Their density agrees to 0 at step 0, 6.2e-14 at step 500 and
  7.6e-14 at step 1000 (measured 2026-11-27).
- **Recorded:** the configuration only. The initial states, read from the files: density 0.5
  and temperature 0.2 on the left, **2.0** and 0.025 on the right.
- **Command** (composes; not executed):

  ```bash
  python -m kinet.apps.simulate case=sod/subsonic case.initial_conditions.right.density=2.0 \
      io.record_distributions=false io.record_equilibria=false \
      paths.data_root=$PSCRATCH/kinet_datasets
  ```

  The shipped `sod/subsonic` has a right density of 1.8, not the 2.0 of these runs, hence the
  override. Everything else matches the configuration (shifts 0.057, stabilizer scales 2.0,
  1.905, 1.851 and tolerances 0.01, 0.1, 1.0, γ = 2, viscosity 0.025).
- **Obstacles:** as for `d17baf`.
- The folder also holds `configs/8908d7.yaml`, the same physics in a third schema, with no data
  file; it was not copied.

## Supersonic cylinder: `a92b16`

- **Data:** `/global/cfs/cdirs/m4790/Data/kinet/flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2/D2Q9_shape-500-300_T-1000_H-a92b16.h5`
  (dated 2026-05-30), stopped at step 156 of 1000 (`kinet_rollout_status: interrupted`), with
  two checkpoints (`simulation_checkpoint_step-133.pt` and `-156.pt`) beside it.
- **Copied:** `supersonic_cylinder/a92b16/a92b16.yaml`.
- **Recorded:** the configuration only.
- **Command, closest on the current kinet** (composes; not executed):

  ```bash
  python -m kinet.apps.simulate case=flow_around_objects/cylinder 'case.lattice.shifts=[0.4,0.0]' \
      'case.collision.stabilizer.scales=[2.0,1.905,1.481]' \
      'case.collision.stabilizer.tolerances=[0.01,0.1,1.0]' \
      io.record_distributions=false io.record_equilibria=false \
      paths.data_root=$PSCRATCH/kinet_datasets
  ```

- **Cannot be reproduced exactly:** the old configuration describes the cylinder only by
  centre (166, 150) and radius 20, while the current case states a link-wall enforcement and a
  wall model whose old equivalents are not recorded; it has keys with no current counterpart
  (`initial_conditions.Ns: 0.6`, `collision.enforce_positive: true`); the current case's
  shift is 0.55, so the override restores 0.4; and the run never finished. Step 28 of
  `BUILD_ORDER.md` reruns it as a new run rather than a reproduction.

## Other kinet data on CFS that no dataset here reads

Not copied, because no configuration of this repository reads them; listed so that nothing
is silently left out. Under `/global/cfs/cdirs/m4790/Data/kinet/`: `mhd/` (three runs with
`configs/db2e9d.yaml`, `1890d4.yaml`, `d27554.yaml`),
`flow_around_objects/weakly_compressible_isoT_fluids/Re-375e2_Ma-173en3/` (`configs/f08a8e.yaml`),
`taylor_green_vortex/Re-50k_Ma-1en1/8c1573/`, `doubly_periodic/Re-50k_Ma-1en1_l-80_eps-5en2_r0-1/79855c/`,
`doubly_periodic/old/` (which `issues/011-cross-dataset-comparison.md` names as the home of the
unreadable ladder members), and `regression/` (kinet's regression baselines). The archive
folders `visualization/` and `256_simulation/` under `hit_scaling/` were not examined.

## Confidence

- **Sure (checked on 2026-11-27):** that every copy is byte-identical to its source; which
  files `yaml.safe_load` reads; that the current kinet's case model refuses the old case keys;
  that every command marked *composes* passes kinet's check app; that the branch export
  reproduces all 45 archived resolved configurations apart from paths; that the isotropic
  configurations differ only in the seed (and the step count of the long runs); the recorded
  commit, job ids and devices; the measured Sod initial states and the frame comparisons quoted.
- **Read, not tested:** that the branch's changes after `6ccfafc73` do not touch the
  simulation (from the list of files changed); that the velocity synthesis is unchanged
  (compared as source text).
- **Not known:** the kinet commit and device of every shear-layer, Sod and cylinder run; the
  torch version of any run; who made the forecast files and how; whether a GPU rerun of an
  isotropic seed is bitwise identical.
- **My reasoning, labelled where it appears:** that the shear-layer reruns would be
  statistically equivalent; that the forecast files come from a trained model.
