---
type: "MTR"
kind: "variant of tail_exceedance"
related: ["metrics/tail_exceedance", "issues/118"]
seen_in: "agent's own"
doi: "none"
found_by: "tail_exceedance, 2026-10-31"
---

# MTR: A summary of the whole frequency-bias curve instead of its point at sqrt(n)

## What it measures

How far a prediction's extremes are from the reference's at every exceedance level at once, rather
than at the one level `tail_exceedance` registers, which saturates at 0 under any blur of more
than a few percent of the field's scale (`issues/118`).

## Definition

My own suggestion. With $B(\theta)$ the stored curve of `tail_exceedance`,

$$
S = \frac{1}{9} \sum_{\theta} \bigl\lvert \log \max\bigl(B(\theta),\, \tfrac{1}{2N(\theta)}\bigr) \bigr\rvert
$$

where $N(\theta)$ is the reference's event count, so that a prediction with no events is scored as
if it had half of one, a continuity correction of my choosing. The floor is a second
convention and must be stated as one.

## Relation to existing work

The analysis already orders `tail_exceedance` by $\lvert\log B\rvert$ at one $\theta$. This would
register the mean over $\theta$ as a sibling bundle importing the same curve, the route
`issues/098` and `issues/105` name for their curves.

## How it could be tested

`gaussian_blur`, `box_blur`, `lowpass_ideal` and `lowpass_butterworth`, on which the registered
point ties at 0 from the second strength; the curve's larger $\theta$ are graded there.

## Why it is helpful

It removes the saturation without choosing another single level, and it keeps a target of 0 for a
prediction whose extremes match at every level.

## References

None beyond the bundle's own.
