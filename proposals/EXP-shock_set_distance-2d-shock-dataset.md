---
type: EXP
kind: benchmark problem
related: ["metrics/shock_set_distance", "metrics/shock_mask_overlap", "metrics/shock_set_hausdorff", "metrics/shock_set_hausdorff95", "metrics/shock_set_masd", "metrics/shock_set_baddeley_delta", "docs/ideas/shock_geometry/shock_turbulence_interaction.md", "issues/002"]
seen_in: "Lax & Liu 1998, SIAM J. Sci. Comput. 19(2), 319-340"
doi: "10.1137/S1064827595291819"
found_by: "shock_set_distance, 2026-10-30"
---

# EXP: A two-dimensional shock dataset for the shock-set distance

Narrowed on 2026-11-27, when part of what it asked for was built. Built: the Sedov–Taylor blast
wave it listed third (`sedov_taylor`, the exact cylindrical solution, with time-offset candidates);
straight shocks oblique to the grid in a solver run scored against their exact solution
(`kinet_oblique_riemann_30deg` and `kinet_oblique_riemann_45deg`, Sod's tube rotated in a square
on 200^2 and 400^2 cells); and several interacting shocks at once, curved and straight, from one
solver with no exact answer (`kinet_double_mach_reflection`, 480 x 120 cells). What remains is
below: the four-quadrant configurations of Lax and Liu, with a high-resolution reference run and a
coarser candidate, and the shocklets of issue 002.

## What the experiment is

Add the datasets whose pressure holds the shocks two-dimensional data still lacks, so that the
surface-distance machinery of `shock_set_distance` (an exact Euclidean distance transform between
two sets of flagged cells) is exercised on curved fronts that interact and on many shocks at once,
each with a candidate of known or measured displacement. Two candidates, in order of cost:

1. **Two-dimensional Riemann problems** of gas dynamics, the configurations computed by Lax and
   Liu (1998): four constant states in the quadrants of a square, whose interacting shocks,
   contacts and rarefactions form curved fronts. They have no closed form, but are standard
   benchmarks computed by many schemes, so a reference run at high resolution is the
   reference and the same run at lower resolution or with another scheme is the candidate.
   The double Mach reflection now in the repository has no such candidate: its finer grids,
   which would take regular-queue jobs, were not run.
2. **Decaying compressible turbulence with eddy shocklets**, the case of issue 002, at the
   turbulent Mach number of Lee, Lele and Moin (1991, Phys. Fluids A 3(4), 657): many small
   shocks embedded in turbulence, the case the metric is meant for. Skipped for now
   (`dataset_specs/BUILD_ORDER.md`, steps 23 and 26).

## What it tests

On a four-quadrant configuration, `translate_x` moves every front of an interacting pattern by a
known number of cells, so the metric must give back Equation (3) of its card on each front, and a
coarser run gives a measured displacement of a pattern whose fronts curve and meet. (On a single
oblique front the same test is now possible on the oblique Riemann runs.) On shocklets, the metric's two open
weaknesses become measurable: the nearest-cell matching of many shocks without object matching,
and the pooled average's weighting toward the larger set (the card's Limitations).

## Metrics it would test

`shock_set_distance`, its siblings `shock_set_hausdorff`, `shock_set_hausdorff95`,
`shock_set_masd` and `shock_set_baddeley_delta`, and `shock_mask_overlap`, all of which import
the same detector; on shocklets, the shock-turbulence interaction statistics as well. The
weather-verification scores of thresholded fields that a single one-dimensional shock leaves
degenerate, the fractions skill score over window width and the critical success index and
equitable threat score, become measurable here.

## Why it is helpful

The detector of `shock_set_distance` takes the jump along each grid axis rather than along the
shock normal (a choice made for want of a temperature gradient). On the oblique Riemann runs it
flags the shock at 30 and 45 degrees (187 to 503 cells at t = 0.2, measured 2026-11-27); whether
it separates interacting fronts and many small shocks remains untested.

## Cost and requirements

A two-dimensional Euler solver run and a dataset page. kinet's finite-volume PonD solver runs such
cases, and its output is read through the existing converter and `kinet_raw` reader, outflow faces
declared `neumann` (as on the oblique Riemann and double Mach reflection runs,
`docs/datasets/logs/kinet_runs/shocks_2d/`; a 400^2 oblique run took 487 s on one GPU there).
Whether kinet ships a four-quadrant case was not checked; if not, one is added as a case. Storage
is small: a few hundred frames at 512^2. No licence issue for solver output.

## References

- Lax, P. D. & Liu, X.-D. (1998). Solution of two-dimensional Riemann problems of gas dynamics
  by positive schemes. *SIAM J. Sci. Comput.* 19(2), 319-340.
  <https://doi.org/10.1137/S1064827595291819> (metadata read; the paper is behind a paywall).
- Lee, S., Lele, S. K. & Moin, P. (1991). Eddy shocklets in decaying compressible turbulence.
  *Phys. Fluids A* 3(4), 657. As cited by `issues/002`; not opened.
