# Delta-variance spectral slope

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The Δ-variance measures how much structure a map holds at a given scale $l$ without a Fourier
transform. The field $f$ is convolved with a filter $\odot_l$ of size $l$, typically a
"Mexican hat" made of a positive core and a negative surrounding annulus whose weights sum to
zero, and the variance of the filtered map is recorded (Stutzki et al. 1998; Ossenkopf, Krips
& Stutzki 2008, Eq. 1):

$$
\sigma_\Delta^2(l)=\big\langle \big(f\ast\odot_l\big)^2(\mathbf{r})\big\rangle_{\mathbf{r}} .
\tag{1}
$$

Repeating this over a range of filter sizes gives a curve that plays the role of a spectrum
in real space. For a two-dimensional map whose power spectrum is a power law,
$P(|\mathbf{k}|)\propto|\mathbf{k}|^{-\zeta}$, the Δ-variance is also a power law,
$\sigma_\Delta^2\propto l^{\alpha}$ with $\alpha=\zeta-2$, valid for $0\le\zeta<6$
(Ossenkopf, Krips & Stutzki 2008, following Eq. 10). Here $\zeta$ is the index of the
two-dimensional power spectrum $P(\mathbf{k})$; the angle-integrated energy spectrum $E(k)$
has index $\zeta - 1$ (their footnote 2). The metric compares the predicted and
reference Δ-variance curves, or the slopes fitted to them.

What it adds over a Fourier spectrum is robustness on maps that are bounded, irregular or
unevenly trustworthy. Ossenkopf, Krips and Stutzki replace truncation of the filter at the
map edge by zero-padding the data and correcting the normalisation with weights. The same
weighting, set from the local noise level, handles maps with irregular boundaries and
variable error bars, and separates noise from genuine small-scale structure (Ossenkopf, Krips
& Stutzki 2008). This suits a prediction or reference on a non-periodic or masked domain,
where a fast Fourier transform assumes a periodicity the data do not have.

## Precedent

The method was introduced to analyse the fractal structure of molecular clouds (Stutzki et
al. 1998) and improved for maps with irregular boundaries and variable noise (Ossenkopf, Krips
& Stutzki 2008). It is implemented in the TurbuStat package (Koch et al. 2019).

## Pitfalls

- Like any spectrum, the Δ-variance is phase-blind. A Gaussian random field with the
  reference spectrum, such as the
  [gaussian_impostor](../../degradations/gaussian_impostor.md), has the same Δ-variance, so
  it must be paired with a phase-sensitive statistic such as the
  [bispectrum](bispectrum.md).
- The filter shape changes the curve. Ossenkopf, Krips and Stutzki recommend a Mexican-hat
  filter with a core-to-annulus diameter ratio of 1.5 as a general compromise; whatever is
  chosen must be declared once and kept fixed.
- On a periodic domain where the full Fourier spectrum is available it adds little to the
  built [spectrum_l2](../../metrics/spectrum_l2.md).

## Rationale

*From the field guide; the team has not yet set a priority.* The Δ-variance recovers the
spectral slope robustly on bounded or irregular maps where a fast Fourier transform fails,
and like the other astrophysics-derived statistics it needs no reference aligned in phase
with the prediction. It matters for references that are not periodic boxes.

## Keywords

Delta-variance, Δ-variance, Mexican-hat filter, wavelet spectral slope, TurbuStat,
structure analysis of interstellar clouds.

## References

- Koch, E. W. et al. (2019). TurbuStat: turbulence statistics in Python. *The Astronomical
  Journal* 158, 1. <https://doi.org/10.3847/1538-3881/ab1cc0>
- Ossenkopf, V., Krips, M. & Stutzki, J. (2008). Structure analysis of interstellar clouds.
  I. Improving the Δ-variance method. *Astronomy & Astrophysics* 485, 917–929.
  <https://doi.org/10.1051/0004-6361:20079106>
- Stutzki, J., Bensch, F., Heithausen, A., Ossenkopf, V. & Zielinsky, M. (1998). On the
  fractal structure of molecular clouds. *Astronomy & Astrophysics* 336, 697–720.
  <https://ui.adsabs.harvard.edu/abs/1998A%26A...336..697S>
