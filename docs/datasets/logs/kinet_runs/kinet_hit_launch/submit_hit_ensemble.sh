#!/bin/bash
# Run an ensemble of hit_scaling simulations on a Perlmutter GPU queue (debug by default).
#
# Each job takes one node and runs independent simulations, one per GPU (4 at once),
# each with its own random seed for the initial turbulent field. Every simulation saves
# every --save-every-th step (10), macroscopic fields only (no F or Feq). The driver
# keeps up to --max-queued jobs submitted (5, the debug QOS limit) until every case has
# --target finished simulations, then exits.
#
# Usage:
#   bash slurm_scripts/submit_hit_ensemble.sh [--target N | --seeds s1,s2,...]
#       [--cases a,b,c] [--sims-per-gpu K] [--save-every S] [--qos QOS]
#       [--time HH:MM:SS] [--max-queued J] [--hold-while CMD] [--ledger DIR]
#       [--poll SECONDS] [--max-failures M] [--dry-run] [-- <extra Hydra overrides>]
#
# --hold-while CMD: submit nothing at a poll where the shell command CMD succeeds (for
# example, while too many finished runs wait on scratch to be downsampled).
#
# Seed: the wall-clock time a simulation starts on the compute node, in microseconds
# since the epoch, with the GPU index (0-3) appended as a last digit so the four
# simulations a job starts together never share a seed. --seeds instead runs exactly
# those seeds for every case (the target is then their number); a job is handed only
# seeds that are neither finished nor in flight, so a failed one is rerun with its own
# seed. The seed is recorded in the simulation's status file and, through the identity
# key, names its output directory.
#
# Ledger: <ledger>/<case>/<job>_gpu<g>_<k>.tsv holds one line per simulation,
# "seed job gpu start end exit run_dir"; exit is "running" until the simulation ends.
# A finished simulation has exit 0. The driver reads the ledger and squeue only, so it
# can be stopped and restarted at any time.

set -euo pipefail

PROJ_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GPUS_PER_NODE=4

usage() {
    sed -n '2,30p' "$0" >&2
}

# --- Inside the allocation: run n_sims simulations of one case, 4 at a time --------
# seeds is "-" (seed each simulation from the clock) or a comma list of n_sims seeds.
run_job() {
    local case_id=$1 n_sims=$2 sims_per_gpu=$3 ledger=$4 save_every=$5 seeds=$6
    shift 6
    [ "${1:-}" = "--" ] && shift
    local extra=("$@")
    local fixed_seeds=()
    if [ "${seeds}" != "-" ]; then
        IFS=',' read -r -a fixed_seeds <<<"${seeds}"
    fi

    # Slurm runs a spooled copy of this script, so $0 does not locate the repo.
    cd "${SLURM_SUBMIT_DIR:?run_job runs inside a Slurm job}"
    # Single-process HDF5 runs need only the venv (torch and h5py bring their own
    # CUDA and HDF5), not the MPI/ADIOS2 modules of perlmutter/export_env.sh.
    # shellcheck disable=SC1091
    source .venv/bin/activate
    export HDF5_USE_FILE_LOCKING=FALSE
    export OMP_NUM_THREADS=$((SLURM_CPUS_PER_TASK / GPUS_PER_NODE))
    local case_dir="${ledger}/${case_id}"
    mkdir -p "${case_dir}/logs"

    local gpu
    for gpu in $(seq 0 $((GPUS_PER_NODE - 1))); do
        (
            local k idx seed name status run_dir start rc
            for k in $(seq 0 $((sims_per_gpu - 1))); do
                idx=$((k * GPUS_PER_NODE + gpu))
                [ "${idx}" -ge "${n_sims}" ] && break
                seed="${fixed_seeds[idx]:-$(date +%s%6N)${gpu}}"
                name="${SLURM_JOB_ID}_gpu${gpu}_${k}"
                status="${case_dir}/${name}.tsv"
                run_dir="outputs/hit_scaling/${case_id}/simulate/ensemble/${name}_seed${seed}"
                start=$(date -Iseconds)
                printf '%s\t%s\t%s\t%s\t-\trunning\t%s\n' \
                    "${seed}" "${SLURM_JOB_ID}" "${gpu}" "${start}" "${run_dir}" >"${status}"
                rc=0
                CUDA_VISIBLE_DEVICES=${gpu} python -m kinet.apps.simulate \
                    "case=hit_scaling/${case_id}" task=simulate launch.device=cuda \
                    distributed.is_distributed=false \
                    "case.initial_conditions.random_seed=${seed}" \
                    "io.save_every_n=${save_every}" \
                    io.record_distributions=false io.record_equilibria=false \
                    "hydra.run.dir=${run_dir}" \
                    "${extra[@]}" >"${case_dir}/logs/${name}.log" 2>&1 || rc=$?
                printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "${seed}" "${SLURM_JOB_ID}" \
                    "${gpu}" "${start}" "$(date -Iseconds)" "${rc}" "${run_dir}" >"${status}"
            done
        ) &
    done
    wait
}

