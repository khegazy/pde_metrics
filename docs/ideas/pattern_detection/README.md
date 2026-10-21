# Pattern and feature detection

The ideas in this theme first find coherent structures in a field, such as eddies, vortices
and shock fronts, and then compare what was found rather than comparing the fields cell by
cell. The highest-priority idea is the winding angle, a standard vortex detector from the
scientific visualisation literature that also finds weak vortices. The classical vortex
criteria serve as the cheap baseline against which it is judged, and the eddy census turns
either detector's output into distributions that can be compared. The Hough transform is the
one idea here for which no precedent was found in the literature.

## Ideas in this theme

- [Hough transform for eddy size](hough_transform.md): detecting circles and lines by voting
  in a space of shape parameters, an untested idea for finding eddies and shock fronts.
- [Winding angle and Poincaré index](winding_angle.md): counting how far streamlines turn, a
  vortex detector that does not depend on the local speed of the flow.
- [Eddy census](eddy_census.md): comparing the distributions of the number, size and lifetime
  of detected eddies.
- [Vortex criteria: Q, λ₂ and Okubo–Weiss](vortex_criteria.md): the established pointwise
  vortex-identification criteria, as a cheap baseline.
