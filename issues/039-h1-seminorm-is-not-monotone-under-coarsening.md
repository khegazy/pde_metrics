# Under `coarsen`, derivative-based metrics measure the staircase, not the lost resolution

**Category:** acceptance criteria / degradation design
**Priority:** —
**Status:** RESOLVED (2026-09-28) — both decisions made and acted on; one observation left
unexplained, recorded under "Outcome"

## Decisions (2026-09-28, by the maintainer)

1. **Keep `h1_seminorm`**, as the recorded negative result it was added to be.
2. **Option (b): a second coarsening degradation, evaluated beside `coarsen`, not instead of
   it.** It is `degradations/coarsen_bandlimited`: the same block average, reconstructed as
   the one band-limited field with exactly those block means, so it discards the same
   information and adds no edges. Both run on the default ladder
   (`configs/degradation/default.yaml`), and every kinet metric card is now measured on both.

## Outcome

Measured on `comparison_1790639359` (`kinet_re5e4`, start 2000, reduction 50, 161 frames,
grid 256): all twelve kinet metrics on the ladder with both coarsenings. On every axis the
two runs share, it reproduces each card's previously pinned run bit for bit, so the only new
evidence is the `coarsen_bandlimited` row.

| metric, field | under `coarsen` | under `coarsen_bandlimited` |
|---|---|---|
| `h1_seminorm`, vorticity | rho 0.2, 0 of 161 frames in order | rho 1, every frame in order |
| `h1_seminorm`, density, damage at factor 2 | 1.11 (worse than an unrelated field) | 0.053 |
| `palinstrophy`, change at factors 2 / 4 / 8 / 16 | +89% / +39% / −28% / −59% | −2% / −39% / −84% / −96% |
| `increment_flatness`, density, factor 2 → 16 | 30 → 177 (reference 15.2) | 15.3 → 13.0 |
| `increment_w1`, density, factor 2 | 5.2e-5 | 7.2e-7 |
| `mse`, density, damage at factor 16 | 0.039 | 0.001 |

Three things this settled or showed:

- **The staircase explanation holds on the real data.** Remove the edges and `h1_seminorm`
  orders vorticity in every frame and `palinstrophy` never rises. Before, that was an
  inference from the synthetic test below; now it is measured.
- **The reach was wider than the two metrics this issue was opened for.** A one-cell increment
  is a finite difference, so the increment metrics measure the staircase as well:
  `increment_flatness`'s clean, monotone `coarsen` row was the block edges making the increment
  distribution a spike at zero with rare jumps, and under `coarsen_bandlimited` it is not
  ordered (rho −0.8 / 0.8 / 0.4). Its card previously read that row as the one family it
  handles cleanly, and has been corrected.
- **Even pointwise metrics were charged mostly for the staircase on the smooth fields.** At a
  factor of 16 `mse` on density is 0.039 under `coarsen` and 0.001 under the band-limited
  operator; on vorticity, whose structure the coarse grid cannot hold, 0.17 against 0.14.
  The same factor therefore does not mean the same damage under the two operators, which the
  new degradation's card states.

**Left unexplained.** Under `coarsen_bandlimited`, density is not in order in every frame for
the pointwise metrics (in order in 59% to 71% of frames), `spectrum_l2` (52%) and
`h1_seminorm` (32%), although the median ordering is correct. `h_minus_one` and `increment_w1`
are in order in every frame. The disorder is between factors 2 and 4, where the damage is
0.002 or less of the unrelated-field value for the pointwise metrics and about 0.05 for
`h1_seminorm`; in 46 of 161 frames `mse` at factor 4 is 1% to
3% *below* `mse` at factor 2 (for example 3.87e-10 against 3.93e-10). Ruled out so far:

- floating-point round-off: the values are about 1e-10, far above it;
- aliasing through the box inversion: on synthetic power-law fields with spectral slopes of
  −4, −6 and −8 the error rises with the factor in every trial, the out-of-band energy making
  up about two thirds of it;
- a white noise floor under a steep spectrum: in order in 40 of 40 synthetic trials.

It is small, 0.002 or less of the unrelated-field value for the pointwise metrics, and it is
recorded here rather than treated as reopening the issue. What would settle it is decomposing one real density frame's error into its
out-of-band part and its in-band alias part at factors 2 and 4.

The rest of this file is the record as it stood when the decisions were asked for.

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

The same fields through `coarsen_bandlimited`, which keeps the same block means but adds no
edges (entries are `h1_seminorm` / `mse`):

| L (cells) | factor 2 | 4 | 8 | 16 | 32 |
|---|---|---|---|---|---|
| 8 | 0.024 / 0.000 | 0.339 / 0.130 | 0.523 / 0.615 | 0.546 / 0.886 | 0.548 / 0.973 |
| 32 | 0.000 / 0.000 | 0.000 / 0.000 | 0.006 / 0.000 | 0.081 / 0.117 | 0.133 / 0.613 |
| 128 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.002 / 0.000 |

`h1_seminorm` is monotone at every correlation length once the edges are gone. The second
table also shows how much of `coarsen`'s damage was the staircase even for `mse`: on the
smoothest field, which the coarse grid can almost fully represent, `mse` at a factor of 32 is
0.085 under `coarsen` and 0.000 here.

## What this is not

- **Not a defect in `h1_seminorm`.** Its card already records the structural objection this
  illustrates: a positive-order Sobolev norm of an error containing jumps is set by the jumps
  and the grid.
- **Not a reason to change `coarsen` for everyone.** Its nearest-neighbour expansion is the
  correct control for pointwise metrics, and changing it would change every metric's committed
  coarsening evidence.

## The two decisions, as they were posed

These are independent. The issue closes when both are made and acted on; both now are, see
"Decisions" at the top.

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
