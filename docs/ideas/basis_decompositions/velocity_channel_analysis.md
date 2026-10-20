# Velocity channel analysis

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Sometimes the reference is not the full field but a *projection* of it: an observation that
integrates the flow along a line of sight. Radio observations of interstellar gas are the
standard case. They record emission as a function of two sky coordinates and of the
line-of-sight velocity, a position–position–velocity cube, and never the three-dimensional
density and velocity themselves. Velocity channel analysis compares flows in that projected
space. It computes the power spectrum of the emission in *velocity channels*, slices of the
cube of a chosen velocity width, and relates those spectra to the statistics of the
underlying density and velocity fields (Lazarian & Pogosyan 2000).

The key result is that the channel width selects what the spectrum sees. In thin channels,
velocity fluctuations dominate the small-scale emission and make the channel spectrum
shallower; as the channels thicken, the spectrum steepens toward that of the density
(Lazarian & Pogosyan 2000). Measuring how the slope changes with channel width therefore
separates the velocity spectrum from the density spectrum using only the projection. The
velocity coordinate spectrum is a companion technique that takes the spectrum along the
velocity axis of the same cube.

For a surrogate, the comparison would apply the same observation operator, the projection
into a position–position–velocity cube, to the prediction and compare the resulting channel
spectra with the reference's. This is a spectral comparison in observation space rather than
in the state space of the simulation.

## Precedent

The method was developed for neutral hydrogen emission from the interstellar medium
(Lazarian & Pogosyan 2000). Implementations of velocity channel analysis and the velocity
coordinate spectrum are collected in the TurbuStat package (Koch et al. 2019).

## Pitfalls

- It applies only when the reference is a projection that carries a line-of-sight velocity.
  For a reference that is the full field on a grid, the ordinary spectra are available
  directly and this adds nothing.
- The comparison is only as good as the observation operator. The prediction must be
  projected exactly as the reference was, and that operator becomes part of the metric's
  definition.
- Like every spectrum, the channel spectra are phase-blind and say nothing about the
  arrangement of structures.
- The same authors warn that turbulent velocity alone can create small-scale structure in a
  channel map that is easily mistaken for genuine density structure (Lazarian & Pogosyan
  2000).

## Rationale

*From the field guide; the team has not yet set a priority.* Velocity channel analysis and
the velocity coordinate spectrum give the principled spectral comparison in observation space
for references that are projected along a line of sight. They belong to a family of
astrophysics statistics built because astrophysics never has a reference aligned in phase with
its data, the same situation a surrogate meets after its rollout decorrelates.

## Keywords

velocity channel analysis, VCA, velocity coordinate spectrum, VCS, position–position–velocity
cube, channel maps, observation operator, synthetic observations.

## References

- Koch, E. W. et al. (2019). TurbuStat: turbulence statistics in Python. *The Astronomical
  Journal* 158, 1. <https://doi.org/10.3847/1538-3881/ab1cc0>
- Lazarian, A. & Pogosyan, D. (2000). Velocity modification of H I power spectrum. *The
  Astrophysical Journal* 537, 720–748. <https://doi.org/10.1086/309040>
