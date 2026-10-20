# Two-point correlation

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The two-point correlation measures how strongly a field at one point is related to the same
field at a point a given separation away, averaged over the domain. It is standard and cheap
to compute, and comparing the predicted and reference correlations as functions of the
separation gives a baseline check on how a field's variation is distributed across length
scales.

It must be read for what it is not. The two-point correlation and the power spectrum (the
energy in each Fourier mode) are Fourier transforms of one another, so they carry the same
information. The energy spectrum is already compared by
[spectrum_l2](../../metrics/spectrum_l2.md), and computing both does not make two
independent checks. More importantly, both discard all Fourier *phase*, the part of each
mode that records where structures sit relative to one another, and phase is where structure
resides. Matching a two-point correlation is therefore a weak constraint. Its physical-space
counterpart is the second-order structure function, a linear function of it, and the
[structure functions](../turbulence_statistics/structure_functions.md) of higher order are
where physical-space statistics go beyond it.

## Pitfalls

- The two-point correlation is blind to phase. A Gaussian random field built to match the
  reference energy spectrum, such as the
  [gaussian_impostor](../../degradations/gaussian_impostor.md), has the same two-point
  correlation as the reference by construction, even though it contains none of the
  reference's structures.
- Agreement in the two-point correlation is not evidence of structural fidelity. It belongs
  in a report as a baseline beside metrics that see phase, not as a substitute for them.

## Rationale

*The team's judgement.* Medium priority: the two-point correlation is standard and cheap, and
it is worth including as a baseline, but it carries the same information as the energy
spectrum, which is already built, so it adds no independent check.
