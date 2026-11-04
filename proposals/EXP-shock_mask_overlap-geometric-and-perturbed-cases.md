---
type: "EXP"
kind: "benchmark problem"
related: ["shock_mask_overlap", "shock_set_distance", "proposals/MTR-shock_mask_overlap-fractions-skill-score.md", "proposals/MTR-shock_set_distance-object-matched-shock-distance.md", "proposals/MTR-shock_set_distance-other-surface-distance-summaries.md", "proposals/EXP-shock_set_distance-2d-shock-dataset.md", "issues/002"]
seen_in: "Ahijevych, Gilleland, Brown & Ebert 2009, Weather Forecast. 24(6), 1485-1497, Sects. 2-3, Tables 1 and 4; Gilleland et al. 2009, Weather Forecast. 24(5), 1416-1430, Sect. 1; Roberts & Lean 2008, Mon. Weather Rev. 136(1), 78-97, Sect. 2d, Fig. 4"
doi: "10.1175/2009WAF2222298.1"
found_by: "update_metric_eval_principles, 2026-11-03"
---

# EXP: Two-dimensional shock sets with known displacement, size and orientation errors

## What the experiment is

The test cases with which spatial forecast verification compares its methods, transferred
from rain areas to shock sets. The Spatial Forecast Verification Methods Intercomparison
Project scored every method on three kinds of case: simple geometric fields, real fields
perturbed by known amounts, and real forecasts (Gilleland et al. 2009, Sect. 1; the cases are
defined in Ahijevych et al. 2009):

1. **Geometric cases** (Ahijevych et al. 2009, Sect. 2a, Table 1): an elliptical observed
   field on a 601 by 501 grid, and forecasts that are the same ellipse displaced by 50 or 200
   points (geom001, geom002), displaced by 125 points and enlarged (geom003), displaced and
   with its aspect ratio changed, a "quasi-rotation" (geom004), or displaced and much larger,
   the only forecast that overlaps the observation (geom005).
2. **Perturbed cases** (Sect. 3, Table 4): one real field shifted right and down by 3/5,
   6/10, 12/20, 24/40 and 48/80 points (pert001 to pert005), and the 12/20 shift combined
   with a global intensity error (pert006, pert007).
3. **The idealised neighbourhood test** of the fractions skill score (Roberts & Lean 2008,
   Sect. 2d, Fig. 4): a band one cell wide displaced by 1, 3, 11 and 21 cells, for which the
   score is zero until the neighbourhood is wider than the displacement.

Transferred here: two-dimensional pressure fields carrying shock fronts of chosen shape (a
straight front, a curved front, a set of closed fronts), with the candidate built by a known
displacement, a known change of the front's length or curvature, a rotation, and the
perturbed-case ladder of shifts applied to a real two-dimensional shock field when one exists.

## What it tests

It changes the geometry of a shock set in controlled and separately known ways: position
only, size only, orientation only, and position plus amplitude. The distance-based summary of
`shock_set_distance` has a known answer for a pure displacement of a sharp step along a grid axis (its card's
Equation 3, (s - 1/2) cell widths for a shift of s cells), and
a pure overlap score such as `shock_mask_overlap` drops to its floor once two thin sets stop
touching, so the geometric cases show directly where each kind of metric saturates; the
neighbourhood test shows the scale at which a fractions skill score recovers.

## Metrics it would test

`shock_mask_overlap` (Dice), `shock_set_distance` (average symmetric surface distance), the
proposed fractions skill score of shock masks and object-matched shock distance, and the
proposed Hausdorff-type summaries. Spatial verification groups such methods as neighbourhood,
scale separation, features-based and field deformation (Gilleland et al. 2009, Sect. 1,
Fig. 1); these cases are how that field tells the groups apart.

## Why it is helpful

The only shock data here is the one-dimensional Sod tube, where a shock set is one or two
cells, so a displacement, a size change and a rotation cannot be told apart, and the evaluation
plan withholds the fractions skill score and the categorical scores as degenerate there.
`EXP-shock_set_distance-2d-shock-dataset.md` proposes physical two-dimensional shocks, which
these cases would complement with known answers per kind of error; the perturbed-case ladder
can be run on that dataset once it exists.

## Cost and requirements

A closed-form dataset in the pattern of `fmeval/data/analytic.py` (fronts drawn as smoothed
pressure jumps of a chosen profile so that the shock detector fires on them), and a handful of
geometric operators (rotation is issue 015; a front-length change is new). The detector's
threshold must stay fixed, as for every thresholded quantity. Seconds per run.

## References

- Ahijevych, D., Gilleland, E., Brown, B. G. & Ebert, E. E. (2009). Application of spatial
  verification methods to idealized and NWP-gridded precipitation forecasts. *Weather and
  Forecasting* 24(6), 1485-1497. <https://doi.org/10.1175/2009WAF2222298.1> (read in full).
- Gilleland, E., Ahijevych, D., Brown, B. G., Casati, B. & Ebert, E. E. (2009).
  Intercomparison of spatial forecast verification methods. *Weather and Forecasting* 24(5),
  1416-1430. <https://doi.org/10.1175/2009WAF2222269.1> (read in full).
- Roberts, N. M. & Lean, H. W. (2008). Scale-selective verification of rainfall accumulations
  from high-resolution forecasts of convective events. *Monthly Weather Review* 136(1), 78-97.
  <https://doi.org/10.1175/2007MWR2123.1> (read in full; FSS is Eq. 6).