if [ "${1:-}" = "--run-job" ]; then
    shift
    run_job "$@"
    exit 0
fi

# --- Driver: keep the queue full until every case has --target simulations ---------
target=100
seeds=""
cases="Re-12p5k_Ma-1en1_2d,Re-25k_Ma-1en1_2d,Re-50k_Ma-1en1_2d"
sims_per_gpu=6 # ~3 min each on an A100 (measured): ~18 of the 30 debug minutes
save_every=10
qos=debug
time_limit="00:30:00"
max_queued=5 # Perlmutter GPU debug QOS: MaxSubmitPU
hold_while=""
ledger="${PROJ_ROOT}/outputs/hit_scaling/ensemble_ledger"
poll=60
max_failures=12
dry_run=0
extra=()
while [ "$#" -gt 0 ]; do
    case "$1" in
        --target) target=${2:?}; shift 2 ;;
        --seeds) seeds=${2:?}; shift 2 ;;
        --cases) cases=${2:?}; shift 2 ;;
        --sims-per-gpu) sims_per_gpu=${2:?}; shift 2 ;;
        --save-every) save_every=${2:?}; shift 2 ;;
        --qos) qos=${2:?}; shift 2 ;;
        --time) time_limit=${2:?}; shift 2 ;;
        --max-queued) max_queued=${2:?}; shift 2 ;;
        --hold-while) hold_while=${2:?}; shift 2 ;;
        --ledger) ledger=$(realpath -m "${2:?}"); shift 2 ;;
        --poll) poll=${2:?}; shift 2 ;;
        --max-failures) max_failures=${2:?}; shift 2 ;;
        --dry-run) dry_run=1; shift ;;
        --) shift; extra=("$@"); break ;;
        *) echo "Unknown option '$1'" >&2; usage; exit 2 ;;
    esac
done
IFS=',' read -r -a case_list <<<"${cases}"
for case_id in "${case_list[@]}"; do
    [ -f "${PROJ_ROOT}/experiments/hit_scaling/${case_id}.yaml" ] || {
        echo "No case experiments/hit_scaling/${case_id}.yaml" >&2
        exit 2
    }
