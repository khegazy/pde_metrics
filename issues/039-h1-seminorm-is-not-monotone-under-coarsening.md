# Under `coarsen`, derivative-based metrics measure the staircase, not the lost resolution

**Category:** acceptance criteria / degradation design
**Priority:** low now; medium once derivative-based metrics such as PDE residuals are added
**Status:** open — two decisions needed, listed at the end

## Summary

The `coarsen` degradation block-averages a field and expands it back to the fine grid by
repeating each block value, so the degraded field is a staircase with a jump at every block
edge. Any metric built on spatial derivatives responds to those jumps, not only to the
resolution that was lost. Two metrics show it on the recorded run:

- `h1_seminorm` (a pairwise error metric) is **not monotone** under coarsening on vorticity.
- `palinstrophy` (a single-field diagnostic) **rises by 89%** at the mildest coarsening, which
  reads as "sharper than the reference" for a field that has lost resolution.

This is a property of how the ladder builds its coarsened field, not a bug in either metric and
not something a real prediction would do (see "Scope"). It still matters, because the
acceptance rule reads the ladder: a metric that is non-monotone on a ladder axis is flagged,
and here the flag comes from the operator.

## Where the staircase comes from

`degradations/coarsen/degradation.py` is `_upsample(block_average(x, factor))`, and
`degradations/_shared/grids.py::_upsample` is nearest-neighbour expansion (`np.repeat`). Its
docstring gives the reason, which is sound: nearest-neighbour "reintroduces no information and
no new smoothing, so the damage measured is resolution loss alone rather than resolution loss
convolved with an interpolation kernel". That is the right choice for pointwise metrics. For a
metric that differentiates, the same choice adds a jump at every block edge, and a jump is
exactly what a derivative is largest on.

## Scope: only the ladder, not real predictions

