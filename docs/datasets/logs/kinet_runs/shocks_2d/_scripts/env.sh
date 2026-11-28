# Environment for the kinet dataset runs: kinet's own .venv unchanged; nothing written to $HOME or the kinet tree.
source /global/u2/k/khegazy/projects/pde/kinet/.venv/bin/activate
export KINET_PROJECT=/global/u2/k/khegazy/projects/pde/kinet
export PYTHONDONTWRITEBYTECODE=1
export W=/pscratch/sd/k/khegazy/kinet_datasets
export TORCHINDUCTOR_CACHE_DIR=${CACHE_ROOT:-$W/_cache}/inductor
export TRITON_CACHE_DIR=${CACHE_ROOT:-$W/_cache}/triton
export XDG_CACHE_HOME=$W/_cache/xdg MPLCONFIGDIR=$W/_cache/mpl
export WANDB_MODE=disabled WANDB_DIR=$W/_cache/wandb MLFLOW_TRACKING_URI=file://$W/_cache/mlruns
