# `persistence_wasserstein` is too slow to run on the turbulence evidence datasets

**Category:** compute
**Priority:** medium. The card cites only `forecast_re5e4`, so its numbers on the two turbulence
ladders (`kinet_re5e4`, `kinet_re1e6`) are missing.
**Status:** open. On Kareem's instruction (2026-11-04) the metric is not run on `kinet_re5e4` or
`kinet_re1e6` for now; both are listed under `not_run` in its `card.yaml`, citing this issue.

## Context

`persistence_wasserstein` is the 1-Wasserstein distance between two fields' sublevel-set
persistence diagrams, with the L-infinity ground norm (Cohen-Steiner et al. 2010, Sect. 3),
computed with Hera at relative error delta = 1e-6 (judgement 018). A vorticity field of the
turbulence datasets has thousands of features, so each diagram has thousands of points, and every
comparison solves an approximate optimal matching between them. The degradation ladder needs one
comparison per frame, severity level and field.

## Evidence

Off-run timings on `kinet_re5e4` frame 5000, vorticity, all homology dimensions, delta = 1e-6
(`agent_logs/2026-11-03-update_metric_eval_principles/task-metrics-topology-shocks.md`):

| Analysis grid | Blur, sigma 1 | Noise, 0.1 |
|---|---|---|
| 256 x 256 | 5.6 s | 23.9 s |
| 128 x 128 | 0.18 s | 2.9 s |
| 64 x 64 | 0.015 s | 0.078 s |

The final evidence pass of `update_metric_eval_principles` (code at `adbdc88`) ran it as 12 frame
shards on `kinet_re5e4` (14 frames, 91 severity levels over 23 axes, density and vorticity,
256 x 256) and 2 on `kinet_re1e6` (81 frames, 128 x 128). The 14 processes shared the login node's
cap of 32 cores per user (`cpu.max` 3200000/100000). None had finished after about 9.75 hours
(launched 09:04, stopped 18:50), and they were stopped. Every other metric's shard on the same
runs finished within about 3 hours.

## Options

1. Run it at a 128 x 128 analysis grid, which is roughly 8 to 30 times faster per comparison. The
   card would then report a different resolution from the other metrics on `kinet_re5e4`, which
   its run summary must say.
2. Use Hera's default delta = 0.01: 1.5 times faster, with a relative change of 2.3e-4 in the
   distance on the measured pair. Alone this does not bring the run within a working day.
3. Run the 256 x 256 ladder on compute nodes under an allocation, as many shards as there are
   frames, instead of on a login node.
4. Fewer frames: a larger `dataset.time.reduction` for this metric alone.
