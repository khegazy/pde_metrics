# Galilean and rotational equivariance

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The Euler and Navier–Stokes equations take the same form in every inertial frame and in every
orientation of the axes. A model that has learned the physics, rather than the frame of its
training data, should share these symmetries. A map $\mathcal{M}$ is *equivariant* under a
transformation $T$ when transforming the input and then applying the map gives the same
result as applying the map and then transforming the output. The test applies $T$ to an
initial state $u_0$, runs the model, and compares:

$$
\epsilon_T = \frac{\big\|\mathcal{M}(T u_0) - T'\,\mathcal{M}(u_0)\big\|}
{\big\|\mathcal{M}(u_0)\big\|} \tag{1}
$$

Here $T'$ is the same transformation as it acts at the output time; for a rotation $T' = T$,
and for a boost the two differ, as below. The score needs no reference field, but it needs the
model itself, because the model must be run on transformed inputs. Most other metrics consume
stored predictions only.

**Galilean boost.** If a flow with density $\rho(\mathbf{x}, t)$, velocity
$\mathbf{u}(\mathbf{x}, t)$ and pressure $p(\mathbf{x}, t)$ solves the equations, so does the
flow seen from a frame moving at constant velocity $-\mathbf{c}$:
$\rho(\mathbf{x} - \mathbf{c}t, t)$, $\mathbf{u}(\mathbf{x} - \mathbf{c}t, t) + \mathbf{c}$
and $p(\mathbf{x} - \mathbf{c}t, t)$. A compressible solver usually carries the conservative
variables: density, momentum $\rho\mathbf{u}$ and total energy $\rho E$, where
$E = e + \tfrac12|\mathbf{u}|^2$ and $e$ is the internal energy per unit mass. Substituting
$\mathbf{u} + \mathbf{c}$ for $\mathbf{u}$, with $\rho$ and $e$ unchanged, gives the boost on
these variables:

$$
\rho \to \rho, \qquad
\rho\mathbf{u} \to \rho(\mathbf{u} + \mathbf{c}), \qquad
\rho E \to \rho E + \rho\mathbf{u}\cdot\mathbf{c} + \tfrac12 \rho |\mathbf{c}|^2 \tag{2}
$$

The last expression follows from expanding the kinetic energy:

$$
\tfrac12\rho|\mathbf{u} + \mathbf{c}|^2
= \tfrac12\rho|\mathbf{u}|^2 + \rho\mathbf{u}\cdot\mathbf{c} + \tfrac12\rho|\mathbf{c}|^2 .
$$

The boost is applied at three sizes, $|\mathbf{c}|/u_{\text{rms}} \in \{0.1, 1, 10\}$, where
$u_{\text{rms}}$ is the root-mean-square velocity of the flow. At the output time $t$, $T'$
applies (2) and also translates the field by $\mathbf{c}t$, which on a periodic grid is
generally a shift by a fraction of a cell and needs spectral interpolation.

**Rotation.** A rotation or reflection $Q$ of the axes acts on a scalar such as density by
$\rho(\mathbf{x}) \to \rho(Q^{\mathsf{T}}\mathbf{x})$ and on a vector by
$\mathbf{u}(\mathbf{x}) \to Q\,\mathbf{u}(Q^{\mathsf{T}}\mathbf{x})$: the velocity components
rotate as well as the positions. On a square or cubic periodic grid only rotations by
multiples of 90 degrees and reflections map the grid onto itself; any other angle needs
interpolation, which adds its own error.

**Statistical symmetry.** A related check needs no model access. If the flow is nominally
isotropic, any anisotropy measured in the prediction's statistics, such as unequal energy in
the three velocity components, is itself an error.

The built degradations include rigid translations of the field
([translate](../../degradations/translate.md),
[translate_subpixel](../../degradations/translate_subpixel.md),
[random_large_translation](../../degradations/random_large_translation.md)). Those move a
reference field in space to test how a metric responds. A boost is a different transformation:
it acts in velocity space, changing every velocity by the same amount, and it is applied to the
model's input to test the model.

## Precedent

Learned turbulence closures have built Galilean and rotational invariance into the model, by
constructing the network or its input features so that they do not change under these
transformations (Ling et al. 2016; Wu et al. 2018).

## Pitfalls

- An equivariant model is not an accurate one. The identity map, which returns its input
  unchanged, is exactly equivariant under rotations (it is not under a boost, whose $T'$
  includes the shift by $\mathbf{c}t$), and so is a model whose architecture is equivariant
  by construction, for which the test checks only the implementation.
- The symmetries hold only where the boundary conditions share them. Walls, inflow and outflow
  boundaries, and forcing fixed to the grid break Galilean invariance, and a non-square domain
  breaks the 90-degree rotations.
- *Added during conversion, not from the field guide or the team:* the reference solver need not be exactly Galilean
  invariant either, because the numerical dissipation of an upwind scheme depends on the flow
  speed relative to the grid. The model's equivariance error is then best compared with the
  solver's own under the same boost.

## Rationale

*From the field guide; the team has not yet set a priority.* Equivariance is a structural
property, independent of pointwise error: a model can have small error on the training frame
and still fail it. The test probes whether the model has learned the physics or the frame of
its training data, needs no reference field, and costs only a few extra model evaluations.

## Keywords

Galilean invariance, Galilean boost, rotational equivariance, frame indifference, tensor basis
neural network, invariant input features, statistical isotropy.

## References

- Ling, J., Kurzawski, A. & Templeton, J. (2016). Reynolds averaged turbulence modelling using
  deep neural networks with embedded invariance. *Journal of Fluid Mechanics* 807, 155–166.
  <https://doi.org/10.1017/jfm.2016.615>
- Wu, J.-L., Xiao, H. & Paterson, E. (2018). Physics-informed machine learning approach for
  augmenting turbulence models: A comprehensive framework. *Physical Review Fluids* 3, 074602.
  <https://doi.org/10.1103/PhysRevFluids.3.074602>
