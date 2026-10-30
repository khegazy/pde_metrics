# Open items

One file per item, so future work is written down where a colleague will find it rather than
living in a plan document or in someone's memory. Each file states the evidence, not just the
intent: six months from now "we need a lower-Reynolds reference" is useless without the
measurement that showed why.

Write an issue while the evidence is in front of you. One written from memory later is worth
much less.

**Delete an issue once it is fully resolved.** This folder holds only what is open, so there is
no resolved list: remove the file and its row below, say in the resolving commit's message what
was done and on what evidence, and rewrite every reference to the issue so it states the reason
itself where the code or document needs it. `git log --diff-filter=D --stat -- issues/` lists
the closed issues and the commits that closed them. An issue resolved only in part stays, and
its status says first what is still open.

## Data generation required

These block criteria that are designed and implemented but cannot be exercised.

| ID | Title | Priority |
|---|---|---|
| [001](001-low-reynolds-reference.md) | The protocol specifies Re ~ 500; no such dataset exists | medium |
| [002](002-shocklet-dataset.md) | No shocklet-populated compressible turbulence | accepted, scheduled |
| [003](003-ensemble-data.md) | CRPS and spread-to-skill need ensembles — estimators built and validated on a synthetic ensemble; physical data is [004](004-independent-realizations.md) | low |
| [004](004-independent-realizations.md) | Only one seed per configuration | medium |
| [037](037-increment-flatness-has-no-damage-scale.md) | The increment flatness is zero over zero on the mean-field anchor, so it alone has no damage scale | low |
| [005](005-3d-and-cost-extrapolation.md) | All data is two-dimensional | low |
| [034](034-the-well-format-copy-is-not-published.md) | The Well-format copy is not published, so that reader's HTTP path is only covered by a fixture | low |
| [084](084-weak-residual-needs-consecutive-states.md) | Residual of the equations in weak form needs states one solver step apart | high |
| [085](085-inviscid-invariants-need-other-data.md) | Helicity, potential vorticity and information transfer need data the repository does not have | unset |
| [086](086-winding-angle-is-untestable.md) | Winding angle and Poincaré index: no experiment changes the vortices in a known way | high |
| [087](087-velocity-channel-analysis-needs-a-projected-reference.md) | Velocity channel analysis needs a projected reference | unset |
| [088](088-log-density-width-needs-supersonic-data.md) | Width of the log-density distribution needs supersonic isothermal turbulence and the sound speed | unset |
| [089](089-wall-bounded-diagnostics-need-wall-data.md) | Wall-bounded flow diagnostics need a dataset with walls | unset |
| [090](090-variable-density-mixing-needs-mixing-data.md) | Variable-density mixing needs Rayleigh–Taylor or Richtmyer–Meshkov data | unset |
| [091](091-reacting-flow-diagnostics-need-reacting-data.md) | Reacting-flow diagnostics need reacting data | unset |

## Deferred functionality

Designed, hooks in place, not built.

