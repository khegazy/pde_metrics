# A metric that produces a table of values has no single number to report

**Category:** method
**Priority:** high — it blocks seven of the planned metrics whose mathematics is otherwise settled
**Status:** open, needs a decision and then a change to the evaluation code or the metrics

## Summary

The evaluation code stores one number for each comparison of a prediction with the reference.
Seven planned metrics naturally produce a table of numbers instead: one value for each distance,
wavenumber, threshold or filter size. Someone has to decide what the stored result is for those
metrics. This issue explains the problem with a measured example, sets out the options, and gives
a recommendation. The rules of this repository point towards storing the whole table (option 2
below), which needs the evaluation code extended first.

## The problem

Each time the evaluation code runs a metric, it stores one number per combination of field
(density, velocity, ...), snapshot in time, and damage level (`fmeval/pipeline.py`). Everything
downstream works on that single number: the test of whether the score gets steadily worse as
damage increases (the rank correlation), the damage score, the sensitivity, the figures and the
cards.

Seven planned metrics do not produce one number. Each produces a list of values, one for each
value of some setting. Plotted against that setting, the list is a line on a graph, which the
idea pages call a "curve".

| Idea | One value for each ... | What its page says about reducing it to one number |
|---|---|---|
| [Increment distributions at every separation](../docs/ideas/optimal_transport/gradient_pdf_w1.md) | distance between the two points | "A single value pooled over separations hides which scale failed; the per-separation curve is what localises it" |
| [Structure functions](../docs/ideas/turbulence_statistics/structure_functions.md) | distance, for several powers; also the slopes fitted to them | compare them "order by order", and the slopes; the fitting range "must be fixed by the evaluator" |
| [Spectral energy flux](../docs/ideas/turbulence_statistics/spectral_energy_flux.md) | wavenumber | "Report the error of the curve $\Pi(k)$ across the inertial range" |
| [Minkowski functionals](../docs/ideas/topology/minkowski_functionals.md) | threshold (area, boundary length and number of holes of the region above it) | "the metric compares the predicted curves with the reference's" |
| [Delta-variance](../docs/ideas/basis_decompositions/delta_variance.md) | filter size | "compares the predicted and reference Δ-variance curves, or the slopes fitted to them" |
| [Error by wavenumber band](../docs/ideas/basis_decompositions/spectral_band_error.md) | band: low, middle, high (three values) | "reported separately in each band" (The Well, Ohana et al. 2024, Appendix E.3) |
| [Spectral coherence](../docs/ideas/basis_decompositions/spectral_coherence.md) | wavenumber | "localise the wavenumber at which phase decoherence begins" |

## A measured example

Measured on 2026-10-26 to make the problem concrete. One snapshot, one direction, and a blur
chosen for illustration rather than a damage level from the ladder.

- **Reference:** density from `kinet_re5e4`, raw frame 2000 (the first frame of the evidence
  window), on its 256 × 256 grid.
- **Prediction:** the same field blurred with `scipy.ndimage.gaussian_filter(rho, sigma=3,
  mode="wrap")`.
- **Quantity:** the second-order structure function along the second array axis, which is the
  average squared difference of the field between two points a distance `l` grid cells apart:

  $$S_2(l) = \big\langle \left(\rho(x + l) - \rho(x)\right)^2 \big\rangle_x, \tag{1}$$

  where the average runs over every grid point, with periodic wrap-around.

| distance `l` (cells) | reference | blurred | blurred ÷ reference |
|---|---|---|---|
| 1 | 4.804e-09 | 4.387e-09 | 0.91 |
| 2 | 1.917e-08 | 1.752e-08 | 0.91 |
| 4 | 7.594e-08 | 6.964e-08 | 0.92 |
| 8 | 2.936e-07 | 2.721e-07 | 0.93 |
| 16 | 1.061e-06 | 1.005e-06 | 0.95 |
| 32 | 3.374e-06 | 3.270e-06 | 0.97 |
| 64 | 8.892e-06 | 8.734e-06 | 0.98 |
| 128 | 1.629e-05 | 1.606e-05 | 0.99 |

The blur removes about 9% of the variation over short distances and almost none over long ones,
as a blur should. The table says where the prediction fails; one number has to give that up.

How each way of reducing the table to one number scores this example:

- **The relative distance used by `spectrum_l2`**,
  $\lVert S_2^{\text{blur}} - S_2^{\text{ref}} \rVert_2 / \lVert S_2^{\text{ref}} \rVert_2$ over
  the eight rows: **0.016**. 84% of the squared difference comes from the last two rows
  (`l` = 64 and 128), because their values are about 3,000 times larger than the first row's.
  The score is driven by the rows the blur changed least.
