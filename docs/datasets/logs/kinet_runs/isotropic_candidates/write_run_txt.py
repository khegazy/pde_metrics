"""Write _provenance/isotropic_candidates/job_<id>/RUN.txt for one candidates job, and copy its configs.

Research-grade helper, adapted from _provenance/shear_layer_ensemble/write_run_txt.py.
Usage: python write_run_txt.py JOB_ID ARGS_FILE "SBATCH LINE"
Reads the job's working directory (_work/isotropic_candidates/job_<id>/), the summary.json that
candidates_driver.py wrote for each kind, and sacct. Copies each kind's composed configuration to
configs/Re-<re>_<kind>.json and kinet's saved config.yaml beside it. Exits non-zero if a run of
the job did not reach its last step (the record is written either way).
"""

import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

W = Path("/pscratch/sd/k/khegazy/kinet_datasets")
P = W / "_provenance/isotropic_candidates"
K = "/global/u2/k/khegazy/projects/pde/kinet"
job, args_file, sbatch = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
wd = W / "_work/isotropic_candidates" / f"job_{job}"
dst = P / f"job_{job}"
dst.mkdir(parents=True, exist_ok=True)
(P / "configs").mkdir(exist_ok=True)


def sh(cmd: str) -> str:
    """Run a shell command and return its stripped stdout."""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


lines = [f"# Isotropic candidates job {job}",
         f"slurm_job_id: {job}",
         "sacct: " + sh(f"sacct -j {job} -X -n -P -o JobID,JobName,Partition,QOS,Account,Submit,Start,End,Elapsed,State,ExitCode,NodeList"),
         f"sbatch_exact (from {W}/_work/isotropic_candidates): {sbatch}",
         f"args_file: {args_file} (copied here)",
         f"kinet: {sh(f'git -C {K} rev-parse HEAD')} branch {sh(f'git -C {K} branch --show-current')}; "
         f"uncommitted changes: {sh(f'git -C {K} status --short') or 'none'}",
         "torch: " + sh(f"{K}/.venv/bin/python -c 'import torch; print(torch.__version__)'"),
         "environment: source /pscratch/sd/k/khegazy/kinet_datasets/_work/env.sh   # kinet .venv unchanged, KINET_PROJECT, caches on scratch",
         f"working_directory: {wd}",
         "invocations (rc and wall time from run_candidates_job.sh):"]
lines += ["  " + x for x in (wd / "invocations.txt").read_text().splitlines()]
all_ok = True
for i, raw in enumerate([x for x in args_file.read_text().splitlines() if x.strip() and not x.startswith("#")], 1):
    a = shlex.split(raw)
    re_key, kinds, out = a[a.index("--re") + 1], a[a.index("--kinds") + 1].split(","), Path(a[a.index("--out") + 1])
    lines += [f"invocation {i}:", "  command: " + (wd / f"command_{i}.txt").read_text().strip()]
    for kind in kinds:
        kdir = out / f"Re-{re_key}" / kind
        sp = kdir / "summary.json"
        if not sp.exists():
            lines.append(f"  kind {kind}: no summary.json (not started)")
            all_ok = False
            continue
        s = json.loads(sp.read_text())
        shutil.copy(kdir / "composed_config.json", P / "configs" / f"Re-{re_key}_{kind}.json")
        first = next(iter(s["runs"].values()))
        cfg = Path(first["path"]).parent / "config.yaml"
        if cfg.exists():
            shutil.copy(cfg, P / "configs" / f"Re-{re_key}_{kind}_config.yaml")
        lines += [f"  kind {kind}: grid {s['grid']}^2, Re {s['reynolds']:g} (reference {s['reynolds_reference']:g} x {s['reynolds_factor']}), "
                  f"collision {s['collision']}, steps {s['steps']}, io.save_every_n {s['save_every_n']}; device {s['device']}; "
                  f"kinet commit recorded by the driver {s['kinet_commit']}; simulator build {s['build_s']} s",
                  f"    composed config: configs/Re-{re_key}_{kind}.json; overrides: {' '.join(s['overrides'])}",
                  "    runs (reference key | stop_reason | status | last saved step | saved frames | reached | IC max diff rho, u | rollout wall s | bytes | path | error):"]
        for key, r in s["runs"].items():
            all_ok &= bool(r["reached_last_step"])
            lines.append(f"      {key} | {r.get('stop_reason')} | {r.get('kinet_rollout_status')} | {r.get('last_saved_step')} | "
                         f"{r.get('saved_frames')} | {r['reached_last_step']} | {r.get('ic_max_abs_density_diff')}, "
                         f"{r.get('ic_max_abs_velocity_diff')} | {r['rollout_wall_s']} | {r.get('bytes')} | {r['path']} | {r.get('error')}")
lines.append(f"every run reached its last step: {all_ok}")
lines.append("checkpoints: the driver deletes <run>/sim_checkpoints after each run; remaining: "
             + (sh(f"find {W}/isotropic_candidates -name sim_checkpoints") or "none"))
shutil.copy(args_file, dst / args_file.name)
shutil.copy(W / "_work/isotropic_candidates" / f"slurm_{job}.out", dst / f"slurm_{job}.out")
for f in sorted(wd.glob("log_*.txt")):
    # keep the log without its per-100-step progress lines (they are most of its size)
    kept = [x for x in f.read_text().splitlines() if "accepted step=" not in x]
    (dst / f.name).write_text("\n".join(kept) + "\n")
(dst / "RUN.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
if not all_ok:
    sys.exit(f"job {job} has a run that did not reach its last step")
