---
name: palinstrophy
kind: metric
---

## Definition

For a vorticity field $\boldsymbol{\omega}$ with components $\omega^{(c)}$ on a periodic
grid, palinstrophy is half the mean squared gradient,

$$
P = \frac{1}{2} \Bigl\langle |\nabla \boldsymbol{\omega}|^2 \Bigr\rangle
  = \frac{1}{2} \sum_{c} \sum_{j} \Bigl\langle
    \bigl( \partial_j \omega^{(c)} \bigr)^2 \Bigr\rangle \tag{1}
$$

where $j$ runs over the spatial directions, $c$ over the components — one in 2D, three in
3D — and $\langle \cdot \rangle$ averages over cells. The factor of one half is the one
Boffetta and Ecke fix on p. 429 of their review [@boffetta2012]: they define enstrophy as
$\Omega = \tfrac12 \langle \omega^2 \rangle = \int k^2 E(k)\,dk$ and palinstrophy, with their
Equation (6) $d\Omega/dt = -2\nu P$, as $P = \int k^4 E(k)\,dk$, which together give
Equation (1). It is also the convention [enstrophy](../../metrics/enstrophy/card.md) uses, so the two
are directly comparable. Their setting is two-dimensional; in 3D Equation (1) sums all three
components, which is the direct generalisation rather than a definition taken from them.

Derivatives are spectral, $\partial_j \to i k_j$ with
$k_j = 2\pi \, \mathrm{fftfreq}(N_j, h_j)$, the convention the repository already uses
throughout [@pope2000]. This is not only a consistency preference. `fmeval/derived.py` records that the
solver's lattice-stencil vorticity and a spectral one differ by 8.1% rms, so a second
differentiation convention introduced here would stack a second discrepancy of that kind on
top of the first.

The pairing with enstrophy is what makes this worth computing. In terms of the vorticity
spectrum $E_\omega(\kappa)$, the two quantities are successive moments,

$$
\text{enstrophy} \propto \int E_\omega(\kappa) \, d\kappa,
\qquad
P \propto \int \kappa^2 \, E_\omega(\kappa) \, d\kappa \tag{2}
$$

so enstrophy asks how much rotational activity there is and palinstrophy asks how sharp it
is [@boffetta2012]. Equation (2) also orders the two under smoothing. For a filter whose
squared gain $G^2$ is a non-increasing function of $\kappa$ alone — a Gaussian, a Butterworth
or an ideal low-pass, though not a box or a median filter — Chebyshev's integral inequality,
applied under the measure $E_\omega(\kappa)\,d\kappa$ to the non-increasing $G^2$ and the
increasing $\kappa^2$, gives

$$
\frac{\int \kappa^2 G^2 E_\omega \, d\kappa}{\int \kappa^2 E_\omega \, d\kappa}
\;\le\;
\frac{\int G^2 E_\omega \, d\kappa}{\int E_\omega \, d\kappa} \tag{3}
$$

so such a filter always removes at least as large a fraction of palinstrophy as of enstrophy.
Equation (3) bounds the ordering only; how wide the gap is on real data is measured under
Results.

### Boundary handling

Periodic on every axis, inherited from the spectral derivative. The spacing is read from the
analysis grid rather than assumed, and here that matters more than it does for a first-order
quantity: the value carries an inverse length *squared*, so on a grid coarsened by a factor,
using the native spacing would inflate the result by the square of that factor.

