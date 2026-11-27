# No analysis reads whether a metric orders several candidate runs as their degradation does

**Category:** analysis
**Priority:** medium. The degraded isotropic reruns (`kinet_hit_re*_candidates`) exist to test
exactly this, and today each rerun is scored alone.
**Status:** open; not built (2026-11-27). Nothing in the repository computes it.

## Context

Step 20 of `dataset_specs/BUILD_ORDER.md` made kinet reruns of five isotropic realisations per
Reynolds number, each degraded on purpose in one stated way: a coarser grid (`grid128`,
`grid64`), a wrong viscosity (`re0.9`, `re0.75`, `re0.5`), plain BGK collision (`bgk`), and an
undegraded `control`. What they are known to show is an ordering, not a value: the control below
every degraded rerun, `grid64` above `grid128`, and the error growing as the Reynolds number falls
(`dataset_specs/05_initial_conditions_and_degraded_solver_runs.md`, Sects. 4.1 and 4.2). The
question a metric should answer here is whether its scores come out in that order, frame by
frame and realisation by realisation.

Each rerun is the `candidate` of the `kinet_raw` reader, scored by `evaluate.py` as one prediction
in place of the degradation ladder, so each kind of rerun is a run folder of its own. The
existing statistics do not span such folders:

- `fmeval.analysis.summarise_axes` reads the per-frame rank correlation over the levels of one
  degradation axis inside one run; a candidate run has one level, the prediction.
- `fmeval.analysis.forecast_by_lead` lists each prediction's value at each step, but its keys
  (`trajectory`, `param_resolution`, `start`, `lead_step`) do not tell apart two reruns on the
  same grid (`control`, `re0.9`, ..., `bgk` are all 256^2).
- `fmeval.analysis.observed_order` reads runs on several grids, so it covers `grid64` against
  `grid128` against the 256^2 control (as log2 of an error ratio, not an order of accuracy), but
  not the viscosity or collision axes.
- `fmeval.io.combine_runs` refuses members that differ in anything but the dataset, the shard or
  the trajectory; two kinds of rerun differ in `dataset.reader.candidate`.

## Evidence

The job's own check (`docs/datasets/logs/kinet_runs/isotropic_candidates/candidates_checks.txt`)
computes the three orderings for two distances, velocity and vorticity relative L2, and finds
them in 5 of 5 realisations at every evaluated frame at Re = 1.25e4 and 2.5e4. Scored through
`evaluate.py` on realisation `c95586` of Re = 2.5e4 at the 128 grid (runs `comparison_1795810088`
to `comparison_1795810094` under `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/step20_candidates/`),
`nrmse` on vorticity reads 1.1e-10 (control), 0.0118, 0.0340, 0.0920 (Re times 0.9, 0.75, 0.5),
0.168 (bgk) and 0.248 (grid128) at frame 150: the order holds there, but only a reader of the
seven folders side by side can say so.

## What would settle it

1. A function in `fmeval/analysis.py` that takes the rows of several candidate runs of one
   dataset, labelled by their candidate (from each folder's `config.yaml`, `dataset.reader.candidate`),
   and a declared order of the candidates, and returns per metric, field and frame the rank
   correlation between the declared order and the metric's values (oriented by the metric's
   measured direction, as `response_direction` does for an axis), with the median over frames and
   realisations and a block-bootstrap interval that never joins two realisations. This is the
   per-frame rank correlation the ladder already reports, applied across runs instead of levels.
2. A place for the declared orders: the dataset configuration cannot hold an unknown key
   (`build_job` refuses it), so either `DatasetConfig` gains one or the order is an argument.
3. A table in the report or card for it, once (1) exists.

Until then, each rerun's run folder is read alone, and the ordering is read by hand.
