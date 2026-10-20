# Winding angle and Poincaré index

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

A *streamline* is a curve that is everywhere tangent to the velocity field. Its *winding
angle* is the total angle through which its direction turns along its length, so a streamline
that circles a vortex accumulates a large winding angle. Sadarjoen and Post present two
methods for detecting vortex structures in two-dimensional vector fields, both based on
streamline geometry. The second "looks at the curvature of a single streamline and computes a
winding angle, a metric of geometric curvature" (Sadarjoen and Post 2000). A vortex detector
of this kind yields a structural count that is integer- or angle-valued and robust to
translation.

The integer-valued relative of the winding angle is the *Poincaré index* of a critical point,
a point where the velocity vanishes. The index counts how many times the velocity vector turns
around as one travels once around a small loop enclosing the point. It underpins *vector field
topology*, the description of a flow by its critical points and the streamlines that connect
them, which Helman and Hesselink introduced for fluid flow data (Helman and Hesselink 1989,
1991).

The idea was first recorded under the informal name "wake number". Reading that name as a
winding quantity is the team's interpretation, which the existence of the winding-angle method
supports but does not prove.

## Precedent

The documented advantage of the winding-angle method is directly relevant here: because the
winding angle does not depend on the velocity magnitude at a single point, the method detects
weak vortices, which criteria based on amplitude miss (Sadarjoen and Post 2000). An earlier
version of the same geometric approach appears in Sadarjoen and Post (1999).

This work is hard to find in the fluid dynamics literature because of its vocabulary. It lives
in the scientific visualisation community under "vector field topology" and "winding angle",
not in fluid dynamics journals. A state-of-the-art survey with a full bibliography is Laramee
et al. (2007).

## Pitfalls

- A large number of streamlines must be seeded and computed to keep complete coverage of the
  domain (Sadarjoen and Post 2000).
- The method is clean in two dimensions. Helman and Hesselink present the two-dimensional
  theory of critical points as the basis from which three-dimensional separated flows are then
  examined (Helman and Hesselink 1989, 1991).

## Rationale

*The team's judgement.* High priority. The priority was raised from medium to high because the
winding angle turns out to be a standard, implemented vortex-detection method with documented
strengths and weaknesses (Sadarjoen and Post 2000). An integer- or angle-valued structural
count that is robust to translation is orthogonal to every continuous metric among these
ideas. The method is implemented and surveyed, and its strengths and weaknesses are documented
rather than speculative. Its specific strength, detecting weak vortices independently of the
local velocity magnitude, is precisely what an over-smoothed surrogate model would erase. Work
should start in two dimensions.

## Keywords

vector field topology, winding angle.

## References

- Helman, J. L. & Hesselink, L. (1989). Representation and display of vector field topology in
  fluid flow data sets. *Computer* 22(8), 27–36. <https://doi.org/10.1109/2.35197>
- Helman, J. L. & Hesselink, L. (1991). Visualizing vector field topology in fluid flows. *IEEE
  Computer Graphics and Applications* 11(3), 36–46. <https://doi.org/10.1109/38.79452>
- Laramee, R. S., Hauser, H., Zhao, L. & Post, F. H. (2007). Topology-based flow
  visualization, the state of the art. In *Topology-based Methods in Visualization*, Springer,
  Berlin, pp. 1–19. <https://doi.org/10.1007/978-3-540-70823-0_1>
- Sadarjoen, I. A. & Post, F. H. (1999). Geometric methods for vortex detection. In *Data
  Visualization '99* (VisSym '99), Springer, pp. 53–62.
- Sadarjoen, I. A. & Post, F. H. (2000). Detection, quantification, and tracking of vortices
  using streamline geometry. *Computers & Graphics* 24(3), 333–341.
  <https://doi.org/10.1016/S0097-8493(00)00029-7>
