# Shock–turbulence interaction statistics

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

When turbulence passes through a shock, the shock amplifies the turbulent fluctuations and the
turbulence wrinkles the shock. These statistics measure both effects, so that a prediction can
be compared with a reference on the physics of the interaction rather than cell by cell.

- **Shock-aligned coordinate.** For each point, the signed distance $d_s$ to the surface found
  by the [shock detector](../../metrics/shock_set_distance.md), negative upstream and positive downstream.
  Statistics are then conditioned on bins of $d_s$, so that they are averaged along the shock
  rather than across it. The same coordinate gives the shock-normal profile of
  [entropy production](../physics_invariants/entropy_production.md).
- **Amplification ratios.** The ratio of a quantity just downstream of the shock to its value
  just upstream, for the turbulent kinetic energy, the Reynolds and Favre stresses (the
  covariances of the velocity fluctuations, the Favre form being weighted by density as
  defined on [one-point statistics](../turbulence_statistics/one_point_statistics.md)), the
  vorticity, the energy of the dilatational part of the velocity from the
  [Helmholtz split](../physics_invariants/helmholtz_split.md), and the density variance. Lee,
  Lele and Moin (1997) found that the amplification of turbulent kinetic energy saturates once
  the upstream Mach number exceeds about 3, and Donzis (2012) proposed the ratio of the
  laminar shock thickness to the Kolmogorov length as the parameter that organises the
  amplification of the streamwise velocity fluctuations in simulations and experiments.
- **Corrugation spectrum.** The wrinkled shock surface, described by its displacement from its
  mean position as a function of position along the surface, has a spectrum $E_s(k_\perp)$
  over the wavenumber $k_\perp$ along the surface. It records at which scales the turbulence
  wrinkles the shock.
- **Shocklet statistics.** For turbulence populated by many small shocks (shocklets), a census:
  the number of shocklets, the distribution of their areas or volumes, the distribution of
  the pressure jump across them, and the distribution of the upstream Mach number normal to
  each. The census is defined only together with a declared detector, a declared rule for
  grouping shocked cells into one shocklet (connected components), and a declared rule for how
  long or how strongly a detection must persist to count.

## Precedent

Eddy shocklets were characterised in decaying compressible turbulence by Lee, Lele and Moin
(1991), and their statistics in compressible isotropic turbulence have been measured directly
(Wang et al. 2017). Several shock-capturing methods have been compared on test problems that
combine turbulence with shocks (Johnsen et al. 2010).

## Pitfalls

- Every statistic here depends strongly on the detector and on how the bins of $d_s$ are
  defined. Both are fixed once by the evaluator and declared with the results.
- Amplification ratios presuppose a well-defined upstream and downstream side. They suit a
  single shock crossed by turbulence; in shocklet-populated turbulence, the shocklet census is
  the natural form.

## Rationale

*From the field guide; the team has not yet set a priority.* These statistics isolate the
physics of amplification across a shock and of the wrinkling of its surface, which a pointwise
norm averages away, and the shocklet census addresses directly the motivating case of
turbulence populated by many small shocks.

## Keywords

shock–turbulence interaction, amplification factors, linear interaction analysis, shock
corrugation, eddy shocklets, shock-aligned conditional statistics, Favre averaging.

## References

- Donzis, D. A. (2012). Amplification factors in shock–turbulence interactions: Effect of
  shock thickness. *Physics of Fluids* 24, 011705. <https://doi.org/10.1063/1.3676449>
- Johnsen, E., Larsson, J., Bhagatwala, A. V., Cabot, W. H., Moin, P., et al. (2010).
  Assessment of high-resolution methods for numerical simulations of compressible turbulence
  with shock waves. *Journal of Computational Physics* 229, 1213–1237.
  <https://doi.org/10.1016/j.jcp.2009.10.028>
- Lee, S., Lele, S. K. & Moin, P. (1991). Eddy shocklets in decaying compressible
  turbulence. *Physics of Fluids A* 3(4), 657–664. <https://doi.org/10.1063/1.858071>
- Lee, S., Lele, S. K. & Moin, P. (1997). Interaction of isotropic turbulence with shock waves:
  effect of shock strength. *Journal of Fluid Mechanics* 340, 225–247.
  <https://doi.org/10.1017/S0022112097005107>
- Wang, J., Gotoh, T. & Watanabe, T. (2017). Shocklet statistics in compressible isotropic
  turbulence. *Physical Review Fluids* 2, 023401.
  <https://doi.org/10.1103/PhysRevFluids.2.023401>
