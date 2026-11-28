#!/bin/bash
# Run one or more kinet simulate runs in one Slurm job, from a working directory on scratch.
#
# Copy of /pscratch/sd/k/khegazy/kinet_datasets/_work/run_kinet_job.sh (the batch-2 job script)
# with its working folder moved to $W/_work/shocks_2d, so that this batch's run folders and job
# records do not mix with another batch's. It mirrors kinet's
# `slurm_scripts/submit_perlmutter.sh --run-job simulate 1 1` (single rank, the same OMP settings
# and the same `distributed.is_distributed=false distributed.is_slurm=true` flags), runs outside
# the kinet checkout with KINET_PROJECT set, and does not source kinet's export_env.sh.
#
# Usage: sbatch <flags> run_kinet_job.sh RUNS_FILE
#   RUNS_FILE: one run per line, "<run name> <data root> <hydra overrides...>".
# Submitted with: --account=m4790 --constraint=gpu --qos=debug --nodes=1 --ntasks=1
#   --cpus-per-task=32 --gpus-per-node=1 --time=...

set -uo pipefail
RUNS_FILE=${1:?runs file required}
WS=/pscratch/sd/k/khegazy/kinet_datasets/_work/shocks_2d
source "${WS}/env.sh"

nplace="${SLURM_CPUS_PER_TASK:-32}"
export OMP_NUM_THREADS="${nplace}" OMP_PLACES=threads OMP_PROC_BIND=spread
export MKL_NUM_THREADS="${nplace}" OPENBLAS_NUM_THREADS="${nplace}" NUMEXPR_NUM_THREADS="${nplace}"

echo "job ${SLURM_JOB_ID} on $(hostname) start $(date -Is)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
echo "kinet $(git -C "$KINET_PROJECT" rev-parse HEAD) $(git -C "$KINET_PROJECT" branch --show-current)"
echo "kinet status: $(git -C "$KINET_PROJECT" status --short | wc -l) changed paths"

set -f  # no globbing of overrides such as [256,256]
status=0
while read -r name data_root overrides; do
    [ -z "${name}" ] && continue
    [[ "${name}" == \#* ]] && continue
    rundir="${WS}/${name}"
    mkdir -p "${rundir}"
    cd "${rundir}" || exit 1
    # shellcheck disable=SC2086
    cmd=(python -m kinet.apps.simulate task=simulate ${overrides} paths.data_root=${data_root}
         distributed.is_distributed=false distributed.is_slurm=true)
    printf '%q ' "${cmd[@]}" > command.txt; echo >> command.txt
    t0=$(date +%s.%N)
    "${cmd[@]}" > log.txt 2>&1
    rc=$?
    t1=$(date +%s.%N)
    echo "${name} rc=${rc} wall_s=$(python -c "print(round(${t1}-${t0},2))") start=${t0} end=${t1}" | tee -a "${WS}/job_${SLURM_JOB_ID}_runs.txt"
    [ ${rc} -ne 0 ] && status=${rc}
done < "${RUNS_FILE}"
echo "job end $(date -Is)"
exit ${status}
