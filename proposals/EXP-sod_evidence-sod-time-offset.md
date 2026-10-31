---
type: EXP
kind: benchmark problem
related: ["docs/ideas/shock_geometry/shock_set_distance.md", "docs/ideas/shock_geometry/shock_mask_overlap.md", "docs/ideas/shock_geometry/shock_front_error.md"]
seen_in: "agent's own idea, built on the closed form in fmeval/data/analytic.py (Toro 2009, Sect. 4.5, eqs. 4.55-4.59)"
doi: "none"
found_by: "sod_evidence, 2026-10-23"
---

# EXP: The exact Sod solution at a shifted time, as a physically consistent wave-position error

## What the experiment is

Score the exact solution at time `t` (the reference) against the exact solution at
`t + dt` (the candidate), for a ladder of offsets `dt`. The candidate is still an exact
solution of the Euler equations with the same initial states: every jump keeps its exact
Rankine-Hugoniot size, and only the positions of the waves are wrong. Because the solution
is self-similar in `xi = (x - 0.5)/t`, each wave moves by its own speed times `dt`: the shock
by `S_R dt`, the contact by `u_* dt`, the rarefaction head and tail by `S_HL dt` and
`S_TL dt` (Toro 2009, eqs. 4.55 and 4.59; values for Sod's data in Marzouk 2020, Table 2:
`S_R = 1.75216`, `S_HL = -1.18322`, `S_TL = -0.07027`; `u_* = 0.92745` from Toro 2009,
Table 4.3). On 2048 cells over `[0, 1)`, an offset `dt = 0.001` moves the shock by 3.59
cells and the contact by 1.90 cells (agent's arithmetic from those speeds, not a measured
value).

## What it tests (the property it changes in a controlled, known way)

The position of each discontinuity, by a known and *different* amount per wave, with the
jump sizes held exactly. `translate_x` moves every wave by the same distance; this moves the
shock about twice as far as the contact and in the opposite direction from the rarefaction
head. A shock-set distance should rise with `|S_R dt|` in cells; a metric that tracks the
contact or the shock separately can be checked wave by wave against the closed-form shift.

## Metrics it would test

The shock-geometry chain (`docs/ideas/shock_geometry/`): the distance between extracted
shock sets, the shock-mask overlap (issue 068), and the Rankine-Hugoniot residual on a
detected surface (issue 051), whose residual should stay at its reference value because the
jumps are exact while the position error grows.

## Why it is helpful

It separates "the right shock in the wrong place" from "the wrong shock", the double
penalty that motivates the repository, with every number known in closed form. A
translation cannot do this: it moves all waves together, so a metric that tracks only the
largest jump cannot be told apart from one that tracks all three.

## Cost and requirements

The reader already evaluates the solution at any time up to 0.2854; the candidate needs a
second evaluation per frame, which costs 0.3 ms per frame on 2048 cells (the measurement in
the `fmeval/data/analytic.py` module docstring). It does not fit the current degradation
interface, which receives one field and no closed form, so it needs either a
dataset-specific operator with access to the trajectory or a paired-dataset reader (issue
010, forecast-pair reader). A person must choose between those.

## References

- Toro, E. F. (2009). *Riemann Solvers and Numerical Methods for Fluid Dynamics*, 3rd ed.
  Springer. Chapter 4, eqs. 4.55-4.59, Table 4.3. <https://doi.org/10.1007/b79761>
- Marzouk, O. A. (2020). The Sod gasdynamics problem as a tool for benchmarking face flux
  construction in the finite volume method. *Scientific African* 10, e00573, Table 2.
  <https://doi.org/10.1016/j.sciaf.2020.e00573>
