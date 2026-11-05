"""1-Wasserstein distance between the persistence diagrams of the reference and the candidate.

The sibling of ``persistence_distance``, on the same diagrams. Where the bottleneck distance
reports the single worst mismatch between the two fields' features, this sums the cost of
every matched feature: each point moved to its partner, or a point with no partner moved onto
the diagonal at half its lifetime. A prediction that gets every vortex slightly wrong, or that
adds many weak spurious features, scores worse than one that gets one feature wrong by the same
largest amount. Like the bottleneck distance it never sees where a feature sits.

The diagram of one field is the companion, the same point set ``persistence_distance`` stores.
"""

from __future__ import annotations

from functools import partial

import gudhi.hera
import numpy as np
from numpy.typing import NDArray

from fmeval.context import FieldContext
from metrics.persistence_distance.metric import diagram_distances, persistence_diagram
from metrics.registry import companion, metric

#: The Wasserstein exponent: 1, the default of GUDHI's ``wasserstein_distance`` (GUDHI 3.13
#: manual, "Wasserstein distance") and of the R package TDA's ``wasserstein``.
ORDER: float = 1.0
#: Hera's bound on the relative error, ``(1 + DELTA)`` times the exact distance (GUDHI 3.13,
#: ``gudhi.hera.wasserstein_distance``). Both libraries default to 0.01; at 1e-6 the value moved
#: by at most 2.3e-4 relative from 0.01 on kinet vorticity, at 1.5 times the cost (measured).
DELTA: float = 1e-6


@metric(
    name="persistence_wasserstein",
    arity="pairwise",
    fields=("density", "vorticity"),   # scalar fields; vorticity is one channel in 2-D only
    differentiable=False,              # no gradient is computed here
    cost="expensive",
    higher_is_better=False,
    symmetric=True,
    units="field",
    requires_periodic=False,           # the complex wraps exactly the axes the grid declares
)
def persistence_wasserstein(reference: NDArray[np.floating], candidate: NDArray[np.floating],
                            *, ctx: FieldContext) -> float:
    """Total 1-Wasserstein distance, with the L-infinity ground norm, between the two diagrams.

    In each homology dimension k, the infimum over matchings of the summed L-infinity
    distances between matched points, a point free to match the diagonal at half its lifetime:
    the degree-p Wasserstein distance of Cohen-Steiner, Edelsbrunner, Harer & Mileyko (2010,
    Found. Comput. Math. 10, 127-139, Sect. 3, "Wasserstein distance"), at p = 1. Points that
    never die are matched among themselves at cost |b - b'| (Skraba & Turner 2020,
    arXiv:2006.16824v7, Definition 2.4). The total over dimensions is the p-th root of the sum
    of the p-th powers (Skraba & Turner, Definition 2.5; Cohen-Steiner et al. 2010, the same
    sum over all dimensions), which at p = 1 is the plain sum.

    Computed by ``gudhi.hera.wasserstein_distance`` (the Hera library, which giotto-tda also
    calls) to a relative error of at most :data:`DELTA`; the exact optimal-transport route
    (``gudhi.wasserstein``) builds a dense cost matrix of 15000 by 15000 points on a 256 x 256
    vorticity field.

    Args:
        reference: The trusted field, shape ``(1, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ctx: The pipeline's context: the grid's boundary types, the candidate's diagram under
            :data:`~fmeval.context.COMPANION_KEY` when the pipeline computed it, and the cache
            that keeps the reference's diagram for the frame.

    Returns:
        The distance in the field's units: zero when the diagrams agree, unbounded above.

    Raises:
        ValueError: If the shapes differ, or a field is not one finite channel.
    """
    # Cohen-Steiner et al. (2010), Sect. 3: W_p = [sum over dimensions and matched points of
    # ||x - gamma(x)||_inf^p]^(1/p); Skraba & Turner (2020), Definition 2.5, for the total.
    distances = diagram_distances(reference, candidate, ctx=ctx, distance=wasserstein)
    return float(np.sum(np.power(distances, ORDER)) ** (1.0 / ORDER))


def wasserstein(a: NDArray[np.floating], b: NDArray[np.floating]) -> float:
    """W_p with the L-infinity ground norm between two diagrams of one dimension.

    A point that never dies is infinitely far from every finite point and from the diagonal
    (Skraba & Turner 2020, Definition 2.4), so an optimal matching pairs the finite points
    among themselves and the points at infinity among themselves, and the p-th power of the
    distance is the sum of the two parts' p-th powers. Hera is called on each part separately:
    handed one diagram with two or more finite points and another with points at infinity only,
    gudhi 3.13's Hera stops the process with a segmentation fault (measured, and covered by
    ``test_metric.py``), where each part alone is computed.

    Args:
        a, b: ``(n, 2)`` and ``(m, 2)`` arrays of (birth, death), death ``inf`` for a point
            that never dies.

    Returns:
        The distance; ``inf`` if the two diagrams have different numbers of points at infinity.
    """
    hera = partial(gudhi.hera.wasserstein_distance, order=ORDER, internal_p=np.inf, delta=DELTA)
    finite_a, finite_b = np.isfinite(a[:, 1]), np.isfinite(b[:, 1])
    parts = (hera(a[finite_a], b[finite_b]), hera(a[~finite_a], b[~finite_b]))
    return float(np.sum(np.power(parts, ORDER)) ** (1.0 / ORDER))


# The diagram of one field, the point set behind the number: persistence_distance's companion,
# registered for this metric too so it is computed once per row and drawn on this card.
companion(of="persistence_wasserstein", kind="points",
          coordinate=(("birth", "field"), ("death", "field"), ("dimension", "")))(
    persistence_diagram)
