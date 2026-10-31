"""Bottleneck distance between the persistence diagrams of the reference and the candidate.

Sweep a threshold up through a scalar field and watch the region below it: connected pieces and
loops appear and later merge or fill in. Each such feature is a point (birth, death) of the
field's persistence diagram, one diagram per homology dimension. The metric is the bottleneck
distance between the two fields' diagrams: the smallest amount by which every point of one has to
move, to a point of the other or onto the diagonal, to turn it into the other. The diagram does not
record where a feature sits, so a feature that is right in shape and depth but displaced costs
nothing, where a pointwise norm charges it twice.

The diagram of one field is the metric's companion, a point set stored on the chosen frames. The
Betti and Euler-characteristic curves are read off the same diagram by :func:`betti_curves` and
:func:`euler_characteristic_curve`, for a metric built on those curves to import.
"""

from __future__ import annotations

import gudhi
import numpy as np
from numpy.typing import NDArray

from fmeval.context import COMPANION_KEY, FieldContext
from metrics.registry import companion, metric

#: ``ctx.cache`` key of the reference's diagram, computed once per frame.
REFERENCE_DIAGRAM = "persistence_distance/reference_diagram"


@metric(
    name="persistence_distance",
    arity="pairwise",
    fields=("density", "vorticity"),   # scalar fields; vorticity is one channel in 2-D only
    differentiable=False,              # no gradient is computed, and one pair sets the value
    cost="expensive",
    higher_is_better=False,
    symmetric=True,
    units="field",
    requires_periodic=False,           # the complex wraps exactly the axes the grid declares
)
def persistence_distance(reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
                         ctx: FieldContext) -> float:
    """Largest bottleneck distance, over homology dimensions, between the two diagrams.

    For each homology dimension k the bottleneck distance is the infimum over bijections between
    the two diagrams, each with the diagonal added at infinite multiplicity, of the largest
    L-infinity displacement of a point (Cohen-Steiner, Edelsbrunner & Harer 2005, Proc. SoCG,
    263-271, Sect. 3.1, Definition of d_B; journal version Discrete Comput. Geom. 37(1),
    103-120, 2007). Their Main Theorem (Sect. 3.1) bounds it, for each k, by the largest pointwise
    difference of the two fields, so the maximum over k is bounded by it too. The distance
    between the diagrams of all dimensions is the supremum over k of the per-dimension distances,
    each dimension matched on its own (Skraba & Turner 2020, arXiv:2006.16824, Eq. 1), the
    limit p -> inf of their total p-Wasserstein distance (Definition 2.5). Points that never die
    are kept and matched among themselves, as Cohen-Steiner et al. place them at infinity in the
    extended plane.

    Computed by ``gudhi.bottleneck_distance`` at its default precision, an additive error of the
    smallest positive double and possibly the last two or three bits of the mantissa (GUDHI
    3.13 manual, "Bottleneck distance"). Identical diagrams return exactly 0 without calling it:
    the identity bijection moves nothing, and gudhi is slowest on that case.

    Args:
        reference: The trusted field, shape ``(1, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ctx: The pipeline's context: the grid's boundary types, the candidate's diagram under
            :data:`~fmeval.context.COMPANION_KEY` when the pipeline computed it, and the cache
            that keeps the reference's diagram for the frame.

    Returns:
        The distance in the field's units: zero when the diagrams agree, never more than the
        largest absolute difference between the fields.

    Raises:
        ValueError: If the shapes differ, or a field is not one finite channel.
    """
    if reference.shape != candidate.shape:
        raise ValueError(f"persistence_distance needs matching shapes, got {reference.shape} "
                         f"and {candidate.shape}")
    if REFERENCE_DIAGRAM not in ctx.cache:
        ctx.cache[REFERENCE_DIAGRAM] = persistence_diagram(reference, ctx=ctx)
    first = ctx.cache[REFERENCE_DIAGRAM]
    second = (ctx.cache[COMPANION_KEY] if COMPANION_KEY in ctx.cache
              else persistence_diagram(candidate, ctx=ctx))
    distances = []
    for k in range(reference.ndim):          # homology dimensions 0 .. n_spatial
        a, b = first[first[:, 2] == k, :2], second[second[:, 2] == k, :2]
        same = a.shape == b.shape and np.array_equal(a[np.lexsort(a.T)], b[np.lexsort(b.T)])
        # Cohen-Steiner et al. (2005), Sect. 3.1: d_B = inf over bijections of the largest
        # L-infinity displacement, the diagonal free to absorb points.
        distances.append(0.0 if same else gudhi.bottleneck_distance(a, b))
    # Skraba & Turner (2020), Eq. 1: the supremum over dimensions of the per-dimension distances.
    return float(max(distances))


