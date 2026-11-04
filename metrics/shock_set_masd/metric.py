"""Mean average surface distance between the shocks of the reference and the candidate.

The sibling of ``shock_set_distance`` that Metrics Reloaded recommends as its default boundary
distance: the mean of the two directed average distances, each field's shocked cells measured
to the nearest shocked cell of the other. Where ``shock_set_distance`` pools every distance and
so weights the field with more shocked cells more, this gives the two directions equal weight.
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
    name="shock_set_masd",
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
def shock_set_masd(reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
                   ctx: FieldContext) -> float:
    """Mean average surface distance between the shock sets of two pressure fields.

    With ``A`` and ``B`` the shocked cells of the reference and the candidate and
    ``d(A, B) = (1/|A|) sum_{a in A} min_{b in B} |a - b|`` the directed average distance
    (Taha & Hanbury 2015, BMC Med. Imaging 15, 29, Eq. (51))::

        MASD(A, B) = (d(A, B) + d(B, A)) / 2

    as Metrics Reloaded's code computes it (``measured_masd``, ``metrics/pairwise_measures.py``;
    Maier-Hein et al. 2024, Nature Methods 21, 195-212, Suppl. Note 2.3, recommend it as the
    default boundary distance when errors are to be penalised by distance). The empty sets are
    scored by the conventions of ``shock_set_distance`` (``issues/102``), channels are averaged
    and a non-finite field scores NaN.

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
        set_distance, summary=mean_average_surface_distance))


def mean_average_surface_distance(a: NDArray[np.bool_], b: NDArray[np.bool_],
                                  spacing: tuple[float, ...]) -> float:
    """The mean of the two directed average nearest-cell distances."""
    d_ab, d_ba = surface_distances(a, b, spacing)
    # MetricsReloaded measured_masd: 0.5 * (mean d(A, B) + mean d(B, A)); Taha & Hanbury
    # (2015) Eq. (51) for each directed mean.
    return float(0.5 * (d_ab.mean() + d_ba.mean()))


# The point set and the line-out behind the number, shared with shock_set_distance.
companion(of="shock_set_masd", kind="points",
          coordinate=(("x", "cells"), ("pressure", "field")))(shock_positions)
companion(of="shock_set_masd", name="profile")(pressure_profile)
