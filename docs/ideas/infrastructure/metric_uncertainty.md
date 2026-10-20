# Uncertainty on every metric value

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

A metric value computed from a finite stretch of a flow is an estimate, and two values can
differ by chance alone. This idea attaches a resampling interval to every reported metric
value and compares a prediction with a reference relative to both of their uncertainties.

1. **A block-bootstrap interval on every value.** The *bootstrap* estimates the sampling
   variability of a statistic by recomputing it on many resamples of the data drawn with
   replacement (Efron & Tibshirani 1993). Frames in time and cells in space are correlated,
   so resampling them one at a time would treat correlated values as independent and give
   intervals that are too narrow. The *moving-block bootstrap* resamples contiguous blocks of
   length $L$ instead (Künsch 1989). The block length is declared with the result and is at
   least the integral or decorrelation scale of the data. In space the blocks become tiles of
   cells, and the tile size raises the same question as the block length.
2. **An uncertainty-normalised comparison.** For any target statistic $T$, such as a spectral
   slope or a flatness, compare prediction and reference by

   $$
   Z_T = \frac{\left| T_{\text{pred}} - T_{\text{ref}} \right|}
   {\sqrt{\hat\sigma^2_{\text{pred}} + \hat\sigma^2_{\text{ref}} + \varepsilon}}, \tag{1}
   $$

   where $\hat\sigma_{\text{pred}}$ and $\hat\sigma_{\text{ref}}$ are the bootstrap standard
   errors of the two values and $\varepsilon$ is a small declared constant that keeps the
   ratio finite. The reference's own uncertainty enters the denominator, so unresolved
   spectral tails, high-order moments and rare-event frequencies of the reference are not
   treated as exact truth.
3. **Comparison only where the reference is resolved.** A statistic is compared only over
   the range the reference itself resolves, such as the band of wavenumbers above its noise
   and below its dissipation cutoff, declared once with the reference.

What exists already: the moving-block bootstrap is implemented once, in
`fmeval/stats.py`, and the degradation-ladder analysis in `fmeval/analysis.py` uses it twice,
for the interval on each metric's rank correlation with severity (with a fixed block length)
and for the upper bound on the largest damage a degradation produces (with a block length
chosen automatically from the data). Both are statistics *about* a metric's response to the
ladder. What remains is an interval on each metric value itself, and the comparison of
Equation (1).

## Pitfalls

- A block that is too short gives intervals that are too narrow; a block that is too long
  leaves few blocks and noisy intervals.
- On a single trajectory, resampling measures variation along that trajectory, not between
  independent realisations of the flow.
- $Z_T$ is a ratio and inherits the instability of its denominator: when both standard
  errors are tiny, a negligible difference gives a large $Z_T$, which is what $\varepsilon$
  is for.
- An interval says whether a difference is distinguishable from sampling noise, not whether
  it matters physically.

## Rationale

*From the field guide; the team has not yet set a priority.* The guide treats uncertainty on
the metric values as a requirement attached to every score rather than as a separate metric:
a difference between two values means something only relative to the sampling uncertainty
of both, and the statistics this project cares most about, such as high-order moments,
spectral tails and rare events, are the slowest to converge. The resampling machinery is
already in the repository.

## Keywords

block bootstrap, moving-block bootstrap, block length selection, uncertainty-normalised
score, standard error of a metric, resolved support.

## References

- Efron, B. & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Springer.
  <https://doi.org/10.1007/978-1-4899-4541-9>
- Künsch, H. R. (1989). The jackknife and the bootstrap for general stationary observations.
  *The Annals of Statistics* 17(3), 1217–1241. <https://doi.org/10.1214/aos/1176347265>
