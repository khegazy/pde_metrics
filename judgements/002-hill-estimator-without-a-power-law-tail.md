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
1.39 against 0.22). The far tail of these increments is lighter than a Gaussian's, and only the
shoulder of the distribution is heavier, which is where `increment_flatness` sees intermittency.
A Gaussian has no power-law tail, so neither, on this evidence, do these increments at the
registered order. The evidence run `tail_index_1793350342` (161 frames) measured the same thing on
the ladder: added noise moves every order of the stored curve toward the value of Gaussian
increments, raising the orders below 0.5 and lowering those above it on every field, and over
the 161 frames vorticity's median at 0.5 lies on the heavier side, so noise lowers it there while it
raises density and velocity (the card's Results, "Noise").

## The choice

**Build it, as the Hill estimate at the fixed order k = ceil(sqrt(n)), and say on the card what
the number is when the tail is not a power law.** Equation (2) of the card is defined and
scale-free for any sample; at a fixed order it is the mean log-excess of the largest values over
the next one, a well-defined statistic of the largest increments whose drift from the reference
is what a single-field metric reports. Not building it would leave the idea page's named estimator
unbuilt for a reason that is itself a finding worth recording, and the curve over k that the
metric stores shows where on the distribution each order sits.

- **What the alternative would have been.** An estimator defined for every sign of the index —
  the moment estimator (abstract of Dekkers, Einmahl & de Haan 1989, *Annals of Statistics* 17(4),
  1833–1855, doi:10.1214/aos/1176347397), or a generalised Pareto fit — would estimate an index
  near or below zero here. It is proposed as a variant, not built, because the idea page names
  Hill's estimator and its full text was not read.
- **What it changes.** The card calls the value a tail index only for a power-law tail and
  otherwise "the mean log-ratio at the stated k"; its Limitations say not to read two values as two
  exponents. Nothing in the harness changes.