It therefore declares `requires_periodic`, and the harness does not run it on a dataset with a
non-periodic axis, such as the Sod shock tube; it reports why in the run log.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence palinstrophy --results results/comparison_1793302178`, do not edit -->

![how the metric responded to each degradation, by field: rank correlation, separation of neighbouring strengths, damage per unit of field change, and the bound on its largest response](_generated/sensitivity_profile.svg)

Four measured statistics for palinstrophy, one row per degradation grouped by family and one marker per field. From left: the rank correlation between the metric and the applied strength within a frame, with the line showing the resampling interval; the separation of neighbouring strengths as Cliff's delta, where 0 means the metric cannot tell one strength from the next and the faint ticks at 0.12, 0.28 and 0.42 are Vargha and Delaney's small, medium and large anchors, for scale and not as grades; the damage charged per unit of field change at the harshest strength; and the upper confidence bound on the largest damage, beside the fixed margin of 0.05. A hollow marker is a field and degradation on which that bound lies below the margin, so the response is provably small. A missing marker is a statistic the analysis withheld, as the rank correlation is on an axis the metric is invariant to.

![median damage against severity level, one panel per degradation family and field, on one shared scale](_generated/response_curves.svg)

Median damage over frames against severity level for palinstrophy, one row per family of degradation and one column per field, on one shared scale. The solid grey line is damage 1, the anchor (by default the field's own mean); the dotted black line is the damage assigned to the fake prediction with the right spectrum, where the run included it. The hollow black ring marks the first level at which the metric has moved a tenth of the way to the anchor. Hollow grey markers are strengths excluded for repeating a milder one or for doing nothing. Degradations with three or fewer usable levels are drawn as markers only; points above 2 are drawn as triangles at the top.

**Trend: does the response follow the degradation?**

| test family | field | degradations | rank correlation | fraction of frames in order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| Displacement | vorticity | 2 | — | — | — |
| Resolution loss | vorticity | 2 | 1 | 0.901 to 1 | 0.578 to 0.685 |
| Smoothing | vorticity | 3 | 1 | 1 | 0.531 to 0.678 |
| Spectral filtering | vorticity | 4 | 1 | 1 | 0.514 to 0.85 |
| Noise | vorticity | 1 | 1 | 1 | 1 |

**Reactivity: how far does it move?**

| test family | field | change from clean at the harshest strength | elasticity | first strength detected |
|---|---|---|---|---|
| Displacement | vorticity | 0 | — | level — |
| Resolution loss | vorticity | -0.96 to -0.578 | 2.27 | level 2 |
| Smoothing | vorticity | -0.98 to -0.734 | 0.432 to 1.07 | level 1 |
| Spectral filtering | vorticity | -0.99 to -0.517 | 0.21 to 5.14 | level 1 |
| Noise | vorticity | 10.8 | 2.01 | level 3 |
| trap test: fake prediction, right spectrum | vorticity | — | — | damage -1.15e-16 |

**Consistency: how much does it vary from snapshot to snapshot?**

| test family | field | consistency, in the strength's units | snapshots per independent block |
|---|---|---|---|
| Displacement | vorticity | — | 1 to 17 |
| Resolution loss | vorticity | 1.42 to 1.9 | 21 |
| Smoothing | vorticity | 0.0161 to 0.0354 | 21 |
| Spectral filtering | vorticity | 0.0335 to 0.058 | 21 to 22 |
| Noise | vorticity | 0.00297 | 22 |

One row per family of degradation and physical field; a cell gives the range over the degradations in that family. **Trend.** The rank correlation is the Spearman correlation between the strength and how far the metric has moved from its value on the undegraded field of the same frame, in the one direction it moves under that degradation, computed inside a single frame. A value of 1 means every strength moved it further than the last in every frame, whichever way it moves; a response that scatters to both sides scores near 0. The fraction of frames in order counts the frames with no exception. The weakest gap is the smallest Mann-Whitney overlap between two neighbouring strengths across frames: 1 means they never overlap, 0.5 that they cannot be told apart. **Reactivity.** The change from clean is the median, at the harshest strength, of the departure from the undegraded value of the same frame over the size of that value: 0.3 means 30%. The elasticity is the percentage change of that departure per percentage change in strength over the mildest strengths. First strength detected is the mildest at which the metric has moved a tenth of the way to the anchor; **damage** reads that 0-to-1 scale as a number. A dash means the measurement is not defined there. A metric's reactivity scales with the power it is expressed in: mean squared error's elasticity is twice root-mean-square error's, though the two carry the same information, so compare magnitudes across metrics with that in mind. **Consistency** is how much the response varies from snapshot to snapshot relative to its size, in the strength's units; the snapshots of one trajectory are correlated, and the last column is how many consecutive snapshots one independent block spans.

These tables report what was measured and grade none of the measurements. What the numbers mean for this metric is written in the subsections below, beside the test that produced each number.

**Profile.**

| field | selectivity | charges most for | charges least for | response provably below 0.05 at 90% on | elasticity to a sub-pixel shift, against severity (distance) | compute cost (x cheapest in this run) |
|---|---|---|---|---|---|---|
| vorticity | 0.526 | `median_blur` | `additive_noise` | `translate_subpixel` `translate_x` | — | 41.1 |

One row per physical field. **Selectivity** is how concentrated the metric's response is on a few degradations, measured per unit of field change: 0 means it charges every degradation the same, as mean squared error does by construction, and values toward 1 that one degradation carries most of it. **Charges most and least for** name the two ends of that profile. **Response provably below** lists degradations on which the upper confidence bound of the largest damage lies below the margin -- an equivalence test, so an entry says the response is provably small, not merely not significant; a dash means no degradation met the bound. **Elasticity** is the slope of log damage against log shift over the smallest shifts: 1 means damage grows in proportion to the shift, 2 with its square. **Compute cost** is wall-clock per evaluation over the cheapest metric and field in the same run.

<!-- END GENERATED performance -->

## Intuition

Vorticity says how fast the fluid is spinning at each point. Enstrophy adds up how much
spinning there is in total. This quantity instead adds up how *abruptly* the spinning changes
from place to place, so it is large when the rotation is organised into thin, sharply bounded
filaments and small when the same total amount of rotation is spread out smoothly.

That makes it a probe for a specific failure. A prediction that has blurred the flow loses
the sharp edges between one rotating region and the next before it loses the bulk of the
rotation, and this quantity weights fine detail far more heavily than coarse structure —
doubling how quickly a feature varies in space quadruples its contribution here, while leaving
its contribution to the total rotation unchanged. So a smooth blur always takes away a larger
share of this quantity than of the total rotation; how much larger on the real flow is
recorded under Results.

A worked example on an eight by eight grid. Take a vorticity field that is a single smooth
wave: one full oscillation across the box, constant in the other direction. Then squeeze the
same wave so it oscillates three times across the box, keeping its amplitude.

```
field                          enstrophy   palinstrophy
one oscillation across 8         0.25        0.1542
three oscillations across 8      0.25        1.388
```

The enstrophy is unchanged, because there is exactly as much rotation as before. The
palinstrophy rises by a factor of nine, because the field now varies three times as fast and
this quantity counts the square of that rate.

What it ignores: everything about where the structure is. Like any single-field quantity it
takes one field and returns one number, so a prediction can match it exactly while having its
vortices in entirely the wrong places.

## Reading the output

Zero and unbounded above, in the square of the vorticity units per square length. There is no
direction in which the value is better on its own: what is read is the drift away from the
reference field's value, in either direction. A prediction scoring below the reference has
smoothed the vorticity; one scoring above has sharpened or roughened it.

Only comparisons at a fixed analysis-grid resolution are meaningful, and this metric is
stricter about that than most. Equation (2) shows the value is dominated by the highest
wavenumbers the grid carries, so changing the resolution changes which scales contribute at
all. Comparing a run at grid 128 with one at grid 256 measures the grids, not the predictions.

On the damage scale the anchor is the field's own spatial mean, a constant with zero
palinstrophy, so damage is the fraction of the reference's palinstrophy lost: positive when the
value falls, 1 when none is left, and negative when the value rises.

## Limitations

The quantity is degenerate in the strong sense: enormously many wrong fields share any given
palinstrophy, so a matching value is no evidence of a correct prediction. It is a tripwire and
must be used as one.

The more specific trap is its resolution sensitivity working against it. Because the $\kappa^2$
weight concentrates the value at the grid scale, palinstrophy is disproportionately sensitive
to anything that changes the smallest resolved scales, including numerical artefacts that are
not physics at all. By Equation (2), energy added at wavenumber $\kappa$ raises the value by
$\kappa^2$ times that energy, so ringing near the grid scale raises palinstrophy *above* the
reference's while making the field worse, and the number alone does not distinguish that from
genuinely better-resolved filaments.

Finally, it inherits everything that is uncertain about the vorticity it is computed from.
Vorticity here is a derived field, recomputed from velocity after any remap rather than
averaged, and the calibration recorded with `comparison_1789632054` gives its characteristic
scale a relative spread of 0.32 across the sampled frames, against 0.06 for density and 0.07
for velocity. A palinstrophy drift of comparable size says as much about which frames were
evaluated as about the prediction.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence palinstrophy --results results/comparison_1793302178`, do not edit -->

