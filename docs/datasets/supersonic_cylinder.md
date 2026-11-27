# Supersonic flow past a cylinder

!!! note "Simulated: the bow shock, in a window upstream of the body"
    `kinet_supersonic_cylinder` reads a complete kinet run of this flow in a window that holds the
    bow shock and leaves out the cylinder and its wake. The wake is not evaluated.

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
| `kinet/flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2/D2Q9_shape-500-300_T-2000_H-33f78849.h5` | kinet's compressible lattice-Boltzmann solver (D2Q9, entropic BGK), $\gamma = 1.4$, Prandtl number 0.71, Reynolds number 300, on 500 × 300 nodes; a cylinder of radius 20 nodes centred at (166.5, 150.5) (1257 solid nodes, centre node (166, 150)); inlet on the low-x face, Neumann on the other three; 2000 steps from the uniform stream $\rho = 1$, $T = 0.2$, saved every 10th step: 201 frames, 965 MB | Yes: `kinet_supersonic_cylinder`, the window below |
| `.../D2Q9_shape-500-300_T-1000_H-a92b16.h5` | The first run of the same flow, by an older kinet | No: stopped at step 155 of 1000 |

The complete run was made on 2026-11-27 (`docs/datasets/logs/kinet_runs/supersonic_cylinder_rerun/cyl_m1p8_re300_T2000/`)
and converted by `python -m fmeval.data.convert_kinet`: density, velocity and the absolute
pressure, with the initial condition as frame 0; the clock is kinet's convective time,
0.0019 per step. The bow shock's stand-off on the centre line is 37 cells and steady from about
step 1200, so frames 120 to 200 (81 frames) are the settled flow.

## The window upstream of the body

The cylinder cannot be left in. The solver holds the nodes inside it at $\rho = 1$, $p = 0.2$ and
rest, against a stagnation pressure of about 0.93 just ahead of the nose, so on the whole domain
the shock detector of `shock_set_distance` flags 227 to 234 nodes in each of frames 120, 160 and
200, of which 178 lie within two nodes of the body (90 inside it), against about 50 on the bow
shock. The shock-set metrics would mostly score the body's outline, and the degradations would
blur the wall's jump as if it were flow.

So the dataset reads only a window, by the `kinet_raw` option `window` (cells `[start, stop)` on
each axis; the grid is the window's, its origin the window's first cell): x from 0 to 143 and y
from 6 to 293, a $144 \times 288$ grid ending two nodes ahead of the body. In it the detector
flags only the normal part of the bow shock, 45 to 56 cells at x 107 to 111 and y 125 to 175, every
one at least 38 nodes from the body (a `data` test pins this). The window's size makes every axis
of its mirror extension divisible by 16, so the default ladder's coarsening by 8 and 16 runs; on a
$146 \times 300$ window those four levels were dropped.

**What the faces are.** Every face is declared `neumann`, the mirror extension:

- *low x*, the inlet: uniform over its first 60 columns to $2 \times 10^{-13}$, so the mirror is
  the stream itself;
- *both y faces*: six cells inside kinet's own Neumann faces, where the flow equals the inflow to
  $3 \times 10^{-5}$, so the mirror is the flow there too;
- *high x*, a cut: two nodes ahead of the body's front face for y 130 to 170, and through the
  shock layer elsewhere. **It is not a boundary of the flow.** A smoothing or shifting degradation
  reads the field reflected about column 143 there instead of the flow beyond it, so within a
  kernel width of the cut a degraded field is not what the same degradation of the whole domain
  would give. `neumann` is chosen because it leaves no jump at the seam; `periodic` would join the
  shock layer ($p$ up to 0.93) to the inflow ($p = 0.2$), a jump the degradations would smear into
  a false shock.

The detector itself pads a field by repeating its edge value and never wraps, so the cut adds no
flagged cell. Every metric that needs a periodic domain is not run (12 of the deterministic
panel).

**What part is evaluated.** Frames 120, 160 and 200 (steps 1200 to 2000). The flow is settled
from step 1200, but not frozen: the bow shock creeps upstream by about one cell over the 81
settled frames, and frame 120 differs from frame 200 by 9% of the pressure's spatial standard
deviation (frame 160 by 2.5%). The settled frames are one state with a slow drift, which three
frames sample. Every metric that runs here takes 31 s wall for the three frames on the default
ladder, `persistence_distance` 41 s (login node, 2026-11-27).

```bash
python evaluate.py dataset=kinet_supersonic_cylinder 'metrics=[shock_set_distance,mse]'
```

## Spectral metrics

On its non-square, non-periodic window, every metric that needs a periodic domain is not run;
issue 046 concerns the wavenumber magnitude on non-square grids.
