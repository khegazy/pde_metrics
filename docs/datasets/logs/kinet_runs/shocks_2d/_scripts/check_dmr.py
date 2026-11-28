"""Check kinet double-Mach-reflection runs: finiteness, positivity and the incident shock.

Usage (kinet's .venv, env.sh sourced):
    python -B check_dmr.py ROLLOUT.h5 [ROLLOUT.h5 ...]

The double Mach reflection has no closed-form solution, but the incident Mach-10 shock away
from the reflection is the undisturbed planar shock: at 60 degrees to the wall, moving at
speed 10 along its normal, crossing ``y = 0`` at ``x = 1/6`` at ``t = 0``, so its foot on the
row ``y`` is at ``x_s(y, t) = 1/6 + y / sqrt(3) + 20 t / sqrt(3)`` (Woodward and Colella 1984
setup as printed by Kemm 2014, arXiv:1404.6510; dataset spec 03, Sect. 4.2, which gives the
top-boundary form at ``y = 1``). On each checked row the measured position is the right-most
cell centre where the density rises through 4.7, the mean of the pre-shock 1.4 and the
post-shock 8, scanning in from the outflow face ``x = 4``. The foot of the Mach stem on the wall
(the bottom row) is found the same way and reported as measured; spec 03 cites no number for
it. The 10 %-to-90 % width of the incident shock's density rise on each row is reported in cells. Frames are read one at a time.
"""

import json
import math
import os
import sys

import hdf5plugin  # noqa: F401  (registers blosc2 before h5py opens a PonD rollout)
import h5py
import numpy as np
import yaml

LEVEL = 0.5 * (1.4 + 8.0)
ROWS = (0.6, 0.7, 0.8, 0.9, 1.0)   # rows checked against the straight incident shock


def front(x: np.ndarray, rho_row: np.ndarray) -> float:
    """The right-most position where the row's density rises through ``LEVEL``, scanning from
    the right; linear interpolation between the two cell centres. NaN without a crossing."""
    above = rho_row >= LEVEL
    idx = np.flatnonzero(above[:-1] & ~above[1:])
    if idx.size == 0:
        return float("nan")
    i = idx[-1]
    return float(x[i] + (rho_row[i] - LEVEL) * (x[i + 1] - x[i]) / (rho_row[i] - rho_row[i + 1]))


def width(x: np.ndarray, rho_row: np.ndarray) -> float:
    """The 10 %-to-90 % width of the right-most rise of the row's density from 1.4 to 8, in the
    units of ``x``: the distance between the right-most crossings of the two levels."""
    lo, hi = 1.4 + 0.1 * (8.0 - 1.4), 1.4 + 0.9 * (8.0 - 1.4)
    crossings = []
    for level in (hi, lo):
        above = rho_row >= level
        idx = np.flatnonzero(above[:-1] & ~above[1:])
        if idx.size == 0:
            return float("nan")
        i = idx[-1]
        crossings.append(x[i] + (rho_row[i] - level) * (x[i + 1] - x[i]) / (rho_row[i] - rho_row[i + 1]))
    return float(crossings[1] - crossings[0])


def check(path: str) -> None:
    """Print the checks of one run."""
    identity = os.path.dirname(os.path.dirname(os.path.dirname(path)))
    with open(os.path.join(identity, "config.yaml")) as fh:
        t_end = float(yaml.safe_load(fh)["case"]["discretization"]["temporal"]["length"])
    with h5py.File(path, "r") as f:
        disc = json.loads(f.attrs["discretization"])
        nx, ny = disc["spatial"]["grid"]
        lx, ly = disc["spatial"]["length"]
        dx, dy = lx / nx, ly / ny
        x = (np.arange(nx) + 0.5) * dx
        y = (np.arange(ny) + 0.5) * dy
        times = f["time/time"][:]
        slots = np.flatnonzero(np.isfinite(times))
        status = f.attrs["kinet_rollout_status"]
        print(f"\n== {path}\n   grid {nx}x{ny}, length {lx}x{ly}, dx={dx:.5g}, status={status}, "
              f"saved_frames={slots.size}, last_time={times[slots[-1]]!r}, t_end={t_end}, "
              f"reached_end={bool(status == 'complete' and math.isclose(times[slots[-1]], t_end, rel_tol=1e-12))}")
        for slot in slots:
            t = float(times[slot])
            rho = f["observables/density"][0, 0, slot]
            p = f["observables/pressure"][0, 0, slot]
            u = f["observables/velocity"][0, :, slot]
            bad = sum(int((~np.isfinite(a)).sum()) for a in (rho, p, u))
            parts = []
            for yr in ROWS:
                j = min(int(yr / dy), ny - 1)
                xs = front(x, rho[:, j])
                exact = 1.0 / 6.0 + (y[j] + 20.0 * t) / math.sqrt(3.0)
                parts.append(f"y={y[j]:.4f}: {xs:.4f} vs {exact:.4f} ({(xs - exact) / dx:+.2f} cells, "
                             f"10-90% width {width(x, rho[:, j]) / dx:.2f} cells)")
            stem = front(x, rho[:, 0])
            print(f"   t={t:.5f} nonfinite={bad} min_rho={rho.min():.4g} max_rho={rho.max():.4g} "
                  f"min_p={p.min():.4g} max_p={p.max():.4g} | incident shock " + "; ".join(parts)
                  + f" | Mach stem foot on the wall (measured) x={stem:.4f}")


if __name__ == "__main__":
    for path in sys.argv[1:]:
        check(path)
