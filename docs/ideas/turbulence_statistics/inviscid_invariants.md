# Helicity, potential vorticity and information transfer across scales

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Energy is not the only quantity that the inviscid equations conserve, and a prediction can
conserve energy while getting the others wrong. This page collects the other conserved
quantities and two measures of how scales are coupled.

**Helicity.** In three dimensions the kinetic helicity

$$
H = \int \mathbf{u} \cdot \boldsymbol{\omega} \, d\mathbf{x} \tag{1}
$$

is conserved by inviscid barotropic flow and measures the linkage and knottedness of vortex lines
(Moffatt 1969; reviewed by Moffatt and Tsinober 1992). Its local form is the relative
helicity density $h_r = \mathbf{u} \cdot \boldsymbol{\omega} / (|\mathbf{u}|
|\boldsymbol{\omega}|) \in [-1, 1]$, the cosine of the angle between velocity and vorticity,
and its scale-by-scale form is the helicity spectrum. Comparing the distribution of $h_r$ and
the helicity spectrum with the reference tests vortex topology, which energy does not
constrain. Unlike the third-order statistics elsewhere in this theme, helicity is quadratic in
the velocity, so a Gaussian field built with the reference's helicity spectrum would reproduce
it; it is a test of topology rather than of non-Gaussianity.

**Two-dimensional cascades.** In two dimensions both energy and enstrophy are inviscid
invariants, and the cascade splits in two: energy moves toward large scales with
$E(k) \propto k^{-5/3}$, while enstrophy moves toward small scales with
$E(k) \propto k^{-3}$ (Kraichnan 1967). A metric tuned to three-dimensional turbulence
misreads both ranges in quasi-two-dimensional, stratified or rotating flows: it expects a
forward energy cascade where there is an inverse one, as noted on the
[four-fifths law](four_fifths_law.md) and [energy-transfer checks](energy_transfer_checks.md)
pages. For two-dimensional data the natural checks are the direction of each cascade and the
spectral slope on each side of the forcing scale.

**Potential vorticity.** In geophysical flows the potential vorticity

$$
q = \frac{(\boldsymbol{\omega} + 2 \boldsymbol{\Omega}) \cdot \nabla \theta}{\rho} \tag{2}
$$

is carried unchanged by each fluid parcel in inviscid, adiabatic flow, and it organises the
large-scale dynamics (Vallis 2017). Here $\boldsymbol{\Omega}$ is the rotation rate of the
frame, $\theta$ the potential temperature and $\rho$ the density. A prediction can be checked
by comparing its potential-vorticity field or distribution with the reference, and by testing
whether potential vorticity is conserved along the rollout where the flow is close to
inviscid and adiabatic.

**Information transfer across scales.** Splitting a field into scale bands, two
information-theoretic quantities describe how the bands depend on one another. The *mutual
information* between two bands measures any statistical dependence, including nonlinear
dependence that a correlation coefficient misses. The *transfer entropy* from a process $Y$
to a process $X$ measures how much the past of $Y$ improves the prediction of the next value
of $X$ beyond what the past of $X$ already gives (Schreiber 2000). With one step of history,

$$
T_{Y \to X} = \sum p(x_{n+1}, x_n, y_n) \,
\log \frac{p(x_{n+1} \mid x_n, y_n)}{p(x_{n+1} \mid x_n)} , \tag{3}
$$

where $p$ denotes probabilities estimated from the data. Unlike mutual information it is
directional, so applied to scale bands it measures the direction of information flow through
the cascade. Tanogami and Araki (2024) relate this information flow between scales to the
energy cascade. Comparing predicted and reference transfer-entropy profiles across scales
tests whether the prediction couples its scales in the same direction.

## Pitfalls

- Helicity is identically zero in planar two-dimensional flow, where velocity and vorticity
  are perpendicular.
- Moffatt (1969) establishes the invariance of helicity for a localised vorticity
  distribution in barotropic inviscid flow under conservative body forces, where the
  pressure is a function of the density alone. Shocked or variable-density flow, in which
  density and pressure gradients are misaligned, is not barotropic, and its helicity can
  change without any error in the prediction. The invariance also needs boundaries that
  vorticity does not cross, which a periodic domain satisfies. Drift along a rollout is
  meaningful only under these conditions.
- Regimes of mixed dimensionality, such as rotating or stratified turbulence, need care in
  deciding which invariants and which cascade directions apply.
- Mutual information and transfer entropy require estimating probability densities from
  samples, which is data-hungry and sensitive to the estimator.

## Rationale

*From the field guide; the team has not yet set a priority.* These quantities detect errors
in vortex topology and in the direction of the cascade, which are invisible to the energy and
its spectrum. For two-dimensional data they also say which of the three-dimensional laws on
the other pages of this theme do not apply.

## Keywords

kinetic helicity, relative helicity, helicity spectrum, dual cascade, inverse energy cascade,
enstrophy cascade, potential vorticity, mutual information, transfer entropy.

## References

- Kraichnan, R. H. (1967). Inertial ranges in two-dimensional turbulence. *Physics of
  Fluids* 10, 1417–1423. <https://doi.org/10.1063/1.1762301>
- Moffatt, H. K. (1969). The degree of knottedness of tangled vortex lines. *Journal of Fluid
  Mechanics* 35, 117–129. <https://doi.org/10.1017/S0022112069000991>
- Moffatt, H. K. & Tsinober, A. (1992). Helicity in laminar and turbulent flow. *Annual Review
  of Fluid Mechanics* 24, 281–312. <https://doi.org/10.1146/annurev.fl.24.010192.001433>
- Schreiber, T. (2000). Measuring information transfer. *Physical Review Letters* 85,
  461–464. <https://doi.org/10.1103/PhysRevLett.85.461>
- Tanogami, T. & Araki, R. (2024). Information-thermodynamic bound on information flow in
  turbulent cascade. *Physical Review Research* 6, 013090.
  <https://doi.org/10.1103/physrevresearch.6.013090>
- Vallis, G. K. (2017). Atmospheric and Oceanic Fluid Dynamics, 2nd edition. *Cambridge
  University Press*. <https://doi.org/10.1017/9781107588417>