The pipeline never upsamples data. `fmeval/remap.py::coarsen_factor` refuses an analysis grid
finer than the data ("upsampling would invent information"), so a real prediction on a coarse
grid is compared on a coarse analysis grid and carries no staircase. The problem exists only
inside the `coarsen` degradation (and would equally affect `subsample`, which uses the same
expansion but was not in this run's ladder).

## Evidence

All measured on `comparison_1789632054` (`kinet_re5e4`, start 2000, reduction 50, 161 frames,
analysis grid 256). Values are medians over frames.

### `h1_seminorm`, vorticity, `coarsen`

| factor | 2 | 4 | 8 | 16 | frames in order | frame maximum at |
|---|---|---|---|---|---|---|
| `h1_seminorm` | 1.10e-3 | 1.32e-3 | 1.27e-3 | 1.18e-3 | 0 of 161 | factor 4 (102 frames), 8 (59) |
| `mse` | 2.1e-7 | 7.7e-7 | 1.6e-6 | 2.5e-6 | 161 of 161 | factor 16 (all) |
| `h_minus_one` | 2.7e-4 | 9.5e-4 | 2.2e-3 | 5.0e-3 | 161 of 161 | factor 16 (all) |

Per-frame rank correlation 0.2. On density and velocity the same axis is monotone (rho = 1);
their characteristic scales are 139 and 189 cells, against vorticity's 33.

### `palinstrophy` and `enstrophy`, vorticity, `coarsen` (change from the reference)

| factor | 2 | 4 | 8 | 16 |
|---|---|---|---|---|
| `palinstrophy` | **+89%** | **+39%** | −28% | −59% |
| `enstrophy` | −4% | −14% | −26% | −40% |

The table on the `palinstrophy` card reports rho = −1 on this axis, which looks like the
correct behaviour for a single-field quantity that falls with damage. It is computed across the
four strengths only, so it cannot show that the two mildest moved the value *up*, away from the
reference, before the stronger ones brought it down. The card's Results text says so in words.

### Both metrics behave on the smooth resolution-loss axes

The low-pass filters remove the same high wavenumbers without creating jumps. On them
`h1_seminorm` has rho = 1 on every field and `palinstrophy` has rho = −1 with no reversal, so
the metrics respond correctly to lost resolution when the operator does not add edges.

## Mechanism, and a test of it

The following argument is ours, not from a citation. The squared gradient of a staircase error
is roughly (number of jumps per unit length) × (jump size)². The number of jumps per length
falls as one over the factor. The jump size grows with the factor while a block is smaller than
the scale the field varies on, then saturates at the field's own amplitude. So the product
rises and then falls, and the peak should sit at larger factors for smoother fields.

Tested through the real `coarsen` and `h1_seminorm` on synthetic unit-variance Gaussian random
fields on 256 × 256 with spectrum exp(−(|k| L / N)²), where L sets the correlation length in
cells. Entries are `h1_seminorm` / `mse`; bold marks the `h1_seminorm` peak.

| L (cells) | factor 2 | 4 | 8 | 16 | 32 |
|---|---|---|---|---|---|
| 8 | 0.650 / 0.071 | **0.744** / 0.282 | 0.659 / 0.620 | 0.577 / 0.864 | 0.551 / 0.967 |
| 32 | 0.209 / 0.005 | 0.294 / 0.024 | **0.382** / 0.096 | 0.377 / 0.316 | 0.261 / 0.649 |
| 128 | 0.051 / 0.000 | 0.072 / 0.001 | 0.103 / 0.006 | 0.145 / 0.022 | **0.191** / 0.085 |

The peak moves from factor 4 to 8 to beyond 32 as the field gets smoother, and `mse` is monotone
throughout, as the mechanism predicts. That the same mechanism operates on the real vorticity is
an inference from this test and from the density/velocity contrast above, not a separate
measurement.

## What this is not

- **Not a defect in `h1_seminorm`.** Its card already records the structural objection this
  illustrates: a positive-order Sobolev norm of an error containing jumps is set by the jumps
  and the grid.
- **Not a reason to change `coarsen` for everyone.** Its nearest-neighbour expansion is the
  correct control for pointwise metrics, and changing it would change every metric's committed
  coarsening evidence.

## The two decisions

These are independent. The issue closes when both are made and acted on.

### Decision 1: keep or remove `h1_seminorm`

`h1_seminorm` was added only to record, as a measurement, the tracker's verdict that an H¹
penalty is "tested and insufficient". That record now exists, in its card and here.

- **Keep it (recommended).** It stays `status: candidate`, costs one FFT per direction, and is
  the mirror image against which `h_minus_one` is read (their product is the MSE for a single
  mode). Removing it would delete the measured record from the catalog.
- **Remove it.** The evidence would survive only in git history and in this file.

### Decision 2: how the ladder should treat derivative-based metrics under resolution loss

This affects `h1_seminorm` and `palinstrophy` now, and every future metric that differentiates
the field, such as the weak PDE residual and the solver-consistency residual on the first-wave
list.

- **(a) Keep `coarsen` as it is and document the limitation (recommended for now).** The cards
  of derivative-based metrics say that their `coarsen` row measures the staircase, and point to
  the low-pass rows as their resolution-loss evidence. The two existing cards already do this in
  their Results text. Cost: none. Downside: the `coarsen` row still appears in tables and heat
  maps without explanation, and a reader applying the acceptance rule mechanically will flag
  `h1_seminorm` for it.
- **(b) Add a second resolution-loss degradation with a band-limited reconstruction.** For
  example, block-average and then reconstruct by keeping only the Fourier modes the coarse grid
  can represent, so no jumps are added. It would sit beside `coarsen` rather than replace it.
  Cost: a new degradation bundle, and regenerated evidence for every metric. It is close to what
  `lowpass_ideal` already does, but parametrised by the grid factor, which is the quantity a
  surrogate's resolution is actually specified in. Worth doing before the PDE-residual metrics
  are validated, because they will hit this harder than a first-derivative norm does.
- **(c) Change `coarsen` itself to a smooth reconstruction (not recommended).** It removes the
  artefact, but it also changes the control that pointwise metrics rely on and every committed
  coarsening result.

## Related

- `metrics/h1_seminorm/card.md`, Results → Resolution loss.
- `metrics/palinstrophy/card.md`, Results → Resolution loss.
- `degradations/_shared/grids.py::_upsample` — the expansion and the reason for it.
