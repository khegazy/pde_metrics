# Distance between extracted shock sets

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Once a [shock detector](shock_detector.md) has extracted shock masks or surfaces from both the
prediction and the reference, compare the two as *geometric objects* rather than as arrays of
values. Two distances do this well.

- **Average symmetric surface distance.** For every point on one surface, take its distance to
  the nearest point of the other surface; do the same in the other direction; average all of
  these distances.
- **95th-percentile Hausdorff distance.** The Hausdorff distance is the largest of those
  point-to-surface distances, so a single stray detection can dominate it. Taking the 95th
  percentile instead of the maximum makes it robust to isolated detector artifacts.

Both measure how far apart two shocks lie, which is the quantity a pointwise norm cannot
report.

The same distances apply to any thin surface extracted from both fields, not only to shocks.
Ridges of the finite-time Lyapunov exponent, used to describe the geometry of
[variable-density mixing](../regime_specific/variable_density_mixing.md), are one example.

## Precedent

Medical imaging solved the problem of deciding whether two thin surfaces occupy the same place
some years ago, in evaluating image segmentation, where an automatically drawn outline is
compared with a reference outline. Taha and Hanbury survey twenty such measures and select
among them systematically (Taha and Hanbury 2015). Their treatment states the specific caveat
needed here: the Hausdorff distance "is generally sensitive to outliers", using it directly is
not recommended when noise and outliers are common, and the quantile version is the
recommended repair.

In weather verification, object-based verification (MODE) uses convolution, smoothing and
thresholding to define objects in a forecast and an observation, then a matching algorithm to
pair them (Davis et al. 2006a, 2006b, 2009). It is the closest existing analogue to extracting
shocklets from both fields and comparing the sets.

## Rationale

*The team's judgement.* High priority: this is the direct answer to the need to calculate the
distance between shocks. Together with the [shock detector](shock_detector.md), it closes that
gap using metrics imported from medical imaging, where they are mature.

## Keywords

average symmetric surface distance, ASSD, 95th percentile Hausdorff distance, surface distance
metrics, boundary F-score.

## References

- Davis, C., Brown, B. & Bullock, R. (2006a). Object-based verification of precipitation
  forecasts. Part I: Methodology and application to mesoscale rain areas. *Monthly Weather
  Review* 134(7), 1772–1784. <https://doi.org/10.1175/MWR3145.1>
- Davis, C., Brown, B. & Bullock, R. (2006b). Object-based verification of precipitation
  forecasts. Part II: Application to convective rain systems. *Monthly Weather Review* 134(7),
  1785–1795. <https://doi.org/10.1175/MWR3146.1>
- Davis, C. A., Brown, B. G., Bullock, R. & Halley-Gotway, J. (2009). The Method for
  Object-Based Diagnostic Evaluation (MODE) applied to numerical forecasts from the 2005
  NSSL/SPC Spring Program. *Weather and Forecasting* 24(5), 1252–1267.
  <https://doi.org/10.1175/2009WAF2222241.1>
- Taha, A. A. & Hanbury, A. (2015). Metrics for evaluating 3D medical image segmentation:
  analysis, selection, and tool. *BMC Medical Imaging* 15, 29.
  <https://doi.org/10.1186/s12880-015-0068-x>
