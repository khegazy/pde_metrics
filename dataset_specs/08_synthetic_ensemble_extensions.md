# Dataset 08: extensions of the generated synthetic ensemble

**Catalog clusters:** D6 (extensions of the synthetic ensemble) and B3 (the synthetic-ensemble
family that builds it). **Metrics served:** the eight ensemble metrics (`crps`,
`crps_skill_score`, `energy_score`, `ensemble_mean_rmse`, `rank_histogram`,
`rank_histogram_chi2`, `spread_skill`, `variogram_score`), and `wasserstein` and `h_minus_one`
on an ensemble's member mean. **Proposals and issues served:**
the Gneiting-forecaster proposal, `EXP-spread_skill-heteroscedastic-synthetic-ensemble`, the
correlated-ensemble proposal (the first and third deleted once built, step 11 of
`BUILD_ORDER.md`), the test half of
`MTR-energy_score-patched-energy-score`; issues 127 and 083 (only their need for
dispersion that varies between cells), and 111 (which two of the new operators also trigger).
**Date:** 2026-11-26. **Author:** research sub-agent (branch `build_datasets`). Nothing here is
built. Every number marked "measured" comes from short scripts in the session scratchpad that
call the repository's own metric functions (listed in Section 8); every formula marked "my
derivation" is mine and was checked against such a script.

## 1. Purpose

The eight ensemble metrics have one piece of evidence, `synthetic_ensemble`: a truth and 16
members drawn as `b(x, t) + σ ε` with one σ everywhere and independent Gaussian noise ε in
every cell (`fmeval/data/synthetic_ensemble.py`; `docs/datasets/synthetic_ensemble.md`,
Eq. 1). That validates the estimators against arithmetic. It cannot reproduce the
experiments these metrics' own fields run, and the cards say so:

- **No calibrated but useless forecaster.** Every rung of `ensemble_miscalibration` is
  miscalibrated, so no experiment asks whether `rank_histogram` and `spread_skill` pass a
  climatological forecast (they should) while `crps` ranks it last (`crps` card, "The
  experiment"; `rank_histogram` card, same heading).
- **A flat spread–error diagram.** With one σ everywhere, cases binned by predicted spread
  differ only by sampling noise, so the binned diagram of Leutbecher and Palmer is withheld as
  degenerate (`spread_skill` card, "The figures").
- **No spatial correlation to get wrong.** `energy_score` and `variogram_score` exist to judge
  the correlation between cells, and "no experiment in the repository changes" it (their cards,
  "The experiment, and what this repository cannot show").
- **No wrong centre under a narrow spread.** The `crps` card notes that no experiment has an
  ensemble "whose centre is wrong, on which collapsing the spread would remove the only thing
  covering that error".
- **No non-Gaussian member distribution.** `spread_inflate` keeps every normalised moment, so a
  skewed or heavy-tailed ensemble is "not represented anywhere" (`degradations/spread_inflate/card.md`,
  Limitations).
- **No positive density.** `wasserstein` is `not_run` because the signed pattern makes every
  value NaN (`metrics/wasserstein/card.yaml`).
- **One draw of the null.** The reader draws from its own `seed` option, not the run's, so a
  second draw of the null is a second reader seed (`+dataset.reader.seed=<n>`); Kareem decided
  on 2026-11-27 that the reader does not need to know the run's seed.

This document specifies the reader options and ensemble operators that close each gap, each
with an answer known in advance. It stays inside the generated ensemble; physical ensembles,
lead time and the exchangeability argument are specified in `01_physical_ensemble.md`
(Section 3 there, which this document uses without repeating). Kareem's instruction of
2026-11-26 governs the design: options on the existing reader and operators in the existing
ensemble registry, with the least new code; where the framework could not produce an exact
known answer, the design was changed to fit it (Section 3.3 and 3.4 say where).

## 2. What the dataset must provide

- **Fields.** `density` only, as today. Grid 64² (32² for the correlated variant, because
  `variogram_score` costs O(d²): 0.12 s at 32² and 1.4 s at 64², `variogram_score` card).
  Every axis periodic, spacing 1 cell.
- **Members and frames.** 16 members, 12 frames (40 for the correlated variant). Every frame is
  an independent draw, so frames are repeats; with cells as cases one frame holds 4 096 cases.
- **Variants.** Six reader configurations (Section 3), each a calibrated null with a known
  answer, plus the candidates: five new ensemble operator entries and the existing three.
- **Known answers.** For every variant and candidate, the expected value of each ensemble
  metric or the exact invariance it must show (Sections 3.1 to 3.7).
- **Several draws.** The run seed must reach the reader (Section 3.7).

## 3. Option A, the analytic ideal: options on the existing generator

Everything here is computed on the fly by `SyntheticEnsembleTrajectory`, nothing is stored,
and a default construction stays bitwise identical to today's (the new options default to
"off"). Per field, frame t and cell x, the reader draws

```
truth(x)    = T( b(x,t) + sigma(x) eta_0(x) )                                    (1)
member_i(x) = T( b(x,t) + delta sigma(x) + sigma(x) eta_i(x) ),  i = 1..M
```

where b is the deterministic part, σ(x) the noise level, η_0 and η_i independent unit-variance
noise fields, δ a member offset in units of σ, and T an optional positive transform. Each of
the seven items below sets one of these.