Measured on `kinet_re5e4`, frames 2000 to 10000 (161 frames of developed flow), on the 256 analysis grid, seed 20260807, at commit `b59bbde617d1` (working tree dirty). Run `comparison_1793302178`.

Every number in this section comes from that one run. Regenerate with `python -m fmeval.cards evidence <name> --results results/comparison_1793302178`.

<!-- END GENERATED run -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence palinstrophy --results results/comparison_1793302178`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `box_blur` | vorticity | 4 | 1 | 1 | 0.531 |
| `gaussian_blur` | vorticity | 4 | 1 | 1 | 0.533 |
| `median_blur` | vorticity | 3 | 1 | 1 | 0.678 |

<!-- END GENERATED results_smoothing -->

Smoothing removes fine detail, so palinstrophy falls steadily as the strength rises and follows
each blur with a rank correlation of 1. What this family
measures is the size of that fall beside enstrophy's. At the mildest `gaussian_blur`
palinstrophy has already lost 31% against enstrophy's 6%, and at the strongest 98% against
47%; `box_blur` gives 42% against 9% at its mildest. Equation (3) guarantees the ordering for
the Gaussian; the box and median kernels are outside its assumptions and show the same
ordering on this data.

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence palinstrophy --results results/comparison_1793302178`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `highpass_butterworth` | vorticity | 4 | 1 | 1 | 0.824 |
| `highpass_ideal` | vorticity | 4 | 1 | 1 | 0.85 |
| `lowpass_butterworth` | vorticity | 4 | 1 | 1 | 0.514 |
| `lowpass_ideal` | vorticity | 4 | 1 | 1 | 0.516 |

