# The dynamics family has a test bed but no rollout input

**Category:** deferred functionality
**Priority:** unset — the team has not set a priority for the dynamics ideas
**Status:** open. The test bed exists; the metrics wait on a stated convention and, for two of
them, on rollouts.

## Context

The dynamics ideas judge a prediction by how it evolves in time rather than by one snapshot:
the valid prediction time ([078](078-valid-prediction-time-needs-rollouts.md)), the temporal
autocorrelation and the decorrelation time read from it
([079](079-temporal-autocorrelation-needs-rollouts.md)), and the invariant measure
([080](080-invariant-measure-needs-long-rollouts.md)). Each issue records why the idea is not
built. This one records what now exists to test them and what the harness still lacks.

## What exists

- **`advecting_blobs`** (`fmeval/data/analytic.py`, page `docs/datasets/advecting_blobs.md`):
  three Gaussian density blobs, each moving at its own constant velocity on a periodic grid.
  Because the speeds differ, the blobs' relative positions change, so an error measured on it
  varies from frame to frame. A single blob would give the same error in every frame. It tests
  the machinery, not physics.
- **`per_unit_time: true`** on a ladder entry of an uncalibrated operator
  (`fmeval/ladder.py::build_ladder`). It multiplies the entry's severity by the frame's physical
  time. A translation then becomes a wrong advection speed, a displacement growing linearly in
  time, and noise an error growing in time. A calibrated operator refuses it, because its
  severity is a fraction of a spectrum and is not a rate.
- **The `response_along_time` figure**, one line per severity level against the frame's time:
  how a reader sees an error grow along a trajectory.

## What is not settled

1. **The valid prediction time is a reduction along time of rows the harness already writes.**
   With `per_unit_time`, each frame's `nrmse` row is the error of a prediction that has drifted
   for that long. The first time at which that error exceeds a threshold is the valid prediction
   time, so no new pipeline path is needed: it is a reduction over `frame_index` of existing
   rows. What is missing is the threshold. The idea page does not fix one, and a value chosen
   here would be a convention with no source. A metric built on it must state its threshold as a
   convention, and the threshold is fixed once in the evaluator, never per model.
2. **The temporal autocorrelation and the invariant measure need a trajectory as one input.**
   The pipeline hands a metric one frame at a time. No metric needs a whole trajectory yet, so
   the trajectory-level input is added when the first one is built, not before. The contract the
   pooled-estimate issue ([095](095-pooling-across-frames-for-distributional-estimates.md))
   records would serve both.
3. **A controlled temporal experiment on real data is still the temporal-ladder proposal**
   (`proposals/EXP-orchestrator-20261023-temporal-ladder.md`). `per_unit_time` covers only its
   third part, consistent spatial damage, and only for a damage that grows linearly in time.

## What would unblock it

A decision on the valid prediction time's threshold convention, and a first metric that needs a
trajectory-level input, built with this test bed as its evidence.

## Related

Written with the harness change that added the test bed (metric-evaluation design rev. 4, §3.6,
decision D4), 2026-10-28.
