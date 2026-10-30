---
type: "MTR"
kind: "variant of energy_score"
related: ["energy_score", "variogram_score"]
seen_in: "Pacchiardi, Adewoyin, Dueben & Dutta 2024, Journal of Machine Learning Research 25(45), 1-64"
doi: "https://jmlr.org/papers/v25/23-0038.html"
found_by: "energy_score, 2026-10-30"
---

# MTR: Patched energy score, local in space and cheap on large grids

## What it measures

The energy score evaluated on many overlapping square patches of the field and summed, so each
term judges the joint distribution of a small neighbourhood. Local structure, which the
whole-field energy score dilutes into one norm over every cell, carries proportionally more
weight, and the cost stays linear in the number of cells.

## Definition

For a set P of patches of fixed size and spacing, with y|_p the reference restricted to patch p,

    S_patched(F, y) = sum_{p in P} ES(F|_p, y|_p)

(Pacchiardi et al. 2024, App. B.2.3, Eq. 35; Sect. 3.2.2). It is proper but not strictly
proper, because it never evaluates dependence between cells farther apart than a patch; adding
the whole-field energy score makes the sum strictly proper (their Sect. 3.2.3, Lemma 4). The
fair estimator of `energy_score` applies patch by patch (App. C.1.4).

## Relation to existing work

`energy_score` is the whole-field score; `variogram_score` localises through inverse-distance
weights but costs O(M N^2). A patched energy score is a third route to locality, cost O(M^2 N
patch-size), and it would reuse `energy_score` directly on each patch. Not in the catalog or
docs/ideas.

## How it could be tested

`synthetic_ensemble` with `ensemble_miscalibration`, as for `energy_score`; and the correlated
synthetic ensemble proposed in EXP-energy_score-correlated-synthetic-ensemble, where it should
respond to a wrong correlation length more than the whole-field score does. Patch size is a
choice that must be fixed once; Pacchiardi et al. use patches of 8 and 16 grid points on
WeatherBench and give the summation weights in App. E.4.2.

## Why it is helpful

It is a whole-field proper score that stays affordable on the 512 by 512 grids where
`variogram_score` is impractical, and it was used as a training loss for a generative weather
model, which is this project's second use of a metric.

## References

- Pacchiardi, L., Adewoyin, R. A., Dueben, P. & Dutta, R. (2024). Probabilistic forecasting
  with generative networks via scoring rule minimization. JMLR 25(45), 1-64.
  https://jmlr.org/papers/v25/23-0038.html (Sect. 3.2.2-3.2.3, App. B.2.3 Eq. 35, App. C.1.4).
