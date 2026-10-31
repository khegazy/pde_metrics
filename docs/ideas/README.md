# Ideas: metrics not yet built

This section is the team's plan for metrics that do not exist in the repository yet. Each
idea has its own page saying what the metric would measure, where the idea comes from in the
literature, what is known to go wrong with it, and why it is worth building. Nothing here has
been implemented or measured. The [catalogue](../catalogue.md) is the record of every metric
that has been built, and a metric's own page is the only place its behaviour is described.

Two pages explain the reasoning behind the ideas rather than any one idea:
[why single metrics are not enough](background.md) covers the ways a pointwise or spectral
metric can rate a physically wrong prediction well, and
[designing an evaluation](evaluation_design.md) covers how metrics are described, grouped by
regime, protected from data leakage and combined.

## How this section is kept

- **This page lists only work that is not built.** Every row of the table below has a page,
  and every page has a row.
- **Built means removed.** Whoever implements an idea deletes its row here, its page, and its
  link on the theme page, in the same change that adds the metric. If the metric covers only
  part of an idea, the row and page are narrowed to what remains. A theme left with no ideas
  is deleted.
- **Owner** names whoever is working on an idea. An empty cell means nobody has started it.
- **No measured numbers appear here.** A claim on an idea page is a citation to published
  work, a derivation shown on the page, or labelled with where it came from: the team's
  judgement, the field guide, an addition made during conversion or review, or an addition by
  an agent that built a related metric, named and dated.

## Columns

- **Gap** says what currently blocks the idea. *Math* means a mathematical question must be
  settled first, such as how to compare signed fields with a transport distance.
  *Implementation* means the mathematics is settled and only code is missing. *Both* means
  both, and *none* means neither. A linked issue says what else blocks the idea, such as an
  open question, a missing dataset, library or experiment, or another metric it builds on;
  the idea is not built until that issue is resolved.
