#!/bin/bash
# Copy of /pscratch/sd/k/khegazy/kinet_datasets/_work/shocks_2d/collect_provenance.sh with its working folder moved to
# _work/shocks_2d/dmr_fine and the kinet commit read from the worktree that env.sh names.
# Copy one finished run's provenance into _provenance/<run name>/ (RUN.txt, with the last-step check and output size) and delete its empty or
# PonD runs are adaptive in time, so the last-step check compares the last stored time with the configured end time.
# leftover sim_checkpoints/ (checkpoints are not data; BUILD_ORDER.md, "How kinet runs are configured").
# Usage: collect_provenance.sh RUN_NAME JOB_ID
set -euo pipefail
name=${1:?run name}; job=${2:?job id}
W=/pscratch/sd/k/khegazy/kinet_datasets
WS=$W/_work/shocks_2d/dmr_fine
K=/pscratch/sd/k/khegazy/kinet_worktrees/dmr_fine
run=$WS/$name
out=$W/_provenance/shocks_2d/$name
mkdir -p "$out"
h5=$(grep -o "Updated manifest for [^ ]*rollout.h5" "$run/log.txt" | tail -1 | sed 's/Updated manifest for //')
[ -n "$h5" ] || { echo "no rollout recorded in $run/log.txt" >&2; exit 1; }
grep -qE "stop_reason=(completed|target_reached)" "$run/log.txt" || { echo "run $name did not complete" >&2; exit 1; }
ident=$(dirname "$(dirname "$(dirname "$h5")")")
hyd=$(ls -d "$run"/outputs/*/*/simulate/job_* | tail -1)
cp "$ident/config.yaml" "$out/config.yaml"
cp "$ident/manifest.yaml" "$out/manifest.yaml"
cp "$hyd/resolved_config.yaml" "$hyd/run_provenance.yaml" "$out/"
cp "$hyd/simulate.log" "$out/simulate.log"
if [ -d "$ident/sim_checkpoints" ]; then
    ls -la "$ident/sim_checkpoints" > "$out/sim_checkpoints_listing_before_delete.txt"
    rm -rf "$ident/sim_checkpoints"
fi
{
    echo "# Run $name"
    echo "slurm_job_id: $job"
    echo "sacct: $(sacct -j "$job" -X -n -P -o JobID,JobName,Partition,QOS,Account,Submit,Start,End,Elapsed,State,ExitCode,NodeList)"
    echo "run_in_job: $(grep "^$name " "$WS/job_${job}_runs.txt")"
    echo "kinet: $(git -C "$K" rev-parse HEAD) worktree $K (detached at origin/main)"
    echo "kinet_uncommitted_paths: $(git -C "$K" status --short | wc -l) (git status --short at collection; the job log records it at run time)"
    echo "device: $(grep -m1 '^  device:' "$out/resolved_config.yaml" | sed 's/^ *device: *//') (launch.device), torch $(/global/u2/k/khegazy/projects/pde/kinet/.venv/bin/python -c 'import torch; print(torch.__version__, "cuda", torch.version.cuda)')"
    echo "gpu: $(grep -m1 'A100\|H100\|NVIDIA' "$WS/slurm_${job}.out")"
    echo "rollout: $h5"
    echo "rollout_bytes: $(stat -c %s "$h5")"
    echo "output_dir_size_after_checkpoint_delete: $(du -sh --apparent-size "$ident" | cut -f1) ($ident)"
    echo "last_step_check: $(/global/u2/k/khegazy/projects/pde/kinet/.venv/bin/python -B -c "import sys,math,hdf5plugin,h5py,numpy as np,yaml; f=h5py.File(sys.argv[1],'r'); a=f.attrs; s=f['time/time'][:]; k=f['time/time_index'][:]; fin=np.isfinite(s); t_end=float(yaml.safe_load(open(sys.argv[2]))['case']['discretization']['temporal']['length']); print('kinet_rollout_status=%s kinet_last_completed_step=%s total_pred_length=%s last_saved_time=%r last_saved_time_index=%d saved_frames=%d t_end=%r reached_end=%s' % (a['kinet_rollout_status'], a.get('kinet_last_completed_step'), a.get('kinet_rollout_total_pred_length'), s[fin][-1], k[fin][-1], fin.sum(), t_end, a['kinet_rollout_status']=='complete' and math.isclose(s[fin][-1], t_end, rel_tol=1e-12)))" "$h5" "$out/config.yaml")"
    echo "working_directory: $run"
    echo "environment: source $WS/env.sh   # kinet .venv, KINET_PROJECT, caches on scratch"
    echo "command (run inside the working directory by run_kinet_job.sh):"
    echo "  $(cat "$run/command.txt")"
    echo "sbatch_exact (from $WS): ${SBATCH_LINE:-not given}"
    echo "sbatch: sbatch --account=m4790 --constraint=gpu --qos=<debug|regular> --nodes=1 --ntasks=1 --cpus-per-task=32 --gpus-per-node=1 --time=<limit> run_kinet_job.sh <runs file>"
} > "$out/RUN.txt"
cp "$WS/run_kinet_job.sh" "$WS/env.sh" "$out/"
echo "collected $name -> $out"
