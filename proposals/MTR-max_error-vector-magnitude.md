---
type: "MTR"
kind: "variant of max_error"
related: ["metrics/max_error"]
seen_in: "agent's own"
doi: "none"
found_by: "max_error, 2026-10-30"
---

# MTR: Maximum of the error vector's length

## What it measures

The largest length of the error vector over all cells of a vector field, rather than the
largest single component. It is the worst-cell error of velocity as a vector, and it does not
depend on the orientation of the coordinate axes.

## Definition

For a field with $C$ components,

$$
\mathrm{MaxE}_{2}(f, g) = \max_{1 \le i \le N} \Bigl( \sum_{c=1}^{C} \bigl( f_{c,i} - g_{c,i} \bigr)^2 \Bigr)^{1/2} \tag{1}
$$

the $L^\infty$ norm in space of the pointwise Euclidean length. This is my own formulation, not
taken from a source; I found no source in this search that fixes the pointwise norm for a
vector-valued maximum error (Roy 2005, Eq. 7, is written for a scalar; PDEBench averages
per-channel maxima).

## Relation to existing work

`max_error` pools channels and so reports $\max_{c,i} |f_{c,i} - g_{c,i}|$, the largest
component. For two components the two satisfy $\mathrm{MaxE} \le \mathrm{MaxE}_2 \le \sqrt{2}\,
\mathrm{MaxE}$ (from $\max_c |e_c| \le |e|_2 \le \sqrt{C} \max_c |e_c|$), and they agree on
one-channel fields. Its per-cell map would be the speed of the error, `np.linalg.norm` over the
channel axis, reduced by `max` as `max_error`'s is.

## How it could be tested

The existing ladder on velocity; the rotation invariance could be checked on a synthetic field
rotated by 45 degrees, where `max_error` changes by up to a factor of the square root of two
and Equation (1) does not change.

## Why it is helpful

It is the natural worst-case error for a velocity field when the physics, not the grid,
should decide the answer, for example on a dataset whose axes have no preferred orientation.

## References

- Roy, C. J. (2005). Review of code and solution verification procedures for computational
  simulation. *Journal of Computational Physics* 205(1), 131–156, Sect. 2.5, Eq. 7.
  doi:10.1016/j.jcp.2004.10.036.
