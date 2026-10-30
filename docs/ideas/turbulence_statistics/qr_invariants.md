# Joint distribution of the velocity-gradient invariants Q and R

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

At each point the velocity gradient tensor $A_{ij} = \partial u_i / \partial x_j$ has three
eigenvalues $\lambda$, the roots of its characteristic equation
$\lambda^3 + P \lambda^2 + Q \lambda + R = 0$. The coefficients are invariants, unchanged by
rotating the coordinate axes. For incompressible flow the trace vanishes, $P = 0$, and the
other two are

$$
Q = -\tfrac{1}{2} \operatorname{tr}(A^2) = \tfrac{1}{2} \bigl( \|\Omega\|^2 - \|S\|^2 \bigr),
\qquad
R = -\det A = -\tfrac{1}{3} \operatorname{tr}(A^3) , \tag{1}
$$

where $S$ and $\Omega$ are the symmetric (strain) and antisymmetric (rotation) parts of $A$.
$Q$ is the quantity used by the $Q$-criterion on
[vortex criteria](../pattern_detection/vortex_criteria.md). The curve

$$
27 R^2 + 4 Q^3 = 0 \tag{2}
$$

divides the $(Q, R)$ plane: above it $A$ has a pair of complex eigenvalues and the local flow
spirals, and below it all three eigenvalues are real and the local flow is strain-dominated.
The signs of $Q$ and $R$ further separate stretching from compressing configurations, which
gives a complete classification of local flow topology (Chong, Perry and Cantwell 1990).

The idea is to compute the joint probability density of $(Q, R)$ over the domain, normalised
by a gradient scale such as $\langle \|S\|^2 \rangle$ so that shape rather than overall
gradient level is compared, and to measure the distance between the predicted and reference
densities with a distance between distributions such as the
[sliced Wasserstein distance](../optimal_transport/sliced_wasserstein.md) or the
[energy_distance](../../metrics/energy_distance.md).

In turbulence this joint density has a characteristic teardrop shape, with a tail along the
lower-right branch of the curve (2), where $Q < 0$ and $R > 0$, known as the Vieillefosse
tail. Chong, Perry and Cantwell (1990) supply the classification behind Equation (2), not
the measured shape, and no primary source for the shape has yet been checked for this page.

A Gaussian field cannot produce the asymmetry. Replacing $A$ by $-A$ leaves $Q$ unchanged
and reverses the sign of $R$, and a zero-mean Gaussian field has the same statistics as its
negative, so its joint density is symmetric under $R \to -R$: it has no teardrop and no tail.

## Pitfalls

- The invariants depend on accurate gradients, so the density is sensitive to resolution.
- In planar two-dimensional flow the gradient tensor has a zero row and column, so $R = 0$
  identically and $Q$ reduces to $-\tfrac{1}{4}$ times the Okubo–Weiss parameter on
  [vortex criteria](../pattern_detection/vortex_criteria.md). The joint density is then
  one-dimensional and adds little beyond that criterion.
- In compressible flow $P = -\nabla \cdot \mathbf{u}$ is not zero, and the classification of
  Chong, Perry and Cantwell uses all three invariants. The two-dimensional $(Q, R)$ plane is
  then a slice of a three-dimensional space.

## Rationale

*From the field guide; the team has not yet set a priority.* The joint density is a compact
fingerprint of the topology produced by vortex stretching, it is cheap once gradients exist,
and a Gaussian field with the right spectrum fails it outright, having neither the teardrop
nor the tail.

## Keywords

velocity gradient invariants, Q–R plane, teardrop, Vieillefosse tail, local flow topology,
critical-point classification.

## References

- Chong, M. S., Perry, A. E. & Cantwell, B. J. (1990). A general classification of
  three-dimensional flow fields. *Physics of Fluids A* 2, 765–777.
  <https://doi.org/10.1063/1.857730>
