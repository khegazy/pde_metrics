---
type: EXP
kind: protocol
related: ["issues/051", "issues/056", "issues/073", "issues/078", "issues/079", "issues/080", "issues/081", "issues/084"]
seen_in: "orchestrator's own; no published protocol was consulted"
doi: "none"
found_by: "orchestrator, 2026-10-23"
---

# EXP: A degradation ladder for trajectories

## What the experiment is

The current ladder damages one snapshot at a time. This experiment damages a short *trajectory*
of consecutive reference frames, with the damage defined in time as well as space:

1. **Time lag.** The "prediction" at frame `t` is the reference at frame `t + d`, for a ladder of
   lags `d`. Every statistic of a single frame is preserved, and only the timing is wrong.
2. **Temporal smoothing.** Each frame of the prediction is a running average of the reference over a
   window of `w` frames, so the dynamics are too slow and fluctuations are damped, as the
   conditional-mean collapse described on the temporal-autocorrelation page would predict.
3. **Consistent spatial damage.** Any existing spatial operator applied with the same severity and
   the same random draw to every frame of the window, so that a pair of consecutive damaged states
   is available to metrics that difference time levels.

## What it tests

It changes, in a controlled and known way, properties that no single-snapshot degradation can
touch: the rollout's timing (lag), the rate at which it forgets its past (smoothing lengthens the
integral time scale by a known amount for a known window), and the consistency of consecutive
states (spatial damage applied identically in time).

## Metrics it would test

Valid prediction time (issue 078), temporal autocorrelation (079), invariant measure (080), modal
decompositions (081), the weak-form residual (084), the speed part of shock front error (051),
the time-differenced part of entropy production (056) and eddy lifetimes (073).

## Why it is helpful

Eight screened-out ideas fail only because no experiment acts on time. One harness extension would
make all of them testable on the existing `kinet_re5e4` trajectory, without new simulation.

## Cost and requirements

A harness change: the pipeline must hand a metric a window of frames rather than one frame, and the
ladder must apply an operator to a window. Frames one solver step apart are needed for the residual;
`kinet_re5e4` stores every solver step at 10001 frames, but the evaluation reads every 50th, so a
residual run would read pairs of adjacent stored frames.

## References

None; the proposal is the orchestrator's own.
