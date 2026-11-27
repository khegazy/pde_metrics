"""Write _provenance/shear_layer_ensemble/job_<id>/RUN.txt for one ensemble job, and copy its configs.

Research-grade helper. Usage: python write_run_txt.py JOB_ID ARGS_FILE "SBATCH LINE"
Reads the job's working directory (_work/shear_layer_ensemble/job_<id>/), the summary.json that
ensemble_driver.py wrote for each invocation, and sacct; refuses a job with a run that did not
reach its last step.
"""

import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

W = Path("/pscratch/sd/k/khegazy/kinet_datasets")
P = W / "_provenance/shear_layer_ensemble"
job, args_file, sbatch = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
wd = W / "_work/shear_layer_ensemble" / f"job_{job}"
dst = P / f"job_{job}"
dst.mkdir(parents=True, exist_ok=True)


def sh(cmd: str) -> str:
    """Run a shell command and return its stripped stdout."""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


lines = [f"# Ensemble job {job}",
         f"slurm_job_id: {job}",
         "sacct: " + sh(f"sacct -j {job} -X -n -P -o JobID,JobName,Partition,QOS,Account,Submit,Start,End,Elapsed,State,ExitCode,NodeList"),
         f"sbatch_exact (from {W}/_work/shear_layer_ensemble): {sbatch}",
         f"args_file: {args_file} (copied here)",
         "kinet: " + sh("git -C /global/u2/k/khegazy/projects/pde/kinet rev-parse HEAD") + " branch "
         + sh("git -C /global/u2/k/khegazy/projects/pde/kinet branch --show-current"),
         "environment: source /pscratch/sd/k/khegazy/kinet_datasets/_work/env.sh   # kinet .venv unchanged, KINET_PROJECT, caches on scratch",
         f"working_directory: {wd}",
         "invocations (rc and wall time from run_ensemble_job.sh):"]
lines += ["  " + x for x in (wd / "invocations.txt").read_text().splitlines()]
all_ok = True
for i, raw in enumerate([x for x in args_file.read_text().splitlines() if x.strip() and not x.startswith("#")], 1):
    a = shlex.split(raw)
    out = Path(a[a.index("--out") + 1]) / f"start_{int(a[a.index('--start') + 1]):05d}"
    s = json.loads((out / "summary.json").read_text())
    shutil.copy(out / "composed_config.json", dst / f"composed_config_invocation{i}.json")
    shutil.copy(Path(s["runs"][0]["path"]).parent / "config.yaml", dst / f"config_invocation{i}.yaml")
    lines += [f"invocation {i}:",
              "  command: " + (wd / f"command_{i}.txt").read_text().strip(),
              f"  device: {s['device']}; kinet commit recorded by the driver: {s['kinet_commit']}",
              f"  start step: {s['start_step']} of {s['reference']}",
              f"  u_rms of the start frame: {s['u_rms']:.6e}; kmax {s['kmax']}; io.save_every_n {s['save_every_n']}",
              f"  reference consistency: {json.dumps(s['consistency'])}",
              f"  output: {out} ({sh(f'du -sh --apparent-size {out} | cut -f1')})",
              "  runs (name | seed = SeedSequence entropy | amplitude/u_rms | steps | stop_reason | status | last saved step | reached | rollout wall s | bytes | path):"]
    for r in s["runs"]:
        all_ok &= bool(r["reached_last_step"])
        lines.append(f"    {r['name']} | {r['seed']} | {r['amplitude']:g} | {r['steps']} | {r['stop_reason']} | "
                     f"{r['kinet_rollout_status']} | {r['last_saved_step']} | {r['reached_last_step']} | "
                     f"{r['rollout_wall_s']} | {r['bytes']} | {r['path']}")
lines.append(f"every run reached its last step: {all_ok}")
lines.append("checkpoints: the driver deletes <run>/sim_checkpoints after each run; remaining: "
             + (sh(f"find {W}/shear_layer_ensemble -name sim_checkpoints") or "none"))
shutil.copy(args_file, dst / args_file.name)
for f in ["slurm_%s.out" % job]:
    shutil.copy(W / "_work/shear_layer_ensemble" / f, dst / f)
for f in sorted(wd.glob("log_*.txt")):
    shutil.copy(f, dst / f.name)
(dst / "RUN.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
if not all_ok:
    sys.exit(f"job {job} has a run that did not reach its last step")
