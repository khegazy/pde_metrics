---
name: spectrum_l2
kind: metric
---

## Definition

Remove the spatial mean of each channel, transform, and sum the squared moduli into shells
of constant wavevector magnitude. Writing $\hat{f}^{(c)}_{\mathbf{m}}$ for the transform of
the mean-removed channel $c$ and $|\mathbf{m}|$ for the integer wavenumber magnitude of mode
$\mathbf{m}$, the shell energies are

$$
E_f(\kappa) = \sum_{c=1}^{C} \; \sum_{|\mathbf{m}| = \kappa}
\bigl| \hat{f}^{(c)}_{\mathbf{m}} \bigr|^2 \tag{1}
$$

where $\kappa$ runs over the distinct magnitudes the grid supports. Equation (1) is the
discrete counterpart of the shell-averaged energy spectrum of turbulence (Equation 3 of
[@boffetta2012]; see also [@pope2000]), with one difference that Limitations spells out: its
shells are exact magnitudes rather than unit-width bands. The metric is the L2
distance between the reference's and the candidate's shell energies, normalised by the
reference's:

$$
S(f, g) = \frac{\bigl( \sum_{\kappa} [ E_f(\kappa) - E_g(\kappa) ]^2 \bigr)^{1/2}}
{\bigl( \sum_{\kappa} E_f(\kappa)^2 \bigr)^{1/2}} \tag{2}
$$

and is NaN when the reference has no fluctuation energy, since Equation (2) then divides by
zero and there is no scale against which a difference could be relative.

Three points about Equation (1) are choices, not consequences.

The spatial mean is removed, so the $\kappa = 0$ shell carries no energy. On this data that
is load-bearing rather than cosmetic: density is $1.0 \pm 1.8 \times 10^{-4}$, so its mean is
four orders of magnitude larger than any fluctuation, and a spectrum retaining it would
compare two means and ignore the flow entirely.

The shells are the *exact* distinct magnitudes of the grid, not rounded bins, and both the
magnitudes and the binning are taken from the code the severity calibration already uses.
There were once two definitions of $|\mathbf{k}|$ in this repository and they disagreed about
the diagonal modes; on density that turned a low-pass asked to remove 30% of the energy into
one that removed 99.997%. A second definition here would reintroduce that hazard.

The normalisation in Equation (2) is taken from the reference, which makes the metric
dimensionless and scale-free — multiplying both fields by a constant scales both spectra by
its square, and the ratio is unchanged — but also asymmetric. Swapping the arguments changes
the value, as it does for [nrmse](../../metrics/nrmse/card.md).

Equation (2) is a function of the moduli $|\hat{f}_{\mathbf{m}}|$ alone. Every phase is
discarded, and that is the metric's defining property rather than an approximation.

### Boundary handling

