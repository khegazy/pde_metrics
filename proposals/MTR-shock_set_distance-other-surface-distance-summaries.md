---
type: MTR
kind: variant of metrics/shock_set_distance
related: ["metrics/shock_set_distance", "metrics/shock_set_masd", "metrics/shock_set_hausdorff95"]
seen_in: "Taha & Hanbury 2015, BMC Medical Imaging 15, 29, Eqs. 50-51"
doi: "10.1186/s12880-015-0068-x"
found_by: "shock_set_distance, 2026-10-30; narrowed by metrics-topology-shocks, 2026-11-04"
---

# MTR: The average distance (AVD) summary of the same shock-set distances

The Hausdorff distance, its 95th percentile and the mean average surface distance are built as
`shock_set_hausdorff`, `shock_set_hausdorff95` and `shock_set_masd` (2026-11-04), beside
Baddeley's Delta, `shock_set_baddeley_delta`. What remains is the average distance of Taha &
Hanbury and medpy's pooled form of HD95.

## What it measures

The same nearest-cell distances between the shock sets of two pressure fields that
`shock_set_distance` computes (`surface_distances`), summarised by the larger of the two directed
means: the worse of "how far are the reference's shocks from the candidate's, on average" and the
reverse.

## Definition

With $d(A, B) = \frac{1}{|A|}\sum_{a \in A} \min_{b \in B} \lVert a - b \rVert$ the directed
average distance (Taha & Hanbury 2015, Eq. 51), the average distance is
$\mathrm{AVD}(A, B) = \max(d(A,B), d(B,A))$ (Eq. 50), "stable and less sensitive to outliers
than the HD" in their words. A second variant is medpy's `hd95`, the 95th percentile of both
directions' distances pooled, which differs from `shock_set_hausdorff95`'s per-direction form
(6.5 against 6.7 on that bundle's worked example).

## Relation to existing work

AVD is `shock_set_masd` with the maximum of the two directed means in place of their mean. No
field read so far reports AVD as its standard; Taha & Hanbury list it among their twenty metrics.

## How it could be tested

On `sod_shock_tube` with `translate_x` (for a sharp step moved $s \ge 1$ cells, AVD gives
$s - 1/2$ cells like ASSD and MASD; my derivation) and `additive_noise`, where the false
detections make the two directed means differ.

## Why it is helpful

It is the worst-direction form of the average, so it charges a candidate with false shocks and one
missing a true shock alike, where MASD averages the two. Each variant is a sibling bundle of a few
lines on `shock_set_distance`'s `shock_set_score`, `set_distance` and `surface_distances`.

## References

- Taha, A. A. & Hanbury, A. (2015). *BMC Medical Imaging* 15, 29, Eqs. 50-51.
  <https://doi.org/10.1186/s12880-015-0068-x> (full text read, PMC4533825).
- medpy, `medpy/metric/binary.py`, `hd95` (source read 2026-11-04).
