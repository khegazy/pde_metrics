# Decaying two-dimensional isotropic turbulence

!!! note "Simulated; registered as evidence, not yet cited by any metric's page"
    Thirty-one realisations are readable now, at three Reynolds numbers, and 90 kinet reruns of
    fifteen of them, degraded on purpose, are scored against them. The six configurations are
    registered as evidence (`evidence_datasets` in `configs/cards/default.yaml`); no metric has
    been run on them for its page yet.

## The problem

A two-dimensional, weakly compressible, isothermal flow on a doubly periodic square, started
from kinet's random-mode initial condition (`k0: 4` in the run's `config.yaml`) and left to
decay. It was simulated with the kinet lattice-Boltzmann solver: D2Q9 lattice, entropic BGK
collision, in dimensionless units, at Mach number 0.1 and Reynolds numbers
$1.25 \times 10^4$, $2.5 \times 10^4$ and $5 \times 10^4$, each run from its own seed. At the
two lower Reynolds numbers a run is 10 000 solver steps on $256^2$ cells, saved every tenth. At
$5 \times 10^4$ a run is 20 000 steps on $512^2$ cells, archived coarse-grained by two in space
and in time, so it is stored on the same $256^2$ grid, with the same 1001 frames on the same
clock, ending at dimensionless time 2.2553. The archive holds 100 such runs at each Reynolds
number, plus one run ten times longer (`dataset_specs/05_initial_conditions_and_degraded_solver_runs.md`,
Sect. 4.1). The pressure is not used: this solver stores it as the gauge $(\rho - 1) c_s^2$,
which carries no information beyond the density.

kinet writes these runs in a grouped layout that no reader here opens. Each is rewritten into
the flat layout of `kinet_re5e4` by

```bash
python -m fmeval.data.convert_kinet <archive>/<key>/tiers/<tier>/rollout.h5 <data>/<key>.h5
```

with `<tier>` `full` at $\mathrm{Re} = 1.25 \times 10^4$ and $2.5 \times 10^4$ and `256` at
$5 \times 10^4$. The converter restores the initial condition as frame 0, keeps the saved steps
10, 20, ..., 10000 and takes the clock from kinet's `time_convection`; it reads every converted
file back with the `kinet_raw` reader before keeping it. At $5 \times 10^4$ the step counter of
the archived tier counts the coarse-grained steps, and its clock equals that of the other two
Reynolds numbers frame for frame. A data-marked test in `tests/test_loader_contract.py`
requires every converted frame of `004ae2` to equal its source exactly.

## Variations of this problem in the repository

| Configuration | What it is |
|---|---|
| `kinet_hit_re12p5k` | One realisation at $\mathrm{Re} = 1.25 \times 10^4$, by default the first drawn below |
| `kinet_hit_re25k` | One realisation at $\mathrm{Re} = 2.5 \times 10^4$, by default the first drawn below |
| `kinet_hit_re50k` | One realisation at $\mathrm{Re} = 5 \times 10^4$, by default the first drawn below |
| `kinet_hit_re12p5k_candidates` | A kinet rerun of one realisation at $\mathrm{Re} = 1.25 \times 10^4$, degraded on purpose, scored against it (below) |
| `kinet_hit_re25k_candidates` | The same at $\mathrm{Re} = 2.5 \times 10^4$ |
| `kinet_hit_re50k_candidates` | The same at $\mathrm{Re} = 5 \times 10^4$, where no rerun is a control (below) |

Each realisation is one file of 1001 frames, 2.10 GB. Any other converted realisation of the
same Reynolds number is read by naming its identity key, for example

```bash
python evaluate.py 'metrics=[mse]' dataset=kinet_hit_re25k dataset.trajectory=49a8ad
```

and `-m dataset.trajectory=<key>,<key>,...` runs several in one sweep. The evaluated part is
the first five drawn at each Reynolds number, frames 150 to 550 every 50th, on a $128^2$
analysis grid that the configurations state. Their run folders are gathered into one, which the
analysis reads as one sample of 45 frames with the realisations independent and the frames
within each dependent:

```python
from fmeval import io as fio
folder = fio.combine_runs(["results/comparison_<a>", ..., "results/comparison_<e>"],
                          fio.claim_stamp("results"), across="trajectory")
```

The reasoning and costs are in its log, `docs/datasets/logs/decaying_isotropic_2d.md`.

## The converted subset

