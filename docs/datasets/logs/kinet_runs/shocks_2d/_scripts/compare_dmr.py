"""Compare two double-Mach-reflection rollouts on one grid, and measure what
check_dmr.py does not: single-cell dips and the disturbance above the reflected shock.

Usage (kinet's .venv, env.sh sourced):
    python -B compare_dmr.py REFERENCE.h5 [OTHER.h5]

REFERENCE is the native 480 x 120 run, or its block average onto a coarser grid; OTHER is a finer
run block-averaged onto the same grid (kinet's coarse graining). For every saved time of REFERENCE, the frame of OTHER nearest in time
is taken and the offset reported, so that a difference of clocks is not read as a difference of
fields (the incident shock moves 20 / sqrt(3) = 11.5 in x per unit time, 0.096 cells of 1/120
per 1e-5 of time). Inside the evaluated window x < 3.2 (the first 0.8 nx cells), per field:

    relative L2 = ||OTHER - REFERENCE||_2 / ||REFERENCE||_2,

the norms over all cells of the window (and both components for the velocity).

Per rollout and frame it also reports:

* dips: the cells with density below 1.3 or pressure below 0.95, values the exact solution
  never takes (its smallest values are the ambient 1.4 and 1), with the smallest of each;
* above the reflected shock: the largest |rho - 8| / 8 and |p - 116.5| / 116.5 in the gas
  between the reflected shock and the incident shock, which in the exact solution is the
  uniform post-shock state (8, 116.5) (Woodward & Colella 1984 set-up as printed by Kemm 2014,
  arXiv:1404.6510). That region is the cells at least 8 cells left of the exact incident shock
  x_s(y, t) = 1/6 + (y + 20 t)/sqrt(3) and at least 4 cells above the top-most density jump
  greater than 1 in their column; columns from x = 0.4, rows below y = 0.97 (the top face holds
  the imposed shock over two cells); with it, the fraction of that region departing from 8 by
  more than 2 % and the root mean square of |rho - 8| / 8 over it. The thin feature seen above
  the reflected shock and the line trailing the incident shock in the 480 x 120 contour plot
  both lie in this region. On the row y = 0.6 every band of that region where the density
  exceeds 8 by more than 1 % is listed with its extent, physical width and peak, so that a band
  that thins in proportion to the cell, or keeps its width, or vanishes, can be told apart.

With one rollout given, only these diagnostics are printed, for every saved frame.
Prototype quality: a measurement for one comparison.
"""

import math
import sys

import hdf5plugin  # noqa: F401  (registers blosc2 before h5py opens a PonD rollout)
import h5py
import numpy as np

WINDOW = 0.8  # the evaluated window x < 3.2 as a fraction of the length 4
ROW = 0.6     # the row on which the bands of excess density above the reflected shock are listed


def frames(f: h5py.File) -> tuple[np.ndarray, np.ndarray]:
    """The saved slots and their times."""
    t = f["time/time"][:]
    slots = np.flatnonzero(np.isfinite(t))
    return slots, t[slots]


def fields(f: h5py.File, slot: int) -> dict[str, np.ndarray]:
    """Density, pressure and velocity of one slot, shapes (nx, ny) and (2, nx, ny)."""
    return {"density": f["observables/density"][0, 0, slot],
            "pressure": f["observables/pressure"][0, 0, slot],
            "velocity": f["observables/velocity"][0, :, slot]}


def diagnostics(q: dict[str, np.ndarray], t: float) -> str:
    """Dips and the disturbance above the reflected shock, as one line."""
    rho, p = q["density"], q["pressure"]
    nx, ny = rho.shape
    dx = 4.0 / nx
    x = (np.arange(nx) + 0.5) * dx
    y = (np.arange(ny) + 0.5) * dx
    region = np.zeros_like(rho, dtype=bool)
    for i in range(int(0.4 / dx), nx):
        jumps = np.flatnonzero(np.abs(np.diff(rho[i])) > 1.0)
        rows = y < 0.97
        left = x[i] < 1 / 6 + (y + 20 * t) / math.sqrt(3) - 8 * dx
        start = jumps[-1] + 5 if jumps.size else ny
        rows[:start] = False
        region[i] = rows & left
    dev_rho = np.abs(rho - 8.0) / 8.0
    dev_p = np.abs(p - 116.5) / 116.5
    if region.any():
        k = np.unravel_index(np.where(region, dev_rho, -1).argmax(), rho.shape)
        above = (f"above reflected shock ({region.sum()} cells): max|drho|/8={dev_rho[region].max():.4f} "
                 f"at x={x[k[0]]:.3f} y={y[k[1]]:.3f}, max|dp|/116.5={dev_p[region].max():.4f}, "
                 f"fraction with |drho|/8>0.02: {(dev_rho[region] > 0.02).mean():.4f}, "
                 f"rms drho/8: {np.sqrt((dev_rho[region] ** 2).mean()):.4f}")
    else:
        above = "above reflected shock: no cells"
    j = int(ROW / dx)
    excess = np.where(region[:, j], (rho[:, j] - 8.0) / 8.0, 0.0) > 0.01
    edges = np.flatnonzero(np.diff(np.concatenate([[0], excess.astype(int), [0]])))
    bands = [f"x={x[a]:.3f}..{x[b - 1]:.3f} width {(b - a) * dx:.4f} ({b - a} cells) "
             f"peak {(rho[a:b, j].max() - 8.0) / 8.0:+.4f}" for a, b in zip(edges[::2], edges[1::2])]
    return (f"dips: {(rho < 1.3).sum()} cells rho<1.3 (min {rho.min():.4g}), {(p < 0.95).sum()} cells "
            f"p<0.95 (min {p.min():.4g}) | {above} | row y={y[j]:.4f}, bands with (rho-8)/8>0.01: "
            + ("; ".join(bands) or "none"))


def main(reference: str, other: str | None) -> None:
    if other is None:
        with h5py.File(reference, "r") as f:
            print(f"rollout {reference}")
            for slot, t in zip(*frames(f)):
                print(f"t={t:.5f} {diagnostics(fields(f, int(slot)), float(t))}")
        return
    with h5py.File(reference, "r") as fr, h5py.File(other, "r") as fo:
        slots_r, times_r = frames(fr)
        slots_o, times_o = frames(fo)
        print(f"reference {reference}\nother     {other}")
        for slot, t in zip(slots_r, times_r):
            k = int(np.abs(times_o - t).argmin())
            a, b = fields(fr, int(slot)), fields(fo, int(slots_o[k]))
            if a["density"].shape != b["density"].shape:
                raise ValueError(f"grids differ: {a['density'].shape} and {b['density'].shape}")
            w = round(WINDOW * a["density"].shape[0])
            rel = {name: float(np.linalg.norm(b[name][..., :w, :] - a[name][..., :w, :])
                               / np.linalg.norm(a[name][..., :w, :])) for name in a}
            print(f"t_ref={t:.5f} t_other={times_o[k]:.5f} (dt={times_o[k] - t:+.2e}) | relative L2 in x<3.2: "
                  + ", ".join(f"{n} {v:.4f}" for n, v in rel.items()))
            print(f"    reference: {diagnostics(a, float(t))}")
            print(f"    other:     {diagnostics(b, float(times_o[k]))}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
