"""Density contours of a double Mach reflection rollout at its last stored frame (prototype).

Usage: MPLBACKEND=Agg python -B plot_dmr_density.py ROLLOUT.h5 OUT.png
30 contour levels from 1.73 to 20.92 on x in [0, 3.2] (a common choice in later papers; not checked against a source here).
"""

import sys

import h5py
import matplotlib.pyplot as plt
import numpy as np

path, out = sys.argv[1], sys.argv[2]
with h5py.File(path, "r") as f:
    t = f["time/time"][:]
    s = np.flatnonzero(np.isfinite(t))[-1]
    rho = f["observables/density"][0, 0, s]
nx, ny = rho.shape
fig, ax = plt.subplots(figsize=(12, 3.5))
ax.contour((np.arange(nx) + 0.5) * 4.0 / nx, (np.arange(ny) + 0.5) * 1.0 / ny, rho.T,
           levels=np.linspace(1.73, 20.92, 30), linewidths=0.6, colors="k")
ax.set_xlim(0, 3.2)
ax.set_aspect("equal")
ax.set_title(f"DMR {nx}x{ny} density t={t[s]:.3f}")
fig.savefig(out, dpi=110, bbox_inches="tight")