All 100 complete runs per Reynolds number can be scored; ten of each are converted first to
keep the first pass cheap (spec 05, Sect. 4.1). The complete runs were identified by
`kinet_rollout_status == "complete"`, `discretization.temporal.grid == 10000` and 1001 saved
steps; the long 100 000-step runs (`6f5a2b`, `bd2304`, `bea170`) and the folders
`visualization` and, at $5 \times 10^4$, `256_simulation` were left out. The ten were drawn
from each Reynolds number's alphabetically sorted keys as the first ten entries of
`numpy.random.default_rng(0).permutation(100)` (NumPy 2.5.1), so the same ten positions are
drawn at each Reynolds number; the runs at different Reynolds numbers are unrelated, so that
correlates nothing. In drawn order:

| Re | Folder under `kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids/` | Identity keys |
|---|---|---|
| $1.25 \times 10^4$ | `sys_Re-12p5k_Ma-1en1` | `c5ccb2`, `6f3450`, `3c2c65`, `10383c`, `f151b4`, `3519ce`, `f3e96c`, `8a91f8`, `ad4dde`, `e81d9c` |
| $2.5 \times 10^4$ | `sys_Re-25k_Ma-1en1` | `c95586`, `49a8ad`, `2bf18d`, `0789a4`, `e72a16`, `264498`, `eec89d`, `6dd7f2`, `a9446b`, `d89acb` |
| $5 \times 10^4$ | `sys_Re-50k_Ma-1en1` | `cf7333`, `6729a8`, `3cf779`, `137164`, `f19e41`, `32651c`, `f2f9a7`, `85bd60`, `b73884`, `e47e04` |

The realisation `004ae2` at $2.5 \times 10^4$ was converted first, to test the converter, and
was not drawn. It stays in the folder and reads as `dataset.trajectory=004ae2`; it is not part
of the subset.

## Degraded solver runs scored against their realisations

Each of the five evaluated realisations of each Reynolds number was rerun by kinet from its own
stored step-0 fields, changed in one stated way, and the rerun is scored against the
realisation as its prediction. These are solver runs degraded on purpose, the project's own
protocol (`CLAUDE.md`, "Evaluation protocol", steps 1 and 2); no machine-learning model is
involved. They are Options B and C of
`dataset_specs/05_initial_conditions_and_degraded_solver_runs.md`, step 20 of
`dataset_specs/BUILD_ORDER.md`. A rerun is chosen with `dataset.reader.candidate=<kind>.h5`:

| Kind | What changed | Notes |
|---|---|---|
| `control` | Nothing: the realisation's own settings | At $1.25 \times 10^4$ and $2.5 \times 10^4$ it matches its realisation to round-off |
| `grid128`, `grid64` | $128^2$ or $64^2$ cells, started from the step-0 fields averaged over $2 \times 2$ or $4 \times 4$ blocks | Scored on its own grid, the realisation block-averaged onto it; `grid64` needs `dataset.analysis_resolution=64` |
| `re0.9`, `re0.75`, `re0.5` | The Reynolds number times 0.9, 0.75 or 0.5, so the viscosity is too large by 1/0.9, 1/0.75 or 2 | Not at $5 \times 10^4$ |
| `bgk` | Plain BGK collision instead of entropic BGK | |

kinet keeps the lattice velocity of a run fixed on every grid (acoustic scaling), so a $64^2$
run takes 2500 steps where the $256^2$ run takes 10 000, and the same Reynolds number is the
same physical viscosity. The runs are read in cells and solver steps of the $256^2$ grid
(`cell: 1` on the `kinet_raw` reader, which gives a coarser candidate cells of $256/N$), so
frame $k$ is step $500k$ of the $256^2$ runs on every grid.

```bash
python evaluate.py -m 'metrics=[mse]' dataset=kinet_hit_re25k_candidates \
    dataset.trajectory=c95586,49a8ad,2bf18d,0789a4,e72a16 \
    dataset.reader.candidate=control.h5,grid128.h5,re0.9.h5,re0.75.h5,re0.5.h5,bgk.h5
python evaluate.py -m 'metrics=[mse]' dataset=kinet_hit_re25k_candidates \
    dataset.trajectory=c95586,49a8ad,2bf18d,0789a4,e72a16 \
    dataset.reader.candidate=grid64.h5 dataset.analysis_resolution=64
```

