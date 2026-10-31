---
type: MTR
kind: variant of energy_distance
related: ["energy_distance", "increment_w1_by_separation"]
seen_in: "agent's own"
doi: "none"
found_by: "energy_distance, 2026-10-30"
---

# MTR: Energy distance between increment distributions at every octave separation

## What it measures

The energy distance between the reference's and the prediction's increment distributions at
separations of 1, 2, 4, ... cells up to half the grid, as a curve, so the scale at which the
increment statistics depart is visible. It is to energy_distance what
increment_w1_by_separation is to increment_w1.

## Definition

D(l) = mean over channels and axes of (2 integral of (F_l - G_l)^2 dx)^(1/2), where F_l and G_l
are the empirical distributions of the increments at separation l (Rizzo & Székely 2016, WIREs
Comput. Stat. 8(1), 27-38, p. 27, for D; Székely & Rizzo 2013, J. Stat. Plann. Inference 143(8),
1249-1272, the display before Eq. (2.3), for the one-dimensional form). The curve is the
companion; the registered number would need a summary, which no source fixes (the same
situation as issues/098 for increment_w1_by_separation).

## Relation to existing work

increment_w1_by_separation is built and is the transport version. The variant reuses its
separation grid (`increment_w1_curve`'s octaves) and `increments(..., separation=l)`; the only
new code would be the distance. Comparing the two curves separation by separation is the
cleanest form of the averaging-versus-transport comparison the energy_distance idea page asked
for, because at large separation the increment distribution approaches the one-point
distribution and its tails change.

## How it could be tested

The existing smoothing, filtering, coarsening and noise axes, exactly as
increment_w1_by_separation is tested; its per-coordinate tables would show at which separation
each metric departs.

## Why it is helpful

A one-cell distance cannot say at which scale the prediction's statistics go wrong; the curve
can, and doing it with both distances on the same separations shows where tails matter.

## References

- Rizzo, M. L. & Székely, G. J. (2016). Energy distance. WIREs Comput. Stat. 8(1), 27-38.
  doi:10.1002/wics.1375.
- Székely, G. J. & Rizzo, M. L. (2013). Energy statistics: A class of statistics based on
  distances. J. Stat. Plann. Inference 143(8), 1249-1272. doi:10.1016/j.jspi.2013.03.018.
