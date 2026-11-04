# The one-cell separation at which `increment_w1` and `energy_distance` register their number is a convention with no source

**Category:** method
**Priority:** unset
**Status:** open. Both metrics are built at one cell, labelled a convention on their cards; what
would replace it is open.

## Context

`increment_w1` (the 1-Wasserstein distance) and `energy_distance` compare the distributions of
the reference's and the prediction's increments at a separation of one cell
(`SEPARATION_CELLS` in `metrics/increment_flatness/metric.py`), longitudinal for velocity. The
field these statistics come from reads increments at many separations, not at one:

- Granero-Belinchón & Cabeza Gallucci (2024), *Mach. Learn.: Sci. Technol.* 5(2), 025032, compare
  a model's increment distributions with the reference's at the octave separations
  $\ell = 2, 4, \dots, 4096$ sampling lengths, from the dissipative to the integral range, by the
  Jeffreys distance between the densities of the standardised increments, drawn against
  $\log \ell$ (App. A, Fig. A4), and draw those densities at nine separations from 2 to 10000
  sampling lengths (Sect. 4, Fig. 8). No separation is singled out
  for a one-number summary.
- Statistics, where the energy distance comes from, compares two samples and has no notion of
  separation (Székely & Rizzo 2013, *J. Stat. Plann. Inference* 143(8), Sect. 6.1).
- In turbulence the separation is read in units of the Kolmogorov scale $\eta$ or the integral
  scale $L$ (Granero-Belinchón & Cabeza Gallucci 2024, Sect. 2.1-2.2, Figs. 6-9). One cell of the
  analysis grid is neither, and moves with `analysis_grid.resolution`.

One cell was chosen for the same reason as `increment_flatness`'s: it is the smallest separation
the grid resolves, where an over-smoothed prediction departs first, and a fixed constant cannot
be tuned per model. That is a reason, not a source.

## What exists already

- `increment_w1_by_separation` stores the distance at every octave separation as its curve
  companion (and the transverse curve for velocity), so the one-cell value is the first point of a
  curve already recorded on every row. Its own registered number, a normalised mean over that
  curve, is the separate convention of `issues/098`.
- `increment_flatness` registers its number at one cell too, and now stores its curve over
  octave separations beside it (`increment_flatness.by_separation`). The flatness grows as the
  separation decreases (Granero-Belinchón & Cabeza Gallucci 2024, Sect. 2.1), so the smallest
  separation is where it departs furthest from the Gaussian 3, which makes the choice less
  arbitrary there than for a distance between two fields.
- No energy distance at other separations is built; it is proposed in
  `proposals/MTR-energy_distance-by-separation.md`.

## What would settle it

A published single-separation convention for comparing increment distributions of a model and a
reference, or a decision to register the distance at a separation defined physically (a multiple
of a measured dissipation scale, once a dataset with an established one exists:
`proposals/EXP-increment_flatness-isotropic-3d-turbulence-cutouts.md`). Either is a sibling
bundle importing the same function, so no recorded number moves.

## Related

`issues/098` (the summary over separations), `issues/036` (the flatness curve), written with the
increment metrics' evaluation by their field's standard, 2026-11-04.
