# Decaying two-dimensional isotropic turbulence

!!! note "Simulated; registered as evidence, not yet cited by any metric's page"
    Thirty-one realisations are readable now, at three Reynolds numbers. The three
    configurations are registered as evidence (`evidence_datasets` in
    `configs/cards/default.yaml`); no metric has been run on them for its page yet.

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

Each realisation is one file of 1001 frames, 2.10 GB. Any other converted realisation of the
same Reynolds number is read by naming its identity key, for example

```bash
python evaluate.py 'metrics=[mse]' dataset=kinet_hit_re25k dataset.trajectory=49a8ad
```

and `-m dataset.trajectory=<key>,<key>,...` runs several in one sweep.

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
