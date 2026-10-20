# Signed entropy production

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Entropy production is the rate at which entropy is generated locally in the flow. In a
shocked flow, physical shocks *must* produce entropy; spurious numerical oscillations
produce negative entropy; and over-smeared learned shocks produce too *little*. Three
separate numbers should therefore be reported:

1. **An entropy-violation score**, capturing unphysical negative production.
2. **A signed mismatch** against the entropy production of the reference.
3. **An excess-dissipation score.**

## Precedent

The theoretical machinery for comparing a numerical scheme's entropy production against an
entropy-conservative reference flux, a numerical flux constructed to produce no entropy so
that a scheme's dissipation can be measured against it, is Tadmor's (Tadmor 1987, 2003).
Entropy production specifically at shocks is treated by Ismail and Roe (Ismail and Roe 2009).

## Pitfalls

- A one-sided check, which looks only at the sign of the production, detects only the first
  of the three errors. It is blind to an over-dissipated, smeared field.

## Rationale

*The team's judgement.* High priority: the diagnostic is reference-free, it is the
physically correct admissibility condition for shocked flow (the condition that singles out
the physical solution among the many that satisfy the equations in weak form), and the
three-way split directly detects the over-smoothing failure most expected from a
machine-learned surrogate.

## References

- Ismail, F. & Roe, P. L. (2009). Affordable, entropy-consistent Euler flux functions II:
  Entropy production at shocks. *Journal of Computational Physics* 228(15), 5410–5436.
  <https://doi.org/10.1016/j.jcp.2009.04.021>
- Tadmor, E. (1987). The numerical viscosity of entropy stable schemes for systems of
  conservation laws. I. *Mathematics of Computation* 49(179), 91–103.
  <https://doi.org/10.1090/S0025-5718-1987-0890255-3>
- Tadmor, E. (2003). Entropy stability theory for difference approximations of nonlinear
  conservation laws and related time-dependent problems. *Acta Numerica* 12, 451–512.
  <https://doi.org/10.1017/S0962492902000156>
