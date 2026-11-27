"""Bow-shock stand-off and wake probe of the kinet Mach 1.8 cylinder run against time (prototype).

Build-order step 28; docs/datasets/logs/supersonic_cylinder.md, "What part will be
evaluated", asks to start the evaluated window where the stand-off distance on the centre
line has settled to within one node. The cylinder (centre (166, 150), radius 20 cells) is
read from the run's own solid mask. The shock on the centre line is the first node,
marching downstream from the inlet, where the pressure exceeds the inflow pressure by half
the normal-shock jump at the inflow Mach number, p2/p1 = 1 + 2 gamma (M^2 - 1)/(gamma + 1)
(the standard normal-shock pressure ratio); the stand-off
is the distance from that node to the cylinder's first solid node. The wake probe is the
transverse velocity two diameters behind the cylinder on the centre line.

Usage: python -B cylinder_settling.py ROLLOUT OUT_JSON
"""

from __future__ import annotations

import json
import sys

import h5py
import hdf5plugin  # noqa: F401  (kinet may compress; harmless otherwise)
import numpy as np

GAMMA, MACH = 1.4, 1.8


def main(path: str, out: str) -> None:
    """Write step, stand-off and wake-probe series and print every 50th step."""
    with h5py.File(path, "r") as f:
        if f.attrs["kinet_rollout_status"] != "complete":
            raise RuntimeError(f"kinet_rollout_status={f.attrs['kinet_rollout_status']}")
        solid = np.asarray(f["geometry/masks/solid"]).astype(bool)
        cx, cy = np.argwhere(solid).mean(axis=0).round().astype(int)
        nose = int(np.flatnonzero(solid[:, cy])[0])
        back = int(np.flatnonzero(solid[:, cy])[-1])
        diameter = back - nose + 1
        probe = back + 2 * diameter
        step = f["time/time"][:]
        keep = np.flatnonzero(np.isfinite(step))
        p_line = f["observables/pressure"][0, 0][keep, :nose, cy]
        v_probe = f["observables/velocity"][0, 1][keep, probe, cy]
    p_in = p_line[:, :5].mean(axis=1)
    jump = 1.0 + 2.0 * GAMMA * (MACH ** 2 - 1.0) / (GAMMA + 1.0)
    threshold = p_in * (1.0 + 0.5 * (jump - 1.0))
    standoff = []
    for p, thr in zip(p_line, threshold):
        above = np.flatnonzero(p > thr)
        standoff.append(float(nose - above[0]) if above.size else float("nan"))
    res = {"steps": step[keep].astype(int).tolist(), "standoff_cells": standoff,
           "wake_probe_uy": v_probe.tolist(), "nose_x": nose, "centre": [int(cx), int(cy)],
           "diameter_cells": diameter, "probe_x": probe, "normal_shock_p2_p1": jump}
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"centre {cx, cy}, nose x {nose}, diameter {diameter}, probe x {probe}, p2/p1 {jump:.3f}")
    for s, d, v in zip(res["steps"], standoff, v_probe):
        if s % 50 == 0:
            print(f"  step {s:5d}  standoff {d:5.1f} cells  wake u_y {v:+.4f}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
