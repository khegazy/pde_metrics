---
type: MTR
kind: variant of metrics/shock_set_distance
related: ["metrics/shock_set_distance", "docs/ideas/shock_geometry/shock_turbulence_interaction.md", "issues/002"]
seen_in: "Davis, Brown, Bullock & Halley-Gotway 2009, Weather Forecast. 24(5), 1252-1267"
doi: "10.1175/2009WAF2222241.1"
found_by: "shock_set_distance, 2026-10-30"
---

# MTR: Object-matched shock distance, after MODE

## What it measures

How well a prediction places and shapes each individual shock (or shocklet), rather than how far
its shocked cells lie from the nearest shocked cell of the reference. Shocks are grouped into
objects in both fields, objects are paired, and each pair is scored on its separation and its
attributes; the summary is over pairs, and unpaired objects are counted as misses and false
alarms.

## Definition

The MODE recipe (Davis et al. 2006a, Part I; Davis et al. 2009), adapted to shocks as my own
proposal:

1. **Objects.** Connected components of the `shock_mask` of each field (MODE smooths and
   thresholds the field; here the detector's mask plays that role).
2. **Attributes.** Per object: centroid, length (number of cells or arc length), orientation,
   and mean pressure ratio across it (the shock strength).
3. **Pairing.** For every forecast-reference pair, a total interest combining attribute
   differences through interest functions in [0, 1] (Davis et al. 2009, abstract: a fuzzy-logic
   "total interest" from separation distance, orientation and other attributes). Each object keeps
   its maximum interest against all objects of the other field.
4. **Summary.** Davis et al. (2009) take the median of those maxima as overall quality. A
   distance-valued alternative of my own: the mean centroid separation over pairs whose
   interest exceeds a fixed threshold, with the counts of unpaired objects reported beside it.

The interest functions and weights are not given in the abstracts I read, so they must be taken
from the full MODE papers (or METplus's MODE documentation) before building; until then the
pairing is an open choice.

## Relation to existing work

`shock_set_distance` matches every shocked cell to the nearest shocked cell of the other field,
whichever shock it belongs to (its card's Limitations). On a field of many shocklets, a missing
shocklet next to a present one barely moves that number; object matching would count it as a
miss. Davis et al. (2006b, Part II) add matching in time, grouping objects into systems across
frames, which would need a trajectory input (proposals/EXP-orchestrator-20261023-temporal-ladder.md).
Neither is in the catalog or `docs/ideas/`; the deleted idea page named MODE only as precedent.

## How it could be tested

Not on `sod_shock_tube`, which has one shock per field, so pairing is trivial and the variant
equals the centroid distance. It needs a field with several shocks: the 2-D dataset of
`.agent/proposals/EXP-shock_set_distance-2d-shock-dataset.md`, with `translate_x` (every pair's
separation rises by a known amount) and `additive_noise` (false-alarm objects rise while paired
separations should not).

## Why it is helpful

The north-star case is shocklet-populated turbulence, where how many shocks a model gets and
whether each is in the right place are separate failures. A pooled cell distance merges them;
object matching keeps them apart, which is the double-penalty remedy weather verification
adopted (MODE was built to avoid the double penalty of grid-point verification).

## References

- Davis, C., Brown, B. & Bullock, R. (2006a). Object-based verification of precipitation
  forecasts. Part I. *Mon. Weather Rev.* 134(7), 1772-1784. <https://doi.org/10.1175/MWR3145.1>
  (abstract read).
- Davis, C., Brown, B. & Bullock, R. (2006b). Part II: Application to convective rain systems.
  *Mon. Weather Rev.* 134(7), 1785-1795. <https://doi.org/10.1175/MWR3146.1> (abstract fragments
  read).
- Davis, C. A., Brown, B. G., Bullock, R. & Halley-Gotway, J. (2009). The Method for
  Object-Based Diagnostic Evaluation (MODE) applied to numerical forecasts from the 2005
  NSSL/SPC Spring Program. *Weather Forecast.* 24(5), 1252-1267.
  <https://doi.org/10.1175/2009WAF2222241.1> (abstract read).