- **The root mean square of the logarithm of the ratio column**,
  $\sqrt{\tfrac{1}{n}\sum_l \left[\ln\left(S_2^{\text{blur}}(l)/S_2^{\text{ref}}(l)\right)\right]^2}$:
  **0.065**. Every row counts equally, so the score is driven by the short distances, where the
  damage is. This form is a suggestion from the person who wrote this issue, not a published
  standard for these metrics.

To reproduce, with the repository's `.venv` active:

```python
import numpy as np
from scipy.ndimage import gaussian_filter
from fmeval.config import compose_config, build_job
from fmeval.data.readers import open_trajectory

job = build_job(compose_config("dataset=kinet_re5e4"))
rho = open_trajectory(job.dataset, job.paths).read_frame(2000, ["density"])["density"]
rho = np.asarray(rho, dtype=float).squeeze()
blur = gaussian_filter(rho, sigma=3, mode="wrap")
s2 = lambda f, l: np.mean((np.roll(f, -l, axis=-1) - f) ** 2)
for l in (1, 2, 4, 8, 16, 32, 64, 128):
    print(l, s2(rho, l), s2(blur, l), s2(blur, l) / s2(rho, l))
```

## The options

1. **Reduce the two tables to one number per comparison.** This works today with no change to
   the evaluation code, and `spectrum_l2` already does it for energy spectra. It loses where the
   prediction failed, which several idea pages say is the point of the metric. It also hides a
   choice: which rows are compared, and how they are weighted. The example shows that the
   plain relative distance weights the largest values, which here means the scales least
   affected.
2. **Store the whole table, and register one summary number beside it for the damage checks.**
   The code is half built for this: a metric declared with `returns="vector"` already has each
   entry expanded into its own row with a `component` column (`fmeval/pipeline.py`). The rest
   is missing, as [012](012-vector-valued-metrics.md) records: nothing draws a table of values
   in a report, and the analysis treats each entry as an unrelated metric. This option is a
   change to the evaluation code and, under `AGENTS.md`, runs alone before these seven metrics.
   The summary number still needs the choice in option 1.
3. **Register a few separately named metrics.** This suits only a table with a handful of named
   entries, which is the band error: `spectral_band_error_low`, `_mid` and `_high`, computed by
   one shared function, each with its own damage checks. It does not suit a table with dozens of
   rows.

For spectral coherence there is a fourth possibility, also a suggestion from the person who wrote
this issue: report the wavenumber at which the coherence first falls below a fixed threshold.
That wavenumber is one number, and it should move to larger scales as damage increases. The
threshold would be fixed once by the evaluator, as `CLAUDE.md` requires of every threshold, and
no standard value is known to the writer.

## The repository's rule on this

`AGENTS.md` ("`target` and `measures`") says to report the quantity the literature reports, and
not to transform a metric to make it fit the evaluation code, "because then the number in the
table is no longer the number the name promises". The owner's ruling of August 2026, made for the
spread-to-skill ratio, was that the repository adjusts to report the true nature of a metric
rather than reshaping the metric to fit. For these seven metrics, the literature reports the
table (or slopes fitted to it), so the rule points to option 2. Option 1 alone would be a
reduction the literature does not make.

## Recommendation

1. **Option 2 for the five metrics with long tables** (increment distributions, structure
   functions, energy flux, Minkowski functionals, delta-variance). Build the storage and a report
   figure that overlays the reference and predicted tables first, as one change to the
   evaluation code that resolves [012](012-vector-valued-metrics.md). Each metric then stores its
   table and registers one summary number for the damage checks. For the summary, prefer the
   logarithm-of-ratio form over the plain relative distance wherever the values span several
   orders of magnitude, for the reason the example shows.
2. **Option 3 for the band error.**
3. **For spectral coherence**, either the threshold wavenumber (with the threshold fixed and its
   source recorded) or the summary number of option 2.
4. If option 2 is deferred, option 1 with the logarithm-of-ratio summary is a usable interim, as
   long as each card says the table was reduced and how.

## Confidence

- **Measured:** every number in the example, from the script above.
- **Read from the code:** how results are stored, how `spectrum_l2` reduces its spectra, and what
  `returns="vector"` does today.
- **Limited:** the example is one snapshot, one direction and an illustrative blur, not the
  project's damage levels. How much the plain relative distance hides on the real ladder has not
  been measured.
- **Suggestions, not published standards:** the logarithm-of-ratio summary, and the coherence
  threshold wavenumber.

## Related

[012](012-vector-valued-metrics.md) (no consumer for vector output). Found while screening
`docs/ideas/` for agent-built metrics (2026-10-23); written up 2026-10-26 and rewritten in plain
terms, with the measured example, the same day.
