# Goal-oriented error estimates

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Often a user needs one number from a simulation, such as the drag on a body, a heat flux or a
mixed mass, rather than the whole field. Call it the output $J(U)$ of the state $U$. A field
can carry large errors that barely change $J$, and small errors in one region that change it a
great deal. The dual-weighted-residual estimate locates where the field's error actually
affects the output. With $R(\hat U)$ the residual of the governing equations evaluated on the
prediction $\hat U$, such as the
[residual of the equations in weak form](weak_residual.md), and $\psi$ the solution of the
adjoint problem defined below,

$$
J(U_{\text{ref}}) - J(\hat U) \approx \big\langle \psi,\, R(\hat U) \big\rangle \tag{1}
$$

where $\langle\cdot,\cdot\rangle$ sums the product over all cells. The cell-by-cell product
$\psi_K R_K(\hat U)$ is a map of where the prediction's error drives the output error.

*Derivation sketch, with the sign convention used here.* The reference satisfies
$R(U_{\text{ref}}) = 0$. Linearising about the prediction, with $A = \partial R/\partial U$
the Jacobian of the residual and $g = \partial J/\partial U$ the sensitivity of the output,
gives $R(\hat U) \approx A\,(\hat U - U_{\text{ref}})$, and so

$$
J(U_{\text{ref}}) - J(\hat U) \approx -g^{\mathsf{T}}(\hat U - U_{\text{ref}})
\approx -g^{\mathsf{T}} A^{-1} R(\hat U) .
$$

Defining the adjoint $\psi$ by the linear problem

$$
A^{\mathsf{T}} \psi = -g \tag{2}
$$

turns this into (1). The adjoint carries the sensitivity of the output to a residual placed in
each cell. Published conventions differ in the sign of $\psi$. Once the adjoint is solved, (1)
estimates the output error without the reference field, which makes it usable where no
reference exists.

## Precedent

The method was set out for finite elements as an optimal-control approach to a posteriori
error estimation, meaning an estimate computed after the solution, from the solution (Becker
and Rannacher 2001). In computational fluid dynamics the same adjoint-weighted residuals drive
output-based mesh adaptation, refining the mesh where (1) says the output error comes from
(Fidkowski and Darmofal 2011).

## Pitfalls

- The estimate needs an adjoint solver for the governing equations, linearised about the
  prediction. That is substantial infrastructure, and none exists in the repository.
- Formula (1) is a linearisation, accurate only when the prediction is close to the reference.
- The estimate is blind, by design, to errors that do not affect the declared output, so the
  output must be chosen before the estimate means anything.
- *Added during conversion, not from the field guide or the team:* for a long rollout of chaotic dynamics, an unsteady
  adjoint integrated backward in time grows at the rate of the leading Lyapunov exponent, so
  the linearised estimate is unlikely to hold past a few Lyapunov times.

## Rationale

*From the field guide; the team has not yet set a priority.* The estimate localises where field
error actually affects an engineering output, which ties field accuracy to the quantity a user
needs, and it uses the residual of the prediction rather than a reference field.

## Keywords

dual-weighted residual, adjoint error estimation, output-based error estimation, goal-oriented
a posteriori error estimate, adjoint-based mesh adaptation, quantity of interest.

## References

- Becker, R. & Rannacher, R. (2001). An optimal control approach to a posteriori error
  estimation in finite element methods. *Acta Numerica* 10, 1–102.
  <https://doi.org/10.1017/S0962492901000010>
- Fidkowski, K. J. & Darmofal, D. L. (2011). Review of output-based error estimation and mesh
  adaptation in computational fluid dynamics. *AIAA Journal* 49, 673–694.
  <https://doi.org/10.2514/1.J050073>
