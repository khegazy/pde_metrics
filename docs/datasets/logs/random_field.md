# Log: periodic random fields with known statistics

This log records why the `random_field` dataset is in its current form, so that the next agent
who changes it does not undo a deliberate choice or repeat a dead end. Its public page is
`docs/datasets/random_field.md`. Entries are appended, never rewritten.

## What the dataset is for

The spectral, increment and tail metrics (`spectrum_l2`, `increment_w1`,
`increment_w1_by_separation`, `increment_flatness`, `energy_distance`, `tail_index`,
`tail_exceedance`) could show only that their numbers move under damage, because no dataset in
the repository had a known increment law. This dataset gives them answers known before the run:
Gaussian increments of exactly known variance at every separation, non-Gaussian fields with an
exact flatness at every separation, a heavy tail of known index, a known anisotropy, and a known
correlation in time. It is the reference the catalog's tail, phase, anisotropy and correlated-noise
clusters (G2, G3, G5, G10) and the degradations X1, X2, X4 and X6 were waiting for, and the
stationary null of spec 04, Option A3. It was specified in
`dataset_specs/09_random_fields_known_statistics.md` and built as step 10 of
`dataset_specs/BUILD_ORDER.md`.

## How it is treated

Nothing is stored. The reader `RandomField` (`fmeval/data/analytic.py`, registered as
`random_field`) is a `ClosedFormTrajectory` on the unit square, periodic on both axes, with the
fields `density`, `velocity` and `vorticity` and no pressure. Every frame filters unit white
noise from `derive_rng(seed, "random_field", frame, field)` by a transfer function built by
`band_transfer`, through `_apply_filter`. The reader options are `slopes` and `k_break` (the
spectrum), `k_min` and `k_max` (the band), `anisotropy`, `density_sigma` and `transform`
(`none`, `hermite2`, `exp`), `velocity_rms`, `multifractal_lambda`, `tau` and `tau_exponent`,
`spikes` (`{fraction, alpha, floor}`) and `seed`, plus the generic `candidate`. The one
configuration, `configs/dataset/random_field.yaml`, is spec 09's Gaussian null: 12 independent
frames on 256² cells with a shell spectrum of slope 5/3 below k = 32 and 3 above, on the band
4 ≤ |k| ≤ 120. The other families are reader overrides listed on the page.

## What part is evaluated

Decided by the step-10 agent, following Kareem's rule of 2026-11-26 (`docs/recipes/add-a-dataset.md`,
step 3). Every frame is an independent draw, so every frame is an independent sample and there
is no developed-flow window, transient or stride to choose; only the grid and the number of
frames matter. Nothing is stored, so the disk used is zero.

- **Grid: 256².** It is the analysis grid of every kinet run and the grid of the registered
  `tail_index` order k = 256, whose Gaussian value 0.0928 is the known answer. A coarser grid
  would cut the cost of the persistence metrics but change that answer and the calibration's
  room on the band.
- **Frames: 12.** The per-frame rank statistics then rest on 12 independent samples, as many as
  the 161-frame default window of `kinet_re5e4` holds (7 to 12, at an autocorrelation time of 13
  to 23 frames). At 256² one frame measures the Gaussian answers tightly: the flatness scatters
  by about 0.03 per frame and the Hill estimate by 0.0027, so 12 frames give standard errors of
  about 0.01 and 0.0008, well inside the tests' tolerances of 0.08 and 0.004. More frames would
  add cost faster than information.
- **Families run by default: the Gaussian null only.** The heavy-tailed families are compared as
  frame averages and need more independent frames: the Hermite and log-normal flatness and the
  multifractal flatness need about 48 frames for 8% to 12% (a per-frame spread of 10% to 22%),
  and the Pareto tail index about 24 frames for 7% (a per-frame spread of 7% to 10%). Their
  override lines on the page and in the configuration set those frame counts.
- **Measured cost per frame** on a Perlmutter login node, default ladder (91 variants), all
  three fields, from `fmeval.pipeline.run` on one frame: `mse` 1 s, of which 0.04 s is the
  metric and the rest the degradations; `increment_flatness` 10 s with its curves;
  `increment_w1_by_separation` 23 s; `energy_distance` 51 s; `wasserstein` (density, the
  positive field) 13 s; `persistence_distance` (density and vorticity) 142 s;
  `persistence_wasserstein` (density and vorticity) more than 30 min, after which the
  measurement was stopped. The other deterministic metrics measured (`h1_seminorm` 3 s,
  `h_minus_one` 1.6 s, `increment_w1` 4 s, and ten more below 1 s each) come to about 1.7 min
  per frame; `spectrum_l2`, `spectral_energy_flux`, `tail_index`, `tail_exceedance` and `vrmse`
  were not timed singly, and about 2 min per frame for all of them together is an estimate.
