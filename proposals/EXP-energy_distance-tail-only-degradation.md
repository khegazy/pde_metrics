---
type: EXP
kind: degradation
related: ["energy_distance", "increment_w1", "increment_flatness", "docs/ideas/distributional/tail_index_estimators.md"]
seen_in: "agent's own"
doi: "none"
found_by: "energy_distance, 2026-10-30"
---

# EXP: A degradation that damages only the tails of the increment distribution

## What the experiment is

A ladder that removes or weakens the rarest, most intense small-scale structures while leaving
the bulk of the field untouched. One concrete form (my own proposal, not from a source): find
the cells whose one-cell increment magnitude exceeds the q-th quantile of the reference's
increments, for q = 0.999, 0.99, 0.95, 0.9, and replace the field in a small neighbourhood of
each such cell by its local Gaussian-smoothed value. The severity is 1 - q, the fraction of the
increment distribution's tail that is attacked. A cleaner but less physical variant applies a
monotone compressive map only above the threshold, so the increments below it are exactly
preserved.

## What it tests

It changes, in a controlled and known way, the tail of the increment distribution and nothing
else: by construction the bulk below the threshold is unchanged, so a distribution metric that
follows this axis sees tails. Every current smoothing, filtering and noise axis changes bulk and
tail together, so no existing degradation can separate a metric that reads tails from one that
reads only the bulk. The energy distance's own algebra predicts it is weak on exactly this axis
(card Definition: a change confined to a few extreme increments costs 2/N of its transport cost
in the squared energy distance), and this experiment is the test that would show it on real data.

## Metrics it would test

energy_distance, increment_w1, increment_w1_by_separation, increment_flatness, and the planned
tail-index estimators (docs/ideas/distributional/tail_index_estimators.md), for which no
existing axis is a controlled test of what they measure.

## Why it is helpful

Intermittency, the rare intense structures, is the failure the project's north-star problem
cares about, and the panel currently has no axis that isolates it. Without it, a metric that
is blind to tails and one that is dominated by them both follow every smoothing axis, and the
evaluation cannot tell them apart.

## Cost and requirements

A new degradation bundle (repository code only, no data or licence), about one quantile, one
mask dilation and one Gaussian filter per field and frame. It must preserve the spatial mean,
which the local-smoothing form does only approximately; the compressive-map form needs care to
keep the field periodic and the increments consistent, since increments are differences and
cannot be edited independently. A degradation is added by a person or a degradation agent,
never by a metric agent (brief rule 8).

## References

None: this proposal is the agent's own. The quantitative motivation is the derivation on the
energy_distance card, pinned by metrics/energy_distance/test_metric.py.
