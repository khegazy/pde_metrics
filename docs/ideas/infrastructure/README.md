# Infrastructure and protocol

The ideas in this theme are not metrics in themselves. They are the machinery every metric
is tested with: how fields from different meshes are put side by side, what the trusted
reference is, and how predictions of known quality are produced so that a metric's response
to them can be recorded. Most of this machinery is built and described on the
[protocol page](../../protocol.md). What remains is listed here.

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
