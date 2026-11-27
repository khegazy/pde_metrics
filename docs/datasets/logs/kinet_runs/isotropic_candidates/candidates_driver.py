"""Degraded kinet runs of the decaying 2D isotropic reference set (BUILD_ORDER.md step 20).

Research-grade (kept for reproducing step 20; dataset_specs/05_initial_conditions_and_degraded_solver_runs.md,
Sects. 4.1 and 4.2). Solver simulations only; nothing here trains or runs a machine-learning model.
Adapted from _provenance/shear_layer_ensemble/ensemble_driver.py (same library route, same
completion checks); the perturbation and the stored-population hand-over are dropped, because the
archived isotropic runs stored no populations and started from equilibrium.

What it does, in one Python process so Python start-up is paid once per job:

1. For each candidate kind (a grid, a Reynolds-number factor, a collision model) compose the
   current kinet's isotropic case `homogeneous_isotropic_turbulence/Re-50k_Ma-1en1` with the
   archive's physics (Re, Ma 0.1, D2Q9, entropic BGK with the entropic equilibrium,
   use_static_weights=true, docs/datasets/logs/kinet_runs/kinet_hit_re*/<key>/config.yaml) and
   `initialization_policy=equilibrium`, so the populations are seeded as F = Feq(rho, u) with no
   non-equilibrium correction, as the archived runs started (kinet_runs/README.md, "Initial
   populations"). Build one simulator per kind; torch.compile once per kind.
2. For each reference key read frame 0 (the stored step-0 state) of the converted flat file:
   density (X, Y) and velocity (2, X, Y). For a coarse grid, block-average both by 256/N
   (velocity averaged directly, as the metrics repository's remap compares it).
3. Start kinet from those macroscopic fields with kinet's `initial_state` route
   (00_how_to_use_kinet.md, Sect. 6a), step it, and write a normal grouped rollout of
   macroscopic observables only (io.record_distributions=false, io.record_equilibria=false).
4. Acoustic scaling (05, Sect. 4.1): steps = 10000 * N / 256, so every grid ends at the same
   convective time 2.2553. Saved every 10 steps at 256^2 (every reference frame), every 5 at
   128^2 (every reference frame), every 5 at 64^2 (= 20 fine steps, every second reference frame,
   which includes every evaluated frame 150, 200, ..., 550; 2.5 steps cannot be saved).
5. Check every run: stop_reason, kinet_rollout_status, last saved step, and that the stored
   initial condition equals the macros handed in. A run that fails (BGK instability, the
   walltime guard) is recorded with its step and the driver goes on to the next run; delete
   simulation checkpoints after each run.

Usage (from a working directory on scratch, KINET_PROJECT set; see _work/env.sh):
    python candidates_driver.py --re 25k --kinds control,grid128,grid64,bgk \
        --out /pscratch/sd/k/khegazy/kinet_datasets/isotropic_candidates [--keys k1,k2] [--steps-cap 20]
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

import h5py
import numpy as np
import torch

import kinet
from kinet.initialization.state import initial_state
from kinet.logging import KinetProcessLog
from kinet.runtime.distributed.process import single_process_config
from kinet.runtime.hydra.compose import compose_run_config
from kinet.runtime.hydra.simulate_save_config import simulate_save_config
from kinet.simulation.access import kinetic_solver_of
from kinet.simulation.rollout_control import RolloutControl

DATA = "/global/cfs/cdirs/m4790/Data/kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids"
# Reynolds number and the five evaluated keys per Reynolds number: the sweep line of each option
# in the metrics repository, configs/dataset/kinet_hit_re{12p5k,25k,50k}.yaml.
REFERENCES = {
    "12p5k": (12500.0, ["c5ccb2", "6f3450", "3c2c65", "10383c", "f151b4"]),
    "25k": (25000.0, ["c95586", "49a8ad", "2bf18d", "0789a4", "e72a16"]),
    "50k": (50000.0, ["cf7333", "6729a8", "3cf779", "137164", "f19e41"]),
}
REF_GRID, REF_STEPS = 256, 10000
# kind -> (grid N, Reynolds factor, collision). "control" is the reference's own settings.
KINDS = {
    "control": (256, 1.0, "entropic"),
    "grid128": (128, 1.0, "entropic"),
    "grid64": (64, 1.0, "entropic"),
    "re0.9": (256, 0.9, "entropic"),
    "re0.75": (256, 0.75, "entropic"),
    "re0.5": (256, 0.5, "entropic"),
    "bgk": (256, 1.0, "bgk"),
}
SAVE_EVERY = {256: 10, 128: 5, 64: 5}
BGK = ["collision@case.collision=bgk", "~collision/stabilizer@case.collision.stabilizer",
       "equilibrium_closure/numeric@case.simulate_equilibrium_closure.F=polynomial"]


def overrides(grid: int, steps: int, reynolds: float, collision: str, data_root: str, device: str) -> list[str]:
    """Hydra overrides for one candidate kind on the current kinet (00_how_to_use_kinet.md, Sects. 3, 7)."""
    return [
        "case=homogeneous_isotropic_turbulence/Re-50k_Ma-1en1",
        f"++case.discretization.spatial.grid=[{grid},{grid}]",
        f"++case.discretization.temporal.grid={steps}",
        f"++case.physics.parameters.reynolds={reynolds}",
        "++case.physics.parameters.initialization_policy=equilibrium",
        "++case.lattice.use_static_weights=true",
        f"++io.save_every_n={SAVE_EVERY[grid]}",
        "++io.record_distributions=false",
        "++io.record_equilibria=false",
        f"++launch.device={device}",
        f"++launch.compile={'true' if device == 'cuda' else 'false'}",
        "task=simulate",
        f"++paths.data_root={data_root}",
    ] + (BGK if collision == "bgk" else [])


def block_average(a: np.ndarray, factor: int) -> np.ndarray:
    """Average the last two axes over factor x factor blocks (exact cell averages on a nested grid)."""
    if factor == 1:
        return a
    *lead, nx, ny = a.shape
    if nx % factor or ny % factor:
        raise ValueError(f"grid {nx}x{ny} is not divisible by {factor}")
    return a.reshape(*lead, nx // factor, factor, ny // factor, factor).mean(axis=(-3, -1))


def start_fields(key_path: str, grid: int) -> tuple[np.ndarray, np.ndarray]:
    """Return density (N, N) and velocity (2, N, N) of the reference's stored step 0 on grid N."""
    with h5py.File(key_path, "r") as f:
        if float(f["time_index"][0]) != 0.0 or float(f["time"][0]) != 0.0:
            raise RuntimeError(f"{key_path}: frame 0 is not step 0")
        rho = f["density"][0, 0, 0]
        u = f["velocity"][0, :, 0]
    if rho.shape != (REF_GRID, REF_GRID):
        raise RuntimeError(f"{key_path}: expected a {REF_GRID}^2 grid, found {rho.shape}")
    return block_average(rho, REF_GRID // grid), block_average(u, REF_GRID // grid)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--re", required=True, choices=sorted(REFERENCES))
    p.add_argument("--kinds", required=True, help=f"comma list of {list(KINDS)}")
    p.add_argument("--keys", default="", help="comma list of reference keys (default: the five evaluated)")
    p.add_argument("--out", required=True)
    p.add_argument("--device", default="cuda")
    p.add_argument("--steps-cap", type=int, default=0, help="test only: cap the steps per run")
    p.add_argument("--force", action="store_true", help="rerun runs already complete")
    a = p.parse_args()

    reynolds, default_keys = REFERENCES[a.re]
    keys = a.keys.split(",") if a.keys else default_keys
    kinds = a.kinds.split(",")
    unknown = [k for k in kinds if k not in KINDS]
    if unknown:
        raise SystemExit(f"unknown kinds {unknown}")
    log = KinetProcessLog("candidates")
    kinet_commit = subprocess.run(["git", "-C", os.environ["KINET_PROJECT"], "rev-parse", "HEAD"],
                                  capture_output=True, text=True, check=True).stdout.strip()
    device_name = torch.cuda.get_device_name() if a.device == "cuda" else "cpu"
    failures = 0

    for kind in kinds:
        grid, factor, collision = KINDS[kind]
        steps = REF_STEPS * grid // REF_GRID
        if a.steps_cap:
            steps = min(steps, a.steps_cap)
        out = Path(a.out) / f"Re-{a.re}" / kind
        out.mkdir(parents=True, exist_ok=True)
        summary_path = out / "summary.json"
        summary = json.loads(summary_path.read_text()) if summary_path.exists() else {"runs": {}}
        todo = [k for k in keys if a.force or not summary["runs"].get(k, {}).get("reached_last_step")]
        if not todo:
            log.info("kind %s: every run already complete", kind)
            continue

        torch._dynamo.reset()  # a fresh compile per kind; no recompile limit shared across simulators
        ov = overrides(grid, steps, reynolds * factor, collision, str(out / "_kinet_data_root"), a.device)
        run = compose_run_config(ov)
        t_build = time.time()
        simulator = kinet.build_simulator(run, logger=log, process_config=single_process_config(device=a.device),
                                          compile=bool(run.launch.compile))
        simulator.eval()
        solver = kinetic_solver_of(simulator)
        dev, dt = solver.lattice.velocities.device, torch.float64
        (out / "composed_config.json").write_text(json.dumps(simulate_save_config(run), indent=1, default=str))
        summary.update({"reynolds_reference": reynolds, "reynolds": reynolds * factor, "reynolds_factor": factor,
                        "grid": grid, "collision": collision, "steps": steps, "save_every_n": SAVE_EVERY[grid],
                        "overrides": ov, "kinet_commit": kinet_commit, "device": device_name,
                        "build_s": round(time.time() - t_build, 2)})

        for key in todo:
            ref_path = f"{DATA}/sys_Re-{a.re}_Ma-1en1/{key}.h5"
            rho, u = start_fields(ref_path, grid)

            def macros(x, y, rho=rho, u=u):
                return {"density": torch.as_tensor(rho, dtype=dt, device=dev),
                        "velocity": torch.as_tensor(np.moveaxis(u, 0, -1).copy(), dtype=dt, device=dev),
                        "temperature": 1.0 / 3.0}  # weakly compressible: T = c_s^2 = 1/3 (lattice units)

            run_dir = out / key
            if run_dir.exists():
                shutil.rmtree(run_dir)
            run_dir.mkdir(parents=True)
            h5 = run_dir / "rollout.h5"
            control = RolloutControl(pred_length=steps, save_results=True, record_forecast=True,
                                     save_dir=str(run_dir), save_config=simulate_save_config(run),
                                     output_path=str(h5), rollout_total_pred_length=steps,
                                     record_policy=type(solver).default_record_policy(simulator.context))
            error = None
            t0 = time.time()
            try:
                fields = initial_state(simulator, run, macros)
                with torch.no_grad():
                    simulator(fields, control=control)
            except Exception as exc:  # BGK blow-up or any other abort: record it and go on
                error = f"{type(exc).__name__}: {exc}"
                log.error("%s/%s failed:\n%s", kind, key, traceback.format_exc())
            wall = time.time() - t0
            stats = solver.rollout_stats
            ckpt = run_dir / "sim_checkpoints"
            if ckpt.exists():
                shutil.rmtree(ckpt)
            rec = {"reference": ref_path, "kind": kind, "grid": grid, "reynolds": reynolds * factor,
                   "collision": collision, "steps": steps, "save_every_n": SAVE_EVERY[grid],
                   "stop_reason": getattr(stats, "stop_reason", None),
                   "accepted_steps": getattr(stats, "accepted_steps", None), "error": error,
                   "rollout_wall_s": round(wall, 2), "path": str(h5)}
            if h5.exists():
                with h5py.File(h5, "r+") as f:
                    s = f["time/time"][:]
                    finite = s[np.isfinite(s)]
                    ic_rho = f["initial_conditions/observables/density"][0, 0, 0]
                    ic_u = f["initial_conditions/observables/velocity"][0, :, 0]
                    rec.update({"kinet_rollout_status": str(f.attrs.get("kinet_rollout_status")),
                                "last_saved_step": int(finite[-1]) if finite.size else None,
                                "saved_frames": int(finite.size),
                                "ic_max_abs_density_diff": float(np.abs(ic_rho - rho).max()),
                                "ic_max_abs_velocity_diff": float(np.abs(ic_u - u).max())})
                    f.attrs.update({"candidate_reference_file": ref_path, "candidate_reference_key": key,
                                    "candidate_kind": kind, "candidate_grid": grid,
                                    "candidate_reynolds": reynolds * factor, "candidate_collision": collision,
                                    "candidate_start": "reference frame 0 (step 0), block-averaged to the grid; F = Feq",
                                    "candidate_driver": os.path.abspath(__file__)})
                rec["bytes"] = h5.stat().st_size
            rec["reached_last_step"] = bool(error is None and rec.get("stop_reason") == "completed"
                                            and rec.get("kinet_rollout_status") == "complete"
                                            and rec.get("last_saved_step") == steps)
            if max(rec.get("ic_max_abs_velocity_diff", 0.0), rec.get("ic_max_abs_density_diff", 0.0)) > 1e-12:
                rec["reached_last_step"] = False
                rec["error"] = (rec["error"] or "") + " stored initial condition differs from the macros handed in"
            failures += not rec["reached_last_step"]
            summary["runs"][key] = rec
            log.info("RUN %s", json.dumps(rec))
            summary_path.write_text(json.dumps(summary, indent=1))
        del simulator, solver
        gc.collect()
        torch.cuda.empty_cache() if a.device == "cuda" else None
    if failures:
        log.error("%d run(s) did not reach their last step", failures)
        sys.exit(3)


if __name__ == "__main__":
    main()
