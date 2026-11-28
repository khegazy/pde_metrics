"""Where the single-cell density dips of a double-Mach-reflection rollout sit, relative to the
exact incident shock x_s(y, t) = 1/6 + (y + 20 t)/sqrt(3) (Kemm 2014, arXiv:1404.6510, Sect. 4.2
set-up), on every 7th saved frame that has a cell below 1.3. Prototype quality, one measurement.

Usage: python -B dip_locations.py ROLLOUT.h5
"""

import math
import sys

import h5py
import numpy as np

with h5py.File(sys.argv[1], "r") as f:
    t = f["time/time"][:]
    nx, ny = f["observables/density"].shape[-2:]
    dx = 4.0 / nx
    print(f"{sys.argv[1]}\n t  min_rho  x  y  (x - x_s)/dx")
    for k in np.flatnonzero(np.isfinite(t))[::7]:
        rho = f["observables/density"][0, 0, k]
        if rho.min() < 1.3:
            i, j = np.unravel_index(rho.argmin(), rho.shape)
            x, y = (i + 0.5) * dx, (j + 0.5) * dx
            print(f"{t[k]:.4f} {rho.min():.3f} {x:.3f} {y:.3f} "
                  f"{(x - 1 / 6 - (y + 20 * t[k]) / math.sqrt(3)) / dx:+.1f}")
