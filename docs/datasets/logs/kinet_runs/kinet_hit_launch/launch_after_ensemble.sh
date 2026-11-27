#!/bin/bash
# Start the Re-50k 512^2 x 200,000-step long run once the 97-run ensemble is archived.
cd /global/u2/k/khegazy/projects/pde/kinet
E=outputs/hit_scaling/ensemble512_ledger/downsample_driver.log
D=outputs/hit_scaling/long512_ledger
until grep -q -E "All 97 runs archived|stopping" "$E"; do sleep 120; done
if ! grep -q "All 97 runs archived" "$E"; then
    echo "$(date -Iseconds) ensemble downsampling stopped on failures; long run not started" >>"$D/launch.log"
    exit 1
fi
echo "$(date -Iseconds) ensemble archived; starting the long run" >>"$D/launch.log"
OV=("case.discretization.spatial.grid=[512,512]" case.discretization.temporal.grid=200000
    "paths.data_root=$SCRATCH/kinet_datasets")
bash slurm_scripts/submit_hit_ensemble.sh --cases Re-50k_Ma-1en1_2d --seeds 17940954423728020 \
    --sims-per-gpu 1 --save-every 1 --qos regular --time 04:00:00 --max-queued 1 \
    --ledger "$D" -- "${OV[@]}" >"$D/driver.log" 2>&1 &
bash slurm_scripts/downsample_hit_ensemble.sh --sim-ledger "$D" --case Re-50k_Ma-1en1_2d \
    --archive /global/cfs/cdirs/m4790/Data/neurde/hit_scaling --target 1 --runs-per-job 1 \
    --qos regular --time 04:00:00 -- "${OV[@]}" >"$D/downsample_driver.log" 2>&1 &
wait
echo "$(date -Iseconds) both drivers exited" >>"$D/launch.log"
