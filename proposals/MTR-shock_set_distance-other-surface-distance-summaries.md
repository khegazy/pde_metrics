---
type: MTR
kind: variant of metrics/shock_set_distance
related: ["metrics/shock_set_distance"]
seen_in: "Taha & Hanbury 2015, BMC Medical Imaging 15, 29"
doi: "10.1186/s12880-015-0068-x"
found_by: "shock_set_distance, 2026-10-30"
---

# MTR: Hausdorff, quantile-Hausdorff, AVD and MASD summaries of the same shock-set distances

## What it measures

The same nearest-cell distances between the shock sets of two pressure fields that
`shock_set_distance` computes (`surface_distances`), summarised differently: by the worst
distance, by a high quantile of the distances, or by the two directed means kept apart.

## Definition

With $d(A, B) = \frac{1}{|A|}\sum_{a \in A} \min_{b \in B} \lVert a - b \rVert$ the directed
average distance (Taha & Hanbury 2015, Eq. 51) and $h(A, B) = \max_{a} \min_{b} \lVert a-b\rVert$
the directed Hausdorff distance (Eq. 49):

- Hausdorff distance, $\max(h(A,B), h(B,A))$ (Eq. 48); its quantile form replaces the maximum
  by the $q$-th quantile of the distances (text after Eq. 49; the 95th percentile is the common
  choice, Maier-Hein et al. 2024, Tab. SN 2.2, "HD95").
- Average distance AVD, $\max(d(A,B), d(B,A))$ (Eq. 50), "stable and less sensitive to outliers
  than the HD" in Taha and Hanbury's words.
- Mean average surface distance MASD, $\frac{1}{2}(d(A,B) + d(B,A))$, the default boundary
  metric recommended by Maier-Hein et al. (2024, Suppl. Note 2.3) over ASSD; its formula is
  from their cheat sheet, which I did not see, so this form is my reading of the name and
  should be checked against Benes and Zitova (2015) before building.

## Relation to existing work

`shock_set_distance` registers the pooled average (ASSD). For one shock in each field all of
these agree. They differ when the detector flags cells away from the shock: the pooled ASSD
weights each direction by its number of points, so spurious detections in the candidate dominate
it; MASD weighs the two directions equally; HD and HD95 report the worst false detection. None
is in the catalog or `docs/ideas/`; the deleted idea page named HD95 and ASSD.

## How it could be tested

On `sod_shock_tube` with `translate_x` (for a sharp step moved $s \ge 1$ cells, AVD and MASD give
$s - 1/2$ cells like ASSD, and the Hausdorff forms give $s$ cells; my derivation) and
`additive_noise`, where the false detections
separate them: HD would jump to the farthest false detection at the first noisy strength.

## Why it is helpful

The choice among them decides how much a scattering of false shocks costs relative to a
misplaced true one, which is the behaviour that matters on shocklet-populated data. Each is a
sibling bundle that imports `surface_distances` and adds a few lines.

## References

- Taha, A. A. & Hanbury, A. (2015). *BMC Medical Imaging* 15, 29, Eqs. 48-51.
  <https://doi.org/10.1186/s12880-015-0068-x> (full text read, PMC4533825).
- Maier-Hein, L. et al. (2024). Metrics reloaded. *Nature Methods* 21, 195-212, Suppl. Note 2.3
  and Tab. SN 2.2. <https://doi.org/10.1038/s41592-023-02151-z> (arXiv HTML read).
