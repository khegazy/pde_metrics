"""Hausdorff distance between the shocks found in the reference and in the candidate pressure.

The sibling of ``shock_set_distance`` on the same detected shock sets: where that metric
averages every shocked cell's distance to the other field's shocks, this reports the largest
of them, the worst-placed shocked cell of either field. One spurious detection far from any
true shock therefore sets the value alone.
"""

from __future__ import annotations

from functools import partial

import numpy as np
from numpy.typing import NDArray

from fmeval.context import FieldContext
from metrics.registry import companion, metric
from metrics.shock_set_distance.metric import (
    pressure_profile,
    set_distance,
    shock_positions,
    shock_set_score,
    surface_distances,
)


@metric(
    name="shock_set_hausdorff",
    arity="pairwise",
    fields=("pressure",),
    differentiable=False,           # a thresholded detector: the sets change in jumps
    cost="cheap",
    higher_is_better=False,
    symmetric=True,
    monotone_under_smoothing=False,  # a thresholded set changes in jumps, with ties
    units="length",
    requires_periodic=False,
)
def shock_set_hausdorff(reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
                        ctx: FieldContext) -> float:
    """Hausdorff distance between the shock sets of two pressure fields.

    With ``A`` and ``B`` the shocked cells of the reference and the candidate, the larger of
    the two directed Hausdorff distances, Taha & Hanbury (2015), BMC Med. Imaging 15, 29,
    Eqs. (48)-(49)::

        HD(A, B) = max(h(A, B), h(B, A)),   h(A, B) = max_{a in A} min_{b in B} |a - b|

    It equals Baddeley's Delta at p = c = infinity, the largest difference over the grid of the
    two sets' distance maps (spatstat.geom's ``deltametric``, Details), which is how the
    weather-verification package SpatialVx computes it. The empty sets are scored by the
    conventions of ``shock_set_distance`` (``issues/102``), channels are averaged and a
    non-finite field scores NaN.

    Args:
        reference: The trusted pressure, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The pressure being scored, same shape and grid.
        ctx: Supplies the grid spacing, and caches the reference's shock set per frame.

    Returns:
        The distance in the units of the grid spacing: zero when the two shock sets coincide,
        at most the domain's diagonal, and NaN on a non-finite field.

    Raises:
        ValueError: If the shapes differ, or do not match the grid in ``ctx``.
    """
    return shock_set_score(reference, candidate, ctx=ctx, score=partial(
        set_distance, summary=hausdorff))


def hausdorff(a: NDArray[np.bool_], b: NDArray[np.bool_], spacing: tuple[float, ...]) -> float:
    """The larger directed maximum of the nearest-cell distances, Taha & Hanbury Eq. (48)."""
    d_ab, d_ba = surface_distances(a, b, spacing)
    # Taha & Hanbury (2015) Eqs. (48)-(49): HD = max(h(A, B), h(B, A)).
    return float(max(d_ab.max(), d_ba.max()))


# The point set and the line-out behind the number, shared with shock_set_distance.
companion(of="shock_set_hausdorff", kind="points",
          coordinate=(("x", "cells"), ("pressure", "field")))(shock_positions)
companion(of="shock_set_hausdorff", name="profile")(pressure_profile)
