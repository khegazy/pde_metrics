# A forecast run stores no prediction's point set, and a forecast-only card has no forecast table

**Category:** analysis / report
**Priority:** medium. `persistence_wasserstein`'s first figure, the field's standard figure,
draws the target's diagram with no prediction beside it.
**Status:** open; reproduced, not fixed.

## Context

A run keeps per-cell maps and companion point sets only for the combinations
`configs/report/default.yaml` names under `error_map`: the last selected frame, on the reference
and the axes `translate_x`, `gaussian_blur` and `gaussian_impostor`. A run on `forecast_re5e4`
has one axis, `forecast`, which is not in that list. So it keeps the target's point set and no
prediction's. Separately, `fmeval.cards evidence` writes the forecast table and the
response-along-the-rollout figure in a card's `### On forecast_re5e4` subsection, which exists
only when the forecast run is not the card's primary run.

## Evidence

- `metrics/persistence_wasserstein/_generated/companion_points__field-vorticity.json` (run
  `comparison_1793811840`) holds 2000 points, all `variant: reference`, `frame_index: 59`; the
  density file holds 12, all the same. `persistence_distance`'s figure, from the turbulence run
  `comparison_1793846511`, holds the reference and four `gaussian_blur` levels.
- `persistence_wasserstein` cites only the forecast run (issue 144), so its card has no forecast
  table and no response-along-the-rollout figure. Its readings take their forecast numbers from
  `_generated/fingerprint.json` and say so. Found by the readings agent for the structure cards
  (`agent_logs/2026-11-03-update_metric_eval_principles/task-readings2-structure.md`); the
  first half reproduced by the orchestrator.

## What would settle it

1. Add `forecast` to `error_map.axes`, re-run `forecast_re5e4`, and regenerate the cards that
   cite it. Check the storage cost first: the forecast run has 60 frames on three grids.
2. Make `fmeval.cards evidence` write the forecast table and figure when the forecast run is
   the primary one too.
3. If issue 144 is settled by running `persistence_wasserstein` on the turbulence ladder, its
   primary run becomes `kinet_re5e4` and both halves stop affecting it, but not the next metric
   that runs only on the forecasts.
