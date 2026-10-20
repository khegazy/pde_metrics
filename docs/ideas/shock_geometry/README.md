# Shock geometry and detection

A shock is a thin layer across which a flow's pressure, density and velocity jump almost
discontinuously. The ideas in this theme work in two steps: first detect where the shocks are
in each field, then compare the detected sets as geometric objects, asking how far apart they
lie rather than how different the field values are cell by cell. Every detector carries a
threshold, and that threshold is fixed once by the evaluator and never tuned per model, or the
metric could be gamed. Some of these measures assume isolated fronts that can be tracked over
time, which is not the motivating case: compressible turbulence populated by many small
shocks, called shocklets. Each page says which of the two it suits.

## Ideas in this theme

- [Shock detector](shock_detector.md): a local sensor, built from pressure gradients and
  compression, that flags which cells are shocked.
- [Distance between extracted shock sets](shock_set_distance.md): surface distances from
  medical imaging that measure how far apart two detected shock sets lie.
- [Overlap of shock masks](shock_mask_overlap.md): cheap overlap scores between detected
  shock regions, and why thin shocks make most of them misleading.
- [Shock front position, speed and jump conditions](shock_front_error.md): position and speed
  errors of a tracked front, and a check that the jump across it obeys conservation.
