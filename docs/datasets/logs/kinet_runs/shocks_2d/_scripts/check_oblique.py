"""Check kinet oblique Riemann runs against the exact one-dimensional solution along the normal.

Usage (kinet's .venv, env.sh sourced, the metrics repository on PYTHONPATH):
    PYTHONPATH=/global/u2/k/khegazy/projects/metrics/fluid_metrics \
        python -B check_oblique.py ROLLOUT.h5 [ROLLOUT.h5 ...]

The Euler equations are invariant under rotation, so a Riemann problem whose interface is a
straight line through ``x0`` with unit normal ``n`` has, until a wave reaches a face, the
one-dimensional solution along ``n``, evaluated at ``s = n . (x - x0)`` with the velocity
``u_n n`` (kinet's ``kinet/reference/riemann/euler_nd.py`` docstring states the same). The
one-dimensional solution is the metrics repository's ``fmeval.data.analytic.SodShockTube``
(Toro 2009, ch. 4), built with the run's own two states and gamma; its star state and wave
speeds give the plateau values and the front positions, and its ``solution`` on centres
``s + 1/2`` (its diaphragm is at 1/2) gives the full field.

For every file: the rollout status and last stored time, that every stored frame is finite,
and at each checked time (a) the rms and max error of density, velocity and pressure over the
interior box ``[margin, 1 - margin]^2``, away from the zero-gradient faces where the front
meets them, and (b) a cut along the normal through ``x0``: cells within ``strip`` of the line,
binned by ``s`` at one cell width, give a profile whose plateau medians are compared with the
exact star state and whose density crossings give the contact and shock positions.
"""

import json
import math
import os
import sys

import hdf5plugin  # noqa: F401  (registers blosc2 before h5py opens a PonD rollout)
import h5py
import numpy as np
import yaml
from fmeval.data.analytic import SodShockTube

MARGIN = 0.2      # interior box [MARGIN, 1 - MARGIN]^2 for the field errors
STRIP = 0.05      # half width of the strip along the normal for the cut
CHECK_TIMES = (0.05, 0.1, 0.15, 0.2)


def run_config(path: str) -> dict:
    """The saved run config beside the data: ``<identity>/config.yaml`` above ``tiers/full``."""
    identity = os.path.dirname(os.path.dirname(os.path.dirname(path)))
    with open(os.path.join(identity, "config.yaml")) as fh:
        return yaml.safe_load(fh)


def crossing(s: np.ndarray, q: np.ndarray, level: float, lo: float, hi: float) -> float:
    """The ``s`` in ``[lo, hi]`` where the profile ``q`` first falls through ``level``, by
    linear interpolation between bins; NaN when it does not."""
    sel = (s >= lo) & (s <= hi)
    ss, qq = s[sel], q[sel]
    idx = np.flatnonzero((qq[:-1] >= level) & (qq[1:] < level))
    if idx.size == 0:
        return float("nan")
    i = idx[0]
    return float(ss[i] + (level - qq[i]) * (ss[i + 1] - ss[i]) / (qq[i + 1] - qq[i]))


