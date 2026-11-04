# 018 — The diagram Wasserstein sibling registers p = 1 only; the HD95 sibling takes the percentile per direction

**Date:** 2026-11-04. **Made by:** the agent of task `metrics-topology-shocks` (branch from
`update_metric_eval_principles`).
**Reverse with:** for p = 2, add a sibling `persistence_wasserstein_2` whose metric is
`persistence_wasserstein`'s with `ORDER = 2.0` passed through (give `wasserstein` and the metric an
`order` argument defaulting to `ORDER`, so no number of `persistence_wasserstein` moves), with its
own card, as `proposals/MTR-persistence_distance-wasserstein-diagram-distance.md` describes. For
the pooled HD95, add a sibling whose summary is `np.percentile(np.concatenate([d_ab, d_ba]), 95)`
on `shock_set_distance`'s `surface_distances`, as
`proposals/MTR-shock_set_distance-other-surface-distance-summaries.md` describes. Then delete this
file.

## The questions that would have been asked

Kareem's rule is that where the fields compute a metric differently, every standard is built as its
own bundle. Two places in this task have more than one standard among the field's software, and
building every one doubles a bundle:

1. The Wasserstein distance between persistence diagrams has an exponent p. GUDHI, the library
   the diagrams come from, and the R package TDA default to p = 1; giotto-tda defaults to p = 2 and
   combines the dimensions by a 2-norm; Cohen-Steiner et al. (2010) suggest W_2 for their
   application. Build p = 1, p = 2, or both?
2. The 95th-percentile Hausdorff distance is computed per direction and the larger taken (Metrics
   Reloaded's code, SpatialVx's partial Hausdorff distance, Taha & Hanbury's quantile method) or on
   the two directions pooled (medpy's `hd95`). Build one or both?

## The choices

1. **p = 1 only**, with the L-infinity ground norm and the sum over dimensions:
   `persistence_wasserstein`. p = 2 stays a proposal.
2. **Per direction only**: `shock_set_hausdorff95`. The pooled form stays in the narrowed proposal.

## The evidence

All read for this task on 2026-11-04.

- **Exponent.** `gudhi.wasserstein.wasserstein_distance(X, Y, matching=False, order=1.0,
  internal_p=inf, ...)` (installed gudhi 3.13.0, signature and docstring); R TDA
  `wasserstein(Diag1, Diag2, p = 1, dimension = 1)` (rdrr.io documentation); giotto-tda 0.4.0
  `PairwiseDistance`: `p` default 2., `delta` default 0.01, `order` default 2. (module source
  page); Cohen-Steiner, Edelsbrunner, Harer & Mileyko 2010, Found. Comput. Math. 10, 127-139,
  Sect. 3 (degree-p Wasserstein distance, L-infinity ground norm, summed over all dimensions) and
  Sect. 4 ("we suggest using W_2"), authors' copy; Skraba & Turner 2020, arXiv:2006.16824v7,
  Definition 2.5 and Remark 2.6 (the literature disagrees on the ground norm; they take it equal
  to p).
- **Cost.** On one 256 x 256 vorticity frame of `kinet_re5e4` (frame 5000), Hera at a relative
  error of 1e-4 took 1.1 to 18.6 s per homology dimension for p = 1 and 5.5 to 68 s for p = 2,
  on a blurred and a noisy candidate (scratch script of this task, not kept; the numbers are in
  the task log). From those timings, a full run of the 161-frame evidence ladder at 256 for p = 1
  alone would take of the order of days (an estimate, not a measurement).
- **HD95.** MetricsReloaded `metrics/pairwise_measures.py`, `measured_hausdorff_distance_perc`:
  `np.max([np.percentile(<one direction>, q=perc), np.percentile(<other>, q=perc)])`, default 95;
  medpy `medpy/metric/binary.py`, `hd95`: `numpy.percentile(numpy.hstack((hd1, hd2)), 95)`;
  SpatialVx `LocMeasures.R`, `locperf`: the partial Hausdorff distance is the larger of the two
  fields' k-th largest (or quantile) distances; Taha & Hanbury 2015, BMC Med. Imaging 15, 29, the
  quantile method after Eq. (49), defined on the directed distance.

## Why

1. p = 1 is the default of the library that computes the diagrams and of the R package, and its
   sum is the natural contrast to the bottleneck distance's maximum. p = 2 is the same function
   with another constant, so the code already allows it; what it costs is a second full ladder of
   the most expensive metric in the repository, four to five times the p = 1 cost, for a number
   that sits between two that are already registered. The choice is about evaluation cost, not
   about which is right, and a person may well want both.
2. The per-direction form is the one the quantile Hausdorff distance is defined as in the
   medical-imaging reference that the bundle family already follows, the one the Metrics Reloaded
   consortium implements, and the one the weather-verification package computes; medpy's pooled
   form is one implementation's shortcut. On the Sod tube, with one or two flagged cells per
   direction, the two forms differ only when the two directions' distances differ.

## What it changes

Nothing that existed moves. Two bundles that might have been built are not.
