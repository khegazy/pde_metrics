# 015 — A forecast's damage is scaled by its own frame, and the forecast is reported step by step

**Date:** 2026-11-04. **Made by:** the agent of task `harness-forecast-on-cards` (branch from
`update_metric_eval_principles`). **Where:** `fmeval/analysis.py` (`add_damage`,
`probe_summary`, `forecast_by_lead`), `fmeval/cards/evidence.py` (`lead_block`).
**Amends:** point 2 of [007](007-a-forecast-is-a-probe-scored-beside-the-anchor.md), which had
`probe_summary` report the forecast's median value and damage.

## The question that would have been asked

On a ladder run a metric's damage divides each departure by one span per (dataset, metric,
field): the median anchor value over every frame minus the median clean value. On
`forecast_re5e4` that span pools six forecasts (three runs, two starts) and ten prediction steps
each, and the run summarised the forecast by one median of value and damage over all sixty
frames. Should the damage scale on forecast rows be shared, per run, per forecast or per frame,
and should a pooled median of a forecast be reported at all?

## The choice

1. **Per frame.** A forecast row's damage is `(v - clean_f) / (anchor_f - clean_f)`, the
   anchor and clean values of its own frame; for a metric with a target value, its distance
   over the anchor's distance in the same frame. A frame whose own span is round-off (below
   `DEGENERATE_SPAN` times the largest value in the frame) or that has no anchor row gets no
   damage. Ladder rows are unchanged: the rule applies only to rows that carry a `lead_step`.
2. **No pooled forecast median.** `probe_summary` no longer reports `forecast_value`,
   `forecast_damage` or `forecast_nearest_level`. A forecast is reported at every prediction
   step of every forecast (`analysis.forecast_by_lead`): the value, the target's own value for
   a single-field quantity, and the damage. A card's subsection on a forecast run prints those
   as tables, one row per lead time and one column per forecast, beside the lead-time figure,
   and its fingerprint records every row.

## Evidence and reasoning

- **The anchor moves with the target along a forecast.** In run `mse_1793794935`
  (`forecast_re5e4`, `analysis_grid.resolution=64`), mean squared error's anchor on density, the
  target's own variance, ranges from 2.2e-7 to 4.9e-5 over the ten steps of each forecast that
  starts at t = 0, the flow developing from its initial state, and lies between 4.3e-5 and
  5.1e-5 along each forecast that starts at t = 1.13. On vorticity it falls from 9.7e-6 to
  5.8e-6 along the first and from 5.5e-6 to 4.3e-6 along the second. A span per run or per
  forecast would still pool the 220-fold range of the first, and turn a change of the target
  into a change of damage. Per frame is the only scale that does not.
- **It is how the forecasting benchmarks normalise.** PDEBench's nRMSE divides by the target's
  norm per sample, channel and time step, and The Well's VRMSE divides each field's error by the
  target's variance (`judgements/010`, which read both codes). With the default anchor, the
  field's spatial mean, a forecast row's damage under mean squared error is exactly the error
  over the target's population variance, the square of VRMSE without its N - 1 and its
  constant. On a ladder the frames are snapshots of one developed flow, whose anchor varies
  little, and the shared span keeps one scale per axis so that strengths are compared on one
  ruler; a forecast has no strengths to compare.
- **A pooled median describes no forecast.** On the same run the 256^2 forecast from t = 0
  has density MSE 1.59e-15 at its first step and 1.09e-07 at its tenth, and the 64^2 forecast
  from t = 0 has 5e-10 and 2.95e-06 (the card of `mse`, *On `forecast_re5e4`*). The repository
  states no expected response along the prediction step (`docs/decisions.md`, "There is still
  no expectation per degradation"), and the benchmarks plot the error against the step
  (PDEBench Sect. 4.3, Fig. 5; WeatherBench 2 Fig. 4; both as read for `metrics/rmse/card.md`),
  so the table and the figure are what is reported.

## What it changes

Runs on `forecast_re5e4` only. On the smoke run `mse_1793780539` the damage of the 180
forecast rows and the 180 anchor rows changed (the anchor rows are now exactly 1), with the
`damage_max` of the six forecast and anchor axes, and the three `forecast_*` columns left the
probe summary. On every ladder run the analysis is bitwise unchanged (refactor gate, commit
`ad4817e`).

## How to reverse it

To share the span again, delete the `lead_step` branch of `analysis.add_damage`. To report a
pooled forecast median again, delete the `predicted` filter in `analysis.probe_summary`; the
card's tables are independent of both.
