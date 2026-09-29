# No generated block carries the one number a displacement-tolerant metric exists for

**Category:** technical debt
**Priority:** medium
**Status:** open

## Context

A card's `### Compared with the other metrics` block reports rank correlations against the
other metrics in the run and nothing else. For the pointwise family that is enough, because
what those metrics are being compared on is whether they order the ladder. For a metric
added specifically to be *gentler* than a pointwise norm on displacement, it is the wrong
statistic: ordering is not the claim, magnitude is, and two metrics can order every
degradation identically while charging wildly different amounts for the same one.

`AGENTS.md` already records the general form of this trap — MAE and MSE correlate at 0.995
across the ladder yet differ by 47x in displacement damage at an eighth of a cell — so the
gap is known in the abstract. What this issue records is that the card machinery makes it
impossible to state the corresponding number *for a new metric* inside the protection that
generated blocks provide. `issues/032` says hand-carried numbers in prose go stale without
anything noticing; the two together mean the headline measurement for `h_minus_one` can
either be unprotected or be absent, and it is currently absent.

## Evidence

From `results/comparison_1789627307` (dataset `kinet_re5e4`, start 2000, reduction 50, 161
frames, analysis grid 256), median damage by level, computed with
`fmeval.analysis.normalisation` and `add_damage`:

`translate_x`, vorticity:

| level | h_minus_one | mae | rmse | nrmse | mse |
|---|---|---|---|---|---|
| 1 | 0.0173 | 0.1724 | 0.1673 | 0.1688 | 0.0280 |
| 2 | 0.0342 | 0.3063 | 0.2982 | 0.3041 | 0.0889 |
| 3 | 0.0664 | 0.4529 | 0.4319 | 0.4469 | 0.1866 |
| 4 | 0.1260 | 0.5815 | 0.5365 | 0.5550 | 0.2879 |
| 5 | 0.2315 | 0.6901 | 0.6838 | 0.7020 | 0.4676 |

`translate_subpixel`, vorticity, level 1 (the smallest shift tested): `h_minus_one` 0.0022
against `mae` 0.0225 — a factor of 10.

The same comparison on the other two fields shows almost no separation at all:
`translate_subpixel` level 1 gives `h_minus_one` 0.0031 against `mae` 0.0033 on density,
and 0.0013 against 0.0016 on velocity.

That field dependence is the substantive finding, and it is consistent with the
calibration the same run recorded: the characteristic scale is 32.5 cells for vorticity
against 138.7 for density and 188.8 for velocity. A shift of a fixed number of cells puts
its error at high wavenumber on the field that varies quickly and at low wavenumber on the
fields that do not, and dividing by the wavenumber only helps in the first case.

Meanwhile the rank correlations in the generated block are 0.943 / 0.942 / 0.942 / 0.924
against `nrmse` / `rmse` / `mse` / `mae` — high enough that a reader looking only at the
generated blocks would reasonably conclude the metric is redundant, which is the opposite
of what the damage table shows.

## What would settle it

A generated block, filled by `python -m fmeval.cards evidence`, holding per-level damage
for this metric beside the other metrics in the same run, at least for the degradation
families where the comparison is the point. The analysis layer already computes every
number involved: `fmeval/analysis.py::add_damage` produces exactly the table above. What is
missing is a card block to put it in and a renderer to fill it.

Until that exists, a card that wants to make a magnitude claim has to either hand-carry the
numbers, which `issues/032` argues against, or point here, which is what
`metrics/h_minus_one/card.md` does.

## Not to be confused with

This is not a request to change `cross_metric_correlation`. That statistic is correct and
its generated caption already warns that a high correlation does not mean two metrics
agree. The gap is that nothing then supplies the number the warning implies a reader should
go and look at.
