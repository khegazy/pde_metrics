#!/bin/bash
# Run ensemble_driver.py once per line of ARGS_FILE in one Slurm job, from a working directory on scratch.
#
# Environment as run_kinet_job.sh of the earlier batches: kinet's .venv unchanged, KINET_PROJECT
# set, caches on scratch, nothing written to $HOME or the kinet tree.
# Usage: sbatch --account=m4790 --constraint=gpu --qos=debug --nodes=1 --ntasks=1 \
#   --cpus-per-task=32 --gpus-per-node=1 --time=00:30:00 run_ensemble_job.sh ARGS_FILE
set -uo pipefail
ARGS_FILE=${1:?args file required}
P=/pscratch/sd/k/khegazy/kinet_datasets/_provenance/shear_layer_ensemble
source /pscratch/sd/k/khegazy/kinet_datasets/_work/env.sh
nplace="${SLURM_CPUS_PER_TASK:-32}"
export OMP_NUM_THREADS="${nplace}" OMP_PLACES=threads OMP_PROC_BIND=spread
wd=$W/_work/shear_layer_ensemble/job_${SLURM_JOB_ID}
mkdir -p "$wd" && cd "$wd" || exit 1
echo "job ${SLURM_JOB_ID} on $(hostname) start $(date -Is)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
echo "kinet $(git -C "$KINET_PROJECT" rev-parse HEAD) $(git -C "$KINET_PROJECT" branch --show-current)"
status=0; i=0
while read -r line; do
    [ -z "${line}" ] && continue
    [[ "${line}" == \#* ]] && continue
    i=$((i + 1))
    # shellcheck disable=SC2086
    cmd=(python -u -B "$P/ensemble_driver.py" ${line})
    printf '%q ' "${cmd[@]}" > "command_${i}.txt"; echo >> "command_${i}.txt"
    t0=$(date +%s.%N)
    "${cmd[@]}" > "log_${i}.txt" 2>&1
    rc=$?
    t1=$(date +%s.%N)
    echo "invocation ${i} rc=${rc} wall_s=$(python -c "print(round(${t1}-${t0},2))") args: ${line}" | tee -a "$wd/invocations.txt"
    [ ${rc} -ne 0 ] && status=${rc}
done < "${ARGS_FILE}"
echo "job end $(date -Is)"
exit ${status}
