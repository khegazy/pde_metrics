# A mean-field anchor for metrics that cannot see the translated one

**Category:** method
**Priority:** medium — follows from `issues/037`, deferred by decision on 2026-09-30
**Status:** open

## Context

The damage scale is anchored on a translated copy of the reference, which every
translation-invariant metric scores at zero (`issues/037`). The anchor is now a declared run
setting (`analysis.anchor`, recorded as `anchor_label`), and the blindness bound and the impostor's
relative response already fall back to a metric's largest ladder response when the anchor is
degenerate. What does not exist is an anchor such metrics *can* see.

## Proposal

A degradation bundle `mean_field` that replaces every cell with the field's spatial mean: the
maximally smoothed field, every fluctuation removed.

```python
@degradation(name="mean_field", family="smoothing", severity_name="n/a", ordinal=False,
             preserves=("spatial_mean",))
def mean_field(x, severity, *, ctx):
    spatial = tuple(range(1, x.ndim))
    return np.broadcast_to(x.mean(axis=spatial, keepdims=True), x.shape).copy()
```

Selected per run with `analysis.anchor=mean_field` and
`degradation.ladder.mean_field.enabled=true`.

## The price

With this anchor D = 1 reads "as bad as a field with no structure at all", a weaker and different
statement than "as bad as an unrelated field", and damages from the two anchors are not comparable.
Every report and card would have to say which anchor a number was measured against, which
`anchor_source` already records.

## What it needs

The bundle, its card and exemplar panel (the panel needs the data), a `LADDERS` entry in the
contract test and a place in the passthrough skip set, a row in `TEST_DESCRIPTION.md` (the operator
count becomes 25), and a measured comparison of the two anchors on the pinned run for the metrics
that have both.
