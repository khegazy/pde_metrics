#!/bin/bash
# Copy one finished run's provenance into _provenance/<run name>/ and delete its empty or
# leftover sim_checkpoints/ (checkpoints are not data; BUILD_ORDER.md, "How kinet runs are configured").
# Usage: collect_provenance.sh RUN_NAME JOB_ID
set -euo pipefail
name=${1:?run name}; job=${2:?job id}
W=/pscratch/sd/k/khegazy/kinet_datasets
run=$W/_work/$name
out=$W/_provenance/$name
mkdir -p "$out"
h5=$(grep -o "Updated manifest for [^ ]*rollout.h5" "$run/log.txt" | tail -1 | sed 's/Updated manifest for //')
[ -n "$h5" ] || { echo "no rollout recorded in $run/log.txt" >&2; exit 1; }
grep -q "stop_reason=completed" "$run/log.txt" || { echo "run $name did not complete" >&2; exit 1; }
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
    echo "run_in_job: $(grep "^$name " "$W/_work/job_${job}_runs.txt")"
    echo "kinet: $(git -C /global/u2/k/khegazy/projects/pde/kinet rev-parse HEAD) branch $(git -C /global/u2/k/khegazy/projects/pde/kinet branch --show-current)"
    echo "device: $(grep -m1 '^torch ' "$W/_work/slurm_${job}.out")"
    echo "gpu: $(grep -m1 'A100\|H100\|NVIDIA' "$W/_work/slurm_${job}.out")"
    echo "rollout: $h5"
    echo "rollout_bytes: $(stat -c %s "$h5")"
    echo "working_directory: $run"
    echo "environment: source $W/_work/env.sh   # kinet .venv, KINET_PROJECT, caches on scratch"
    echo "command (run inside the working directory by run_kinet_job.sh):"
    echo "  $(cat "$run/command.txt")"
    echo "sbatch: sbatch --account=m4790 --constraint=gpu --qos=debug --nodes=1 --ntasks=1 --cpus-per-task=32 --gpus-per-node=1 --time=<limit> run_kinet_job.sh <runs file>"
} > "$out/RUN.md"
cp "$W/_work/run_kinet_job.sh" "$W/_work/env.sh" "$out/"
echo "collected $name -> $out"