@companion(of="persistence_distance", kind="points",
           coordinate=(("birth", "field"), ("death", "field"), ("dimension", "")))
def persistence_diagram(x: NDArray[np.floating], *, ctx: FieldContext) -> NDArray[np.float64]:
    """The persistence diagram of one scalar field's sublevel sets, every homology dimension.

    The field is a cubical complex in which each grid cell is a top-dimensional cube carrying
    the cell's value, and every lower-dimensional face takes the smallest value of the cubes it
    bounds: the T-construction (Bleile, Garin, Heiss, Maggs & Robins 2022, Research in
    Computational Topology 2, AWM Series 30, 1-26, Definition 4.4; "Method 1" of Skraba & Turner
    2020, arXiv:2006.16824, Sect. 5.1), the one that matches cell averages and connects cells
    that touch at a corner. Each axis the grid declares periodic is
    wrapped, so on a doubly periodic grid the complex is the torus (their Sect. 4.2) and the full
    complex has Betti numbers 1, 2, 1. Computed with ``gudhi.PeriodicCubicalComplex`` (GUDHI 3.13
    manual, "Cubical complex"), coefficients in gudhi's default field Z/11, and intervals of zero
    length dropped (gudhi's default ``min_persistence=0``).

    A point (b, d) is a feature born when the threshold reaches b and gone when it reaches d, so
    it is alive on [b, d); a feature of the whole domain never dies and has d = +inf
    (Cohen-Steiner, Edelsbrunner & Harer 2005, Sect. 2, Definition of the persistence diagram).

    Args:
        x: One scalar field, shape ``(1, *spatial)``.
        ctx: Supplies the grid's boundary type along each axis.

    Returns:
        An ``(N, 3)`` array of rows (birth, death, dimension), in the field's units except the
        dimension, ordered by dimension.

    Raises:
        ValueError: If ``x`` has more than one channel or a non-finite value: the diagram of a
            vector field, or of a field with holes in it, is not defined here.
    """
    if x.shape[0] != 1:
        raise ValueError(f"persistence_distance takes one scalar channel, got {x.shape[0]}; "
                         "a vector field has no sublevel sets")
    if not np.isfinite(x).all():
        raise ValueError("persistence_distance needs a finite field: a sublevel set is not "
                         "defined at a NaN or infinite cell")
    # Bleile et al. (2022), Definition 4.4: cells as top-dimensional cubes (the T-construction);
    # wrapping every periodic axis makes the complex the torus of their Sect. 4.2.
    cubical = gudhi.PeriodicCubicalComplex(
        top_dimensional_cells=np.asarray(x[0], dtype=np.float64),
        periodic_dimensions=[b == "periodic" for b in ctx.grid.boundary])
    cubical.compute_persistence()
    return np.concatenate([
        np.column_stack([pairs, np.full(len(pairs), k)])
        for k in range(x.ndim)
        for pairs in [np.reshape(cubical.persistence_intervals_in_dimension(k), (-1, 2))]])


def betti_curves(diagram: NDArray[np.floating], thresholds: NDArray[np.floating],
                 n_dimensions: int) -> NDArray[np.int64]:
    """Betti numbers of the sublevel set at each threshold, one row per homology dimension.

    The k-th Betti number at threshold t is the number of points of the dimension-k diagram
    with b <= t < d: the k-Triangle Lemma (Cohen-Steiner, Edelsbrunner & Harer 2005, Sect. 2)
    with x = y = t.

    Args:
        diagram: Rows (birth, death, dimension), as :func:`persistence_diagram` returns.
        thresholds: The thresholds, any shape-``(T,)`` array.
        n_dimensions: How many homology dimensions to count, 0 .. n_dimensions - 1.

    Returns:
        An integer array of shape ``(n_dimensions, T)``.
    """
    t = np.asarray(thresholds, dtype=float)[None, :]
    # Cohen-Steiner et al. (2005), Sect. 2, k-Triangle Lemma at x = y = t: count b <= t < d.
    return np.array([((d[:, :1] <= t) & (t < d[:, 1:2])).sum(axis=0)
                     for k in range(n_dimensions) for d in [diagram[diagram[:, 2] == k]]],
                    dtype=np.int64).reshape(n_dimensions, -1)


def euler_characteristic_curve(diagram: NDArray[np.floating], thresholds: NDArray[np.floating],
                               n_dimensions: int) -> NDArray[np.int64]:
    """Euler characteristic of the sublevel set at each threshold, the alternating sum of the
    Betti numbers of :func:`betti_curves`: chi(t) = beta_0(t) - beta_1(t) + beta_2(t) - ...
    (the Euler-Poincare formula)."""
    signs = (-1) ** np.arange(n_dimensions)
    return signs @ betti_curves(diagram, thresholds, n_dimensions)
