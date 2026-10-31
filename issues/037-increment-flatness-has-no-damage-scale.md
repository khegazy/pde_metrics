# The increment flatness has no damage scale: it is undefined on the anchor

**Category:** protocol
**Priority:** low — one metric, and its raw values and rank correlations are unaffected
**Status:** open only for `increment_flatness`. The rest of this issue — every translation-invariant
metric scoring the old translated anchor at its clean value — was resolved by making the field's
spatial mean the anchor (`judgements/001`).

## Context

Damage runs from the reference at 0 to the anchor at 1, and the anchor is the field's spatial mean
(`mean_field`). Every metric registered on 2026-10-29 has a finite span against it except
`increment_flatness`: the increments of a constant field are all zero, so the flatness, a fourth
moment over a squared second moment, is zero over zero.

## Evidence

On the pinned run `comparison_1793434653` (`kinet_re5e4`, start 2000, reduction 50, 161 frames),
`increment_flatness` has `value_anchor` NaN and `degenerate` true on density, velocity and
vorticity. Under the earlier translation anchor it was degenerate too, for a different reason: it
is a single-field statistic that a translation leaves unchanged.

The harness already handles this as designed: the impostor is reported as
`gaussian_impostor_relative`, a fraction of the metric's largest ladder response, and the
blindness bound is read on the same relative scale.

## What would settle it

Either of:

- **An independent realisation** (`issues/004`): the flatness of an unrelated field of the same
  statistics is defined, so a span would exist.
- **A per-metric convention for a constant field**, such as treating a vanishing second moment as
  flatness 0. This would be a definition chosen for this metric, so it needs a source or a
  judgement record.

## Related

- `issues/004-independent-realizations.md`
- `judgements/001-damage-anchor-is-the-spatial-mean.md`
