# The field gallery hides the cell a maximum map is about

**Category:** technical debt
**Priority:** low — the value is right in the stored map; only the figure misleads
**Status:** open.

## Context

`fmeval/report/plots.py::field_gallery` draws each metric's per-cell map for every stored
variant. It clips the colour scale at the 0.995 quantile of all the metric's panels pooled, and
captions every map "Per-cell contribution to the metric". Both fit a map whose reduction is a sum
or a mean. For a map reduced by `max` (`max_error`, pull request 25), the metric is the single
worst cell, which the clip can saturate, and no cell is a share of the metric.

Found in the adversarial review of `max_error` (2026-10-30); its card now tells readers to take
the value from the stored map.

## Evidence

In `results/max_error_1793355020` the worst cell is saturated in 9 of the 30 panels; on
vorticity, `gaussian_impostor_l1`, the panel's maximum is 2.55 times the colour scale's top.

## Options

1. Mark each panel's maximum cell.
2. Caption, and clip, by the metric's declared reduction.
3. Leave it, with the card's warning.
