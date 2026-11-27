"""Score the kinet gamma = 1.4 Sod runs at 751, 1501, 3001 nodes against the exact solution
(prototype).

Build-order step 17 (dataset_specs/02_grid_refinement_known_solution.md, Sect. 5.2). The
exact Riemann solution is the metrics repository's `SodShockTube` (fmeval/data/analytic.py,
Toro 2009 ch. 4), imported read-only; nothing of it is reimplemented here.

Unit mapping. kinet runs in lattice units: cell i spans [i, i+1) with centre x_i = i + 1/2
(cells), one step is one time unit, and the states are (rho, T) = (1, 0.2) | (0.125, 0.16),
so p = rho T = 0.2 | 0.02 and every wave speed is in cells per step. The Euler equations
are invariant under x -> a x, t -> a t, so the exact solution in lattice units is the
solution for those (rho, p) at xi = (x - x0) / t, xi in cells per step. kinet's LBM painter
puts cell i on the left when x_i < interface * N (kinet/initialization/riemann.py,
_paint_lattice), so the discrete diaphragm x0 is the face before the first right-state cell,
read here from the stored initial density. `SodShockTube` evaluates its solution at
xi = (centre - 0.5) / t on a unit tube, so its centres are set to 0.5 + (x_i - x0)/N and its
time to t = step / N: that is tube length 1, dx = 1/N, and the same xi. The physical time of
a level is step / N; steps 250, 500, 1000 on 751, 1501, 3001 nodes are t = 0.33289, 0.33311,
0.33322 (they match only to 1e-3 relative, because N - 1, not N, halves exactly).

Errors per level and saved step, per field (density, x velocity, pressure; each row averaged
over the 5 transverse nodes, whose spread is reported): L1 = sum |e| dx, L2 = sqrt(sum e^2 dx),
dx = 1/N. Observed order between successive levels p = ln(E_coarse / E_fine) / ln(N_fine /
N_coarse) (Roy 2005, Eq. 8, with r = N_fine/N_coarse = 1.9987 and 1.9993).

Usage: python -B compare_sod_exact.py OUT_JSON ROLLOUT_751 ROLLOUT_1501 ROLLOUT_3001
"""

from __future__ import annotations

import json
import sys

import h5py
import numpy as np

from fmeval.data.analytic import SodShockTube

GAMMA = 1.4
REPORT_STEPS_3001 = (700, 852, 1000)  # spec 02 asks for 700, 850, 1000; 852 is the nearest step divisible by 4


def load(path: str) -> dict:
    """Steps, x0 and row-averaged density, velocity_x, pressure of one rollout."""
    with h5py.File(path, "r") as f:
        if f.attrs["kinet_rollout_status"] != "complete":
            raise RuntimeError(f"{path}: kinet_rollout_status={f.attrs['kinet_rollout_status']}")
        conv = str(f.attrs.get("pressure_convention", ""))
        step = f["time/time"][:]
        keep = np.flatnonzero(np.isfinite(step))
        obs, ic = f["observables"], f["initial_conditions/observables"]
        rho0, t0 = ic["density"][0, 0, 0], ic["temperature"][0, 0, 0]
        fields = {"density": obs["density"][0, 0][keep], "velocity": obs["velocity"][0, 0][keep],
                  "pressure": obs["pressure"][0, 0][keep]}
        vy_max = float(np.abs(obs["velocity"][0, 1][keep]).max())
        u0_max = float(np.abs(ic["velocity"][0]).max())
        temp = obs["temperature"][0, 0][keep]
    n = rho0.shape[0]
    right = np.flatnonzero(rho0[:, 0] < 0.5)
    x0 = float(right[0])
    if not np.all(np.diff(right) == 1) or right[-1] != n - 1:
        raise RuntimeError(f"{path}: initial density is not one step function")
    states = {"left": (float(rho0[0, 0]), float(rho0[0, 0] * t0[0, 0])),
              "right": (float(rho0[-1, 0]), float(rho0[-1, 0] * t0[-1, 0]))}
    p_rel = float(np.abs(fields["pressure"] - fields["density"] * temp).max())
    spread = {k: float(np.abs(v - v.mean(axis=-1, keepdims=True)).max()) for k, v in fields.items()}
    return {"n": n, "steps": step[keep].astype(int), "x0": x0, "states": states,
            "pressure_convention": conv, "max|p - rho T|": p_rel, "max|u_y|": vy_max,
            "max|u|_initial": u0_max, "max_transverse_spread": spread,
            "fields": {k: v.mean(axis=-1) for k, v in fields.items()}}


