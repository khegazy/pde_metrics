# Shock front position, speed and jump conditions

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Two kinds of measurement on a detected shock front belong to this idea.

- **Position and speed errors.** Locate the front in the prediction and in the reference, and
  report how far apart they are and how much their speeds differ. These errors are highly
  interpretable.
- **The Rankine–Hugoniot residual.** The Rankine–Hugoniot conditions are the jump conditions
  that a conservation law imposes across a moving discontinuity: for a front moving at speed
  $s$ that separates states $U_L$ and $U_R$, with flux $F$, they require
  $s\,(U_R - U_L) = F(U_R) - F(U_L)$. The residual measures how far the jump across a detected
  front is from satisfying them. It is a valuable physical check that needs no reference field.

## Pitfalls

- Position and speed errors are well defined only for isolated fronts that can be tracked,
  which is exactly *not* the case of turbulence populated by many small shocks (shocklets).
- The jump-condition residual demands careful sampling. Never sample the states *on* the
  detected surface, because a captured shock is smeared across several cells. Sample instead
  at offsets along the normal to the surface, on either side, and average along the surface.

## Rationale

*The team's judgement.* Medium priority: high value when the field contains a few clean
shocks, but harder to define for a field populated by many small shocklets, which is the
motivating case.
