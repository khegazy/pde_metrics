# Most ladder axes do not reach the anchor

**Category:** method
**Priority:** medium
**Status:** open

## Context

`saturation_level` is the first severity level at which a metric has moved 90% of the way from
clean to the anchor, the field's spatial mean (`judgements/001`). On the pinned run
`comparison_1793492906` (`kinet_re5e4`, 18 metrics, 161 frames) it is defined on 109 of the 540
ordinary rows, `severity_50` on 229 and `severity_10` on 383. Against the earlier translation
anchor it was defined on 12 of 360, so the change of anchor populated it partly but not for most
rows.

A blank saturation column carries no information, and a reader could mistake it for a
computation that failed.

It also means the ladder spans the informative range but does not bracket it. Whether that
matters depends on the intended use: for ranking models that differ mildly it is fine, and for
characterising a metric's full response it is not.

## What is needed

Either extend the severe end of the ladder -- larger translations, coarsening beyond 16,
noise above 0.5 -- or state in the report that saturation was not reached rather than leaving
the column blank. Probably both.

If the ladder is extended, note that the harshest smoothing approaches the anchor by
construction (a blur wide enough removes every fluctuation), so it stops being an independent
measurement and starts being a second estimate of the same quantity.

## Acceptance criteria

Either the saturation column is populated for most axes, or the report states explicitly
that the ladder does not reach saturation and why.

## Related

`saturation_level` in TEST_DESCRIPTION.md; `fmeval/analysis.py`.
