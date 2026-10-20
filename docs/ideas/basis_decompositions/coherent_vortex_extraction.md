# Wavelets and coherent vortex extraction

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

A wavelet is a short oscillating function that is localised in both position and scale. A
wavelet transform describes a field by how much of each wavelet, at each position and scale,
it contains. Because each wavelet has limited spatial extent, wavelets do not smear a shock
across all wavenumbers the way Fourier modes do. As Farge puts it in the review that
introduced this toolset to the turbulence community, wavelets "unfold a signal, or a field,
into both space and scale", and their limited spatial support means the analysis "can be
performed locally on the signal, as opposed to the Fourier transform which is inherently
nonlocal due to the space-filling nature of the trigonometric functions" (Farge 1992).

Coherent vortex extraction uses this to split a turbulent field in two. The coherent part,
which holds the organised structures such as vortices, is carried by a small number of large
wavelet coefficients. The incoherent part is a Gaussian-like background carried by the many
small coefficients (Farge, Schneider & Kevlahan 1999; Farge, Pellegrino & Schneider 2001).
Each part can then be compared with a metric suited to it.

This is
[splitting a field into smooth and sharp parts](../norms/mollification_split.md),

$$
f = f * \eta_\varepsilon + \Delta ,
$$

where $f * \eta_\varepsilon$ is the field smoothed at scale $\varepsilon$ and $\Delta$ is the
sharp remainder, carried out in a principled basis that is localised in space, with a split
chosen by the data rather than by an arbitrary scale $\varepsilon$. If that split is the
right organising principle, then wavelets are its mature implementation. The Farge quotation
above is also, in effect, the argument for why wavelets should outperform Fourier methods on
*shocklets*, the many small shocks embedded in compressible turbulence.

## Precedent

The toolset was introduced to turbulence by Farge (1992), and coherent vortex extraction was
developed for two-dimensional turbulence (Farge, Schneider & Kevlahan 1999) and then for
three-dimensional turbulent flows (Farge, Pellegrino & Schneider 2001). A more recent survey
of wavelet methods in computational fluid dynamics is Schneider and Vasilyev (2010).

Weather forecast verification has its own version. Intensity-scale verification scores
forecast skill jointly by intensity threshold and spatial scale, using a wavelet
decomposition of the error field (Casati et al. 2004). It is the ancestor of this idea,
applied to verification rather than to analysis.

## Rationale

*The team's judgement.* High priority: it is the mature, principled implementation of
[splitting a field into smooth and sharp parts](../norms/mollification_split.md), the
principle that most other ideas here slot into, and its spatial localisation is exactly what
a comparison of sharp features needs and Fourier methods lack.

## Keywords

coherent vortex extraction, CVS, wavelet thresholding turbulence, local intermittency
measure, wavelet methods computational fluid dynamics.

## References

- Casati, B., Ross, G. & Stephenson, D. B. (2004). A new intensity-scale approach for the
  verification of spatial precipitation forecasts. *Meteorological Applications* 11(2),
  141–154. <https://doi.org/10.1017/S1350482704001239>
- Farge, M. (1992). Wavelet transforms and their applications to turbulence. *Annual Review
  of Fluid Mechanics* 24, 395–458. <https://doi.org/10.1146/annurev.fl.24.010192.002143>
- Farge, M., Pellegrino, G. & Schneider, K. (2001). Coherent vortex extraction in 3D
  turbulent flows using orthogonal wavelets. *Physical Review Letters* 87(5), 054501.
  <https://doi.org/10.1103/PhysRevLett.87.054501>
- Farge, M., Schneider, K. & Kevlahan, N. (1999). Non-Gaussianity and coherent vortex
  simulation for two-dimensional turbulence using an adaptive orthogonal wavelet basis.
  *Physics of Fluids* 11(8), 2187–2201. <https://doi.org/10.1063/1.870080>
- Schneider, K. & Vasilyev, O. V. (2010). Wavelet methods in computational fluid dynamics.
  *Annual Review of Fluid Mechanics* 42, 473–503.
  <https://doi.org/10.1146/annurev-fluid-121108-145637>
