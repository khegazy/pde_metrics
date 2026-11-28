"""Check kinet isentropic-vortex runs against the exact solution and read the observed order.

Usage (kinet's .venv, env.sh sourced):
    python -B check_vortex.py ROLLOUT.h5 [ROLLOUT.h5 ...]

The exact solution is Shu's vortex carried by the uniform flow, the same formula kinet paints
its initial condition from (``kinet.reference.vortex.isentropic_vortex``; Shu, ICASE Report
98-32, Sect. 4.5; Spiegel, Huynh and DeBonis 2015, Sect. IV.B.1: the exact solution is the
translation of the initial condition). It is evaluated at every stored frame's own time on the
run's cell centres ``x_i = (i + 1/2) L / N``, read from the file's ``discretization`` attribute.

For every file: the rollout status, that the last stored time is the configured end time, that
every stored frame of density, velocity and pressure is finite, and per frame the rms (L2 over
cells) and max (L-infinity) error of density, each velocity component and pressure. Across
files on a ratio-2 grid sequence: the observed order ``p = log(e_coarse / e_fine) / log(N_fine
/ N_coarse)`` of each error, from the coarse grid's stored frame nearest each target time and
the fine grid's stored frame nearest that one (pairs more than ``MAX_MISMATCH`` apart are
skipped) (Roache 1998;
dataset spec 02, Sect. 3). Frames are read one at a time.
"""

import json
import math
import os
import sys

import hdf5plugin  # noqa: F401  (registers blosc2 before h5py opens a PonD rollout)
import h5py
import numpy as np
import torch
import yaml
from kinet.config.components.vortex import IsentropicVortexIC
from kinet.reference.vortex import isentropic_vortex

FIELDS = ("density", "velocity_x", "velocity_y", "pressure")
TARGET_TIMES = (2.5, 5.0, 10.0)
MAX_MISMATCH = 0.01  # largest time difference between the two frames of an order pair


def run_config(path: str) -> dict:
    """The saved run config beside the data: ``<identity>/config.yaml`` above ``tiers/full``."""
    identity = os.path.dirname(os.path.dirname(os.path.dirname(path)))
    with open(os.path.join(identity, "config.yaml")) as fh:
        return yaml.safe_load(fh)


def frame(f: h5py.File, prefix: str, slot: int) -> dict[str, np.ndarray]:
    """Density, the two velocity components and pressure of one stored slot, as ``(X, Y)``."""
    velocity = f[f"{prefix}observables/velocity"][0, :, slot]
    return {"density": f[f"{prefix}observables/density"][0, 0, slot],
            "velocity_x": velocity[0], "velocity_y": velocity[1],
            "pressure": f[f"{prefix}observables/pressure"][0, 0, slot]}


def check(path: str) -> dict:
    """Errors per frame of one run, with its status checks printed."""
    cfg = run_config(path)
    case = cfg["case"]
    ic = IsentropicVortexIC(**case["initial_conditions"])
    gamma = float(case["physics"]["parameters"]["specific_heat_ratio"])
    t_end = float(case["discretization"]["temporal"]["length"])
    with h5py.File(path, "r") as f:
        disc = json.loads(f.attrs["discretization"])
        nx, ny = disc["spatial"]["grid"]
        lx, ly = disc["spatial"]["length"]
        centres = [torch.as_tensor((np.arange(n) + 0.5) * (length / n), dtype=torch.float64)
                   for n, length in ((nx, lx), (ny, ly))]
        times = f["time/time"][:]
        slots = np.flatnonzero(np.isfinite(times))
        status = f.attrs["kinet_rollout_status"]
        print(f"\n== {path}\n   grid {nx}x{ny}, length {lx}x{ly}, status={status}, "
              f"last_completed_step={f.attrs.get('kinet_last_completed_step')}, "
              f"saved_frames={slots.size}, last_time={times[slots[-1]]!r}, t_end={t_end}, "
              f"reached_end={bool(status == 'complete' and math.isclose(times[slots[-1]], t_end, rel_tol=1e-12))}")
        rows, nonfinite = [], 0
        for prefix, slot, t in [("initial_conditions/", 0, 0.0)] + [("", s, float(times[s])) for s in slots]:
            got = frame(f, prefix, slot)
            nonfinite += sum(int((~np.isfinite(v)).sum()) for v in got.values())
            exact = isentropic_vortex(ic, gamma=gamma, coordinates=centres, lo=[0.0, 0.0],
                                      length=[lx, ly], t=t)
            ref = {"density": exact["density"].numpy(), "velocity_x": exact["velocity"][..., 0].numpy(),
                   "velocity_y": exact["velocity"][..., 1].numpy(), "pressure": exact["pressure"].numpy()}
            err = {k: got[k] - ref[k] for k in FIELDS}
            rows.append({"t": t, **{f"rms_{k}": float(np.sqrt(np.mean(e * e))) for k, e in err.items()},
                         **{f"max_{k}": float(np.abs(e).max()) for k, e in err.items()}})
        print(f"   non-finite values in density, velocity, pressure over all frames: {nonfinite}")
        print("   t          " + " ".join(f"rms_{k:11s}" for k in FIELDS) + " " + " ".join(f"max_{k:11s}" for k in FIELDS))
        for r in rows:
            print(f"   {r['t']:<10.5f} " + " ".join(f"{r['rms_' + k]:<15.4e}" for k in FIELDS)
                  + " " + " ".join(f"{r['max_' + k]:<15.4e}" for k in FIELDS))
    return {"n": nx, "rows": rows}


def nearest(rows: list[dict], t: float) -> dict:
    """The stored frame nearest time ``t``."""
    return min(rows, key=lambda r: abs(r["t"] - t))


def main(paths: list[str]) -> None:
    """Check every file, then print the observed orders between consecutive grids."""
    runs = sorted((check(p) for p in paths), key=lambda r: r["n"])
    for coarse, fine in zip(runs, runs[1:]):
        print(f"\n== observed order, N = {coarse['n']} -> {fine['n']}")
        for t in TARGET_TIMES:
            # The fine frame nearest the coarse one, so both errors are read at (nearly) one
            # time; a pair further apart than MAX_MISMATCH, or far from the target, is skipped.
            a = nearest(coarse["rows"], t)
            b = nearest(fine["rows"], a["t"])
            if abs(a["t"] - b["t"]) > MAX_MISMATCH or abs(a["t"] - t) > 0.5:
                print(f"   target t={t}: no matched pair (frames at t={a['t']:.5f} and {b['t']:.5f}); skipped")
                continue
            ratio = math.log(fine["n"] / coarse["n"])
            orders = {k: math.log(a[k] / b[k]) / ratio for k in a if k != "t"}
            print(f"   target t={t}: frames at t={a['t']:.5f} and {b['t']:.5f}; "
                  + " ".join(f"p_{k}={v:.3f}" for k, v in orders.items()))


if __name__ == "__main__":
    main(sys.argv[1:])
