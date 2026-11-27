# Log: synthetic exchangeable ensemble

This log records why the `synthetic_ensemble` dataset is in its current form, so that the next
agent who changes it does not undo a deliberate choice. Its public page is
`docs/datasets/synthetic_ensemble.md`. Entries are appended, never rewritten.

## The configuration before step 11

The `synthetic_ensemble` configuration (`configs/dataset/synthetic_ensemble.yaml`, 16 members,
12 frames, 64² cells, density only) existed before this log. Its history is recorded in
`issues/003-ensemble-data.md`, on the dataset page, and in the git log of
`fmeval/data/synthetic_ensemble.py` and its config. It is not reconstructed here. The step-11
work below left its output bitwise unchanged.

## What the extensions are for

The eight ensemble metrics (`crps`, `crps_skill_score`, `energy_score`, `ensemble_mean_rmse`,
`rank_histogram`, `rank_histogram_chi2`, `spread_skill`, `variogram_score`) had one experiment:
an ensemble with one noise level everywhere and independent noise in every cell. That
experiment cannot show a calibrated but useless forecaster, a spread that varies between
regions, a wrong spatial correlation, a wrong centre, members of the wrong shape, or a positive
density. The extensions add each of these with an answer known in advance. They were specified
in `dataset_specs/08_synthetic_ensemble_extensions.md` and built as step 11 of
`dataset_specs/BUILD_ORDER.md`.

## How it is treated

Nothing is stored. The reader `SyntheticEnsembleTrajectory` (`fmeval/data/synthetic_ensemble.py`)
computes every frame from its seed. Per field, frame and cell, the truth is
T(b + σ(x) η₀) and member i is T(b + δ σ(x) + σ(x) ηᵢ). Every axis is periodic with a spacing
of one cell. The options, all off by default, are:

- `base` sets b: `two_scale` (the original pattern), `case_means` (an independent N(0, 1) value
  per cell, frame and field, the case means of Gneiting, Balabdaoui and Raftery 2007, Table 1),
  or `zero`.
- `sigma_ratio` R makes the noise level vary along the first axis, σ(x) = σ R^w with
  w = (1 + sin 2πi/nₓ)/2 (spec 08, Eq. 3), for truth and members alike.
- `noise_length` and `noise_covariance` give the noise an exponential or rational covariance in
  the torus distance between cells (Scheuerer and Hamill 2015, Eq. 5 and Sect. 3c).
- `member_noise_length` and `member_noise_covariance` give the members alone a different
  covariance.
- `member_offset` δ moves the members' centre, in units of σ(x).
- `log_amplitude` λ applies T(v) = exp(λv) to truth and members, which gives a positive density.

Three operators act on the member stack: `gneiting_forecaster`, `flow_dependence` and
`member_shape` (`degradations/`). Their ladders are `configs/degradation/gneiting_forecasters.yaml`
and four entries in `configs/degradation/ensemble_miscalibration.yaml`.

## What part is evaluated

The reader stores nothing, so there is no disk cost; the frames, members and grid set the time.
Every frame is an independent draw from a fresh seed, so each frame is an independent sample of
every per-frame statistic, and no frame is redundant with another. This section was decided by
the agent of step 11 on 2026-11-26 under Kareem's rule of the same day (recipe step 3); a
person may override it.

**Measured cost** (login node, no Slurm job, results in
`/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets`). Per frame and severity level,
`crps` takes 0.0009 s and `variogram_score` 1.67 s at 64² and 0.12 s at 32²; the variogram
score's cost grows with the square of the cell count. The whole metric registry on one frame
of `ensemble_miscalibration` (30 severity levels) took 42 s, of which `variogram_score` took
40.7 s (97%) and `persistence_wasserstein`, the next most expensive, 0.6 s. The full panel over
the default 12 frames is therefore about 8.4 minutes. Before the four step-11 entries were
added the ladder had 14 levels, and the same panel took about 19.6 s per frame, or 3.9
minutes. On the Gneiting ladder (5 levels) the registry took 9.5 s per frame, about 2 minutes
for 12 frames; on the correlated variant at 32² it took 4.5 s per frame, about 3 minutes for 40
frames.

