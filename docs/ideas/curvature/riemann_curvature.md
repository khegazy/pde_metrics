# Riemann curvature of the flow's configuration space

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Every arrangement of the particles of an incompressible fluid filling a domain $D$ is a
volume-preserving diffeomorphism of $D$: a smooth, invertible map of the domain onto itself
that preserves volume. These maps form a group, $\mathrm{SDiff}(D)$, and the motion of an
ideal fluid traces a path through it. Arnold extends Euler's theorems on the geodesics of the
rotation group $SO(3)$ with a left-invariant metric, which describe the free rotation of a
rigid body, to arbitrary Lie groups, and in particular to $\mathrm{SDiff}(D)$. A geodesic is
a path of locally shortest length, and the geodesics of $\mathrm{SDiff}(D)$ are the flows of
ideal fluids. This yields stability criteria for nonlinear hydrodynamics. Arnold also
computes the Riemannian curvature of $\mathrm{SDiff}(D)$ and finds it *negative in most
sections* (Arnold 1966).

The analytic foundation, showing that these groups can be treated as infinite-dimensional
manifolds on which the Euler equations are genuinely geodesic, is due to Ebin and Marsden
(Ebin and Marsden 1970). The modern textbook treatment is Arnold and Khesin (Arnold and
Khesin 1998).

## Rationale

*The team's judgement.* Low priority as a near-term metric. Computing sectional curvatures of
the diffeomorphism group for a discrete velocity field is a research project in itself. The
physical content it would deliver, a predictability horizon arising from negative curvature,
is already available far more cheaply from Lyapunov exponents, the rates at which nearby
trajectories separate, and from decorrelation times. It is the right answer to a question
that can already be answered another way.

## References

- Arnold, V. I. (1966). Sur la géométrie différentielle des groupes de Lie de dimension
  infinie et ses applications à l'hydrodynamique des fluides parfaits. *Annales de
  l'Institut Fourier* 16(1), 319–361. <https://doi.org/10.5802/aif.233>
- Arnold, V. I. & Khesin, B. A. (1998). *Topological Methods in Hydrodynamics*. Applied
  Mathematical Sciences 125, Springer, New York.
- Ebin, D. G. & Marsden, J. E. (1970). Groups of diffeomorphisms and the motion of an
  incompressible fluid. *Annals of Mathematics* 92(1), 102–163.
  <https://doi.org/10.2307/1970699>
