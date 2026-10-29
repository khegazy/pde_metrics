# Pooling across frames for a distributional estimate

**Category:** method
**Priority:** unset
**Status:** open, no customer yet

## Context

Every metric here returns one number per (frame, field, severity level), and the analysis reads
each frame as one sample. Some planned estimators need more samples than one frame holds. The
tails of an increment distribution are sparsely sampled by definition
(`docs/ideas/optimal_transport/gradient_pdf_w1.md`, "Pitfalls"). A tail index needs many
exceedances (`docs/ideas/distributional/tail_index_estimators.md`). An invariant measure is a
distribution over a whole trajectory ([080](080-invariant-measure-needs-long-rollouts.md)).
Pooling the samples of several frames would steady such an estimate, but then the number no
longer belongs to one frame. Every statistic of the analysis would see one point where it now
sees many, and the trend rule's per-frame departures and ranks would lose their unit.

## The contract, should a metric need it

A **series-level procedure**: it receives every variant of a frame window at once, as
`{variant_label: stack of frames}`, and returns one number per variant. The result rows keep
the existing key with the window's first frame as `frame_index`. The analysis then reads one
window as one sample, and windows must not overlap, or neighbouring samples would share frames
and look more independent than they are.

## Why it is not built

No metric needs it yet. Building the path before its first customer would be machinery with
no test (`AGENTS.md` §1, a helper needs two callers or a reason).

## What would unblock it

A metric whose estimate is unusable on one frame, measured, with the frame count its estimate
needs.

## Related

Written with the harness change of pull request #19, 2026-10-28.
The dynamics family ([094](094-dynamics-family-has-a-test-bed-but-no-rollout-input.md)) needs
the same kind of input.
