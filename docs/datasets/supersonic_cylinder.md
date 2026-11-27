# Supersonic flow past a cylinder

!!! note "On disk, not readable: the run stopped at step 155 of 1000"
    No configuration reads this flow yet. The one run of it stopped early, and the converter
    refuses an unfinished run.

## The problem

A uniform stream at Mach number 1.8 meets a fixed circular cylinder, and a curved bow shock
stands ahead of it. The shock is normal to the stream at the nose, with a pressure ratio of
3.61 there, and weakens into an oblique front along its arc
(`dataset_specs/03_two_dimensional_shocks.md`, Sect. 4.7). It is the repository's planned
test of a shock detector on a real curved front whose flagged length depends on the
detector's threshold.

## What is on disk

| Run | What it is | Readable here |
|---|---|---|
| `kinet/flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2/D2Q9_shape-500-300_T-1000_H-a92b16.h5` | kinet's compressible lattice-Boltzmann solver (D2Q9, entropic BGK), $\gamma = 1.4$, Prandtl number 0.71, Reynolds number 300, on 500 × 300 nodes; a cylinder of radius 20 nodes at (166, 150); inlet on the low-x face, Neumann on the other three; started from the uniform stream $\rho = 1$, $T = 0.2$ | Not yet: stopped at step 155 of 1000 |

The file is in kinet's older grouped layout, as the Sod runs are: density, velocity, the
absolute pressure $p = \rho T$, temperature, energy and Mach number, with `time/time` as its
clock (1/300 per step). Its root attribute `kinet_rollout_status` is `interrupted`: it holds
steps 1 to 155 and NaN in the other 845 slots, and two simulation checkpoints (steps 133 and
156) sit beside it. `python -m fmeval.data.convert_kinet` refuses it for that reason.

The file stores no mask of the cylinder. Inside it the solver holds the fluid at rest at
$\rho = 1$, so a metric would score those nodes as flow unless the dataset masks them from
the cylinder's position and radius in the run's `configs/a92b16.yaml`.

## What would make it readable

1. **Finish the run.** Resume it from its last checkpoint, or rerun it, to step 1000; the
   converter then writes it as it wrote the Sod runs.
2. **Declare its boundaries.** No axis is periodic, and the inlet is not a zero-gradient
   face, so `fmeval/data/base.py` has no boundary type for it yet; the three Neumann faces
   are. A metric that needs a periodic domain is not run on it.
3. **Mask the cylinder**, as above.
4. **Spectral metrics** on its non-square grid wait on the definition of the wavenumber
   magnitude (issue 046).
