# The rank-correlation interval's fixed block length is half the estimated one

**Category:** method
**Priority:** medium — every recorded `rho_ci_lo`/`rho_ci_hi` depends on it
**Status:** open

## Context

`summarise_axes` resamples frames in moving blocks of a fixed 10 frames for the interval on `rho`,
and `TEST_DESCRIPTION.md` has always said the block length "should reflect the decorrelation time
of the flow and is currently a configured constant". The blindness bound added on 2026-09-30
estimates its block length per row with the Politis–White selector instead, on the frame-scaled
trace, which gives a measurement of that decorrelation time.

## Evidence

On `results/comparison_1790639359` (kinet_re5e4, start 2000, reduction 50, 161 frames), over the
360 ordinal (metric, field, degradation) rows: median estimated block length 21 frames, range 1 to
22, none at the quarter-length cap of 40. Blocks shorter than the decorrelation time make a
block-bootstrap interval too narrow, so the recorded `rho` intervals are probably narrower than the
data support. That is a conjecture about their width: it has not been measured by rerunning them.

A second property of the same interval: it draws from one generator shared across every group in
group order, so a group's interval depends on which groups ran before it, and adding a metric to a
comparison run moves every other metric's interval (`fmeval/analysis.py`, the comment above
`all_round_off` in `_block_bootstrap_rho`). The new statistics avoid this with a generator derived
from each group's keys.

## What would settle it

Rerun the interval with the estimated block length and a per-group generator on the pinned run and
compare widths; if they widen materially, switch, regenerate every card's evidence in the same
change, and say in the commit which intervals moved and by how much.
