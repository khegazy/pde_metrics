#!/bin/bash
# Run one or more kinet simulate runs in one Slurm job, from a working directory on scratch.
#
# Copy of /pscratch/sd/k/khegazy/kinet_datasets/_work/shocks_2d/run_kinet_job.sh with its working
# folder moved to $W/_work/shocks_2d/dmr_fine, whose env.sh runs the worktree of kinet main; the
# rest is unchanged. It mirrors kinet's
# `slurm_scripts/submit_perlmutter.sh --run-job simulate 1 1` (single rank, the same OMP settings
# and the same `distributed.is_distributed=false distributed.is_slurm=true` flags), runs outside
# the kinet checkout with KINET_PROJECT set, and does not source kinet's export_env.sh.
#
# Usage: sbatch <flags> run_kinet_job.sh RUNS_FILE [POST_FILE]
#   RUNS_FILE: one run per line, "<run name> <data root> <hydra overrides...>".
#   POST_FILE: optional; shell commands run one per line after every run has finished (the
#     coarse graining of the runs, CPU work kept in the GPU job), each logged with its exit code
#     and wall time to post_<job>.txt.
# Submitted with: --account=m4790 --constraint=gpu --qos=debug --nodes=1 --ntasks=1
#   --cpus-per-task=32 --gpus-per-node=1 --time=...

set -uo pipefail
RUNS_FILE=${1:?runs file required}
WS=/pscratch/sd/k/khegazy/kinet_datasets/_work/shocks_2d/dmr_fine
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
set +f
if [ -n "${2:-}" ]; then
    cd "${WS}" || exit 1
    while read -r line; do
        [ -z "${line}" ] && continue
        [[ "${line}" == \#* ]] && continue
        t0=$(date +%s.%N)
        bash -c "${line}"
        rc=$?
        t1=$(date +%s.%N)
        echo "rc=${rc} wall_s=$(python -c "print(round(${t1}-${t0},2))") ${line}" | tee -a "${WS}/post_${SLURM_JOB_ID}.txt"
        [ ${rc} -ne 0 ] && status=${rc}
    done < "$2"
fi
echo "job end $(date -Is)"
exit ${status}