done
seed_list=()
if [ -n "${seeds}" ]; then
    IFS=',' read -r -a seed_list <<<"${seeds}"
    target=${#seed_list[@]}
fi
cd "${PROJ_ROOT}" # the job's SLURM_SUBMIT_DIR, from which it finds the repo
per_job=$((GPUS_PER_NODE * sims_per_gpu))
tag=$(basename "${ledger}")
mkdir -p "${ledger}/slurm"

# Count a case's ledger entries into done_n, inflight and failed_n: done has exit 0; in
# flight is "queued" or "running" in a job still in the queue; failed is a nonzero exit,
# or "queued"/"running" in a job that has left the queue (it died, or hit the time
# limit). claimed lists the seeds of the done and in-flight entries.
count_status() {
    local case_id=$1 live_jobs=$2 f seed job gpu start end rc rest
    done_n=0 inflight=0 failed_n=0 claimed=" "
    shopt -s nullglob
    for f in "${ledger}/${case_id}"/*.tsv; do
        IFS=$'\t' read -r seed job gpu start end rc rest <"${f}"
        if [ "${rc}" = 0 ]; then
            done_n=$((done_n + 1))
            claimed+="${seed} "
        elif { [ "${rc}" = queued ] || [ "${rc}" = running ]; } &&
            [[ " ${live_jobs} " == *" ${job} "* ]]; then
            inflight=$((inflight + 1))
            claimed+="${seed} "
        else
            failed_n=$((failed_n + 1))
        fi
    done
}

while true; do
    # Slurm reports a GPU job submitted with --qos=<q> under QOS "gpu_<q>".
    queue=$(squeue -h -u "${USER}" -o '%i %q' |
        awk -v q="${qos}" '$2 == q || $2 == "gpu_" q {print $1}')
    n_queued=$(grep -c . <<<"${queue}" || true)
    live_jobs=$(tr '\n' ' ' <<<"${queue}")
    held=0
    if [ -n "${hold_while}" ] && bash -c "${hold_while}"; then
        held=1
        echo "$(date -Iseconds) holding submissions: ${hold_while}"
    fi
    all_done=1
    for case_id in "${case_list[@]}"; do
        count_status "${case_id}" "${live_jobs}"
        need=$((target - done_n - inflight))
        echo "$(date -Iseconds) ${case_id}: done=${done_n} failed=${failed_n} in_flight=${inflight} need=${need}"
        if [ "${failed_n}" -gt "${max_failures}" ]; then
            echo "${case_id}: ${failed_n} failed simulations (> ${max_failures}); stopping. See ${ledger}/${case_id}/logs" >&2
            exit 1
        fi
        [ $((done_n)) -lt "${target}" ] && all_done=0
        while [ "${held}" -eq 0 ] && [ "${need}" -gt 0 ] && [ "${n_queued}" -lt "${max_queued}" ]; do
            n=$((need < per_job ? need : per_job))
            # The seeds this job runs: the first n not yet claimed, or "-" (clock seeds).
            job_seeds=()
            for s in "${seed_list[@]}"; do
                if [ "${#job_seeds[@]}" -lt "${n}" ] && [[ "${claimed}" != *" ${s} "* ]]; then
                    job_seeds+=("${s}")
                fi
            done
            seeds_arg=$(IFS=','; echo "${job_seeds[*]:--}")
            cmd=(sbatch --parsable --hold --qos="${qos}" --constraint=gpu --account="${SLURM_ACCOUNT:-m4790}"
                --nodes=1 --ntasks=1 --cpus-per-task=128 --gpus-per-node="${GPUS_PER_NODE}"
                --time="${time_limit}" --job-name="hitens.${tag}.${case_id}.${n}"
                --output="${ledger}/slurm/%j.out" --export=ALL
                "$0" --run-job "${case_id}" "${n}" "${sims_per_gpu}" "${ledger}"
                "${save_every}" "${seeds_arg}" -- "${extra[@]}")
            if [ "${dry_run}" -eq 1 ]; then
                printf '%q ' "${cmd[@]}"; printf '\n'
                exit 0
            fi
            if ! job=$("${cmd[@]}"); then
                echo "sbatch refused the job; retrying at the next poll" >&2
                break
            fi
            # One "queued" entry per planned simulation, so a job that dies before
            # starting them is counted as failed rather than forgotten. The job is
            # held until these exist, so they never overwrite a "running" entry.
            mkdir -p "${ledger}/${case_id}"
            for idx in $(seq 0 $((n - 1))); do
                printf -- '%s\t%s\t%s\t-\t-\tqueued\t-\n' "${job_seeds[idx]:--}" "${job}" \
                    $((idx % GPUS_PER_NODE)) \
                    >"${ledger}/${case_id}/${job}_gpu$((idx % GPUS_PER_NODE))_$((idx / GPUS_PER_NODE)).tsv"
                claimed+="${job_seeds[idx]:-} "
            done
            scontrol release "${job}"
            echo "submitted job ${job} for ${case_id} (${n} simulations, seeds ${seeds_arg})"
            need=$((need - n))
            n_queued=$((n_queued + 1))
        done
    done
    if [ "${all_done}" -eq 1 ]; then
        echo "All cases have ${target} finished simulations; ledger in ${ledger}"
        exit 0
    fi
    sleep "${poll}"
done