- **Cost** is a rough estimate of the effort and compute needed to build and run it.
- **Priority** is the team's decision about what to build next. It is a planning choice
  rather than a judgement of the metric, and it is dropped once the idea is built.
  - **High** means there is strong precedent in another field facing the same problem, mature
    software exists, and the metric targets a failure that a pointwise norm provably misses.
    Build these first.
  - **Medium** means the idea is plausible, but the precedent is indirect, the implementation
    is nontrivial, or it may duplicate what another metric already gives. Build these after
    the high-priority ones.
  - **Low** means the theory is immature, the tooling is research grade, or the quantity is
    too indirect to serve as a routine diagnostic soon. Park these, and revisit one if a
    built metric fails in a way it would explain.
  - **Unset** means the team has not decided yet. Ideas added from the field guide (see
    [where this came from](#where-this-came-from)) start here.

## All ideas

| Idea | Theme | Gap | Cost | Priority | Owner |
|---|---|---|---|---|---|
| [Wasserstein distance for horizontal displacement](optimal_transport/wasserstein.md) | [Optimal transport](optimal_transport/README.md) | math, [issue 066](https://github.com/khegazy/pde_metrics/blob/main/issues/066-wasserstein-needs-a-transport-library.md) | medium | high | |
| [Transport between signed fields](optimal_transport/signed_field_transport.md) | [Optimal transport](optimal_transport/README.md) | math, [issue 047](https://github.com/khegazy/pde_metrics/blob/main/issues/047-signed-field-transport-has-no-chosen-formulation.md) | medium | high | |
| [Sliced Wasserstein distance](optimal_transport/sliced_wasserstein.md) | [Optimal transport](optimal_transport/README.md) | implementation, [issue 048](https://github.com/khegazy/pde_metrics/blob/main/issues/048-sliced-wasserstein-measure-is-undefined.md) | low | high | |
| [Entropic relaxation and Sinkhorn divergences](optimal_transport/sinkhorn.md) | [Optimal transport](optimal_transport/README.md) | implementation, [issue 067](https://github.com/khegazy/pde_metrics/blob/main/issues/067-sinkhorn-waits-on-wasserstein.md) | low | medium | |
| [Increment distances with other stencils, longitudinal and transverse](optimal_transport/gradient_pdf_w1.md) | [Optimal transport](optimal_transport/README.md) | implementation | low | high | |
| [Overlap of shock masks](shock_geometry/shock_mask_overlap.md) | [Shock geometry](shock_geometry/README.md) | implementation | low | medium | |
| [Shock front position, speed and jump conditions](shock_geometry/shock_front_error.md) | [Shock geometry](shock_geometry/README.md) | both, [issue 051](https://github.com/khegazy/pde_metrics/blob/main/issues/051-shock-front-reference-surface-score.md) | medium | medium | |
| [Shock–turbulence interaction statistics](shock_geometry/shock_turbulence_interaction.md) | [Shock geometry](shock_geometry/README.md) | implementation, [issue 002](https://github.com/khegazy/pde_metrics/blob/main/issues/002-shocklet-dataset.md) | medium | unset | |
| [Negative Sobolev norms of general order](norms/negative_sobolev_hs.md) | [Norms](norms/README.md) | math, [issue 049](https://github.com/khegazy/pde_metrics/blob/main/issues/049-negative-sobolev-order-and-length-scale.md) | low | high | |
| [Splitting a field into smooth and sharp parts](norms/mollification_split.md) | [Norms](norms/README.md) | math, [issue 050](https://github.com/khegazy/pde_metrics/blob/main/issues/050-mollification-split-three-open-choices.md) | low | high | |
| [Curvature statistics of level sets](curvature/isosurface_curvature.md) | [Curvature](curvature/README.md) | implementation, [issue 052](https://github.com/khegazy/pde_metrics/blob/main/issues/052-isosurface-curvature-isovalue-choice.md) | medium | medium | |
| [Discrete differential geometry on meshes](curvature/discrete_differential_geometry.md) | [Curvature](curvature/README.md) | math, [issue 053](https://github.com/khegazy/pde_metrics/blob/main/issues/053-discrete-differential-geometry-defines-no-metric.md) | medium | low | |
| [Curvature without smooth structure](curvature/metric_geometry_curvature.md) | [Curvature](curvature/README.md) | math, [issue 054](https://github.com/khegazy/pde_metrics/blob/main/issues/054-metric-geometry-curvature-defines-no-metric.md) | medium | low | |
| [Riemann curvature of the flow's configuration space](curvature/riemann_curvature.md) | [Curvature](curvature/README.md) | math, [issue 055](https://github.com/khegazy/pde_metrics/blob/main/issues/055-riemann-curvature-has-no-discrete-algorithm.md) | high | low | |
| [Signed entropy production](physics_invariants/entropy_production.md) | [Physics invariants](physics_invariants/README.md) | both, [issue 056](https://github.com/khegazy/pde_metrics/blob/main/issues/056-entropy-production-sign-contradiction.md) | low | high | |
| [Residual of the equations in weak form](physics_invariants/weak_residual.md) | [Physics invariants](physics_invariants/README.md) | implementation, [issue 084](https://github.com/khegazy/pde_metrics/blob/main/issues/084-weak-residual-needs-consecutive-states.md) | low | high | |
| [Consistency with one step of a trusted solver](physics_invariants/solver_consistency.md) | [Physics invariants](physics_invariants/README.md) | implementation, [issue 069](https://github.com/khegazy/pde_metrics/blob/main/issues/069-solver-consistency-needs-a-trusted-solver.md) | medium | high | |
| [Helmholtz split into rotational and compressive parts](physics_invariants/helmholtz_split.md) | [Physics invariants](physics_invariants/README.md) | math, [issue 057](https://github.com/khegazy/pde_metrics/blob/main/issues/057-helmholtz-split-formulation-and-testability.md) | medium | high | |
| [Admissibility checks](physics_invariants/admissibility_checks.md) | [Physics invariants](physics_invariants/README.md) | implementation, [issue 070](https://github.com/khegazy/pde_metrics/blob/main/issues/070-admissibility-checks-are-untestable.md) | low | unset | |
| [Galilean and rotational equivariance](physics_invariants/equivariance_tests.md) | [Physics invariants](physics_invariants/README.md) | implementation, [issue 071](https://github.com/khegazy/pde_metrics/blob/main/issues/071-equivariance-needs-the-model.md) | low | unset | |
| [Goal-oriented error estimates](physics_invariants/goal_oriented_error.md) | [Physics invariants](physics_invariants/README.md) | implementation, [issue 072](https://github.com/khegazy/pde_metrics/blob/main/issues/072-goal-oriented-error-needs-an-adjoint.md) | high | unset | |
| [Four-fifths law and the third-order structure function](turbulence_statistics/four_fifths_law.md) | [Turbulence statistics](turbulence_statistics/README.md) | implementation, [issue 005](https://github.com/khegazy/pde_metrics/blob/main/issues/005-3d-and-cost-extrapolation.md) | low | unset | |
| [Structure functions and scaling exponents](turbulence_statistics/structure_functions.md) | [Turbulence statistics](turbulence_statistics/README.md) | implementation | low | unset | |
| [Velocity-derivative skewness](turbulence_statistics/derivative_skewness.md) | [Turbulence statistics](turbulence_statistics/README.md) | implementation | low | unset | |
| [Spectral energy flux](turbulence_statistics/spectral_energy_flux.md) | [Turbulence statistics](turbulence_statistics/README.md) | implementation | medium | unset | |
| [Vortex stretching and energy budgets](turbulence_statistics/vortex_stretching.md) | [Turbulence statistics](turbulence_statistics/README.md) | implementation, [issue 005](https://github.com/khegazy/pde_metrics/blob/main/issues/005-3d-and-cost-extrapolation.md) | medium | unset | |
| [Joint distribution of the velocity-gradient invariants Q and R](turbulence_statistics/qr_invariants.md) | [Turbulence statistics](turbulence_statistics/README.md) | implementation, [issue 005](https://github.com/khegazy/pde_metrics/blob/main/issues/005-3d-and-cost-extrapolation.md) | low | unset | |
| [Helicity, potential vorticity and information transfer across scales](turbulence_statistics/inviscid_invariants.md) | [Turbulence statistics](turbulence_statistics/README.md) | both, [issue 085](https://github.com/khegazy/pde_metrics/blob/main/issues/085-inviscid-invariants-need-other-data.md) | medium | unset | |
| [One-point statistics and characteristic scales](turbulence_statistics/one_point_statistics.md) | [Turbulence statistics](turbulence_statistics/README.md) | implementation, [issue 058](https://github.com/khegazy/pde_metrics/blob/main/issues/058-one-point-statistics-what-remains.md) | low | unset | |
| [Hough transform for eddy size](pattern_detection/hough_transform.md) | [Pattern detection](pattern_detection/README.md) | implementation, [issue 059](https://github.com/khegazy/pde_metrics/blob/main/issues/059-hough-transform-defines-no-distance.md) | medium | low | |
| [Winding angle and Poincaré index](pattern_detection/winding_angle.md) | [Pattern detection](pattern_detection/README.md) | implementation, [issue 086](https://github.com/khegazy/pde_metrics/blob/main/issues/086-winding-angle-is-untestable.md) | medium | high | |
| [Eddy census](pattern_detection/eddy_census.md) | [Pattern detection](pattern_detection/README.md) | implementation, [issue 073](https://github.com/khegazy/pde_metrics/blob/main/issues/073-eddy-census-waits-on-a-detector.md) | medium | medium | |
| [Vortex criteria: Q, λ₂ and Okubo–Weiss](pattern_detection/vortex_criteria.md) | [Pattern detection](pattern_detection/README.md) | implementation, [issue 060](https://github.com/khegazy/pde_metrics/blob/main/issues/060-vortex-criteria-define-no-comparison.md) | low | medium | |
| [Persistence diagrams](topology/persistence_diagrams.md) | [Topology](topology/README.md) | implementation, [issue 074](https://github.com/khegazy/pde_metrics/blob/main/issues/074-persistence-diagrams-need-a-tda-library.md) | low | high | |
| [Multiparameter persistence](topology/multiparameter_persistence.md) | [Topology](topology/README.md) | math, [issue 061](https://github.com/khegazy/pde_metrics/blob/main/issues/061-multiparameter-persistence-has-no-complete-invariant.md) | high | low | |
| [Well groups](topology/well_groups.md) | [Topology](topology/README.md) | math, [issue 062](https://github.com/khegazy/pde_metrics/blob/main/issues/062-well-groups-have-no-computable-definition.md) | high | low | |
| [Reeb graphs and Morse–Smale complexes](topology/reeb_graphs.md) | [Topology](topology/README.md) | implementation, [issue 063](https://github.com/khegazy/pde_metrics/blob/main/issues/063-reeb-graph-distance-is-not-standard.md) | medium | medium | |
| [Jacobi sets](topology/jacobi_sets.md) | [Topology](topology/README.md) | implementation, [issue 064](https://github.com/khegazy/pde_metrics/blob/main/issues/064-jacobi-set-defines-no-scalar.md) | medium | medium | |
| [Minkowski functionals and tensors](topology/minkowski_functionals.md) | [Topology](topology/README.md) | implementation | low | unset | |
| [Two-point correlation](basis_decompositions/two_point_correlation.md) | [Basis decompositions](basis_decompositions/README.md) | none, [issue 075](https://github.com/khegazy/pde_metrics/blob/main/issues/075-two-point-correlation-anisotropy-is-untestable.md) | low | medium | |
| [Wavelets and coherent vortex extraction](basis_decompositions/coherent_vortex_extraction.md) | [Basis decompositions](basis_decompositions/README.md) | implementation, [issue 076](https://github.com/khegazy/pde_metrics/blob/main/issues/076-coherent-vortex-extraction-needs-wavelets.md) | medium | high | |
| [Wavelet scattering and phase harmonics](basis_decompositions/wavelet_scattering.md) | [Basis decompositions](basis_decompositions/README.md) | implementation, [issue 077](https://github.com/khegazy/pde_metrics/blob/main/issues/077-wavelet-scattering-needs-kymatio.md) | medium | high | |
| [Bispectrum and bicoherence](basis_decompositions/bispectrum.md) | [Basis decompositions](basis_decompositions/README.md) | implementation, [issue 065](https://github.com/khegazy/pde_metrics/blob/main/issues/065-bispectrum-distance-is-not-fixed.md) | medium | unset | |
| [Error by wavenumber band](basis_decompositions/spectral_band_error.md) | [Basis decompositions](basis_decompositions/README.md) | implementation | low | unset | |
| [Spectral coherence and phase error](basis_decompositions/spectral_coherence.md) | [Basis decompositions](basis_decompositions/README.md) | implementation | low | unset | |
| [Delta-variance spectral slope](basis_decompositions/delta_variance.md) | [Basis decompositions](basis_decompositions/README.md) | implementation | low | unset | |
| [Velocity channel analysis](basis_decompositions/velocity_channel_analysis.md) | [Basis decompositions](basis_decompositions/README.md) | implementation, [issue 087](https://github.com/khegazy/pde_metrics/blob/main/issues/087-velocity-channel-analysis-needs-a-projected-reference.md) | medium | unset | |
| [Valid prediction time](dynamics/valid_prediction_time.md) | [Dynamics](dynamics/README.md) | implementation, [issue 078](https://github.com/khegazy/pde_metrics/blob/main/issues/078-valid-prediction-time-needs-rollouts.md) | medium | unset | |
| [Temporal autocorrelation](dynamics/temporal_autocorrelation.md) | [Dynamics](dynamics/README.md) | implementation, [issue 079](https://github.com/khegazy/pde_metrics/blob/main/issues/079-temporal-autocorrelation-needs-rollouts.md) | low | unset | |
| [Invariant measure and attractor comparison](dynamics/invariant_measure.md) | [Dynamics](dynamics/README.md) | both, [issue 080](https://github.com/khegazy/pde_metrics/blob/main/issues/080-invariant-measure-needs-long-rollouts.md) | high | unset | |
| [Modal decompositions and radiated sound](dynamics/modal_decompositions.md) | [Dynamics](dynamics/README.md) | implementation, [issue 081](https://github.com/khegazy/pde_metrics/blob/main/issues/081-modal-decompositions-need-trajectories.md) | medium | unset | |
| [Energy distance](distributional/energy_distance.md) | [Distributional](distributional/README.md) | implementation | low | medium | |
| [Tail exceedance and peaks-over-threshold](distributional/tail_index_estimators.md) | [Distributional](distributional/README.md) | implementation | low | high | |
| [Pair-correlation function of features](distributional/pair_correlation.md) | [Distributional](distributional/README.md) | implementation, [issue 082](https://github.com/khegazy/pde_metrics/blob/main/issues/082-pair-correlation-waits-on-features.md) | medium | medium | |
| [Energy score, variogram score and calibration](distributional/multivariate_proper_scores.md) | [Distributional](distributional/README.md) | implementation | low | unset | |
| [Width of the log-density distribution](distributional/density_log_pdf.md) | [Distributional](distributional/README.md) | implementation, [issue 088](https://github.com/khegazy/pde_metrics/blob/main/issues/088-log-density-width-needs-supersonic-data.md) | low | unset | |
| [Quality of predictive uncertainty](distributional/predictive_uncertainty.md) | [Distributional](distributional/README.md) | implementation, [issue 083](https://github.com/khegazy/pde_metrics/blob/main/issues/083-predictive-uncertainty-needs-the-model.md) | low | unset | |
| [Wall-bounded flow diagnostics](regime_specific/wall_bounded_flows.md) | [Regime-specific](regime_specific/README.md) | implementation, [issue 089](https://github.com/khegazy/pde_metrics/blob/main/issues/089-wall-bounded-diagnostics-need-wall-data.md) | low | unset | |
| [Variable-density mixing](regime_specific/variable_density_mixing.md) | [Regime-specific](regime_specific/README.md) | implementation, [issue 090](https://github.com/khegazy/pde_metrics/blob/main/issues/090-variable-density-mixing-needs-mixing-data.md) | medium | unset | |
| [Reacting-flow and scalar-mixing diagnostics](regime_specific/reacting_flows.md) | [Regime-specific](regime_specific/README.md) | implementation, [issue 091](https://github.com/khegazy/pde_metrics/blob/main/issues/091-reacting-flow-diagnostics-need-reacting-data.md) | low | unset | |
| [Comparing refinement maps across meshes](infrastructure/refinement_map_comparison.md) | [Infrastructure](infrastructure/README.md) | implementation | medium | medium | |
| [Reference and solver predictor for the degradation ladder](infrastructure/degradation_ladder_reference.md) | [Infrastructure](infrastructure/README.md) | implementation | medium | high | |
| [Uncertainty on every metric value](infrastructure/metric_uncertainty.md) | [Infrastructure](infrastructure/README.md) | implementation | low | unset | |
| [Selecting checkpoints by rollout](infrastructure/checkpoint_selection.md) | [Infrastructure](infrastructure/README.md) | implementation | high | unset | |
| [Baseline predictors](infrastructure/baseline_predictors.md) | [Infrastructure](infrastructure/README.md) | implementation | medium | unset | |
| [Grid convergence of the reference](infrastructure/grid_convergence.md) | [Infrastructure](infrastructure/README.md) | implementation | high | unset | |
| [Robustness against the equations' own sensitivity](infrastructure/robustness.md) | [Infrastructure](infrastructure/README.md) | both | medium | unset | |

## What to build next

These are the high-priority ideas ordered by value per unit of effort. The order is the team's
judgement.

1. **[Persistence diagrams](topology/persistence_diagrams.md) on vorticity and density.**
   Off-the-shelf software exists, the stability theory is settled, and there is precedent at
   LBNL.
2. **[Tail exceedance and peaks-over-threshold](distributional/tail_index_estimators.md),**
   what remains of the tail-index idea once its Hill-estimator tier was built as
   [tail_index](../metrics/tail_index.md). It has no positivity problem to solve, and it
   measures intermittency directly.
3. **The [weak-form residual](physics_invariants/weak_residual.md) with
   [solver consistency](physics_invariants/solver_consistency.md).** Both need no reference
   field, and solver consistency is nearly free once a trusted solver is in the repository.

After these come [wavelet scattering](basis_decompositions/wavelet_scattering.md), the
[Helmholtz split](physics_invariants/helmholtz_split.md), the
[winding angle](pattern_detection/winding_angle.md) in two dimensions, and the full
[Wasserstein distance](optimal_transport/wasserstein.md) together with
[transport between signed fields](optimal_transport/signed_field_transport.md).

## What other fields have already solved

Weather forecast verification has met this project's central problem, and its literature can
be imported rather than reinvented.

- **The double-penalty problem is stated in the literature.** Wernli et al. write that "the
  classical example to illustrate the limitations of gridpoint-based error measures is the
  'double penalty problem': a prediction of a precipitation structure that is correct in terms
  of amplitude, size, and timing but (maybe only slightly) incorrect concerning position is
  very poorly rated" (Wernli et al. 2008). Replace "precipitation structure" with "shock" and
  that is this project's problem. Searching the term surfaces two decades of work on it.
- **SAL** (structure, amplitude, location) splits forecast quality into three parts. The
  location part combines the displacement of the field's centre of mass with the error in how
  far features sit from that centre (Wernli et al. 2008). It follows the same philosophy as
  [splitting a field into smooth and sharp parts](norms/mollification_split.md).
- **MODE** (object-based verification) uses convolution, smoothing and thresholding to define
  objects, then a matching algorithm to pair them between forecast and observation (Davis et
  al. 2006a, 2006b, 2009). It is the closest existing analogue to extracting shocklets from
  both fields and comparing the sets.
- **CRA** (contiguous rain area verification) splits error into displacement, volume and
  pattern parts (Ebert and McBride 2000).
- **Intensity-scale verification** scores skill jointly by intensity threshold and spatial
  scale, using a wavelet decomposition of the error field (Casati et al. 2004). It is the
  verification-side ancestor of
  [coherent vortex extraction](basis_decompositions/coherent_vortex_extraction.md).
- **Threshold-free topological detection** of atmospheric rivers (Muszynski et al. 2019) is
  discussed under [persistence diagrams](topology/persistence_diagrams.md).
- **Diagnostics and training losses are separate artifacts.** A diagnostic may be
  non-differentiable, expensive and discontinuous. A training loss may not.

## The same mathematics in different clothes

Several ideas are one idea seen from different communities, and recognising this reduces the
total work. These groupings are the team's reading.

- **The Hough transform, the Radon transform, and the sliced Wasserstein distance** are one
  transform. Projecting a field onto planes and comparing the projections is the same idea
  again, and is folded into [sliced Wasserstein](optimal_transport/sliced_wasserstein.md).
- **Splitting a field into smooth and sharp parts, coherent vortex extraction, the Helmholtz
  decomposition, and intensity-scale verification** share one principle: separate the smooth
  from the sharp and compare each part with a metric suited to it.
- **The Wasserstein distance, the negative Sobolev norm, and Ollivier–Ricci curvature** are
  all built on transport. The first two are quantitatively equivalent under stated density
  bounds (Peyre 2018), which makes the negative Sobolev norm the cheap proxy.
- **The double penalty in weather, cycle skipping in seismic inversion, and the shock-shift
  problem here** are one pathology under three names. Two of those names carry a mature
  literature to import.
- **Persistence diagrams, the eddy census, Ripley's K function, and MODE object matching** all
  identify features and then compare their distributions. They differ in how a feature is
  defined and whether features are matched pairwise before comparison.

## Where this came from

This section merges two documents.

- **The team's tracker**, "Fluid Metrics Exploration Tracker" (August 2026), recoverable from
  the repository's git history as `Table_of_Ideas.tex`. Its two-letter identifiers are
  retired; an idea is named by its page. Every citation was checked against its primary
  source when the tracker was written. One claim did not survive that check: no precedent was
  found for detecting eddies with the Hough transform, so that idea is recorded as untested
  and original. Ideas from the tracker carry the team's priority.
- **A field guide**, "Measuring, Categorizing, and Comparing Fluid Flows and Their
  Simulations: A Ranked, Annotated Field Guide" (August 2026), a survey written with an AI
  assistant. Its ideas were merged into the existing pages where they overlap, and added as
  new pages where they do not; their priority is unset until the team decides. The guide's
  ranking into tiers was not carried over, because this site does not rank metrics. The guide
  attributes part of its framework to an unpublished 2026 benchmarking document that could
  not be identified, so that attribution is not repeated here. Every reference taken from the
  guide was checked against its registered record in Crossref or arXiv; two titles the guide
  gave wrongly were corrected, and citations that could not be confirmed were dropped.

## References

- Casati, B., Ross, G. & Stephenson, D. B. (2004). A new intensity-scale approach for the
  verification of spatial precipitation forecasts. *Meteorological Applications* 11(2),
  141–154. <https://doi.org/10.1017/S1350482704001239>
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
- Ebert, E. E. & McBride, J. L. (2000). Verification of precipitation in weather systems:
  Determination of systematic errors. *Journal of Hydrology* 239(1–4), 179–202.
  <https://doi.org/10.1016/S0022-1694(00)00343-7>
- Muszynski, G., Kashinath, K., Kurlin, V., Wehner, M. & Prabhat (2019). Topological data
  analysis and machine learning for recognizing atmospheric river patterns in large climate
  datasets. *Geoscientific Model Development* 12(2), 613–628.
  <https://doi.org/10.5194/gmd-12-613-2019>
- Peyre, R. (2018). Comparison between $W_2$ distance and $\dot H^{-1}$ norm, and localization
  of Wasserstein distance. *ESAIM: Control, Optimisation and Calculus of Variations* 24(4),
  1489–1501. <https://doi.org/10.1051/cocv/2017050>
- Wernli, H., Paulat, M., Hagen, M. & Frei, C. (2008). SAL — A novel quality measure for the
  verification of quantitative precipitation forecasts. *Monthly Weather Review* 136(11),
  4470–4487. <https://doi.org/10.1175/2008MWR2415.1>
