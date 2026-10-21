# Infrastructure and protocol

The ideas in this theme are not metrics in themselves. They are the machinery every metric
is tested with: how fields from different meshes are put side by side, what the trusted
reference is, and how predictions of known quality are produced so that a metric's response
to them can be recorded. Others are the machinery a surrogate is evaluated with: the
uncertainty attached to each metric value, the baselines a score is read against, how a
checkpoint is chosen, and how sensitive a surrogate is to its input. Much of the machinery
for testing metrics is built and described on the [protocol page](../../protocol.md). What
remains is listed here.

Built already, and so not listed here: the conservative remap onto a common analysis grid,
which is part of the evaluation harness; the degradation-ladder harness itself, described on
the [protocol page](../../protocol.md); and the Gaussian-impostor canary
([gaussian_impostor](../../degradations/gaussian_impostor.md)). Projecting a field onto
planes and comparing the projections is folded into the
[sliced Wasserstein distance](../optimal_transport/sliced_wasserstein.md), and is kept only
as a visualisation task rather than as a separate metric.

## Ideas in this theme

- [Comparing refinement maps across meshes](refinement_map_comparison.md): comparing where
  two adaptive solvers chose to refine their meshes, as a comparison of where each believes
  structure lives.
- [Reference and solver predictor for the degradation ladder](degradation_ladder_reference.md):
  the low-Reynolds-number reference simulation and the trusted solver, degraded in
  controlled steps, that the protocol was specified against.
- [Uncertainty on every metric value](metric_uncertainty.md): a block-bootstrap interval on
  each reported value, and a comparison of prediction and reference scaled by both of their
  uncertainties.
- [Selecting checkpoints by rollout](checkpoint_selection.md): a procedure that chooses a
  checkpoint from autoregressive rollouts rather than the one-step validation loss, and
  diagnoses exposure bias.
- [Baseline predictors](baseline_predictors.md): persistence, interpolation, a coarse solver
  and standard neural architectures, run on the same data so that a surrogate's score can
  be read against them.
- [Grid convergence of the reference](grid_convergence.md): the observed order, Richardson
  extrapolation and the Grid Convergence Index, which bound the reference's own
  discretisation error.
- [Robustness against the equations' own sensitivity](robustness.md): how much a surrogate's
  output responds to a perturbed input, compared with how much the equations respond.