Periodic on every axis, inherited from the discrete Fourier transform in Equation (1). The
shells depend only on the grid's shape and not on its spacing, so unlike
[h_minus_one](../../metrics/h_minus_one/card.md) this metric reads no length from the analysis grid and
its value is unchanged by a rescaling of the cell size.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence spectrum_l2 --results results/comparison_1789632054`, do not edit -->

| test family | field | degradations | rank correlation | weakest gap between neighbouring strengths | first strength detected |
|---|---|---|---|---|---|
| Displacement | density | 2 | — to — | — | level — |
| Displacement | velocity | 2 | — to — | — | level — |
| Displacement | vorticity | 2 | — to — | — | level — |
| Resolution loss | density | 1 | 1 to 1 | 1 | level — |
| Resolution loss | velocity | 1 | 1 to 1 | 1 | level — |
| Resolution loss | vorticity | 1 | 1 to 1 | 0.895 | level — |
| Smoothing | density | 3 | 1 to 1 | 1 | level — |
| Smoothing | velocity | 3 | 1 to 1 | 0.971 | level — |
| Smoothing | vorticity | 3 | 1 to 1 | 0.74 | level — |
| Spectral filtering | density | 4 | 1 to 1 | 0.989 | level — |
| Spectral filtering | velocity | 4 | 1 to 1 | 0.999 | level — |
| Spectral filtering | vorticity | 4 | 1 to 1 | 0.842 | level — |
| Noise | density | 1 | 1 to 1 | 0.999 | level — |
| Noise | velocity | 1 | 1 to 1 | 1 | level — |
| Noise | vorticity | 1 | 1 to 1 | 1 | level — |
| trap test: fake prediction, right spectrum | density | 1 | — | — | damage — |
| trap test: fake prediction, right spectrum | velocity | 1 | — | — | damage — |
| trap test: fake prediction, right spectrum | vorticity | 1 | — | — | damage — |

One row per family of degradation and physical field. **Rank correlation** asks whether the metric put the strengths of one degradation in the right order: it is the Spearman correlation between the metric and the applied strength, computed inside a single frame, and the column gives the range over the degradations in that family. A value of 1 means every strength was ordered correctly in every frame. **Weakest gap between neighbouring strengths** asks whether the metric can tell one strength from the next: it is the smallest Mann-Whitney overlap between any two neighbouring strengths, where 1 means the two never overlap and 0.5 means the metric cannot separate them at all. **First strength detected** is the mildest strength at which the metric has moved a tenth of the way from the undegraded reference toward a field with no relation to the truth; a dash means the metric never reached that tenth. **Damage** is that same 0-to-1 scale read as a number: 0 is the undegraded reference and 1 is an unrelated field.

This table reports what was measured and grades none of the measurements. What the numbers mean for this metric is written in the subsections below, beside the test that produced each number.

<!-- END GENERATED performance -->

## Intuition

Any field can be broken into waves of different wavelengths. The energy spectrum says how
much of the field's total variation sits at each wavelength — how much is large sweeping
structure and how much is fine detail — and says nothing at all about where any of it is or
how it is arranged. This metric compares two such profiles and reports how different they
are, as a fraction of the reference's own size.

What it reveals is a prediction that has the wrong balance of scales: one that is too smooth
has lost energy at short wavelengths, one that is noisy has gained it there, and either shows
up here directly and in proportion. What it cannot reveal is anything about arrangement. Two
fields can have exactly the same profile of energy against wavelength and look completely
unrelated, because the information distinguishing them lives entirely in the alignment of the
waves rather than in their sizes.

That blindness is deliberate and is the reason this metric is in the repository. The
evaluation includes a fake prediction built to have the reference's exact energy profile with
its wave alignments randomised — a field that is obviously wrong to look at and that this
metric scores as perfect, exactly as it scores the reference itself. A suite in which every
metric shrugs that fake off is not a reassuring suite; it means the trap has nothing to
catch, and this metric is something for it to catch. The trap's normalised score cannot show
it yet, for the reason given under Limitations.

A worked example, four cells by four cells. On the left, a reference holding a single wave.
On the right, a prediction that is simply flat. The prediction has none of the reference's
energy, so the two profiles differ by the whole of the reference's, and the relative distance
is exactly one.

```
reference        candidate        spectrum_l2
 1  1  1  1      0 0 0 0
 0  0  0  0      0 0 0 0              1.0
-1 -1 -1 -1      0 0 0 0
 0  0  0  0      0 0 0 0
```

Now replace the flat prediction with the same wave shifted along the vertical axis by one
cell — a field that disagrees with the reference by one unit in every single cell.

```
reference        candidate        spectrum_l2    rms error
 1  1  1  1      0  0  0  0
 0  0  0  0      1  1  1  1           0.0          1.0
-1 -1 -1 -1      0  0  0  0
 0  0  0  0     -1 -1 -1 -1
```

This metric returns zero, because shifting a wave changes only its alignment and not its
size. The cell-by-cell root-mean-square error is 1, larger than the wave's own typical size
of 0.71.

What it ignores: where everything is. Position, arrangement, and the alignment of one scale
against another are all invisible to it.

## Reading the output

Dimensionless, zero and unbounded above. Lower is better. Zero means the two energy profiles
coincide, which is much weaker than the two fields coinciding. One is the value a prediction
with no fluctuation at all receives, so values approaching one mean the candidate has lost
most of its energy, and values above one mean it has more energy than the reference rather
than less.

Because Equation (2) cancels any overall scaling, values are comparable across fields of
completely different magnitude, which is unusual here — density and vorticity can be read on
the same axis. Comparison across analysis-grid resolutions is not valid: the set of shells in
Equation (1) is fixed by the grid, so a finer grid contributes shells a coarser one does not
have.

The comparison that matters most is against a phase-sensitive metric on the same pair of
fields. A large value here means the balance of scales is wrong. A small value here says
almost nothing on its own, and should be read only as "the balance of scales is not the
problem".

## Limitations

The metric assigns zero to fields that are not remotely alike, and this is not an edge case
but the common case for any prediction that has the right statistics and the wrong structure.
A translated copy and a phase-randomised impostor both score perfectly. Used alone it would
certify a useless model. The blindness is to phase specifically, not to arrangement in
general: shuffling the cells at random spreads a smooth field's energy evenly over every
wavenumber, and `test_metric.py` measures that at about 1, as far from the reference as a
flat prediction. `AGENTS.md` states
the general principle this instantiates: matching a spectrum is a weak constraint, and the
two-point correlation is the Fourier transform of this quantity, so running both is
not two independent checks.

A second, quieter failure comes from the linear normalisation in Equation (2). The sum is
dominated by whichever shells hold the most energy, and on this data that is a handful of very
low wavenumbers: the calibration recorded with `comparison_1789632054` puts half of density's
fluctuation energy below $|\mathbf{m}| = 1.29$ and 90% below 3.03, and for velocity half at
$|\mathbf{m}| = 1$. It follows from Equation (2) that a prediction that destroys the entire
inertial range while preserving the largest scales scores close to zero, because the shells
it ruined contributed little to the norm in the first place. A logarithmic or
per-shell-relative comparison would weight the scales more evenly and is not what this
computes.

Third, the shells are very fine. Grouping by exact magnitude gives 5924 distinct shells on the
256 by 256 analysis grid, holding a median of 8 modes each, where rounding to integer
magnitudes would give 182. Equation (1) is therefore close to a comparison of individual mode
energies, pooled only over the grid's reflection and rotation symmetries, rather than the
shell-averaged spectrum of the turbulence literature. On the degradation ladder, where every
candidate is an operator applied to the reference, that makes no difference. Against a
prediction that is a different realisation of the flow, each shell's energy would be an
average over about eight modes rather than over hundreds, and the realisation-to-realisation
scatter would enter the value; that is a consequence of the binning, not yet measured, and
`issues/038` asks whether to keep it.

Finally, the normalised damage scale is not available. It is anchored on an unrelated field
built from large translations, which this metric cannot see: the anchor scores the same
round-off as the reference, so every damage score and every sensitivity level is withheld,
including the Gaussian-impostor damage that is this metric's reason to exist. The raw values
under Results carry the evidence instead. `issues/037` records the problem for the whole
position-blind family and what would settle it.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence spectrum_l2 --results results/comparison_1789632054`, do not edit -->

