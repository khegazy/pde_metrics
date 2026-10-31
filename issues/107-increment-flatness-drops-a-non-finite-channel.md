# The increment flatness drops a non-finite channel without saying so

**Category:** technical debt
**Priority:** low — the harness's readers refuse non-finite fields, so only a direct caller or a
future degradation reaches it
**Status:** open. Reproduced, not fixed.

## Context

`increment_flatness` averages one flatness per (channel, axis) pair and leaves out any pair whose
flatness is not finite (`metrics/increment_flatness/metric.py`, `finite = [v for v in values if
np.isfinite(v)]`). That rule is there for an axis along which the field is constant, but it also
removes a pair holding a NaN or an infinity. A field with one bad cell in one channel is then
scored on its other channels, and nothing records that a channel was dropped.

Found by the agent that built `tail_index` (finding 015, 2026-10-30), whose metric had the same
behaviour and now raises `ValueError` on a non-finite field. `shock_set_distance` returns NaN.

## Evidence

A two-channel 64 x 64 standard-normal field (seed 0), then the same field with one cell of
channel 0 set to NaN:

```
python -c 'import numpy as np; from metrics.increment_flatness.metric import increment_flatness as f; ...'
clean, both channels   2.955426496085674
channel 1 alone        2.9417753772424016
NaN in channel 0       2.9417753772424016
```

## What would settle it

Refuse a non-finite field, as `tail_index` does, or return NaN, as `shock_set_distance` does; the
two bundles should then agree on one rule, written once where both can use it.

## Related

- `issues/103` (on pull request 23): the same pair-dropping rule is discontinuous when an axis is
  constant only up to round-off.
