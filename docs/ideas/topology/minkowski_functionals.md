# Minkowski functionals and tensors

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Threshold a scalar field $f$ at a level $\nu$ and look at the *excursion set*, the region
where $f\ge\nu$. Minkowski functionals measure the shape of that region. In $d$ dimensions
there are $d+1$ of them. In three dimensions they are the volume, the surface area, the
integrated mean curvature of the surface and the Euler characteristic, which counts
connected pieces minus tunnels plus enclosed cavities; in two dimensions they are the area,
the boundary length and the Euler characteristic. Recording all of them as functions of the
threshold $\nu$ gives a set of curves that summarise the field's morphology, and the metric
compares the predicted curves with the reference's (Mecke, Buchert & Wagner 1994; Schmalzing
& Buchert 1997).

What makes this set special is a completeness theorem. By Hadwiger's theorem, any measure of
shape that is unchanged by rigid motions, additive (the measure of a union is the sum of the
measures minus that of the intersection) and continuous is, on convex bodies, a linear
combination of the $d+1$ Minkowski functionals (Mecke, Buchert & Wagner 1994). Within that
class of shape measures, the Minkowski functionals are a complete vector, not an arbitrary
selection.

Scalar Minkowski functionals are blind to orientation: a field stretched in one direction
and the same field stretched in another give the same values. *Minkowski tensors* are
tensor-valued generalisations that restore this sensitivity, so that the anisotropy of a
structure, such as the alignment of sheets or tubes, can be measured and compared
(Schröder-Turk et al. 2013).

The Euler characteristic is shared with the topology of
[persistence diagrams](persistence_diagrams.md): the Euler-characteristic curve described
there is one of these functionals. The others add geometry, the size and curvature of the
excursion sets, that topology deliberately ignores.

## Precedent

Mecke, Buchert and Wagner introduced Minkowski functionals as robust morphological measures
of the large-scale structure of the Universe (Mecke, Buchert & Wagner 1994), and Schmalzing
and Buchert unified the approach with the earlier genus statistics of cosmology (Schmalzing &
Buchert 1997). The field guide also lists them as the structure check in its panel for
[variable-density mixing](../regime_specific/variable_density_mixing.md).

## Pitfalls

- Scalar Minkowski functionals are blind to anisotropy by construction; the tensors are
  needed for that.
- Like other shape statistics, they say nothing about amplitudes beyond the thresholds or
  about where in the domain the structures sit.
- Estimates of curvature and of the Euler characteristic on a grid depend on how the
  excursion set's boundary is reconstructed, which must be declared once and kept fixed.

## Rationale

*From the field guide; the team has not yet set a priority.* Hadwiger's theorem makes the
Minkowski functionals a complete morphology vector rather than a hand-picked list, they need
no reference aligned in phase with the prediction, and the tensors extend them to the
anisotropy that scalar measures miss.

## Keywords

Minkowski functionals, Minkowski tensors, Hadwiger's theorem, excursion sets, genus
statistics, Euler characteristic, morphology, anisotropy.

## References

- Mecke, K., Buchert, T. & Wagner, H. (1994). Robust morphological measures for large-scale
  structure in the Universe. *Astronomy & Astrophysics* 288, 697–704.
  <https://ui.adsabs.harvard.edu/abs/1994A%26A...288..697M>
- Schmalzing, J. & Buchert, T. (1997). Beyond genus statistics: a unifying approach to the
  morphology of cosmic structure. *The Astrophysical Journal Letters* 482, L1–L4.
  <https://doi.org/10.1086/310680>
- Schröder-Turk, G. E. et al. (2013). Minkowski tensors of anisotropic spatial structure.
  *New Journal of Physics* 15, 083028. <https://doi.org/10.1088/1367-2630/15/8/083028>
