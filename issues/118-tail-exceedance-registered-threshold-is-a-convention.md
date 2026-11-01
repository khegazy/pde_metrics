# The threshold at which `tail_exceedance` registers its frequency bias is a convention with no source

**Category:** method
**Priority:** unset
**Status:** open. The metric is built with the convention labelled; what would replace it is open.

## Context

`tail_exceedance` counts how many of a prediction's absolute one-cell increments reach the
reference's $k$-th largest, over how many of the reference's do: the frequency bias of forecast
verification, perfect at 1 (JWGFVR, "Forecast verification: methods, issues and FAQ", section
"Frequency bias (bias score)", <https://jwgfvr.github.io/forecastverification>). Its companion is
that ratio at nine orders $k = \lceil n^\theta \rceil$, $\theta = 0.1, \dots, 0.9$, the orders of
`tail_index`. The panel needs one number, and the metric registers the curve's point
$\theta = 1/2$, $k = \lceil\sqrt{n}\rceil$.

No source fixes that point. The verification literature computes a frequency bias at whatever
threshold the user cares about, and the percentile-based climate-extremes indices use fixed
percentiles (the 90th and the 10th for TX90p and TN10p, ETCCDI's list of the 27 core indices) for
daily data of a different size. The $\sqrt{n}$ order is one of the two fixed rules Clauset,
Shalizi and Newman (2009, *SIAM Review* 51(4), 661–703, Sect. 3.5) name for the sample a tail
estimate keeps; carrying it over to an exceedance threshold, so that this metric counts the
extremes `tail_index` reads, is the repository's choice.

## What was measured before the choice was declared

On nine frames of `kinet_re5e4` (2000 to 10000 every 1000, the real ladder operators and a
calibration measured on those frames), the point $\theta = 1/2$ saturates on the smoothing axes:
the median value is 0.02 to 0.27 at the first strength of `gaussian_blur` and `box_blur` and
exactly 0 from the second strength on every field, and 0 at every strength of `lowpass_ideal` and
`lowpass_butterworth` on density and velocity. A value of 0 is infinitely far from the target on
the scale the analysis orders by, so the harsher strengths of those axes tie. The evidence run
`tail_exceedance_1793494833` (161 frames) bears this out: the Gaussian and box blurs and both
low-pass filters have their rank correlation withheld on density and velocity at $\theta = 1/2$,
and are graded again only from $\theta = 0.6$ or 0.7 upward; the dominance of the weakest pair of
Gaussian-blur strengths is 0.429, 0.764 and 0.59 on the three fields, so there the registered
point does not stand for the curve (the card's "The curve behind the number").

## What would settle it

A published choice of the exceedance level for comparing a prediction's extremes with a
reference's, or a decision to register a different summary for a stated purpose. Options:

1. **Keep $\theta = 1/2$.** The same extremes `tail_index` reads; saturates on smoothing.
2. **A larger $\theta$**, such as 0.7 (about 2400 of 65536 increments per axis), a commoner event
   that a blur reduces gradually rather than removes; it is less about extremes.
3. **A summary of the curve**, such as the mean of $\lvert \log B(\theta) \rvert$ over $\theta$
   with a floor for $B = 0$; it needs a floor, which is a second convention.

Any of these is a sibling bundle importing the same curve, not a change to this one.

## Related

- `metrics/tail_exceedance/card.md`, Definition and Limitations.
- `issues/098`, `issues/105`: the same question for two other curve metrics.
- `judgements/005`: why the threshold is the reference's own order statistic.
