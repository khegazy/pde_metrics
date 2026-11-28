#!/bin/bash
# Copy one forced-turbulence run's provenance into _provenance/forced_turbulence/<run name>/:
# config.yaml and manifest.yaml from beside the data, resolved_config.yaml, run_provenance.yaml
# and simulate.log from the Hydra run directory, the job header (kinet.__file__, worktree commit
# and status, versions), command, log and Slurm output, and a RUN.txt that states whether the
# rollout reached its last step (the walltime guard exits 0 when it stops early).
# Usage: collect_run.sh RUN_NAME JOB_ID [SBATCH_LINE]
set -euo pipefail
name=${1:?run name}; job=${2:?job id}; sbatch_line=${3:-not given}
W=/pscratch/sd/k/khegazy/kinet_datasets
P=$W/_provenance/forced_turbulence
run=$W/_work/forced_turbulence/$name
out=$P/$name
mkdir -p "$out"
h5=$(grep -o "Updated manifest for [^ ]*rollout.h5" "$run/log_$job.txt" | tail -1 | sed 's/Updated manifest for //')
[ -n "$h5" ] || { echo "no rollout recorded in $run/log_$job.txt" >&2; exit 1; }
ident=$(dirname "$(dirname "$(dirname "$h5")")")
hyd=$(ls -d "$run"/outputs/*/*/simulate/job_* | tail -1)
cp "$ident/config.yaml" "$ident/manifest.yaml" "$out/"
cp "$hyd/resolved_config.yaml" "$hyd/run_provenance.yaml" "$hyd/simulate.log" "$out/"
cp "$run/job_${job}_header.txt" "$run/command_$job.txt" "$run/log_$job.txt" "$out/"
cp "$W/_work/forced_turbulence/slurm_$job.out" "$out/"
check=$(python -B -c "
import sys, h5py, numpy as np
f = h5py.File(sys.argv[1], 'r'); a = f.attrs; s = f['time/time'][:]; fin = s[np.isfinite(s)]
total = int(a.get('kinet_rollout_total_pred_length'))
print('kinet_rollout_status=%s kinet_last_completed_step=%s total_pred_length=%d last_saved_step=%d saved_frames=%d reached_last_step=%s'
      % (a['kinet_rollout_status'], a.get('kinet_last_completed_step'), total, fin[-1], fin.size,
         a['kinet_rollout_status'] == 'complete' and int(fin[-1]) == total))" "$h5")
{
    echo "# Run $name"
    echo "slurm_job_id: $job"
    echo "sacct: $(sacct -j "$job" -X -n -P -o JobID,JobName,Partition,QOS,Account,Submit,Start,End,Elapsed,State,ExitCode,NodeList)"
    echo "run_in_job: $(grep "^$name job=$job " "$W/_work/forced_turbulence/runs.txt" || true)"
    echo "job_header:"; sed 's/^/  /' "$run/job_${job}_header.txt"
    echo "rollout: $h5"
    echo "rollout_bytes: $(stat -c %s "$h5")"
    echo "sim_checkpoints: $(ls "$ident/sim_checkpoints" 2>/dev/null | tr '\n' ' ' || true)"
    echo "last_step_check: $check"
    echo "rollout_timing: $(grep -E 'Rollout finished' "$run/log_$job.txt" | tail -1)"
    echo "steady_ms_per_step: $(grep -E 'ms/step' "$run/log_$job.txt" | tail -1 | sed 's/.*(\(.*ms\/step\)).*/\1/')"
    echo "working_directory: $run"
    echo "environment: source $P/env.sh"
    echo "command (run in the working directory by run_forced_job.sh):"
    echo "  $(cat "$run/command_$job.txt")"
    echo "sbatch_exact (from $W/_work/forced_turbulence): $sbatch_line"
} > "$out/RUN.txt"
echo "collected $name -> $out"; grep last_step_check "$out/RUN.txt"
