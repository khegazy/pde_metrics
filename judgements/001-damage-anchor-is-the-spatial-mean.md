# 001 — The damage anchor is the field's spatial mean

**Date:** 2026-10-29. **Made by:** the agent resolving issue 092 (branch `biase_issue`).
**Reverse with:** `analysis.anchor=uncorrelated` for a run, or `analysis.anchor: uncorrelated` in
`configs/config.yaml` for every run; then delete this file and restore the wording it changed.

## The question that would have been asked

Damage runs from 0 at the reference to 1 at an anchor. The anchor was the reference moved by a
large random offset (`random_large_translation`, ladder entry `uncorrelated`), meant to be "a field
with the same statistics and no relation to the truth". Measured, it is not one, on the main
dataset as well as on Sod. What should damage 1 mean instead?

## What was measured

A translation by d multiplies the Fourier mode at wavenumber k by the phase k·d. A field whose
energy sits in a few large-scale modes does not average that phase away, so the moved copy stays
partly correlated, or anti-correlated, with the reference. On a domain with walls the harness rolls
the mirror-extended field and crops it, which on a step flips the step.

The test of "unrelated" used here is `energy_changed`, the mean squared difference from the
reference divided by its variance: an unrelated field with the same mean and variance gives exactly
2 (this follows from the definitions; it is not a citation).

| dataset, run | field | median `energy_changed` of the moved copy | within-frame max/min of the six draws, median |
|---|---|---|---|
| `kinet_re5e4`, `comparison_1790639359` | density | 1.64 (5–95%: 0.38–2.12) | 3.15 |
| | velocity | 3.05 (2.32–3.78) | 1.45 |
| | vorticity | 2.25 (2.00–2.88) | 1.24 |
| `sod_shock_tube`, `mse_1792825406` | density | 3.46 | 1.62 |
| | pressure | 3.49 | 1.73 |
| | velocity | 2.35 | 6.47 |

Every offset of the Sod tube was also enumerated exactly (2049 per frame, reproducing each of the
run's anchor values to 1e-16): the moved copy's median correlation with the reference is −0.77 on
density, and the mean squared error it scores is 1.6 times 2·var. The scale every Sod and kinet
damage number was divided by was therefore off by up to a factor of about 1.7, in a direction that
depended on the field. The pooled median itself was well determined (about ±5% on Sod density
under resampling of the draws), so the problem is bias, not noise, and more draws would not fix it.

Separately, every translation-invariant metric scores a translated copy at exactly its clean value,
so `increment_w1`, `increment_w1_by_separation`, `spectrum_l2`, `enstrophy`, `kinetic_energy` and
`palinstrophy` had no damage scale at all (`issues/037`).

## The choice

**The anchor is `mean_field`: each channel replaced by its spatial mean.** Damage 1 reads "as far
from the truth as the field's own mean".

- **Standard practice.** Skill scores are measured against a climatological reference forecast,
  the mean of the observations (Murphy 1988, *Monthly Weather Review* 116(12), 2417–2424,
  doi:10.1175/1520-0493(1988)116<2417:SSBOTM>2.0.CO;2). WeatherBench reports climatology as a
  baseline every data-driven model must beat (Rasp et al. 2020, *Journal of Advances in Modeling
  Earth Systems* 12(11), e2020MS002203).
- **Exact and deterministic.** For mean squared error the anchor is the reference's spatial
  variance exactly; nothing is drawn at random.
- **Independent of the boundaries.** A mean over the domain does not depend on what lies outside
  it, so the same anchor holds on a periodic domain and between walls.
- **Defined for nearly every metric.** Scored against a broadband 128² field, every pairwise and
  single-field metric then registered has a finite, nonzero span except `increment_flatness`, which
  is zero over zero on a constant field and takes the existing degenerate fallback.

**The translation stays, as a probe.** It is still run (`uncorrelated`, six draws) and reported on
the damage scale beside the Gaussian impostor, as "the right statistics in the wrong place": the
double penalty at its limit, which is the question this repository exists for. Its bias is now a
documented property of a probe rather than a factor in every number.

## Two close calls inside the choice

- **The per-frame spatial mean, not a time-mean climatology.** For a statistically homogeneous flow
  the two agree; the spatial mean needs no other frame. For an inhomogeneous problem such as the
  Sod tube a per-location time mean would keep the tube's structure, which would defeat the purpose
  of a reference that knows nothing about positions. This is the agent's reasoning, not a source.
- **Ensemble runs are unchanged.** Their ladder (`ensemble_miscalibration.yaml`) carries neither
  the old nor the new anchor; their fingerprints already record `spread_inflate@max` or `bias@max`.

## What it changes

Every damage number, and every statistic read on the damage scale: detection and saturation
levels, the blindness bound, the impostor's damage. Under the new anchor a pointwise error charges
more per unit of field change than before (for mean squared error the span is the variance rather
than the 1.45 to 3.05 times the variance the translation gave on kinet), so detection comes earlier, and a field with the right statistics in the wrong place scores
a damage near 2. The impostor threshold of 0.5 keeps its meaning: a metric fooled by the impostor
still scores it near 0. Six metrics gain a damage scale they did not have.

Measured on the new pinned run `comparison_1793302178` (`kinet_re5e4`, start 2000, reduction
50, 161 frames) against the previous one, `comparison_1790639359`, which used the same data, seed
and ladder plus the `mean_field` entry. The ratio is old span over new span, so it is the factor
by which each metric's damage numbers grow; "none" means the metric had no damage scale before.

| metric | density | velocity | vorticity |
|---|---|---|---|
| `mse` | 1.45 | 3.05 | 2.36 |
| `rmse` | 1.21 | 1.75 | 1.54 |
| `mae` | 1.17 | 1.72 | 1.90 |
| `nrmse` | 1.28 | 1.75 | 1.50 |
| `h1_seminorm` | 1.38 | 1.54 | 1.41 |
| `h_minus_one` | 1.11 | 1.79 | 1.75 |
| `increment_w1`, `increment_w1_by_separation`, `spectrum_l2` | none | none | none |
| `enstrophy`, `palinstrophy` (vorticity only) | — | — | none |
| `kinetic_energy` (velocity only) | — | none | — |
| `increment_flatness` | none, still | none, still | none, still |

For `mse` the ratio is the old anchor's median `energy_changed`, since the new span is the
variance: 3.05 against 3.05 on velocity, and 1.45 against 1.64 on density, where the variance
changes enough between frames that a ratio of medians and a median of ratios differ. Over the 396 ordinary rows, 88 now reach
`saturation_level` (12 of 360 before), 173 reach `severity_50` (69) and 291 `severity_10` (165).
`spectrum_l2` scores the Gaussian impostor at damage 0.000 on every field: the trap now prints the
phase blindness it was built to catch, where before it printed a dash.

## Not chosen

- **Keep the translation and report the spread of its draws** (issue 092's first option). The
  spread measures noise; the problem is bias, which a spread cannot show.
- **An exact Sod solution at another time or diaphragm position** (issue 092's second option). It
  applies to one dataset only and changes the waves' widths, so it is not a twin either.
- **An independent realisation** (`issues/004`). The principled "unrelated field", and still wanted,
  but the data does not exist.
