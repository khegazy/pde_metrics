# Curvature and differential geometry

Curvature measures how a curve, a surface or a whole space bends. This theme collects
geometric descriptors of a flow at four levels of abstraction: the curvature of the surfaces
on which a field takes a fixed value, differential geometry built directly on a mesh,
curvature defined without any smooth structure, and the Riemannian curvature of the space of
all ideal-fluid flows. The first has real precedent in combustion; the others are deeper but
further from a routine diagnostic. Edge detection with the Canny and Sobel operators, a cheap
image-processing way to locate shocks, is folded into the
[shock detector](../../metrics/shock_set_distance.md) as an implementation shortcut rather
than listed here as an idea of its own.

## Ideas in this theme

- [Curvature statistics of level sets](isosurface_curvature.md): the distributions of the
  curvature of surfaces of constant density, pressure or vorticity magnitude.
- [Discrete differential geometry on meshes](discrete_differential_geometry.md):
  structure-preserving operators on a mesh, relevant mainly to comparison across meshes.
- [Curvature without smooth structure](metric_geometry_curvature.md): comparison-triangle
  and transport-based notions of curvature, with a track record on networks.
- [Riemann curvature of the flow's configuration space](riemann_curvature.md): Arnold's
  curvature of the group of volume-preserving maps, whose geodesics are ideal-fluid flows.
