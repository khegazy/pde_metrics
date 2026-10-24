# EXP: A directional (anisotropic) blur

Found by: the orchestrator screening `docs/ideas/`, 2026-10-23. Seen in: the orchestrator's own
proposal.

## What the experiment is

A Gaussian blur with different widths along x and y, the ratio of the widths being the severity,
with the geometric mean of the widths held at a fixed fraction of the characteristic scale (the
`scale` calibration the smoothing family already uses).

## What it tests

It makes a nominally isotropic field anisotropic by a controlled, known amount: at width ratio 1 it
is the existing isotropic blur, and as the ratio grows the correlation length along one axis grows
relative to the other. Every existing smoothing, spectral and noise operator is isotropic, so no
current degradation changes anisotropy at all.

## Metrics it would test

The direction-dependent part of the two-point correlation (issue 075), Reynolds-stress anisotropy
(058), the statistical-isotropy check of equivariance (071), and Minkowski tensors (the
anisotropic part of the Minkowski-functionals idea, which a scalar Minkowski metric does not cover).

## Why it is helpful

Anisotropy is the property several ideas add over the built spectrum and kinetic energy, and
without this operator none of that addition can be tested.

## Cost and requirements

One new degradation bundle (`degradations/`), reusing the Gaussian kernel code in
`degradations/_shared/`. It must declare `preserves=("spatial_mean",)` only.

## References

None; the proposal is the orchestrator's own.
