---
type: "MTR"
kind: "variant of max_error"
related: ["metrics/max_error", "metrics/mae", "docs/ideas/shock_geometry/shock_set_distance.md"]
seen_in: "agent's own"
doi: "none"
found_by: "max_error, 2026-10-30"
---

# MTR: A high quantile of the pointwise absolute error

## What it measures

The error that only a small, fixed fraction of the cells exceed, for example the 99th
percentile of the absolute error over cells. It keeps the maximum error's focus on the worst
part of the domain while depending on more than one cell.

## Definition

With $|e|_{(1)} \le \dots \le |e|_{(CN)}$ the sorted absolute errors over every channel and
cell,

$$
Q_p(f, g) = |e|_{(\lceil p\, C N \rceil)} \tag{1}
$$

for a fixed $p$ such as 0.99, where $p = 1$ recovers `max_error`. The formulation is my own by
analogy with the 95th-percentile Hausdorff distance that `docs/ideas/shock_geometry/
shock_set_distance.md` records as a robust replacement for the Hausdorff maximum; I found no
source that applies a quantile to the pointwise field error.

## Relation to existing work

Between `mae` (every cell weighted equally) and `max_error` (one cell weighted fully). The
quantile is fixed once, never tuned to the data, as the repository's threshold rule requires.

## How it could be tested

The existing ladder, `additive_noise` especially: a run would measure whether its
frame-to-frame consistency is better than `max_error`'s, and an analysis on grids of two sizes
would measure whether it depends less on the number of cells.

## Why it is helpful

The maximum error's first two pitfalls are that it rests on one cell and that the maximum of
noise grows with the number of cells. A fixed quantile is less sensitive to a single
outlier and to grid size while still reporting a worst-case-like number, which could make
it more stable as a panel member.

## References

None beyond the idea page named above; this is the agent's own proposal.
