# Helmholtz split into rotational and compressive parts

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Vorticity, the curl of the velocity, measures local rotation. Diagnostics built on it are
contaminated near shocks, because the velocity gradient there is dominated by compression
rather than rotation. The principled remedy is the Helmholtz decomposition of the velocity
$\mathbf{u}$ into a solenoidal part, which is divergence-free and carries the rotation, and
a dilatational part, which is curl-free and carries the compression:

$$
\mathbf{u} = \mathbf{u}_{\text{sol}} + \mathbf{u}_{\text{dil}},
\qquad \nabla\cdot\mathbf{u}_{\text{sol}} = 0,
\qquad \nabla\times\mathbf{u}_{\text{dil}} = \mathbf{0} \tag{1}
$$

Curl-based diagnostics, such as [enstrophy](../../metrics/enstrophy.md), are then computed on
$\mathbf{u}_{\text{sol}}$ alone, and shock diagnostics, such as the
[shock detector](../shock_geometry/shock_detector.md), on $\mathbf{u}_{\text{dil}}$.

In compressible turbulence the same split is applied to the energy spectrum. The spectra of
the solenoidal and dilatational parts, computed from density-weighted (Favre) quantities as
defined on [one-point statistics](../turbulence_statistics/one_point_statistics.md), are
compared separately with the reference's. A prediction can match the total spectrum while
putting too much energy into compression or too little, and only the split spectra show it.
The dilatational energy is also one of the quantities amplified across a shock, compared on
[shock–turbulence interaction statistics](../shock_geometry/shock_turbulence_interaction.md),
and pressure dilatation, which exchanges kinetic and internal energy and involves only the
dilatational part because $\nabla \cdot \mathbf{u}_{\text{sol}} = 0$, is one of the exchange
terms of the compressible budget on [energy-transfer checks](../turbulence_statistics/energy_transfer_checks.md).

## Precedent

The Ducros family of shock sensors embodies the same logic point by point. They gate on the
ratio of dilatation (the divergence of the velocity) to dilatation plus vorticity, in order
to avoid mistaking intense vortical regions for shocks (Ducros et al. 1999). Eddy shocklets,
the small shocks that form inside compressible turbulence, were characterised in exactly this
decomposed language (Lee et al. 1991).

## Rationale

*The team's judgement.* High priority: the split is standard practice in the
compressible-turbulence community, and it yields a principled version of
[splitting a field into smooth and sharp parts](../norms/mollification_split.md) in which the
split is defined by physics rather than by an arbitrary smoothing scale.

## Keywords

Helmholtz decomposition, solenoidal dilatational split, compressible turbulence
decomposition, eddy shocklets, solenoidal and dilatational spectra, Favre average.

## References

- Ducros, F., Ferrand, V., Nicoud, F., Weber, C., Darracq, D., Gacherieu, C. & Poinsot, T.
  (1999). Large-eddy simulation of the shock/turbulence interaction. *Journal of
  Computational Physics* 152(2), 517–549. <https://doi.org/10.1006/jcph.1999.6238>
- Lee, S., Lele, S. K. & Moin, P. (1991). Eddy shocklets in decaying compressible
  turbulence. *Physics of Fluids A* 3(4), 657–664. <https://doi.org/10.1063/1.858071>
