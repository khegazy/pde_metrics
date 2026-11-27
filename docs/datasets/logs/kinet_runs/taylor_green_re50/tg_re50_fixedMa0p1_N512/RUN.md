# Run tg_re50_fixedMa0p1_N512
slurm_job_id: 62101401
sacct: 62101401|kinet-tgfix512|gpu_ss11|gpu_debug|m4790_g|2026-11-27T08:42:37|2026-11-27T08:48:46|2026-11-27T08:53:28|00:04:42|COMPLETED|0:0|nid003433
run_in_job: tg_re50_fixedMa0p1_N512 rc=0 wall_s=274.73 start=1795798132.859537052 end=1795798407.587300900
kinet: d1cd353b83e994376d2c4476c968e82bca823f5f branch perf/cleanup
device: 
gpu: NVIDIA A100-SXM4-40GB, 40960 MiB, 580.196.07
rollout: /pscratch/sd/k/khegazy/kinet_datasets/taylor_green_re50/taylor_green_vortex/Re-50k_Ma-1en1/ef4dc9f7/tiers/full/rollout.h5
rollout_bytes: 497599712
working_directory: /pscratch/sd/k/khegazy/kinet_datasets/_work/tg_re50_fixedMa0p1_N512
environment: source /pscratch/sd/k/khegazy/kinet_datasets/_work/env.sh   # kinet .venv, KINET_PROJECT, caches on scratch
command (run inside the working directory by run_kinet_job.sh):
  python -m kinet.apps.simulate task=simulate case=taylor_green_vortex/Re-50k_Ma-1en1 case.discretization.spatial.grid=\[512\,512\] case.discretization.temporal.grid=5632 case.physics.parameters.reynolds=50 case.physics.parameters.mach=0.1 io.save_every_n=176 io.record_distributions=false io.record_equilibria=false paths.data_root=/pscratch/sd/k/khegazy/kinet_datasets/taylor_green_re50 distributed.is_distributed=false distributed.is_slurm=true 
sbatch: sbatch --account=m4790 --constraint=gpu --qos=debug --nodes=1 --ntasks=1 --cpus-per-task=32 --gpus-per-node=1 --time=<limit> run_kinet_job.sh <runs file>
sbatch_exact: sbatch --account=m4790 --constraint=gpu --qos=debug --nodes=1 --ntasks=1 --cpus-per-task=32 --gpus-per-node=1 --time=00:15:00 --job-name=kinet-tgfix512 run_kinet_job.sh runs_tg_fixedmach_512.txt   # rerun of the run preempted at step 1 in job 62100815 (partial output deleted)