- **Projected full panel:** at 12 frames, about 25 min without the two persistence metrics,
  about 53 min with `persistence_distance`, and more than 6 h with `persistence_wasserstein`,
  which alone sets the time. Fewer frames would not fix that, and 12 is already the fewest that
  match the kinet window's independent samples; the remedy belongs to that metric (a coarser
  analysis grid for it, or a cheaper diagram distance), an open point below.

## Decisions and why

1. **A new subclass of `ClosedFormTrajectory`, not options on an existing reader** (decided in
   spec 09 by its agent and kept by the step-10 agent). Kareem's rule of 2026-11-26 asks for an
   option on an existing reader first. `synthetic_ensemble` declares an ensemble, so a
   deterministic metric would score its member mean, not the field. `advecting_blobs` already
   draws a static Gaussian background, but it has no frame-to-frame draw, no time correlation,
   no transforms and a pressure field the random fields must not have; giving it all of these
   would have made every random-field configuration a population of zero-amplitude features.
   To reverse, move the options onto `AdvectingBlobs` and its `background`.
2. **The draw is the existing `_apply_filter` on seeded white noise, and the spectrum code is
   shared with `advecting_blobs`** (the draw decided by the coordinating session in
   `BUILD_ORDER.md`, "one random-field draw"; the sharing by the step-10 agent). The spectrum
   and the normalisation that `AdvectingBlobs` built inline for its background are now the
   module function `band_transfer`, which both readers call; the per-axis stretch for the
   anisotropic family was added as an optional argument of `wavenumber_magnitude`
   (`fmeval/wavenumbers.py`), so the repository keeps one definition of |k|. The spectral
   Biot–Savart inversion `AdvectingBlobs` used is now the module function `biot_savart`, which
   both readers call. Both moves keep `advecting_blobs` bitwise unchanged: the arithmetic is the
   same operations in the same order, and its tests, which pin the defaults bit for bit, pass.
   No `gaussian_random_field` function was written. To reverse, inline the two functions back
   into `AdvectingBlobs`.
3. **One spectrum serves density and velocity** (the step-10 agent; spec 09 left it open).
   Spec 09's intermittent configuration wanted a Matérn density and a power-law velocity. The
   flatness targets of Eqs. (8), (9) and (11) of spec 09 are exact for any spectrum, so a second
   spectrum option would add code and no known answer. With the Matérn spectrum for both, the
   multifractal velocity's exact flatness still varies with separation (4.9 at one cell to 3.8
   at 64 on 256 × 192, measured from Eq. 11), so the intermittent family loses nothing it was
   built to test. To reverse, add a velocity `slopes` and `k_break` and pass them to a second
   `band_transfer` call.
4. **The spectrum is one smoothly broken power law** (the step-10 agent). Spec 09 proposed a
   power law, a sharply broken power law and a Matérn form as three options. The per-mode
   variance `k^-(beta_1 + 1) (1 + k²/k_b²)^(-(beta_2 - beta_1)/2)` is all three: one slope is a
   power law, two slopes a power law broken at k_b, and slopes (−1, 2ν + 1) exactly the Matérn
   density of Porcu et al. (2023), Eq. 23. The break is smooth rather than sharp, which changes
   no test, since every target is computed from the reader's own transfer function. To reverse,
   add a sharp-break branch to `band_transfer`.
5. **The multifractal construction applies to the velocity and vorticity only, and its scale
   is the box** (the step-10 agent). The intermittent family is a log-normal density beside a
   multifractal velocity, as spec 09 proposed, so the density keeps its own transform; the
   vorticity, being a scalar, carries the scalar target of Eq. (11). Spec 09's
   `multifractal_scale` option was dropped, its default (the box) being the only value it used.
   A time-correlated multifractal field is refused: the recursion of Eq. (7) would mix
   independent chaos fields, whose law Eq. (11) does not describe.
