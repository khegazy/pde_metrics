#!/bin/bash
# Downsample finished hit_scaling simulations and archive them, as they finish.
#
# Watches the ledger of a submit_hit_ensemble.sh campaign whose rollouts are written to
# scratch. For every finished simulation it runs, in a Slurm job (up to --runs-per-job
# at once on one node):
#   1. coarse-grain the rollout to the --grid tier (space and time by the same factor,
#      mesoscopic/momentum_time_scale and mesoscopic/stability_scale left out);
#   2. check the tier (one frame per coarse step, a finite last frame);
#   3. copy the run directory without tiers/full to <archive>/<case>/<identity key>;
#   4. check the copied tier has the source's size, then delete the scratch run.
# The driver exits once --target runs are archived.
#
# Usage:
#   bash slurm_scripts/downsample_hit_ensemble.sh --sim-ledger DIR --case CASE
#       --archive DIR --target N [--grid 256] [--save-every 1] [--runs-per-job 4]
#       [--qos debug] [--time 00:30:00] [--max-queued 2] [--ledger DIR]
#       [--poll 60] [--max-failures 4] [--dry-run] -- <the simulations' overrides>
#
# The overrides after -- must be those the simulations ran with (grid, temporal grid,
# paths.data_root): coarse_grain composes the same case from them, so it finds the run
# by its identity key.
#
# Ledger: <ledger>/<seed>.tsv holds "seed job start end exit archive_dir"; exit is
# "queued" or "running" until the run is archived (0) or fails.

set -euo pipefail

PROJ_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IGNORED="mesoscopic/momentum_time_scale,mesoscopic/stability_scale"

usage() {
    sed -n '2,25p' "$0" >&2
}

