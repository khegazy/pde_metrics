# Catalog of the experiments, benchmarks and degradations the metrics still need

Written 2026-11-04 on branch `update_metric_eval_principles`. A survey, not a plan: nothing
here is built, and no file outside this one was changed. A first draft was checked by an
adversarial reviewer on the same day; its findings, several of which overturned the draft's
own additions, are folded in below and the standalone critique was deleted. Where a claim
rests on the reviewer's measurement rather than on a repository file, it says so.

## At a glance

This page is for a reader who wants the picture in five minutes. Everything in it is
expanded, with sources and caveats, in Sections 1 to 3 below; the reading map at the end of
this part says where.

**The one-paragraph version.** The metric-building agents asked for about a hundred
experiments, which reduce to 24 distinct needs. Most of what they asked for falls into four
gaps in the repository: there is no physical ensemble or second realisation of any flow,
nothing acts on time, no dataset stores a pressure with shocks in two dimensions, and no
dataset is statistically stationary with an inertial range. One solver job closes the first
two gaps for 32 of the 39 metrics, and two cheap degradations (correlated noise and graded
phase randomisation) and one closed-form generator would give nearly every metric a known
answer. Several wanted datasets are already on disk without a reader.

### The ten things to build, in order

| # | Build | What it is | Metrics it reaches | Cost | Blocked on |
|---|---|---|---|---|---|
| 1 | **Solver ensemble job** (B1) | 17 perturbed kinet runs from each of 3 start states, every run the truth in turn, stored every 10th step | 32 of 39: the 8 ensemble metrics directly, every other metric through its damage anchor | 51 runs of 5 000 steps at 256²; about 14 GB | A wall-clock measurement of one run |
| 2 | **Readers for data on disk** (B7) | The 512² reference run, three independent isotropic realisations, the old Reynolds-ladder members, Well sets with pressure, kinet Sod and obstacle runs | Varies; the 512² run gives the 8 pointwise norms a real refinement comparison today | A reader each, no simulation | Issue 046 for the non-square Sod runs; boundary mapping for the Well |
| 3 | **Correlated noise** (X1) | Additive noise with a chosen correlation length, a spatially smooth error instead of white noise | 32 | One bundle | Nothing |
| 4 | **Graded phase randomisation** (X2) | Rotate every Fourier phase by a random angle up to sπ; s = 1 is the impostor | 25 (all but shock and ensemble) | One bundle | Fixing the impostor's per-channel phase draw first |
| 5 | **Feature-population generator** (B5) | A smooth random background plus listed vortices, fronts and bumps of known position, amplitude and count | Every family except ensemble, each with an answer known before the run | A closed-form reader, seconds per run | A decision on whether it counts as evidence |
| 6 | **Temporal ladder** (X3) | Time lag, temporal smoothing, and the same spatial damage on every frame of a window | 3 single-field metrics and 8 blocked ideas now; every metric along time later | Three operators | A harness change: a metric receives a window of frames |
| 7 | **Synthetic-ensemble family** (B3) | Four forecasters with published scores, varying spread, correlated noise, positive density | The 8 ensemble metrics, with closed-form answers | Seconds per run | Nothing |
| 8 | **Forced 2D compressible turbulence** (B2) | Stationary, forced, with drag, turbulent Mach about 0.3 to 0.5, pressure stored | 8 spectral and tail metrics, 6 shock metrics, the Helmholtz split | A new simulation | Whether kinet supports forcing and a drag term |
| 9 | **Tail family** (X4) | Pareto spikes with a known exponent; tail-only compression | 6 distributional and tail metrics, the peaks-over-threshold idea | Two bundles | Nothing |
| 10 | **2D shock dataset** (B4) | Sedov blast wave, 2D Riemann problems, then shocklet turbulence | 6 shock metrics, persistence, compressible flux | Euler solver runs | A reader and per-axis boundaries |

The remaining builds (feature injection and simplification, anisotropic blur, the Helmholtz
and admissibility families, rotation and boost probes, draws per severity, Sod at a shifted
time, transport fixtures) are in Sections 3.1 and 3.2.

### Every need on one page

Reach counts metrics out of 39. "Asked by" gives the strongest evidence that an agent wanted
it. Cluster IDs are the ones used in Section 2.

| ID | Need | One line | Asked by | Reach | Cost |
|---|---|---|---|---|---|
| D1 | Physical ensemble and independent realisations | N + 1 perturbed solver runs, each the truth in turn; plus unrelated realisations | 8 ensemble cards; issue 004; judgement 001 | 32 | Solver runs |
| D2 | Many initial conditions, scored step by step | Reference trajectories from many starts; candidates from analytic formulas or degraded solver runs; each metric averaged over starts at every step | 13 cards, the most-cited want | 13 + time-dependent ideas | Readers; minute-scale kinet runs |
| D3 | Two-dimensional shock dataset | Sedov, 2D Riemann, shocklet turbulence | 6 shock cards; issue 002 | 7 + ideas | Euler solver runs |
| D4 | Stationary forced turbulence with an inertial range | Forced 2D compressible run with drag, or 3D cutouts | 8 spectral and tail cards | 14 + ideas | New simulation or a database reader |
| D5 | Grid refinement against a known solution | Order of accuracy from 64² to 512² | 8 pointwise cards; issue 126 | 8 | On disk in part (512² run) |
| D6 | Synthetic-ensemble extensions | Forecaster suite, varying spread, correlated noise, positive density | 6 ensemble cards | 9 | Seconds |
| D7 | Known vortex population | Closed-form field with listed vortices | 2 persistence cards; 4 ideas | 2 + ideas | Seconds; merged into the generator |
| D8 | Shock fronts with known geometric errors; Sod at a shifted time | Closed-form fronts displaced, resized, rotated; exact Sod at t against t + dt | 6 shock cards | 6 | Seconds; a paired-time reader for Sod |
| D9 | Known-answer transport pairs; background sweep | Exact Wasserstein pairs; blob height swept over decades | 2 transport cards; 3 ideas | 2 + ideas | Twenty lines; no new code for the sweep |
| G1 | Temporal ladder and windowed budgets | Lag, temporal smoothing, consistent damage over a window; energy and enstrophy budgets over about 100 steps | 3 single-field cards; 12 issues | 3 + 8 ideas | Three operators and a harness change |
| G2 | Tail axes with a known answer | Pareto spikes (target 1/α); tail-only compression | 6 cards | 6 | Two bundles |
| G3 | Graded phase randomisation | Impostor as an ordinal axis | 2 cards; serves all spectral and phase statistics | 25 | One bundle, after fixing the impostor |
| G4 | Feature add, remove, simplify | Spurious wells; persistence simplification | 2 persistence cards | 3 | Two bundles, one needs a new routine |
| G5 | Anisotropic blur | Different widths along x and y | 3 issues | Ideas only | One bundle |
| G6 | Helmholtz family | Scale the dilatational part; solenoidal projection option | Issues 024, 057 | 3 + ideas | One bundle plus one option |
| G7 | Admissibility family | Negative cells, non-finite cells, positive-preserving noise, bias on Sod | Issues 070, 139 | Positive-field and shock metrics | Two or three small bundles |
| G8 | Rotation, boost, invariance probes | 90° rotation, Galilean boost, invariance audit, gradient norm | Issues 013 to 015 | 39 | Two operators and renderers |
| G9 | Draws per severity | Several random draws per level, a signal-to-noise ratio per metric | Issues 097, 106 | 39 | A ladder option; cost times the draws |
| G10 | Spatially structured errors | Correlated noise, regional blur, one-feature displacement, patterned bias | Degradation cards | 32 | One bundle for the noise |
| H1 | Window of frames to a metric | Multi-frame input and series-level pooling | Issues 094, 095 | Prerequisite for G1 | Harness change |
| H2 | Several fields to one metric; positive-field declaration | Pressure beside velocity; refuse a gauge pressure | Issues 096, 101 | Shock and flux metrics | Harness change plus a pressure dataset |
| H3 | Evidence plumbing | Curve companions on forecasts; one analysis grid for the Reynolds ladder; member-stack damage | 24 cards (grid), 6 (curves), 7 (issue 111) | Many | Configuration |
| H4 | Statistics and provenance | Block length, autocorrelation time, block bootstrap, cost and seed handling | Issues 042, 044, 114, 125, 132 | 39 | Harness changes |

### Fixes that cost a configuration change or a unit test

- Run the `kinet_re1e6` comparison every card cites at `analysis_grid.resolution=256`, so
  the two Reynolds numbers are compared on one grid (24 cards carry the confound).
- Tabulate the curve companions on `forecast_re5e4` (6 cards read only the registered
  number).
- Pin the three single-field bundles against `taylor_green_2d`, where dE/dt = −2νΩ holds
  exactly.
- Fix the impostor's per-channel phase draw, which puts about a quarter of a solenoidal
  velocity's energy into a divergent part; open an issue first.
- Pass the run seed to the synthetic-ensemble reader (issue 044).

### Decisions only a person can take

1. Whether kinet supports forcing and a large-scale drag (B2) and a manufactured source term (D5).
2. Whether the Sod time offset is a trajectory-aware operator or a paired reader (B6).
3. Whether a deliberately non-finite prediction may pass the frame check (X8).
4. Which vortex profile the generator uses, and its citation (B5).
5. Whether a closed-form dataset such as the generator is admitted as evidence, as Sod was.
6. Compute for `persistence_wasserstein` on the 256² ladders (issue 144).
7. Whether to generate a Re ≈ 500 reference or amend the protocol (issue 001).

### Reading map

| If you want | Read |
|---|---|
| What already exists, and what is on disk without a reader | Section 1 |
| Every need with its sources, the metrics it serves and its cost | Section 2.1 (data), 2.2 (degradations), 2.3 (harness) |
| Where each proposal, issue and note landed | Section 2.4 |
| Specifications for the recommended builds | Section 3.1 (data), 3.2 (degradations), 3.3 (tests) |
| Which needs serve which metric family | Section 3.4 |
| What was verified, what was measured by the reviewer, and what is still unchecked | Confidence |

## Summary (in prose)

Previous metric-building agents logged the experiments their metrics lack in six places:
the 25 `proposals/EXP-*.md` files and the "How it could be tested" sections of the 27
`proposals/MTR-*.md` files; the "How its field reports it", "Limitations" and "Results"
sections of the 39 metric cards; the per-metric `research_notes.md` and `code_notes.md`; the
`judgements/`; the `issues/`; and the degradation cards' "Limitations". The plan documents at
the repository root and the idea pages under `docs/ideas/` repeat the same wants in planning
language. Two sub-agents swept the cards and the notes file by file, and the reviewer swept
the sources they missed; every count of "cards naming it" is a count over card text.

