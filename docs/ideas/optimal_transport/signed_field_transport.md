# Transport between signed fields

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Optimal transport compares two nonnegative distributions of equal total mass, so it cannot be
applied directly to a pressure or velocity field, which can be negative and need not conserve
its total. The [Wasserstein distance](wasserstein.md) therefore needs one of four standard
ways around these two constraints.

1. **Split into positive and negative parts.** Write the field as the difference of two
   nonnegative fields and transport each part separately.
2. **Add a constant and renormalise.** Shift the field until it is nonnegative and rescale it
   to unit total. This is crude, and the size of the constant is a tunable parameter.
3. **Unbalanced optimal transport.** In the Hellinger–Kantorovich formulation, transport is
   allowed to create and destroy mass as well as move it, at a price. The two fields then
   need not have the same total.
4. **Graph-space optimal transport.** Instead of treating the data values as mass, compare
   the discrete graph of the data: the set of points (position, value) that plots the field.
   Those points are always a valid set to transport, whatever the sign of the values. This
   handles signed data with no fixed total natively, and it keeps the property that makes
   transport attractive in the first place: the misfit stays convex with respect to shifts,
   meaning it grows steadily as a feature is displaced further, with no false minimum
   (Métivier et al. 2018, *Geophysics*).

## Precedent

The graph-space approach comes from seismic full-waveform inversion, where the signals being
compared are oscillating and signed. It grew out of the same group's earlier
optimal-transport misfit for seismograms (Métivier et al. 2016). It has since been
generalised into a family of distances that contains the $L^p$ distances as special cases
(Métivier et al. 2019).

## Rationale

*The team's judgement.* High priority: this is the single idea that makes the
[Wasserstein distance](wasserstein.md) usable on real pressure and velocity fields. It is a
mathematical gap, but one the seismic community has already filled, so the work is importing
a known solution rather than inventing one.

## Keywords

unbalanced optimal transport, Hellinger–Kantorovich, graph-space OT, partial optimal
transport, signed measure transport.

## References

- Métivier, L., Brossier, R., Mérigot, Q., Oudet, E. & Virieux, J. (2016). Measuring the
  misfit between seismograms using an optimal transport distance: Application to full
  waveform inversion. *Geophysical Journal International* 205(1), 345–377.
  <https://doi.org/10.1093/gji/ggw014>
- Métivier, L., Allain, A., Brossier, R., Mérigot, Q., Oudet, E. & Virieux, J. (2018).
  Optimal transport for mitigating cycle skipping in full-waveform inversion: A graph-space
  transform approach. *Geophysics* 83(5), R515–R540. <https://doi.org/10.1190/geo2017-0807.1>
- Métivier, L., Brossier, R., Mérigot, Q. & Oudet, E. (2019). A graph space optimal transport
  distance as a generalization of $L^p$ distances: application to a seismic imaging inverse
  problem. *Inverse Problems* 35(8), 085001. <https://doi.org/10.1088/1361-6420/ab206f>
