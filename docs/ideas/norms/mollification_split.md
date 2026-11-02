# Splitting a field into smooth and sharp parts

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Convolve the field $f$ with a mollifier $\eta_\varepsilon$, a smooth nonnegative kernel of
unit integral and width $\varepsilon$, to obtain a smooth part. The remainder $\Delta$ then
carries the sharp structure:

$$
f = \underbrace{f * \eta_\varepsilon}_{\text{smooth part}} +
\underbrace{\Delta}_{\text{singular remainder}} \tag{1}
$$

The smooth parts of two fields are compared with ordinary metrics such as $L^2$ or the
[$H^1$ seminorm](../../metrics/h1_seminorm.md). The remainders are compared with
position-tolerant metrics, such as the
[Wasserstein distance](../../metrics/wasserstein.md) applied to $|\Delta|$, or the
[distance between extracted shock sets](../../metrics/shock_set_distance.md) applied to
the support of $\Delta$, the set of points where it is nonzero.

Equation (1) is not itself a metric. It is the *organising principle* behind most of the
plan: decide which part of a field each metric should see. Nearly every other idea slots
naturally into one side of the split or the other.

Three choices are open, and they are why the gap is mathematical:

- How should $\varepsilon$ be chosen: fixed, swept, or tied to the grid?
- Should the split be iterated across several scales, which would turn it into a wavelet
  decomposition?
- Should $\Delta$ be compared as a signed field, or through $|\Delta|$?

## Precedent

The same split, carried out in a wavelet basis, is what
[coherent vortex extraction](../basis_decompositions/coherent_vortex_extraction.md) does. In
weather verification it is intensity-scale verification, which decomposes forecast skill
simultaneously by intensity threshold and by spatial scale using a wavelet decomposition of
the error field (Casati et al. 2004). The SAL score of weather verification, which separates
structure, amplitude and location errors, follows the same philosophy (Wernli et al. 2008).
The [Helmholtz split into rotational and compressive
parts](../physics_invariants/helmholtz_split.md) is a version of the split defined by physics
rather than by a smoothing scale.

## Rationale

*The team's judgement.* High priority: the split resolves the central difficulty of
shocklet-populated flow, in which many small shocks sit inside turbulence. Shocklets are
smooth and sharp at once, and the split lets the right metric be applied to each part
instead of demanding that a single metric handle both.

## References

- Casati, B., Ross, G. & Stephenson, D. B. (2004). A new intensity-scale approach for the
  verification of spatial precipitation forecasts. *Meteorological Applications* 11(2),
  141–154. <https://doi.org/10.1017/S1350482704001239>
- Wernli, H., Paulat, M., Hagen, M. & Frei, C. (2008). SAL — A novel quality measure for the
  verification of quantitative precipitation forecasts. *Monthly Weather Review* 136(11),
  4470–4487. <https://doi.org/10.1175/2008MWR2415.1>