6. **Pareto spikes are a reader option, not the X4 `pareto_spikes` degradation** (the step-10
   agent). Spec 09 assigned them to X4, which is not built; building a degradation bundle with a
   card and calibration was outside this step, and the reader option is about ten lines through
   the candidate mechanism or the reader itself. The spikes are positive only, so the density
   stays positive; each spike still makes increments of both signs. **When X4 is built, delete
   the reader option** so the spike law has one definition. The fraction used is 2/√M, the
   catalog's G2 margin recorded in `BUILD_ORDER.md`, step 10 (spec 09 measured the estimate
   failing at 1/(2√M)), and the floor must exceed the largest Gaussian increment; the test
   checks both. The reader does not refuse a smaller fraction, since that is a condition of the
   Hill estimator, not of the field.
7. **Every frame is an Ornstein–Uhlenbeck step, and `tau = 0` is the same recursion with zero
   correlation** (spec 09's design, the step-10 agent's implementation). With `tau = 0` a frame
   is drawn directly at its index; with `tau > 0` the reader steps forward from the last frame
   read and restarts from frame 0 when an earlier frame is asked for. `tau = inf` holds the
   first frame, which is the persistence candidate.
8. **One configuration, the other families as overrides** (the step-10 agent). Spec 09
   proposed four configurations. The families differ only in reader options, and a
   configuration states a key only to change it, so each would have been a list of overrides.
   A family that is registered as evidence needs its own configuration, because the claim label
   is keyed by configuration name; add it then.
9. **Not registered as evidence, and `docs/decisions.md` not edited** (the coordinating session,
   by instruction for this step). `BUILD_ORDER.md`, "The task", says every dataset built there
   is admitted with a claim label (Kareem, 2026-11-26), and issue 044 (the run seed reaching
   the reader) should be settled first.

## Log entries

### 2026-11-26: built (step 10), by the step-10 agent

- Code: `fmeval/data/analytic.py` (`band_transfer`, `biot_savart`, `RandomField`;
  `AdvectingBlobs` now calls the two functions), `fmeval/wavenumbers.py` (the `stretch`
  argument of `wavenumber_magnitude`), `tests/analytic_fields.py` (`gaussian_mean_square`, the
  mean and spread of a Gaussian field's mean square), `tests/test_analytic_datasets.py` (nine
  tests, thirteen cases), `configs/dataset/random_field.yaml`, `docs/datasets/random_field.md`
  and its row in `docs/datasets/README.md`.
- Verified through `fmeval.pipeline.run`: the spectrum shapes against independent formulas; the
  velocity solenoidal and its curl equal to the vorticity to 1e-12; the increment variance along
  each axis (isotropic, and anisotropic with a = 2) within four exact standard errors; flatness
  3 on all three fields within 0.08; `increment_w1` between two Gaussian fields within 6%; the
  Hill population value 0.0928 within 0.004; the Pareto tail index at α = 2 and 4 within 7%;
  the Hermite, log-normal and multifractal flatness at every separation within 8%, 12% and 8%
  of 48-frame means; the Ornstein–Uhlenbeck lag correlation within four standard errors per
  frame; flatness 3 on every level of the default ladder's twelve linear operators. The
  tolerances come from measurements over several seeds, stated in each docstring.
- Evaluated part chosen (12 frames on 256², the Gaussian null by default) from per-frame costs
  measured with `fmeval.pipeline.run` on one frame of the default ladder; section "What part is
  evaluated".
- Not verified: the energy distance of spec 09 Eq. (6) and the frequency bias of
  `tail_exceedance`, which no test asserts; the calibration on the 256² configuration beyond
  three smoke runs (default ladder with 33 frames before the frame count was set to 12, 6 min for
  four metrics; the intermittent override on the quick ladder, 38 s; a seed-and-amplitude
  candidate, 4 s); the dynamics figures, which were not drawn.

## Open points

1. A configuration per family, and the `evidence_datasets` entries, once issue 044 is decided.
2. Spec 09's Eq. (6) (`energy_distance`), the `tail_exceedance` bias with spikes and the
   expected `spectrum_l2` floor between two draws are derived but not asserted.
3. The Pareto option should move to the X4 `pareto_spikes` degradation when that is built.
4. The dynamics figures (`python -m fmeval.cards dynamics random_field`) are not drawn.
5. `persistence_wasserstein` costs more than 30 min per 256² frame on the default ladder, so the
   full panel takes more than 6 h on 12 frames; whether to run it on a coarser analysis grid
   here is the team's call. Its exact per-frame cost was not measured to the end.