| ID | Title | Priority |
|---|---|---|
| [010](010-forecast-pair-reader.md) | Read the real prediction/target pairs | **high** |
| [011](011-cross-dataset-comparison.md) | Compare metrics across a Reynolds ladder | medium |
| [013](013-remaining-intuition-figures.md) | Outlier, invariance, triangle-inequality figures | low |
| [014](014-gradient-signal-criterion.md) | Gradient quality where L2 goes flat | medium |
| [015](015-rotation-degradation.md) | Rotation, which must rotate vector components | low |
| [016](016-mass-weighted-remap.md) | Momentum-conserving remap option | low |
| [024](024-leray-projection.md) | Solenoidal projection for the spectral operators | low |
| [066](066-wasserstein-needs-a-transport-library.md) | Wasserstein distance for horizontal displacement needs a transport library | high |
| [067](067-sinkhorn-waits-on-wasserstein.md) | Sinkhorn divergences wait on the Wasserstein distance | medium |
| [068](068-shock-mask-overlap-waits-on-the-detector.md) | Overlap of shock masks waits on the shock detector | medium |
| [069](069-solver-consistency-needs-a-trusted-solver.md) | Consistency with one step of a trusted solver needs the solver | high |
| [070](070-admissibility-checks-are-untestable.md) | Admissibility checks: no existing experiment violates an admissibility condition | unset |
| [071](071-equivariance-needs-the-model.md) | Galilean and rotational equivariance needs the model | unset |
| [072](072-goal-oriented-error-needs-an-adjoint.md) | Goal-oriented error estimates need an adjoint solver and a declared output | unset |
| [073](073-eddy-census-waits-on-a-detector.md) | Eddy census waits on a vortex detector | medium |
| [074](074-persistence-diagrams-need-a-tda-library.md) | Persistence diagrams need a topology library | high |
| [075](075-two-point-correlation-anisotropy-is-untestable.md) | Two-point correlation: what it adds beyond spectrum_l2 is untestable | medium |
| [076](076-coherent-vortex-extraction-needs-wavelets.md) | Coherent vortex extraction needs a wavelet library, and its comparison is unspecified | high |
| [077](077-wavelet-scattering-needs-kymatio.md) | Wavelet scattering needs a scattering-transform library | high |
| [078](078-valid-prediction-time-needs-rollouts.md) | Valid prediction time needs rollouts and a temporal experiment | unset |
| [079](079-temporal-autocorrelation-needs-rollouts.md) | Temporal autocorrelation needs rollouts and a temporal experiment | unset |
| [080](080-invariant-measure-needs-long-rollouts.md) | Invariant measure and attractor comparison needs long rollouts and the model | unset |
| [094](094-dynamics-family-has-a-test-bed-but-no-rollout-input.md) | The dynamics family has a test bed (`advecting_blobs`, `per_unit_time`) but no rollout input, and the valid prediction time needs a stated threshold convention | unset |
| [096](096-several-fields-handed-to-one-metric.md) | Several fields handed to one metric together, without reusing `fields=` | unset |
| [081](081-modal-decompositions-need-trajectories.md) | Modal decompositions need time-resolved trajectories | unset |
| [082](082-pair-correlation-waits-on-features.md) | Pair-correlation function of features waits on feature extraction | medium |
| [083](083-predictive-uncertainty-needs-the-model.md) | Quality of predictive uncertainty needs a surrogate that reports uncertainty | unset |

## Method and calibration

| ID | Title | Priority |
|---|---|---|
| [031](031-saturation-never-reached.md) | Most ladder axes do not reach 90% of the way to the anchor, so `saturation_level` is blank on most rows | medium |
| [042](042-rank-interval-block-length-is-half-the-estimate.md) | The rank-correlation interval's fixed 10-frame blocks are half the estimated decorrelation, and its generator is shared across groups | medium |
| [039](039-h1-seminorm-is-not-monotone-under-coarsening.md) | Under `coarsen_bandlimited`, density is out of order in some frames for several metrics, unexplained; the `coarsen` decisions themselves are acted on | low |
| [041](041-subpixel-shift-drops-the-nyquist-mode.md) | A fractional Fourier shift drops the Nyquist mode of an even grid; negligible on the production data | low |
| [044](044-synthetic-ensemble-ignores-the-run-seed.md) | The synthetic ensemble is generated from its own seed, so `seed=` does not change a synthetic run and the ensemble cards cite a seed that had no effect; needs a decision | low |
| [046](046-wavenumber-magnitude-is-anisotropic-on-non-square-domains.md) | The wavenumber magnitude counts cycles across each axis's own length, so a cutoff is anisotropic on a non-square domain, and a wall on only some axes makes a square grid non-square; needs a decision on the definition of `\|k\|` | low |
| [047](047-signed-field-transport-has-no-chosen-formulation.md) | Transport between signed fields: which of the four formulations to use | high |
| [048](048-sliced-wasserstein-measure-is-undefined.md) | Sliced Wasserstein distance: what measure is sliced, on a periodic domain | high |
| [049](049-negative-sobolev-order-and-length-scale.md) | Negative Sobolev norms of general order: which orders, and the inhomogeneous norm's length scale | high |
| [050](050-mollification-split-three-open-choices.md) | Splitting a field into smooth and sharp parts: three open choices | high |
| [051](051-shock-front-reference-surface-score.md) | Shock front position, speed and jump conditions: the reference-surface score is unsettled | medium |
| [052](052-isosurface-curvature-isovalue-choice.md) | Curvature statistics of level sets: which isovalue | medium |
| [053](053-discrete-differential-geometry-defines-no-metric.md) | Discrete differential geometry on meshes defines no metric | low |
| [054](054-metric-geometry-curvature-defines-no-metric.md) | Curvature without smooth structure defines no metric for flow fields | low |
| [055](055-riemann-curvature-has-no-discrete-algorithm.md) | Riemann curvature of the flow's configuration space has no discrete algorithm | low |
| [056](056-entropy-production-sign-contradiction.md) | Signed entropy production: the over-smeared-shock contradiction, and consecutive time levels | high |
| [057](057-helmholtz-split-formulation-and-testability.md) | Helmholtz split: which field is decomposed, what number is reported, and what tests it | high |
| [058](058-one-point-statistics-what-remains.md) | One-point statistics and characteristic scales: what remains that is neither built, three-dimensional, nor untestable | unset |
| [059](059-hough-transform-defines-no-distance.md) | Hough transform for eddy size defines no distance between accumulators | low |
| [060](060-vortex-criteria-define-no-comparison.md) | Vortex criteria define a detector, not a comparison | medium |
| [061](061-multiparameter-persistence-has-no-complete-invariant.md) | Multiparameter persistence: no complete invariant, research-grade tooling, and it builds on persistence | low |
| [062](062-well-groups-have-no-computable-definition.md) | Well groups have no computable definition on the page | low |
| [063](063-reeb-graph-distance-is-not-standard.md) | Reeb graphs and Morse–Smale complexes: no standard distance between graphs | medium |
| [064](064-jacobi-set-defines-no-scalar.md) | Jacobi sets define a set, not a number | medium |
| [065](065-bispectrum-distance-is-not-fixed.md) | Bispectrum and bicoherence: the distance between maps is not fixed | unset |
| [095](095-pooling-across-frames-for-distributional-estimates.md) | Pooling across frames for a distributional estimate; the contract of a series-level procedure, should a metric need one | unset |
| [104](104-equivalence-test-misreads-a-flag-valued-anchor.md) | The blindness test lists an axis as blind for a metric whose anchor is a worst-case flag value (`shock_set_distance` follows `translate_x` with rho 1 yet is listed blind to it); needs a decision | unset |
| [106](106-max-error-scores-the-density-impostor-under-the-anchor.md) | `max_error` scores the Gaussian impostor on density near the anchor because density's extreme is one deep minimum on a vortex core; why the harness's 0.955 sits below the per-frame medians near 1.02 is unexplained | unset |
| [097](097-stochastic-ladder-for-comparable-magnitudes.md) | A stochastic ladder (several draws per severity) would make response magnitudes comparable across a metric's functional forms | none set |
| [098](098-increment-w1-registered-number-is-a-convention.md) | The number `increment_w1_by_separation` registers, a normalised mean over separations, is a convention with no source | unset |