Measured on `kinet_re5e4`, frames 2000 to 10000 (161 frames of developed flow), on the 256 analysis grid, seed 20260807, at commit `0104b46cf8d9` (working tree dirty). Run `comparison_1789632054`.

Every number in this section comes from that one run. Regenerate with `python -m fmeval.cards evidence <name> --results results/comparison_1789632054`.

<!-- END GENERATED run -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence spectrum_l2 --results results/comparison_1789632054`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `box_blur` | density | 4 | 1 | 1 | 1 |
| `box_blur` | velocity | 4 | 1 | 1 | 1 |
| `box_blur` | vorticity | 4 | 1 | 1 | 0.74 |
| `gaussian_blur` | density | 4 | 1 | 1 | 1 |
| `gaussian_blur` | velocity | 4 | 1 | 1 | 1 |
| `gaussian_blur` | vorticity | 4 | 1 | 1 | 0.88 |
| `median_blur` | density | 3 | 1 | 1 | 1 |
| `median_blur` | velocity | 3 | 1 | 1 | 0.971 |
| `median_blur` | vorticity | 3 | 1 | 1 | 0.928 |

<!-- END GENERATED results_smoothing -->

Every smoothing axis is ordered correctly in every frame on all three fields, which is what
Equation (2) implies for any operator that only removes energy. The size of the response is
set by where each field keeps its energy. At the strongest `gaussian_blur` the metric reads
0.62 on density and 0.58 on velocity, where the blur removes 70% and 64% of the fluctuation
energy, but only 0.15 on vorticity, where it removes 47%. The vorticity figure is lower than
its energy loss alone would suggest. Our reading, not a separate measurement, is that the
square in Equation (2) weights the few most energetic shells, and on vorticity the blur takes
its energy from many weak high-wavenumber shells that contribute little to that norm. The
weakest separation in the family, 0.74 on `box_blur` applied to vorticity, is on the same
field.

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence spectrum_l2 --results results/comparison_1789632054`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `highpass_butterworth` | density | 4 | 1 | 1 | 0.989 |
| `highpass_butterworth` | velocity | 3 | 1 | 1 | 1 |
| `highpass_butterworth` | vorticity | 4 | 1 | 1 | 0.926 |
| `highpass_ideal` | density | 3 | 1 | 1 | 0.994 |
| `highpass_ideal` | velocity | 2 | 1 | 1 | 1 |
| `highpass_ideal` | vorticity | 4 | 1 | 1 | 0.935 |
| `lowpass_butterworth` | density | 4 | 1 | 1 | 0.989 |
| `lowpass_butterworth` | velocity | 3 | 1 | 1 | 1 |
| `lowpass_butterworth` | vorticity | 4 | 1 | 1 | 0.842 |
| `lowpass_ideal` | density | 3 | 1 | 1 | 0.997 |
| `lowpass_ideal` | velocity | 2 | 1 | 1 | 0.999 |
| `lowpass_ideal` | vorticity | 4 | 1 | 1 | 0.847 |

<!-- END GENERATED results_spectral -->

