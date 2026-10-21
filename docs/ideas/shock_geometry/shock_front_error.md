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

On a curved surface in two or three dimensions, with unit normal $\mathbf{n}$, normal speed
$V_n$, and $[\,\cdot\,]$ the jump across the surface, the conditions read

$$
\big[F(U)\cdot\mathbf{n}\big] - V_n\,[U] = 0 \tag{1}
$$

and the residual is computed by a fixed procedure:

1. **Sample the two states away from the surface.** Take the left and right states at offsets
   of $n_o \in \{2, 3, 4\}$ local grid spacings along the normal on each side, and average each
   over a $3\times 3$ patch of points along the surface. Never sample *on* the detected surface:
   a captured shock is smeared across several cells, so the states there are intermediate
   states that satisfy no jump condition.
2. **Estimate the normal speed from a smoothed track.** Take $V_n$ from a level-set or
   temporally smoothed track of the surface, not from the difference of its position between
   two frames, which amplifies the cell-scale jitter of the detected surface.
3. **Score on both surfaces.** Evaluate the predicted field's residual on the surface detected
   in the prediction and again on the surface detected in the reference. The four combinations
   read as follows:
    - low on both: correct physics in the correct place;
    - low on the predicted surface, high on the reference surface: a self-consistent shock in
      the wrong place;
    - high on the predicted surface, low on the reference surface: a smeared shock, or a failure
      to extract the surface;
    - high on both: neither surface carries a jump consistent with conservation.

How the reference-surface score should register a missing or displaced shock is not settled.
A field that has no jump at the sampled location gives $[U] = 0$ and $[F\cdot\mathbf{n}] = 0$,
and so a zero residual. Normalising the residual by the size of the reference jump does not
change this, because zero divided by any jump is still zero. The residual alone therefore
scores a missing shock as low, and the second reading in the list holds only if the residual
is paired with a quantity that sees the missing jump, for instance the mismatch between the
predicted and reference jumps $[U]$ sampled on the reference surface. Which such quantity to
use is an open question (*added in review, not from the field guide or the team*).

## Precedent

Canonical test cases for these measurements are the Sod shock tube (Sod 1978) and the double
Mach reflection, both of which contain a few clean fronts.

## Pitfalls

- Position and speed errors are well defined only for isolated fronts that can be tracked,
  which is exactly *not* the case of turbulence populated by many small shocks (shocklets).
- The jump-condition residual depends on every choice in the procedure above: the offsets, the
  tangential averaging, the speed estimate and the detector threshold. Each is fixed once by
  the evaluator.

## Rationale

*The team's judgement.* Medium priority: high value when the field contains a few clean
shocks, but harder to define for a field populated by many small shocklets, which is the
motivating case.

## References

- Sod, G. A. (1978). A survey of several finite difference methods for systems of nonlinear
  hyperbolic conservation laws. *Journal of Computational Physics* 27, 1–31.
  <https://doi.org/10.1016/0021-9991(78)90023-2>
