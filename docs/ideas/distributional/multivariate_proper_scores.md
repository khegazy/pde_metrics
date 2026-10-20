# Energy score, variogram score and calibration

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

A *scoring rule* assigns a number $S(F, y)$ to a forecast distribution $F$ once the outcome
$y$ is known. It is *proper* if, in expectation, no forecast scores better than the true
distribution of $y$, and *strictly proper* if the true distribution is the unique best
forecast (Gneiting & Raftery 2007). A proper score therefore rewards an ensemble for being
calibrated, not for being sharp and wrong. The built
[crps](../../metrics/crps.md), [spread_skill](../../metrics/spread_skill.md) and
[rank_histogram](../../metrics/rank_histogram.md) all score each grid value separately, so
they cover the *marginal* distributions and say nothing about how values at different
points vary together. This idea is the multivariate part and the calibration checks that
remain.

1. **Energy score.** For a forecast $F$ of a vector $\mathbf{y}$, such as a whole field, with
   $\mathbf{Y}$ and $\mathbf{Y}'$ independent draws from $F$ and $\|\cdot\|$ the Euclidean
   norm,

   $$
   \mathrm{ES}_\beta(F, \mathbf{y}) = \tfrac{1}{2}\, \mathbb{E}\, \|\mathbf{Y} - \mathbf{Y}'\|^\beta
   - \mathbb{E}\, \|\mathbf{Y} - \mathbf{y}\|^\beta, \qquad \beta \in (0, 2). \tag{1}
   $$

   It is strictly proper for $\beta \in (0, 2)$ (Gneiting & Raftery 2007). Equation (1) is
   written in Gneiting and Raftery's orientation, in which larger is better. In one
   dimension with $\beta = 1$ it reduces to the continuous ranked probability score, up to
   that sign convention. With an ensemble of $M$ members the expectations become averages
   over members and over pairs of members.

2. **Variogram score.** For a forecast of a vector with components $y_i$,

   $$
   \mathrm{VS}_p(F, \mathbf{y}) = \sum_{i,j} w_{ij} \left( |y_i - y_j|^p
   - \mathbb{E}_F\, |Y_i - Y_j|^p \right)^2, \tag{2}
   $$

   where $w_{ij} \ge 0$ are weights chosen by the user and $p > 0$ is an order (Scheuerer &
   Hamill 2015). It compares the differences between pairs of components, which is the
   *variogram* of geostatistics, and so targets the correlation structure that the marginal
   scores miss. Lower is better.

3. **Reliability diagram.** For an event such as "the value at a point exceeds a threshold",
   bin the forecast probabilities of the event and plot, for each bin, how often the event
   actually occurred. A calibrated forecast lies on the diagonal.

4. **Interval coverage.** For central prediction intervals at nominal levels of 50%, 80% and
   95%, report the fraction of reference values that fall inside. A calibrated forecast
   covers each at its nominal rate; less coverage means the ensemble is overconfident.

5. **Distribution of spectra.** For a generative model, compute the energy spectrum of each
   member and score the distribution of spectra, for example the logarithm of the spectrum
   at each wavenumber, rather than the spectrum of the ensemble mean. The same applies to
   any derived quantity of interest: a proper score can be applied to it instead of to the
   grid values.

## Pitfalls

- The energy score separates forecasts that differ only in their correlation structure
  weakly. This is the motivation Scheuerer and Hamill give for the variogram score
  (Scheuerer & Hamill 2015).
- The variogram score is unchanged when the same constant is added to every component,
  because each term in Equation (2) depends only on differences. It must be paired with a
  score that sees a common bias, such as the
  [crps](../../metrics/crps.md).
- The sum in Equation (2) runs over all pairs of points, so on a grid of $N$ cells it has
  $N^2$ terms. The weights $w_{ij}$, for example restricting pairs to a neighbourhood, set
  both the cost and what the score is sensitive to, and must be declared.
- Every item here needs an ensemble or a predictive distribution. For a deterministic
  surrogate it does not apply.

## Rationale

*From the field guide; the team has not yet set a priority.* Proper scores reward
calibrated ensembles rather than sharp-but-wrong point predictions, and the field guide
lists the energy score, rank histograms, spread–skill and the distribution of spectra as the
minimal panel for a generative ensemble. The built probabilistic metrics are marginal, so
nothing in the repository yet scores whether an ensemble gets the spatial correlation of its
members right, which is the property a generative model of turbulence is meant to have.

## Keywords

energy score, variogram score, multivariate proper scoring rule, reliability diagram,
prediction interval coverage, ensemble calibration, distribution of spectra.

## References

- Gneiting, T. & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and
  estimation. *Journal of the American Statistical Association* 102, 359–378.
  <https://doi.org/10.1198/016214506000001437>
- Scheuerer, M. & Hamill, T. M. (2015). Variogram-based proper scoring rules for
  probabilistic forecasts of multivariate quantities. *Monthly Weather Review* 143,
  1321–1334. <https://doi.org/10.1175/MWR-D-14-00269.1>
