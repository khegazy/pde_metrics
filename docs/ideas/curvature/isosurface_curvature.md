# Curvature statistics of level sets

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

An isosurface is the surface on which a field takes one fixed value, the isovalue. Extract
isosurfaces of density, pressure or vorticity magnitude from both fields, compute their mean
curvature (the average of the two principal curvatures at a point) and their Gaussian
curvature (the product of the two), and compare the resulting *distributions* rather than
the surfaces point by point. For shocked flow the quantities of interest are shock-front
curvature and corrugation statistics, which describe how the front is wrinkled.

## Precedent

Combustion has a mature version of this idea: probability density functions of flame-front
curvature are a standard diagnostic of how turbulence wrinkles a front.

## Pitfalls

- The result is sensitive to the choice of isovalue.
- Curvature needs second derivatives of the field, so the result is sensitive to noise.

## Rationale

*The team's judgement.* Medium priority: there is real precedent and the implementation
cost is moderate, but the result is sensitive both to the choice of isovalue and to noise in
second derivatives.

## Keywords

flame front curvature PDF, isosurface curvature turbulence, shock corrugation spectrum,
level-set curvature statistics.
