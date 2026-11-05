# Choosing a metric

This page helps you find the metrics that measure the failure you care about, and tells you
where to read about each one. It does not rank them. A metric that misses one failure usually
catches another, so the page says what each group of metrics sees and what it misses, and
leaves the choice to your question
([there is no pass or fail](https://github.com/khegazy/pde_metrics/blob/main/docs/decisions.md#there-is-no-pass-or-fail)).

Two words are used in two senses here. A **research field** is the community a metric comes
from, such as the machine-learning benchmarks for PDEs or ensemble weather verification. A
**physical field** is one quantity over the domain, such as density or vorticity
([glossary](glossary.md)).

This page quotes no measured number. The metric pages are regenerated from new runs, and a
number copied here would go stale. Every comparison it mentions is on the pages it links.

## Read a metric the way its own field reads it, then compare

Every metric here is evaluated in a fixed order
([`AGENTS.md`](https://github.com/khegazy/pde_metrics/blob/main/AGENTS.md) §1, "How every
metric is evaluated"), and its page is read in the same order.

1. **First, as its own research field evaluates it.**
    - *Where:* the subsection *How its field reports it*, at the end of the metric page's
      Definition, and the first figure under Performance where the field's figure can be drawn.
    - *What it says:* which field the metric comes from; the object that field computes and how
      it normalises it; the figure it draws; the statistics it reports beside the number; and
      the experiment it tests the metric on, each with a citation.
    - *When fields disagree:* each field's form is its own metric with its own page, and the
      subsection names the sibling. If you come from one of those fields, start from the
      metric that is your field's standard; the groups below name it.
2. **Then, beside the other metrics.**
    - *Compared with the other metrics*, under Results: the rank correlation with every other
      metric, one column per physical field, across the degradations. A value near 1 means two
      metrics order the damage alike and are redundant for ranking models. It does not make
      them interchangeable as training losses, because they may weight the same damage very
      differently.
    - *Damage beside the other metrics*: the metric's damage against an applied shift, beside
      the pointwise controls.
    - [Sensitivity at a glance](sensitivity.md): every metric on the same figures.
3. **Last, check what it was run on.** *Across the experiments*, at the top of Results, and the
   [coverage page](coverage.md) say which experiments the page cites, which cannot apply and
   why, and which proposed experiments name the metric. The experiments are the degradation
   ladder on the developed flow `kinet_re5e4`, the same flow at a higher Reynolds number
   `kinet_re1e6`, the real forecasts `forecast_re5e4`, the Sod shock tube `sod_shock_tube` and
   the synthetic ensemble `synthetic_ensemble` ([datasets](datasets/README.md)).

Full references, with equation, section and figure numbers, are on each metric's page; this
page names the source of each standard and links it.

## Start from the failure you care about

| What you need to detect | Group | Research fields whose standard is built here |
|---|---|---|
| A wrong value at each point: damping, noise, bias, lost detail | [Pointwise errors](#pointwise-errors) | machine-learning benchmarks for PDEs; numerical analysis; weather verification |
| Error weighted by scale, or a displacement charged by how far it moved | [Sobolev and transport norms](#sobolev-and-transport-norms) | finite-element analysis; neural-operator learning; optimal transport; seismic inversion |
| Energy at the wrong scales, or moving between scales at the wrong rate | [Spectra and fluxes](#spectra-and-fluxes) | turbulence; machine-learned surrogates of flows and weather |
| Sharp events of the wrong size or frequency, wherever they sit | [Increment statistics and tails](#increment-statistics-and-tails) | turbulence; statistics; extreme-value statistics; forecast verification |
| The wrong total energy, enstrophy or sharpness of a flow | [Integrals of one field](#integrals-of-one-field) | turbulence; learned turbulence models |
| Features such as vortices of the wrong strength or number | [Topology](#topology) | topological data analysis |
| A shock in the wrong place, missing, or spurious | [Shocks](#shocks) | shock detection in computational fluid dynamics; medical image segmentation; spatial forecast verification |
| An ensemble whose spread or calibration is wrong | [Ensemble verification](#ensemble-verification) | probabilistic forecast verification |

The **double penalty** ([glossary](glossary.md)) is the reason this repository exists: a sharp
feature of the right shape in slightly the wrong place is charged twice by a comparison made
one cell at a time. The groups meet it in three ways. The pointwise errors suffer it. The
transport norms are built to charge a displaced feature by how far it moved, though a large
mean value weakens that (`wasserstein`'s Limitations), and the shock-set distances measure how
far a shock moved. The increment statistics, spectra, integrals and topology avoid it by
ignoring position altogether, which is also their blind spot.

## Pointwise errors

[mse](metrics/mse.md), [rmse](metrics/rmse.md), [mae](metrics/mae.md),
[max_error](metrics/max_error.md), [rmse_channel_mean](metrics/rmse_channel_mean.md),
[max_error_channel_mean](metrics/max_error_channel_mean.md), [nrmse](metrics/nrmse.md),
[vrmse](metrics/vrmse.md).

**What they see and miss.** Each compares the two fields cell by cell, so each sees every error
of amplitude and none of position: a feature one cell from its place is charged as a miss and a
false alarm. They differ in how they weigh an error.

- `mse` and `rmse` order any set of predictions identically, since a square root cannot
  reorder. Ranking by them selects for smoothness, which is why regression losses give blurry
  predictions (`mse`'s Limitations).
- `mae` responds to a small displacement in proportion to it rather than to its square, so it
  is more sensitive to sub-cell shifts, and a single badly wrong region weighs no more than the
  same error spread thinly.
- `max_error` reports the worst single cell, and shows the double penalty in its most extreme
  form: once a sharp front is misplaced by a cell or two, it no longer tells a near miss from a
  gross one.
- `nrmse` and `vrmse` carry no units, so they can be read across physical fields; the others
  carry the field's own units. `nrmse` divides by the reference's root mean square, so on a
  field with a large mean, such as density, it is compressed towards zero. `vrmse` divides by
  the reference's standard deviation and hides the absolute size of the error.
- The two `_channel_mean` metrics average over the components of a vector field after
  reducing each, as the benchmarks do. On a one-component field they equal `rmse` and
  `max_error`.

**Where each research field's standard lives.**

- **Machine-learning benchmarks for PDEs.** PDEBench
  ([Takamoto et al. 2022](https://doi.org/10.52202/068431-0117)) tabulates
  `nrmse`, `rmse_channel_mean` and `max_error_channel_mean` per PDE and model; its curve of
  error against the unrolled time step pools the channels, which is `rmse`. The Well
  ([Ohana et al. 2024](https://doi.org/10.52202/079017-1430)) reports `vrmse` as its headline
  number and trains its baselines on `mse`. No benchmark read reports `mae`; The Well's library
  defines it but leaves it out of its reported suite.
- **Numerical analysis and code verification**
  ([Roy 2005](https://doi.org/10.1016/j.jcp.2004.10.036)) uses the discrete L2 and L-infinity
  norms of the error, `rmse` and `max_error` on one variable, drawn against the grid spacing to
  read off the observed order of accuracy.
- **Weather verification** (WeatherBench 2,
  [Rasp et al. 2024](https://doi.org/10.1029/2023MS004019)) reports the RMSE of each variable
  against lead time; `rmse`'s page sets out how its vector form differs.

**Experiments.** The research fields test these on rollouts from many initial conditions and on
grid refinement against a known solution. Neither exists here:
[EXP-nrmse-rollouts-over-many-initial-conditions](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-nrmse-rollouts-over-many-initial-conditions.md)
and
[EXP-max_error-grid-convergence-with-a-known-solution](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-max_error-grid-convergence-with-a-known-solution.md)
write them up. The nearest is `forecast_re5e4`, one model's error against lead time from two
starting times; its three runs at different resolutions are not a refinement sequence
([issue 126](https://github.com/khegazy/pde_metrics/blob/main/issues/126-forecast-runs-as-a-refinement-sequence.md)).
These metrics need nothing but two fields on one grid, so they also run on the degradation
ladder, the Reynolds ladder, Sod and the member mean of the synthetic ensemble; the two
`_channel_mean` metrics skip the datasets whose fields all have one component.

## Sobolev and transport norms

[h1_seminorm](metrics/h1_seminorm.md), [h1_relative](metrics/h1_relative.md),
[h_minus_one](metrics/h_minus_one.md), [wasserstein](metrics/wasserstein.md).

**What they see and miss.** A Sobolev norm weights the error at each scale. The two H1 norms add
the error's gradient, so they charge small-scale error more than a pointwise norm does;
`h1_seminorm`'s page shows it at its worst on a small displacement. `h1_relative` takes
its slope term from centred differences, which leave an error alternating from cell to cell
uncharged there. `h_minus_one` divides each mode by its wavenumber, so it charges small-scale
error less, and an offset uniform over the domain is invisible to it. `wasserstein` measures
how far the reference's mass must move to become the candidate's; it runs on density only,
divides both fields by their own mean, and so cannot see a wrong total mass. On a density whose
values stay close to their mean the two transport metrics are close to each other; read
*Compared with the other metrics* on either page before using both.

**Where each research field's standard lives.**

- **Finite-element analysis** reports the absolute H1 seminorm of the error against mesh size:
  `h1_seminorm`.
- **Neural-operator learning** reports a relative H1 error that also includes the value term,
  as the neuraloperator library computes it: `h1_relative`. Its plain relative L2 counterpart,
  in PDEBench's per-channel form, is `nrmse`.
- **Optimal transport** uses the H^-1 distance as the linearisation of the quadratic
  Wasserstein distance ([Peyre 2018](https://doi.org/10.1051/cocv/2017050), Theorem 1), so
  `h_minus_one`'s check is the comparison with `wasserstein` on the same density.
- **Seismic inversion** draws the misfit against the shift of a signal
  ([Engquist and Froese 2014](https://doi.org/10.4310/CMS.2014.v12.n5.a7), Fig. 1). That is the
  first figure on `wasserstein`'s and `h_minus_one`'s pages. Numerical optimal transport checks
  a solver against a known transport
  ([Saumier et al. 2015](https://doi.org/10.1093/imamat/hxt032)).

**Experiments.** The misfit against shift is drawn from the translation axes of the
degradation ladder, the one research-field experiment of this group that exists here. Missing:
refinement against a known solution for the H1 norms (the proposal above), a transport with a
closed-form answer
([EXP-wasserstein-known-answer-transport](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-wasserstein-known-answer-transport.md)),
and a density whose fluctuation is not small against its mean, where the two transport metrics
separate
([EXP-wasserstein-background-ratio-sweep](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-wasserstein-background-ratio-sweep.md)).
All four also run on the forecasts and the Reynolds ladder; none runs on Sod, whose walls rule
out a periodic domain.

## Spectra and fluxes

[spectrum_l2](metrics/spectrum_l2.md), [spectral_energy_flux](metrics/spectral_energy_flux.md).

**What they see and miss.** `spectrum_l2` compares how energy is spread over scales and discards
phase, so a translated copy and the fake prediction with the right spectrum and scrambled phases
both score zero; read alone it would approve a useless model. `spectral_energy_flux` compares
how fast the nonlinear term moves energy across scales, on velocity only. It is not the full
compressible flux: it leaves out density weighting and the exchange with internal energy
([judgement 003](https://github.com/khegazy/pde_metrics/blob/main/judgements/003-spectral-flux-from-velocity-alone.md)).

**Where each research field's standard lives.**

- **Turbulence** draws the energy spectrum on log-log axes with the expected power laws, and
  the flux against wavenumber on a logarithmic axis with its zero line, reading off a plateau
  and its sign ([Boffetta and Ecke 2012](https://doi.org/10.1146/annurev-fluid-120710-101240);
  [Alexakis and Biferale 2018](https://doi.org/10.1016/j.physrep.2018.08.001)). It does not
  reduce two curves to one number.
- **Machine-learned surrogates** draw the prediction's spectrum over the reference's
  ([Kochkov et al. 2021](https://doi.org/10.1073/pnas.2101784118); Rasp et al. 2024), and
  where they report a number it takes one of several forms.

Both metrics store the curve, the field's object, and draw it as the field does. The single
number each registers, a relative distance between two curves, is this repository's convention
([issue 136](https://github.com/khegazy/pde_metrics/blob/main/issues/136-spectrum-l2-linear-summary-is-a-convention.md),
[issue 105](https://github.com/khegazy/pde_metrics/blob/main/issues/105-spectral-energy-flux-summary-is-a-convention.md)).

**Experiments.** The research field's experiment is forced, statistically stationary turbulence
with an inertial range; `kinet_re5e4` is unforced and decaying. Missing:
[EXP-spectral_energy_flux-forced-2d-compressible-flux-loop](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-spectral_energy_flux-forced-2d-compressible-flux-loop.md)
and
[EXP-increment_flatness-isotropic-3d-turbulence-cutouts](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-increment_flatness-isotropic-3d-turbulence-cutouts.md).
Both metrics run on the degradation ladder, the forecasts and the Reynolds ladder, and not on
Sod, whose walls rule out a periodic transform.

## Increment statistics and tails

[increment_flatness](metrics/increment_flatness.md), [increment_w1](metrics/increment_w1.md),
[increment_w1_by_separation](metrics/increment_w1_by_separation.md),
[energy_distance](metrics/energy_distance.md), [tail_index](metrics/tail_index.md),
[tail_exceedance](metrics/tail_exceedance.md).

**What they see and miss.** Each reads the distribution of differences between neighbouring
cells (increments), which carries the sharp structures of a flow, and ignores where those
differences sit. A prediction with every structure in the wrong place, or offset by a constant,
can score perfectly, so each must be read beside a metric that sees position. Within the group:

- `increment_flatness` is one number for a whole distribution; a field that has lost its real
  sharp structures and gained spurious noise can land back on the reference's value.
- `increment_w1` and `energy_distance` compare whole distributions. `energy_distance` is weak
  exactly where intermittency lives, in the rare extreme increments.
- `increment_w1_by_separation` reads the same comparison at every octave of separation, as a
  curve.
- `tail_index` assumes a power-law tail and independent samples, neither guaranteed here.
- `tail_exceedance` counts extreme increments against the reference's; under smoothing it
  reaches zero and stops telling strengths apart.

**Where each research field's standard lives.**

- **The statistical theory of turbulence** measures intermittency by the flatness of
  longitudinal velocity increments against separation: `increment_flatness`, whose page draws
  that curve. The one source read that compares a model's increment distributions with a
  reference's uses a Jeffreys distance at octave separations
  ([Granero-Belinchón and Cabeza Gallucci 2024](https://doi.org/10.1088/2632-2153/ad43b3));
  the nearest built form is `increment_w1_by_separation`, and the Jeffreys distance itself is
  not built.
- **Statistics** reports the energy distance as a two-sample test
  ([Székely and Rizzo 2013](https://doi.org/10.1016/j.jspi.2013.03.018)); `energy_distance`
  reports the distance without the test, because the increments of one field are not
  independent samples.
- **Extreme-value statistics** reads the Hill estimate off the Hill plot
  ([Drees, de Haan and Resnick 2000](https://doi.org/10.1214/aos/1016120372)): `tail_index`,
  whose page draws both the classical and the alternative plot.
- **Forecast verification** reports the frequency bias against threshold: `tail_exceedance`.
  The score it is reported beside for rare events is not built
  ([MTR-tail_exceedance-paired-extreme-events](https://github.com/khegazy/pde_metrics/blob/main/proposals/MTR-tail_exceedance-paired-extreme-events.md)).

**Experiments.** The research fields' experiments are stationary turbulence with an inertial
range, samples with a known tail and long records with a base period. None exists here:
[EXP-increment_flatness-isotropic-3d-turbulence-cutouts](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-increment_flatness-isotropic-3d-turbulence-cutouts.md),
[EXP-energy_distance-tail-only-degradation](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-energy_distance-tail-only-degradation.md),
[EXP-tail_index-pareto-spike-injection](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-tail_index-pareto-spike-injection.md)
and
[EXP-tail_exceedance-base-period-climatology](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-tail_exceedance-base-period-climatology.md).
Separations are counted in cells, because `kinet_re5e4` has no established inertial range to
measure them in. The group runs on the degradation ladder, the forecasts and the Reynolds
ladder; not on Sod, whose walls rule out a periodic increment, nor on the synthetic ensemble,
for the reason each page gives.

## Integrals of one field

[kinetic_energy](metrics/kinetic_energy.md), [enstrophy](metrics/enstrophy.md),
[palinstrophy](metrics/palinstrophy.md).

**What they see and miss.** Each is one number computed from the prediction alone: the energy
of the velocity, the mean squared vorticity, and the mean squared vorticity gradient. Enormously
many wrong flows share any one value, so a match is no evidence of a good prediction; these are
alarms, never read alone. Enstrophy and palinstrophy live at the smallest resolved scales, so
they fall on a coarser grid without any physical loss.

**Where each research field's standard lives.**

- **Turbulence theory** reads each as a time series and as a term of the decay budget, energy
  falling at a rate set by enstrophy, and enstrophy at a rate set by palinstrophy
  ([Boffetta and Ecke 2012](https://doi.org/10.1146/annurev-fluid-120710-101240), Eqs. (5) and
  (6)).
- **Learned turbulence models** draw the energy and enstrophy of a rollout against time over the
  reference simulation's curve
  ([Frezat et al. 2022](https://doi.org/10.1029/2022MS003124);
  [List et al. 2022](https://doi.org/10.1017/jfm.2022.738)). That is the first figure on each
  page. The relative error of the integral at each time, which the pages report, is this
  repository's reading of those curves.

**Experiments.** On `forecast_re5e4` the first figure is the field's figure exactly, the
prediction's value beside its target's at each prediction step. Missing: the budget closure,
which needs consecutive states of a predicted trajectory
([EXP-enstrophy-budget-closure-from-consecutive-states](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-enstrophy-budget-closure-from-consecutive-states.md)),
and rollouts from many initial conditions. All three also run on the degradation ladder and
the Reynolds ladder; `kinetic_energy` also runs on Sod's one-dimensional velocity.

## Topology

[persistence_distance](metrics/persistence_distance.md),
[persistence_wasserstein](metrics/persistence_wasserstein.md).

**What they see and miss.** Both compare the persistence diagrams of the two fields: at which
levels their connected pieces and loops appear and disappear, a record of how many features
there are and how strong. Position is invisible, so any rearrangement that keeps that record,
such as a translation by whole cells, scores zero. `persistence_distance`, the bottleneck
distance, is set by the single worst-matched feature. `persistence_wasserstein` sums over every
feature, so many faint ones from noise can outweigh one strong one missing.
`persistence_wasserstein`'s page recommends reading the two together. Both run on density and vorticity.

**Where each research field's standard lives.** **Topological data analysis** uses both
distances
([Cohen-Steiner et al. 2007](https://doi.org/10.1007/s00454-006-1276-5);
[Cohen-Steiner et al. 2010](https://doi.org/10.1007/s10208-010-9060-6)), draws the persistence
diagram itself, which is the first figure on both pages, and reports beside the number a
stability theorem bounding it by the change in the field.

**Experiments.** The stability theorems concern perturbed fields, which are the noise and
smoothing axes of the degradation ladder. `persistence_distance` runs on that ladder, the
forecasts and the Reynolds ladder. `persistence_wasserstein` runs only on the forecasts, on a 64
by 64 grid: it is held back from both turbulence ladders because it is too slow there for now
([issue 144](https://github.com/khegazy/pde_metrics/blob/main/issues/144-persistence-wasserstein-too-slow-on-turbulence-runs.md)).
Missing: fields with a known population of features, and features added or
removed by a known amount
([EXP-orchestrator-20261023-known-vortex-field](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-orchestrator-20261023-known-vortex-field.md),
[EXP-persistence_distance-spurious-feature-injection](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-persistence_distance-spurious-feature-injection.md),
[EXP-persistence_distance-topological-simplification](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-persistence_distance-topological-simplification.md)).

## Shocks

[shock_set_distance](metrics/shock_set_distance.md),
[shock_set_hausdorff](metrics/shock_set_hausdorff.md),
[shock_set_hausdorff95](metrics/shock_set_hausdorff95.md),
[shock_set_masd](metrics/shock_set_masd.md),
[shock_set_baddeley_delta](metrics/shock_set_baddeley_delta.md),
[shock_mask_overlap](metrics/shock_mask_overlap.md).

**What they see and miss.** All six run one detector on each pressure field, which marks the
cells across which the pressure jumps by at least as much as across a shock of Mach number
1.3, and then compare the two marked
sets. The distances say how far apart the shocks are; the overlap says how many shocked cells
the two share. A shock smeared over more than a few cells is not detected. Within the group:

- `shock_mask_overlap` gives the same value to a shock two cells off as to one far away.
- `shock_set_hausdorff` is set by a single cell, so one false detection anywhere replaces the
  true shock's distance.
- `shock_set_masd` gives many false shocks and a few the same weight if they lie at the same
  mean distance.
- `shock_set_baddeley_delta` averages over every cell, so the size of the domain enters its
  value.

**Where each research field's standard lives.**

- **Shock detection in computational fluid dynamics** validates a detector against the exact
  shock position ([Schaal and Springel 2015](https://doi.org/10.1093/mnras/stu2386)), not by a
  distance between two detected sets. Its one-dimensional form, the pressure line-out with the
  detected cells over the reference's, is the first figure on `shock_set_distance`'s page.
- **Medical image segmentation** reports an overlap score beside a boundary distance
  ([Taha and Hanbury 2015](https://doi.org/10.1186/s12880-015-0068-x); Metrics Reloaded,
  [Maier-Hein et al. 2024](https://doi.org/10.1038/s41592-023-02151-z)). The overlap is the
  Dice coefficient, `shock_mask_overlap`. The boundary distances are the average symmetric
  surface distance, `shock_set_distance`; the Hausdorff distance, `shock_set_hausdorff`, which
  Taha and Hanbury advise against using directly; its 95th percentile, `shock_set_hausdorff95`;
  and Metrics Reloaded's recommended mean average surface distance, `shock_set_masd`.
- **Spatial forecast verification** uses Baddeley's Delta as a displacement metric for
  thresholded fields ([Gilleland 2011](https://doi.org/10.1175/WAF-D-10-05061.1)):
  `shock_set_baddeley_delta`. Its neighbourhood and categorical scores are not built, because on
  one one-dimensional shock they would say nothing these do not (the pages' reasoning, not a
  measurement)
  ([MTR-shock_mask_overlap-fractions-skill-score](https://github.com/khegazy/pde_metrics/blob/main/proposals/MTR-shock_mask_overlap-fractions-skill-score.md)).

**Experiments.** The group needs pressure, so it runs only on `sod_shock_tube`: an analytic
check of how a metric scores one known shock, which says nothing about turbulence. Missing: a
two-dimensional dataset with many shocks, the case this repository is aimed at
([issue 002](https://github.com/khegazy/pde_metrics/blob/main/issues/002-shocklet-dataset.md);
[EXP-shock_set_distance-2d-shock-dataset](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-shock_set_distance-2d-shock-dataset.md)),
the segmentation field's geometric and perturbed test cases
([EXP-shock_mask_overlap-geometric-and-perturbed-cases](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-shock_mask_overlap-geometric-and-perturbed-cases.md)),
and a shock displaced by a physically consistent amount
([EXP-sod_evidence-sod-time-offset](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-sod_evidence-sod-time-offset.md)).

## Ensemble verification

[crps](metrics/crps.md), [crps_skill_score](metrics/crps_skill_score.md),
[energy_score](metrics/energy_score.md), [variogram_score](metrics/variogram_score.md),
[spread_skill](metrics/spread_skill.md), [rank_histogram](metrics/rank_histogram.md),
[rank_histogram_chi2](metrics/rank_histogram_chi2.md),
[ensemble_mean_rmse](metrics/ensemble_mean_rmse.md).

**What they see and miss.** These score a prediction made of several members against one
reference. They need an ensemble, so they do not apply to a single prediction.

- `crps` scores each cell's spread of members against the reference value. It is dominated by
  the bulk of the field and, being cell by cell, suffers the double penalty.
- `energy_score` and `variogram_score` score the whole field as one vector. The energy score can
  hardly tell a forecast with the right spatial correlation from one with the wrong correlation;
  the variogram score was introduced to see it, but cannot see a bias common to every cell.
- `spread_skill`, `rank_histogram` and `rank_histogram_chi2` say whether the spread is honest,
  and nothing about accuracy: members all wrong in the same way, honestly spread, read as
  calibrated. The rank histogram's two summaries do not say which way the ensemble is wrong;
  `spread_skill`'s ratio does.
- `ensemble_mean_rmse` scores the members' mean and ignores the spread. On the data that exists
  it equals `rmse` exactly; it is kept because ensemble verification reports it by this name.

**Where each research field's standard lives.** All come from **probabilistic forecast
verification**.

- The mean score that ranks forecasters is `crps` in its fair ensemble form
  ([Gneiting and Raftery 2007](https://doi.org/10.1198/016214506000001437);
  [Ferro 2014](https://doi.org/10.1002/qj.2270)). Its skill against climatology is
  `crps_skill_score`, which Gneiting and Raftery note is generally improper, so ranking uses
  the mean score.
- For a whole field: `energy_score`
  ([Gneiting et al. 2008](https://doi.org/10.1007/s11749-008-0114-x)) and `variogram_score`
  ([Scheuerer and Hamill 2015](https://doi.org/10.1175/MWR-D-14-00269.1)). Both depart from that
  practice in scoring thousands of cells as one vector, where the sources score small vectors;
  their pages say how.
- For calibration: the rank histogram itself, drawn on `rank_histogram`'s page with its
  reliability index ([Delle Monache et al. 2006](https://doi.org/10.1029/2005JD006917)); the
  chi-square statistic of the same histogram, `rank_histogram_chi2`
  ([Hamill 2001](https://doi.org/10.1175/1520-0493%282001%29129%3C0550:IORHFV%3E2.0.CO;2)); and
  the spread against the error of the ensemble mean, `spread_skill` and `ensemble_mean_rmse`
  ([Fortin et al. 2014](https://doi.org/10.1175/JHM-D-14-0008.1)).

**Experiments.** The only ensemble here is `synthetic_ensemble`: a calibrated null with a
miscalibration ladder, whose dispersion is the same at every cell, whose cells are independent,
and whose frames are not lead times. So the field's standard figures, a score against lead time
and the binned spread-error diagram, cannot be drawn honestly, and no difference in spatial
correlation exists for the whole-field scores to detect. Missing: real ensembles
([issue 004](https://github.com/khegazy/pde_metrics/blob/main/issues/004-independent-realizations.md)),
[EXP-spread_skill-perturbed-initial-condition-ensemble](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-spread_skill-perturbed-initial-condition-ensemble.md),
[EXP-spread_skill-heteroscedastic-synthetic-ensemble](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-spread_skill-heteroscedastic-synthetic-ensemble.md),
[EXP-crps-gneiting-forecaster-suite](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-crps-gneiting-forecaster-suite.md)
and
[EXP-energy_score-correlated-synthetic-ensemble](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-energy_score-correlated-synthetic-ensemble.md).
On the synthetic ensemble every two-field metric of the other groups scores the members' mean.

## Using several metrics together

Two metrics belong in one panel when each sees something the other misses. The pages name
these pairings in their Limitations:

- A metric blind to position (the increment statistics and tails, the spectra, the integrals,
  topology) beside one that sees it, such as a pointwise error or a transport norm.
- `h_minus_one` and `wasserstein` beside a metric that sees the mean or the amplitude.
- `shock_mask_overlap` beside `shock_set_distance`, which says how far a missed shock is.
- `persistence_distance` beside `persistence_wasserstein`: one feature against all of them.
- `spread_skill` and the rank histogram beside `crps` or `ensemble_mean_rmse`, which see
  accuracy; `energy_score` and `variogram_score` beside `crps`, as their sources advise.

Two metrics whose rank correlation is near 1 under *Compared with the other metrics* order the
damage alike; a panel holding both adds cost without adding information about which model is
better. The case for keeping both must then rest on something else, such as a different
response to small displacements on *Damage beside the other metrics*, or use as a training
loss. The *Trap tests* subsection of a page measured on the degradation ladder shows how the
metric scores the fake prediction with the right spectrum and scrambled phases
([gaussian_impostor](degradations/gaussian_impostor.md)); a metric that scores it well is blind
to phase and must not be used alone.

Metrics that are planned but not built, including further position-tolerant ones, are listed
under [ideas not yet built](ideas/README.md).