The wants are heavily duplicated. Roughly a hundred distinct want statements collapse to
**24 clusters**: 9 datasets or benchmark problems, 10 degradation families, and 4 harness or
protocol capabilities, plus a short list of regime data with no proposal. Section 2 is the
deduplicated catalog with every source mapped onto its cluster. Section 3 recommends what to
build, ordered by how many metrics each item serves per unit of cost, with a specification
for each.

The headline recommendations:

1. **One production job of solver runs** on the `kinet_re5e4` configuration: 17 perturbed
   runs from each of several start states, none unperturbed, each run in turn the truth;
   stored every 10th solver step over a short horizon. It supplies the physical ensemble (8
   ensemble metrics), the reference set of many initial conditions (13 pairwise metrics and the time-dependent ideas),
   windowed budget residuals (3 single-field metrics, the weak residual, the temporal ladder),
   and the exchangeable realisations the damage anchor has wanted since judgement 001. It
   reaches 32 of the 39 metrics; the 6 shock metrics need a stored pressure, which this
   isothermal flow does not carry, and `persistence_wasserstein` is held back from turbulence
   runs for cost (issue 144).
2. **Readers for data already on disk.** A readable 512² run of the reference shear layer
   sits beside `kinet_re5e4` with the same deterministic initial condition and the same
   physical times, so a two-level solver refinement comparison of the reference exists today
   (issue 126's missing condition). Three independent realisations of a random-mode isotropic
   flow, a supersonic obstacle flow, two lattice-Boltzmann Sod runs, an acoustic dipole and
   several Well datasets that store pressure are also on disk without readers.
3. **A forced, statistically stationary, two-dimensional compressible turbulence run** with
   a large-scale drag, at a turbulent Mach number of about 0.3 to 0.5. It is the one dataset
   that gives the spectral, increment and tail metrics an inertial range and a stationary
   base period, and the shock metrics their many small shocklets, the north-star case of
   `CLAUDE.md`.
4. **Three degradations that reach most metrics at once:** spatially correlated noise (the
   additive-noise card itself calls white noise "the least realistic failure in the default
   set"); graded phase randomisation, which turns the impostor canary into an ordinal axis,
   provided the per-channel phase draw it would inherit is fixed first; and a temporal
   ladder, which unblocks eight screened-out ideas and needs one harness change.
5. **One closed-form generator of fields with a known feature population** (a smooth random
   background plus a listed set of vortices, fronts and bumps with known positions,
   amplitudes, widths and counts), replacing three separate fixtures the proposals ask for
   and giving every family an answer known before the run.

Everything added beyond what an agent logged is marked **(mine)**.

## 1. What exists today, so the gaps are legible

### 1.1 Experiments the repository runs

From `AGENTS.md` §1, "How every metric is evaluated": the degradation ladder on `kinet_re5e4`
(`configs/degradation/default.yaml`, 23 ladder entries), the miscalibration ladder on
`synthetic_ensemble` (`spread_inflate`, `spread_deflate`, `bias`, the anchor), `sod_shock_tube`
as an analytic check, the real forecasts of `forecast_re5e4` at ten prediction steps from two
starts in three runs, and the Reynolds ladder (`kinet_re5e4` and `kinet_re1e6` on one 128²
grid). `advecting_blobs` and `taylor_green_2d` are fixtures, never evidence
(`docs/decisions.md`).

### 1.2 Degradations (25 operators, `python -m degradations`)

Ensemble: `spread_deflate`, `spread_inflate`. Geometric: `translate`, `translate_subpixel`,
`random_large_translation` (probe). Pointwise: `bias`, `gain`. Resolution: `coarsen`,
`coarsen_bandlimited`, `subsample`. Smoothing: `gaussian_blur`, `box_blur`, `disk_blur`,
`epanechnikov_blur`, `median_blur`, `mean_field` (probe). Spectral: `lowpass_ideal`,
`lowpass_butterworth`, `highpass_ideal`, `highpass_butterworth`, `band_attenuate`. Stochastic:
`additive_noise`, `multiplicative_noise`, `gaussian_impostor` (probe). Plus `identity`.

Every smoothing, spectral and noise operator is isotropic; only the translations have a
direction. Every operator acts on one snapshot, and (except the ensemble pair) on one field
at a time; none is `whole_frame`. None changes anisotropy of a statistic, phase coherence by a
graded amount, the tail of a distribution alone, the vortex or shock population, the
solenoidal-to-dilatational partition, timing, admissibility, or the spatial correlation of an
error. Those eight absences are what Section 2.2 fills.

### 1.3 Data on disk that no proposal uses **(mine, from directory listings and solver configs; the reviewer opened the HDF5 headers and first frames)**

The proposals were written from the dataset pages, and several ask for data that already
exists under `datasets/` without a reader.

| On disk | What it is | What it bears on |
|---|---|---|
| `kinet/doubly_periodic/weakly_compressible_isoT_fluids/sys_Re-5e4_Ma-1en1/D2Q9_shape-512-512_T-20000_H-56d32e.h5` (1.43 TB, readable) | **The reference shear layer at 512².** Its config `56d32e.yaml` has the same deterministic initial condition as `kinet_re5e4` (`lambda: 80`, `epsilon: 0.05`, Re 5e4, Ma 0.1; no random seed, so the initial field is resolution-independent). Step 2n is at the physical time of step n of the 256² run. The reviewer measured the 2 by 2 block average of its velocity against `kinet_re5e4`: relative L2 of 7e-3 at steps 0, 500 and 2000, 2.4e-2 at 5000, 3.9e-2 at 10000. Block-averaged copies at 128, 64, 32 and 16 sit beside it. Issue 011 and judgement 009 call the 512² Re 5e4 runs unreadable, but they mean the ones under `old/`; this one is not under `old/` | A two-level solver refinement comparison of the reference flow itself (issue 126, `EXP-max_error-grid-convergence-with-a-known-solution.md`). The 7e-3 difference at step 0 is the remap of a pointwise initial condition onto cell averages, so an observed order must be read at a time where the difference has grown past it, and on each grid's own cells. A third level needs one 128² rerun from t = 0 |
| `.../sys_Re-5e4_Ma-1en1/prev_256/D2Q9_shape-256-256_T-20000_H-131010.h5` (readable) | The same flow at 256² for 20 000 steps, to physical time 4.51, twice the horizon of `kinet_re5e4` | A longer record of the reference; later frames are further decayed |
| `kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids/sys_Re-5e4_Ma-1en1/` (1.6 TB) | Despite the folder name, a **two-dimensional** D2Q9 run: random-mode initial condition (`k0: 4`, `random_seed: 42`), Re 5e4, Ma 0.1, unforced and decaying, periodic, stored at 128², 256² and 512² for 5 000, 10 000 and 20 000 steps (the same physical end time, 2.2553, as `kinet_re5e4`), with pressure stored as density / 3. **Not** one flow at three resolutions: the seeded generator draws per cell, so the three runs start from different fields. The reviewer measured the initial x-velocity correlation after block-averaging onto 128² at 0.12 (256² against 128²) and 0.005 (512² against 128²), and the overlap of the modes with |k| ≤ 8 at 0.03 to 0.16. The downsampled copies of the 512² run are also averaged over 4 time steps, and the stored vorticity is in lattice units and must be recomputed from velocity | Three statistically equivalent, mutually independent realisations of an isotropic flow, each at a different resolution: the nearest thing on disk to the independent realisations of issue 004 (cluster D1), and an isotropic reference for the isotropy half of issue 001 (not its Reynolds number). Not a refinement sequence |
| `kinet/flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2/` (12 GB) | A compressible (γ = 1.4) obstacle flow at inlet Mach 1.8 (`a92b16.yaml`), inlet plus Neumann boundaries, 500 by 300 cells, 1 000 frames | Issue 002 names it as shocked data that exists elsewhere. Not periodic and not a shocklet field, but a two-dimensional supersonic pressure field with curved fronts for the shock-set metrics (cluster D3). It also shows kinet's compressible solver runs supersonic flow, which bears on the feasibility of B2 |
| `kinet/sod/compressible_fluids/` (two configurations, 7 and 15 GB) | Lattice-Boltzmann Sod runs at γ = 1.4 and γ = 2, 3 001 by 5 cells, 1 000 frames | Scoring a solver against the exact Sod solution; `docs/datasets/sod_shock_tube.md` says they wait on a reader and issue 046 on a wavenumber definition for non-square domains |
| `kinet/doubly_periodic/old/` (five runs, 1.3 to 2.0 TB each) | Re 5e4, 6.25e4, 7.5e4, 8.75e4, 1e5, same shear-layer initial condition | The four unreadable Reynolds-ladder members (issue 011, judgement 009) |
| `well/datasets/` | The Well: `rayleigh_taylor_instability` (three-dimensional, 128³, periodic in x and y with a wall in z), `turbulent_radiative_layer_2D` (one open axis) and `_3D` (open in z), `turbulence_gravity_cooling` (all axes open), `MHD_64`, `MHD_256`, `supernova_explosion_64` and `_128`, `rayleigh_benard`, `planetswe`, `convective_envelope_rsg`, `post_neutron_star_merger`, `gray_scott_reaction_diffusion`. The reviewer read the boundary groups: `pressure` is stored in `turbulence_gravity_cooling`, both supernova sets and both turbulent-radiative-layer sets | The existing Well reader (`fmeval/data/well.py`, lines 99 to 106) refuses any non-periodic axis, so each of these needs a boundary mapping first, and three need three-dimensional support (issues 005, 117). Rayleigh–Taylor is the variable-density mixing data of issue 090. `turbulent_radiative_layer_2D` is a two-dimensional dataset that stores pressure, so it is a candidate for the shock metrics' first non-Sod run once its open axis is mapped |
| `acoustic/dipole/` | An acoustic dipole run (config and manifest present; not inspected further) | A purely dilatational field: a natural known answer for the Helmholtz family (cluster G6) |
| `kinet/mhd/` and `mhd/orszag_tang_vortex_test/` | A 1024² isothermal MHD Orszag–Tang run at Mach 0.043 (reviewer's reading of the config) | Too slow for shocks; not useful here |
| `treb_data/` | `karman_vortex_street`, `double_shear_layer`, `2d_packed_flow`, `3d_flat`, with a `read_data.py` | Not inspected; a vortex street is a natural case for the vortex-population ideas |
| `kinet/homogeneous_isotropic_turbulence/Re-1k_Ma-1en1_*_forced_3d/` | Two folders holding only empty `sim_checkpoints/` and `tiers/` directories, no configs and no data | Forced 3D runs were at least named; whether kinet supports forcing is unchecked |

## 2. The deduplicated catalog

Each cluster lists: what it is, which logged sources ask for it (proposal files, issue
numbers, card counts), which metrics it serves, and what it costs. "Cards naming it" counts
the metric cards whose text names the proposal or the gap.

### 2.1 Datasets and benchmark problems

**D1. A physical ensemble and independent realisations of the same flow.**
N + 1 solver runs from one state plus N + 1 independent small perturbations, at several start
times, each run in turn the truth, scored at every stored lead time; and runs from unrelated
initial conditions.
*Sources:* `EXP-spread_skill-perturbed-initial-condition-ensemble.md`; issues 003, 004, 037,
132 (its line 58 wants independent realisations for the Hill interval); `judgements/001` ("the
principled unrelated field, and still wanted, but the data does not exist");
`METRIC_EVALUATION_DESIGN.md` and `METRIC_EVALUATION_CRITIQUE.md` on the position-blind onset;
`ANALYTIC_DATASETS_LOG.md` on the bounded-domain anchor.
*Cards naming it:* the 8 ensemble metrics name the perturbed-initial-condition ensemble or
issue 004 (`crps`, `crps_skill_score`, `energy_score`, `ensemble_mean_rmse`, `rank_histogram`,
`rank_histogram_chi2`, `spread_skill`, `variogram_score`); four of them add that the
smoothing, spectral, displacement, resolution and noise families and the trap tests are
absent from their evidence because no physical ensemble exists.
*Serves:* the 8 ensemble metrics (their field's first figure, spread and error against lead
time, and the binned spread-error diagram); every metric's damage anchor, since the
independent realisation is the unrelated field the `uncorrelated` probe only approximates
(issue 004 measured the probe's `energy_changed` at 1.64 to 3.05 against the 2 of a true
realisation); `increment_flatness` and `tail_index`, whose anchors are 0/0 or NaN on a
constant field (issue 037 and the `tail_index` card); the stochastic ladder of G9.
*Known answer:* for an exchangeable ensemble the squared error of the ensemble mean is
(N + 1)/N times the true variance at every lead time and in every spread bin (Leutbecher and
Palmer 2008, *J. Comput. Phys.* 227(7), 3515–3539, Sect. 2.2, Eqs. 5 to 7 in the numbering of
ECMWF Tech. Memo. 514; the reviewer's sub-agent read the memorandum). The exchangeability is
load-bearing: with the unperturbed run as truth the ratio of squared error to spread is
1/(N − 1) instead of (N + 1)/(N − 1) at lead zero, a factor N + 1, and the factor persists
through the linear-growth regime (the reviewer's derivation, not simulated).
*Cost:* (N + 1) runs per start; the proposal's arithmetic is 51 runs of the horizon
at 256² for 16 members and three starts. A reader that assembles members from separate runs.
*Dedupe note:* issue 004 (unrelated initial conditions) and the perturbed-initial-condition
ensemble (small perturbations) share a production job but not an initial-condition option:
the shear-layer configuration has no seed parameter, and a shear layer whose geometry is fixed
by λ and the domain will likely roll up into the same vortex pair in the same place, so
issue 004's acceptance test (`energy_changed` of 2) may not be met on it, particularly on
density (the reviewer's reasoning). The random-mode family on disk (Section 1.3) already
gives three independent realisations and is the natural source of more. The "statistical
twin for the bounded-domain anchor" on Sod (`ANALYTIC_DATASETS_LOG.md`) is the same want on a
different dataset.

**D2. Many initial conditions, scored step by step.**
Reference trajectories from many different initial conditions, and for each a candidate
trajectory from the same start, made by an analytic formula or by a solver run degraded in a
controlled way (a coarser grid, a wrong viscosity, a different collision model or solver). Every
metric is computed at every stored step and averaged over the starts. Specified in
`dataset_specs/05_initial_conditions_and_degraded_solver_runs.md`.
*Sources:* `EXP-nrmse-rollouts-over-many-initial-conditions.md`; issues 078, 079, 080, 081 and
094 (the time-dependent ideas); `docs/ideas/infrastructure/baseline_predictors.md`
(persistence and a coarse solver as references); `STANDARD_EVALUATION_PLAN_CRITIQUE.md`
finding 1.
*Cards naming it:* 13 (`enstrophy`, `h1_relative`, `kinetic_energy`, `mae`, `max_error`,
`max_error_channel_mean`, `mse`, `nrmse`, `palinstrophy`, `rmse`, `rmse_channel_mean`,
`spectrum_l2`, `vrmse`). This is the most-cited single want on the cards.
*Serves:* every pairwise metric (the per-step error averaged over initial conditions, with a
spread, which the `nrmse` and `vrmse` cards cite as their field's reporting); the single-field
metrics as time series; the time-dependent ideas; `max_error` as a stability diagnostic.
*Cost:* none for the reference set: 100 complete decaying isotropic runs at each of three
Reynolds numbers are on disk (`dataset_specs/00_how_to_use_kinet.md`, "Read this first").
Analytic candidates are readers; coarse-grid and wrong-viscosity kinet runs started from the
archive's own fields take minutes each; an OpenFOAM run of the same initial velocity is an
independent-solver candidate.
*Dedupe note:* `forecast_re5e4` is the existing partial instance (one set of predictions of
unknown provenance, two starts, ten steps). The persistence reference is G1's time lag under
another name.

**D3. A two-dimensional shock dataset, up to shocklet-populated turbulence.**
Three tiers in order of cost: a Sedov–Taylor blast wave (a closed front at a known radius);
the two-dimensional Riemann configurations of Lax and Liu (curved, oblique, interacting
fronts); decaying compressible turbulence with eddy shocklets (issue 002, the north-star
case).
*Sources:* `EXP-shock_set_distance-2d-shock-dataset.md`; issues 002 (accepted and scheduled
2026-08-07), 016, 088, 120; `METRIC_EVALUATION_DESIGN.md` D7; both critiques;
`STANDARD_EVALUATION_PLAN_CRITIQUE.md` (FSS, CSI and ETS "degenerate on one 1-D shock");
`docs/ideas/README.md`; `docs/datasets/README.md`; `metrics/shock_set_distance/code_notes.md`
line 109 (a jump on the seam of a periodic grid, a case no dataset has).
*Cards naming it:* the 6 shock cards (`shock_mask_overlap`, `shock_set_distance`,
`shock_set_hausdorff`, `shock_set_hausdorff95`, `shock_set_masd`, `shock_set_baddeley_delta`),
plus `persistence_distance` (wants a dataset with pressure and topology). The same 6 cards
record that every non-Sod dataset is skipped with "needs pressure".
*Serves:* the 6 shock metrics on oblique and multiple fronts, where the axis-by-axis detector
and the pooled averaging are untested; the shock-turbulence interaction statistics; the
compressible spectral flux and the Helmholtz split (judgement 003 says the velocity-only flux
is a weak-compressibility approximation); the both-empty convention of issue 120; the
mass-weighted remap of issue 016.
*Cost:* a two-dimensional Euler solver run (the kinet solver already runs Sod and the
supersonic obstacle flow), a reader, boundary types per axis. A few hundred frames at 512².
Citations as the proposal gives them: Schaal and Springel 2015, *MNRAS* 446, 3992–4007,
Sect. 3.1, ran the Sedov–Taylor test in three dimensions at 25³ to 100³ cells; Lee, Lele and
Moin 1991, *Phys. Fluids A* 3(4), 657–664, is primarily a three-dimensional study; a
two-dimensional version of either is this repository's own choice.
*Dedupe note:* D8 is the closed-form companion with known answers per kind of error, not a
duplicate. The on-disk obstacle flow and kinet Sod runs (Section 1.3) and The Well's
`turbulent_radiative_layer_2D` are interim two-dimensional pressure fields with no new
simulation.

**D4. Forced, statistically stationary turbulence with an inertial range.**
Two forms were proposed: (a) forced two-dimensional compressible turbulence, solenoidally
forced at a fixed wavenumber, with a flux loop, known cascade slopes and shocklets; (b)
cutouts of the Johns Hopkins forced isotropic three-dimensional dataset (Li et al. 2008).
*Sources:* `EXP-spectral_energy_flux-forced-2d-compressible-flux-loop.md`;
`EXP-increment_flatness-isotropic-3d-turbulence-cutouts.md`;
`EXP-tail_exceedance-base-period-climatology.md` (needs "a long, statistically stationary
reference record" and names both); issues 005, 085, 128; `STANDARD_EVALUATION_PLAN_CRITIQUE.md`
("isotropic turbulence with an established scaling range before any scaling exponent is
promised"); `docs/ideas/README.md` rows for the four-fifths law and structure functions.
*Cards naming it:* 8 name the three-dimensional cutouts (`energy_distance`,
`increment_flatness`, `increment_w1`, `increment_w1_by_separation`, `spectral_energy_flux`,
`spectrum_l2`, `tail_exceedance`, `tail_index`); `spectral_energy_flux` and `spectrum_l2` name
the forced two-dimensional run; `tail_exceedance` names the base period.
*Serves:* every spectral, increment, distributional and tail metric, which today can show only
that their number moves under damage and not that it reads the statistic their field defines
(flatness against separation, the compensated spectrum and slope, the flux plateau and sign
change at the forcing scale, exceedance against a climatological threshold); the shock
metrics in the shocklet regime; the inviscid-invariant checks of issue 085; a physical
separation scale for the increment metrics (issue 128).
*What the source actually reports (the reviewer's sub-agent read it):* Kritsuk, "Energy
transfer and spectra in simulations of two-dimensional compressible turbulence", in
*Turbulent Cascades II*, ERCOFTAC Series 26, Springer 2019, pp. 61–70,
doi:10.1007/978-3-030-12547-9_8 (arXiv:1802.08228). Its turbulent Mach numbers 0.33 and 0.54
are the end states of two separate runs, not an operating range; shocklets are reported from
about Mach 0.25 to 0.3; the Fig. 6 caption says Case B's total energy "is not statistically
stationary and continues to grow". The runs have no large-scale friction, and in two
dimensions the inverse cascade piles energy at the box scale unless a drag removes it
(Boffetta and Ecke 2012, *Annu. Rev. Fluid Mech.* 44, 427–451, the friction term α in their
equations of motion). A base period therefore needs a drag term the proposal does not mention.
*Cost:* (a) a new simulation; kinet runs supersonic compressible flow (the obstacle run), but
whether it supports forcing and a drag is unchecked. (b) a reader for the database's web
service and three periodic axes; 0.2 GB per 256³ cutout; the 1 024 stored frames span about
one eddy turnover, which may be too short for a base period plus a disjoint evaluation period.
*Dedupe note:* form (a) covers D3's shocklet tier at the same time.

**D5. A grid-refinement sequence against a known solution.**
A problem with an exact or manufactured solution solved at 64², 128², 256², 512², with the
observed order of accuracy read from successive grids (Roy 2005, *J. Comput. Phys.* 205(1),
131–156, Eq. 8).
*Sources:* `EXP-max_error-grid-convergence-with-a-known-solution.md`; issue 126; the "Can the
three runs be read as a grid-refinement sequence?" section of `docs/datasets/reynolds_ladder_2d.md`;
`docs/ideas/evaluation_design.md` (the grid-convergence index of the reference);
`docs/ideas/infrastructure/grid_convergence.md`; `proposals/MTR-max_error-high-quantile-error.md`
line 40 (grids of two sizes for the cell-count dependence of an extreme statistic).
*Cards naming it:* 5 explicitly (`h1_seminorm`, `mae`, `max_error`, `mse`, `rmse`) and 3 more
through issue 126 (`nrmse`, `rmse_channel_mean`, `vrmse`).
*Serves:* the 8 pointwise and gradient norms (the numerical analyst's first figure, error
against spacing on log-log axes with the formal slope drawn in); the reference's own
discretisation error for every metric; `shock_set_distance` on Sod against resolution.
*Cost:* a solver run per level plus a manufactured source term (not checked whether kinet
supports one) or the Sod exact solution at several solver resolutions. The comparison must be
on each grid's own cells, not after the analysis-grid remap.
*What is on disk:* the 512² and 256² runs of the reference shear layer from one deterministic
initial condition (Section 1.3) are a two-level solver comparison today, with the finest run
as reference rather than an exact solution; a 128² rerun from t = 0 would make three levels.
The kinet Sod runs give one solver resolution each against the exact solution.

**D6. Extensions of the synthetic ensemble.**
Three reader options and seven ensemble operators on `synthetic_ensemble`:
the Gneiting forecaster suite (ideal, climatological, unfocused, Hamill; published CRPS in
Table 5 of Gneiting, Balabdaoui and Raftery 2007, *J. R. Stat. Soc. B* 69(2), 243–268); a
heteroscedastic variant whose true σ varies from case to case with three operators that
remove, exaggerate or invert the flow-dependence; a correlated variant whose noise is a
Gaussian random field of known correlation length with one operator that redraws it at the
wrong length. Plus a positive-density variant, since `wasserstein` is `not_run` there because
the current signed pattern makes every value NaN (`metrics/wasserstein/card.yaml`).
*Sources:* `EXP-crps-gneiting-forecaster-suite.md`;
`EXP-spread_skill-heteroscedastic-synthetic-ensemble.md`;
`EXP-energy_score-correlated-synthetic-ensemble.md`; issues 083, 127;
`STANDARD_EVALUATION_PLAN_CRITIQUE.md` (the binned spread-error diagram of a calibrated
uniform-σ ensemble is flat, not diagonal, so the figure is withheld as degenerate);
`degradations/spread_inflate/card.md` lines 86 to 93 (a skewed or heavy-tailed member
distribution, which scaling about the mean cannot produce).
*Cards naming it:* 6 name the forecaster suite, 6 the perturbed-initial-condition ensemble, 4
the heteroscedastic variant, 2 the correlated variant (`energy_score`, `variogram_score`,
which record that "no experiment in the repository changes" an ensemble's spatial
correlation, the one thing those two scores exist to judge).
*Serves:* the 8 ensemble metrics, with closed-form answers: a calibrated-but-useless
climatological forecaster that `rank_histogram` and `spread_skill` must pass and `crps` must
rank last; the spread-error diagram with a known slope per operator; a correlation error that
cell-by-cell scores must be blind to and `variogram_score` must follow; `wasserstein` on an
ensemble at all.
*Cost:* seconds per run on 64² with 16 members; a few lines of seeded sampling each. The
cheapest item in this catalog with a published answer.

**D7. Closed-form fields with a known feature population.**
A periodic superposition of a known number of vortices of known radii, circulations and
positions (profile to be chosen and cited; the proposal leaves a TODO). The proposal to
`MTR-persistence_distance-signed-vortex-census.md` adds a one-sign weakening (lines 42–43).
*Sources:* `EXP-orchestrator-20261023-known-vortex-field.md`; issues 060, 073, 082, 086;
`DECISIONS_OVERVIEW.md` §4.2.
*Cards naming it:* `persistence_distance`, `persistence_wasserstein`.
*Serves:* the two persistence metrics (a known number of persistent points); the winding
angle, vortex criteria, eddy census and feature pair-correlation ideas, all blocked on it.
*Cost:* a new `ClosedFormTrajectory` reader, seconds per run. Admitted as evidence only by a
decision like the one that admitted Sod. Section 3 merges D7, D8(a) and D9 into one generator.

**D8. Closed-form shock benchmarks with known geometric errors.**
(a) Pressure fields carrying fronts of chosen shape (straight, curved, closed), with
candidates built by a known displacement, length change, rotation, and displacement plus
amplitude error, transferred from the spatial-verification intercomparison cases (Ahijevych
et al. 2009, *Weather Forecast.* 24(6), 1485–1497, five geometric and seven perturbed cases;
the table numbers in the proposal could not be rechecked behind the paywall; Roberts and Lean
2008, *Mon. Weather Rev.* 136(1), 78–97, Fig. 4, a one-cell band displaced by 1, 3, 11 and 21
cells). (b) The exact Sod solution at time t scored against the exact solution at t + dt, so
each wave moves by its own speed times dt with every jump exact.
*Sources:* `EXP-shock_mask_overlap-geometric-and-perturbed-cases.md`;
`EXP-sod_evidence-sod-time-offset.md`; issue 051; `DECISIONS_OVERVIEW.md` §4.4.
*Cards naming it:* the 6 shock cards name both.
*Serves:* the 6 shock metrics with one known answer per kind of error (the distance summary
has a closed form for a pure shift; an overlap score drops to its floor once thin sets stop
touching; the neighbourhood score recovers at a known width); the shock-front speed of issue
051. (b) already works as a one-offset unit test in `metrics/shock_set_distance/test_metric.py`
and lacks only a paired-time degradation or reader to become a ladder axis.
*Cost:* (a) a closed-form reader and a rotation operator (issue 015); (b) 0.3 ms per frame,
but it does not fit the one-field degradation interface, so a person must choose between a
dataset-specific operator with trajectory access and a reader that pairs each frame with a
second one, as `fmeval/data/forecast.py` does.

**D9. Known-answer transport problems and a background-ratio sweep.**
(a) Periodic density pairs with an exact quadratic Wasserstein distance: a manufactured
Monge–Ampère map (Saumier, Agueh and Khouider 2015, *IMA J. Appl. Math.* 80(1), 135–157,
Sect. 5.1) and one-dimensional profiles on the circle (Delon, Salomon and Sobolevski 2010,
*SIAM J. Appl. Math.* 70(7), 2239–2258, Sect. 2, not rechecked). (b) `advecting_blobs` with
the bump height swept over decades so the background goes from dominant to negligible.
Engquist and Yang 2022, *Commun. Pure Appl. Math.* 75(10), 2201–2244, Theorem 4.6, bounds the
*squared* distance W₂² for one-dimensional compactly supported densities: O(s²) for shifts up
to about 1/c plus the support width and O(|s|) beyond; applying it to the two-dimensional
blobs is an extrapolation. Also wanted: high-contrast and near-empty densities for the
Monge–Ampère solver (`metrics/wasserstein/code_notes.md` lines 276 and 280;
`MTR-wasserstein-full-newton-gmres.md` lines 37–38), and a varying background for `max_error`
(`metrics/max_error/code_notes.md` line 62).
*Sources:* `EXP-wasserstein-known-answer-transport.md`;
`EXP-wasserstein-background-ratio-sweep.md`; issues 047, 048, 066, 067.
*Cards naming it:* `wasserstein`, `h_minus_one`.
*Serves:* every transport metric, built or planned (sliced Wasserstein and Sinkhorn both need
"validation against the exact Wasserstein distance on small cases"); the signed-field
normalisation question of issue 047.
*Cost:* (a) about twenty lines of test fixture; (b) no new code, the bump height is already a
reader option.

**Regime data and references with no proposal, recorded for completeness.** A reference at
Re ≈ 500, isotropic and doubly periodic, or an amended protocol (issue 001;
`docs/ideas/infrastructure/degradation_ladder_reference.md`, item 1); wall-bounded flow
(issue 089); variable-density mixing (090); reacting or scalar-mixing flow (091); supersonic
isothermal turbulence with the sound speed stored (088); a line-of-sight projection of a 3D
field with its observation operator (087); data on more than one mesh (053); a transported
scalar for the Batchelor scale (058); rotating stratified data (085); a simulated
Taylor–Green run (`docs/datasets/taylor_green_vortex.md`); a turbulence dataset that stores
pressure (judgements 003 and 006, issue 101, `ANALYTIC_DATASETS_LOG.md`); the four unreadable
Reynolds-ladder members (issue 011); a light-tail fixture with uniform increments
(`MTR-tail_index-moment-estimator.md` line 41). Several are on disk (Section 1.3).

### 2.2 Degradation families

**G1. A temporal ladder, and windowed budget residuals.**
Three operators on a window of consecutive reference frames: a time lag (the prediction at
frame t is the reference at t + d), temporal smoothing (a running average over w frames), and
consistent spatial damage (an existing operator applied with the same severity and random
draw to every frame of the window). Plus the states needed to close the energy and enstrophy
budgets dE/dt = −2νΩ and dΩ/dt = −2νP (Boffetta and Ecke 2012, Eqs. 5 and 6, valid with no
forcing and no friction; the three bundles' normalisations are consistent with them,
per the reviewer's sub-agent).
*Sources:* `EXP-orchestrator-20261023-temporal-ladder.md`;
`EXP-enstrophy-budget-closure-from-consecutive-states.md`; issues 051, 056, 069, 073, 078,
079, 080, 081, 084, 094; `METRIC_EVALUATION_CRITIQUE.md` §9 (non-overlapping frame blocks as
sample units); `docs/datasets/reynolds_ladder_2d.md`; `DECISIONS_OVERVIEW.md` §4.1;
`docs/ideas/infrastructure/baseline_predictors.md` (persistence). This is the most-cited
cluster across the non-card sources.
*Cards naming it:* `enstrophy`, `kinetic_energy`, `palinstrophy` (the budget form).
*Serves:* eight screened-out ideas that "fail only because no experiment acts on time" (valid
prediction time, temporal autocorrelation, invariant measure, modal decompositions, weak
residual, shock speed, entropy production, eddy lifetimes); the three single-field metrics,
whose mutual consistency on a candidate is otherwise unreadable; object matching in time for
the shock metrics.
*What the budget needs (the reviewer's measurement on `kinet_re5e4`):* the one-step budget
does not close on the reference. With E = ½⟨|u|²⟩ and Ω = ½⟨ω²⟩ from a spectral curl, the
effective viscosity −(dE/dt)/(2Ω) from central differences one solver step apart has a 5th to
95th percentile range of 0.67 to 2.15 over steps 2000 to 2200 and of −4.2 to 6.3 over steps
6000 to 6200, negative in 44% of those steps; over the whole 200-step windows it is 1.23 and
1.31, one constant to about 6%. The proposal's warning that Eqs. 5 and 6 "hold only
approximately" on a weakly compressible solver is the point; the reviewer's conjecture is
acoustic exchange between kinetic and compressional energy. So the budget is a residual over
windows of order 100 steps with the reference's windowed residual as the floor, and storage
every 10th step suffices. The weak-form residual (issue 084) should be checked the same way
before it is promised one-step pairs.
*Cost:* a harness change (H1): the pipeline hands a metric a window of frames and the ladder
applies an operator to a window. `per_unit_time` on `advecting_blobs` already covers the
third operator for linearly growing damage (issue 094). A test with no new data **(mine)**:
`taylor_green_2d` is an exact decaying solution with known ν (`fmeval/data/analytic.py`); with
the repository's normalisations E = ¼e^(−4νt) and Ω = ½e^(−4νt), so dE/dt = −2νΩ holds
exactly and the three bundles' normalisations can be pinned by a unit test today.

**G2. Tail and intermittency axes with a known answer.**
(a) Pareto spike injection: a fraction of cells receives a spike of amplitude drawn from a
Pareto law with exponent α and random sign, so the Hill estimate has a known target 1/α.
(b) Tail-only damage: cells whose one-cell increment exceeds the reference's q-th quantile
are locally smoothed or compressed, with severity 1 − q, leaving the bulk exactly unchanged.
*Sources:* `EXP-tail_index-pareto-spike-injection.md`;
`EXP-energy_distance-tail-only-degradation.md` (the two already cross-reference each other as
"see also"); `metrics/tail_exceedance/research_notes.md` (the peaks-over-threshold tier was
not built because "no ladder axis moves a fitted generalised-Pareto shape in a known
direction"); issue 128.
*Cards naming it:* 6 name the tail-only axis (`energy_distance`, `increment_flatness`,
`increment_w1`, `increment_w1_by_separation`, `tail_exceedance`, `tail_index`); 2 name the
Pareto spikes (`tail_index`, `tail_exceedance`).
*Serves:* the six distributional and tail metrics, which today cannot be told apart from
metrics that read only the bulk because "every current smoothing, filtering and noise axis
changes bulk and tail together"; the peaks-over-threshold fits that head "What to build next".
*What the known answer requires (the reviewer's simulation on a synthetic k⁻³ field, not on
kinet):* the Hill estimate uses the top k = ceil(√n) increments per axis (`metrics/tail_index/card.md`:
k = 256 of n = 65 536 at 256²). The spikes must dominate those k, so their number per axis
must exceed about k/2. With a fraction of 1e-3 at 256² the estimate came out at 1.2 to 2.2
against targets of 0.17 to 0.5; with 4e-3 at 256² and 1e-2 at 128² it matched the target to
three figures at every α from 6 to 2. Spec 09 refined the threshold by simulation: a fraction of
exactly 1/(2√n) fails; 1/√n works only if the spike floor a₀ exceeds the reference's largest
increment (about three times the fluctuation rms there); **2/√n works either way**
(`dataset_specs/09_random_fields_known_statistics.md`). Kinet increments are more clustered than the synthetic field (issue 132), so the required
fraction there may be higher. For α ≤ 4 the flatness has no finite expectation and for α ≤ 2
the spike variance diverges, so fourth-order statistics are undefined on that part of the
ladder by construction.
*Cost:* two stochastic bundles of about thirty lines each, uncalibrated; the tail-only form
must keep the field periodic and the spatial mean, which local smoothing does only
approximately.

**G3. Graded phase randomisation.**
Keep every Fourier amplitude and rotate each mode's phase by a uniform random angle of
half-width sπ, Hermitian symmetry kept; s = 0 is the reference and s = 1 the impostor.
*Sources:* `EXP-spectral_energy_flux-graded-phase-randomisation.md`; issue 065 (bispectrum);
`metrics/spectral_energy_flux/research_notes.md`.
*Cards naming it:* `spectral_energy_flux`, `spectrum_l2`.
*Serves:* the 25 non-shock, non-ensemble metrics (the shock metrics have no periodic pressure
field to randomise, and on Sod's walls the operator acts on an extended and cropped field so
neither the preserved spectrum nor the prediction holds; on `synthetic_ensemble` the field is
mostly per-cell white noise, whose phase randomisation changes nothing in distribution). For
the spectrum-based metrics and the two-point correlation it is a declared blind axis; for
every third-order statistic (flux, bispectrum, coherence, derivative skewness) a predicted
response curve; and for every other metric it converts the canary's single all-or-nothing
reading, which is excluded from every rank correlation, into an ordinal axis with a trend.
*Two corrections to the proposal, from the reviewer:*
1. **The prediction is approximate.** For a real field θ(−k) = −θ(k), so a triad term gets
   the product over its ± pairs of sinc(c s) with c the pair's net integer coefficient:
   sinc(s)³ for three distinct pairs, sinc(2s)·sinc(s) when two members coincide. On a 64²
   band-limited test field the exact sum over triads and a Monte Carlo agree with each other
   (0.237 against 0.258 from sinc³ at s = 0.5; 0.020 against 0.027 at s = 0.75), and the
   departure grows as energy concentrates in few modes, which is the case for kinet density
   (69% of its fluctuation energy in four modes, `CLAUDE.md`). Self-conjugate modes can only
   be rotated by 0 or π and need a special case. The argument covers third-order statistics
   only; `increment_flatness`, a fourth-order quantity, has no prediction from it.
2. **The impostor's phase draw it would reuse injects divergence.** `degradations/gaussian_impostor/degradation.py`
   draws an independent phase field per channel (the loop at line 57). On an exactly
   solenoidal two-channel velocity that puts 0.228 of the energy into the dilatational part
   (expected 1/4). Nothing in the impostor's card, any issue or any judgement records this, so
   it is also in today's canary readings on velocity and vorticity. The fix for both is to
   rotate all components of a vector field by one phase per wavevector, which keeps k·û = 0;
   an issue should be opened against `gaussian_impostor`.
*Cost:* one bundle; `preserves=("amplitude_spectrum", "spatial_mean")`; stochastic. No new
data.

**G4. Feature-population axes: add, remove, simplify.**
(a) Spurious feature injection: a fixed number of small isolated Gaussian wells or bumps of
depth h in units of the fluctuation rms at random positions. (b) Persistence-sensitive
simplification: replace the field by one within ε of it whose persistence diagram loses every
point of persistence at most ε (Edelsbrunner, Morozov and Pascucci 2006, *Proc. 22nd Symp.
Comput. Geom.*, 127–134), so the weakest features are removed by a known amount; the
bottleneck distance is then at most ε/2 (the proposer's derivation, not a statement of the
paper). (c) The degradation form of D7: attenuate the vorticity inside chosen closed contours,
optionally of one sign only.
*Sources:* `EXP-persistence_distance-spurious-feature-injection.md`;
`EXP-persistence_distance-topological-simplification.md`;
`EXP-orchestrator-20261023-known-vortex-field.md` (form 2); issues 013 (the single-cell spike
probe), 073, 086; `MTR-persistence_distance-signed-vortex-census.md`.
*Cards naming it:* `persistence_distance`, `persistence_wasserstein`.
*Serves:* the two persistence metrics with known answers; `max_error` and the pointwise
controls, which dilute a few spurious cells in their mean (the contrast the topological
metrics exist for); the eddy census and winding angle.
*Cost:* (a) a few lines; (b) a simplification routine on the cubical complex with no library
support found, validated against the diagram the metric already computes; (c) needs a vortex
detector, which is the thing under test, so (a) and (b) are the cleaner forms.
*Dedupe note:* the single-cell spike probe of issue 013 is (a) at a width of one cell, so one
operator with a width option covers both.

**G5. A directional (anisotropic) blur.**
Gaussian widths that differ along x and y, the ratio being the severity, with the geometric
mean held at a fixed fraction of the characteristic scale.
*Sources:* `EXP-orchestrator-20261023-anisotropic-blur.md`; issues 058, 071, 075;
`DECISIONS_OVERVIEW.md` §4.3.
*Cards naming it:* none.
*Serves:* the direction-dependent two-point correlation, Reynolds-stress anisotropy, the
statistical-isotropy check of equivariance, Minkowski tensors: "anisotropy is the property
several ideas add over the built spectrum and kinetic energy, and without this operator none
of that addition can be tested". It is *not* a blind axis for the radial spectrum: at fixed
σxσy the angle-averaged transfer of an anisotropic Gaussian depends on the ratio, damping low
wavenumbers more and high wavenumbers less (the reviewer's derivation; the proposal makes no
blind-axis claim and the first draft of this catalog wrongly added one).
*Cost:* one bundle reusing the kernel code in `degradations/_shared/`; `preserves=
("spatial_mean",)`. The harness resolves only the *severity* under `calibration="scale"`
(`fmeval/ladder.py`, the `length_for_scale_fraction` branch), so a ratio severity must use
`calibration=None` and the operator must resolve its mean width itself from `ctx`; a ratio has
no identity at 0, so `zero_is_identity=False`.

**G6. The Helmholtz family: dilatational scaling and solenoidal projection.**
Split the velocity by Fourier projection, multiply the dilatational part by 1 + s (s down to
−1 removes it), recombine; and a `project_solenoidal` option on the spectral degradations so
that lost small scales and gained spurious divergence can be separated.
*Sources:* `EXP-orchestrator-20261023-dilatational-scaling.md`; issues 024, 057;
`DECISIONS_OVERVIEW.md` §4.5.
*Cards naming it:* none.
*Serves:* the Helmholtz split (ranked high by the team), any compressibility diagnostic; and a
blind-axis test for every curl-based metric (`enstrophy`, `palinstrophy`, `spectral_energy_flux`
on the solenoidal part must be invariant), which the impostor's divergence defect (G3)
currently muddies. The on-disk acoustic dipole is a purely dilatational known answer.
*Cost:* one `whole_frame=True` bundle on velocity, periodic domains only, plus one option on
the five spectral operators. Both share one projection operator.

**G7. The admissibility family.**
Controlled negative excursions of density or pressure in a known fraction of cells; a known
number of non-finite cells (needs the frame-finiteness check relaxed for this operator only);
and a positivity-preserving (log-normal) multiplicative noise, because the current
`multiplicative_noise` at severity 0.5 makes density negative and `wasserstein` scores NaN
there, removing the axis's ordering statistics.
*Sources:* `EXP-orchestrator-20261023-constraint-violation.md`; issues 070, 139;
`metrics/wasserstein/research_notes.md`; `metrics/shock_mask_overlap/research_notes.md`
(`bias` on the Sod ladder: an offset of 0.2 erases a perfectly placed shock and the evidence
never exercised it); `DECISIONS_OVERVIEW.md` §4.6.
*Cards naming it:* `wasserstein` (issue 139).
*Serves:* the admissibility checks ("among the cheapest and most decisive physical checks on a
prediction", untestable today); every positive-field metric on the noise axis; the shock
metrics against a pressure offset.
*Cost:* two or three small bundles and one ladder-config line.

**G8. Probes: rotation, Galilean boost, invariance audit, triangle inequality.**
A 90° rotation that rotates vector components (issue 015) and a 45° rotation fixture for the
vector form of `max_error` (`MTR-max_error-vector-magnitude.md` line 42); a Galilean boost at
|c|/u_rms of 0.1, 1 and 10 (`docs/ideas/physics_invariants/equivariance_tests.md`, line 49);
an invariance audit (rotation, reflection, joint translation of both fields) and a
triangle-inequality scatter (issue 013); a gradient-norm-against-displacement renderer for
differentiable metrics (issue 014).
*Sources:* issues 013, 014, 015; the equivariance idea page; `MTR-max_error-vector-magnitude.md`.
*Cards naming it:* none.
*Serves:* every metric: a rotation or boost of both fields must leave any metric on an
isotropic flow unchanged, and a differentiable metric's gradient against a sub-pixel
displacement is drawn for every metric that declares one.
*Cost:* one geometric operator (exact only at multiples of 90°; 45° needs interpolation and is
a fixture, not a ladder axis), a boost operator on velocity, probe configurations and
renderers.

**G9. A stochastic ladder: several draws per severity.**
Independent random draws per (frame, severity) for the stochastic operators, so the spread
across draws is a noise scale in the metric's own units and a response divided by it is a
signal-to-noise ratio, invariant to monotone re-expression to first order; the anchor draws
also give the noise floor for a two-sample test (`CURVE_METRICS_CRITIQUE.md` line 460).
*Sources:* issues 097, 106 (one impostor draw per frame gives a median of 0.955 against
per-frame medians near 1.02 over 300 seeds); `metrics/max_error/research_notes.md`;
`METRIC_EVALUATION_CRITIQUE.md` Alternative D; `METRIC_EVALUATION_CRITIQUE_2.md`;
`METRIC_EVALUATION_DESIGN.md`.
*Cards naming it:* `max_error`.
*Serves:* every metric: it is the only experiment that makes response magnitudes comparable
across metrics (issue 097 measured `elasticity` agreeing on 2 of 36 rows between MSE and RMSE,
which carry identical information), and it gives the impostor reading an interval.
*Cost:* no new operator; a ladder option and a multiplier on run cost equal to the number of
draws. D1 is its physical-data counterpart.

**G10. Spatially structured errors, from the degradation cards' own limitations.**
Spatially correlated additive noise (a Gaussian random field of given correlation length,
drawable with the impostor's spectral machinery); a regional blur; selective displacement of
one feature; a spatially patterned bias.
*Sources:* `degradations/additive_noise/card.md` lines 73–75 (it calls white noise "the least
realistic failure in the default set", because realistic errors are correlated in space); `degradations/gaussian_blur/card.md`
lines 78–79; `degradations/translate/card.md` lines 80–83; `degradations/bias/card.md` lines
64–65. Found by the reviewer; no metric card or proposal names them.
*Cards naming it:* none.
*Serves:* every metric: spatially correlated error is what any smooth approximation of a
flow produces, a coarse or overly diffusive solver included, and a metric that follows white noise "has been shown very little". Selective displacement of
one feature is the double-penalty case in its purest form, which the global translations
cannot produce.
*Cost:* one stochastic bundle for correlated noise (severity the amplitude as a fraction of
the fluctuation rms, correlation length an option calibrated against the characteristic
scale); the other three are small operators or fixtures.

**Ladder housekeeping with no proposal.** Extend the severe end of the ladder or state that
saturation is not reached (issue 031); usable sharp-filter and median levels on Sod
(`docs/datasets/sod_shock_tube.md`, `ANALYTIC_DATASETS_LOG.md`); a sub-pixel shift that does
not ring beside a sharp jump (`metrics/shock_mask_overlap/research_notes.md`); a Nyquist
convention for `translate_subpixel` (issue 041); a wider blur list for vorticity at Re 1e6
(issue 011); an artificial-viscosity axis as the protocol's second ladder axis
(`docs/ideas/infrastructure/degradation_ladder_reference.md`, item 2; `CLAUDE.md`, "Evaluation
protocol", step 2), which needs a solver run rather than an operator.

### 2.3 Harness and protocol capabilities

**H1. A window of frames handed to a metric, and series-level pooling.**
*Sources:* issues 094, 095, 078 to 084; `judgements/011`; `metrics/max_error/research_notes.md`;
`metrics/shock_set_distance/research_notes.md`; `METRIC_EVALUATION_DESIGN.md`;
`METRIC_EVALUATION_CRITIQUE.md` §9; `EXP-tail_exceedance-base-period-climatology.md`.
*Serves:* G1 entirely, the base-period threshold, the dynamics family, the budget metrics,
the CRPS skill climatology, and any distributional estimate pooled over non-overlapping
frame windows. The design documents say to add it with its first customer; G1 is that
customer.

**H2. Several fields handed to one metric, and a positive-field declaration.**
*Sources:* issues 096, 101, 016; judgements 003, 006; the `spectral_energy_flux`,
`shock_set_distance`, `shock_mask_overlap` and `wasserstein` notes; `ANALYTIC_DATASETS_LOG.md`.
*Serves:* the compressible flux budget, the full Schaal–Springel shock criterion, the Mach
histogram, a mass-weighted remap, and a refusal rather than a meaningless number when a
gauge pressure reaches a shock metric. Pressure must come from a dataset, never be computed
(dataset design rule); D3, D4 or The Well's `turbulent_radiative_layer_2D` would be the first
dataset to store it.

**H3. Evidence plumbing the cards ask for.**
- Six cards (`increment_flatness`, `increment_w1_by_separation`, `spectral_energy_flux`,
  `spectrum_l2`, `tail_exceedance`, `tail_index`) say only the registered number, not the
  curve companion, is tabulated on `forecast_re5e4`.
- Every card that reports `kinet_re1e6` (24) cites run `comparison_1793846600` on the 128²
  analysis grid against its primary run `comparison_1793846511` on the 256² grid
  (`results/comparison_1793846600/data/config.yaml`), so their sentence "the two runs differ
  in both Reynolds number and analysis grid" is literally true of what they compare; the
  explicit caveat appears on 8 to 10 cards depending on phrasing, and the confound on all 24.
  The fix is one override, `analysis_grid.resolution=256` on `kinet_re1e6` (1024 to 256 is an
  integer factor), or citing the 128² ladder sweep for both members. The first draft of this
  catalog misread this as a complaint about the ladder sweep.
- Six pointwise cards say "the trap tests are not run on" `synthetic_ensemble`, and eleven
  cards skip that dataset because the miscalibration ladder leaves the member mean's
  increments, spectrum or gradient unchanged. Running the default ladder through the
  broadcast lane (`fmeval/ladder.py`, lines 343 to 399: a non-ensemble operator is applied to
  each member, a stochastic one with an independent draw per member, and deterministic
  metrics score the member mean) is a configuration change, but it would yield little: in the
  mean of 16 members a noise operator acts with 1/16 of its variance, the impostor becomes the
  mean of 16 independent impostors and is no longer an impostor, and smoothing the member mean
  removes member noise the truth does not share. Only the deterministic operators would say
  anything, and that about white noise. It is not recommended below.
- Seven ensemble cards cite issue 111 (damage per change divides by round-off on dispersion
  axes). Thirteen cards skip Sod with "needs a periodic domain", which a wall-aware increment
  or derivative would lift (count not rechecked by the reviewer).

**H4. Statistics, cost, provenance and declarations.**
Rank-correlation intervals with the estimated block length (issue 042); the integrated
autocorrelation time beside every scatter statistic, since 161 frames hold 7 to 12 effective
samples (`METRIC_EVALUATION_CRITIQUE.md`); a spatial block bootstrap over tiles (issue 132);
an uncertainty on every metric value and test splits by trajectory
(`docs/ideas/evaluation_design.md`); comparable wall-clock costs (issue 125) and a grid-size
cost guard (issue 114); git state at run start (issue 115); the run seed reaching the
synthetic-ensemble reader (issue 044); a dataset's γ, Re and Ma in `ctx` (issue 022); metric
options from configuration (issue 049) and a declared dimensionality per metric (issue 117, the
3-D side of issue 005); a trusted solver and an adjoint (issues 069, 072), which are infrastructure rather than
experiments.

### 2.4 Where each logged source landed

| Logged source | Cluster |
|---|---|
| EXP-crps-gneiting-forecaster-suite | D6 |
| EXP-energy_distance-tail-only-degradation | G2 |
| EXP-energy_score-correlated-synthetic-ensemble | D6 |
| EXP-enstrophy-budget-closure-from-consecutive-states | G1 (data side also D1, D2) |
| EXP-increment_flatness-isotropic-3d-turbulence-cutouts | D4 |
| EXP-max_error-grid-convergence-with-a-known-solution | D5 |
| EXP-nrmse-rollouts-over-many-initial-conditions | D2 |
| EXP-orchestrator-20261023-anisotropic-blur | G5 |
| EXP-orchestrator-20261023-constraint-violation | G7 |
| EXP-orchestrator-20261023-dilatational-scaling | G6 |
| EXP-orchestrator-20261023-known-vortex-field | D7 (dataset form), G4 (degradation form) |
| EXP-orchestrator-20261023-temporal-ladder | G1, needs H1 |
| EXP-persistence_distance-spurious-feature-injection | G4 |
| EXP-persistence_distance-topological-simplification | G4 |
| EXP-shock_mask_overlap-geometric-and-perturbed-cases | D8 |
| EXP-shock_set_distance-2d-shock-dataset | D3 |
| EXP-sod_evidence-sod-time-offset | D8 |
| EXP-spectral_energy_flux-forced-2d-compressible-flux-loop | D4 (also D3's shocklet tier) |
| EXP-spectral_energy_flux-graded-phase-randomisation | G3 |
| EXP-spread_skill-heteroscedastic-synthetic-ensemble | D6 |
| EXP-spread_skill-perturbed-initial-condition-ensemble | D1 |
| EXP-tail_exceedance-base-period-climatology | D4 (data), H1 (harness) |
| EXP-tail_index-pareto-spike-injection | G2 |
| EXP-wasserstein-background-ratio-sweep | D9 |
| EXP-wasserstein-known-answer-transport | D9 |
| MTR-* "How it could be tested" sections (27 files) | D5, D7, D9, G4, G8, regime list, as cited above; the rest test the proposed metric on existing experiments |
| Degradation cards' Limitations (`additive_noise`, `gaussian_blur`, `translate`, `bias`, `spread_inflate`) | G10, D6 |
| Issue 001; `degradation_ladder_reference.md` | regime list (Re ≈ 500); ladder housekeeping (artificial viscosity) |
| Issues 004, 037, 132; judgement 001; `robustness.md` | D1 |
| Issues 078 to 081, 094; `baseline_predictors.md` | D2, G1, H1 |
| Issues 002, 016, 088, 120 | D3 |
| Issues 005, 085, 128 | D4 |
| Issue 126 | D5 |
| Issues 060, 073, 082, 086 | D7, G4 |
| Issue 051 | D8, G1 |
| Issues 047, 048, 066, 067 | D9 |
| Issues 051, 056, 084, 069 | G1 |
| Issues 013, 014, 015; `equivariance_tests.md` | G8, G4 (spike probe) |
| Issues 024, 057 | G6 |
| Issues 058, 075, 071 | G5 |
| Issues 070, 139 | G7 |
| Issues 097, 106; `CURVE_METRICS_CRITIQUE.md` line 460 | G9 |
| Issues 031, 041, 011 (blur list) | ladder housekeeping |
| Issues 094, 095 | H1 |
| Issues 096, 101, 016 | H2 |
| Issues 111, 104, 037 (anchor scale) | H3 |
| Issues 042, 044, 022, 049, 114, 115, 117, 125 | H4 |
| Issues 053, 087, 089, 090, 091 | regime data, no proposal |

Near-duplicates the proposals already mark with "see also" (tail-only and Pareto spikes) are
one cluster here. Three pairs that were not cross-referenced but are one job each: the
perturbed-initial-condition ensemble and the robustness experiment's solver half (D1); the
temporal ladder and the budget closure (G1); the known vortex field's degradation form and the
simplification operator (G4).

## 3. What to build: shared experiments ordered by reach per unit cost

"Reach" is how many of the 39 metrics the item changes the evidence for, counted against
the families in Section 3.4; "cost" is as the proposals state it. The order within each list
is my judgement **(mine)**.

### 3.1 Benchmarks and datasets

**B1. One production job on the kinet solver (D1 + D2 + G1's data side).**
Reach: 32 of 39 (not the 6 shock metrics, which need a stored pressure; not
`persistence_wasserstein`, held back from turbulence runs for cost). The ensemble metrics get
their first physical evidence; every other metric gets exchangeable realisations for its
damage anchor; thirteen cards get many initial conditions scored step by step; three get windowed budget
residuals.

Specification, following `EXP-spread_skill-perturbed-initial-condition-ensemble.md` with the
reviewer's corrections:
1. **Configuration.** The `kinet_re5e4` shear-layer problem as it stands (`λ = 80`,
   `ε = 0.05`, Re 5e4, Ma 0.1, 256²). Restart from a stored frame is feasible because
   `kinet_re5e4` stores the distribution functions.
2. **Members.** From each of three start states (the frames at solver steps 2 000, 5 000
   and 8 000 are my guess; the proposal says "several start times"), run 17 trajectories,
   **every one** from an independent small perturbation of the start state and **none
   unperturbed**, each run in turn the truth. An unperturbed truth breaks the exchangeability
   the known answer needs (D1). The decorrelation check of the proposal is then a statement
   about physical realism, not a condition for the known answer.
3. **Unrelated realisations.** Not from this configuration: the shear layer has no seed
   option and would likely roll up into the same vortex pair in the same place (D1). Use the
   three random-mode realisations already on disk (Section 1.3) and, if more are needed, that
   configuration with new seeds.
4. **Storage cadence.** Every 10th solver step for the first 1 000 steps of each member (the
   budget residual is a windowed quantity; one-step pairs do not close it, G1), then every
   50th to a horizon of 5 000 steps (the lead range `forecast_re5e4` already uses).
   Write only the fields the metrics read (density, velocity; vorticity is recomputed) unless
   the distribution functions are wanted for restarts.
5. **A third refinement level (mine).** One 128² run of the unperturbed reference from
   t = 0, to complete the 512²/256² pair already on disk (D5) and to serve as a coarse-grid
   candidate of known provenance (D2).
6. **Readers.** One reader that assembles members from separate run files into
   `Frame.members`; the forecast-pair reader generalised to many trajectories; a reader for
   the 512² shear-layer run.
7. **Known answer.** The exchangeable-ensemble relation of D1 at every lead time and in every
   spread bin.

Cost: 51 runs of 5 000 steps at 256² plus one 128² run. Storage, from the reviewer's file-size
measurement (kinet writes 34 float64 values per cell at its default output, 272 bytes per cell
per frame): the 51 runs hold about 9 200 frames of 256² (100 per run in the dense block, 80
more in the every-50th block), which is about 14 GB with density and velocity only and about
160 GB at the solver's default output (my arithmetic). No wall-clock is known;
one measured 256² run of 5 000 steps should be timed before the job is sized.

**B2. Forced two-dimensional compressible turbulence with a large-scale drag (D4 form a).**
Reach: the 8 spectral, increment and tail cards, the 6 shock cards (if pressure is stored),
the Helmholtz split, the energy-transfer checks, the base-period protocol, and every metric
as a second physical regime with shocklets.

Specification: doubly periodic; solenoidal white-in-time random force at a fixed wavenumber;
a linear large-scale drag so that the inverse cascade does not pile energy at the box scale
and a statistically steady state exists (Kritsuk's runs have none and his Case B is reported
as not stationary, D4); a turbulent Mach number of about 0.3 to 0.5, with shocklets reported
from about 0.25; store density, velocity and pressure (or the sound speed, so the Mach number
is readable); a base period and a disjoint evaluation period of several correlation times
each. Known answers: the flux loop (Kritsuk 2019, Sect. 3, Fig. 6), the cascade slopes
k^−5/3 and k^−3 on the two sides of the forcing scale (Boffetta and Ecke 2012, Eqs. 12 and 13,
incompressible), a non-trivial shock mask.

Cost: a new simulation. kinet runs supersonic compressible flow (the obstacle run at inlet
Mach 1.8), but whether it supports forcing and a drag term is unchecked. If it cannot, the
Johns Hopkins cutouts (D4 form b) give the inertial range but not the shocklets or two
dimensions.

**B3. The synthetic-ensemble family (D6).**
Reach: the 8 ensemble metrics, with published or closed-form answers, plus `wasserstein` on
an ensemble. Cost: seconds per run.
Specification: four reader options on `fmeval/data/synthetic_ensemble.py` (per-cell case
means drawn N(0, 1); a σ field varying by frame or region; noise as a Gaussian random field of
given correlation length, drawn with the impostor's spectral machinery once G3's per-channel
fix is in; a positive background so density stays positive) and seven ensemble operators
(four forecasters of Gneiting et al. 2007, Table 1; three flow-dependence operators; one
correlation-length redraw). The operators replace members rather than perturb them, so they
declare no `preserves`; the correlation redraw preserves per-cell variance only in
expectation, which the `preserves` vocabulary cannot yet say. Also pass the run seed to the
reader (issue 044) so several draws of the null can be taken.

**B4. A two-dimensional shock dataset (D3), in three tiers.**
Reach: the 6 shock cards, `persistence_distance`, the compressible flux, H2's first customer.
1. A Sedov–Taylor blast wave on 256² to 512² (my choice of a two-dimensional size; Schaal and
   Springel ran it in three dimensions): a closed front at a known radius, so a candidate at a
   shifted time or another resolution displaces every point by a known amount in every
   direction.
2. The two-dimensional Riemann configurations of Lax and Liu 1998, *SIAM J. Sci. Comput.*
   19(2), 319–340: a high-resolution run as reference, the same run at lower resolution or
   another scheme as candidate; outflow boundaries declared per axis.
3. Decaying compressible turbulence with eddy shocklets, the case issue 002 accepted on
   2026-08-07. B2 covers this tier if it is run.
Interim **(mine)**: readers for the on-disk supersonic obstacle flow and the two kinet Sod runs
(Section 1.3), once issue 046's wavenumber definition for non-square domains is settled, and
a boundary mapping for The Well's `turbulent_radiative_layer_2D`, which stores pressure.

**B5. One closed-form generator of fields with a known feature population (merging D7, D8(a) and D9(b)) (mine, with the reviewer).**
Reach: every family. The three fixtures the proposals ask for are one idea: a periodic smooth
random background of chosen spectrum plus a listed set of sharp features, each with its own
position, amplitude, width, orientation and count. One reader in the `ClosedFormTrajectory`
pattern of `fmeval/data/analytic.py` with feature types:
- **vortices** (Lamb–Oseen or Gaussian profile, to be cited) with known centres, radii and
  circulations, so the persistence diagram's point count and the vortex census are known;
- **fronts** (smoothed pressure jumps, straight, curved or closed) so the shock set is known,
  with candidates built by the intercomparison's displacement, size, rotation and amplitude
  errors;
- **bumps** of chosen height on a chosen background, so the transport distance under a
  translation and the background-ratio transition are known.
Every family then has an answer before the run: pointwise norms under a known shift, the
spectrum under a known width, increment tails from a known population, persistence diagrams
from known extrema, shock sets from known fronts, W₂ from a known translation. Seconds per
run. It is a fixture unless a decision admits it as evidence, as Sod was admitted.

**B6. Two more closed-form fixtures that do not fit the generator.**
1. **Sod at a shifted time** (D8(b)): the exact solution at t against t + dt for a ladder of
   dt; needs a decision between a trajectory-aware operator and a paired reader.
2. **Known-answer transport pairs** (D9(a)): the manufactured Monge–Ampère map and the circle
   profiles, as test fixtures in `tests/analytic_fields.py`, about twenty lines.

**B7. Readers for data already on disk (mine).**
Reach: varies; cost: a reader each, no simulation. In order of value: the 512² shear-layer
run beside `kinet_re5e4` (a two-level solver comparison of the reference, D5); the three
random-mode isotropic realisations (D1's unrelated realisations and an isotropic reference);
the four old Reynolds-ladder members (issue 011); a boundary mapping for The Well's
`turbulent_radiative_layer_2D` (two-dimensional, stores pressure) and three-dimensional
support for `rayleigh_taylor_instability` (issue 090) and `turbulent_radiative_layer_3D`
(issue 005); the kinet Sod and obstacle-flow runs (B4 interim); the acoustic dipole (G6's
known answer).

### 3.2 Degradations

Each is one bundle under `degradations/` built by the recipe in `AGENTS.md` §4, added to
`LADDERS` in `tests/test_degradation_contract.py` and to `TEST_DESCRIPTION.md`.

**X1. Spatially correlated noise (G10).** Reach: 32 (every metric that runs on kinet).
`family="stochastic"`, severity the amplitude as a fraction of the fluctuation rms (the same
scale as `additive_noise`), correlation length an option as a fraction of the characteristic
scale, drawn as a Gaussian random field with one phase per wavevector for all components of a
vector field. It is the realistic, spatially smooth form of error, and it is cheap.

**X2. Graded phase randomisation (G3).** Reach: 25 (non-shock, non-ensemble).
`family="stochastic"`, severity s in [0, 1], `preserves=("amplitude_spectrum", "spatial_mean")`,
`ordinal=True`, `stochastic=True`, no calibration; ladder severities 0.1, 0.25, 0.5, 0.75, 1.0
(mine). **First** fix the per-channel phase draw it would inherit from `gaussian_impostor`
(one phase per wavevector for all components) and open an issue against the impostor. Known
answer for third-order statistics: the exact per-triad product of G3 computed on the
reference, or "sinc(s)³ up to degenerate triads"; no prediction for `increment_flatness`.

**X3. The temporal ladder (G1) on H1.** Reach: all metrics once per-frame evidence can be
read along a window; the three budget metrics and eight ideas immediately. Three operators:
`time_lag` (severity d in frames), `time_smooth` (window w), and a `window` option on the
ladder that applies any existing operator with one draw to every frame of a window. The
budget residuals are windowed over about 100 steps with the reference's residual as the
floor. Needs the harness to pass a window of frames.

**X4. The tail family (G2).** Reach: the 6 distributional and tail cards, the POT tier.
`pareto_spikes`: option `a0` (multiple of the fluctuation rms); the spike fraction scales with
the grid, at least 2/√n (about 1.6e-2 at 128², 7.8e-3 at 256²; 1/√n suffices only with a
spike floor above the reference's largest increment, spec 09;
higher on clustered kinet increments); severity α decreasing (mine: 6, 5, 4.5, 4 for any
fourth-order statistic, continuing to 3 and 2 only for the Hill and exceedance metrics, since
flatness has no finite expectation at α ≤ 4). `tail_compress`: severity 1 − q for q = 0.999,
0.99, 0.95, 0.9, acting on cells above the reference's q-th increment quantile; must preserve
the spatial mean and periodicity, which needs a design choice between local smoothing and a
monotone compressive map above the threshold.

**X5. Feature add and remove (G4).** Reach: the 2 persistence cards, `max_error`, the feature
ideas. `spurious_features`: count fixed, depth h in rms units as severity, width in cells as an
option (width 1 is the single-cell spike probe of issue 013). `persistence_simplify`: severity
ε in rms units; known answer, bottleneck distance at most ε/2.

**X6. Anisotropic blur (G5).** Reach: the anisotropy ideas; a response axis, not a blind one,
for the isotropic summaries. Severity the width ratio (1, 2, 4, 8) with `calibration=None`
and `zero_is_identity=False`; the geometric-mean width resolved by the operator from `ctx` at
the `gaussian_blur` ladder's second level (mine); `preserves=("spatial_mean",)`.

**X7. The Helmholtz family (G6).** `scale_dilatational`, `whole_frame=True`, severity a
magnitude s in [0, 1] with an `amplify` option, as two ladder entries sharing one operator;
a signed severity in [−1, 1] would break the ladder's sorting of severities (spec 10). Periodic
only; and a `project_solenoidal` option on the five spectral operators. Known answers:
vorticity unchanged, kinetic energy E_s + λ²E_d, `mse` δ²E_d (spec 10, measured). The on-disk
acoustic dipole is not a known answer: it is a momentum source with nonzero curl (spec 10).

**X8. The admissibility family (G7).** `negative_excursion` (fraction of cells and depth),
`nonfinite_cells` (count; needs the finiteness check in `Trajectory.frame()` relaxed for this
operator only, a decision a person must take), `lognormal_noise` as the positivity-preserving
form of `multiplicative_noise`, and `bias` added to the Sod ladder.

**X9. Rotation, boost and the invariance audit (G8).** `rotate90` with vector components
rotated by the field's declared channel count; `galilean_boost` on velocity at |c|/u_rms of
0.1, 1 and 10; a probe configuration that transforms both fields and a renderer for the
invariance audit, the triangle-inequality scatter and the gradient norm against sub-pixel
displacement; a 45° rotation as a test fixture only.

**X10. Draws per severity (G9).** A ladder option `draws: n` that repeats each stochastic
entry with n generators and a `draw` column on the rows; the analysis reports the spread across
draws and the signal-to-noise ratio beside the elasticity. Multiplies the stochastic part of a
run's cost by n.

### 3.3 Tests and protocol changes

1. **A window of frames to a metric (H1)**, added with X3 as its first customer, and the
   series-level pooling contract of issue 095 in the same change.
2. **Several fields to one metric and a positive-field declaration (H2)**, added with B4, B2
   or the Well radiative layer as the first dataset that stores pressure.
3. **A budget unit test on `taylor_green_2d` (mine)**: pin the three single-field bundles'
   normalisations against dE/dt = −2νΩ, which holds exactly on that fixture, before any
   budget residual is read on real data.
4. **Configuration-only evidence fixes (H3)**: the curve companions tabulated on
   `forecast_re5e4`; `analysis_grid.resolution=256` on the `kinet_re1e6` run every card cites;
   damage per change measured on the member stack (issue 111). The default ladder on
   `synthetic_ensemble` is *not* recommended (H3).
5. **Statistics (H4)**: the estimated block length in the rank-correlation interval (issue
   042); the integrated autocorrelation time beside every scatter statistic; a spatial block
   bootstrap over tiles for the Hill interval (issue 132).

### 3.4 Coverage: which clusters serve which metric families

Filled from the clusters' own "Serves" lines. The family counts sum to 39.

| Metric family (count) | Serving clusters |
|---|---|
| Pointwise and gradient norms (10: mse, mae, rmse, rmse_channel_mean, nrmse, vrmse, max_error, max_error_channel_mean, h1_seminorm, h1_relative) | D1 (anchor), D2, D5, B5, G3, G4, G8, G9, G10 |
| Spectral (2: spectrum_l2, spectral_energy_flux) | D1 (anchor), D2, D4, G3 (blind axis), G5, G6, G8, G9, G10, H2, H3 |
| Increment, distributional, tail (6: increment_w1, increment_w1_by_separation, increment_flatness, energy_distance, tail_index, tail_exceedance) | D1, D4, B5, G2, G3, G5, G8, G9, G10, H1, H3 |
| Single-field physics (3: kinetic_energy, enstrophy, palinstrophy) | D1 (anchor), D2, G1, G6, G8, G9, G10, the Taylor–Green test |
| Transport (2: wasserstein, h_minus_one) | D1, D6 (positive variant), D9, B5, G3, G7, G8, G9, G10 |
| Topology (2: persistence_distance, persistence_wasserstein) | D1, D3, D7, B5, G3, G4, G8, G9, G10, compute (issue 144) |
| Shock geometry (6) | D3, D8, B5, G7 (bias), G8 (rotation), G9, H2; not D1, G3 or G10, which act on kinet data without pressure |
| Ensemble (8) | D1, D6, G9, G10 (on members), H3 (issue 111) |

Only G8 (the invariance probes) and G9 (draws per severity) appear in every row, because
they act on whatever data a metric already runs on. D1, G3 and G10 serve every family except
the shock metrics, which have no pressure field on kinet, and the generator B5 serves every
family except the ensemble metrics.

## Confidence

**Sure.** The catalog of logged wants covers the 25 EXP proposals in full, all 39 cards, every
research-notes and code-notes file, every judgement, every issue, the plan documents, the idea
pages the reviewer swept, the 27 MTR proposals' test sections and the degradation cards. The
mapping of proposals to clusters in Section 2.4 is unambiguous for 23 of 25 EXP proposals.
The following were verified by the reviewer against files, code or HDF5 reads, and I
re-checked the code claims myself: the per-channel phase loop in the impostor; the 512²
shear-layer run's config and existence; the random-mode run's three native grids and the fact
that its runs start from different fields; the Well reader's refusal of non-periodic axes and
which Well sets store pressure; the cards' citation of a 128² `kinet_re1e6` run against a
256² primary run; the calibration branch of `fmeval/ladder.py`; the obstacle flow's inlet
Mach number; kinet's 272 bytes per cell per frame; the Taylor–Green budget identity.

**Measured by the reviewer, not by me, with scripts kept in the session scratchpad:** the
initial-field correlations of the random-mode runs; the one-step budget's failure to close on
`kinet_re5e4`; the Pareto spike fraction needed for the Hill target; the exact-triad and
Monte Carlo departures from sinc(s)³; the impostor's 0.228 dilatational fraction.

**Less sure.** Card counts ("13 cards name the many-initial-condition experiment") come from a sweep of card text;
the reviewer confirmed the counts for that experiment, the cutouts, tail-only axis, grid convergence,
forecaster suite, perturbed ensemble and issue 111, and did not re-check the Sod-skip and
curve-companion counts. The factor of N + 1 for an unperturbed truth is a derivation for the
linear regime, not a simulation. The claim that a seeded shear layer would not decorrelate is
reasoning. The acoustic mechanism behind the one-step budget scatter is a conjecture. The
Pareto fraction was simulated on a synthetic field, not on kinet increments. Literature verdicts (Kritsuk's venue and Mach numbers,
Leutbecher and Palmer's equations, Engquist and Yang's theorem, Edelsbrunner et al.'s
definition, Schaal and Springel's and Lee et al.'s dimensionality) are the reviewer's
sub-agent's reading of the primary sources; the Ahijevych table numbers and Delon et al.'s
section remain unchecked.

**My additions, not logged by any agent.** Section 1.3 (with the reviewer's corrections);
the merging of D1 and D2 into one production job (B1) and its cadence and start states; the
coarse-grid candidate; the generator B5 and the Taylor–Green test (both with the reviewer);
B7; the ordering in Section 3; the ladder severities suggested for X2, X4 and X6.

**Open decisions only a person can take**, as the proposals state them: whether the kinet
solver supports forcing and a drag (B2) and a manufactured source term (D5); whether the Sod
time offset is a trajectory-aware operator or a paired reader (B6); whether a deliberately
non-finite prediction may pass `Trajectory.frame()` (X8); the vortex profile and its citation
(B5); the compute allocation for `persistence_wasserstein` on the 256² ladders (issue 144);
whether a closed-form dataset such as B5 is admitted as evidence, as Sod was; and whether to
generate a Re ≈ 500 reference or amend the protocol (issue 001).

## Connections

The clusters map onto the organising principles already in `CLAUDE.md`. G3 (phase) and G4
(features) are the two sides of the smooth-versus-sharp split: phase coherence is what the
sharp part carries and the Gaussian impostor lacks, and feature injection or removal is the
sharp part changing while the smooth part stays. G6 is the Helmholtz instance of the same
split, and the impostor's divergence defect is what happens when a phase operator ignores
it. The weather-verification lineage the repository imports (double penalty, SAL, MODE, FSS)
supplies D8's geometric cases and D6's forecaster suite directly; G1's time lag is the
temporal analogue of the spatial double penalty; and the exchangeability requirement in D1 is
why weather centres verify ensembles against an independent analysis rather than their own
control run. The seismic cycle-skipping lineage is D9: the background-ratio sweep is the known
transition where transport stops behaving like a pointwise norm. The one-step budget failure
in G1 is the familiar difficulty of reading dissipation from instantaneous energy in a weakly
compressible solver, where acoustic energy is exchanged faster than viscosity drains it, and
averaging over many acoustic periods is the standard remedy. B1 is also the data on which the
protocol's degraded Boltzmann solver runs (`CLAUDE.md`, "Evaluation protocol", steps 1 and 2)
would be scored.