<!-- END GENERATED results_spectral -->

The two sides of the spectrum separate the pair cleanly. A low-pass removes the modes this
quantity is built on: the mildest `lowpass_butterworth` removes 66% of palinstrophy and 11% of
enstrophy. A high-pass removes the modes it ignores: the mildest `highpass_ideal` removes 45%
of enstrophy and 0.5% of palinstrophy. Read together, the two single-field quantities say
which end of the spectrum a prediction has lost, which neither says alone.

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence palinstrophy --results results/comparison_1793302178`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `translate_subpixel` | vorticity | 6 | — | — | — |
| `translate_x` | vorticity | 5 | — | — | — |

<!-- END GENERATED results_geometric -->

Invariant, as a single-field quantity must be: translation does not change how sharp the
vorticity is, the values are equal to round-off at every strength, and every ordering
statistic is withheld.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence palinstrophy --results results/comparison_1793302178`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `coarsen` | vorticity | 4 | 1 | 0.901 | 0.685 |
| `coarsen_bandlimited` | vorticity | 4 | 1 | 1 | 0.578 |

<!-- END GENERATED results_resolution -->

This is the one family where the number misleads, and it does so in the direction Limitations
warns about. Coarsening by a factor of 2 *raises* palinstrophy by 89% above the reference,
and a factor of 4 still leaves it 39% high; only at factors 8 and 16 does it fall below, by 28%
and 59%. The degradation expands each block back to the fine grid as a constant, so it adds
a jump at every block edge, and a jump is exactly the steep gradient this quantity counts.
Enstrophy falls throughout, by 4% to 40%. The rank correlation of 1 in the table says the value
moves steadily one way across the four strengths, read as a departure from the clean value; the
clean value is not one of the points, so the table does not show that the two mildest
strengths raised palinstrophy above it. The response curve does, as damage of -0.89 and -0.39.
For the same reason the first strength detected under `coarsen` is factor 8: detection counts
movement in the direction the degradation takes the value overall, which here is down.
`issues/039` records the same mechanism for `h1_seminorm`.

