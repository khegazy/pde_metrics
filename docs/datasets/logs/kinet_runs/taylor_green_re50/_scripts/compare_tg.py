"""Compare kinet 2D Taylor-Green runs with the exact solution and compute observed orders.

Prototype quality (a one-off verification script for step 16 of BUILD_ORDER.md).

Exact solution (Taylor 1923; spec 02, Sect. 4.1), in each run's own lattice units:

    u =  U0 sin(k x) cos(k y) exp(-2 nu k^2 t)
    v = -U0 cos(k x) sin(k y) exp(-2 nu k^2 t)

with x, y the cell centres (i + 1/2) in cells (kinet's `_build_coordinate_grid` places node i at
(i + 1/2) 2 pi / N), k = 2 pi / N per cell, nu = nu_l and U0 = u_l from the file's
`normalization_plan`, and t the lattice clock `time/time` (steps). Errors are divided by U0, so
they are the physical errors of a unit-amplitude vortex on [0, 2 pi)^2 and comparable across
levels whose lattice velocity differs (diffusive scaling).

Norms (Roy 2005, Eq. 7): L2 = sqrt(mean over nodes of (du^2 + dv^2) / 2), Linf = max over nodes
and both components of |du|, |dv|. Observed order (Roy 2005, Eq. 8): p = ln(E_2h / E_h) / ln 2.

The error is also split into an amplitude part (the projection of the numerical field on the
exact mode shape, minus the exact amplitude: a decay-rate or start-up error) and a shape part
(the rest, orthogonal to the mode: aliasing, compressibility harmonics, node misplacement).

Usage: python compare_tg.py OUT.json LABEL=PATH/rollout.h5 [LABEL=PATH ...]
Labels of one sequence must be given coarse to fine.
"""

import json
import math
import sys

import h5py
import numpy as np

FRACTIONS = (0.25, 0.5, 0.75, 1.0)  # comparison times as fractions of the run's last step


def compare(path: str) -> dict:
    """Return per-frame errors of one rollout against the exact Taylor-Green solution."""
    with h5py.File(path, "r") as f:
        plan = json.loads(f.attrs["normalization_plan"])["lattice"]
        nu, U0 = plan["nu_l"], plan["u_l"]
        grid = json.loads(f.attrs["discretization"])["spatial"]["grid"]
        if grid[0] != grid[1]:
            raise ValueError(f"{path}: grid {grid} is not square")
        N = grid[0]
        steps = f["time/time"][:]
        saved = np.flatnonzero(np.isfinite(steps))
        vel = f["observables/velocity"]
        k = 2.0 * math.pi / N
        x = np.arange(N) + 0.5  # cell centres in cells; axis 3 is x, axis 4 is y
        sx, cx = np.sin(k * x)[:, None], np.cos(k * x)[:, None]
        sy, cy = np.sin(k * x)[None, :], np.cos(k * x)[None, :]
        shape_u, shape_v = sx * cy, -cx * sy
        norm2 = (shape_u**2 + shape_v**2).sum()
        frames = []
        for slot in saved:
            t = float(steps[slot])
            u, v = vel[0, 0, slot], vel[0, 1, slot]
            amp_exact = U0 * math.exp(-2.0 * nu * k * k * t)
            du, dv = u - amp_exact * shape_u, v - amp_exact * shape_v
            amp_num = float((u * shape_u + v * shape_v).sum() / norm2)
            ru, rv = u - amp_num * shape_u, v - amp_num * shape_v
            frames.append(
                {
                    "step": t,
                    "t_over_td": t * 2.0 * nu * k * k,
                    "L2": math.sqrt(float((du**2 + dv**2).mean()) / 2.0) / U0,
                    "Linf": float(max(np.abs(du).max(), np.abs(dv).max())) / U0,
                    "amplitude_error": (amp_num - amp_exact) / U0,
                    "shape_L2": math.sqrt(float((ru**2 + rv**2).mean()) / 2.0) / U0,
                }
            )
    return {"N": N, "nu_l": nu, "u_l": U0, "tau": 0.5 + 3.0 * nu, "frames": frames}


def at_fraction(run: dict, frac: float) -> dict:
    """Return the frame whose step equals frac times the last step (exactly, else refuse)."""
    last = run["frames"][-1]["step"]
    target = frac * last
    for fr in run["frames"]:
        if abs(fr["step"] - target) < 1e-9:
            return fr
    raise ValueError(f"N={run['N']}: no frame at step {target}")


def main() -> None:
    out = sys.argv[1]
    runs = {}
    for arg in sys.argv[2:]:
        label, path = arg.split("=", 1)
        runs[label] = compare(path)
    labels = list(runs)
    table = []
    for frac in FRACTIONS:
        prev = None
        for label in labels:
            fr = at_fraction(runs[label], frac)
            row = {"label": label, "N": runs[label]["N"], "fraction": frac, **fr}
            if prev is not None:
                for key in ("L2", "Linf", "shape_L2"):
                    row[f"p_{key}"] = math.log(prev[key] / fr[key]) / math.log(2.0)
                row["p_amplitude"] = math.log(
                    abs(prev["amplitude_error"]) / abs(fr["amplitude_error"])
                ) / math.log(2.0)
            table.append(row)
            prev = fr
    with open(out, "w") as fh:
        json.dump({"runs": runs, "table": table}, fh, indent=1)
    head = f"{'label':>10} {'N':>4} {'t/T':>5} {'t/td':>6} {'L2':>10} {'p':>6} {'Linf':>10} {'p':>6} {'amp err':>10} {'p':>6} {'shape L2':>10} {'p':>6}"
    print(head)
    for r in table:
        def p(key: str) -> str:
            return f"{r[key]:6.2f}" if key in r else "     -"
        print(
            f"{r['label']:>10} {r['N']:>4} {r['fraction']:5.2f} {r['t_over_td']:6.3f} "
            f"{r['L2']:10.3e} {p('p_L2')} {r['Linf']:10.3e} {p('p_Linf')} "
            f"{r['amplitude_error']:10.3e} {p('p_amplitude')} {r['shape_L2']:10.3e} {p('p_shape_L2')}"
        )


if __name__ == "__main__":
    main()
