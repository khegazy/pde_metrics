# A real forecast is a probe scored beside the anchor, not a ladder

**Date:** 2026-11-04. **Made by:** the agent building the forecast-pair reader (plan Part 2,
item 1). **Where:** `evaluate.py`, `fmeval/ladder.py` (`FORECAST_LEVEL`), `fmeval/pipeline.py`
(`prediction=`), `fmeval/report/plots.py` (`response_along_time`).

## The question

The analysis was built for a degradation ladder: several strengths of one operator per frame,
ranked within each frame. A real forecast gives one prediction per frame and an ordered lead
time across frames. How should its rows enter that analysis: as a ladder whose strength is the
lead time, as a probe, or outside the analysis altogether? And should the ladder still run on
the targets?

## The choice

1. **The prediction replaces the ladder.** On a dataset whose reader pairs every frame with a
   prediction, `evaluate.py` runs only the reference and the anchor entry (`analysis.anchor`,
   the field's spatial mean by default) on the targets, and scores the prediction as one more
   variant, labelled `forecast`.
2. **The forecast is a probe.** `FORECAST_LEVEL` is declared not ordinal, so it is listed among
   the run's probe labels and the analysis withholds every ordering statistic on it (`rho`, the
   separability, the thresholds), while `probe_summary` reports its median value and damage.
3. **The lead time is drawn, not ranked.** `response_along_time` draws the metric against
   `lead_time`, one line per forecast file.
4. **Runs at several resolutions are pooled only on one analysis grid.** The pipeline refuses a
   run whose frames remap to more than one grid.

## Evidence and reasoning

- Reading the lead time as a strength would make `rho` measure whether the error grows along
  the forecast, which is an expectation about the predictor, and the repository records no
  expected response per degradation (`docs/decisions.md`, "There is still no expectation per
  degradation"). It would also put the reference of each "level" at a different time, so the
  clean value the statistics pair against would change with the level.
- The machine-learning benchmarks score a rollout step by step: PDEBench computes its errors
  at every time step of a rollout (Takamoto et al. 2022, NeurIPS Datasets and Benchmarks Track,
  Sect. 3.3, and its code's `metric_func`, as read in `metrics/max_error/research_notes.md`).
  The plan also cites The Well (Ohana et al. 2024) for this; the agent did not open it. The
  figure drawn is that error against the prediction step.
- Keeping the anchor makes D defined on the forecast rows, and with the spatial mean as anchor
  it is the forecast's error as a fraction of the climatological forecast's, the reading of a
  skill score (Murphy 1988, *Monthly Weather Review* 116(12), 2417–2424; `judgements/001`).
  Without it the fallback anchor in `analysis._anchor` would pick the largest reference-level
  value, which for a single-field quantity is a meaningless scale.
- Running the full ladder on the targets as well would repeat the `kinet_re5e4` experiment on
  the forecasts' target frames, the first three of the $256^2$ run's before frame 2000, where
  that dataset's evidence window starts, and would mix two experiments in one run folder.
- On the smoke run `comparison_1793779575` (`analysis_grid.resolution=64`, `mse`, `nrmse`,
  `enstrophy`) the report renders the forecast figures and the report card, and skips every
  ladder figure with a stated reason; no ordering statistic is reported on a forecast row.

## What it changes

Only runs on `forecast_re5e4`. A ladder run is unchanged: `FORECAST_LEVEL` is added only when a
prediction is passed, and the per-frame remap computes the same factor as before.

## How to reverse it

To rank along the lead time, give the forecast rows a level per prediction step and make
`FORECAST_LEVEL` ordinal; the analysis would then compute `rho` across the steps of each forecast,
with the caveat above about the clean value. To run the ladder on the targets too, delete the
filter on `severity_levels` in `evaluate.py`.
