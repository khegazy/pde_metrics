---
type: "MTR"
kind: "variant of variogram_score"
related: ["variogram_score", "energy_score", "crps"]
seen_in: "Scheuerer & Hamill 2015, Monthly Weather Review 143(4), 1321-1334"
doi: "10.1175/MWR-D-14-00269.1"
found_by: "energy_score, 2026-10-30"
---

# MTR: Proper scores of the vector of weighted pairwise differences

## What it measures

Whether the ensemble's distribution of pairwise differences between cells matches the
reference's, judged by a full distributional score (CRPS or energy score) rather than only by
the mean of each difference as the variogram score does.

## Definition

Map a field to the d^2-vector g(y)_ij = wtilde_ij |y_i - y_j|^p with wtilde_ij = w_ij^(1/p).
The variogram score is, up to a factor 1/d^2, the mean squared error of the members' mean of
g against g(y) (Scheuerer & Hamill 2015, end of Sect. 2). Applying instead the mean CRPS over
the d^2 components, or the energy score to the whole vector g, gives other proper scores
(Sect. 2 and Sect. 3f, Fig. 6, with p = 0.5 and wtilde_ij = 1/|i - j|^p). In their tests all
of these separate correct from wrong correlation models; the transformation, not the score
applied to it, carries the sensitivity (Sect. 3f).

## Relation to existing work

`variogram_score` is the MSE member of this family. The CRPS member would reuse `crps` on the
transformed vectors and is fair by construction; the energy-score member would reuse
`energy_score`. Neither is in the catalog or docs/ideas. They share the variogram score's
O(M N^2) cost and its blindness to a common offset.

## How it could be tested

The correlated synthetic ensemble of EXP-energy_score-correlated-synthetic-ensemble, against
`variogram_score`, and `ensemble_miscalibration` on `synthetic_ensemble` for dispersion.

## Why it is helpful

Building the CRPS member gives a fair score of pairwise structure with no new estimator,
which removes the ensemble-size bias of `variogram_score` (see MTR-energy_score-fair-variogram-score)
by reusing code that already exists.

## References

- Scheuerer, M. & Hamill, T. M. (2015). Monthly Weather Review 143(4), 1321-1334.
  https://doi.org/10.1175/MWR-D-14-00269.1 (Sect. 2, Sect. 3f, Fig. 6).
