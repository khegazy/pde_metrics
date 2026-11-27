"""Checks on the perturbed-initial-condition ensemble of the kinet shear layer (BUILD_ORDER.md step 21).

Research-grade. Reads the rollouts that ensemble_driver.py wrote and the reference `dc804f`
(read-only); writes JSON and text tables and one figure. Solver output only; no ML model.

Subcommands
  config    compare the composed kinet config with the archived dc804f config, key by key
  validate  2a: du = 0 continuation against the reference frames; 2b: the perturbation of every
            member (divergence under three discrete operators, rms, band); 2c: two members
            with different seeds at lead 0 and their difference along the lead axis
  ensemble  4: spread, leave-one-out error of the ensemble mean against the variance of the
            other N = 16 members (Leutbecher & Palmer 2007, ECMWF Tech. Memo. 514, Eq. 6:
            E e^2 = (N + 1)/N sigma^2 when the truth is exchangeable with the members), the
            scale-by-scale decorrelation, the spread map, and the amplitude check. Pooled over
            all N + 1 choices of truth, that ratio equals (N + 1)/N identically in every cell
            (an algebraic identity, shown in the text output), so the check that remains is the
            range of the ratio over single truths. A ratio binned by the per-cell variance of
            the other N is not used: with N = 16 that variance is too noisy (relative standard
            deviation sqrt(2/(N-1)) = 0.37) and the binning alone tilts the ratio.

Conventions
  * spread(field) = sqrt(mean over cells (and velocity components) of the member variance),
    variance with ddof = 1 so that its expectation is sigma^2 and the expected ratio of mean
    squared error to mean variance is (N + 1)/N (with ddof = 0 it would be (N + 1)/(N - 1)).
  * Leads are solver steps since the start: 0 is the stored initial condition, then the saved
    steps 1, 10, 20, ... of each rollout.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import h5py
import numpy as np
import yaml

REFERENCE = ("/global/cfs/cdirs/m4790/Data/kinet/doubly_periodic/weakly_compressible_isoT_fluids/"
             "sys_Re-5e4_Ma-1en1/D2Q9_shape-256-256_T-10000_H-dc804f.h5")
DC804F = ("/global/u2/k/khegazy/projects/metrics/fluid_metrics/docs/datasets/logs/kinet_runs/"
          "kinet_re5e4/dc804f/dc804f.yaml")
FIELDS = ("density", "velocity", "vorticity")
D2Q9 = [((0, 0), 4 / 9), ((1, 0), 1 / 9), ((0, 1), 1 / 9), ((-1, 0), 1 / 9), ((0, -1), 1 / 9),
        ((1, 1), 1 / 36), ((-1, 1), 1 / 36), ((-1, -1), 1 / 36), ((1, -1), 1 / 36)]


def saved_steps(h: h5py.File) -> tuple[np.ndarray, np.ndarray]:
    """Return the saved slots and their solver steps (lead) of a grouped rollout."""
    s = h["time/time"][:]
    slots = np.where(np.isfinite(s))[0]
    return slots, s[slots].astype(int)


def frame(h: h5py.File, field: str, slot: int | None) -> np.ndarray:
    """Field at a slot as (C, X, Y); slot None is the initial condition."""
    if slot is None:
        return h[f"initial_conditions/observables/{field}"][0, :, 0]
    return h[f"observables/{field}"][0, :, slot]


def derivative(a: np.ndarray, axis: int, op: str) -> np.ndarray:
    """d a / d x_axis on the periodic unit-spacing grid with one of three operators."""
    if op == "central":
        return (np.roll(a, -1, axis) - np.roll(a, 1, axis)) / 2
    if op == "d2q9":  # kinet's Curl stencil: 3 sum_i w_i c_i a(x + c_i) (Ramadugu et al. 2013, Eq. 11)
        return 3 * sum(w * c[axis] * np.roll(a, (-c[0], -c[1]), (0, 1)) for c, w in D2Q9 if c[axis])
    k = np.fft.fftfreq(a.shape[axis], d=1 / a.shape[axis]) * 2 * np.pi / a.shape[axis]
    shape = [1, 1]
    shape[axis] = -1
    return np.fft.ifft2(1j * k.reshape(shape) * np.fft.fft2(a)).real


def perturbation_checks(du: np.ndarray, u_rms: float, kmax: float = 16.0) -> dict:
    """Divergence (relative to vorticity) under three operators, rms over u_rms, band leakage."""
    out = {"rms_over_u_rms": float(np.sqrt(np.mean(np.sum(du**2, 0))) / u_rms)}
    for op in ("spectral", "central", "d2q9"):
        div = derivative(du[0], 0, op) + derivative(du[1], 1, op)
        vort = derivative(du[1], 0, op) - derivative(du[0], 1, op)
        out[f"max_div_over_max_vort_{op}"] = float(np.abs(div).max() / np.abs(vort).max())
    m = np.fft.fftfreq(du.shape[1], d=1 / du.shape[1])
    kmag = np.hypot(*np.meshgrid(m, m, indexing="ij"))
    e = np.sum(np.abs(np.fft.fft2(du)) ** 2, 0)
    band = (kmag >= 1) & (kmag <= kmax)
    out["energy_fraction_outside_band"] = float(e[~band].sum() / e.sum())
    out["energy_weighted_mean_k"] = float((e * kmag).sum() / e.sum())
    return out


def rms(a: np.ndarray) -> float:
    """sqrt of the mean over cells of the sum over channels of a^2."""
    return float(np.sqrt(np.mean(np.sum(a**2, 0))))


def cmd_config(a) -> None:
    """Key-by-key comparison of the composed config (config.yaml of a run) with dc804f."""
    class Loader(yaml.SafeLoader):
        pass
    Loader.add_multi_constructor("tag:yaml.org,2002:python/", lambda l, s, n: l.construct_sequence(n)[0]
                                 if isinstance(n, yaml.SequenceNode) else None)
    old = yaml.load(open(DC804F), Loader=Loader)
    new = yaml.safe_load(open(a.run_config))
    c, sp = new["case"], old["solver"]["system_parameters"]
    rows = [
        ("grid", old["spatiotemporal_grid"]["spatial"]["grid"], c["discretization"]["spatial"]["grid"]),
        ("lattice", old["lattice"]["type"], c["lattice"]["type"]),
        ("lattice shifts", old["lattice"]["shifts"], c["lattice"]["shifts"]),
        ("use_static_weights", old["lattice"]["use_static_weights"], c["lattice"]["use_static_weights"]),
        ("collision", old["collision"]["type"], c["collision"]["type"]),
        ("enforce_positive", old["collision"]["enforce_positive"], c["collision"].get("enforce_positive", "no key")),
        ("stabilizer type", old["stability"]["type"], c["collision"]["stabilizer"]["type"]),
        ("stabilizer input_dists", old["stability"]["input_dists"], c["collision"]["stabilizer"]["input_dists"]),
        ("stabilizer max_iterations", old["stability"]["max_iterations"], c["collision"]["stabilizer"]["max_iterations"]),
        ("equilibrium closure F", old["neurde"]["F"]["type"], c["simulate_equilibrium_closure"]["F"]["type"]),
        ("physics", old["solver"]["type"], c["physics"]["type"]),
        ("reynolds", sp["reynolds"], c["physics"]["parameters"]["reynolds"]),
        ("mach", sp["mach"], c["physics"]["parameters"]["mach"]),
        ("density (IC / reference)", sp["initial_conditions"]["density"], c["physics"]["parameters"]["reference"]["density"]),
        ("lambda", sp["initial_conditions"]["lambda"], c["initial_conditions"]["lambda"]),
        ("epsilon", sp["initial_conditions"]["epsilon"], c["initial_conditions"]["epsilon"]),
        ("boundary", old["boundary_conditions"], c["boundary_conditions"]),
        ("output_variables", old["solver"]["output_variables"], c["physics"]["output_variables"]),
        ("dtype", old["dtype"], new["precision"]["dtype"]),
        ("steps (identity only; members run 5000)", old["pred_length"], c["discretization"]["temporal"]["grid"]),
    ]
    lines = [f"{'key':42s} | dc804f (archived) | composed (current kinet)"]
    lines += [f"{k:42s} | {o} | {n}" for k, o, n in rows]
    Path(a.out).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def cmd_validate(a) -> None:
    """2a, 2b, 2c."""
    res = {}
    ref = h5py.File(REFERENCE, "r")
    # 2a: du = 0 continuation, saved every step.
    h = h5py.File(a.control, "r")
    s0 = int(h.attrs["ensemble_start_step"])
    slots, steps = saved_steps(h)
    rows = []
    for sl, st in zip(slots, steps):
        rows.append({"step": int(st),
                     "max_abs_density": float(np.abs(frame(h, "density", sl) - ref["density"][0, :, s0 + st]).max()),
                     "max_abs_velocity": float(np.abs(frame(h, "velocity", sl) - ref["velocity"][0, :, s0 + st]).max()),
                     "rms_velocity": rms(frame(h, "velocity", sl) - ref["velocity"][0, :, s0 + st])})
    umax = float(np.abs(ref["velocity"][0, :, s0]).max())
    res["2a_control"] = {"start": s0, "max_abs_u_ref": umax, "rows": rows}
    # 2b: every member's perturbation, recovered from its stored initial condition.
    res["2b_perturbations"] = []
    for f in sorted(glob.glob(a.members_glob)):
        g = h5py.File(f, "r")
        s = int(g.attrs["ensemble_start_step"])
        du = frame(g, "velocity", None) - ref["velocity"][0, :, s]
        dr = float(np.abs(frame(g, "density", None) - ref["density"][0, 0, s]).max())
        rec = {"file": f, "start": s, "seed": g.attrs["ensemble_seed"],
               "amplitude": float(g.attrs["ensemble_amplitude_over_u_rms"]), "max_abs_density_change": dr}
        rec.update(perturbation_checks(du, float(g.attrs["ensemble_start_u_rms"])))
        res["2b_perturbations"].append(rec)
    # 2c: two members of different seeds.
    p, q = h5py.File(a.pair[0], "r"), h5py.File(a.pair[1], "r")
    A = float(p.attrs["ensemble_amplitude_over_u_rms"]) * float(p.attrs["ensemble_start_u_rms"])
    slots, steps = saved_steps(p)
    rows = [{"lead": 0, "rms_velocity_difference": rms(frame(p, "velocity", None) - frame(q, "velocity", None))}]
    for sl, st in zip(slots, steps):
        rows.append({"lead": int(st), "rms_velocity_difference": rms(frame(p, "velocity", sl) - frame(q, "velocity", sl))})
    res["2c_pair"] = {"perturbation_rms": A, "sqrt2_times_rms": float(np.sqrt(2) * A),
                      "ratio_at_lead0": rows[0]["rms_velocity_difference"] / (np.sqrt(2) * A), "rows": rows}
    Path(a.out).write_text(json.dumps(res, indent=1))
    c = res["2a_control"]["rows"]
    print("2a step, max|drho|, max|du|, rms du:")
    for r in c:
        if r["step"] in (1, 2, 5, 10, 20, 50, 100):
            print(f"  {r['step']:4d} {r['max_abs_density']:.3e} {r['max_abs_velocity']:.3e} {r['rms_velocity']:.3e}")
    keys = [k for k in res["2b_perturbations"][0] if k not in ("file", "seed", "start")]
    print("2b over", len(res["2b_perturbations"]), "members: min / max")
    for k in keys:
        v = [r[k] for r in res["2b_perturbations"] if (r["amplitude"] > 0 or k == "max_abs_density_change")]
        print(f"  {k:36s} {min(v):.3e} {max(v):.3e}")
    print("2c ratio at lead 0:", res["2c_pair"]["ratio_at_lead0"])
    for r in res["2c_pair"]["rows"]:
        if r["lead"] in (0, 1, 10, 100, 500, 1000, 2000, 3000, 4000, 5000):
            print(f"  lead {r['lead']:5d} rms|u_a - u_b| = {r['rms_velocity_difference']:.3e} "
                  f"({r['rms_velocity_difference'] / (np.sqrt(2) * A):.3f} x sqrt2 A)")


def shell_ratio(stack: np.ndarray, edges: list[float]) -> list[float]:
    """Member variance over mean member energy, per wavenumber shell, for (M, C, X, Y)."""
    n = stack.shape[-1]
    m = np.fft.fftfreq(n, d=1 / n)
    kmag = np.hypot(*np.meshgrid(m, m, indexing="ij"))
    hat = np.fft.fft2(stack)
    var = np.sum(np.var(hat.real, 0, ddof=1) + np.var(hat.imag, 0, ddof=1), 0)
    en = np.sum(np.mean(np.abs(hat) ** 2, 0), 0)
    return [float(var[(kmag > lo) & (kmag <= hi)].sum() / en[(kmag > lo) & (kmag <= hi)].sum())
            for lo, hi in zip(edges[:-1], edges[1:])]


def cmd_ensemble(a) -> None:
    """Spread, leave-one-out error-to-variance ratio, decorrelation by scale, amplitude check."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    root = Path(a.root)
    edges = [0, 4, 16, 64, 182]
    spec_leads = (0, 100, 500, 1000, 2000, 3000, 4000, 5000)
    res = {"definition": __doc__.split("Conventions")[1].strip(), "shell_edges": edges, "starts": {}}
    for sdir in sorted(root.glob("start_*")):
        files = sorted(sdir.glob("member_*_amp1e-03/rollout.h5"))
        hs = [h5py.File(f, "r") for f in files]
        N1 = len(hs)  # N + 1 runs; each is the truth in turn against the other N
        slots, steps = saved_steps(hs[0])
        leads = [0] + [int(x) for x in steps]
        st = {"n_runs": N1, "leads": leads, "fields": {f: {"spread": [], "mse": [], "var": [], "std": []} for f in FIELDS},
              "shell_ratio_velocity": {}, "shell_ratio_vorticity": {}}
        for i, sl in enumerate([None] + list(slots)):
            for fld in FIELDS:
                x = np.stack([frame(h, fld, sl) for h in hs])          # (N + 1, C, X, Y)
                S, Q = x.sum(0), (x**2).sum(0)
                mo = (S[None] - x) / (N1 - 1)                          # mean of the other N
                vo = (Q[None] - x**2 - (N1 - 1) * mo**2) / (N1 - 2)    # their variance, ddof = 1
                d = st["fields"][fld]
                d["mse"].append(float(np.mean((x - mo) ** 2) * x.shape[1]))
                d["var"].append(float(np.mean(vo) * x.shape[1]))
                per_truth = np.mean((x - mo) ** 2, axis=(1, 2, 3)) / np.mean(vo, axis=(1, 2, 3))
                d.setdefault("per_truth_ratio_min", []).append(float(per_truth.min()))
                d.setdefault("per_truth_ratio_max", []).append(float(per_truth.max()))
                d["spread"].append(float(np.sqrt(np.mean(np.var(x, 0, ddof=1)) * x.shape[1])))
                d["std"].append(float(np.sqrt(np.mean(np.var(x, axis=(2, 3))) * x.shape[1])))
                if leads[i] in spec_leads and fld in ("velocity", "vorticity"):
                    st[f"shell_ratio_{fld}"][leads[i]] = shell_ratio(x, edges)
                if leads[i] == leads[-1] and fld == "vorticity":
                    fig, ax = plt.subplots(1, 2, figsize=(10, 4.4))
                    for axi, img, t in ((ax[0], x[:, 0].mean(0), "ensemble-mean vorticity"),
                                        (ax[1], x[:, 0].std(0, ddof=1), "member std of vorticity")):
                        im = axi.imshow(img.T, origin="lower", cmap="RdBu_r" if axi is ax[0] else "viridis")
                        axi.set_title(f"{t}, start {sdir.name[6:]}, lead {leads[i]}")
                        fig.colorbar(im, ax=axi, shrink=0.8)
                    fig.tight_layout()
                    fig.savefig(Path(a.out).with_name(f"spread_map_{sdir.name}.png"), dpi=110)
                    plt.close(fig)
        res["starts"][sdir.name] = st
        # Amplitude check: the 1e-2 run and the 1e-3 run of the same seed against the reference.
        big = sorted(sdir.glob("member_*_amp1e-02/rollout.h5"))
        if big:
            ref = h5py.File(REFERENCE, "r")
            s0 = int(hs[0].attrs["ensemble_start_step"])
            hb = h5py.File(big[0], "r")
            hm = h5py.File(sdir / big[0].parent.name.replace("amp1e-02", "amp1e-03") / "rollout.h5", "r")
            rows = []
            for lead, sl in zip(leads, [None] + list(slots)):
                if s0 + lead > 10000:
                    break
                r = ref["velocity"][0, :, s0 + lead]
                db, dm = rms(frame(hb, "velocity", sl) - r), rms(frame(hm, "velocity", sl) - r)
                rows.append({"lead": lead, "d_amp1e-2": db, "d_amp1e-3": dm, "ratio_over_10": db / dm / 10})
            res["amplitude_check"] = {"start": s0, "big": str(big[0]), "small": hm.filename, "rows": rows}
    # The ratio pooled over the N + 1 choices of truth and the starts.
    N = res["starts"][next(iter(res["starts"]))]["n_runs"] - 1
    res["expected_ratio"] = (N + 1) / N
    table = {}
    leads = res["starts"][next(iter(res["starts"]))]["leads"]
    for fld in FIELDS:
        mse = np.mean([st["fields"][fld]["mse"] for st in res["starts"].values()], 0)
        var = np.mean([st["fields"][fld]["var"] for st in res["starts"].values()], 0)
        per = np.array([np.array(st["fields"][fld]["mse"]) / np.array(st["fields"][fld]["var"]) for st in res["starts"].values()])
        table[fld] = {"ratio": (mse / var).tolist(), "per_start": per.tolist()}
    res["pooled"] = table
    Path(a.out).write_text(json.dumps(res, indent=1))

    show = [0, 1, 10, 100, 500, 1000, 2000, 3000, 4000, 5000]
    lines = [f"N = {N}; expected mean squared error / mean variance = (N+1)/N = {res['expected_ratio']:.4f}",
             "NOTE: pooled over all N+1 choices of truth, sum_j e_j^2 / sum_j var_-j = (N+1)/N is an algebraic",
             "identity in every cell (x_j - mean_-j = (M/(M-1))(x_j - mean); M = N+1), so the pooled ratio tests",
             "nothing. Any statistic symmetric in the N+1 runs (pooled rank histogram too) is fixed the same way;",
             "what the data can show is whether single truths depart, the {min-max} below.",
             "ratio pooled over the N+1 truths and the starts [per start] {min-max over single truths}:"]
    for fld in FIELDS:
        for L in show:
            j = leads.index(L)
            lo = min(st["fields"][fld]["per_truth_ratio_min"][j] for st in res["starts"].values())
            hi = max(st["fields"][fld]["per_truth_ratio_max"][j] for st in res["starts"].values())
            lines.append(f"  {fld:9s} lead {L:5d}: {table[fld]['ratio'][j]:.6f} "
                         f"[{', '.join(f'{p[j]:.6f}' for p in table[fld]['per_start'])}] {{{lo:.3f}-{hi:.3f}}}")
    Path(a.out).write_text(json.dumps(res, indent=1))
    lines.append("spread (relative to its lead-0 value) and spread / field spatial std, per start:")
    for name, st in res["starts"].items():
        for fld in FIELDS:
            sp, sd = np.array(st["fields"][fld]["spread"]), np.array(st["fields"][fld]["std"])
            lines.append(f"  {name} {fld:9s} " + " ".join(
                f"{L}:{sp[leads.index(L)] / sp[0]:.3g}({sp[leads.index(L)] / sd[leads.index(L)]:.2g})" for L in show))
    lines.append(f"member variance / mean energy per |k| shell {edges} (velocity | vorticity):")
    for name, st in res["starts"].items():
        for L in spec_leads:
            lines.append(f"  {name} lead {L:5d}: " + " ".join(f"{v:.2e}" for v in st["shell_ratio_velocity"][L])
                         + " | " + " ".join(f"{v:.2e}" for v in st["shell_ratio_vorticity"][L]))
    if "amplitude_check" in res:
        lines.append(f"amplitude check (start {res['amplitude_check']['start']}): rms|u - u_ref|, ratio/10")
        for r in res["amplitude_check"]["rows"]:
            if r["lead"] in show:
                lines.append(f"  lead {r['lead']:5d}: {r['d_amp1e-2']:.3e} {r['d_amp1e-3']:.3e} {r['ratio_over_10']:.3f}")
    Path(a.out).with_suffix(".txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("config")
    c.add_argument("run_config")
    c.add_argument("--out", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--control", required=True)
    v.add_argument("--members-glob", required=True)
    v.add_argument("--pair", nargs=2, required=True)
    v.add_argument("--out", required=True)
    e = sub.add_parser("ensemble")
    e.add_argument("--root", required=True)
    e.add_argument("--out", required=True)
    a = p.parse_args()
    {"config": cmd_config, "validate": cmd_validate, "ensemble": cmd_ensemble}[a.cmd](a)


if __name__ == "__main__":
    main()