def exact(n: int, x0: float, step: int, left, right) -> dict[str, np.ndarray]:
    """Exact density, velocity, pressure at the run's own cell centres after `step` steps."""
    t = step / n
    sod = SodShockTube(gamma=GAMMA, left=left, right=right, grid=(n,), n_frames=1,
                       t_start=t, t_end=t)
    sod.centres = [0.5 + ((np.arange(n) + 0.5) - x0) / n]
    return {k: v[0] for k, v in sod.solution(t).items()}


def main(out: str, *paths: str) -> None:
    """Score every saved step of every level and print the table at the report steps."""
    runs = [load(p) for p in paths]
    ns = [r["n"] for r in runs]
    if ns != sorted(ns):
        raise RuntimeError(f"levels must be given coarse to fine, got {ns}")
    for r in runs[1:]:
        if r["states"] != runs[0]["states"]:
            raise RuntimeError(f"initial states differ: {r['states']} vs {runs[0]['states']}")
    left, right = runs[0]["states"]["left"], runs[0]["states"]["right"]
    result = {"levels": {}, "orders": {}}
    errors = {}
    for r in runs:
        n, dx = r["n"], 1.0 / r["n"]
        lvl = {k: r[k] for k in ("x0", "states", "pressure_convention", "max|p - rho T|",
                                 "max|u_y|", "max|u|_initial", "max_transverse_spread")}
        lvl["steps"], lvl["t_phys"], lvl["L1"], lvl["L2"] = [], [], {}, {}
        for i, s in enumerate(r["steps"]):
            if s < 2:
                continue
            ex = exact(n, r["x0"], int(s), left, right)
            lvl["steps"].append(int(s)); lvl["t_phys"].append(s / n)
            for k in ("density", "velocity", "pressure"):
                e = r["fields"][k][i] - ex[k]
                lvl["L1"].setdefault(k, []).append(float(np.abs(e).sum() * dx))
                lvl["L2"].setdefault(k, []).append(float(np.sqrt((e ** 2).sum() * dx)))
        result["levels"][str(n)] = lvl
        errors[n] = lvl
    # Matched times: coarse step s, fine step s * (N_fine - 1) / (N_coarse - 1) (exactly 2 s).
    for nc, nf in zip(ns[:-1], ns[1:]):
        r_ratio = nf / nc
        key = f"{nc}->{nf}"
        result["orders"][key] = {"r": r_ratio, "coarse_steps": [], "L1": {}, "L2": {}}
        c, f = errors[nc], errors[nf]
        for j, s in enumerate(c["steps"]):
            sf = s * (nf - 1) // (nc - 1)
            if sf not in f["steps"]:
                continue
            jf = f["steps"].index(sf)
            result["orders"][key]["coarse_steps"].append(s)
            for norm in ("L1", "L2"):
                for k in ("density", "velocity", "pressure"):
                    p = np.log(c[norm][k][j] / f[norm][k][jf]) / np.log(r_ratio)
                    result["orders"][key][norm].setdefault(k, []).append(float(p))
    with open(out, "w") as fh:
        json.dump(result, fh, indent=1)

    for n, lvl in result["levels"].items():
        print(f"N={n}: x0={lvl['x0']} states={lvl['states']} {lvl['pressure_convention']} "
              f"max|p-rhoT|={lvl['max|p - rho T|']:.1e} max|u_y|={lvl['max|u_y|']:.1e} "
              f"max|u0|={lvl['max|u|_initial']:.1e} transverse={lvl['max_transverse_spread']}")
    print("\nstep_3001  N  t_phys  L1(rho u p)  L2(rho u p)")
    for s3 in REPORT_STEPS_3001:
        for n in ns:
            lvl = result["levels"][str(n)]
            s = s3 * (n - 1) // 3000
            j = lvl["steps"].index(s)
            print(f"{s3:5d} {n:5d} {lvl['t_phys'][j]:.5f}  "
                  + " ".join(f"{lvl['L1'][k][j]:.3e}" for k in ("density", "velocity", "pressure"))
                  + "  " + " ".join(f"{lvl['L2'][k][j]:.3e}" for k in ("density", "velocity", "pressure")))
        for key, o in result["orders"].items():
            nc = int(key.split("->")[0])
            s = s3 * (nc - 1) // 3000
            j = o["coarse_steps"].index(s)
            print(f"       p {key}: L1 " + " ".join(f"{o['L1'][k][j]:.3f}" for k in ("density", "velocity", "pressure"))
                  + "  L2 " + " ".join(f"{o['L2'][k][j]:.3f}" for k in ("density", "velocity", "pressure")))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
