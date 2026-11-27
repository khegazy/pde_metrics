# Dataset specifications for the missing experiments

One document per dataset that `FUTURE_EXPERIMENTS_CATALOG.md` says the metrics need. Each
document tells a person what to prepare: ideally a physical system with an analytic solution,
otherwise a handful of simulated systems from the literature with enough detail to set up the
run, and in every case what to store and what answer is known in advance. Written 2026-11-04
to 2026-11-26 by research sub-agents, one per document; nothing here is built yet.

## The task

Every dataset is analytic (a reader that computes the fields on the fly, with nothing stored),
simulated (kinet first, OpenFOAM or another established solver where kinet cannot run the
system), or public simulation data used as a reference. Candidate fields are made by the
repository's degradation operators or by solver runs degraded in a controlled way: a coarser
grid, a wrong parameter, a more diffusive scheme, a different solver. Nothing in this work
trains, runs or evaluates a machine-learning model. `BUILD_ORDER.md` states the task in full.

## How each document is organised

1. **Front matter**: the catalog cluster IDs it serves, the metrics and ideas it serves, the
   date, and the author agent.
2. **Purpose**: which tests, degradations and metrics need this dataset and why, in one or
   two paragraphs drawn from the catalog.
3. **What the dataset must provide**: fields, dimensionality, boundaries, grid, time cadence,
   duration, number of realisations, and the answers that must be known in advance.
4. **Option A, the analytic ideal**: a physical system with a closed-form solution that gives
   the test its known answer. Governing equations, the solution, its parameters, what is known
   exactly, how it serves each test, and its limits. If no analytic system exists, say so and
   give the nearest thing (a self-similar solution, a known statistic, a manufactured solution).
5. **Options B, C, D (a handful)**: simulated systems from the literature. For each: the
   governing equations and regime, the standard configuration (initial condition, domain,
   boundaries, resolution, parameters) with the source's table or equation number, the
   reference values or figures that are known, the solver or public data that produces it,
   data already on disk under `datasets/` if any, and cost.
6. **Recommendation**: which option to prepare first and why, and what the others add.
7. **What to store**: fields in the repository's vocabulary (density, velocity, pressure,
   vorticity; pressure is never computed from density by repository rule), precision, cadence,
   grid, boundary declaration per axis, following `docs/recipes/add-a-dataset.md`.
8. **References**: full citations with author, year, venue, volume and pages, DOI or link, and
   a note on what was read (full text, abstract, or secondary source).
9. **Confidence**: what the author is sure of, what is reasoning, and what was not checked.

## Rules every author followed

- Every fact beyond graduate common knowledge carries a citation with the equation, table or
  figure number. Nothing is cited from memory alone; a citation that could not be opened is
  marked as such. Conjecture and the author's own choices are labelled.
- Numbers are copied from the source, never estimated and presented as the source's.
- A system is included only if a person could set it up from the document plus the cited
  source.
- Plain, complete sentences; every symbol and technical term defined at first use.

## Build order

`BUILD_ORDER.md` is the one record of the order in which datasets are made, in four phases:
readers for kinet data already on disk, analytic readers, kinet runs, then other solvers and
public data. `00_how_to_use_kinet.md` is the guide for running kinet, verified by small runs.

## Index

| File | Dataset | Catalog clusters |
|---|---|---|
| 00_how_to_use_kinet.md | How to use kinet to simulate datasets | all simulated options |
| 01_physical_ensemble.md | Physical ensemble and independent realisations | D1, G9 |
| 02_grid_refinement_known_solution.md | Grid refinement against a known solution | D5 |
| 03_two_dimensional_shocks.md | Two-dimensional shocks, from closed-form fronts to shocklet turbulence | D3, D8 |
| 04_forced_stationary_turbulence.md | Forced, statistically stationary turbulence with an inertial range | D4, G2 (base period) |
| 05_initial_conditions_and_degraded_solver_runs.md | Trajectories from many initial conditions, with degraded solver runs as candidates | D2, G1 |
| 06_feature_population_generator.md | Feature-population generator: vortices, fronts and bumps with known positions, on the `advecting_blobs` reader | D7, D8, D9, G4, G10 |
| 08_synthetic_ensemble_extensions.md | Synthetic-ensemble extensions with published and closed-form answers | D6 |
| 07_transport_known_answer_pairs.md | Known-answer transport pairs with exact Wasserstein distances | D9 |
| 09_random_fields_known_statistics.md | Random fields with known spectrum, increment statistics, anisotropy and tails | D4 (A3), G2, G3, G5, G10 |
| 10_acoustic_and_helmholtz_fields.md | Acoustic and Helmholtz fields with an exact solenoidal–dilatational split | G6 |
| 11_regime_data.md | Regime data: wall-bounded flow, variable-density mixing, scalar mixing, line-of-sight projections | issues 053, 058, 087, 089, 090, 091 |
