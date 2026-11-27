"""Checks on the degraded isotropic kinet runs of candidates_driver.py (BUILD_ORDER.md step 20).

Research-grade. Reads each complete candidate run and its reference (CFS, read-only) and computes,
at reference frames F (solver step 10 F at 256^2; candidate step 10 F N / 256 on grid N):

* relative L2 distances  d_u = ||u_c - u_r|| / ||u_r||  and  d_w = ||w_c - w_r|| / ||w_r||  on the
  candidate's grid, the reference block-averaged to it for the coarse grids;
* the saturation level of each distance, sqrt(||a_c||^2 + ||a_r||^2) / ||a_r||, which is what d
  becomes for two uncorrelated fields (cross term zero), so d / d_sat near 1 means decorrelated;
* kinetic energy E = <|u|^2> / 2 and enstrophy Z = <w^2> / 2 (cell means; density not weighted)
  of candidate and reference on the candidate's grid;
* at the evaluated frames 150, 200, ..., 550 (configs/dataset/_decaying_isotropic_2d.yaml), whether
  the candidates order as expected: control below every degradation, 64^2 above 128^2, and
  Re x 0.5 above Re x 0.75 above Re x 0.9.

Vorticity is recomputed for both fields as the spectral curl of the velocity on the comparison
grid, in units of 1 / (256^2 solver step) on every grid: the archive stores the D2Q9 stencil curl
at Re 1.25e4 and 2.5e4 but the spectral curl at 5e4 (coarse-graining recomputed it), and kinet's
stored vorticity is per step of its own grid, so stored values are not comparable across grids.

Usage: python candidates_checks.py OUT_DIR RESULT_PREFIX   (writes RESULT_PREFIX.json and .txt)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from candidates_driver import DATA, KINDS, REF_GRID, REFERENCES, block_average  # noqa: E402

FRAMES = [0, 2, 4, 10, 20, 50] + list(range(100, 1001, 50))
EVALUATED = list(range(150, 600, 50))
DEGRADED = [k for k in KINDS if k != "control"]


def curl(u: np.ndarray) -> np.ndarray:
    """Spectral curl d(u_y)/dx - d(u_x)/dy of a periodic (2, N, N) field, per 256^2 cell (axis 0 = x)."""
    n = u.shape[-1]
    k = np.fft.fftfreq(n, d=1.0 / n) * 2.0 * np.pi / REF_GRID
    kx, ky = np.meshgrid(k, k, indexing="ij")
    uh = np.fft.fft2(u)
    return np.fft.ifft2(1j * kx * uh[1] - 1j * ky * uh[0]).real


def distances(uc: np.ndarray, ur: np.ndarray) -> dict:
    """Relative L2 distances, saturation levels, energy and enstrophy of a candidate/reference pair."""
    wc, wr = curl(uc), curl(ur)
    out = {}
    for name, c, r in (("u", uc, ur), ("w", wc, wr)):
        nr, nc = np.linalg.norm(r), np.linalg.norm(c)
        out[f"d_{name}"] = float(np.linalg.norm(c - r) / nr)
        out[f"dsat_{name}"] = float(np.hypot(nc, nr) / nr)
    out.update(E_c=float(0.5 * np.mean(np.sum(uc**2, 0))), E_r=float(0.5 * np.mean(np.sum(ur**2, 0))),
               Z_c=float(0.5 * np.mean(wc**2)), Z_r=float(0.5 * np.mean(wr**2)))
    return out


def candidate_frame(f: h5py.File, step: int, index: dict) -> np.ndarray | None:
    """Velocity (2, N, N) of the candidate at solver step `step`, or None if it was not saved."""
    if step == 0:
        return f["initial_conditions/observables/velocity"][0, :, 0]
    i = index.get(step)
    return None if i is None else f["observables/velocity"][0, :, i]


def main() -> None:
    out_dir, prefix = Path(sys.argv[1]), sys.argv[2]
    result = {"frames": FRAMES, "evaluated_frames": EVALUATED, "definitions": __doc__.split("\n\n")[1:3], "Re": {}}
    for re_key, (_, keys) in REFERENCES.items():
        per = {}
        for kind, (grid, _, _) in KINDS.items():
            sp = out_dir / f"Re-{re_key}" / kind / "summary.json"
            if not sp.exists():
                continue
            runs = json.loads(sp.read_text())["runs"]
            for key in keys:
                rec = runs.get(key)
                if rec is None:
                    continue
                entry = {"reached_last_step": rec["reached_last_step"], "last_saved_step": rec.get("last_saved_step"),
                         "stop_reason": rec.get("stop_reason"), "error": rec.get("error"), "series": {}}
                with h5py.File(rec["path"], "r") as fc, h5py.File(f"{DATA}/sys_Re-{re_key}_Ma-1en1/{key}.h5", "r") as fr:
                    s = fc["time/time"][:]
                    index = {int(v): i for i, v in enumerate(s) if np.isfinite(v)}
                    for F in FRAMES:
                        step = 10 * F * grid // REF_GRID
                        if (10 * F * grid) % REF_GRID:
                            continue
                        uc = candidate_frame(fc, step, index)
                        if uc is None or not np.all(np.isfinite(uc)):
                            continue
                        ur = block_average(fr["velocity"][0, :, F], REF_GRID // grid)
                        entry["series"][F] = {k: float(f"{v:.5g}") for k, v in distances(uc, ur).items()}
                per.setdefault(key, {})[kind] = entry
        if per:
            result["Re"][re_key] = per
    result["ordering"] = ordering(result)
    Path(prefix + ".json").write_text(json.dumps(result, separators=(",", ":")))
    Path(prefix + ".txt").write_text(render(result))
    print(render(result))


def ordering(result: dict) -> dict:
    """At each evaluated frame and reference, which expected orderings hold (velocity and vorticity)."""
    out = {}
    for re_key, per in result["Re"].items():
        for key, kinds in per.items():
            for F in EVALUATED:
                d = {k: kinds[k]["series"].get(F) for k in kinds}
                d = {k: v for k, v in d.items() if v is not None}
                for q in ("u", "w"):
                    v = {k: d[k][f"d_{q}"] for k in d}
                    checks = {}
                    if "control" in v and any(k in v for k in DEGRADED):
                        checks["control_below_all"] = all(v["control"] < v[k] for k in DEGRADED if k in v)
                    if "grid64" in v and "grid128" in v:
                        checks["grid64_above_grid128"] = v["grid64"] > v["grid128"]
                    if all(k in v for k in ("re0.5", "re0.75", "re0.9")):
                        checks["viscosity_monotone"] = v["re0.5"] > v["re0.75"] > v["re0.9"]
                    out.setdefault(re_key, {}).setdefault(key, {}).setdefault(q, {})[F] = checks
    return out


def render(result: dict) -> str:
    """Text tables: per Re, the median over references of d_u, d_w, d/d_sat, and the ordering counts."""
    lines = []
    for re_key, per in result["Re"].items():
        kinds = [k for k in KINDS if any(k in per[key] for key in per)]
        lines.append(f"== Re {re_key}: {len(per)} references; median over references (n = references with that frame)")
        for q in ("u", "w"):
            lines.append(f"-- relative L2 distance d_{q} [median d/d_sat in brackets]")
            lines.append("frame  " + "".join(f"{k:>20s}" for k in kinds))
            for F in result["frames"]:
                row = []
                for k in kinds:
                    vals = [(per[key][k]["series"][F][f"d_{q}"], per[key][k]["series"][F][f"dsat_{q}"])
                            for key in per if k in per[key] and F in per[key][k]["series"]]
                    if vals:
                        dd = np.array(vals)
                        row.append(f"{np.median(dd[:, 0]):9.3g} [{np.median(dd[:, 0] / dd[:, 1]):.2f}] n{len(vals)}")
                    else:
                        row.append("-")
                lines.append(f"{F:5d}  " + "".join(f"{x:>20s}" for x in row))
        lines.append("-- energy and enstrophy ratio candidate / reference (median), at evaluated frames 150 and 550")
        for k in kinds:
            r = []
            for F in (150, 550):
                vals = [(per[key][k]["series"][F]["E_c"] / per[key][k]["series"][F]["E_r"],
                         per[key][k]["series"][F]["Z_c"] / per[key][k]["series"][F]["Z_r"])
                        for key in per if k in per[key] and F in per[key][k]["series"]]
                if vals:
                    m = np.median(np.array(vals), axis=0)
                    r.append(f"F{F}: E {m[0]:.3f} Z {m[1]:.3f}")
            lines.append(f"   {k:8s} " + "; ".join(r))
        lines.append("-- expected ordering at evaluated frames: references where it holds / references checked")
        ordr = result["ordering"].get(re_key, {})
        for q in ("u", "w"):
            for check in ("control_below_all", "grid64_above_grid128", "viscosity_monotone"):
                cells = []
                for F in EVALUATED:
                    got = [ordr[key][q][F][check] for key in ordr if check in ordr[key][q].get(F, {})]
                    cells.append(f"{F}:{sum(got)}/{len(got)}" if got else f"{F}:-")
                lines.append(f"   d_{q} {check:22s} " + " ".join(cells))
        lines.append("-- runs that did not reach their last step")
        for key in per:
            for k, e in per[key].items():
                if not e["reached_last_step"]:
                    lines.append(f"   {key} {k}: stop_reason={e['stop_reason']} last_saved_step={e['last_saved_step']} error={e['error']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
