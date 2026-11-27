# Run tg_re50_fixedMa0p1_N256
slurm_job_id: 62100815
sacct: 62100815|kinet-tgfixMa|gpu_ss11|gpu_debug|m4790_g|2026-11-27T08:21:22|2026-11-27T08:22:13|2026-11-27T08:39:43|00:17:30|COMPLETED|0:0|nid003116
run_in_job: tg_re50_fixedMa0p1_N256 rc=0 wall_s=256.92 start=1795797074.888800885 end=1795797331.806382876
kinet: d1cd353b83e994376d2c4476c968e82bca823f5f branch perf/cleanup
device: torch 2.15.0+cu132 cuda 13.2 NVIDIA A100-SXM4-40GB
gpu: NVIDIA A100-SXM4-40GB, 40960 MiB, 580.196.07
rollout: /pscratch/sd/k/khegazy/kinet_datasets/taylor_green_re50/taylor_green_vortex/Re-50k_Ma-1en1/8b881515/tiers/full/rollout.h5
rollout_bytes: 124579730
working_directory: /pscratch/sd/k/khegazy/kinet_datasets/_work/tg_re50_fixedMa0p1_N256
environment: source /pscratch/sd/k/khegazy/kinet_datasets/_work/env.sh   # kinet .venv, KINET_PROJECT, caches on scratch
command (run inside the working directory by run_kinet_job.sh):
  python -m kinet.apps.simulate task=simulate case=taylor_green_vortex/Re-50k_Ma-1en1 case.discretization.spatial.grid=\[256\,256\] case.discretization.temporal.grid=2816 case.physics.parameters.reynolds=50 case.physics.parameters.mach=0.1 io.save_every_n=88 io.record_distributions=false io.record_equilibria=false paths.data_root=/pscratch/sd/k/khegazy/kinet_datasets/taylor_green_re50 distributed.is_distributed=false distributed.is_slurm=true 
sbatch: sbatch --account=m4790 --constraint=gpu --qos=debug --nodes=1 --ntasks=1 --cpus-per-task=32 --gpus-per-node=1 --time=<limit> run_kinet_job.sh <runs file>
sbatch_exact: sbatch --account=m4790 --constraint=gpu --qos=debug --nodes=1 --ntasks=1 --cpus-per-task=32 --gpus-per-node=1 --time=00:20:00 --job-name=kinet-tgfixMa run_kinet_job.sh runs_tg_fixedmach.txt
