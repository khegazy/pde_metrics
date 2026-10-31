# An axis is left out only when it is exactly constant, so round-off changes the value by a third

**Category:** technical debt
**Priority:** unset
**Status:** open. Found by the adversarial review of `tail_index`; it applies to
`increment_flatness` by the same rule.

## Context

Both single-field increment statistics average one value per (channel, spatial axis) pair and
leave a pair out when its statistic is undefined: `increment_flatness` when the pair's
increments are all exactly zero, `tail_index` when the (k+1)-th largest absolute increment is
exactly zero. Both statistics are scale-free, so a pair whose increments are round-off counts as
much as a pair carrying the field's real variation. The rule therefore jumps: a field constant
along one axis, and the same field with a negligible perturbation, score very differently.

## Evidence

A 64 x 32 channel that varies only along x (a sine plus 5% noise; the test below builds it)
scores `tail_index` 0.0937; adding Gaussian noise of standard deviation 1e-12 (the field's rms is
about 0.7) gives 0.1215, because the y-axis pair, now pure round-off, enters the mean with its own
scale-free estimate. On the same pair of fields `increment_flatness` moves from 2.60 to 2.82. On a
256 x 256 field of the same kind, `tail_index` moved from 0.0579 to 0.0780, and the adversarial
reviewer of `tail_index` measured 0.289 against 0.191 on another. The kinet fields are never constant along an axis, so the
evidence runs are unaffected; a doubly periodic shear flow, named in `CLAUDE.md` as a reference
case, is constant along one axis at its initial condition.

`metrics/tail_index/test_metric.py::test_round_off_on_a_constant_axis_does_not_change_the_value`
is marked `xfail(strict=True)` against this issue.

## What would settle it

A rule that makes a negligible pair negligible, chosen once for both metrics. Options:

1. **Weight each pair by the size of its increments** (for example by its increment rms), so a
   round-off axis has a round-off weight. This changes both metrics' numbers on every field with
   anisotropic increments, and so their evidence.
2. **Leave a pair out when its increments are below a fixed fraction of the field's fluctuation
   rms** (`ctx.fluctuation_rms`). A threshold fixed once in the evaluator, as `CLAUDE.md` requires,
   but with no source for its value.
3. **Pool all pairs into one sample.** Removes the jump, but measured on kinet velocity at frames
   2000 and 8000, the largest sqrt(n) values of the pooled sample then come from a single pair of
   the four, so the number reads one component along one axis.

No source fixes this; it is a convention shared by two bundles.

## Related

- `metrics/tail_index/card.md`, Limitations.
- `metrics/increment_flatness/metric.py`, the constant-axis rule.
- `issues/037-increment-flatness-has-no-damage-scale.md`, the constant field as a whole.
