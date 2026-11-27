"""Run a perturbed-initial-condition ensemble of the kinet Re 5e4 shear layer from one stored frame.

Research-grade (kept for reproducing BUILD_ORDER.md step 21; dataset_specs/01_physical_ensemble.md,
Option B). Solver simulations only; nothing here trains or runs a machine-learning model.

What it does, in one Python process so start-up and torch.compile are paid once:

1. Read the reference frame of `kinet_re5e4` (`dc804f`, old flat layout) at solver step S:
   density rho, velocity u and the populations F (post-streaming state after step S).
2. Reorder F from the old file's D2Q9 velocity order to the current kinet lattice order. The
   old order is the one for which sum_i c_i F_i reproduces the stored rho*u; the driver checks
   that the reordered moments match the stored velocity and that kinet's own equilibrium of the
   stored macros matches the stored Feq, and refuses to run otherwise.
3. For each member draw a seeded, solenoidal, band-limited velocity perturbation du: the curl
   of a random stream function psi whose Fourier coefficients are white noise divided by |k| on
   the integer-wavenumber shell 1 <= |k| <= kmax (so du's coefficients are white Gaussian
   vectors projected perpendicular to k, spec 01, Sect. 5.1), rescaled to
   rms(du) = amplitude * u_rms, with u_rms = sqrt(<|u - <u>|^2>) of the start frame.
4. Enter it keeping the stored non-equilibrium part (spec 01, Sect. 5.1, route (i)):
       F_member = F + Feq(rho, u + du) - Feq(rho, u),
   with Feq kinet's own (entropic) equilibrium of the composed run.
5. Step it with kinet's library route (build_simulator -> initial_state -> simulator(...),
   00_how_to_use_kinet.md, Section 6a) and write a normal grouped rollout file of macroscopic
   observables (io.record_distributions=false, io.record_equilibria=false).
6. Refuse a run that did not reach its last step; delete any simulation checkpoint; stamp the
   provenance of the member (start step, seed, amplitude, reference file) as root attributes.

Usage (from a working directory on scratch, KINET_PROJECT set; see env.sh):
    python ensemble_driver.py --start 2000 --members 0-16 --amplitude 1e-3 --steps 5000 \
        --save-every 10 --out /pscratch/.../shear_layer_ensemble [--extra 0:1e-2] [--control 100]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
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

REFERENCE = ("/global/cfs/cdirs/m4790/Data/kinet/doubly_periodic/weakly_compressible_isoT_fluids/"
             "sys_Re-5e4_Ma-1en1/D2Q9_shape-256-256_T-10000_H-dc804f.h5")
# D2Q9 order of the old flat file, found from its data: least squares of rho*u on F gives these
# c_i exactly (residual 1e-29), and streaming F_collided with them reproduces F bit for bit.
OLD_D2Q9 = np.array([[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1], [1, 1], [-1, 1], [-1, -1], [1, -1]])
SEED_BASE = 20261127  # the date the jobs were approved; seeds are SeedSequence([SEED_BASE, start, member])


def overrides(grid: int, steps: int, save_every: int, data_root: str, device: str) -> list[str]:
    """Hydra overrides that give the physics of the archived dc804f run on the current kinet.

    From docs/datasets/logs/kinet_runs/README.md (`kinet_re5e4`): the shipped shear-layer case
    at 256^2 with Re 5e4 and `use_static_weights=false` as the old run had; macroscopic
    observables only (BUILD_ORDER.md, "How kinet runs are configured").
    """
    return [
        "case=doubly_periodic/shear_layer",
        f"++case.discretization.spatial.grid=[{grid},{grid}]",
        f"++case.discretization.temporal.grid={steps}",
        "++case.physics.parameters.reynolds=50000",
        "++case.lattice.use_static_weights=false",
        f"++io.save_every_n={save_every}",
        "++io.record_distributions=false",
        "++io.record_equilibria=false",
        f"++launch.device={device}",
        f"++launch.compile={'true' if device == 'cuda' else 'false'}",
        "task=simulate",
        f"++paths.data_root={data_root}",
    ]


def solenoidal_perturbation(n: int, kmax: float, seed: list[int], target_rms: float
                            ) -> tuple[np.ndarray, dict]:
    """Return du (2, n, n), the spectral curl of a random band-limited stream function.

    psi_hat = xi / |k| on 1 <= |k| <= kmax (integer mode numbers), xi the FFT of real white
    noise, so psi is real; du_x = d psi/dy, du_y = -d psi/dx (axis 0 is x, as in kinet's
    velocity channel 0). The result is rescaled to rms sqrt(<du_x^2 + du_y^2>) = target_rms.
    """
    rng = np.random.default_rng(np.random.SeedSequence(seed))
    m = np.fft.fftfreq(n, d=1.0 / n)                      # integer mode numbers
    kx, ky = np.meshgrid(m, m, indexing="ij")
    kmag = np.hypot(kx, ky)
    band = (kmag >= 1.0) & (kmag <= kmax)
    psi_hat = np.where(band, np.fft.fft2(rng.standard_normal((n, n))) / np.where(band, kmag, 1.0), 0.0)
    du_hat = np.stack([1j * ky * psi_hat, -1j * kx * psi_hat])
    du = np.fft.ifft2(du_hat).real
    du *= target_rms / np.sqrt(np.mean(np.sum(du**2, axis=0)))
    # Checks at the boundary: rms, spectral divergence, energy outside the band.
    dh = np.fft.fft2(du)
    div = np.fft.ifft2(1j * kx * dh[0] + 1j * ky * dh[1]).real
    vort = np.fft.ifft2(1j * kx * dh[1] - 1j * ky * dh[0]).real
    e = np.sum(np.abs(dh) ** 2, axis=0)
    checks = {
        "rms": float(np.sqrt(np.mean(np.sum(du**2, axis=0)))),
        "spectral_divergence_over_vorticity": float(np.abs(div).max() / np.abs(vort).max()),
        "energy_fraction_outside_band": float(e[~band].sum() / e.sum()),
    }
    if abs(checks["rms"] / target_rms - 1.0) > 1e-12 or checks["spectral_divergence_over_vorticity"] > 1e-12:
        raise RuntimeError(f"perturbation failed its checks: {checks}")
    return du, checks


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--start", type=int, required=True, help="solver step of the reference to start from")
    p.add_argument("--members", default="0-16", help="member indices, 'a-b', 'a,b,c' or 'none'")
    p.add_argument("--amplitude", type=float, default=1e-3, help="rms(du) / u_rms of the start frame")
    p.add_argument("--extra", action="append", default=[], help="'member:amplitude', a run with that member's seed at another amplitude")
    p.add_argument("--control", type=int, default=0, help="also run du = 0 for this many steps (validation)")
    p.add_argument("--steps", type=int, default=5000)
    p.add_argument("--save-every", type=int, default=10)
    p.add_argument("--kmax", type=float, default=16.0)
    p.add_argument("--out", required=True)
    p.add_argument("--device", default="cuda")
    a = p.parse_args()

    members = ([] if a.members == "none" else
               list(range(int(a.members.split("-")[0]), int(a.members.split("-")[1]) + 1))
               if "-" in a.members else [int(x) for x in a.members.split(",")])
    runs = [(f"member_{i:02d}_amp{a.amplitude:.0e}", i, a.amplitude, a.steps) for i in members]
    runs += [(f"member_{int(e.split(':')[0]):02d}_amp{float(e.split(':')[1]):.0e}", int(e.split(":")[0]),
              float(e.split(":")[1]), a.steps) for e in a.extra]
    if a.control:
        runs.insert(0, ("control_amp0", -1, 0.0, a.control))
    out = Path(a.out) / f"start_{a.start:05d}"
    out.mkdir(parents=True, exist_ok=True)
    log = KinetProcessLog("ensemble")

    with h5py.File(REFERENCE, "r") as f:
        if int(f["time_index"][a.start]) != a.start:
            raise RuntimeError("reference frame index is not the solver step")
        rho = f["density"][0, 0, a.start]
        u = f["velocity"][0, :, a.start]
        F_old = f["F"][0, :, a.start]
        Feq_old = f["Feq"][0, :, a.start]
    n = rho.shape[0]
    u_rms = float(np.sqrt(np.mean(np.sum((u - u.mean(axis=(1, 2), keepdims=True)) ** 2, axis=0))))

    run = compose_run_config(overrides(n, max(r[3] for r in runs), a.save_every, str(out / "_kinet_data_root"), a.device))
    simulator = kinet.build_simulator(run, logger=log, process_config=single_process_config(device=a.device),
                                      compile=bool(run.launch.compile))
    simulator.eval()
    solver = kinetic_solver_of(simulator)
    c_new = solver.lattice.velocities.cpu().numpy().astype(int)
    perm = [int(np.where((OLD_D2Q9 == c_new[j]).all(axis=1))[0][0]) for j in range(len(c_new))]
    F = F_old[perm]
    dev, dt = solver.lattice.velocities.device, torch.float64

    def carrier(vel: np.ndarray):
        """kinet's initial carrier painted with (rho, vel) and kinet's equilibrium of it."""
        def macros(x, y):
            return {"density": torch.as_tensor(rho, dtype=dt, device=dev),
                    "velocity": torch.as_tensor(np.moveaxis(vel, 0, -1).copy(), dtype=dt, device=dev),
                    "temperature": 1.0 / 3.0}  # weakly compressible: T = c_s^2 = 1/3 (lattice units)
        fields = initial_state(simulator, run, macros)
        solver.compute_equilibrium_distributions(fields)
        return fields, fields.dists.pop("Feq")[0].cpu().numpy()

    _, Feq_base = carrier(u)
    consistency = {
        "permutation_old_to_new": perm,
        "max_abs_u_minus_moment_of_reordered_F": float(np.abs(np.einsum("qd,qxy->dxy", c_new, F) / F.sum(0) - u).max()),
        "max_abs_kinet_Feq_minus_stored_Feq": float(np.abs(Feq_base - Feq_old[perm]).max()),
    }
    log.info("reference consistency: %s", consistency)
    if consistency["max_abs_u_minus_moment_of_reordered_F"] > 1e-13 or consistency["max_abs_kinet_Feq_minus_stored_Feq"] > 1e-13:
        raise RuntimeError(f"stored populations are not consistent with this kinet: {consistency}")

    kinet_commit = subprocess.run(["git", "-C", os.environ["KINET_PROJECT"], "rev-parse", "HEAD"],
                                  capture_output=True, text=True, check=True).stdout.strip()
    (out / "composed_config.json").write_text(json.dumps(simulate_save_config(run), indent=1, default=str))
    summary = {"start_step": a.start, "reference": REFERENCE, "u_rms": u_rms, "kmax": a.kmax,
               "save_every_n": a.save_every, "kinet_commit": kinet_commit, "consistency": consistency,
               "device": torch.cuda.get_device_name() if a.device == "cuda" else "cpu", "runs": []}

    for name, member, amp, steps in runs:
        seed = [SEED_BASE, a.start, member]
        if amp > 0:
            du, checks = solenoidal_perturbation(n, a.kmax, seed, amp * u_rms)
        else:
            du, checks = np.zeros_like(u), {"rms": 0.0}
        fields, Feq_pert = carrier(u + du)
        F_member = F + Feq_pert - Feq_base
        mom_err = float(np.abs(np.einsum("qd,qxy->dxy", c_new, F_member) / F_member.sum(0) - (u + du)).max())
        rho_err = float(np.abs(F_member.sum(0) - rho).max())
        if mom_err > 1e-13 or rho_err > 1e-13:
            raise RuntimeError(f"{name}: perturbed populations do not carry (rho, u + du): {mom_err}, {rho_err}")
        fields.dists["F"] = torch.as_tensor(F_member[None], dtype=dt, device=dev)
        run_dir = out / name
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True)
        h5 = run_dir / "rollout.h5"
        control = RolloutControl(pred_length=steps, save_results=True, record_forecast=True,
                                 save_dir=str(run_dir), save_config=simulate_save_config(run),
                                 output_path=str(h5), rollout_total_pred_length=steps,
                                 record_policy=type(solver).default_record_policy(simulator.context))
        t0 = time.time()
        with torch.no_grad():
            simulator(fields, control=control)
        wall = time.time() - t0
        stats = solver.rollout_stats
        ckpt = run_dir / "sim_checkpoints"
        if ckpt.exists():
            shutil.rmtree(ckpt)
        with h5py.File(h5, "r+") as f:
            s = f["time/time"][:]
            last = int(s[np.isfinite(s)][-1])
            status = str(f.attrs["kinet_rollout_status"])
            f.attrs.update({"ensemble_reference_file": REFERENCE, "ensemble_start_step": a.start,
                            "ensemble_member": member, "ensemble_seed": json.dumps(seed),
                            "ensemble_amplitude_over_u_rms": amp, "ensemble_start_u_rms": u_rms,
                            "ensemble_kmax": a.kmax, "ensemble_driver": os.path.abspath(__file__)})
        ok = stats.stop_reason == "completed" and status == "complete" and last == steps
        rec = {"name": name, "member": member, "seed": seed, "amplitude": amp, "steps": steps,
               "stop_reason": stats.stop_reason, "accepted_steps": stats.accepted_steps,
               "kinet_rollout_status": status, "last_saved_step": last, "reached_last_step": ok,
               "rollout_wall_s": round(wall, 2), "path": str(h5), "bytes": h5.stat().st_size,
               "perturbation_checks": checks, "momentum_err": mom_err, "density_err": rho_err}
        summary["runs"].append(rec)
        log.info("RUN %s", json.dumps(rec))
        (out / "summary.json").write_text(json.dumps(summary, indent=1))
        if not ok:
            raise RuntimeError(f"{name} did not reach its last step: {rec}")


if __name__ == "__main__":
    sys.exit(main())