def check(path: str) -> None:
    """Print the checks of one run."""
    case = run_config(path)["case"]
    ic = case["initial_conditions"]
    gamma = float(case["physics"]["parameters"]["specific_heat_ratio"])
    t_end = float(case["discretization"]["temporal"]["length"])
    normal = np.asarray(ic["normal"], dtype=float)
    normal /= np.linalg.norm(normal)
    left = (ic["left"]["density"], ic["left"]["pressure"])
    right = (ic["right"]["density"], ic["right"]["pressure"])
    with h5py.File(path, "r") as f:
        disc = json.loads(f.attrs["discretization"])
        nx, ny = disc["spatial"]["grid"]
        lx, ly = disc["spatial"]["length"]
        dx = lx / nx
        x, y = np.meshgrid((np.arange(nx) + 0.5) * lx / nx, (np.arange(ny) + 0.5) * ly / ny, indexing="ij")
        x0 = (ic["interface"] * lx, ic["interface"] * ly)
        s = normal[0] * (x - x0[0]) + normal[1] * (y - x0[1])
        tang = -normal[1] * (x - x0[0]) + normal[0] * (y - x0[1])
        times = f["time/time"][:]
        slots = np.flatnonzero(np.isfinite(times))
        status = f.attrs["kinet_rollout_status"]
        angle = math.degrees(math.atan2(normal[1], normal[0]))
        print(f"\n== {path}\n   grid {nx}x{ny}, length {lx}x{ly}, normal at {angle:.2f} deg to x, "
              f"left={left}, right={right}, gamma={gamma}, status={status}, "
              f"saved_frames={slots.size}, last_time={times[slots[-1]]!r}, t_end={t_end}, "
              f"reached_end={bool(status == 'complete' and math.isclose(times[slots[-1]], t_end, rel_tol=1e-12))}")
        nonfinite = 0
        for slot in slots:
            nonfinite += sum(int((~np.isfinite(f[f"observables/{k}"][0, :, slot])).sum())
                             for k in ("density", "velocity", "pressure"))
        print(f"   non-finite values in density, velocity, pressure over all {slots.size} frames: {nonfinite}")
        tube = SodShockTube(gamma=gamma, left=left, right=right, grid=(nx,), n_frames=1,
                            t_start=t_end, t_end=t_end)
        st, sp = tube.star, tube.speeds
        print(f"   exact star state: p*={st['pressure']:.6g} u*={st['velocity']:.6g} "
              f"rho*_L={st['density_left']:.6g} rho*_R={st['density_right']:.6g}; speeds: "
              + " ".join(f"{k}={v:.6g}" for k, v in sp.items()))
        tube.centres = [s + SodShockTube.DIAPHRAGM]  # evaluate the 1D solution at s
        interior = (x > MARGIN) & (x < lx - MARGIN) & (y > MARGIN) & (y < ly - MARGIN)
        cut = interior & (np.abs(tang) < STRIP)
        bins = np.round(s[cut] / dx).astype(int)
        for target in CHECK_TIMES:
            slot = slots[np.argmin(np.abs(times[slots] - target))]
            t = float(times[slot])
            vel = f["observables/velocity"][0, :, slot]
            got = {"density": f["observables/density"][0, 0, slot], "pressure": f["observables/pressure"][0, 0, slot],
                   "velocity_n": normal[0] * vel[0] + normal[1] * vel[1],
                   "velocity_t": -normal[1] * vel[0] + normal[0] * vel[1]}
            ex = tube.solution(t)
            ref = {"density": ex["density"][0], "pressure": ex["pressure"][0],
                   "velocity_n": ex["velocity"][0], "velocity_t": np.zeros_like(s)}
            errs = " ".join(f"{k}: rms={np.sqrt(np.mean((got[k] - ref[k])[interior] ** 2)):.3e} "
                            f"max={np.abs(got[k] - ref[k])[interior].max():.3e};" for k in got)
            print(f"   t={t:.5f} interior-box errors  {errs}")
            # The cut: bin the strip by s at one cell width and average each bin.
            uniq = np.unique(bins)
            prof = {k: np.array([got[k][cut][bins == b].mean() for b in uniq]) for k in got}
            sb = uniq * dx
            x_contact, x_shock = sp["contact"] * t, sp["shock"] * t
            x_tail, x_head = sp["tail"] * t, sp["head"] * t
            pad = 4 * dx
            plateaus = {
                "p* (tail..shock)": (prof["pressure"], (x_tail + pad, x_shock - pad), st["pressure"]),
                "u* (tail..shock)": (prof["velocity_n"], (x_tail + pad, x_shock - pad), st["velocity"]),
                "rho*_L (tail..contact)": (prof["density"], (x_tail + pad, x_contact - pad), st["density_left"]),
                "rho*_R (contact..shock)": (prof["density"], (x_contact + pad, x_shock - pad), st["density_right"]),
            }
            line = []
            for name, (q, (a, b), exact) in plateaus.items():
                sel = (sb >= a) & (sb <= b)
                med = float(np.median(q[sel])) if sel.any() else float("nan")
                line.append(f"{name}={med:.5g} (exact {exact:.5g}, rel {(med - exact) / exact:+.2e}, {int(sel.sum())} bins)")
            shock_level = 0.5 * (st["density_right"] + right[0])
            contact_level = 0.5 * (st["density_left"] + st["density_right"])
            # From the rarefaction tail rightwards the density falls through the contact level
            # first, then (below rho*_R) through the shock level.
            xs = crossing(sb, prof["density"], shock_level, x_tail, x_shock + 20 * dx)
            xc = crossing(sb, prof["density"], contact_level, x_tail, x_shock + 20 * dx)
            print(f"   t={t:.5f} cut ({uniq.size} bins of {dx:.4g}): " + "; ".join(line))
            print(f"   t={t:.5f} cut: shock at s={xs:.5f} (exact {x_shock:.5f}, diff {(xs - x_shock) / dx:+.2f} cells); "
                  f"contact at s={xc:.5f} (exact {x_contact:.5f}, diff {(xc - x_contact) / dx:+.2f} cells); "
                  f"max |tangential velocity| in interior {np.abs(got['velocity_t'][interior]).max():.3e}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        check(p)
