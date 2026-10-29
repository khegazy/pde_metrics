# Designing an evaluation

[Why single metrics are not enough](background.md) explains why one number cannot certify a
surrogate. This page covers what to do instead: how to describe a metric precisely, how to
decide which flow is being compared before comparing fields, which ideas belong together for
a given regime or task, how to keep test data honest, how to report many results together,
and how evaluation metrics relate to training losses. Where no citation is given, the
framing is the synthesis of the field guide described in
[where this came from](README.md#where-this-came-from), not an established consensus.

## Five axes that describe a metric

Any metric can be described by five choices.

1. **Representation: what is compared.**
   - The state itself, cell by cell; derived fields such as gradients, the vorticity, the
     vortex criteria $Q$ and $\lambda_2$, or the divergence; integral quantities of interest
     such as a drag coefficient; spectra; probability distributions and their moments;
     geometric objects such as shock surfaces and level sets; topological or morphological
     summaries; modal decompositions; Lagrangian objects such as particle paths; dynamical
     invariants such as Lyapunov exponents; or the image of the field under an observation
     operator.
2. **Comparison: how two representations are compared.** The classes behave differently and
   are not interchangeable; they are described in the next subsection.
3. **Ground: what the prediction is compared against.**
   - An external reference solution; the prediction's own physical self-consistency, with no
     reference; a symmetry the equations obey; a baseline predictor, giving a skill score;
     or an analytic result.
4. **Conditioning: where the comparison is made.**
   - Over the whole domain, or restricted to a regime, region, scale or structure: bins along
     the normal to a shock, a layer near a wall, or the spectral bands the reference resolves.
5. **Aggregation: how many numbers become a report.**
   - A panel of separate results, a weighted scalar, a Pareto front (the set of predictions
     that no other prediction beats on every component at once), rank comparisons, or
     normalisation by uncertainty.

On this reading, a panel is complete for a regime when no relevant combination of
representation, comparison and ground is left empty. Each built metric's card already records
several of these choices: its category, what it is given, the units of its value, and which
direction is better, all listed in [the catalogue](../catalogue.md).

### Classes of comparison

Let $P$ and $Q$ be two probability distributions, for example of a velocity gradient in the
prediction and in the reference.

- **Norms and correlations** compare two fields directly: the $L^p$ norms, Sobolev norms
  that weight scales differently, their duals, and correlation coefficients. Built examples
  are [mse](../metrics/mse.md), [h1_seminorm](../metrics/h1_seminorm.md) and
  [h_minus_one](../metrics/h_minus_one.md); the idea
  [negative Sobolev norms of general order](norms/negative_sobolev_hs.md) extends them.
- **$f$-divergences** compare distributions through their density ratio,
  $D_f(P\,\Vert\,Q) = \int f\!\left(dP/dQ\right) dQ$ for a convex $f$ with $f(1)=0$. The
  Kullback–Leibler and Jensen–Shannon divergences are examples. They are unstable when the two
  distributions do not overlap. For two point masses at $x$ and $x+h$ with $h \neq 0$, the
  Kullback–Leibler divergence is infinite and the Jensen–Shannon divergence is $\ln 2$
  whatever the size of $h$, so neither says how far apart the distributions are.
- **Integral probability metrics** take the largest difference in expectation over a class
  $\mathcal{F}$ of test functions,
  $d_{\mathcal{F}}(P,Q) = \sup_{f\in\mathcal{F}} \lvert \mathbb{E}_P[f] - \mathbb{E}_Q[f] \rvert$,
  where $\mathbb{E}_P[f]$ is the average of $f$ under $P$. Different classes give the
  Wasserstein-1 distance (the 1-Lipschitz functions), the maximum mean discrepancy (the unit
  ball of a reproducing-kernel Hilbert space) and, in one dimension, the Kolmogorov–Smirnov
  distance (indicators of half-lines) (Müller 1997). The energy distance
  belongs to the same family. These stay well behaved when the distributions do not overlap:
  for the two point masses above, the Wasserstein-1 distance is $h$. See the
  [Wasserstein distance](optimal_transport/wasserstein.md), the
  [sliced Wasserstein distance](optimal_transport/sliced_wasserstein.md), the
  [energy distance](distributional/energy_distance.md) and the built
  [increment_w1](../metrics/increment_w1.md).
- **Proper scoring rules** judge a predicted distribution against an observed outcome. A
  score is *proper* when its expected value is optimised by predicting the true distribution,
  and *strictly proper* when only the true distribution optimises it (Gneiting & Raftery
  2007). The built [crps](../metrics/crps.md) is one; the
  [energy and variogram scores](distributional/multivariate_proper_scores.md) extend it to
  many variables at once.
- **Set overlap and geometric distances** compare extracted objects rather than fields:
  overlap ratios such as intersection over union, and distances between surfaces. See
  [overlap of shock masks](shock_geometry/shock_mask_overlap.md) and
  [distance between extracted shock sets](shock_geometry/shock_set_distance.md).

## What a metric's description should declare

A metric's value means something only together with the choices behind it. The field guide
asks each metric to declare:

- **object**: the quantity compared, for example density, or the vorticity magnitude;
- **regime**: the flows for which the metric is meaningful, for example homogeneous
  turbulence in an inertial range;
- **comparator**: the comparison functional, from the classes above;
- **observation operator**: the map from the full simulated state to what is compared, such
  as a projection, a filter, a remap onto an analysis grid, or sampling at sensor locations;
- **normalisation**: what the value is divided by, so that it can be read across fields and
  datasets;
- **invariances**: the transformations that leave the value unchanged, such as a shift of the
  whole domain or a rotation;
- **estimator**: how the value is computed from a finite sample of fields and times;
- **uncertainty**: the error bar on the value itself, from resampling or from a convergence
  study.

This follows the discipline of verification and validation in computational fluid dynamics,
which asks every reported comparison to state what is compared, against what, and with what
numerical and statistical uncertainty (Oberkampf & Trucano 2002; Roache 1997). The
discretisation part of that uncertainty has a standard reporting procedure based on the grid
convergence index (Celik et al. 2008); see
[grid convergence of the reference](infrastructure/grid_convergence.md) and
[uncertainty on every metric value](infrastructure/metric_uncertainty.md).

## Classify the regime before comparing fields

Dimensionless numbers state which physical effects compete in a flow and therefore which
qualitative regime it is in. With $U$ a velocity scale, $L$ a length scale and $\nu$ the
kinematic viscosity, the usual ones are:

- the Reynolds number $Re = UL/\nu$, inertia against viscosity;
- the Mach number $Ma = U/c$, flow speed against the speed of sound $c$;
- the Prandtl and Schmidt numbers $Pr = \nu/\kappa$ and $Sc = \nu/D$, momentum diffusion
  against the diffusion of heat ($\kappa$) or of a species ($D$);
- the Rayleigh number $Ra = g\beta\Delta T L^3/(\nu\kappa)$, buoyant forcing by a
  temperature difference $\Delta T$ against diffusion, with $g$ gravity and $\beta$ the
  thermal expansion coefficient;
- the Froude number $Fr = U/\sqrt{gL}$, inertia against gravity;
- the Knudsen number $Kn = \lambda/L$, the molecular mean free path $\lambda$ against the
  flow scale, which says whether a continuum description holds;
- the Weber number $We = \rho U^2 L/\sigma$, inertia against surface tension $\sigma$, with
  $\rho$ the density;
- the Strouhal number $St = fL/U$, an oscillation frequency $f$ against the flow's own time
  scale.

These numbers are cheap to compute, apply to any flow, and say whether two fields can sensibly
be compared at all. Pipe flow is the standard example: turbulence that decays at lower
Reynolds numbers becomes sustained at a sharp critical value, $Re_c \approx 2040 \pm 10$
(Avila et al. 2011), so a prediction and a reference on opposite sides of that value are
different flows, whatever their fields look like. Matching the dimensionless numbers is
necessary, not sufficient: it says nothing about the accuracy of a solution, and matched
$Re$ or $Ma$ does not guarantee matched statistics.

## Ideas for each regime and task

Each row lists the ideas and built metrics that together cover the failures typical of one
regime or task, and what is easy to miss there; an empty cell means the field guide names
nothing. A row is a starting point for a panel, not a recommendation that excludes anything
else.

| Regime or task | Ideas and built metrics | What is easy to miss |
|---|---|---|
| Smooth surrogates, and learned surrogates in general | Built [nrmse](../metrics/nrmse.md); [error by wavenumber band](basis_decompositions/spectral_band_error.md); conservation in [admissibility checks](physics_invariants/admissibility_checks.md); [valid prediction time](dynamics/valid_prediction_time.md) | Decorrelation past the predictability horizon; spectral bias |
| Shock tubes and blast waves | Jump conditions, position and speed in [shock front error](shock_geometry/shock_front_error.md); [signed entropy production](physics_invariants/entropy_production.md); positivity in [admissibility checks](physics_invariants/admissibility_checks.md); total variation | Over-smeared shocks, which pass one-sided entropy checks |
| Compressible homogeneous turbulence | Spectra of the [rotational and compressive parts](physics_invariants/helmholtz_split.md); [spectral energy flux](turbulence_statistics/spectral_energy_flux.md), including the pressure–density exchange term; [width of the log-density distribution](distributional/density_log_pdf.md); [four-fifths law](turbulence_statistics/four_fifths_law.md) | Over-dissipated shocklets |
| Incompressible turbulence, and direct numerical simulation | Built [spectrum_l2](../metrics/spectrum_l2.md); [spectral energy flux](turbulence_statistics/spectral_energy_flux.md); [structure functions](turbulence_statistics/structure_functions.md); built [increment_flatness](../metrics/increment_flatness.md); [four-fifths law](turbulence_statistics/four_fifths_law.md); divergence in [admissibility checks](physics_invariants/admissibility_checks.md) | Whether high-order moments have converged with the sample size ([uncertainty on every metric value](infrastructure/metric_uncertainty.md)) |
| Shock–turbulence interaction | Amplification ratios in bins along the shock normal, the spectrum of shock corrugation, and shocklet statistics in [shock–turbulence interaction](shock_geometry/shock_turbulence_interaction.md); [shock detector](shock_geometry/shock_detector.md) | Detector thresholds tuned per model |
| Wall-bounded flows and aerodynamics | Friction velocity, log law, skin friction, Reynolds stresses and premultiplied spectra in [wall-bounded flows](regime_specific/wall_bounded_flows.md); lift and drag through [goal-oriented error](physics_invariants/goal_oriented_error.md); realizability in [admissibility checks](physics_invariants/admissibility_checks.md) | Error in the form of the turbulence model, which a reference computed with the same model shares |
| Super-resolution | [Error by wavenumber band](basis_decompositions/spectral_band_error.md); distribution distances such as built [increment_w1](../metrics/increment_w1.md) and [increment_w1_by_separation](../metrics/increment_w1_by_separation.md); [structure functions](turbulence_statistics/structure_functions.md) | |
| Generative ensembles | Built [crps](../metrics/crps.md), [rank_histogram](../metrics/rank_histogram.md) and [spread_skill](../metrics/spread_skill.md); [energy and variogram scores](distributional/multivariate_proper_scores.md); the distribution of spectra across members | Calibration of each variable separately while correlations between them are wrong |
| Variable-density mixing | Growth-rate exponent, molecular mixing fraction, anisotropy and Lagrangian ridges in [variable-density mixing](regime_specific/variable_density_mixing.md) | |
| Geophysical and climate flows | Potential vorticity in [inviscid invariants](turbulence_statistics/inviscid_invariants.md); the anomaly correlation coefficient; built [crps](../metrics/crps.md) and [spread_skill](../metrics/spread_skill.md); the two-dimensional cascade through the [spectral energy flux](turbulence_statistics/spectral_energy_flux.md) | Metrics designed for three-dimensional turbulence applied to nearly two-dimensional flow |
| Combustion | Statistics conditioned on mixture fraction, scalar dissipation rate, flame index and flame surface density in [reacting flows](regime_specific/reacting_flows.md) | A correct mean temperature hiding wrong flame structure |
| Astrophysical flows | [Width of the log-density distribution](distributional/density_log_pdf.md); [Minkowski functionals](topology/minkowski_functionals.md); [delta-variance](basis_decompositions/delta_variance.md); [bispectrum](basis_decompositions/bispectrum.md); [velocity channel analysis](basis_decompositions/velocity_channel_analysis.md) | The projection along the line of sight, which is the observation operator |
| Choosing a checkpoint during training | [Valid prediction time](dynamics/valid_prediction_time.md); [spectral energy flux](turbulence_statistics/spectral_energy_flux.md); [four-fifths law](turbulence_statistics/four_fifths_law.md); built [increment_w1_by_separation](../metrics/increment_w1_by_separation.md) or [skewness](turbulence_statistics/derivative_skewness.md) with flatness; the long-time spectrum in the resolved band; [admissibility checks](physics_invariants/admissibility_checks.md). The procedure is in [selecting checkpoints by rollout](infrastructure/checkpoint_selection.md) | One-step validation error that improves while rollouts degrade |

The anomaly correlation coefficient is the correlation between predicted and observed
departures from a long-term mean. It measures phase alignment and is used in weather
forecasting at short and medium horizons (Rasp et al. 2024).

## Tasks and data leakage

Different tasks call for different metrics, and the task should be stated before choosing
any. The common ones are:

- one-step forecasting, and autoregressive rollout over many steps;
- operator learning, from parameters or initial conditions to solutions;
- super-resolution, from coarse fields to fine ones;
- closure modelling, which is judged *a priori* (the closure term compared on given resolved
  fields) or *a posteriori* (the flow obtained when the closure runs inside a solver), and
  the two can disagree;
- shock detection;
- reconstruction of a field from sparse sensors, and other inverse problems;
- generative ensembles;
- learned numerical fluxes or limiters, and learned wall models;
- warm-starting or accelerating a solver;
- adaptive sampling and meshing.

**Splits must not leak.** Adjacent snapshots of one turbulent trajectory are strongly
correlated over the flow's decorrelation time, so a test snapshot drawn at random from the
same trajectory as the training snapshots is nearly a copy of one of them. The test error
then measures interpolation, not prediction. Random temporal splits of a single trajectory
are therefore avoided; data are split by trajectory, initial condition, random seed,
geometry or physical parameters. Results inside the training distribution and outside it
are reported separately, and a *stress matrix* records how results change as the test moves
away from training along each of these directions:

- physical parameters;
- geometry;
- boundary conditions;
- resolution or mesh;
- the numerical method that produced the reference;
- data quality, such as noise;
- the length of the prediction horizon.

**Benchmarks.** Several public collections define tasks and splits of this kind: PDEBench
(Takamoto et al. 2022), The Well (Ohana et al. 2024), AirfRANS (Bonnet et al. 2022),
LagrangeBench (Toshev et al. 2023), WeatherBench 2 (Rasp et al. 2024), a benchmark of flow
prediction around complex geometries (Rabeh et al. 2025), and the Johns Hopkins Turbulence
Databases (Li et al. 2008). PDEArena, BLASTNet, FlowBench, RealPDEBench and the NASA
Turbulence Modeling Resource are further collections in the same spirit.

## Reporting many results together

The results of a panel are reported as a dashboard of separate numbers, grouped for example
into state fidelity, shock fidelity, turbulence statistics, physical consistency, quantities
of interest, rollout behaviour, structural checks and cost. A prediction that violates an
admissibility condition, such as a negative density or pressure, a drift in a conserved
total, a NaN or a blow-up, is non-physical. A weighted average can let small errors
elsewhere offset that, so admissibility results are reported in their own columns rather
than folded into a combined score.

If a single scalar is ever formed, each component is first normalised against a declared
baseline, such as one of the [baseline predictors](infrastructure/baseline_predictors.md),
clipped so that one component cannot dominate, and published alongside the scalar so a reader
can see what produced it. Differences between two predictions carry paired bootstrap
intervals: the same test cases are resampled for both, so case-to-case variation in
difficulty cancels in the difference (Efron & Tibshirani 1993). For correlated fields the
resampling unit is a block at least as long as the decorrelation scale, as described in
[uncertainty on every metric value](infrastructure/metric_uncertainty.md). When several
predictions are compared across several datasets, the rank-based tests recommended by
Demšar (2006), the Friedman test followed by the Nemenyi test, guard against reading noise as
a ranking. A statistically significant difference in rank is not necessarily a physically
significant one.

This section concerns reporting the results of predictions. It does not rank the metrics
themselves, which this site never does.

## Training losses and the Goodhart caveat

Most families of evaluation metric have a differentiable counterpart that can be used as a
training loss.

- **Spectral losses** compare binned or logarithmic spectral power (Chakraborty et al. 2026).
- **Sobolev losses** weight the error at each scale: positive orders such as the built
  [h1_seminorm](../metrics/h1_seminorm.md) emphasise sharpness, and negative orders such as
  [h_minus_one](../metrics/h_minus_one.md) and the idea
  [negative Sobolev norms of general order](norms/negative_sobolev_hs.md) tolerate small
  displacements of rough features.
- **Distributional losses** use optimal transport, made differentiable by
  [entropic relaxation and Sinkhorn divergences](optimal_transport/sinkhorn.md), or the
  maximum mean discrepancy (Gretton et al. 2012).
- **Adversarial losses** train a second network to tell predicted fields from true ones, which
  acts as a learned test of statistical realism (Granero Belinchon & Cabeza Gallucci 2024
  apply this to turbulent fields).
- **Proper scoring rules** such as the built [crps](../metrics/crps.md) and the
  [energy score](distributional/multivariate_proper_scores.md) train calibrated ensembles
  (Gneiting & Raftery 2007).
- **Physics-constrained losses** penalise the residual of the equations: physics-informed
  neural networks (Raissi et al. 2019), their weak form for entropy solutions of conservation
  laws (De Ryck et al. 2024), and losses built on Godunov fluxes (Cassia & Kerswell 2025).
- **Solver-in-the-loop and unrolled training** run the model through a differentiable solver
  over several steps, so it trains on its own rollout distribution (Um et al. 2020; Kochkov et
  al. 2021; List et al. 2022), and the pushforward trick trains on its own perturbed outputs
  (Brandstetter et al. 2022).

On the field guide's reading, physics-constrained losses constrain admissibility but do not
by themselves remove spectral bias or rollout instability.

A quantity that has been optimised during training stops being an independent check on the
model, because training pushes it towards its target whether or not the rest of the physics
follows. This is Goodhart's law: a measure that becomes a target ceases to be a good measure.
An evaluation therefore keeps a holdout of metrics that never enter any training loss. In
the repository, whether a built metric can be used as a loss is listed in
[the catalogue](../catalogue.md); a diagnostic and a training loss are kept as separate
artifacts with separate requirements.

## References

- Avila, K., Moxey, D., de Lozar, A., Avila, M., Barkley, D. & Hof, B. (2011). The onset of
  turbulence in pipe flow. *Science* 333, 192–196. <https://doi.org/10.1126/science.1203223>
- Bonnet, F., Mazari, J., Cinnella, P. & Gallinari, P. (2022). AirfRANS: High fidelity
  computational fluid dynamics dataset for approximating Reynolds-averaged Navier–Stokes
  solutions. *Advances in Neural Information Processing Systems* 35, 23463–23478.
  <https://doi.org/10.52202/068431-1705>
- Brandstetter, J., Worrall, D. & Welling, M. (2022). Message passing neural PDE solvers.
  *ICLR*. <https://arxiv.org/abs/2202.03376>
- Cassia, R. & Kerswell, R. (2025). Godunov loss functions for modelling of hyperbolic
  conservation laws. *Computer Methods in Applied Mechanics and Engineering* 437, 117782.
  <https://doi.org/10.1016/j.cma.2025.117782>
- Celik, I. B., Ghia, U., Roache, P. J., Freitas, C. J., Coleman, H. & Raad, P. E. (2008).
  Procedure for estimation and reporting of uncertainty due to discretization in CFD
  applications. *ASME Journal of Fluids Engineering* 130, 078001.
  <https://doi.org/10.1115/1.2960953>
- Chakraborty, D., Mohan, A. T. & Maulik, R. (2026). Binned spectral power loss for improved
  prediction of chaotic systems. *Journal of Computational Physics* 558, 114866.
  <https://doi.org/10.1016/j.jcp.2026.114866>
- De Ryck, T., Mishra, S. & Molinaro, R. (2024). wPINNs: weak physics-informed neural
  networks for approximating entropy solutions of hyperbolic conservation laws. *SIAM Journal
  on Numerical Analysis* 62, 811–841. <https://doi.org/10.1137/22M1522504>
- Demšar, J. (2006). Statistical comparisons of classifiers over multiple data sets.
  *Journal of Machine Learning Research* 7, 1–30. <https://jmlr.org/papers/v7/demsar06a.html>
- Efron, B. & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Springer.
  <https://doi.org/10.1007/978-1-4899-4541-9>
- Gneiting, T. & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and
  estimation. *Journal of the American Statistical Association* 102, 359–378.
  <https://doi.org/10.1198/016214506000001437>
- Granero Belinchon, C. & Cabeza Gallucci, M. (2024). A multiscale and multicriteria
  Generative Adversarial Network to synthesize 1-dimensional turbulent fields. *Machine
  Learning: Science and Technology* 5(2), 025032. <https://doi.org/10.1088/2632-2153/ad43b3>
- Gretton, A. et al. (2012). A kernel two-sample test. *Journal of Machine Learning
  Research* 13, 723–773. <https://jmlr.org/papers/v13/gretton12a.html>
- Kochkov, D., Smith, J. A., Alieva, A., Wang, Q., Brenner, M. P. & Hoyer, S. (2021).
  Machine learning–accelerated computational fluid dynamics. *PNAS* 118, e2101784118.
  <https://doi.org/10.1073/pnas.2101784118>
- Li, Y., Perlman, E., Wan, M., Yang, Y. et al. (2008). A public turbulence database cluster
  and applications to study Lagrangian evolution of velocity increments in turbulence.
  *Journal of Turbulence* 9, N31. <https://doi.org/10.1080/14685240802376389>
- List, B., Chen, L.-W. & Thuerey, N. (2022). Learned turbulence modelling with
  differentiable fluid solvers: physics-based loss functions and optimisation horizons.
  *Journal of Fluid Mechanics* 949, A25. <https://doi.org/10.1017/jfm.2022.738>
- Müller, A. (1997). Integral probability metrics and their generating classes of functions.
  *Advances in Applied Probability* 29, 429–443. <https://doi.org/10.2307/1428011>
- Oberkampf, W. L. & Trucano, T. G. (2002). Verification and validation in computational
  fluid dynamics. *Progress in Aerospace Sciences* 38, 209–272.
  <https://doi.org/10.1016/S0376-0421(02)00005-2>
- Ohana, R. et al. (2024). The Well: a large-scale collection of diverse physics simulations
  for machine learning. *NeurIPS*. <https://arxiv.org/abs/2412.00568>
- Rabeh, A., Herron, E., Balu, A., Sarkar, S. et al. (2025). Benchmarking scientific
  machine-learning approaches for flow prediction around complex geometries. *Communications
  Engineering* 4, 182. <https://doi.org/10.1038/s44172-025-00513-3>
- Raissi, M., Perdikaris, P. & Karniadakis, G. E. (2019). Physics-informed neural networks:
  A deep learning framework for solving forward and inverse problems involving nonlinear
  partial differential equations. *Journal of Computational Physics* 378, 686–707.
  <https://doi.org/10.1016/j.jcp.2018.10.045>
- Rasp, S., Hoyer, S., Merose, A., Langmore, I. et al. (2024). WeatherBench 2: A benchmark for
  the next generation of data-driven global weather models. *Journal of Advances in Modeling
  Earth Systems* 16, e2023MS004019. <https://doi.org/10.1029/2023ms004019>
- Roache, P. J. (1997). Quantification of uncertainty in computational fluid dynamics.
  *Annual Review of Fluid Mechanics* 29, 123–160.
  <https://doi.org/10.1146/annurev.fluid.29.1.123>
- Takamoto, M. et al. (2022). PDEBench: an extensive benchmark for scientific machine
  learning. *NeurIPS Datasets and Benchmarks*. <https://arxiv.org/abs/2210.07182>
- Toshev, A., Galletti, G., Fritz, F., Adami, S. et al. (2023). LagrangeBench: A
  Lagrangian fluid mechanics benchmarking suite. *Advances in Neural Information Processing
  Systems* 36, 64857–64884. <https://doi.org/10.52202/075280-2830>
- Um, K., Brand, R., Fei, Y., Holl, P. & Thuerey, N. (2020). Solver-in-the-loop: learning
  from differentiable physics to interact with iterative PDE-solvers. *NeurIPS*.
  <https://arxiv.org/abs/2007.00016>
