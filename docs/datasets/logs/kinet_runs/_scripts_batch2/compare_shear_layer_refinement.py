"""Compare the kinet shear-layer refinement sequence 128^2, 256^2, 512^2 (prototype).

Build-order step 19 (dataset_specs/02_grid_refinement_known_solution.md, Sect. 5.1). Each
level is the shipped case `doubly_periodic/shear_layer` (Re 5e4, Ma 0.1, lambda 80,
epsilon 0.05) run to 1000, 2000 and 4000 steps, saved every 10th, 20th and 40th step, so
saved frame k of every level is at the same convective time t = 10 k * Ma c_s / 128.

kinet paints cell i of N at (i + 1/2)/N (kinet/initialization/shear_layer.py, lines 70-73;
kinet/grid/grid.py, Grid.cell_centers), so cell j of the 256 grid is exactly the union of
cells 2j, 2j+1 of the 512 grid: the levels are nested as cells, and the comparison is a
block average of the finer level onto the coarser grid (the conservative remap).

Reported per saved time t and field (density, velocity, vorticity recomputed spectrally
from the velocity on the comparison grid, in box units):
  E_N   = || u_N - B_{512->N} u_512 ||_2     (RMS over the N^2 cells), N = 128, 256
  p_E   = ln(E_128 / E_256) / ln 2           (the order asked for; biased, see below)
  d_1   = || u_256 - B_2 u_512 ||, d_2 = || u_128 - B_2 u_256 ||
  p_3g  = ln(d_2 / d_1) / ln 2               (three-grid order of successive differences,
                                              NPARC tutorial form, spec 02 Sect. 5.1)
If the error is C h^p, E_128 / E_256 = (4^p - 1)/(2^p - 1) = 2^p + 1 (the author's algebra),
so p_E = log2(2^p + 1) overstates p (2.32 for p = 2, 1.58 for p = 1); p_from_E =
log2(E_128/E_256 - 1) undoes that, and equals p_3g when the error is exactly C h^p.

Usage: python compare_shear_layer_refinement.py ROLLOUT_128 ROLLOUT_256 ROLLOUT_512 OUT_JSON
"""

from __future__ import annotations

import json
import sys

import h5py
import numpy as np


def load(path: str) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Convective times and fields (density (T,X,Y), velocity (T,2,X,Y)) of the saved steps,
    with the initial condition prepended as t = 0. Step 1, saved by kinet whatever the
    cadence, is dropped so frames are evenly spaced."""
    with h5py.File(path, "r") as f:
        if f.attrs["kinet_rollout_status"] != "complete":
            raise RuntimeError(f"{path}: kinet_rollout_status={f.attrs['kinet_rollout_status']}")
        step = f["time/time"][:]
        keep = np.flatnonzero(np.isfinite(step) & (step > 1))
        t = np.concatenate([[0.0], f["time/time_convection"][keep]])
        ic = f["initial_conditions/observables"]
        rho = np.concatenate([ic["density"][0, 0], f["observables/density"][0, 0, keep]])
        vel = np.concatenate([ic["velocity"][0].transpose(1, 0, 2, 3),
                              f["observables/velocity"][0][:, keep].transpose(1, 0, 2, 3)])
    return t, {"density": rho, "velocity": vel}


def block(a: np.ndarray, r: int) -> np.ndarray:
    """Average r x r blocks over the last two axes (the conservative remap onto a grid r
    times coarser, for nested cells)."""
    *lead, nx, ny = a.shape
    return a.reshape(*lead, nx // r, r, ny // r, r).mean(axis=(-3, -1))


def vorticity(vel: np.ndarray) -> np.ndarray:
    """Spectral curl d u_y/dx - d u_x/dy on the periodic unit box; axis -2 is x."""
    n = vel.shape[-1]
    k = 2j * np.pi * np.fft.fftfreq(n, d=1.0 / n)
    ux, uy = np.fft.fft2(vel[..., 0, :, :]), np.fft.fft2(vel[..., 1, :, :])
    return np.real(np.fft.ifft2(k[:, None] * uy - k[None, :] * ux))


def rms(a: np.ndarray, channel_axis: bool) -> np.ndarray:
    """Per-frame RMS over cells (summing the squared channels for a vector field)."""
    sq = a ** 2
    if channel_axis:
        sq = sq.sum(axis=1)
    return np.sqrt(sq.mean(axis=(-2, -1)))


def main(p128: str, p256: str, p512: str, out: str) -> None:
    """Load the three levels, check their clocks match, and write the difference table."""
    (t1, f1), (t2, f2), (t3, f3) = load(p128), load(p256), load(p512)
    if not (len(t1) == len(t2) == len(t3)) or max(abs(t1 - t2).max(), abs(t1 - t3).max()) > 1e-12:
        raise RuntimeError("saved times do not match across levels")
    fields = {
        "density": (f1["density"], f2["density"], f3["density"], False),
        "velocity": (f1["velocity"], f2["velocity"], f3["velocity"], True),
        "vorticity": (vorticity(f1["velocity"]), vorticity(f2["velocity"]),
                      vorticity(f3["velocity"]), False),
    }
    result = {"time_convection": t1.tolist(), "fields": {}}
    for name, (a128, a256, a512, vec) in fields.items():
        if name == "vorticity":
            # Vorticity of the block-averaged velocity, so every term lives on one grid.
            b2_512 = vorticity(block(f3["velocity"], 2))
            b4_512 = vorticity(block(f3["velocity"], 4))
            b2_256 = vorticity(block(f2["velocity"], 2))
        else:
            b2_512, b4_512, b2_256 = block(a512, 2), block(a512, 4), block(a256, 2)
        e256, e128 = rms(a256 - b2_512, vec), rms(a128 - b4_512, vec)
        d1, d2 = e256, rms(a128 - b2_256, vec)
        scale = rms(a512 - a512.mean(axis=(-2, -1), keepdims=True), vec)
        with np.errstate(divide="ignore", invalid="ignore"):
            p_e = np.log(e128 / e256) / np.log(2)
            p_from_e = np.log2(e128 / e256 - 1.0)
            p_3g = np.log(d2 / d1) / np.log(2)
        result["fields"][name] = {
            "E_128": e128.tolist(), "E_256": e256.tolist(), "d_2": d2.tolist(),
            "rms_fluctuation_512": scale.tolist(),
            "p_E": p_e.tolist(), "p_from_E": p_from_e.tolist(), "p_3grid": p_3g.tolist(),
        }
    with open(out, "w") as fh:
        json.dump(result, fh, indent=1)
    for name, r in result["fields"].items():
        print(f"\n{name}: t, E_128, E_256 (abs RMS), E_256/rms', p_E, p_from_E, p_3grid")
        for k, t in enumerate(result["time_convection"]):
            if k % 10 == 0 or k == len(t1) - 1:
                print(f"  {t:7.4f}  {r['E_128'][k]:.3e}  {r['E_256'][k]:.3e}  "
                      f"{r['E_256'][k] / r['rms_fluctuation_512'][k]:.2e}  {r['p_E'][k]:6.3f}  "
                      f"{r['p_from_E'][k]:6.3f}  {r['p_3grid'][k]:6.3f}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