`coarsen_bandlimited` keeps the same block means as `coarsen` without adding edges, and under
it palinstrophy only falls: by 2%, 39%, 84% and 96% at factors 2 to 16, while enstrophy falls
by 0.1% to 31%. The rise under `coarsen` was therefore the staircase and nothing else. It also
falls by a larger fraction than enstrophy at every factor, the ordering Equation (3) guarantees
for smooth radial filters, although this operator is not one of them: its band is square, and
it boosts the modes nearest the cut.

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence palinstrophy --results results/comparison_1793302178`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `additive_noise` | vorticity | 4 | 1 | 1 | 1 |

<!-- END GENERATED results_stochastic -->

Noise is broadband, so it adds energy at the highest wavenumbers, where Equation (2) weights
it most. At the strongest noise palinstrophy is 12 times its reference value while enstrophy
has risen by 25%. The ordering is correct in every frame, and read against the clean value of
the same frame no two neighbouring strengths overlap (a weakest gap of 1), although the two
mildest move the value by only 0.01% and 0.4%, small beside how much the value itself changes
from one frame to the next.

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence palinstrophy --results results/comparison_1793302178`, do not edit -->

| field | damage assigned to the fake prediction | closest real degradation | damage of the reference moved far away | value on the anchor |
|---|---|---|---|---|
| vorticity | -1.15e-16 | `translate_x=4` | -5.73e-17 | 0 |

The fake prediction here has exactly the reference field's amplitude spectrum and completely scrambled structure. Damage 1 is what the anchor scores, by default the reference's own spatial mean, a prediction that knows the mean and nothing else. The damage column therefore says how close to useless this metric considers that fake prediction: a low number means the metric was fooled. The third column translates the same number into an ordinary degradation whose damage the fake prediction matches, which is easier to picture. The fourth is the reference moved by a large random offset, the right statistics in the wrong place; where a field's energy sits in its largest scales that copy stays partly correlated with the reference, so it is not the score of an unrelated field.

<!-- END GENERATED results_canaries -->

Both score exactly the reference's palinstrophy, damage 0 to round-off. The fake prediction
has the reference's amplitude spectrum, and Equation (2) is a function of that spectrum alone,
so the two cannot differ; the moved copy is a translation of the reference. The trap therefore
records this metric as fooled, which for a single-field quantity follows from the definition
rather than from the data.

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence palinstrophy --results results/comparison_1793302178`, do not edit -->

| compared with | rank correlation over every degradation |
|---|---|
| `kinetic_energy` | 0.805 |
| `enstrophy` | 0.758 |
| `increment_flatness` | 0.459 |
| `h1_seminorm` | 0.11 |
| `mae` | -0.0971 |
| `rmse` | -0.141 |
| `mse` | -0.141 |
| `nrmse` | -0.158 |
| `h_minus_one` | -0.208 |
| `increment_w1_by_separation` | -0.551 |
| `increment_w1` | -0.57 |
| `spectrum_l2` | -0.694 |

Computed on the median value at each combination of degradation and strength, over every degradation and physical field in the run, with the undegraded reference excluded. Two metrics correlating near 1 put the degradations in the same order, but the two may still weight those degradations very differently. A correlation near 1 therefore means the two metrics are redundant for ranking models, not that the two are interchangeable as training losses.

<!-- END GENERATED results_summary -->

The closest rankings are those of the other two single-field quantities, `kinetic_energy` at
0.81 and `enstrophy` at 0.76. The second is expected of two moments of one spectrum, and it is
also the measure of how much palinstrophy adds: the two disagree most on
high-pass filtering and on coarsening, both described above. The negative correlations with
the pairwise metrics are orientation rather than disagreement, since this quantity falls
under most damage while theirs rises.

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence palinstrophy --results results/comparison_1793302178`, do not edit -->

![damage against applied strength for this metric beside the pointwise controls, log-log, one panel per displacement degradation and field](_generated/damage_beside_controls.svg)

