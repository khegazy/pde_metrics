# 002 — The Hill estimator is reported on fields whose increments may have no power-law tail

**Date:** 2026-10-30. **Made by:** the agent building `tail_index` (branch `metric/tail_index`).
**Reverse with:** delete `metrics/tail_index`, or replace its estimator by one defined for every
tail (the moment estimator of Dekkers, Einmahl and de Haan 1989, or the peaks-over-threshold fit
still on the idea page); then delete this file and its row in `README.md`.

## The question that would have been asked

The idea page asks for a tail index of increments, estimated "with the Hill estimator". Hill's
estimator estimates the extreme-value index of a power-law tail, and it is consistent exactly when
the tail is one (Boucheron & Thomas 2015, *Electronic Journal of Statistics* 9(2), 2751–2792,
doi:10.1214/15-EJS1088, Sect. 1). Before reading a fitted exponent as one, standard practice is to
test whether a power law fits at all (Clauset, Shalizi & Newman 2009, *SIAM Review* 51(4),
661–703, doi:10.1137/070710111, Sects. 4 and 5). Should the repository report a Hill estimate on
fields whose increments may not have a power-law tail?

## What was measured

Before the metric was declared, the Hill estimate of the absolute one-cell increments was computed
on frames 2000 and 5000 of `kinet_re5e4` at k = ceil(n^theta) for theta = 0.1 to 0.9, beside one
draw of independent Gaussian noise of the same size (n = 65536). At theta = 0.5, the registered
order, every field scored below the Gaussian (density 0.052 and 0.064, velocity 0.070 and 0.037,
vorticity 0.082 and 0.092, Gaussian 0.095); at theta = 0.8 every field scored above it (0.47 to
1.39 against 0.22). Taken alone, that would say the far tail of these increments is lighter than a
Gaussian's. It does not show that: the largest increments of a smooth field sit side by side, and
that clustering lowers the Hill estimate of a field whose tail is a power law too. Blurring an
independent Pareto field (alpha = 1, true index 1) by two cells lowers its estimate from a mean of
1.039 to 0.481 over eight 128 x 64 draws, while a blurred independent Gaussian field keeps its
value (`metrics/tail_index/test_metric.py`). So the measurement leaves open whether these
increments have a power-law tail; what it shows is that the Hill estimate here is set by the
clustering as much as by the tail, and is not a tail index. The evidence run
`tail_index_1793350342` (161 frames) adds that noise raises the orders below theta = 0.5 and lowers
those above it on every field, and that over the 161 frames vorticity's median at 0.5 lies above
the noise-dominated value, so noise lowers it there while it raises density and velocity (the
card's Results, "Noise").

## The choice

**Build it, as the Hill estimate at the fixed order k = ceil(sqrt(n)), and say on the card what
the number is when the tail is not a power law.** Equation (2) of the card is defined and
scale-free for any sample; at a fixed order it is the mean log-excess of the largest values over
the (k+1)-th largest, a well-defined statistic of the largest increments whose drift from the reference
is what a single-field metric reports. Not building it would leave the idea page's named estimator
unbuilt for a reason that is itself a finding worth recording, and the curve over k that the
metric stores shows where on the distribution each order sits.

- **What the alternative would have been.** An estimator defined for every sign of the index —
  the moment estimator (abstract of Dekkers, Einmahl & de Haan 1989, *Annals of Statistics* 17(4),
  1833–1855, doi:10.1214/aos/1176347397), or a generalised Pareto fit — would remove the
  restriction to positive indices, but not the clustering, which any estimator built for
  independent samples shares. It is proposed as a variant, not built, because the idea page names
  Hill's estimator and its full text was not read.
- **What it changes.** The card calls the value a tail index only for a power-law tail and
  otherwise "the mean log-ratio at the stated k"; its Limitations say not to read two values as two
  exponents, and that a value below independent Gaussian noise's does not show a lighter tail.
  Nothing in the harness changes.
