---
type: EXP
kind: benchmark problem
related: ["metrics/shock_set_distance", "metrics/shock_mask_overlap", "docs/ideas/shock_geometry/shock_turbulence_interaction.md", "issues/002"]
seen_in: "Lax & Liu 1998, SIAM J. Sci. Comput. 19(2), 319-340"
doi: "10.1137/S1064827595291819"
found_by: "shock_set_distance, 2026-10-30"
---

# EXP: A two-dimensional shock dataset for the shock-set distance

## What the experiment is

Add one dataset whose pressure holds shocks in two dimensions, so that the surface-distance
machinery of `shock_set_distance` (an exact Euclidean distance transform between two sets of
flagged cells) is exercised on curved and oblique fronts and on several shocks at once. Two
candidates, in order of cost:

1. **Two-dimensional Riemann problems** of gas dynamics, the configurations computed by Lax and
   Liu (1998): four constant states in the quadrants of a square, whose interacting shocks,
   contacts and rarefactions form curved fronts. They have no closed form, but are standard
   benchmarks computed by many schemes, so a reference run at high resolution is the
   reference and the same run at lower resolution or with another scheme is the candidate.
2. **Decaying compressible turbulence with eddy shocklets**, the case of issue 002, at the
   turbulent Mach number of Lee, Lele and Moin (1991, Phys. Fluids A 3(4), 657): many small
   shocks embedded in turbulence, the case the metric is meant for.

## What it tests

On a Riemann configuration, `translate_x` moves every front by a known number of cells, so the
metric must give back Equation (3) of its card on each front, now with the flagged band oblique
to the grid; a test the one-dimensional tube cannot make. On shocklets, the metric's two open
weaknesses become measurable: the nearest-cell matching of many shocks without object matching,
and the pooled average's weighting toward the larger set (the card's Limitations).

## Metrics it would test

`shock_set_distance`, and `shock_mask_overlap`, which imports the same detector; on shocklets,
the shock-turbulence interaction statistics as well.

## Why it is helpful

The card of `shock_set_distance` can only say that the one-dimensional case is evidenced. Its
detector takes the jump along each grid axis rather than along the shock normal (a choice made
for want of a temperature gradient); whether that misses oblique shocks is untested until a
dataset has one.

## Cost and requirements

A two-dimensional Euler solver run (the kinet solver, which already runs the Sod configurations,
or any finite-volume code), a reader for its output, boundary types declared per axis
(Riemann configurations are usually run with outflow boundaries), and a dataset page. Storage is
small: a few hundred frames at 512^2. No licence issue for solver output.

## References

- Lax, P. D. & Liu, X.-D. (1998). Solution of two-dimensional Riemann problems of gas dynamics
  by positive schemes. *SIAM J. Sci. Comput.* 19(2), 319-340.
  <https://doi.org/10.1137/S1064827595291819> (metadata read; the paper is behind a paywall).
- Lee, S., Lele, S. K. & Moin, P. (1991). Eddy shocklets in decaying compressible turbulence.
  *Phys. Fluids A* 3(4), 657. As cited by `issues/002`; not opened.