The five realisations of one kind are gathered with
`fmeval.io.combine_runs(<folders>, stamp, across="trajectory")`, as for the realisations alone.
A candidate replaces the degradation ladder: each frame is scored on three levels, the clean
reference, the anchor (the reference's spatial mean) and the rerun.

**At $\mathrm{Re} = 5 \times 10^4$ there is no control.** These realisations were simulated on
$512^2$ cells and stored coarse-grained to $256^2$, and every rerun ran on $256^2$ cells or
fewer from the stored fields. So `control` is a grid candidate, $256^2$ against $512^2$, and
every other rerun carries the same grid error on top of its own. The three wrong-viscosity
reruns were run but are not converted: their own error is hidden under the grid error, so they
do not order as their viscosity does (the log, section 7). `control`, `grid128`, `grid64` and
`bgk` are kept.

**What the job measured** (`docs/datasets/logs/kinet_runs/isotropic_candidates/candidates_checks.txt`):
the relative $L^2$ distance between rerun and realisation, $\lVert a_c - a_r \rVert / \lVert a_r \rVert$
for velocity $u$ and vorticity $\omega$ on the rerun's grid, median over the five realisations,
at the first and last evaluated frames.

| Re | Field | Frame | control | grid128 | grid64 | re0.9 | re0.75 | re0.5 | bgk |
|---|---|---|---|---|---|---|---|---|---|
| $1.25 \times 10^4$ | $u$ | 150 | 1.28e-11 | 0.0312 | 0.144 | 0.00512 | 0.0151 | 0.0435 | 0.049 |
| | | 550 | 7.09e-11 | 0.332 | 0.788 | 0.0536 | 0.146 | 0.35 | 0.476 |
| | $\omega$ | 150 | 2.03e-10 | 0.157 | 0.423 | 0.018 | 0.0512 | 0.133 | 0.126 |
| | | 550 | 5.22e-10 | 0.706 | 1.14 | 0.171 | 0.379 | 0.67 | 0.918 |
| $2.5 \times 10^4$ | $u$ | 150 | 1.83e-11 | 0.0424 | 0.156 | 0.00281 | 0.00829 | 0.0239 | 0.0542 |
| | | 550 | 1.23e-10 | 0.391 | 0.803 | 0.0397 | 0.107 | 0.268 | 0.728 |
| | $\omega$ | 150 | 2.84e-10 | 0.231 | 0.499 | 0.0131 | 0.0372 | 0.0973 | 0.18 |
| | | 550 | 8.14e-10 | 0.905 | 1.26 | 0.177 | 0.404 | 0.67 | 1.13 |
| $5 \times 10^4$ | $u$ | 150 | 0.011 | 0.0457 | 0.153 | — | — | — | 0.047 |
| | | 550 | 0.155 | 0.379 | 0.835 | — | — | — | 0.535 |
| | $\omega$ | 150 | 0.122 | 0.278 | 0.486 | — | — | — | 0.183 |
| | | 550 | 0.544 | 0.912 | 1.28 | — | — | — | 0.984 |

Two uncorrelated fields of equal norm are $\sqrt{2} \approx 1.41$ apart in this distance. At
$1.25 \times 10^4$ and $2.5 \times 10^4$ three orderings hold for all five realisations at every
evaluated frame, in velocity and in vorticity: the control below every degraded rerun, $64^2$
above $128^2$, and the distance growing as the Reynolds number falls. At $5 \times 10^4$, with
the three wrong-viscosity reruns included, in vorticity the control lies below every other rerun
for only 0 to 2 of the five realisations at a frame, and the viscosity ordering holds for 0 to 5
(2 or fewer at frames 150 and 200). Among the four
kinds kept, the $256^2$ rerun lies below `grid128`, `grid64` and `bgk`, and `grid64` above
`grid128`, for all five realisations at every evaluated frame in both fields (computed from the
job's `candidates_checks.json`).

**Files.** `kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids/sys_Re-<Re>_Ma-1en1_candidates/<key>/`
holds `reference.h5` and one `<kind>.h5` per kind: 105 files, 3.51 GB. Each holds 21 frames,
the realisation's frames 0, 50, ..., 1000, written by
`python -m fmeval.data.convert_kinet <rollout> <file> --every N`. `reference.h5` is the
realisation itself at that stride, equal to its full file there; it sits beside the reruns so
that one candidate file name serves every realisation. The evaluated part is frames 3 to 11
(the realisation's 150 to 550), on the $128^2$ grid ($64^2$ for `grid64`). The runs'
configurations, commands and checks are in `docs/datasets/logs/kinet_runs/isotropic_candidates/`;
the reasoning and costs in the log.
