# Environment for the forced-turbulence kinet runs (BUILD_ORDER step 22).
# kinet's own .venv, unchanged, with the code taken from the worktree of branch
# datasets/forced-drag: PYTHONPATH puts the worktree ahead of the .venv's editable finder,
# which points at the main checkout. Nothing is written to $HOME or to a kinet tree.
source /global/u2/k/khegazy/projects/pde/kinet/.venv/bin/activate
export KINET_WORKTREE=/pscratch/sd/k/khegazy/kinet_worktrees/forced_drag
export KINET_PROJECT=$KINET_WORKTREE
export PYTHONPATH=$KINET_WORKTREE
export PYTHONDONTWRITEBYTECODE=1
export W=/pscratch/sd/k/khegazy/kinet_datasets
export TORCHINDUCTOR_CACHE_DIR=$W/_cache/forced_turbulence/inductor
export TRITON_CACHE_DIR=$W/_cache/forced_turbulence/triton
export XDG_CACHE_HOME=$W/_cache/xdg MPLCONFIGDIR=$W/_cache/mpl
export WANDB_MODE=disabled WANDB_DIR=$W/_cache/wandb MLFLOW_TRACKING_URI=file://$W/_cache/mlruns
