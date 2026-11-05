# The neural-operator relative H^1 error has two implementations in its own field, and the papers do not say which produced their tables

**Category:** method
**Priority:** unset
**Status:** open. `h1_relative` is built as the library's `H1Loss` computes it; whether a
second sibling for the spectral form is needed is open.

## Context

The neural-operator literature reports a relative, inhomogeneous H^1 test error beside the
relative L^2 one (Li et al. 2022, NeurIPS 35, "Learning chaotic dynamics in dissipative
systems", App. A.3, Table 3, and Table 5; Kossaifi et al. 2023, arXiv:2310.00120, Fig. 1 and
Tables 3-4). Two implementations of it exist in that field, and they weight the derivative
differently:

- **The library's `H1Loss`** (neuraloperator, `neuralop/losses/data_losses.py`, read at commit
  0c10234 on 2026-11-04): periodic centred differences on a domain one unit long per axis, the
  value and the first derivatives summed with equal weight, the ratio of square roots per
  channel, summed over channels. This is `h1_relative`, and `judgements/017` records the
  unit-domain convention.
- **The Markov neural operator authors' `HsLoss`** (`markov_neural_operator`, `utilities.py`,
  commit 352eecf, read by a research sub-agent of this task on 2026-11-04): Fourier
  coefficients weighted by `sqrt(1 + a_0^2 |k|^2 [+ a_1^2 |k|^4])` with integer wavenumbers and no
  factor 2 pi, the ratio taken per sample. Its paper defines the Sobolev norm with the same
  inhomogeneous sum (their Sect. 3, Eqs. (3)-(4)) but does not say which weights `a_i` the
  tables used, nor that the reported error is relative.

Neither paper names the code that produced its H^1 column, so which of the two is "the field's
number" cannot be read from the papers. On a smooth error the two differ by the scale of the
derivative weight (2 pi m against m, and a factor `a_0`); near the grid scale they differ in the
stencil too, since a centred difference cannot see the alternating mode at all
(`metrics/h1_relative/test_metric.py`, the checkerboard case).

## What would settle it

A statement from the authors, or a reproduction of one published H^1 number with each
implementation on the paper's released data. If the spectral form turns out to be the one a
table reports, it becomes a sibling bundle beside `h1_relative`, so no recorded number moves.

## Related

`judgements/017` (the unit-length domain), `metrics/h1_relative/card.md` ("How its field reports
it"), written with the Sobolev norms' evaluation by their field's standard, 2026-11-04.
