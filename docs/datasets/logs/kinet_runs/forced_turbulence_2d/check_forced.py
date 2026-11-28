"""Check a forced 2D kinet rollout for stationarity, spectra and scales (BUILD_ORDER step 22).

Research-grade (kept with the provenance of the forced-turbulence runs). Solver output only;
nothing here trains or runs a machine-learning model.

Reads one grouped rollout.h5 frame by frame (never the whole file) and writes a plain-text
report and two figures next to the path given by --out:

1. Time series per saved frame: kinetic energy E = <|u - <u>|^2>/2, enstrophy
   Z = <omega^2>/2 (omega from a spectral curl of the stored velocity), rms speed u', max |u|,
   density range, the energy in the lowest shells |n| < 3 (the condensate check), the drag
   dissipation eps_alpha = 2 alpha E and the viscous dissipation eps_nu = 2 nu Z
   (incompressible periodic identity, accurate up to O(Ma^2)).
2. The shell-summed energy spectrum E(n) on integer shells of the Fourier index n, averaged
   over the frames after --t-start, with least-squares log-log slopes over the inverse
   range [--inv-lo, --inv-hi] and the direct range [--dir-lo, --dir-hi], compared with the
   dual-cascade expectation -5/3 and -3 (Boffetta and Ecke 2012, Annu. Rev. Fluid Mech. 44,
   427, Eqs. 12-13; Boffetta and Musacchio 2010, Phys. Rev. E 82, 016307, Table I reports
   the direct-range exponent steeper than -3 by delta = 1.8 at 2048^2 with friction).
3. Correlation times over the frames after --t-start: the integral time of the
   autocorrelation of E(t) and of the velocity field itself, rho(lag) = <u(t) . u(t + lag)> /
   <|u|^2> (both integrated to their first zero crossing), which say how many saved frames
   are nearly independent.
4. Scales in cells: the integral scale L = 2 pi sum E(n)/k / sum E(n) with k = 2 pi n / N,
   the large-eddy time T_L = L / u', the arrest scale u'/alpha (spec 04, Option B, item 3),
   and the energy relaxation time 1/(2 alpha).

Usage:
    python check_forced.py ROLLOUT.h5 --alpha 2.26e-4 --nu 0.0219 --out PREFIX \
        [--t-start 20000] [--every 1]
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np


def shell_spectrum(u: np.ndarray) -> np.ndarray:
    """Energy per integer shell of the Fourier index, E(n) = sum_{|n| in shell} |u_hat|^2 / 2.

    Args:
        u: Velocity of shape (2, N, N) on a periodic grid.

    Returns:
        E(n) for n = 0 .. N/2, normalised so that sum_n E(n) = <|u|^2>/2 (Parseval).
    """
    n_cells = u.shape[-1]
    u_hat = np.fft.fft2(u, axes=(-2, -1)) / (n_cells * n_cells)
    density = 0.5 * (np.abs(u_hat) ** 2).sum(axis=0)
    index = np.fft.fftfreq(n_cells, d=1.0 / n_cells)
    radius = np.rint(np.hypot(index[:, None], index[None, :])).astype(int)
    return np.bincount(radius.ravel(), weights=density.ravel(), minlength=n_cells)[: n_cells // 2 + 1]


def spectral_vorticity(u: np.ndarray) -> np.ndarray:
    """omega = d u_y / dx - d u_x / dy, axis 0 = x, spectral derivative on a unit cell grid."""
    n_cells = u.shape[-1]
    k = 2 * math.pi * np.fft.fftfreq(n_cells)
    ux_hat, uy_hat = np.fft.fft2(u[0]), np.fft.fft2(u[1])
    return np.fft.ifft2(1j * k[:, None] * uy_hat - 1j * k[None, :] * ux_hat).real


def slope(n: np.ndarray, e: np.ndarray, lo: int, hi: int) -> float:
    """Least-squares slope of log E against log n over lo <= n <= hi."""
    sel = (n >= lo) & (n <= hi) & (e > 0)
    return float(np.polyfit(np.log(n[sel]), np.log(e[sel]), 1)[0])


def field_correlation(fields: list[np.ndarray], lag: int) -> float:
    """<u(t) . u(t + lag)> / <|u|^2> averaged over all frame pairs at that lag."""
    num = np.mean([(fields[i] * fields[i + lag]).sum(axis=0).mean() for i in range(len(fields) - lag)])
    den = np.mean([(f**2).sum(axis=0).mean() for f in fields])
    return float(num / den)


def integral_time(series: list, spacing: float) -> float:
    """Integral of the autocorrelation to its first zero crossing, times the frame spacing.

    ``series`` is either scalars (autocorrelation of their fluctuation) or velocity fields
    (``field_correlation``). Returns inf when the correlation never crosses zero.
    """
    if isinstance(series[0], np.ndarray):
        rho = [field_correlation(series, m) for m in range(len(series) // 2)]
    else:
        x = np.asarray(series) - np.mean(series)
        rho = [float((x[: len(x) - m] * x[m:]).mean() / (x * x).mean()) for m in range(len(x) // 2)]
    total = 0.5
    for value in rho[1:]:
        if value <= 0:
            return total * spacing
        total += value
    return math.inf


def main() -> None:
    """Parse arguments, read the rollout frame by frame, write the report and figures."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("rollout", type=Path)
    p.add_argument("--alpha", type=float, required=True, help="drag rate, positive")
    p.add_argument("--nu", type=float, required=True, help="lattice kinematic viscosity")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--t-start", type=float, default=0.0, help="first step of the spectrum average")
    p.add_argument("--every", type=int, default=1, help="read every Nth saved frame")
    p.add_argument("--inv-lo", type=int, default=4)
    p.add_argument("--inv-hi", type=int, default=20)
    p.add_argument("--dir-lo", type=int, default=45)
    p.add_argument("--dir-hi", type=int, default=150)
    a = p.parse_args()
    if a.alpha <= 0 or a.nu <= 0 or a.every < 1:
        raise SystemExit("--alpha and --nu must be positive and --every at least 1")

    with h5py.File(a.rollout, "r") as f:
        steps_all = f["time/time"][:]
        slots = np.flatnonzero(np.isfinite(steps_all))[:: a.every]
        status = {k: (v.decode() if isinstance(v, bytes) else (v.item() if hasattr(v, "item") else v))
                  for k, v in f.attrs.items()
                  if k in ("kinet_rollout_status", "kinet_last_completed_step", "kinet_rollout_total_pred_length")}
        vel, rho = f["observables/velocity"], f["observables/density"]
        n_cells = vel.shape[-1]
        if vel.shape[-2] != n_cells:
            raise SystemExit("square grids only")
        n_index = np.arange(n_cells // 2 + 1)
        low = n_index < 3
        rows, spec_sum, spec_count, fields = [], np.zeros(n_cells // 2 + 1), 0, []
        for s in slots:
            u = vel[0, :, s]
            u = u - u.mean(axis=(1, 2), keepdims=True)
            r = rho[0, 0, s]
            if not (np.isfinite(u).all() and np.isfinite(r).all()):
                rows.append({"step": float(steps_all[s]), "finite": False})
                break
            e_n = shell_spectrum(u)
            energy = 0.5 * float((u**2).sum(axis=0).mean())
            omega = spectral_vorticity(u)
            enstrophy = 0.5 * float((omega**2).mean())
            rows.append({
                "step": float(steps_all[s]), "finite": True, "E": energy, "Z": enstrophy,
                "u_rms": math.sqrt(2 * energy), "u_max": float(np.sqrt((u**2).sum(axis=0)).max()),
                "rho_min": float(r.min()), "rho_max": float(r.max()),
                "E_low_shells": float(e_n[low].sum()),
                "eps_alpha": 2 * a.alpha * energy, "eps_nu": 2 * a.nu * enstrophy,
            })
            if steps_all[s] >= a.t_start:
                spec_sum += e_n
                spec_count += 1
                fields.append(u[:, ::4, ::4].copy())  # every 4th cell: enough for a large-scale correlation

    lines = [f"rollout: {a.rollout}", f"attributes: {json.dumps(status)}",
             f"grid: {n_cells}^2; frames read: {len(rows)} (every {a.every} saved frame)",
             f"alpha = {a.alpha:.6g} per step, nu = {a.nu:.6g} cells^2 per step", "",
             "step E Z u_rms u_max rho_min rho_max E_low(|n|<3) eps_alpha eps_nu"]
    for r in rows:
        if not r["finite"]:
            lines.append(f"{r['step']:.0f} NON-FINITE FIELD: run blew up here")
            continue
        lines.append(f"{r['step']:.0f} {r['E']:.5e} {r['Z']:.5e} {r['u_rms']:.5e} {r['u_max']:.4e} "
                     f"{r['rho_min']:.5f} {r['rho_max']:.5f} {r['E_low_shells']:.4e} "
                     f"{r['eps_alpha']:.4e} {r['eps_nu']:.4e}")
    good = [r for r in rows if r["finite"]]
    late = [r for r in good if r["step"] >= a.t_start]
    if late and spec_count:
        spec = spec_sum / spec_count
        k = 2 * math.pi * n_index[1:] / n_cells
        e_mean = float(np.mean([r["E"] for r in late]))
        u_rms = math.sqrt(2 * e_mean)
        integral = 2 * math.pi * float((spec[1:] / k).sum() / spec[1:].sum())
        half = len(late) // 2
        first, second = late[:half] or late, late[half:]
        lines += ["", f"averages over steps >= {a.t_start:.0f} ({len(late)} frames, spectrum over {spec_count}):",
                  f"  E mean {e_mean:.5e}; first half {np.mean([r['E'] for r in first]):.5e}, "
                  f"second half {np.mean([r['E'] for r in second]):.5e}; std/mean {np.std([r['E'] for r in late]) / e_mean:.3f}",
                  f"  Z mean {np.mean([r['Z'] for r in late]):.5e}; first half {np.mean([r['Z'] for r in first]):.5e}, "
                  f"second half {np.mean([r['Z'] for r in second]):.5e}",
                  f"  u_rms {u_rms:.5e} (Mach on c_s = 1/sqrt(3): {u_rms * math.sqrt(3):.4f}); max |u| seen {max(r['u_max'] for r in late):.4e}",
                  f"  density range seen [{min(r['rho_min'] for r in late):.5f}, {max(r['rho_max'] for r in late):.5f}]",
                  f"  eps_alpha mean {np.mean([r['eps_alpha'] for r in late]):.4e}; eps_nu mean {np.mean([r['eps_nu'] for r in late]):.4e}; "
                  f"injection eps_I = eps_alpha + eps_nu (stationary) {np.mean([r['eps_alpha'] + r['eps_nu'] for r in late]):.4e}; "
                  f"eps_alpha/eps_I {np.mean([r['eps_alpha'] for r in late]) / np.mean([r['eps_alpha'] + r['eps_nu'] for r in late]):.3f}",
                  f"  energy in |n| < 3: mean fraction {np.mean([r['E_low_shells'] / r['E'] for r in late]):.4f}; "
                  f"first half {np.mean([r['E_low_shells'] for r in first]):.4e}, second half {np.mean([r['E_low_shells'] for r in second]):.4e}",
                  f"  spectrum peak at shell n = {int(np.argmax(spec[1:]) + 1)}",
                  f"  integral scale L = {integral:.1f} cells; arrest scale u'/alpha = {u_rms / a.alpha:.1f} cells",
                  f"  large-eddy time T_L = L/u' = {integral / u_rms:.0f} steps; energy relaxation 1/(2 alpha) = {1 / (2 * a.alpha):.0f} steps",
                  f"  slope over inverse range n in [{a.inv_lo}, {a.inv_hi}]: {slope(n_index, spec, a.inv_lo, a.inv_hi):.3f} (expected -5/3 = -1.667)",
                  f"  slope over direct range n in [{a.dir_lo}, {a.dir_hi}]: {slope(n_index, spec, a.dir_lo, a.dir_hi):.3f} (expected -3, steeper with friction)",
                  f"  correlation time of E(t): {integral_time([r['E'] for r in late], late[1]['step'] - late[0]['step'] if len(late) > 1 else 0):.0f} steps; "
                  f"of the velocity field: {integral_time(fields, late[1]['step'] - late[0]['step'] if len(late) > 1 else 0):.0f} steps "
                  "(integral of the autocorrelation to its first zero crossing; inf if it does not cross)",
                  f"  velocity-field autocorrelation at lags of 1, 2, 4, 8, 16, 32 frames: "
                  + ", ".join(f"{field_correlation(fields, m):.3f}" for m in (1, 2, 4, 8, 16, 32) if m < len(fields)),
                  "", "shell spectrum E(n), mean over the window (n E):"]
        lines += [f"  {n} {spec[n]:.5e}" for n in n_index[1:] if n <= 64 or n % 16 == 0]
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        ax[0].loglog(n_index[1:], spec[1:], label="E(n)")
        for lo, hi, pw, lab in ((a.inv_lo, a.inv_hi, -5 / 3, "n^-5/3"), (a.dir_lo, a.dir_hi, -3, "n^-3")):
            nn = np.arange(lo, hi + 1)
            ax[0].loglog(nn, spec[lo] * (nn / lo) ** pw, "--", label=lab)
        ax[0].set_xlabel("shell n"); ax[0].set_ylabel("E(n)"); ax[0].legend()
        ax[1].loglog(n_index[1:], spec[1:] * n_index[1:] ** (5 / 3), label="n^(5/3) E(n)")
        ax[1].loglog(n_index[1:], spec[1:] * n_index[1:] ** 3.0, label="n^3 E(n)")
        ax[1].set_xlabel("shell n"); ax[1].set_ylabel("compensated"); ax[1].legend()
        fig.tight_layout()
        fig.savefig(Path(str(a.out) + ".spectrum.png"), dpi=110)
        plt.close(fig)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    st = [r["step"] for r in good]
    ax[0].plot(st, [r["E"] for r in good]); ax[0].set_xlabel("step"); ax[0].set_ylabel("E")
    ax[1].plot(st, [r["Z"] for r in good]); ax[1].set_xlabel("step"); ax[1].set_ylabel("Z")
    fig.tight_layout(); fig.savefig(Path(str(a.out) + ".timeseries.png"), dpi=110)
    plt.close(fig)
    Path(str(a.out) + ".txt").write_text("\n".join(lines) + "\n")
    cut = next((i for i, line in enumerate(lines) if line.startswith("shell spectrum")), len(lines))
    print("\n".join(lines[:cut]))


if __name__ == "__main__":
    main()
