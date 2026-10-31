# Probabilistic and distributional metrics

These metrics compare probability distributions rather than fields cell by cell. The
distribution may be of a quantity over the domain, such as the values taken by a velocity
increment, or of the members of an *ensemble*, a set of forecasts of the same state. A
distributional comparison does not care where in the domain a value occurs, so it is
insensitive to displacement by construction, and it can be aimed directly at the rare,
intense events that an over-smoothed prediction loses. Its weakness is the mirror image: it is
blind to how features are arranged in space unless features are first extracted and their
positions treated as data.

Built already, and so not listed here: the continuous ranked probability score
([crps](../../metrics/crps.md)), the spread-to-skill ratio
([spread_skill](../../metrics/spread_skill.md)), the rank histogram
([rank_histogram](../../metrics/rank_histogram.md)), the flatness of increments
([increment_flatness](../../metrics/increment_flatness.md)), the Hill estimate of their tail
index ([tail_index](../../metrics/tail_index.md)), and the energy distance between increment
distributions ([energy_distance](../../metrics/energy_distance.md)).

## Ideas in this theme

- [Tail exceedance and peaks-over-threshold](tail_index_estimators.md): direct comparison of
  how often large values occur, and a generalised Pareto fit to the values above a high
  threshold.
- [Pair-correlation function of features](pair_correlation.md): the distribution of
  distances between extracted features such as eddy centres, compared between two fields.
- [Energy score, variogram score and calibration](multivariate_proper_scores.md): proper
  scores for whole fields rather than single grid values, and the reliability and coverage
  checks of an ensemble.
- [Width of the log-density distribution](density_log_pdf.md): the variance of the
  logarithm of density, which has a physical target set by the Mach number and the driving.
- [Quality of predictive uncertainty](predictive_uncertainty.md): conformal prediction,
  calibration, sharpness and out-of-distribution detection for a surrogate that reports
  its own uncertainty.
