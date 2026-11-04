# A card's JSON files round every number to ten decimal places

**Category:** technical debt
**Priority:** medium
**Status:** open in part. Every card JSON is now written through `fmeval.cards.loader.json_records`, with exact floats; the committed JSONs still hold rounded values until each card is regenerated, which the final evidence pass of `update_metric_eval_principles` does. Delete this issue after that pass.

## Context

The numbers beside every card figure (`fmeval/cards/metric_figures.py::_panels`) and most of a
card's `fingerprint.json` (`fmeval/cards/evidence.py`: `_record`'s `axes`, `probes`, `profile`;
`generate`'s `companion` and `dominance`) go through `json.loads(frame.to_json(orient="records"))`.
`pandas.DataFrame.to_json` rounds to `double_precision=10` **decimal places**, not significant
figures, so a value below 5e-11 is written as 0.0 and a value of 4e-5 keeps six significant
figures. `docs/decisions.md` calls `fingerprint.json` and the `.json` beside each card figure
"the stable record", and the module docstring of `metric_figures.py` says the JSON carries the
renderer's data for a reader who cannot open the SVG.

## Evidence

- Measured with the repository's pandas: `pd.DataFrame({"a": [1.59e-15, 4.57e-11,
  1.2345678901234e-3]}).to_json(orient="records")` gives `0.0`, `0.0`, `0.0012345679`.
- `metrics/mse/_generated/response_along_time__dataset-forecast_re5e4__field-density__along-lead.json`
  (run `mse_1793794935`): 15 points read `"value": 0.0` (9 on vorticity, 5 on velocity), while the
  same predictions' errors on the card's table are 1.59e-15 to 1.08e-11 (the 256^2 forecasts and
  the first steps of the 128^2 ones). The SVG beside it draws them correctly.
- The same file's fingerprint record of that run, written before the fix in `_record`, read 0.0
  for the same predictions.

## What would settle it

Write every card JSON with exact floats: `frame.astype(object).where(frame.notna(),
None).to_dict(orient="records")`, as `_record` now does for `forecast`, in one shared helper used
by `_panels`, `_record` and `generate`. Every committed figure JSON and fingerprint then changes
in its trailing digits on the next regeneration, and no table on a card (which prints three
significant figures from the analysis frames, not from the JSON) changes. Do it in the final
evidence pass, when every card is regenerated anyway.
