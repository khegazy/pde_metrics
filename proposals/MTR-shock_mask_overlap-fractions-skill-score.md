---
type: MTR
kind: variant of metrics/shock_mask_overlap
related: ["metrics/shock_mask_overlap", "metrics/shock_set_distance", "docs/ideas/shock_geometry/shock_boundary_f_score.md"]
seen_in: "Antonio & Aitchison 2025, Mon. Weather Rev. 153(6), 1021-1033; Roberts & Lean 2008, Mon. Weather Rev. 136(1), 78-97"
doi: "10.1175/2007MWR2123.1"
found_by: "shock_mask_overlap, 2026-10-31"
---

# MTR: Fractions skill score of shock masks over neighbourhood width

## What it measures

How well two fields agree on where their shocks are, at a range of spatial tolerances: for
each neighbourhood width, the fraction of shocked cells in a window around every cell is
compared between the reference and the candidate. At width one it is the Dice coefficient that
`shock_mask_overlap` registers; at larger widths a shock missed by a few cells regains credit,
which removes that metric's saturation (a two-cell miss and a sixteen-cell miss both score 0 on
the Sod tube, run `shock_mask_overlap_1793494245`).

## Definition

With $o_i, f_i \in \{0, 1\}$ the reference and candidate shock indicators and
$y_i(n) = \frac{1}{(2n+1)^d}\sum_{j \in W_n(i)} x_j$ the neighbourhood fraction over the window
$W_n(i)$ of width $2n+1$ (Antonio & Aitchison 2025, Eq. 21, written there for $d = 2$),

$$
\mathrm{FSS}(n) = \frac{2\langle o(n) f(n)\rangle}{\langle f(n)^2\rangle + \langle o(n)^2\rangle}
$$

(their Eq. 5; their Eqs. 1-2 give the summed form; originally Roberts & Lean 2008, not opened).
For binary fields at $n = 0$, $o^2 = o$ and $f^2 = f$, so
$\mathrm{FSS}(0) = 2|A \cap B| / (|A| + |B|)$, the Dice coefficient (my algebra; the paper does
not name it). The registered number would be the curve's value at a fixed width, or the curve
summarised; the curve over $n$ is a natural `kind="curve"` companion with coordinate
("half-width", "cells").

## Relation to existing work

`shock_mask_overlap` is FSS(0). The planned boundary F-score
(`docs/ideas/shock_geometry/shock_boundary_f_score.md`) also adds a tolerance, but as a hard
matching radius on cell-to-cell distances; FSS smooths both indicator fields and compares the
smoothed coverage, so a candidate with the right number of shocked cells near the right place
scores high even when no single cell matches. `shock_set_distance` reports a distance instead of
a score. Nothing in `docs/catalog.json` or `docs/ideas/` is a neighbourhood score.

## How it could be tested

On `sod_shock_tube` with `translate_x` (shifts of 1 to 16 cells): FSS(n) should stay near 1 for
shifts below about n cells and fall beyond, so the curve resolves the shifts the Dice
coefficient cannot (my expectation, not measured). The window must not wrap on the walled
tube; a box filter with the reader's boundary extension, not an FFT, keeps it runnable there.
`additive_noise` tests how false detections dilute the coverage.

## Why it is helpful

It is the weather community's standard answer to the double penalty for thresholded fields,
the exact pathology this repository is built around, and it degrades gracefully from strict
cell overlap (n = 0) to coverage agreement at the scale of the window. On shocklet-populated
data, where shocks are many and small, it avoids matching individual shocks.

## References

- Roberts, N. M. & Lean, H. W. (2008). Scale-selective verification of rainfall accumulations
  from high-resolution forecasts of convective events. *Mon. Weather Rev.* 136(1), 78-97.
  <https://doi.org/10.1175/2007MWR2123.1> (not opened; the definition is taken from the next
  source).
- Antonio, B. & Aitchison, L. (2025). How to derive skill from the fractions skill score.
  *Mon. Weather Rev.* 153(6), 1021-1033 (volume and pages from a search result, not checked).
  <https://doi.org/10.1175/MWR-D-24-0120.1>; arXiv 2311.11985v3, Eqs. 1, 2, 5, 21 (arXiv HTML
  read through a fetch tool).
