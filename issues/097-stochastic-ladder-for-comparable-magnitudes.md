# A stochastic ladder would make response magnitudes comparable across metrics

**Category:** method
**Priority:** none set
**Status:** open

## Context

Each degradation reports three measurements per metric: the trend (rank statistics on the
departure from clean), the reactivity (the change relative to clean, and the elasticity), and
the consistency (`severity_resolution`). Only the trend compares exactly across metrics. The
rank statistics are unchanged by any monotone re-expression of a metric, and the magnitudes are
not.

**Measured** on the pinned run `comparison_1790639359` (metric-evaluation design rev. 4, §2.1;
re-measured for this issue with the analysis of this change), MSE against RMSE, which carry identical information, over 36 (field, degradation) rows:
`rho` and `cliffs_delta_min` agree on 36 of 36, `elasticity` on 2 of 36, with RMSE's exactly half
of MSE's, and `severity_resolution` on 0 of 36, with a ratio between 0.31 and 1.16. A metric
raised to a power `p` has `p` times the elasticity, so no relative magnitude escapes this.

## The experiment that would change it

Several independent random draws per severity, rather than one damaged field per (frame,
severity). The spread of a metric across draws at one severity is then a noise scale in the
metric's own units, and a response divided by it is a signal-to-noise ratio. Such a ratio is
invariant to a monotone re-expression to first order, and it is defined for every metric, a
single-field quantity included. It needs stochastic operators (noise, the impostor) or a random
choice inside a deterministic one, and it multiplies the run's cost by the number of draws.

## Why it is not built

The design records it as the experiment that would make magnitudes comparable, with no priority
set. [004](004-independent-realizations.md), a second realisation of the flow, is the
physical-data counterpart.

## Related

Written with the harness change of the metric-evaluation design (rev. 4, §3.9), 2026-10-28.
