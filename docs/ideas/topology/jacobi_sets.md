# Jacobi sets

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

A *Morse function* is a smooth function whose critical points (where the gradient vanishes)
are all nondegenerate. The Jacobi set of two Morse functions defined on a common
$d$-dimensional manifold is the set of critical points of the restrictions of one function to
the level sets of the other. Equivalently, and more usefully here, it is "the set of points
where the gradients of the functions are parallel" (Edelsbrunner and Harer 2004).

That makes the Jacobi set natively a *comparison* object, which is unusual: most topological
summaries characterise a single field, and the summaries are then compared. For comparing a
prediction against a reference, this is structurally the right shape of tool.

## Precedent

Two points from the source strengthen the case (Edelsbrunner and Harer 2004). There is a
polynomial-time algorithm for the piecewise-linear analogue on triangulations, so the Jacobi
set is computable on discretised data. The authors' own motivating example is oceanography,
where researchers study several attributes of water on a common domain, which is close to
comparing several fields of one flow.

## Rationale

*The team's judgement.* Medium priority, but with the highest upside per unit of obscurity in
the topology theme. The gap is implementation only, rather than mathematics and
implementation, now that the polynomial-time piecewise-linear algorithm is confirmed. This is
the place to look for a distinctive contribution.

## References

- Edelsbrunner, H. & Harer, J. (2004). Jacobi sets of multiple Morse functions. In
  *Foundations of Computational Mathematics, Minneapolis 2002* (Cucker, F., DeVore, R.,
  Olver, P. & Süli, E., eds.), London Mathematical Society Lecture Note Series 312, Cambridge
  University Press, pp. 37–57. <https://doi.org/10.1017/CBO9781139106962.003>