Ordered correctly everywhere, and this is the family where the linear normalisation of
Equation (2) is most visible. `highpass_ideal` at its mildest strength removes 45% of
vorticity's energy, all of it from the lowest, most energetic shells, and the metric already
reads 0.97 — almost the value of a flat prediction. `lowpass_ideal`, removing a comparable 6%
to 47% from the other end of the spectrum, reads 0.01 to 0.20 on the same field. Energy lost
at large scales costs far more here than the same energy lost at small scales, which is the
Limitations point measured.

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence spectrum_l2 --results results/comparison_1789632054`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `translate_subpixel` | density | 6 | — | — | — |
| `translate_subpixel` | velocity | 6 | — | — | — |
| `translate_subpixel` | vorticity | 6 | — | — | — |
| `translate_x` | density | 5 | — | — | — |
| `translate_x` | velocity | 5 | — | — | — |
| `translate_x` | vorticity | 5 | — | — | — |

<!-- END GENERATED results_geometric -->

Blind, as the definition requires. A whole-cell translation leaves every Fourier amplitude
unchanged, and the values on `translate_x` are round-off, between 2e-17 and 2e-16. The
Fourier-shift interpolation in `translate_subpixel` moves them only to about 1e-12. Every
ordering statistic in the table is withheld on both axes, because a ranking of those values is
a ranking of the last bits of floating-point arithmetic.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence spectrum_l2 --results results/comparison_1789632054`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `coarsen` | density | 4 | 1 | 1 | 1 |
| `coarsen` | velocity | 4 | 1 | 1 | 1 |
| `coarsen` | vorticity | 4 | 1 | 1 | 0.895 |

<!-- END GENERATED results_resolution -->

Ordered correctly on all three fields in every frame. The response is small on the smooth
fields — 0.06 on density and 0.03 on velocity at a factor of 16 — because block averaging
there removes little of the energy that dominates Equation (2); on vorticity it reaches 0.15.

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence spectrum_l2 --results results/comparison_1789632054`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `additive_noise` | density | 4 | 1 | 1 | 0.999 |
| `additive_noise` | velocity | 4 | 1 | 1 | 1 |
| `additive_noise` | vorticity | 4 | 1 | 1 | 1 |

<!-- END GENERATED results_stochastic -->

Ordered correctly, with neighbouring strengths separated almost perfectly, but the values
are the smallest of any family: 0.007 on density and 0.018 on vorticity at the strongest
noise. White noise spreads its energy thinly over every shell, and Equation (2) weights each
shell by its energy, so noise that is plain to the eye barely registers.

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence spectrum_l2 --results results/comparison_1789632054`, do not edit -->

| field | damage assigned to the fake prediction | closest real degradation | value on an unrelated field |
|---|---|---|---|
| density | — | `` | 1.64e-16 |
| velocity | — | `` | 1.62e-16 |
| vorticity | — | `` | 1.65e-16 |

The fake prediction here has exactly the reference field's amplitude spectrum and completely scrambled structure. Damage of 1 is what a field with no relation to the truth scores, so the damage column says how close to useless this metric considers that fake prediction: a low number means the metric was fooled. The third column translates the same number into an ordinary degradation whose damage the fake prediction matches, which is easier to picture.

<!-- END GENERATED results_canaries -->

The fake prediction was caught in the sense that matters: it has the reference's exact
Fourier amplitudes, and the metric scored it at 2.8e-15, 1.6e-16 and 2.2e-16 on density,
velocity and vorticity, indistinguishable from the undegraded reference. The damage column
cannot say so, because the unrelated-field anchor is built from translations, which this
metric also cannot see, and the table shows that anchor at 1.6e-16. Every damage score is
therefore withheld. `issues/037` records this for the whole position-blind family.

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence spectrum_l2 --results results/comparison_1789632054`, do not edit -->

| compared with | rank correlation over every degradation |
|---|---|
| `increment_w1` | 0.727 |
| `nrmse` | 0.199 |
| `h_minus_one` | 0.136 |
| `rmse` | 0.125 |
| `mse` | 0.125 |
| `mae` | 0.115 |
| `h1_seminorm` | -0.19 |
| `increment_flatness` | -0.201 |
| `palinstrophy` | -0.741 |
| `enstrophy` | -0.839 |

Computed on the median value at each combination of degradation and strength, over every degradation and physical field in the run, with the undegraded reference excluded. Two metrics correlating near 1 put the degradations in the same order, but the two may still weight those degradations very differently. A correlation near 1 therefore means the two metrics are redundant for ranking models, not that the two are interchangeable as training losses.

<!-- END GENERATED results_summary -->

The ranking this metric produces is close to independent of the pointwise family, correlating
0.115 to 0.199 with `mae`, `mse`, `rmse` and `nrmse`, and closest to `increment_w1` at 0.73,
the other metric here that reads only a distribution rather than an arrangement. The strong
negative correlations with `enstrophy` and `palinstrophy` are orientation rather than
disagreement: those two are single-field quantities that fall as the damage rises.

## References

\bibliography
