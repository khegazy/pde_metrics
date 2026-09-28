# `h1_seminorm` is not monotone under coarsening on vorticity: it measures the staircase

**Category:** acceptance criteria
**Priority:** low — the metric was added to record a negative result; this sharpens it
**Status:** open

## Context

`coarsen` block-averages a field by a factor and expands it back to the fine grid as a
piecewise-constant staircase. `h1_seminorm` is the root-mean-square *gradient* of the error, so
on a staircase it is dominated by the jumps between blocks rather than by the lost detail.

## Evidence

Measured on `comparison_1789632054` (`kinet_re5e4`, start 2000, reduction 50, 161 frames,
grid 256), vorticity, `coarsen`:

| factor | 2 | 4 | 8 | 16 | frames monotone | frame maximum at |
|---|---|---|---|---|---|---|
| `h1_seminorm` (median) | 1.10e-3 | 1.32e-3 | 1.27e-3 | 1.18e-3 | 0 of 161 | 4 (102 frames), 8 (59) |
| `mse` (median) | 2.1e-7 | 7.7e-7 | 1.6e-6 | 2.5e-6 | 161 of 161 | 16 (all) |
| `h_minus_one` (median) | 2.7e-4 | 9.5e-4 | 2.2e-3 | 5.0e-3 | 161 of 161 | 16 (all) |

The per-frame rank correlation is 0.2. On density and velocity, whose characteristic scales
are 139 and 189 cells against vorticity's 33, the same axis is monotone (rho = 1).

## Mechanism, and a test of it

The jump between neighbouring blocks grows with the factor only while the block is smaller
than the scale the field varies on; beyond that it saturates at the field's own amplitude,
while the number of jumps per unit length keeps falling as one over the factor. The squared
gradient of the error is roughly (jumps per length) x (jump size)^2, so it rises and then
falls, and the peak should move to larger factors for smoother fields.

Tested on synthetic unit-variance Gaussian random fields on 256 x 256, spectrum
exp(-(|k| L / N)^2), through the real `coarsen` and `h1_seminorm` (values are
`h1_seminorm` / `mse`):

| L (cells) | factor 2 | 4 | 8 | 16 | 32 |
|---|---|---|---|---|---|
| 8 | 0.650 / 0.071 | **0.744** / 0.282 | 0.659 / 0.620 | 0.577 / 0.864 | 0.551 / 0.967 |
| 32 | 0.209 / 0.005 | 0.294 / 0.024 | **0.382** / 0.096 | 0.377 / 0.316 | 0.261 / 0.649 |
| 128 | 0.051 / 0.000 | 0.072 / 0.001 | 0.103 / 0.006 | 0.145 / 0.022 | **0.191** / 0.085 |

The peak moves from factor 4 to 8–16 to beyond 32 as the field gets smoother, and `mse` is
monotone throughout, which is consistent with the mechanism. That it is *the* mechanism on the
real vorticity is an inference from this, not a separate measurement.

## What it means

This is not a defect in either the metric or the degradation. It is the card's structural
objection measured on the ladder: a positive-order Sobolev norm of an error containing jumps
is set by the jumps and the grid, not by how much information was lost. A coarsened
prediction expanded by a smooth interpolant instead of a staircase would not show it.

## Decision needed

Whether `h1_seminorm` stays in the repository as the recorded negative result it was added as
(its `status` is `candidate`), with this as part of the record — the recommendation here — or
is removed now that the record exists.
