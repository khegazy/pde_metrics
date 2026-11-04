# 017 — `h1_relative` takes every axis of the domain as one unit long, as `H1Loss` does by default

**Date:** 2026-11-04. **Made by:** the agent of task `metrics-physics-norms` (branch from
`update_metric_eval_principles`), under Kareem's delegation of per-metric details
(2026-11-03). **Reverse with:** give `h1_relative` a `ctx` argument and replace the factor
`x.shape[axis] / 2.0` in `metrics/h1_relative/metric.py` by `1 / (2 * ctx.grid.spacing[j])`,
update the worked example in `test_metric.py` and the card, delete this file and its row in
`README.md`, and regenerate the card's evidence.

## The question that would have been asked

The neural-operator relative H^1 error adds the squared error to its squared first derivatives
before dividing by the same sum for the reference. The two terms carry different units, so how
much the derivative counts against the value depends on the length unit the derivative is taken
in. `H1Loss` takes its grid spacing as `measure / N` with `measure = 1.0` by default, which treats
every axis of the domain as one unit long. Should this bundle do the same, or take the derivative
in the dataset's own length unit, the analysis grid's spacing?

On this repository's data the two answers give different metrics. `kinet_re5e4` declares a domain
of 256 by 256 (`docs/datasets/reynolds_ladder_2d.md`; `configs/dataset/forecast_re5e4.yaml`,
`length`), so with the physical spacing a mode m carries a derivative weight of about
(2 pi m / 256)^2, below 0.04 for m < 8, and the number is the relative L2 error to within a few
percent. With the unit domain the weight is about (2 pi m)^2, from 39 at m = 1, and the derivative
term dominates. (Both weights are the agent's arithmetic from the stencil, not a measurement.)

## The choice

**The domain is one unit long on every axis, as `H1Loss(d=2)` takes it.** The derivative is the
centred difference with `h_j = 1 / N_j`, whatever the analysis grid's spacing, and the metric
takes no `ctx`.

## Evidence and sources

- **The code.** neuraloperator `neuralop/losses/data_losses.py`, `H1Loss.__init__`
  (`measure=1.0`) and `uniform_quadrature` (`quadrature[-j] = self.measure[-j] / x.size(-j)`),
  passed as `h` to `FiniteDiff` (`neuralop/losses/differentiation.py`); read at commit 0c10234
  (2026-02-24) on 2026-11-04.
- **How the field calls it.** The library's own training scripts build the loss with no
  `measure`: `h1loss = H1Loss(d=2)` in `scripts/train_navier_stokes.py` (line 157) and
  `scripts/train_darcy.py` (line 148), read on `main` on 2026-11-04.
- **The field's problems are posed on unit domains.** FNO's Darcy problem maps into
  `H^1_0((0,1)^2)` (Li et al. 2021, ICLR, Sect. 5.2). On those problems the default and the
  physical length agree, so the library's number is the unit-domain one.
- **A dimensionless number should not depend on the length unit.** With the physical spacing the
  value would change if the same flow were stored in other units, and would differ between two
  datasets of one flow stored at different lengths. The unit domain makes the derivative one
  with respect to x / L, which no change of unit moves. This is the agent's reasoning.

## What it changes

Only the new bundle `h1_relative`. No other number moves. Its card states the convention under
"How its field reports it", and its worked example pins the stencil factor `N / 2`.