## Technical debt

| ID | Title | Priority |
|---|---|---|
| [020](020-import-name-collision.md) | `metrics` is a very generic top-level import name | low |
| [032](032-prose-numbers-can-go-stale.md) | Numbers written into card prose can go stale unnoticed | medium |
| [033](033-link-rewriting-is-only-checked-for-deadness.md) | Site link rewriting is checked for dead links, not correct destinations | medium |
| [100](100-site-shows-citations-as-raw-text.md) | The documentation site shows a card's citations as raw `[@key]` and `\bibliography`, and a bundle's three reference lists disagree | medium |
| [107](107-increment-flatness-drops-a-non-finite-channel.md) | `increment_flatness` silently scores the other channels when one channel holds a NaN or an infinity | low |
| [108](108-field-gallery-hides-the-cell-a-maximum-map-is-about.md) | The report's field gallery clips the colour scale at the 0.995 quantile, saturating the worst cell a `max` map is about, and captions every map as a per-cell share | low |
| [109](109-pointwise-controls-accept-broadcastable-shapes.md) | `mae`, `mse`, `rmse` and `nrmse` return a number for shapes numpy can broadcast, and the contract test's mismatch cannot broadcast | low |
| [099](099-derived-field-read-without-its-inputs.md) | A run that reads vorticity without velocity scores the solver's stored vorticity, not the recomputed one, without warning | medium |
| [036](036-increment-flatness-is-not-monotone-under-smoothing.md) | Increment flatness is not monotone under smoothing on any field, so it fails the stated acceptance rule; needs a decision, not a fix | medium |
| [022](022-sim-config-parsing.md) | Solver configs carry executable YAML tags | low |
| [023](023-vendored-kinet-drift.md) | Vendored kinet code is pinned and may drift | low |
| [045](045-retired-tracker-ids-in-code.md) | Retired tracker IDs remain in code comments, tests and six issues | low |

**The pattern for a new defect**: reproduce it, write the test, mark it `xfail(strict=True)`
naming the issue file, and write the issue with the measurement in front of you. Strict mode is
what makes the loop close — fixing the defect makes the test pass, strict mode turns an
unexpected pass into a failure, and whoever fixed it is sent back to remove the marker and the
issue. Do not delete a marker without fixing the issue it names.
