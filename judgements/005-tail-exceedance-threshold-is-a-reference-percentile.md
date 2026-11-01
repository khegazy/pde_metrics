# 005 — The tail-exceedance threshold is a percentile of the reference, and the comparison its frequency bias

**Date:** 2026-10-31. **Made by:** the agent building `tail_exceedance` (branch
`metric/tail_exceedance`).
**Reverse with:** a sibling bundle whose threshold is a multiple of the reference's increment rms
and whose comparison is a difference or a ratio of probabilities, importing the same increments;
or a change to `metrics/tail_exceedance/metric.py`'s thresholds, which changes every number the
card records. Then delete this file and its row in `README.md`.

## The question that would have been asked

The idea page left two things open for tail exceedance probabilities: "how the threshold $a$ is
fixed once for every model (for example in units of the reference's increment standard
deviation), and how two probabilities are compared (a difference, a ratio, or a curve over $a$)".
Which threshold, and which comparison?

## The choice

**The threshold is the reference's own $k$-th largest absolute increment, per channel and axis,
and the comparison is the frequency bias, the prediction's count of increments at least that large
over the reference's, perfect at 1.** The frequency bias is the standard score for how often an
event is predicted against how often it occurs: "(hits + false alarms) / (hits + misses)", perfect
score 1 (WWRP/WCRP Joint Working Group on Forecast Verification Research, "Forecast verification:
methods, issues and FAQ", section "Frequency bias (bias score)",
<https://jwgfvr.github.io/forecastverification>). Without pairing cells, hits plus false alarms is
the prediction's event count and hits plus misses the reference's. A threshold set as a percentile
of a reference sample, with exceedances of it counted in another sample, is how the ETCCDI
percentile indices are built (TX90p: days above the base period's 90th percentile; "Definitions of
the 27 core indices", <https://etccdi.pacificclimate.org/list_27_indices.shtml>, item 13). The
metric reports the ratio as the literature does and declares `target=1.0`, so the analysis orders it
by distance from 1, as it does `spread_skill`.

- **Why a percentile of the reference and not a multiple of an rms.** A multiple of
  `ctx.fluctuation_rms`, the brief's suggestion, is a multiple of the field's rms, not of its
  increments'. Measured on `kinet_re5e4` frames 2000, 6000 and 10000 (recomputed vorticity), the
  one-cell increment rms is 0.027 to 0.038 of the fluctuation rms on density and velocity and 0.16
  to 0.29 on vorticity, so one multiple would be a rare event on one field and none at all on
  another. A multiple of the reference's increment rms is consistent across fields but leaves the
  reference's event rate to the shape of its distribution: on the same frames the rate of
  increments at least three increment rms in size is 0.0145 to 0.0315 across fields and frames,
  against 0.0027 for a Gaussian. A percentile fixes the reference's
  rate at $k/n$ everywhere and assumes nothing about the distribution, and its level is set by the
  same order `tail_index` reads.
- **Why the frequency bias and not a difference of probabilities.** A difference of two
  probabilities of order $1/\sqrt{n}$ is itself of that order and depends on the grid; the ratio is
  dimensionless and has a fixed perfect value, and it is the score the verification literature
  defines for this question.
- **Why the $k$-th largest with $\ge$.** Derived on the card (Equation (5), this bundle's own,
  for a reference of independent values): an independent prediction from the reference's
  distribution then has an expected frequency bias of $n/(n+1)$, while the $(k+1)$-th largest with
  $>$ gives $n(k+1)/((n+1)k)$, about 1.25 at the curve's first point. Zhang, Hegerl, Zwiers and
  Kenyon (2005, *J. Climate* 18(11), 1641–1651, doi:10.1175/JCLI3366.1, abstract) describe how a
  percentile threshold's exceedance rate differs inside and outside the sample it was estimated
  from, and correct it with a bootstrap; the choice of order statistic here is a different remedy.
  The ETCCDI indices themselves use a strict inequality.

## What it changes

The metric's number is a ratio of counts with a target of 1, not a probability or a difference.
Which point of the curve is registered is a separate convention, `issues/118`. Nothing in the
harness changes beyond letting the two pairwise identity contract tests expect a declared target.