Median damage over frames against the applied strength, log-log, for palinstrophy (bold, in colour) and the pointwise controls mae, mse, rmse, nrmse (thin, grey), one column per displacement degradation and one row per field. The grey line is damage 1, the anchor (by default the field's own mean). Parallel lines charge in the same proportion at every strength; a steeper line charges relatively more for the larger shifts, which is what decides whether two metrics are interchangeable as training losses. These are the same numbers as the table beneath.

**Displacement, density, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `palinstrophy` | — | — | — | — | — | — |
| `mae` | 0.00383 | 0.00767 | 0.0153 | 0.0306 | 0.061 | 0.121 |
| `mse` | 2.17e-05 | 8.68e-05 | 0.000347 | 0.00138 | 0.00551 | 0.0219 |
| `rmse` | 0.00466 | 0.00931 | 0.0186 | 0.0372 | 0.0743 | 0.148 |
| `nrmse` | 0.00463 | 0.00926 | 0.0185 | 0.037 | 0.0738 | 0.147 |

**Displacement, density, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `palinstrophy` | — | — | — | — | — |
| `mae` | 0.0306 | 0.061 | 0.121 | 0.24 | 0.469 |
| `mse` | 0.00138 | 0.00551 | 0.0219 | 0.0849 | 0.307 |
| `rmse` | 0.0372 | 0.0743 | 0.148 | 0.291 | 0.555 |
| `nrmse` | 0.037 | 0.0738 | 0.147 | 0.29 | 0.55 |

**Displacement, velocity, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `palinstrophy` | — | — | — | — | — | — |
| `mae` | 0.00279 | 0.00559 | 0.0112 | 0.0223 | 0.0441 | 0.0859 |
| `mse` | 1.45e-05 | 5.81e-05 | 0.000232 | 0.000924 | 0.0036 | 0.0136 |
| `rmse` | 0.00381 | 0.00762 | 0.0152 | 0.0304 | 0.06 | 0.117 |
| `nrmse` | 0.00382 | 0.00763 | 0.0153 | 0.0304 | 0.06 | 0.117 |

**Displacement, velocity, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `palinstrophy` | — | — | — | — | — |
| `mae` | 0.0223 | 0.0441 | 0.0859 | 0.163 | 0.31 |
| `mse` | 0.000924 | 0.0036 | 0.0136 | 0.0489 | 0.165 |
| `rmse` | 0.0304 | 0.06 | 0.117 | 0.221 | 0.406 |
| `nrmse` | 0.0304 | 0.06 | 0.117 | 0.221 | 0.406 |

**Displacement, vorticity, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `palinstrophy` | 9.61e-14 | 3.28e-13 | 6.56e-13 | -2.29e-16 | -2.29e-16 | -2.29e-16 |
| `mae` | 0.0428 | 0.0854 | 0.169 | 0.328 | 0.582 | 0.86 |
| `mse` | 0.00112 | 0.00448 | 0.0176 | 0.066 | 0.21 | 0.44 |
| `rmse` | 0.0335 | 0.0669 | 0.133 | 0.257 | 0.458 | 0.663 |
| `nrmse` | 0.0328 | 0.0654 | 0.13 | 0.253 | 0.456 | 0.67 |

**Displacement, vorticity, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `palinstrophy` | -0 | -0 | -1.15e-16 | -0 | -0 |
| `mae` | 0.328 | 0.582 | 0.86 | 1.1 | 1.31 |
| `mse` | 0.066 | 0.21 | 0.44 | 0.679 | 1.1 |
| `rmse` | 0.257 | 0.458 | 0.663 | 0.824 | 1.05 |
| `nrmse` | 0.253 | 0.456 | 0.67 | 0.832 | 1.05 |

Median damage over frames at every strength, this metric in the first row and the pointwise controls beneath it, all on the same 0-to-1 scale where 0 is the undegraded reference and 1 the anchor (by default the field's own mean); a dash means no damage scale on that field. The rank correlations under *Compared with the other metrics* say whether two metrics put the strengths in the same order; this table says how much each one charges for the same strength, which decides whether two metrics are interchangeable as training losses.

<!-- END GENERATED results_damage_by_level -->

## References

\bibliography
