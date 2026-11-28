"""Functional check of the drag and the forcing shell as a composed run wires them (step 22).

Research-grade (kept with the provenance of the forced-turbulence runs). Solver code only;
nothing here trains or runs a machine-learning model.

Composes the forced case on a small grid (CPU), builds the simulator, takes the two terms of
the ``sum`` forcing law that the solver holds, evaluates each on a random divergence-free
velocity with unit density, and checks:

1. ``random_modes`` with ``minimum_mode``: the acceleration's Fourier content lies only on
   integer shells minimum_mode <= |n| <= maximum_mode (fraction outside printed), and the
   selected mode list equals the analytic count of half-plane integer vectors in the shell.
2. ``linear`` with a negative rate: the force equals rate * rho * (u - <u>) to round-off, so
   its power <u . F> is negative (energy removed) and its net momentum is zero.

Usage: python functional_check.py N MIN_MODE MAX_MODE RATE   (e.g. 128 7 9 -1e-3)
"""

from __future__ import annotations

import itertools
import math
import sys

import numpy as np
import torch

import kinet
from kinet.logging import KinetProcessLog
from kinet.runtime.distributed.process import single_process_config
from kinet.runtime.hydra.compose import compose_run_config
from kinet.simulation.access import kinetic_solver_of


def main() -> None:
    """Build the simulator, evaluate the two forcing terms, print and assert the checks."""
    n, lo, hi, rate = int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    forcing = (f"{{type: sum, terms: [{{type: random_modes, seed: 1729, correlation_time: 10.0, "
               f"variance: 1.0e-8, minimum_mode: {lo}, maximum_mode: {hi}}}, "
               f"{{type: linear, rate: {rate}, rate_policy: constant}}]}}")
    run = compose_run_config([
        "case=homogeneous_isotropic_turbulence/Re-2700_Ma-1en1_forced_drag_2d", "task=simulate",
        f"++case.discretization.spatial.grid=[{n},{n}]", "++case.discretization.temporal.grid=10",
        f"++case.physics.forcing_term={forcing}", "++launch.device=cpu", "++launch.compile=false",
        "++paths.data_root=/pscratch/sd/k/khegazy/kinet_datasets/_work/forced_turbulence/functional/data",
    ])
    simulator = kinet.build_simulator(run, logger=KinetProcessLog.null("check"),
                                      process_config=single_process_config(device="cpu"), compile=False)
    sum_law = kinetic_solver_of(simulator).forcing_term
    shell_law, drag_law = sum_law.laws
    print("kinet", kinet.__file__, "| terms:", type(shell_law).__name__, type(drag_law).__name__)

    # A random solenoidal velocity from a random stream function; density 1.
    rng = np.random.default_rng(0)
    k = 2 * math.pi * np.fft.fftfreq(n)
    psi_hat = np.fft.fft2(rng.standard_normal((n, n)))
    u = np.stack([np.fft.ifft2(1j * k[None, :] * psi_hat).real, np.fft.ifft2(-1j * k[:, None] * psi_hat).real])
    u = 0.05 * u / np.sqrt((u**2).sum(axis=0).mean()) + 0.01  # nonzero mean to test the fluctuation
    obs = {"density": torch.ones(1, 1, n, n, dtype=torch.float64),
           "velocity": torch.as_tensor(u[None], dtype=torch.float64)}

    accel = shell_law.calculate_sources(obs, dt=0.0, step=0, state=None)[0]["momentum"][0].numpy()
    power = (np.abs(np.fft.fft2(accel, axes=(-2, -1))) ** 2).sum(axis=0)
    index = np.fft.fftfreq(n, d=1.0 / n)
    radius = np.hypot(index[:, None], index[None, :])
    inside = (radius >= lo - 1e-9) & (radius <= hi + 1e-9)
    outside_fraction = float(power[~inside].sum() / power.sum())
    expected = sum(1 for m in itertools.product(range(-int(hi), int(hi) + 1), repeat=2)
                   if next((v for v in m if v), 0) > 0 and lo <= math.hypot(*m) <= hi)
    print(f"shell: modes selected {shell_law.mode_indices.shape[0]}, expected {expected}; "
          f"radii {shell_law.mode_indices.double().norm(dim=1).min():.4f}..{shell_law.mode_indices.double().norm(dim=1).max():.4f}; "
          f"power fraction outside {lo} <= |n| <= {hi}: {outside_fraction:.3e}")

    force = drag_law.calculate_sources(obs, dt=1.0, step=0, state=None)[0]["momentum"][0].numpy()
    fluct = u - u.mean(axis=(1, 2), keepdims=True)
    err = float(np.abs(force - rate * fluct).max() / np.abs(rate * fluct).max())
    print(f"drag: max |F - rate (u - <u>)| / max |rate (u - <u>)| = {err:.3e}; "
          f"<u . F> = {(u * force).sum(axis=0).mean():.4e} (negative removes energy); "
          f"net momentum {np.abs(force.sum(axis=(1, 2))).max():.3e}")
    ok = shell_law.mode_indices.shape[0] == expected and outside_fraction < 1e-20 and err < 1e-12 \
        and (u * force).sum(axis=0).mean() < 0
    print("FUNCTIONAL CHECK", "PASSED" if ok else "FAILED")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