# --- Inside the allocation: downsample, check, archive and delete each seed's run ----
# One seed's run, every step checked explicitly: errexit is off in a function whose
# status is tested, and nothing may be deleted after a failed step. Prints the archive
# directory last.
archive_run() {
    local case_id=$1 sim_ledger=$2 ledger=$3 archive=$4 grid=$5 save_every=$6 seed=$7
    shift 7
    local status rollout sim_dir key dest tier
    status=$(grep -l -P "^${seed}\t[^\t]*\t[^\t]*\t[^\t]*\t[^\t]*\t0\t" \
        "${sim_ledger}/${case_id}"/*.tsv | head -1) || return 1
    rollout=$(grep -m1 -o "/[^ ]*/tiers/full/rollout.h5" \
        "${sim_ledger}/${case_id}/logs/$(basename "${status}" .tsv).log") || return 1
    sim_dir=$(dirname "$(dirname "$(dirname "${rollout}")")")
    key=$(basename "${sim_dir}")
    dest="${archive}/${case_id}/${key}"
    tier="${sim_dir}/tiers/${grid}/rollout.h5"
    echo "seed ${seed}: ${sim_dir} -> ${dest}"
    [ ! -e "${dest}" ] || { echo "refusing: ${dest} exists"; return 1; }

    python -m kinet.apps.coarse_grain "case=hit_scaling/${case_id}" \
        task=coarse_grain "task.targets_spatial=[${grid},${grid}]" \
        "task.ignore_datasets=[${IGNORED}]" \
        "case.initial_conditions.random_seed=${seed}" "io.save_every_n=${save_every}" \
        io.record_distributions=false io.record_equilibria=false \
        launch.device=cpu "hydra.run.dir=${ledger}/hydra/${seed}" "$@" || return 1

    python - "${tier}" <<'PY' || return 1
import sys

import h5py
import numpy as np

with h5py.File(sys.argv[1], "r") as f:
    n_steps = f["time/time_index"].shape[0]
    velocity = f["observables/velocity"]
    if velocity.shape[2] != n_steps:
        sys.exit(f"tier has {velocity.shape[2]} frames for {n_steps} coarse steps")
    if not np.isfinite(velocity[0, :, -1]).all():
        sys.exit("tier's last frame is not finite")
    print(f"tier ok: {n_steps} coarse steps, last frame finite")
PY
    rsync -a --exclude "tiers/full/" "${sim_dir}/" "${dest}/" || return 1
    [ "$(stat -c %s "${tier}")" = "$(stat -c %s "${dest}/tiers/${grid}/rollout.h5")" ] ||
        { echo "archived tier size differs from ${tier}"; return 1; }
    # Delete only a run directory on scratch named by an identity key.
    [[ "${sim_dir}" == "${SCRATCH:?}"/* && "${key}" =~ ^[0-9a-f]{6}$ ]] ||
        { echo "refusing to delete ${sim_dir}"; return 1; }
    rm -rf "${sim_dir}" || return 1
    echo "archived ${dest}; deleted ${sim_dir}"
}

run_job() {
    local case_id=$1 sim_ledger=$2 ledger=$3 archive=$4 grid=$5 save_every=$6 seeds=$7
    shift 7
    [ "${1:-}" = "--" ] && shift
    local extra=("$@")
    cd "${SLURM_SUBMIT_DIR:?run_job runs inside a Slurm job}"
    # shellcheck disable=SC1091
    source .venv/bin/activate
    export HDF5_USE_FILE_LOCKING=FALSE
    mkdir -p "${ledger}/logs"
    local seed
    IFS=',' read -r -a seed_arr <<<"${seeds}"
    for seed in "${seed_arr[@]}"; do
        (
            local start rc=0 log dest
            start=$(date -Iseconds)
            log="${ledger}/logs/${seed}.log"
            printf '%s\t%s\t%s\t-\trunning\t-\n' "${seed}" "${SLURM_JOB_ID}" "${start}" \
                >"${ledger}/${seed}.tsv"
            archive_run "${case_id}" "${sim_ledger}" "${ledger}" "${archive}" "${grid}" \
                "${save_every}" "${seed}" "${extra[@]}" >"${log}" 2>&1 || rc=$?
            dest=$(grep -o -m1 "^archived [^;]*" "${log}" | cut -d' ' -f2) || dest="-"
            printf '%s\t%s\t%s\t%s\t%s\t%s\n' "${seed}" "${SLURM_JOB_ID}" "${start}" \
                "$(date -Iseconds)" "${rc}" "${dest:--}" >"${ledger}/${seed}.tsv"
        ) &
    done
    wait
}

if [ "${1:-}" = "--run-job" ]; then
    shift
    run_job "$@"
    exit 0
fi

# --- Driver -----------------------------------------------------------------------
sim_ledger=""
case_id=""
archive=""
target=""
grid=256
save_every=1
runs_per_job=4
qos=debug
time_limit="00:30:00"
max_queued=2
ledger=""
poll=60
max_failures=4
dry_run=0
extra=()
while [ "$#" -gt 0 ]; do
    case "$1" in
        --sim-ledger) sim_ledger=$(realpath -m "${2:?}"); shift 2 ;;
        --case) case_id=${2:?}; shift 2 ;;
        --archive) archive=$(realpath -m "${2:?}"); shift 2 ;;
        --target) target=${2:?}; shift 2 ;;
        --grid) grid=${2:?}; shift 2 ;;
        --save-every) save_every=${2:?}; shift 2 ;;
        --runs-per-job) runs_per_job=${2:?}; shift 2 ;;
        --qos) qos=${2:?}; shift 2 ;;
        --time) time_limit=${2:?}; shift 2 ;;
        --max-queued) max_queued=${2:?}; shift 2 ;;
        --ledger) ledger=$(realpath -m "${2:?}"); shift 2 ;;
        --poll) poll=${2:?}; shift 2 ;;
        --max-failures) max_failures=${2:?}; shift 2 ;;
        --dry-run) dry_run=1; shift ;;
        --) shift; extra=("$@"); break ;;
        *) echo "Unknown option '$1'" >&2; usage; exit 2 ;;
    esac
done
[ -n "${sim_ledger}" ] && [ -n "${case_id}" ] && [ -n "${archive}" ] && [ -n "${target}" ] ||
    { usage; exit 2; }
[ -d "${sim_ledger}/${case_id}" ] || { echo "No ${sim_ledger}/${case_id}" >&2; exit 2; }
[ -d "${archive}/${case_id}" ] || { echo "No archive ${archive}/${case_id}" >&2; exit 2; }
ledger=${ledger:-${sim_ledger}/downsample}
cd "${PROJ_ROOT}" # the job's SLURM_SUBMIT_DIR, from which it finds the repo
mkdir -p "${ledger}/slurm"

while true; do
    # Slurm reports a GPU job submitted with --qos=<q> under QOS "gpu_<q>".
    live_jobs=" $(squeue -h -u "${USER}" -o '%i %q' |
        awk -v q="${qos}" '$2 == q || $2 == "gpu_" q {print $1}' | tr '\n' ' ') "
    n_queued=$(wc -w <<<"${live_jobs}")
    # Simulations finished, and this ledger's archived / in-flight / failed runs.
    shopt -s nullglob
    sim_done=$(cat /dev/null "${sim_ledger}/${case_id}"/*.tsv | awk -F'\t' '$6 == "0" {print $1}')
    n_sim_done=$(grep -c . <<<"${sim_done}" || true)
    archived=0 inflight=0 failed=0 claimed=" "
    for f in "${ledger}"/*.tsv; do
        IFS=$'\t' read -r seed job start end rc rest <"${f}"
        if [ "${rc}" = 0 ]; then
            archived=$((archived + 1)) claimed+="${seed} "
        elif [[ "${rc}" =~ ^(queued|running)$ && "${live_jobs}" == *" ${job} "* ]]; then
            inflight=$((inflight + 1)) claimed+="${seed} "
        else
            failed=$((failed + 1))
        fi
    done
    todo=()
    for s in ${sim_done}; do [[ "${claimed}" == *" ${s} "* ]] || todo+=("${s}"); done
    echo "$(date -Iseconds) simulated=${n_sim_done} archived=${archived} in_flight=${inflight} failed=${failed} waiting=${#todo[@]}"
    if [ "${failed}" -gt "${max_failures}" ]; then
        echo "${failed} failed runs (> ${max_failures}); stopping. See ${ledger}/logs" >&2
        exit 1
    fi
    if [ "${archived}" -ge "${target}" ]; then
        echo "All ${target} runs archived in ${archive}/${case_id}"
        exit 0
    fi
    # Fill a job before submitting it, unless no more simulations are coming.
    while [ "${#todo[@]}" -gt 0 ] && [ "${n_queued}" -lt "${max_queued}" ] &&
        { [ "${#todo[@]}" -ge "${runs_per_job}" ] || [ "${n_sim_done}" -ge "${target}" ]; }; do
        batch=("${todo[@]:0:${runs_per_job}}")
        todo=("${todo[@]:${#batch[@]}}")
        seeds_arg=$(IFS=','; echo "${batch[*]}")
        cmd=(sbatch --parsable --hold --qos="${qos}" --constraint=gpu
            --account="${SLURM_ACCOUNT:-m4790}" --nodes=1 --ntasks=1 --cpus-per-task=128
            --time="${time_limit}" --job-name="hitds.${case_id}.${#batch[@]}"
            --output="${ledger}/slurm/%j.out" --export=ALL
            "$0" --run-job "${case_id}" "${sim_ledger}" "${ledger}" "${archive}" "${grid}"
            "${save_every}" "${seeds_arg}" -- "${extra[@]}")
        if [ "${dry_run}" -eq 1 ]; then
            printf '%q ' "${cmd[@]}"; printf '\n'
            exit 0
        fi
        if ! job=$("${cmd[@]}"); then
            echo "sbatch refused the job; retrying at the next poll" >&2
            break
        fi
        # A "queued" entry per run, so a job that dies before starting is a failure.
        for s in "${batch[@]}"; do
            printf '%s\t%s\t-\t-\tqueued\t-\n' "${s}" "${job}" >"${ledger}/${s}.tsv"
        done
        scontrol release "${job}"
        echo "submitted job ${job}: ${seeds_arg}"
        n_queued=$((n_queued + 1))
    done
    sleep "${poll}"
done
