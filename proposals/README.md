# Proposals

Benchmarks, experiments, metrics and variants of metrics that an agent or a person found while
researching, written up so they are not lost, each as one file. **EXP** documents propose a
benchmark or experiment (a standard test problem, a benchmark dataset, a published comparison of
metrics, a degradation, a protocol); **MTR** documents propose a metric or a variant of one.
Each file begins with front matter that is the one record of its kind, related bundles and
idea pages, source and finder, so this index carries only the title and status.

**A proposal is a staging copy.** Once it is accepted it becomes an idea page with a row in
`docs/ideas/README.md`, an issue, or the dataset or degradation work itself, and the proposal is
deleted; a rejected proposal is deleted too. The commit that deletes it says why, as for a
resolved issue (`AGENTS.md` §1). Proposals are not published on the site: they are unreviewed.

Status is `proposed`, or `see also <file>` for a near-duplicate of another proposal.

| File | Title | Status |
|---|---|---|
| [EXP-energy_distance-tail-only-degradation.md](EXP-energy_distance-tail-only-degradation.md) | A degradation that damages only the tails of the increment distribution | see also EXP-tail_index-pareto-spike-injection.md |
| [EXP-orchestrator-20261023-anisotropic-blur.md](EXP-orchestrator-20261023-anisotropic-blur.md) | A directional (anisotropic) blur | proposed |
| [EXP-orchestrator-20261023-constraint-violation.md](EXP-orchestrator-20261023-constraint-violation.md) | Controlled violations of admissibility conditions | proposed |
| [EXP-orchestrator-20261023-dilatational-scaling.md](EXP-orchestrator-20261023-dilatational-scaling.md) | Scaling the dilatational part of the velocity | proposed |
| [EXP-orchestrator-20261023-known-vortex-field.md](EXP-orchestrator-20261023-known-vortex-field.md) | A field with a known vortex population | proposed |
| [EXP-orchestrator-20261023-temporal-ladder.md](EXP-orchestrator-20261023-temporal-ladder.md) | A degradation ladder for trajectories | proposed |
| [EXP-shock_set_distance-2d-shock-dataset.md](EXP-shock_set_distance-2d-shock-dataset.md) | A two-dimensional shock dataset for the shock-set distance | proposed |
| [EXP-sod_evidence-sod-time-offset.md](EXP-sod_evidence-sod-time-offset.md) | The exact Sod solution at a shifted time, as a physically consistent wave-position error | proposed |
| [EXP-spectral_energy_flux-forced-2d-compressible-flux-loop.md](EXP-spectral_energy_flux-forced-2d-compressible-flux-loop.md) | Forced two-dimensional compressible turbulence at Mach 0.3 to 0.5 | proposed |
| [EXP-spectral_energy_flux-graded-phase-randomisation.md](EXP-spectral_energy_flux-graded-phase-randomisation.md) | Graded phase randomisation, an ordinal axis between the reference and the impostor | proposed |
| [EXP-tail_index-pareto-spike-injection.md](EXP-tail_index-pareto-spike-injection.md) | Inject sparse spikes with power-law amplitudes of a known exponent | see also EXP-energy_distance-tail-only-degradation.md |
| [MTR-energy_distance-alpha-exponent.md](MTR-energy_distance-alpha-exponent.md) | Generalised energy distance with exponent alpha | proposed |
| [MTR-energy_distance-by-separation.md](MTR-energy_distance-by-separation.md) | Energy distance between increment distributions at every octave separation | proposed |
| [MTR-energy_distance-cramer-loss.md](MTR-energy_distance-cramer-loss.md) | Squared energy (Cramér) distance of increments as a training loss | proposed |
| [MTR-max_error-high-quantile-error.md](MTR-max_error-high-quantile-error.md) | A high quantile of the pointwise absolute error | proposed |
| [MTR-max_error-mean-of-channel-maxima.md](MTR-max_error-mean-of-channel-maxima.md) | Maximum error averaged over channels (PDEBench's reduction) | proposed |
| [MTR-max_error-vector-magnitude.md](MTR-max_error-vector-magnitude.md) | Maximum of the error vector's length | proposed |
| [MTR-shock_set_distance-full-shock-zone-detector.md](MTR-shock_set_distance-full-shock-zone-detector.md) | The full shock-zone detector, with a compression gate and the jump across the zone | proposed |
| [MTR-shock_set_distance-object-matched-shock-distance.md](MTR-shock_set_distance-object-matched-shock-distance.md) | Object-matched shock distance, after MODE | proposed |
| [MTR-shock_set_distance-other-surface-distance-summaries.md](MTR-shock_set_distance-other-surface-distance-summaries.md) | Hausdorff, quantile-Hausdorff, AVD and MASD summaries of the same shock-set distances | proposed |
| [MTR-shock_set_distance-shock-thickness-and-overshoot.md](MTR-shock_set_distance-shock-thickness-and-overshoot.md) | Shock thickness and overshoot at the detected shocks | proposed |
| [MTR-spectral_energy_flux-enstrophy-flux.md](MTR-spectral_energy_flux-enstrophy-flux.md) | Spectral enstrophy flux of two-dimensional flow | proposed |
| [MTR-spectral_energy_flux-flux-sign-agreement.md](MTR-spectral_energy_flux-flux-sign-agreement.md) | Direction-of-transfer disagreement, a dimension-neutral backscatter fraction | proposed |
| [MTR-tail_index-hill-by-separation.md](MTR-tail_index-hill-by-separation.md) | Hill estimate of the increments at every octave of separation | proposed |
| [MTR-tail_index-ks-threshold.md](MTR-tail_index-ks-threshold.md) | Power-law exponent with a Kolmogorov-Smirnov threshold and a goodness-of-fit p-value | proposed |
| [MTR-tail_index-moment-estimator.md](MTR-tail_index-moment-estimator.md) | Moment (Dekkers-Einmahl-de Haan) estimator of the extreme-value index of increments | proposed |
