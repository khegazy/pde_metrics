# Entropic relaxation and Sinkhorn divergences

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Entropic relaxation adds an entropy penalty to the optimal-transport problem behind the
[Wasserstein distance](../../metrics/wasserstein.md). The penalty smooths the problem, so it can be solved by
the Sinkhorn algorithm, which alternately rescales the rows and columns of the transport plan
until its row and column sums match the two distributions. A Sinkhorn divergence is the
transport cost computed this way; the debiased version corrects it so that a field is at zero
distance from itself. The related Kantorovich
dual formulation, which writes the same transport cost as a maximisation over functions rather
than a minimisation over transport plans, belongs to the same item.

Sinkhorn divergences are differentiable. That matters if optimal transport later moves from a
diagnostic to a training loss, since a diagnostic may be non-differentiable but a training loss
may not. Sinkhorn divergences are proposed as distributional training losses alongside the
maximum mean discrepancy, of which the built [energy_distance](../../metrics/energy_distance.md) is one instance.
A quantity used as a loss then ceases to be an independent validation metric, so a Sinkhorn
loss must be checked by metrics it was not trained on; the training counterparts of
evaluation metrics are collected in [designing an evaluation](../evaluation_design.md).

## Rationale

*The team's judgement.* Medium priority: this becomes relevant only after the
[Wasserstein distance](../../metrics/wasserstein.md) has shown that it is useful. The open question is
whether Wasserstein helps at all, and that should be answered before its cost is optimised.

## Keywords

Sinkhorn divergence, entropic regularization optimal transport, debiased Sinkhorn divergence,
iterative Bregman projections.
