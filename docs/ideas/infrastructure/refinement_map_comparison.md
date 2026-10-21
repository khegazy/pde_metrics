# Comparing refinement maps across meshes

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Comparing fields that live on different meshes raises two distinct questions. The first is
how to compare such fields at all. That is answered, and is already part of the evaluation
harness: both fields are remapped conservatively onto a common analysis grid, cell averages
are compared rather than point samples, and the remapping operator is recorded as part of the
metric's definition. This idea is the second question.

An *adaptive* solver refines its mesh where a *refinement indicator*, a quantity it computes
from the solution, flags fine-scale structure. The indicator is therefore a statement about
where the solver believes structure lives. Comparing the refinement maps of a prediction and
a reference compares those structural beliefs directly, rather than comparing the field
values.

If this path is pursued, discrete exterior calculus, which supplies operators on meshes that
preserve the structure of their continuous counterparts, becomes relevant; see
[discrete differential geometry on meshes](../curvature/discrete_differential_geometry.md).

## Rationale

*The team's judgement.* Medium priority: the question is genuinely interesting, but unlike the
conservative remap it is not infrastructure that every other metric needs, so it can wait.
