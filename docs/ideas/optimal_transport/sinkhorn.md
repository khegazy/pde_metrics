# Entropic relaxation and Sinkhorn divergences

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Entropic relaxation adds an entropy penalty to the optimal-transport problem behind the
[Wasserstein distance](wasserstein.md). The penalty smooths the problem, so it can be solved by
the Sinkhorn algorithm, which alternately rescales the rows and columns of the transport plan
until its row and column sums match the two distributions. A Sinkhorn divergence is the
transport cost computed this way; the debiased version corrects it so that a field is at zero
distance from itself. The related Kantorovich
dual formulation, which writes the same transport cost as a maximisation over functions rather
than a minimisation over transport plans, belongs to the same item.

Sinkhorn divergences are differentiable. That matters if optimal transport later moves from a
diagnostic to a training loss, since a diagnostic may be non-differentiable but a training loss
may not.

## Rationale

*The team's judgement.* Medium priority: this becomes relevant only after the
[Wasserstein distance](wasserstein.md) has shown that it is useful. The open question is
whether Wasserstein helps at all, and that should be answered before its cost is optimised.

## Keywords

Sinkhorn divergence, entropic regularization optimal transport, debiased Sinkhorn divergence,
iterative Bregman projections.
