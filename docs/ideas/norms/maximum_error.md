# Maximum pointwise error

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The maximum error, or $L^\infty$ error, is the largest absolute difference between the
prediction $\hat u$ and the reference $u$ anywhere in the domain:

$$
\| \hat u - u \|_{\infty} = \max_{\mathbf{x}} \, | \hat u(\mathbf{x}) - u(\mathbf{x}) |. \tag{1}
$$

On a grid the maximum runs over cells. The built pointwise controls
([mae](../../metrics/mae.md), [rmse](../../metrics/rmse.md),
[nrmse](../../metrics/nrmse.md)) average the error over the domain, so a single cell with a
large error contributes to them only in proportion to its share of the cells. The maximum
error reports that cell alone. It therefore detects a local excursion that an average
dilutes: a spurious spike, an overshoot beside a shock, or the first cell of a growing
instability. Tracked along a rollout, its growth is a worst-case stability diagnostic.

## Pitfalls

- It suffers the double penalty in its most extreme form. A sharp jump displaced by a single
  cell gives a maximum error equal to the full height of the jump, however small the
  displacement.
- It depends on one cell, so it is noisy and depends on the grid: a finer grid offers more
  cells to take the maximum over, and a remap onto cell averages lowers peaks.
- Like every pointwise error, it is meaningful only while the prediction is still aligned
  with the reference, and carries no information once the two have decorrelated.

## Rationale

*From the field guide; the team has not yet set a priority.* The guide recommends reporting
the maximum error beside the averaged pointwise norms, but only as a worst-case stability
diagnostic, because it is the one pointwise quantity that a single bad cell cannot hide
from. It costs one pass over the field.

## Keywords

maximum norm, $L^\infty$ error, worst-case error, rollout stability, overshoot.
