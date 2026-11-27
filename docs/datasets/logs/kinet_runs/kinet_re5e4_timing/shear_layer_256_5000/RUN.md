# Run shear_layer_256_5000
slurm_job_id: 62100814
sacct: 62100814|kinet-sl256|gpu_ss11|gpu_debug|m4790_g|2026-11-27T08:21:21|2026-11-27T08:22:13|2026-11-27T08:27:44|00:05:31|COMPLETED|0:0|nid002877
run_in_job: shear_layer_256_5000 rc=0 wall_s=265.12 start=1795796596.583947506 end=1795796861.706374722
kinet: d1cd353b83e994376d2c4476c968e82bca823f5f branch perf/cleanup
device: torch 2.15.0+cu132 cuda 13.2 NVIDIA A100-SXM4-40GB
gpu: NVIDIA A100-SXM4-40GB, 40960 MiB, 580.196.07
rollout: /pscratch/sd/k/khegazy/kinet_datasets/shear_layer_re5e4/doubly_periodic/shear_layer/856c2568/tiers/full/rollout.h5
rollout_bytes: 1842751978
working_directory: /pscratch/sd/k/khegazy/kinet_datasets/_work/shear_layer_256_5000
environment: source /pscratch/sd/k/khegazy/kinet_datasets/_work/env.sh   # kinet .venv, KINET_PROJECT, caches on scratch
command (run inside the working directory by run_kinet_job.sh):
  python -m kinet.apps.simulate task=simulate case=doubly_periodic/shear_layer case.discretization.spatial.grid=\[256\,256\] case.discretization.temporal.grid=5000 case.physics.parameters.reynolds=50000 io.save_every_n=10 io.record_distributions=false io.record_equilibria=false paths.data_root=/pscratch/sd/k/khegazy/kinet_datasets/shear_layer_re5e4 distributed.is_distributed=false distributed.is_slurm=true 
sbatch: sbatch --account=m4790 --constraint=gpu --qos=debug --nodes=1 --ntasks=1 --cpus-per-task=32 --gpus-per-node=1 --time=<limit> run_kinet_job.sh <runs file>
sbatch_exact: COLD_CACHE=1 sbatch --account=m4790 --constraint=gpu --qos=debug --nodes=1 --ntasks=1 --cpus-per-task=32 --gpus-per-node=1 --time=00:15:00 --job-name=kinet-sl256 --export=ALL,COLD_CACHE=1 run_kinet_job.sh runs_taskA.txt   # COLD_CACHE: a fresh torch.compile cache, so the warm-up is measured cold
