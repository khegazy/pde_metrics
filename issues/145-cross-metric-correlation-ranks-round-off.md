# The cross-metric correlation ranks medians that differ only by round-off

**Category:** analysis
**Priority:** medium. The "Compared with the other metrics" table of every ensemble card reads
an ordering that does not exist.
**Status:** open; reproduced, not fixed.

## Context

`fmeval/analysis.py::cross_metric_correlation` takes, for one field, the median over frames of
each metric at every (degradation, level), and correlates metrics by Spearman's rank correlation
over those points. Ranking has no tolerance. Two medians that differ in the last bit of a float64
count as ordered, exactly as in the per-frame correlation before `_is_round_off` guarded it. The
same kind of defect, a statistic divided by round-off on the ensemble axes, is
[issue 111](111-damage-per-change-divides-by-round-off-on-ensemble-axes.md).

## Evidence

Run `comparison_1793812401` (`synthetic_ensemble`, density). The dispersion axes
(`spread_deflate`, `spread_inflate`) leave the member mean unchanged by construction, so a metric
of the member mean must give the same value at all eight strengths. Medians over frames, printed
to 17 significant digits:

| metric | values on the eight dispersion levels |
|---|---|
| `rmse` | 0.15594852721891944 at every level |
| `vrmse` | 0.24766230139876355 or 0.2476623013987635 |
| `max_error` | 0.63354431781970866 or 0.63354431781970877 |

`cross_metric_correlation(..., field="density")` then gives 0.907 between `rmse` and `vrmse` and
0.670 between `rmse` and `max_error`. All three are computed on the same unchanged mean, and the
two pairs differ only in how the last digits fall. Found by the readings agent for the ensemble
cards (`agent_logs/2026-11-03-update_metric_eval_principles/task-readings2-ensemble-shock.md`);
reproduced by the orchestrator.

## What would settle it

Treat medians that differ by less than `DEGENERATE_SPAN` times the metric's scale as tied before
ranking, with the scale taken as in `_is_round_off`. The change moves numbers in the
cross-metric tables of the ensemble cards, and possibly of others, so the cards need
regenerating after it, and a test should pin a constant-mean axis giving tied ranks.
