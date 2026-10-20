# Energy distance

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The energy distance is a distance between two probability distributions, built from the
average distances between samples drawn from them. It belongs to the kernel family of
distances: it is in fact the *maximum mean discrepancy* (a distance that compares two
distributions through the averages of a chosen kernel function over their samples) with a
particular kernel. It is cheap to compute.

## Pitfalls

- The energy distance does some averaging, and is therefore a poor tool for heavy tails,
  meaning extreme values that occur far more often than a Gaussian distribution would
  predict. This is exactly why a Wasserstein distance is preferred for comparing
  distributions here, as in [increment_w1](../../metrics/increment_w1.md) and the
  [Wasserstein distance between gradient distributions](../optimal_transport/gradient_pdf_w1.md).

## Rationale

*The team's judgement.* Medium priority: it is worth keeping as a cheap baseline that shows
the difference between an averaging distance and a transport distance on heavy-tailed data,
but it is not expected to outperform the Wasserstein distance.
