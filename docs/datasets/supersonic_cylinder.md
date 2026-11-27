# Supersonic flow past a cylinder

!!! note "Converted, not configured: no configuration reads it yet"
    A complete run of this flow is converted and readable by the `kinet_raw` reader, but no
    dataset configuration reads it, because the harness has no way to leave the cylinder out of
    the evaluated part. The options are under [What stands in the way](#what-stands-in-the-way).

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
| `kinet/flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2/D2Q9_shape-500-300_T-2000_H-33f78849.h5` | kinet's compressible lattice-Boltzmann solver (D2Q9, entropic BGK), $\gamma = 1.4$, Prandtl number 0.71, Reynolds number 300, on 500 × 300 nodes; a cylinder of radius 20 nodes centred at (166.5, 150.5) (1257 solid nodes, centre node (166, 150)); inlet on the low-x face, Neumann on the other three; 2000 steps from the uniform stream $\rho = 1$, $T = 0.2$, saved every 10th step: 201 frames, 965 MB | Yes, by `kinet_raw`; no configuration |
| `.../D2Q9_shape-500-300_T-1000_H-a92b16.h5` | The first run of the same flow, by an older kinet | No: stopped at step 155 of 1000 |

The complete run was made on 2026-11-27 (`docs/datasets/logs/kinet_runs/supersonic_cylinder_rerun/cyl_m1p8_re300_T2000/`)
and converted by `python -m fmeval.data.convert_kinet`: density, velocity and the absolute
pressure, with the initial condition as frame 0; the clock is kinet's convective time,
0.0019 per step. The bow shock's stand-off on the centre line is 37 cells and steady from about
step 1200, so frames 120 to 200 (81 frames) are the settled flow.

## What stands in the way

- **The inlet is honest as `neumann`.** In the settled frames every field is uniform over the
  first 60 columns to $2 \times 10^{-13}$ (and over 90 columns to $2 \times 10^{-9}$), so the
  mirror extension a degradation applies across a Neumann face continues the stream exactly as
  it is. The other three faces are kinet's own Neumann faces. No new boundary type is needed.
- **The cylinder is not.** The solver holds the nodes inside it at $\rho = 1$, $p = 0.2$ and
  rest, against a stagnation pressure of about 0.93 just ahead of the nose. On the whole domain
  the shock detector of `shock_set_distance` flags 227 to 234 nodes in each of frames 120, 160
  and 200, of which 178 lie within two nodes of the body (90 inside it), against about 50 on
  the bow shock (x 107 to 145, y 125 to 175). The shock-set metrics would mostly score the
  body's outline, and the degradations would blur the wall's jump as if it were flow.
- **The harness has no mask and no spatial window.** A dataset selects frames (`time`,
  `frame_stride`), an analysis grid, ladder entries and slow metrics, but nothing that leaves
  out part of the domain.

The options, none built, each with what it costs:

1. **A spatial window on the reader** (a `kinet_raw` option slicing each axis, about 10 lines and
   a test): the window upstream of the body, x below 146, holds the detected part of the bow
   shock and the uniform inflow; its cut face would be declared `neumann`, as The Well reader
   declares an open face. It leaves out the wake, and its frames are near copies of one another
   (the shock is steady), so a few frames hold all its information.
2. **The whole domain**, with no code: the shock-set results would be dominated by the body, as
   measured above.
3. **A mask carried through the pipeline**, so metrics and degradations ignore the solid nodes:
   a change to every metric and degradation, the largest option.

## Spectral metrics

On its non-square, non-periodic grid, every metric that needs a periodic domain is not run;
issue 046 concerns the wavenumber magnitude on non-square grids.
