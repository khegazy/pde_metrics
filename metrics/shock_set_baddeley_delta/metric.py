"""Baddeley's Delta between the shocks found in the reference and in the candidate pressure.

The binary-image distance that spatial forecast verification applies to thresholded fields:
every cell of the grid, shocked or not, is given its distance to the nearest shocked cell of
each field, and the root mean square of the difference of the two distance maps is reported.
Unlike the Hausdorff distance, which it equals at an infinite exponent, every cell contributes,
so one spurious detection far from the true shock moves it only in proportion to the cells it
is nearest to.
"""

from __future__ import annotations

from functools import partial

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import distance_transform_edt

from fmeval.context import FieldContext
from metrics.registry import companion, metric
from metrics.shock_set_distance.metric import (
    pressure_profile,
    set_distance,
    shock_positions,
    shock_set_score,
)

#: The exponent p: 2, the default of spatstat.geom's ``deltametric`` (Baddeley's own
#: implementation) and of SpatialVx's ``locmeasures2d``, which calls it.
P: float = 2.0


@metric(
    name="shock_set_baddeley_delta",
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
def shock_set_baddeley_delta(reference: NDArray[np.floating], candidate: NDArray[np.floating],
                             *, ctx: FieldContext) -> float:
    """Baddeley's Delta, p = 2 and no cutoff, between the shock sets of two pressure fields.

    With ``A`` and ``B`` the shocked cells of the reference and the candidate, ``d(x, S)`` the
    Euclidean distance from the centre of cell ``x`` to the nearest cell of ``S``, ``w(t) =
    min(t, c)`` and ``N`` the number of cells::

        Delta(A, B) = [ (1/N) sum_x |w(d(x, A)) - w(d(x, B))|^p ]^(1/p)

    as spatstat.geom's ``deltametric`` computes it on a pixel image (Baddeley 1992, through
    spatstat's documentation of the function and its source): the mean over the window of the
    p-th power of the difference of the two distance maps, each cut off at ``c``. Its defaults,
    p = 2 and c = infinity, are SpatialVx's too, Gilleland's verification package, whose
    documentation cites Gilleland (2011, Weather Forecasting 26, 409-415) for the metric;
    c = infinity leaves the maps uncut. The distance
    transform measures across the domain and never around it. The empty sets, where a distance
    map is infinite, are scored by the conventions of ``shock_set_distance`` (``issues/102``):
    the domain's diagonal bounds Delta between two non-empty sets, since it bounds the Hausdorff
    distance. Channels are averaged and a non-finite field scores NaN.

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
        set_distance, summary=baddeley_delta))


def baddeley_delta(a: NDArray[np.bool_], b: NDArray[np.bool_],
                   spacing: tuple[float, ...]) -> float:
    """Delta between two non-empty sets: the L^p mean over every cell of the distance maps'
    difference, with no cutoff (c = infinity)."""
    d_a = distance_transform_edt(~a, sampling=spacing)
    d_b = distance_transform_edt(~b, sampling=spacing)
    # spatstat.geom deltametric (Baddeley 1992): mean over the window of |d_A - d_B|^p, ^(1/p).
    return float(np.mean(np.abs(d_a - d_b) ** P) ** (1.0 / P))


# The point set and the line-out behind the number, shared with shock_set_distance.
companion(of="shock_set_baddeley_delta", kind="points",
          coordinate=(("x", "cells"), ("pressure", "field")))(shock_positions)
companion(of="shock_set_baddeley_delta", name="profile")(pressure_profile)
