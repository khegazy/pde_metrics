---
type: MTR
kind: new metric
related: ["metrics/shock_set_distance"]
seen_in: "agent's own"
doi: "none"
found_by: "shock_set_distance, 2026-10-30"
---

# MTR: Shock thickness and overshoot at the detected shocks

## What it measures

Two properties of each shock the detector finds, which the deleted shock-detector idea page
listed as "direct quality measures in their own right" and which no built metric reports: the
**thickness** $w_{10\text{-}90}$, the distance along the shock normal over which the pressure
rises from 10% to 90% of its jump, in cells; and an **overshoot and undershoot** score, how far
the profile across the shock exceeds the state on either side. A smeared shock is a thickness
error, a ringing one an overshoot error; the shock-set distance sees neither unless the shock
disappears.

## Definition

My own formulation, not from a source: at each flagged cell of the reference and candidate
(`shock_mask` in `metrics/shock_set_distance/metric.py`), take the pressure profile along the
axis of largest jump, find the pre- and post-shock plateaus as the first cells outside the
flagged band, and report the 10-90% width in cells and $\max(0, p_{\max} - p_2, p_1 - p_{\min})/
(p_2 - p_1)$ over a fixed window. The comparison is the difference between candidate and
reference, averaged over matched shocks. The idea page gave no citation for either quantity;
one is needed before building.

## Relation to existing work

Uses the detector built in `shock_set_distance`. The idea page that listed it was deleted with
that bundle; this proposal keeps the two quantities from being lost.

## How it could be tested

On `sod_shock_tube`, `gaussian_blur` and `box_blur` widen the shock by a known kernel width,
but every calibrated width also removes it from the detector (the card's Smoothing results), so
the thickness would need to be measured where the reference flags the shock, not where the
candidate does. `lowpass_ideal` creates Gibbs overshoot of known size at a sharp step.

## Why it is helpful

It separates the two classic failures of a shock-capturing scheme, smearing and oscillation,
which a distance between shock positions does not see.

## References

None; the quantities come from the deleted idea page `docs/ideas/shock_geometry/shock_detector.md`,
which cites no source for them.