| Option (new, default) | Sets | Item |
|---|---|---|
| `base`: `two_scale` (today), `case_means`, `zero` | b | 3.1, 3.3 |
| `sigma_ratio`: 1.0 | σ(x) | 3.2 |
| `noise_length`: 0 (independent cells); `noise_covariance`: `exponential` or `rational` | η_0, η_i | 3.3 |
| `member_noise_length`, `member_noise_covariance`: unset (as truth) | η_i only | 3.3 |
| `member_offset`: 0.0 | δ | 3.5 |
| `log_amplitude`: 0.0 | T(v) = exp(λ v) when λ > 0 | 3.6 |
| `seed`: `${seed}` in the dataset config | every draw | 3.7 |

The ensemble operators act on the member stack only, through `apply_severity_level`
(`fmeval/ladder.py`): they never see b, σ(x) or the truth. That constraint decides which
candidate is an operator and which a reader option.

### 3.1 The Gneiting forecaster suite (reader `base: case_means`, `sigma: 1`; operator `gneiting_forecaster`)

**The source experiment.** Gneiting, Balabdaoui and Raftery (2007, Sect. 1, Table 1, p. 245):
nature draws a case mean μ_t ~ N(0, 1) and the observation from G_t = N(μ_t, 1), for
t = 1 … 10 000; four forecasters issue

| Forecaster | Predictive distribution F_t (their Table 1) | Calibration (their Sect. 2.2, 2.3, Table 2) |
|---|---|---|
| Ideal | N(μ_t, 1) | probabilistically, exceedance and marginally calibrated (Example 1) |
| Climatological | N(0, 2) | probabilistically and marginally calibrated, not exceedance (Example 2) |
| Unfocused | ½{N(μ_t, 1) + N(μ_t + τ_t, 1)}, τ_t = ±1 with probability ½ | probabilistically calibrated only (Example 3) |
| Hamill's | N(μ_t + δ_t, σ_t²), (δ_t, σ_t²) = (½, 1), (−½, 1) or (0, 169/100), each with probability ⅓ | none; its PIT departs from uniform by at most 0.0032 (Sect. 2.3) |

The PIT (probability integral transform, F_t evaluated at the observation) histograms of all
four "are essentially uniform" (Sect. 1, Fig. 1). Table 5 (Sect. 3.4, p. 257) reports average
CRPS ideal 0.56, Hamill's 0.61, unfocused 0.63, climatological 0.78, and average logarithmic
score 1.41, 1.52, 1.53, 1.75; Table 4 (Sect. 3.3) reports central 90% interval widths 3.29,
3.62, 3.68, 4.65.

**Transfer to the grid (my design).** Each cell is a case. The reader option
`base: case_means` replaces the two-scale pattern by μ(x) ~ N(0, 1) drawn independently per
cell, frame and field from `derive_rng(seed, "case_mean", t, field)`, and the dataset config
sets `sigma: 1`. Then truth = μ + η_0 and the clean members μ + η_i *are* the ideal forecaster,
so the ladder's reference level is the ideal forecaster. One operator,
`gneiting_forecaster(members, severity, *, ctx, kind)`, registered `family="ensemble"`,
`ensemble=True`, `stochastic=True`, `ordinal=False`, `zero_is_identity=False`, no
`preserves`, produces the other three from the ideal members without knowing μ:

1. **`kind: climatological`.** Replace every member by `sqrt(2) * ctx.rng.standard_normal`.
2. **`kind: unfocused`.** Add τ(x) B_i(x), τ = ±1 drawn once per cell, B_i ∈ {0, 1} drawn per
   member and cell. An ideal member plus τB is a draw from the mixture exactly.
3. **`kind: hamill`.** Draw (δ, s²) once per cell from the three equiprobable pairs and add
   δ + sqrt(s² − 1) ζ_i with ζ_i standard normal. Since s² ≥ 1 this is N(μ + δ, s²) exactly.

The constants are Table 1's and live only in this operator; they presuppose the suite's
reader settings, which the operator's docstring and card state. Ladder file
`configs/degradation/gneiting_forecasters.yaml`: three entries with `op: gneiting_forecaster`,
`severities: [0]` and `options: {kind: ...}` (the `translate_x`/`translate_y` pattern of
`configs/degradation/default.yaml`), plus the `mean_field` anchor. Being `ordinal=False`, they
enter the analysis as probes, excluded from every rank correlation, as `gaussian_impostor` is.

**Known answers (exact expectations; my derivations from the kernel form
CRPS = E|X − y| − ½E|X − X′|, the `crps` card's Eq. 2, and from the forecasters' definitions).**
With E|N(m, v)| = m(2Φ(m/√v) − 1) + 2√v φ(m/√v):

```
CRPS_ideal = (1/2) E|N(0,2)|                                    = 1/sqrt(pi)  = 0.5642
CRPS_clim  = (1/2) E|N(0,4)|                                    = sqrt(2/pi)  = 0.7979
CRPS_unf   = (1/2)[E|N(0,2)| + E|N(1,2)|] - (1/4)[E|N(0,2)| + E|N(1,2)|]  = 0.6319   (2)
CRPS_ham   = (1/3) sum over (d, s2) of { E|N(d, s2+1)| - (1/2) E|N(0, 2 s2)| } = 0.6144
```

