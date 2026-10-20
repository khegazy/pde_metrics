# Velocity-derivative skewness

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The velocity-derivative skewness is the normalised third moment of a longitudinal velocity
derivative, a velocity component differentiated along its own direction:

$$
S = \frac{\bigl\langle (\partial_x u)^3 \bigr\rangle}
{\bigl\langle (\partial_x u)^2 \bigr\rangle^{3/2}} . \tag{1}
$$

It is the small-separation limit of the skewness of the longitudinal increment, and so the
gradient-scale counterpart of the [four-fifths law](four_fifths_law.md). For a Gaussian field
its expected value is zero, because every odd moment of a zero-mean Gaussian variable
vanishes. In real turbulence it is close to $-0.5$ and depends only weakly on the Reynolds
number, with a fit $-S \sim 0.32\, \mathrm{Re}_\lambda^{0.11}$ to direct numerical
simulations (Ishihara et al. 2007), where $\mathrm{Re}_\lambda$ is the Reynolds number built
on the Taylor microscale (defined on
[one-point statistics and characteristic scales](one_point_statistics.md)).

The idea is to report $S$ for the prediction at every checkpoint, and, where a reference
exists, to compare it with the reference's value. It costs one pass over the derivative
field.

Its fourth-order companion, the gradient flatness, is exactly 3 for a Gaussian field and well
above 3 in real turbulence, growing with the Reynolds number (Sreenivasan and Antonia 1997).
Most of it is already built: [increment_flatness](../../metrics/increment_flatness.md) is the
flatness of one-cell increments, which for velocity is the flatness of a one-sided difference
approximation to the gradient. That metric averages over every channel-and-axis pair, so it
mixes longitudinal derivatives with transverse ones (a component differentiated across its
own direction). What remains of the gradient flatness is to report the longitudinal and
transverse values separately, computed with the same derivative stencil as Equation (1).

## Pitfalls

- Both quantities depend on resolution and on the differentiation stencil. Under-resolution
  lowers $|S|$ and the flatness artificially, which mimics the very failure they are meant to
  detect, so the resolution must be reported beside them.
- A single number cannot show at which scale a prediction fails; the
  [structure functions](structure_functions.md) and the per-separation
  [four-fifths law](four_fifths_law.md) localise it.
- The reference values above come from incompressible simulations. How shocklets in
  compressible turbulence change them is not covered by the sources cited here.

## Rationale

*From the field guide; the team has not yet set a priority.* The skewness costs almost
nothing, needs no reference, and collapses to its Gaussian value of zero when a model drifts
toward a Gaussian-like state with the right spectrum. That makes it a candidate for an
always-on monitor during training.

## Keywords

velocity-derivative skewness, gradient flatness, longitudinal and transverse derivatives,
small-scale intermittency, Taylor-microscale Reynolds number.

## References

- Ishihara, T., Kaneda, Y., Yokokawa, M., Itakura, K. & Uno, A. (2007). Small-scale
  statistics in high-resolution direct numerical simulation of turbulence: Reynolds number
  dependence of one-point velocity gradient statistics. *Journal of Fluid Mechanics* 592,
  335–366. <https://doi.org/10.1017/S0022112007008531>
- Sreenivasan, K. R. & Antonia, R. A. (1997). The phenomenology of small-scale turbulence.
  *Annual Review of Fluid Mechanics* 29, 435–472.
  <https://doi.org/10.1146/annurev.fluid.29.1.435>
