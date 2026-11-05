"""95th-percentile Hausdorff distance between the shocks of the reference and the candidate.

The sibling of ``shock_set_hausdorff`` that medical image segmentation reports in its place:
each field's shocked cells are measured to the nearest shocked cell of the other field, and the
95th percentile of those distances, taken in each direction, replaces the maximum, so that the
worst few cells (five in a hundred) no longer set the value alone.
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

#: The percentile of each direction's distances: 95, the default of Metrics Reloaded's
#: ``measured_hausdorff_distance_perc`` (Maier-Hein et al. 2024; MetricsReloaded code,
#: ``metrics/pairwise_measures.py``) and the "HD95" of their Suppl. Tab. SN 2.2.
PERCENTILE: float = 95.0


@metric(
    name="shock_set_hausdorff95",
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
def shock_set_hausdorff95(reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
                          ctx: FieldContext) -> float:
    """95th-percentile Hausdorff distance between the shock sets of two pressure fields.

    With ``A`` and ``B`` the shocked cells of the reference and the candidate, the larger of
    the two directed 95th percentiles of the nearest-cell distances::

        HD95(A, B) = max(P95{d(a, B) : a in A}, P95{d(b, A) : b in B})

    the quantile form of the directed Hausdorff distance that Taha & Hanbury (2015), BMC Med.
    Imaging 15, 29, describe after their Eq. (49), at the 95th percentile, computed as Metrics
    Reloaded's code computes it (``np.percentile`` of each direction, linear interpolation,
    then the maximum). medpy's ``hd95`` instead takes the percentile of the two directions
    pooled; the card states the difference. The empty sets are scored by the conventions of
    ``shock_set_distance`` (``issues/102``), channels are averaged and a non-finite field
    scores NaN.

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
        set_distance, summary=hausdorff_percentile))


def hausdorff_percentile(a: NDArray[np.bool_], b: NDArray[np.bool_],
                         spacing: tuple[float, ...]) -> float:
    """The larger of the two directed :data:`PERCENTILE` percentiles of nearest-cell distances."""
    d_ab, d_ba = surface_distances(a, b, spacing)
    # Taha & Hanbury (2015), the quantile method after Eq. (49); MetricsReloaded's
    # measured_hausdorff_distance_perc: max of the two directed percentiles.
    return float(max(np.percentile(d_ab, PERCENTILE), np.percentile(d_ba, PERCENTILE)))


# The point set and the line-out behind the number, shared with shock_set_distance.
companion(of="shock_set_hausdorff95", kind="points",
          coordinate=(("x", "cells"), ("pressure", "field")))(shock_positions)
companion(of="shock_set_hausdorff95", name="profile")(pressure_profile)