**What each experiment needs.**

- **Default (`two_scale`, 16 members, 12 frames, 64²).** Kept unchanged, because the four
  ensemble cards cite numbers from it. Twelve independent frames give every per-frame rank
  correlation twelve samples, and 16 members keep the rank histogram's sampling floor below
  its signal (the config's own comment).
- **Gneiting forecasters (`base: case_means`, `sigma: 1`).** The CRPS of one 64² frame has a
  standard error of about 0.009 (measured from the test's 12 frames), and the two closest
  forecasters, Hamill's and the unfocused, differ by 0.0175. Twelve frames bring the standard
  error to about 0.0025, so the four values are separated by at least seven standard errors;
  four frames would leave only four. The default frames and grid are therefore right here.
- **Varying spread (`sigma: 0.05`, `sigma_ratio: 4`).** The binned spread–error slope over 20
  bins of 12 frames at 64² (2 458 cells per bin) is measured to within 1% of its predicted
  value. Fewer frames were not measured.
- **Correlated noise (`base: zero`, `sigma: 1`, `noise_length: 3`).** 32² rather than 64²,
  because the variogram score is fourteen times cheaper there. Independent member noise is
  detected in 12 frames (paired t = 7.0), but the smaller effects of spec 08, Sect. 3.3 (a
  member length of 2 or 4.5, or the rational model, with paired t of 4 to 7 in 40 frames) need
  40 frames.
- **Wrong centre (`member_offset: 1`) and positive density (`log_amplitude: 0.1`).** The default
  frames and grid; spec 08 measured Eq. 6 within 0.9% and Eq. 7 at that size.

**Named experiments run by default.** None. Only the default configuration runs by default; the
spec-08 variants run by the overrides listed in `configs/dataset/synthetic_ensemble.yaml`,
because none has a dataset config yet (open points).

**Proposed, not applied.** The default grid could drop to 32², which would cut the full panel
from about 8.4 minutes to about 1 minute (4.5 s per frame, measured at 32²), since nearly all
of it is the variogram score. The cost is
that the per-frame standard error of the per-cell scores would double, and every number on the
four ensemble cards would change, so it needs Kareem's decision. A smaller step that changes no
existing number is to trim the four step-11 entries in `ensemble_miscalibration.yaml` to three
severities each, which would save about 6 s of the 42 s per frame.

## Decisions and why

1. **Every change to the truth or to the members' relation with it is a reader option, not an
   operator** (decided in spec 08 by its agent, following Kareem's rule of 2026-11-26 that
   analytic datasets are options on existing readers). An operator receives only the members,
   through `apply_severity_level` in `fmeval/ladder.py`, and never sees the truth, b or σ(x).
   So the case means, the noise profile, the truth's correlation and the positive transform
   must be set where the truth is drawn. A wrong member correlation was also tried as an
   operator in spec 08, by re-colouring each member's departure from the member mean. That made
   the members share a component and therefore dependent, and the variogram score then fell by
   0.23%, the wrong direction for a proper score, so the members' correlation became a reader
   option too. The member offset is a reader option because the ladder applies one operator per
   entry and cannot compose `bias` with `spread_deflate`. To reverse any of these, an operator
   would need access to the truth, which the ladder does not give.
2. **The correlated noise is drawn with `_apply_filter`, not with the impostor's draw**
   (decided in spec 08 by its agent and confirmed in `BUILD_ORDER.md`, "one random-field
   draw"). `_apply_filter` (`degradations/_shared/filters.py`) applied to seeded white noise
   with the square root of the covariance's spectrum gives an exactly Gaussian field with
   exactly that covariance on the grid. `gaussian_impostor` keeps a given field's Fourier
   amplitudes and randomises its phases, which is Gaussian only asymptotically, and every known
   answer here needs an exactly Gaussian field. Its draw also lives inside the impostor's own
   module. The reader imports `_apply_filter` from `degradations/`, as `fmeval/ladder.py`
   already does, and uses `fmeval.wavenumbers.wavenumber_magnitude` for the torus distance. The
   reader refuses a covariance whose smallest eigenvalue on the grid is not positive. The
   alternative, an inline `ifftn(fftn(w) * A)`, would duplicate `_apply_filter`.
3. **The three operators and what they declare** (designed in spec 08 by its agent; the build
   followed it, the agent of step 11).
   - `gneiting_forecaster` turns the ideal forecaster's members into the climatological,
     unfocused or Hamill's forecaster. It is a probe (`ordinal=False`), stochastic, with
     `zero_is_identity=False` and no `preserves`, because it changes the member mean. Its
     constants presuppose `base: case_means` and `sigma: 1`.
   - `flow_dependence` sets each cell's spread to k ŝ^a, a = 1 − s (`damp`) or 1 + s
     (`amplify`), with k keeping the frame's mean variance (spec 08, Eq. 4). It reuses
     `scale_spread`, whose signature was extended to take a per-cell factor array. It declares
     `preserves: [ensemble_mean]`.
   - `member_shape` maps each cell's members onto a Student-t or a two-piece normal and
     re-standardises them, so every cell's mean, variance and member order are kept. It
     declares `preserves: [ensemble_mean]`, the only word the contract test can measure on a
     member stack; the kept variance and order are tested separately in
     `tests/test_degradation_contract.py`. Adding a word for the variance would be about five
     lines in `degradations/registry.py` and was left optional.
4. **The Gneiting forecasters have their own ladder file**, `gneiting_forecasters.yaml` (the
   agent of step 11, within Kareem's instruction to take whichever is the least configuration).
   They mean something only on the case-means reader. Placed in `ensemble_miscalibration.yaml`
   they would have to be disabled there, and a run of them would then need about six
   command-line overrides. To reverse it, move the three entries into
   `ensemble_miscalibration.yaml` with `enabled: false`.
5. **The four new entries in `ensemble_miscalibration.yaml` are enabled**
   (`flow_dependence_damp`, `flow_dependence_amplify`, `heavy_tails`, `skew`; the agent of
   step 11, Kareem having left `enabled` to the builder). They are miscalibration axes on any
   ensemble, like `spread_inflate` and `spread_deflate`, and they trigger issue 111 exactly as
   those already do. The consequence is that the four ensemble cards that cite this ladder will
   gain these four axes the next time their evidence is regenerated. To reverse it, set
   `enabled: false` on the four entries.
6. **The Student-t CRPS test uses independent Student-t members, not `member_shape`** (the agent
   of step 11). The closed form (Jordan, Krüger and Lerch 2019, App. A.2.5) is the expected CRPS
   of independent draws from the family, and the fair estimator is unbiased only for
   independent members. `member_shape` re-standardises 16 members, which bounds their tails, so
   it approaches the closed form only as the ensemble grows; at 200 members it was still short
   (+0.020 against +0.027 at ν = 2.5, measured). The test therefore pins the closed form
   through the repository's `crps`, and the card states that the finite ensemble does not reach
   it.
7. **Statistical tolerances are four standard errors measured from the frames**, each frame
   being an independent draw (the agent of step 11). The seeds are fixed, so the tests are
   deterministic.

## Log entries

### 2026-11-26: step 11 built (agent)

- Reader: the eight options above in `fmeval/data/synthetic_ensemble.py`, validated at
  construction and recorded in `meta`. Verified bitwise identical to the HEAD reader with
  default options on 64² with 16 members, on 16×8 with two fields and seed 3, and on an 8×6×4
  grid, by comparing `tobytes()` of every array.
- Operators: the three bundles above, each with a card that `python -m fmeval.cards check`
  passes. Exemplar panels were not generated, because no test requires them.
- Configs: `configs/degradation/gneiting_forecasters.yaml` and the four entries in
  `ensemble_miscalibration.yaml`. No dataset config was added and nothing was registered in
  `configs/cards/default.yaml`.
- Tests in `tests/test_synthetic_ensemble.py`: the four Gneiting CRPS values against the exact
  0.5642, 0.6144, 0.6319 and 0.7979 within four standard errors (about 0.0025); `spread_skill`
  and `ensemble_mean_rmse` unchanged to 1e-12 under `flow_dependence` and `member_shape`; the
  binned spread–error slope times a equal to the calibrated slope (about 0.87) within 1%; the
  variogram score rising under independent member noise (paired t = 7.0 over 12 frames of 32²)
  while `crps` and `ensemble_mean_rmse` stay within |t| < 3; the Student-t closed form at ν = 5
  and 2.5; and reader checks of the noise profile, the covariance, the ranks under
  `log_amplitude` and the member offset. In `tests/test_degradation_contract.py`: the three
  operators in `LADDERS`, each Gneiting kind's per-cell distribution, and `member_shape`
  keeping mean, variance and order.
- Smoke runs, written to `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets`: the
  Gneiting ladder on `base=case_means, sigma=1` gave CRPS 0.5668, 0.6174, 0.6333 and 0.8031
  for the ideal, Hamill's, unfocused and climatological forecasters; the four new
  miscalibration entries on `sigma=0.05, sigma_ratio=4` moved `crps` and left `spread_skill`
  (0.99160) and `ensemble_mean_rmse` (0.12898) unchanged.
- Issue 111 is triggered by both mean-preserving operators: on the second smoke run their
  `field_change_max` was about 1e-32 and their `damage_per_change` 1.2e29 to 1.2e30. It was
  not fixed here.
- Not verified: spec 08's Eq. 6 (deflation under a member offset) and Eq. 7 (the log-normal
  CRPS), and the rational covariance beyond its positive-definiteness check.

### 2026-11-26: what part is evaluated (agent)

- Decided and recorded which part of the dataset is evaluated, in the new section "What part
  is evaluated" above, and as comments in `configs/dataset/synthetic_ensemble.yaml`,
  `configs/degradation/ensemble_miscalibration.yaml` and
  `configs/degradation/gneiting_forecasters.yaml`. No default was changed.
- Measured with `python evaluate.py dataset=synthetic_ensemble` on the login node, with
  `dataset.time.max_frames` of 1 or 3, `degradation.only=[mean_field]` for the per-metric cost
  at 64² and 32², and the whole registry on `ensemble_miscalibration` (64²), on the correlated
  variant (32²) and on `gneiting_forecasters`. Results are in
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets` (`panel`, `panel32`,
  `panelg` and the `crps_*` and `variogram_score_*` folders). The timings are from the rows'
  `wall_time_s` and the run's own summary line.
- Not verified: the timings on a compute node, and how few frames the binned spread–error
  slope tolerates.

### 2026-11-27: issue 044 closed with no change (step-32 agent)

- **Decision.** Kareem, 2026-11-27: "The reader does not need to know the seed used to generate
  the data" (decision 14 of `dataset_specs/BUILD_ORDER.md`). The reader keeps its own `seed`
  option, which `run_meta.json` records under `reader_options`; the run seed reaches the
  degradation operators only. Another draw of the null is another reader seed
  (`+dataset.reader.seed=<n>`).
- **Done.** Issue 044 deleted with its row in `issues/README.md`, and every reference that said
  something waited on it rewritten to state the decision. No code, configuration or card number
  changed.

## Open points

- **The published climatological CRPS.** Gneiting, Balabdaoui and Raftery (2007), Table 5,
  report 0.78 for the climatological forecaster, about three standard errors below the exact
  0.7979 (spec 08, Sect. 3.1). The cause is not established; a different random draw or
  rounding is plausible. The tests use the exact value.
- **Dataset configs and evidence.** The five configurations of spec 08, Sect. 6.1, and their
  `evidence_datasets` entries are not made.
- **Exemplar panels** of the three bundles are not generated.
- **Untested known answers:** Eq. 6 and Eq. 7 of spec 08.
- **The binned spread–error figure** needs a separate change to `spread_skill`.
- **Issue 111** misreads the profile rows of `flow_dependence` and `member_shape` until it is
  fixed.
