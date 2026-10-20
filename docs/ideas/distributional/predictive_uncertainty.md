# Quality of predictive uncertainty

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Some surrogates report their own uncertainty: an error bar, a prediction interval, or the
spread of an ensemble. This idea measures whether that uncertainty is useful, which is a
separate question from whether the prediction is accurate. The built
[spread_skill](../../metrics/spread_skill.md) and
[rank_histogram](../../metrics/rank_histogram.md) check the calibration of an ensemble on
average; the items below go further.

1. **Conformal prediction.** A method that wraps *any* predictor and returns a prediction set
   $C(x)$ for each input $x$ with a guaranteed coverage

   $$
   \Pr\big(y \in C(x)\big) \ge 1 - \alpha, \tag{1}
   $$

   for a chosen error rate $\alpha$, with no assumption on the distribution of the data and
   for a finite sample (Angelopoulos & Bates 2021). In its simplest, *split* form, the
   predictor's errors are scored on a held-out calibration set of $n$ examples, the
   $\lceil (n+1)(1-\alpha) \rceil / n$ quantile of those scores is taken, and the interval
   around each new prediction is widened by that quantile. The guarantee needs the
   calibration and test examples to be *exchangeable*, meaning their joint distribution does
   not change when they are reordered (Angelopoulos & Bates 2021). It has been applied to
   operator-learning surrogates (Moya et al. 2025). As a metric, the empirical coverage on
   test data and the width of the resulting intervals are what is reported.
2. **Error–uncertainty correlation.** The rank correlation, across samples or cells, between
   the uncertainty the surrogate reports and the error it actually makes. It measures
   whether the uncertainty separates the surrogate's successes from its failures.
3. **Calibration curve.** For each nominal level, the fraction of reference values that fall
   inside the surrogate's interval at that level, plotted against the level. A calibrated
   surrogate lies on the diagonal.
4. **Sharpness.** The average width of the surrogate's intervals, regardless of the outcome.
   Of two calibrated surrogates, the sharper one says more.
5. **Out-of-distribution detection.** Use the reported uncertainty as a score for whether an
   input lies outside the training distribution, and report the area under the receiver
   operating characteristic curve (AUROC), the probability that a randomly chosen
   out-of-distribution input receives a higher score than a randomly chosen
   in-distribution one.

## Pitfalls

- The coverage of Equation (1) is averaged over inputs. It does not guarantee coverage for
  each input separately (Angelopoulos & Bates 2021), so a surrogate may over-cover easy
  regions of the flow and under-cover shocks while meeting the average.
- Adjacent frames of one trajectory are strongly correlated, so treating them as
  exchangeable calibration examples breaks the assumption the guarantee rests on.
  Calibration examples should come from separate trajectories.
- A correlation ignores scale: uncertainty that is ten times too small everywhere can still
  correlate perfectly with the error. The correlation must be read beside the calibration
  curve.
- Sharpness alone rewards overconfidence and is meaningful only for a calibrated surrogate.
- None of these applies to a surrogate that reports no uncertainty.

## Rationale

*From the field guide; the team has not yet set a priority.* A surrogate that will be used
without a reference beside it is only as safe as its uncertainty, and the guide groups these
checks with goal-oriented error and robustness as what decides whether a surrogate can be
deployed. Conformal prediction gives a coverage guarantee for any predictor, including one
that was not designed to report uncertainty.

## Keywords

conformal prediction, split conformal, distribution-free coverage, calibration curve,
sharpness, error–uncertainty correlation, out-of-distribution detection AUROC.

## References

- Angelopoulos, A. N. & Bates, S. (2021). A gentle introduction to conformal prediction and
  distribution-free uncertainty quantification. <https://arxiv.org/abs/2107.07511>
- Moya, C., Mollaali, A., Zhang, Z., Lu, L. & Lin, G. (2025). Conformalized-DeepONet: A
  distribution-free framework for uncertainty quantification in deep operator networks.
  *Physica D: Nonlinear Phenomena* 471, 134418.
  <https://doi.org/10.1016/j.physd.2024.134418>
