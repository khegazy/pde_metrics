# Consistency with one step of a trusted solver

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Take the model's predicted field, advance it by one small step using a trusted numerical
solver, and measure how far the model's own next state lies from the solver's. This is the
evaluation-side mirror of solver-in-the-loop training, in which a numerical solver is part
of the training loop. It requires no ground truth, and it remains meaningful long after the
predicted trajectory has decorrelated from any reference.

It needs a trusted solver in the repository. The planned
[solver predictor for the degradation ladder](../infrastructure/degradation_ladder_reference.md),
a Boltzmann solver, would provide one.

## Pitfalls

- A small one-step residual can still conceal slow secular drift, an error that accumulates
  steadily over many steps. Pair this metric with conservation drift measured over the full
  rollout.

## Rationale

*The team's judgement.* High priority: like the
[residual of the equations in weak form](weak_residual.md), it is reference-free, and it is
nearly free once a trusted solver is in the repository.
