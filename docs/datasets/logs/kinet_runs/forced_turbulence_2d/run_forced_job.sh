#!/bin/bash
# Run one kinet simulate run of the forced-turbulence dataset (BUILD_ORDER step 22) in a Slurm job.
#
# As _work/run_kinet_job.sh of the earlier batches (single rank, the same simulate line as
# kinet's slurm_scripts/submit_perlmutter.sh), but the code is the worktree of kinet branch
# datasets/forced-drag (env.sh beside this file), and the job prints which kinet ran and at
# which commit, so the log proves the worktree's code was used. Resuming: submit the same
# command again; kinet finds sim_checkpoints/ beside the rollout and continues it.
#
# Usage: sbatch --account=m4790 --constraint=gpu --qos=<debug|regular> --nodes=1 --ntasks=1 \
#   --cpus-per-task=32 --gpus-per-node=1 --time=<limit> run_forced_job.sh RUN_NAME DATA_ROOT OVERRIDES...
set -uo pipefail
name=${1:?run name}; data_root=${2:?data root}; shift 2
P=/pscratch/sd/k/khegazy/kinet_datasets/_provenance/forced_turbulence
source "$P/env.sh"
nplace="${SLURM_CPUS_PER_TASK:-32}"
export OMP_NUM_THREADS="${nplace}" OMP_PLACES=threads OMP_PROC_BIND=spread
export MKL_NUM_THREADS="${nplace}" OPENBLAS_NUM_THREADS="${nplace}" NUMEXPR_NUM_THREADS="${nplace}"
rundir="$W/_work/forced_turbulence/${name}"
mkdir -p "${rundir}" && cd "${rundir}" || exit 1
{
echo "job ${SLURM_JOB_ID:-none} on $(hostname) start $(date -Is)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
echo "kinet worktree $KINET_WORKTREE commit $(git -C "$KINET_WORKTREE" rev-parse HEAD) branch $(git -C "$KINET_WORKTREE" branch --show-current)"
echo "kinet worktree status (empty means clean):"; git -C "$KINET_WORKTREE" status --short
python -B -c "import kinet, torch, h5py, numpy; print('kinet.__file__', kinet.__file__); print('torch', torch.__version__, 'cuda', torch.version.cuda, 'h5py', h5py.__version__, 'numpy', numpy.__version__)"
} 2>&1 | tee -a "job_${SLURM_JOB_ID:-none}_header.txt"
set -f  # no globbing of overrides such as [1024,1024]
cmd=(python -m kinet.apps.simulate task=simulate "$@" paths.data_root="${data_root}"
     distributed.is_distributed=false distributed.is_slurm=true)
printf '%q ' "${cmd[@]}" > "command_${SLURM_JOB_ID:-none}.txt"; echo >> "command_${SLURM_JOB_ID:-none}.txt"
t0=$(date +%s.%N)
"${cmd[@]}" > "log_${SLURM_JOB_ID:-none}.txt" 2>&1
rc=$?
t1=$(date +%s.%N)
echo "${name} job=${SLURM_JOB_ID:-none} rc=${rc} wall_s=$(python -c "print(round(${t1}-${t0},2))")" | tee -a "$W/_work/forced_turbulence/runs.txt"
grep -E "stop_reason|Resuming|Traceback|Error" "log_${SLURM_JOB_ID:-none}.txt" | tail -5
echo "job end $(date -Is)"
exit ${rc}