The fair estimator has these expectations for independent members (Ferro 2014, through the
`crps` card). For the ensemble mean x̄ of M members, E(x̄ − y)² is 1 + 1/M (ideal),
2(1 + 1/M) (climatological), 1.25(1 + 1/M) (unfocused) and 7/6 + 1.23/M (Hamill's), and the
mean member variance is 1, 2, 1.25 and 1.23. Every probabilistically calibrated forecaster
gives a flat rank histogram in expectation, because the probability of rank k is a binomial
moment of the PIT distribution (my derivation). The energy score per √d tends, for many
independent cells, to sqrt(E(X − y)²) − ½ sqrt(E(X − X′)²) (my derivation, by concentration of
the norm). The skill score's climatology is the frame's own empirical distribution
(`judgements/011`), here a 4 096-sample of N(0, 2), so CRPSS ≈ 1 − CRPS/0.7979.

| Metric (M = 16) | Ideal | Hamill's | Unfocused | Climatological | Source |
|---|---|---|---|---|---|
| `crps`, exact | 0.5642 | 0.6144 | 0.6319 | 0.7979 | Eq. (2) |
| `crps`, Gneiting et al. Table 5 | 0.56 | 0.61 | 0.63 | 0.78 | published |
| `crps`, measured | 0.5625 | 0.6128 | 0.6297 | 0.7975 | scratch run |
| `ensemble_mean_rmse`, exact sqrt(E e²) | 1.0308 | 1.1151 | 1.1524 | 1.4577 | above |
| `ensemble_mean_rmse`, measured | 1.0293 | 1.1138 | 1.1492 | 1.4569 | scratch run |
| `spread_skill`, ratio of expectations | 1 | 1.0251 | 1 | 1 | above |
| `spread_skill`, measured | 1.0008 | 1.0251 | 1.0024 | 1.0001 | scratch run |
| `rank_histogram`, measured (null 0.050 ± 0.009) | 0.049 | 0.050 | 0.047 | 0.048 | scratch run |
| `rank_histogram_chi2`, measured (null 16 ± 5.7) | 16.0 | 15.8 | 15.1 | 15.1 | scratch run |
| `energy_score`/√d, large-d limit | 0.7071 | 0.7639 | 0.7906 | 1.0000 | above |
| `energy_score`/√d, measured | 0.7061 | 0.7630 | 0.7882 | 0.9994 | scratch run |
| `crps_skill_score`, ≈ 1 − CRPS/0.7979 | 0.293 | 0.230 | 0.208 | 0 | above |
| `crps_skill_score`, measured | 0.295 | 0.232 | 0.210 | −0.000 | scratch run |

"Measured" is the mean over 12 frames of 64² cells with the scratch implementation of the
three operators above, scored by the repository's metric functions; the null values are the
multinomial reliability index and the χ²(16) mean and standard deviation. **The published
climatological value 0.78 sits about three standard errors below the exact 0.7979** (the
standard error of a 10 000-case mean is 0.0057, measured from the per-case spread); the
other three agree to the published rounding. The build should test against the exact column.
`variogram_score` is not derived here: on independent cells it adds nothing beyond the per-cell
scores (the proposal's point), and its values should simply rank the four as the CRPS does.

**What it shows.** A calibrated but useless forecaster that `rank_histogram`,
`rank_histogram_chi2` and `spread_skill` pass while `crps`, `energy_score` and
`crps_skill_score` rank last; Hamill's forecaster, nearly calibrated and wrong case by case,
which only the proper scores separate from the unfocused one.

### 3.2 Heteroscedastic ensembles (reader `sigma_ratio`; operator `flow_dependence`)

**Reader option.** `sigma_ratio = R ≥ 1` makes the noise level vary over the first axis,

```
sigma(x) = sigma * R^{w(x)},   w(x) = (1/2)[1 + sin(2 pi i / n_x)],   i = 0..n_x-1      (3)
```

for truth and members alike, so the ensemble stays exchangeable cell by cell and every
statement of `01_physical_ensemble.md`, Section 3, holds per cell. Proposed: `sigma: 0.05`,
`R = 4` (σ from 0.05 to 0.2), base `two_scale`. Only variation between regions is specified,
not between frames: an operator sees one frame at a time, so a σ that changes only from frame
to frame could not be acted on.

**Operator `flow_dependence(members, severity, *, direction)`** (`ensemble=True`,
deterministic, `preserves=("ensemble_mean",)`, severity s ≥ 0, two ladder entries with
`options: {direction: damp}` and `{direction: amplify}`). With ŝ(x) the per-cell sample
standard deviation of the members, it sets the members' per-cell spread to k ŝ^a with
a = 1 − s (damp) or 1 + s (amplify), k chosen so the frame's mean sample variance is kept:

```
members' = scale_spread(members, k * s_hat^(a-1)),   k^2 = mean(s_hat^2) / mean(s_hat^(2a))     (4)
```

`scale_spread` (`degradations/_shared/ensemble.py`) already scales about the member mean;
passed a per-cell factor array it broadcasts, so no change to it is needed. Severity 0 is
the identity; damp s = 1 removes flow-dependence (a = 0), s = 2 inverts it (a = −1); amplify
s = 1 is a = 2. Proposed severities: damp [0.25, 0.5, 1, 1.5, 2], amplify [0.5, 1, 2].

**Known answers.**
1. **Exact invariances (my derivation, measured to round-off).** The member mean is unchanged,
   so `ensemble_mean_rmse` and every bin's error are unchanged; the frame's mean sample variance
   is unchanged, so `spread_skill` is unchanged. Measured: 1.00611 and 0.12721 at every a.
2. **The binned spread–error diagram (Leutbecher and Palmer 2008, Sect. 2.2, Fig. 4: 20
   equally populated bins of predicted spread; through `01_physical_ensemble.md`).** Binned by the
   *true* σ(x), which the reader knows, a calibrated ensemble lies on the diagonal:
   E e² = (M + 1)/M σ² in each bin (memo Eq. 6). Binned by the *sample* spread ŝ, the curve is
   flattened, because E[e² | ŝ] = (M + 1)/M E[σ² | ŝ] and large ŝ overstates σ (my derivation;
   the point Leutbecher and Palmer make in Sect. 2.2 that spread variability must exceed
   sampling noise, quoted in the `spread_skill` card). Measured log–log slope of error against
   sqrt((M + 1)/M) × spread over the 20 bins: 0.869 (R = 4, M = 16).
3. **Each operator's slope.** Because (4) is monotone in ŝ for a > 0 and errors are unchanged,
   the bins hold the same cells and only their spread coordinate moves to k ŝ^a: the slope is
   the calibrated slope divided by a (my derivation). Predicted and measured: a = 0.5, 1.738
   and 1.736; a = 2, 0.435 and 0.435; a = −1 (bins reversed), −0.869 and −0.866; a = 0, all
   20 bins collapse onto one point (spread 0.128, error 0.124 to 0.125).
4. **What responds.** `crps` rises: 0.0631 (calibrated), 0.0633 (a = 0.5), 0.0659 (a = 0),
   0.0677 (a = 2), 0.0751 (a = −1). `rank_histogram` rises from 0.047 to 0.17, 0.23, 0.48 and
   0.41; at a = 0 the pooled histogram is a dome (end bins 0.85, centre 1.41 of the flat
   value), a shape set by this σ distribution, not a general law. `energy_score` moves by
   less than 1e-4 relative: it is nearly blind to flow-dependence on independent cells
   (measured, 12 frames).

This is also the data that issue 127 (a CRPS decomposition needs dispersion varying between
cases) and issue 083 (a correlation between reported uncertainty and error is undefined at
constant dispersion) name; neither the decomposition nor issue 083's model is built here.

### 3.3 Correlated members (reader options only; no operator)

**Construction.** With `noise_length = ℓ > 0` each noise field is a stationary Gaussian random
field on the periodic grid with covariance C(r), r the shortest distance on the torus in cells:

```
exponential:  C(r) = exp(-r / l)          (Scheuerer and Hamill 2015, Eq. 5, with r for |i - j|)
rational:     C(r) = (1 + r / l)^(-1)     (their Sect. 3c, model (i))                     (5)
eta = Re IFFT( A(k) FFT(w) ),   A(k)^2 = lambda(k) / mean(lambda),   lambda = Re FFT( C(r) )
```

with w white standard-normal noise from the reader's existing generator. λ are the eigenvalues
of the circulant covariance matrix, so η has covariance exactly C(r) on the grid and per-cell
variance exactly 1 in expectation; the multiply-and-invert step is `_apply_filter`
(`degradations/_shared/filters.py`). The torus distance grid equals
`fmeval.wavenumbers.wavenumber_magnitude(shape)`, whose entries are |fftfreq(n)·n| per axis,
the same min(k, n − k) rule `variogram_score` uses for its periodic distances. Measured: lag
correlations of a 128² draw at ℓ = 3 of 1, 0.716, 0.513, 0.367, 0.263, 0.188 against
exp(−r/3) = 1, 0.717, 0.513, 0.368, 0.264, 0.189; the smallest eigenvalue is positive for
ℓ = 2, 3, 4.5 at 32² and 64² and for the rational model at 32² (the reader must check this
and raise otherwise). Scheuerer and Hamill's vectors are one-dimensional; using the Euclidean
torus distance in two dimensions is my transfer.

**Why the impostor's draw is not reused.** `gaussian_impostor` keeps a given field's |X_k|
and randomises only the phases. A field with fixed Fourier amplitudes is Gaussian only
asymptotically, and every known answer here (identical per-cell marginals, the variogram
score's Gaussian moments) needs an exactly Gaussian field, which a filter applied to white
noise gives. Its draw also lives in the impostor's own module, not in `_shared/`.

**Why the candidate is a reader option, not an operator (the framework constraint).** An
operator sees only the members, so the only redraw open to it re-colours each member's
deviation from the member mean, x̄ + T(x_i − x̄). The members then share the component
(I − T) ε̄, which makes them dependent, and the fair estimators are unbiased only for
independent members. Measured with such an operator (32², 12 frames, r = 2 against a truth at
r = 3, with an approximate spectral form of the exponential): `variogram_score` fell by 0.23% (paired t = −4.2), the wrong direction for a proper
score. So the members' correlation is set by `member_noise_length` and
`member_noise_covariance` (unset means as the truth), and each miscorrelated ensemble is a
reader variant, exactly Scheuerer and Hamill's experiment (their Sect. 3b–c: truth at r = 3,
forecasts at r = 2, 3, 4.5; models (i) and (ii) at matched lag-one correlation; n = 5 000
cases, ensembles of 20 and 100, 10 repetitions). Proposed variants: truth ℓ = 3 exponential;
members ℓ = 2, 4.5, rational ℓ = 3, and independent cells (`member_noise_length: 0`). Base
`zero` and `sigma: 1`, because the two-scale pattern swamps the noise in |y_i − y_j|^p: with it
and σ = 0.15 the variogram score moved by 0.1% to 1.7% with paired t of at most 2.7 in 24
frames, against t up to 26 with base `zero` and σ = 1 (measured).

**Known answers.**
1. **Per-cell scores flat in expectation, exactly.** Every member's marginal at every cell is
   N(0, σ²) in every variant, so the expectations of `crps`, `ensemble_mean_rmse`² and the
   mean member variance are identical (my derivation). Nonlinear pooled summaries
   (`rank_histogram`, `rank_histogram_chi2`, the ratio `spread_skill`) keep their per-cell
   law but their sampling spread grows with the correlation of the cells, so the χ² null of
   mean M holds only for independent cells (`rank_histogram_chi2` card).
2. **`variogram_score` must respond, `energy_score` hardly.** Scheuerer and Hamill find the
   energy score "can hardly discriminate multivariate forecasts that differ only with respect to
   their correlations" (Sect. 3b, Fig. 2) and again lacks sensitivity to a wrong correlation
   model (Sect. 3c, Fig. 3), while the variogram score with p = 0.5 or 1 "discriminates well"
   (Sect. 3b), smaller p better (Sect. 3c), and discrimination falls slightly from d = 5 to 15
   (Sect. 3b). Expected values of the variogram score follow from Gaussian moments,
   E|X_i − X_j|^p = (2 Var)^{p/2} Γ((p + 1)/2)/√π with Var = 2σ²(1 − C(r_ij))
   (`01_physical_ensemble.md`, Sect. 4.4, its author's derivation).
3. **Measured on this grid** (32², σ = 1, 40 frames, 16 members, common random numbers),
   change against the calibrated ensemble: `variogram_score` +0.54% (ℓ = 2, paired t = 7.3),
   +0.49% (ℓ = 4.5, t = 4.0), +1.04% (rational, t = 3.7), +4.0% (independent cells, t = 26);
   `energy_score` +0.23%, −0.15%, −0.08%, +0.95% (|t| ≤ 2.6); `crps` and
   `ensemble_mean_rmse` with paired t between −2.0 and 2.3 over eight comparisons, consistent
   with no change. The responses are small because
   one frame is one case of d = 1 024 cells; forty frames suffice.

### 3.4 Skewed and heavy-tailed members (operator `member_shape`)

**Operator** `member_shape(members, severity, *, family)` (`ensemble=True`, deterministic,
`preserves=("ensemble_mean",)`, two ladder entries `heavy_tails` with
`options: {family: student_t}` and `skew` with `{family: two_piece}`). Per cell, with x̄ and ŝ
the members' sample mean and standard deviation:

1. Standardise: z_i = (x_i − x̄)/ŝ.
2. Map through a quantile function: u_i = Q(Φ(z_i)), with Q the Student-t quantile at
   ν = 1/s, or the two-piece normal quantile with σ₁ = 1 − s, σ₂ = 1 + s (the two-piece CDF of
   Jordan, Krüger and Lerch 2019, App. A.2.7).
3. Re-standardise u over the members and return x̄ + ŝ u.

The map is monotone and the identity as s → 0, so damage grows with severity (measured mean
squared change 0.0016 to 0.037 σ² for t, 0.0042 to 0.045 σ² for two-piece). Proposed
severities: t [0.1, 0.2, 0.3, 0.4] (ν = 10, 5, 3.3, 2.5); two-piece [0.2, 0.4, 0.6, 0.8]
(skewness 0.79 at s = 0.6, measured). A skew-normal is not used because no closed-form CRPS
for it was found in Jordan et al. (their Table 1 lists none); the two-piece normal has one.
A redraw from the family would have been simpler to write, but it does not move further from
the clean members as severity grows, which the contract test of a monotone axis requires.

**Known answers.**
1. **Exact blindness of the first two moments (my derivation, measured to 1e-16).** Every
   cell's sample mean and sample variance are unchanged, so `ensemble_mean_rmse` and
   `spread_skill` are bitwise unchanged at every severity. `energy_score` moved by less than
   1e-5 relative (measured): it too reads only the first two moments on independent cells.
2. **The rank histogram responds strongly.** Reliability index from 0.053 to 0.074, 0.116,
   0.173, 0.236 (t) and 0.094, 0.174, 0.241, 0.292 (two-piece). Heavy tails raise ranks 1 and
   M − 1 (1.64 and 1.61 of flat at ν = 2.5) and lower the centre; skew tilts it (rank 0 at
   2.03, rank M at 0.63 of flat at s = 0.8).
3. **The CRPS responds weakly, with a closed-form limit.** For M → ∞ the members become draws
   from the family with the truth's mean and variance (my reasoning), and the expected CRPS
   against a Gaussian truth is a one-dimensional integral of the closed forms (Jordan et al.,
   App. A.2.5 for t, checked against direct integration to 1e-15; App. A.2.7 for two-piece,
   citing Gneiting and Thorarinsdottir 2010). Per σ, Gaussian 0.5642; t at ν = 10, 5, 3.3,
   2.5: 0.5646, 0.5666, 0.5726, 0.5914; two-piece at s = 0.2 to 0.8: 0.5650, 0.5672, 0.5699,
   0.5725 (my quadrature). Measured at M = 16, as increments over the clean value: t +0.0013,
   +0.0036, +0.0073, +0.0124; two-piece +0.0006, +0.0024, +0.0047, +0.0068. The finite
   ensemble understates the t limit at small ν, because re-standardising 16 values bounds
   their tails.

### 3.5 A wrong-centre ensemble (existing `bias`; reader `member_offset` for deflation under bias)

**Calibrated spread around a wrong centre needs no new code.** The existing `bias` operator,
run through the broadcast lane, adds severity × (reference fluctuation RMS) to every member,
so `ensemble_miscalibration` already contains it.

**Deflation under bias needs the reader.** The ladder applies one operator per entry and does
not compose two, so `member_offset = δ` (in units of σ) moves the members' centre in the
reader, and the existing `spread_deflate` and `spread_inflate` axes then act on biased members.
Proposed configuration `synthetic_ensemble_offset` with δ = 1.

**Known answer (my derivation, measured).** `scale_spread` with factor α gives members
x̄ + α(x_i − x̄). For Gaussian members x̄ is independent of the deviations, so
x′_i − y ~ N(δσ, σ²[(1 + 1/M) + α²(1 − 1/M)]) and x′_i − x′_j ~ N(0, 2α²σ²), hence

```
E[fair CRPS] / sigma = E|N(delta, (1 + 1/M) + alpha^2 (1 - 1/M))| - alpha / sqrt(pi)        (6)
E[spread_skill]     ~ alpha sqrt((M+1)/M) / sqrt(delta^2 + (M+1)/M)
```

Measured against (6) at δ = 0, 1, 2 and α = 0.2 to 1.25 (64², 12 frames): agreement within
0.9%. At δ = 0, (6) puts the optimum at α* = sqrt((1 + 1/M)/((1 − 1/M)(1 − 2/M))) = 1.138
for M = 16, which explains the `crps` card's finding that the mildest inflation scores below
the clean ensemble. At δ = 1 the optimum moves to α* = 1.64 and at δ = 2 to 2.75. Deflation to
α = 0.2 costs 0.160σ at δ = 0, 0.243σ at δ = 1 and 0.374σ at δ = 2: the case the `crps` card
calls untested, with its answer.

### 3.6 A positive-density variant (reader `log_amplitude`)

`log_amplitude = λ > 0` applies T(v) = exp(λ v) to truth and members after (1). Proposed
λ = 0.1, so density lies in about [0.82, 1.23], near the unit mean density of the kinet data.

**What stays known.**
1. **Rank histogram bitwise identical** to the untransformed run with the same seed, because T
   is monotone (measured: identical histograms in every frame).
2. **Exchangeability survives any transform**, so the Leutbecher–Palmer relations and a
   `spread_skill` of one in expectation hold (measured 0.999).
3. **CRPS in closed form.** Each cell is log-normal with parameters (λb, λσ); the expected CRPS of
   a calibrated log-normal forecast is ½E|X − X′|,

   ```
   E CRPS(x) = exp(lambda b(x) + lambda^2 sigma^2 / 2) (2 Phi(lambda sigma / sqrt(2)) - 1)      (7)
   ```

   (my derivation from the kernel form; checked by Monte Carlo against the log-normal CRPS of
   Baran and Lerch 2015 as given by Jordan et al., App. A.3.5). Measured mean CRPS 0.00847
   against 0.00848 from (7) at λ = 0.1.
4. **`wasserstein` runs** on the member mean, as every pairwise metric on an ensemble does.
   For densities near 1 it should approach the H⁻¹ norm of the difference (Peyre 2018, Eq. 5,
   through the `h_minus_one` card). Measured ratio of `wasserstein` to `h_minus_one` on the
   mean-normalised pair: 0.995 at λ = 0.1 and 0.889 at λ = 1 (6 frames, 0.02 s per call).
   Every mean-preserving operator here (`spread_inflate`, `spread_deflate`,
   `flow_dependence`, `member_shape`) leaves it exactly unchanged, the same blindness recorded
   for `h_minus_one` on `synthetic_ensemble`; only `bias` and the anchor move it.

### 3.7 Several draws of the null

**Not done, by decision.** This proposed adding `seed: ${seed}` to the `reader` block of
`configs/dataset/synthetic_ensemble.yaml`, which would change every number of a synthetic run.
Kareem decided on 2026-11-27 that the reader does not need to know the seed used to generate the
data, so the reader keeps its own `seed` option and another draw is another reader seed. Each
frame is already an independent draw, so twelve frames give twelve draws within a run; reader
seeds add more. Measured spread over 40 seeds of the default reader (frame 0, 64², 16
members): `crps` 0.0846 ± 0.0010 (closed form σ/√π = 0.0846), `spread_skill` 1.0005 ± 0.0109,
`ensemble_mean_rmse` 0.1546 ± 0.0016 (σ sqrt(17/16) = 0.1546), `energy_score` 6.786 ± 0.075
(large-d limit 6.788), `rank_histogram` 0.052 ± 0.011 (multinomial null 0.050 ± 0.009),
`rank_histogram_chi2` 17.2 ± 5.8 (χ²(16): 16 ± 5.7), `crps_skill_score` 0.763 ± 0.003.

## 4. Options B to D: simulated systems

None. Every answer above is exact or a one-dimensional integral, and seconds of generation
replace any solver. The physical counterpart, a perturbed-initial-condition ensemble on which
the same operators could be applied to real members, is `01_physical_ensemble.md`, Options B
to D; that document's Option A is the lead-time extension of this generator and is not
repeated here.

## 5. Recommendation

1. ~~The seed interpolation (3.7)~~: not done, by Kareem's decision of 2026-11-27 (3.7).
2. **The Gneiting suite (3.1)**: the only item with published values, and the clearest
   demonstration on any card that calibration is not skill.
3. **`member_offset` (3.5) and `member_shape` (3.4)**: a reader option of two lines and one
   operator; both run on the existing default variant and the existing ladder file.
4. **`sigma_ratio` and `flow_dependence` (3.2)**: needed before the binned spread–error figure
   can be drawn; that figure itself is a separate change to `spread_skill` (a companion storing
   per-bin spread and error), outside this specification.
5. **Correlated members (3.3)**: the largest reader change and the slowest run (40 frames of
   the variogram score), but the only test of what `energy_score` and `variogram_score` add.
6. **The positive variant (3.6)** last: it admits `wasserstein`, which then measures little
   beyond `bias`.

## 6. What to store

Nothing is stored: every variant is a reader configuration, generated on the fly from its
seed. The repository receives configs and code.

### 6.1 Dataset configs and evidence entries

Each new dataset config starts `defaults: [synthetic_ensemble, _self_]` (the `kinet_re5e4.yaml`
pattern) and sets its name, options and `complexity` block (family `synthetic_ensemble`, rank
−1). Each is admitted to `evidence_datasets` in `configs/cards/default.yaml` with
`{periodic: true, ensemble: true}`, as Decision 9 of `BUILD_ORDER.md` requires:

| Config | Reader options | Evidence label (proposed) |
|---|---|---|
| `synthetic_ensemble_gneiting` | `base: case_means`, `sigma: 1` | forecasters of known calibration and sharpness with published and exact scores: evidence on whether the metric ranks them as proper scores do, and nothing about turbulence |
| `synthetic_ensemble_heteroscedastic` | `sigma: 0.05`, `sigma_ratio: 4` | a calibrated null whose true spread varies across the domain: evidence on whether the metric sees an ensemble that knows which cells are uncertain |
| `synthetic_ensemble_correlated` | `grid: [32, 32]`, `n_frames: 40`, `base: zero`, `sigma: 1`, `noise_length: 3`; member variants by `+dataset.reader.member_noise_length=...` | a calibrated null with spatially correlated noise: evidence on whether the metric sees the members' correlation structure |
| `synthetic_ensemble_offset` | `member_offset: 1` | an ensemble centred one noise level off the truth: evidence on how the metric charges a wrong spread around a wrong centre |
| `synthetic_ensemble_positive` | `log_amplitude: 0.1` | a calibrated null on a positive density: evidence that transport metrics run on an ensemble mean and are blind to its spread |

Ladders: `gneiting_forecasters.yaml` (new) for the first; `ensemble_miscalibration.yaml`,
extended by four entries (`flow_dependence_damp`, `flow_dependence_amplify`, `heavy_tails`,
`skew`), for all the others. Every new degradation and figure goes into `TEST_DESCRIPTION.md`
(a test fails otherwise), and `docs/datasets/synthetic_ensemble.md` gains a row per variant in
its "Variations" table.

### 6.2 Existing code reused and new code needed

Line counts are my estimates of code, excluding docstrings, cards and tests unless stated.

| Piece | Existing code it extends or reuses | New code |
|---|---|---|
| Reader options `base`, `sigma_ratio`, `member_offset`, `log_amplitude` | `SyntheticEnsembleTrajectory.__init__` and `read_frame` in `fmeval/data/synthetic_ensemble.py`; `derive_rng` for the case means; `meta` records the options | about 20 lines plus validation |
| Reader options `noise_length`, `noise_covariance`, `member_noise_*` | `_apply_filter` (`degradations/_shared/filters.py`) for the draw, `wavenumber_magnitude` (`fmeval/wavenumbers.py`) for the torus distance; transfer computed once in `__init__` | about 15 lines |
| Run seed to reader | `${seed}` interpolation in `configs/dataset/synthetic_ensemble.yaml`, as `${paths.data}` is | 1 config line |
| `gneiting_forecaster` operator | `@degradation` registry, `ctx.rng`, the ladder's `op`/`options` entries | about 20 lines, plus a bundle card and a test of the three distributions |
| `flow_dependence` operator | `scale_spread` (`degradations/_shared/ensemble.py`) with a per-cell factor array, unchanged | about 10 lines, plus card and test |
| `member_shape` operator | x̄ and ŝ as `scale_spread` uses them; `scipy.stats` quantiles | about 15 lines, plus card and test |
| Wrong centre, calibrated spread | `bias` through the broadcast lane | none |
| Deflation and inflation under bias | `spread_deflate`, `spread_inflate` on the offset variant | none |
| Contract tests | `LADDERS` in `tests/test_degradation_contract.py` | 3 entries |
| Configs | `synthetic_ensemble.yaml` inherited; `ensemble_miscalibration.yaml` extended | 5 dataset files of about 10 lines, 1 ladder file of about 15, 4 ladder entries, 10 evidence lines |

No new reader, no new shared helper and no alias. Two questions of fit are left to the
builder: whether the reader in `fmeval/data/` may import a helper from
`degradations/_shared/` (it crosses packages; the alternative is the one line
`np.real(np.fft.ifftn(np.fft.fftn(w) * A))`), and whether calling `wavenumber_magnitude` for a
distance reads clearly enough with a comment, or a two-line `minimum(k, n − k)` grid is better.

**Known interactions with open issues.** `flow_dependence` and `member_shape` preserve the
ensemble mean exactly, so their `field_change_max` is round-off and their
`damage_per_change` is about 1e30, exactly the defect of issue 111; the cards' profile rows
will misread them until that issue is fixed. The `preserves` vocabulary cannot say that
`member_shape` also keeps every cell's sample variance; a word for it would be about five
lines in `degradations/registry.py` and its contract test, and is optional.

## 7. References

- Gneiting, T., Balabdaoui, F. and Raftery, A. E. (2007). Probabilistic forecasts, calibration
  and sharpness. *Journal of the Royal Statistical Society B* 69(2), 243–268,
  https://doi.org/10.1111/j.1467-9868.2007.00587.x. **Read in full** (University of Washington
  copy, sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jrssb.pdf, through a
  text extraction of the PDF; figures not viewed): Sect. 1 and Table 1 (p. 245), Fig. 1
  caption and text; Sect. 2.2, Examples 1 to 3 and Table 2; Sect. 2.3 (pp. 249–250,
  |ε(p)| ≤ 0.0032); Sect. 3.3, Table 4; Sect. 3.4, Eq. (14) and Table 5 (p. 257).
- Scheuerer, M. and Hamill, T. M. (2015). Variogram-based proper scoring rules for
  probabilistic forecasts of multivariate quantities. *Monthly Weather Review* 143(4),
  1321–1334, https://doi.org/10.1175/MWR-D-14-00269.1. **Read Sect. 3 to 3c in full** (NOAA
  repository copy, repository.library.noaa.gov/view/noaa/22327, through a text extraction):
  Eq. (5); Sect. 3b (r = 3 against 2, 3, 4.5; d = 5 and 15; n = 5 000; m = 20 and 100; 10
  repetitions); Sect. 3c models (i) and (ii); the quoted findings. Figures not viewed.
- Jordan, A., Krüger, F. and Lerch, S. (2019). Evaluating probabilistic forecasts with
  scoringRules. *Journal of Statistical Software* 90(12), https://doi.org/10.18637/jss.v090.i12;
  arXiv:1709.04743. **Read on ar5iv** (arXiv version): Table 1; App. A.2.3 (normal), A.2.5
  (Student t), A.2.7 (two-piece normal), A.3.5 (log-normal). Appendix formulas are unnumbered;
  the section numbers are the arXiv version's and were not checked against the journal.
- Gneiting, T. and Thorarinsdottir, T. L. (2010). Predicting inflation: professional experts
  versus no-change forecasts. Working paper. **Not opened**; cited by Jordan et al., App. A.2.7,
  for the two-piece normal CRPS.
- Baran, S. and Lerch, S. (2015). Log-normal ensemble model output statistics for wind speed.
  **Not opened**; cited by Jordan et al., App. A.3.5, for the log-normal CRPS; the full
  bibliographic details were not checked.
- Leutbecher, M. and Palmer, T. N. (2008). Ensemble forecasting. *Journal of Computational
  Physics* 227(7), 3515–3539, https://doi.org/10.1016/j.jcp.2007.02.014. **Not re-read here**;
  Sect. 2.2, Eqs. 5 to 7 and Fig. 4 as read in full by the author of `01_physical_ensemble.md`
  (ECMWF Tech. Memo. 514 numbering) and quoted in the `spread_skill` card.
- Ferro, C. A. T. (2014), fair scores; Fortin et al. (2014), the spread estimator; Hamill
  (2001), rank histograms; Gneiting and Raftery (2007), the kernel form of the CRPS (their
  Eq. 21); Peyre (2018), *ESAIM: COCV* 24(4), 1489–1501, Eq. 5. **Not opened here**; cited
  through the `crps`, `spread_skill`, `rank_histogram` and `h_minus_one` cards, whose authors
  read them.
- Repository sources read: `dataset_specs/README.md`, `BUILD_ORDER.md`,
  `01_physical_ensemble.md`; `FUTURE_EXPERIMENTS_CATALOG.md` (D6, B3); the four proposals and
  issues 003, 044, 083, 111, 127 named in the front matter; `fmeval/data/synthetic_ensemble.py`,
  `fmeval/ladder.py` (ensemble application), `fmeval/context.py`, `fmeval/wavenumbers.py`,
  `degradations/registry.py`, `degradations/_shared/{ensemble,filters}.py`,
  `degradations/{bias,gaussian_impostor,spread_inflate,spread_deflate}`; the eight ensemble
  cards' Definition, field and Limitations sections; `metrics/wasserstein/card.yaml`.
- Scratch scripts (session scratchpad, `spec08/`): `a_gneiting.py`, `b_hetero.py`,
  `c_corr.py`, `c2_corr.py`, `c3_corr.py`, `d2_shape.py`, `e_bias.py`, `f_lognormal.py`,
  `g_seeds.py`. They implement the proposed operators in a few lines each and call the
  repository's metric functions; they are not the build.

## 8. Confidence

**Sure of.** Gneiting et al.'s Table 1 scenario, the calibration properties of the four
forecasters, the 0.0032 bound, Tables 4 and 5, read from the paper's text. Scheuerer and
Hamill's Eq. (5), their experimental settings and their findings on the energy and variogram
scores, read from the text. Jordan et al.'s t and log-normal formulas, and the t formula
checked against direct integration. The exact CRPS values of Eq. (2), confirmed by the
repository's `crps` on 49 152 cases to within 0.4%. The exact invariances of
`flow_dependence` and `member_shape` (measured to round-off). Equation (6), measured within
0.9%. The repository facts: operators see only members, the ladder does not compose
operators, `scale_spread` broadcasts a per-cell factor, `${...}` interpolation already works in
dataset configs, and issue 111 applies to any mean-preserving operator.

**Reasoning, not sourced.** Every transfer from the sources to a grid: cells as cases, the
operators' constructions, the torus distance in two dimensions, the σ profile (3), the
proposed parameters (σ = 0.05 and R = 4; ℓ = 3; λ = 0.1; the severities; 32² and 40 frames).
The derivations marked "my derivation": Eqs. (2), (4), (6), (7), the ensemble-mean errors,
the large-d energy-score limit, the slope-divided-by-a rule, the flat rank histogram of a
probabilistically calibrated forecaster. The claim that `member_shape` tends to the family as
M grows. Line counts.

**Not checked or uncertain.** Why Table 5's climatological CRPS (0.78) is three standard
errors below the exact value; a different random draw or rounding is plausible but not
established. The journal numbering of Jordan et al.'s appendix. The variogram score's
expected values on the Gneiting suite, not derived. Whether the card machinery handles three
non-ordinal ensemble probes without wording meant for `gaussian_impostor`
(`fmeval/analysis.py::probe_summary` treats probes generically, but the generated sentences
were not read). How a card should cite the correlated variant's member-override runs, which
share one dataset name; separate configs per override are the fallback. The positivity of
the circulant eigenvalues beyond the grids and lengths measured. Whether `wasserstein`
converges on the positive variant at every λ (measured only at λ = 0.1 and 1 on 6 frames).
