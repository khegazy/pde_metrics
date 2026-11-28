# Environment for the 960 x 240 double Mach reflection rerun (kinet main e67a1136e).
# kinet's own .venv, unchanged, with the code taken from a detached worktree of origin/main:
# PYTHONPATH puts the worktree ahead of the .venv's editable finder, which points at the main
# checkout. Nothing is written to $HOME or to a kinet tree.
source /global/u2/k/khegazy/projects/pde/kinet/.venv/bin/activate
export KINET_WORKTREE=/pscratch/sd/k/khegazy/kinet_worktrees/dmr_fine
export KINET_PROJECT=$KINET_WORKTREE
export PYTHONPATH=$KINET_WORKTREE
export PYTHONDONTWRITEBYTECODE=1
export W=/pscratch/sd/k/khegazy/kinet_datasets
export TORCHINDUCTOR_CACHE_DIR=$W/_cache/shocks_2d_main/inductor
export TRITON_CACHE_DIR=$W/_cache/shocks_2d_main/triton
export XDG_CACHE_HOME=$W/_cache/xdg MPLCONFIGDIR=$W/_cache/mpl
export WANDB_MODE=disabled WANDB_DIR=$W/_cache/wandb MLFLOW_TRACKING_URI=file://$W/_cache/mlruns
