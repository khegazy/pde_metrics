# Reliability, interval coverage and the distribution of spectra

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The built [crps](../../metrics/crps.md), [spread_skill](../../metrics/spread_skill.md),
[rank_histogram](../../metrics/rank_histogram.md),
[energy_score](../../metrics/energy_score.md) and
[variogram_score](../../metrics/variogram_score.md) score an ensemble's values, cell by cell
or over the whole field. The energy and variogram scores cover the multivariate part of this
idea as first written. What remains are two calibration checks that read differently from a
score, and the application of a proper score to a derived quantity rather than to the grid
values.

1. **Reliability diagram.** For an event such as "the value at a point exceeds a threshold",
   bin the forecast probabilities of the event and plot, for each bin, how often the event
   actually occurred. A calibrated forecast lies on the diagonal.

2. **Interval coverage.** For central prediction intervals at nominal levels of 50%, 80% and
   95%, report the fraction of reference values that fall inside. A calibrated forecast
   covers each at its nominal rate; less coverage means the ensemble is overconfident. The
   interval score of Gneiting and Raftery (2007, Section 6.2, Equation 43) is the proper
   score that goes with a central interval, combining its width with a penalty for the
   reference falling outside it.

3. **Distribution of spectra.** For a generative model, compute the energy spectrum of each
   member and score the distribution of spectra, for example the logarithm of the spectrum
   at each wavenumber, rather than the spectrum of the ensemble mean. The same applies to
   any derived quantity of interest: a proper score can be applied to it instead of to the
   grid values (Gneiting & Raftery 2007).

## Pitfalls

- Every item here needs an ensemble or a predictive distribution. For a deterministic
  surrogate it does not apply.
- A reliability diagram and a coverage table are curves or tables, not one number. The
  number registered for each, such as a deviation from the diagonal or from nominal
  coverage, is a summary the literature does not fix, so it is a convention and must be
  declared as one.

## Rationale

*From the field guide; the team has not yet set a priority.* Proper scores reward
calibrated ensembles rather than sharp-but-wrong point predictions, and the field guide
lists the energy score, rank histograms, spread–skill and the distribution of spectra as the
minimal panel for a generative ensemble. Of that panel only the distribution of spectra is
not built.

## Keywords

reliability diagram, prediction interval coverage, interval score, ensemble calibration,
distribution of spectra.

## References

- Gneiting, T. & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and
  estimation. *Journal of the American Statistical Association* 102, 359–378.
  <https://doi.org/10.1198/016214506000001437>
