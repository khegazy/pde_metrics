# Shock geometry and detection

A shock is a thin layer across which a flow's pressure, density and velocity jump almost
discontinuously. The ideas in this theme work in two steps: first detect where the shocks are
in each field, then compare the detected sets as geometric objects, asking how far apart they
lie rather than how different the field values are cell by cell. Every detector carries a
threshold, and that threshold is fixed once by the evaluator and never tuned per model, or the
metric could be gamed. Some of these measures assume isolated fronts that can be tracked over
time, which is not the motivating case: compressible turbulence populated by many small
shocks, called shocklets. Each page says which of the two it suits.

The first step and the first comparison are built: the built
[shock_set_distance](../../metrics/shock_set_distance.md) holds the detector, a pressure-jump
test, as shared code, and measures the average distance between the two detected sets.

## Ideas in this theme

- [Overlap of shock masks](shock_mask_overlap.md): cheap overlap scores between detected
  shock regions, and why thin shocks make most of them misleading.
- [Shock front position, speed and jump conditions](shock_front_error.md): position and speed
  errors of a tracked front, and a check that the jump across it obeys conservation.
- [Shock–turbulence interaction statistics](shock_turbulence_interaction.md): statistics
  conditioned on distance from a shock, amplification across it, wrinkling of its surface,
  and the census of shocklets.
