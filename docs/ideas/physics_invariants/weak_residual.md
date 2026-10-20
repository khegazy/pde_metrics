# Residual of the equations in weak form

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

A residual measures how far a predicted field is from satisfying the governing equations.
The *strong-form* residual, obtained by substituting the field into the differential
operator, is meaningless at a discontinuity. Solutions with shocks are weak solutions: they
satisfy the equations only after integration over cells or against test functions, and their
derivatives are distributions rather than functions.

The *finite-volume weak residual* is the cell-average update plus the flux balance across the
cell faces minus the source term. It remains valid at shocks, and it is the residual that
should be reported.

## Rationale

*The team's judgement.* High priority: the residual is reference-free, cheap, and always
available.
