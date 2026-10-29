"""1-Wasserstein distance between increment distributions at every separation, and one number.

``increment_w1`` compares the distributions of one-cell increments. This metric compares them at
every octave of separation, 1, 2, 4, ... cells up to half the smallest side of the grid, so the
scale at which a prediction's increment statistics depart from the reference's is visible: the
curve of distances is the metric's companion, stored on every row in the field's units, exactly
as the transport distance is defined. The number registered for the panel is the mean over
separations of each distance divided by the reference's mean absolute increment at that
separation. No source fixes that summary: it is a repository convention (``issues/098``), chosen
because the increments grow with separation, so a plain mean would be carried by the largest
separations, the ones a blur changes least.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import COMPANION_KEY, FieldContext
from metrics.increment_flatness.metric import increments
from metrics.increment_w1.metric import increment_w1
from metrics.registry import companion, metric

#: ``ctx.cache`` key of the reference's mean absolute increment at each separation.
REFERENCE_SCALE = "increment_w1_by_separation/reference_scale"


def octave_separations(shape: tuple[int, ...]) -> NDArray[np.int64]:
    """1, 2, 4, ... cells, up to half the smallest spatial extent of ``shape``.

    Raises:
        ValueError: If an axis has fewer than two cells: there is no separation to read, and the
            mean over none would be NaN rather than a number.
    """
    largest = min(shape) // 2
    if largest < 1:
        raise ValueError(f"increment separations need at least two cells along every spatial "
                         f"axis; the spatial shape is {tuple(shape)}")
    return 2 ** np.arange(int(np.log2(largest)) + 1)


def mean_absolute_increment(x: NDArray[np.floating],
                            separations: NDArray[np.int64]) -> NDArray[np.float64]:
    """The mean of ``|x(r + l) - x(r)|`` at each separation ``l``, averaged over channels and
    spatial axes as ``increment_w1`` averages its distances."""
    n_spatial = x.ndim - 1
    return np.array([np.mean([np.mean(np.abs(increments(channel, axis, separation=int(l))))
                              for channel in x for axis in range(-n_spatial, 0)])
                     for l in separations])


@metric(
    name="increment_w1_by_separation",
    arity="pairwise",
    fields=("*",),
    differentiable=True,
    cost="moderate",
    higher_is_better=False,
    symmetric=False,             # normalised by the reference's increments
    units="dimensionless",
    requires_periodic=True,      # increment_flatness's wrap-around increments
)
def increment_w1_by_separation(reference: NDArray[np.floating], candidate: NDArray[np.floating],
                               *, ctx: FieldContext | None = None) -> float:
    """Mean over octave separations of W1(l) / <|delta_l u_ref|>; a convention, issues/098.

    ``W1(l)`` is the 1-Wasserstein distance between the increment distributions at separation
    ``l`` (:func:`increment_w1_curve`); ``<|delta_l u_ref|>`` the reference's mean absolute
    increment there. Each separation is made dimensionless against the reference at that
    separation before the mean, so every separation weighs alike. A separation at which the
    reference has no increments at all contributes 0 when the candidate has none either and
    is infinite otherwise.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ctx: The pipeline's context. Its cache supplies the curve for this variant and keeps the
            reference's increment scale for the frame; without it both are computed here.

    Returns:
        A dimensionless number, zero when every increment distribution matches.
    """
    cache = ctx.cache if ctx is not None else {}
    separations, distances = (cache[COMPANION_KEY] if COMPANION_KEY in cache
                              else increment_w1_curve(reference, candidate))
    if REFERENCE_SCALE not in cache:
        cache[REFERENCE_SCALE] = mean_absolute_increment(reference, separations)
    scale = cache[REFERENCE_SCALE]
    distances = np.asarray(distances, dtype=float)
    ratio = np.divide(distances, scale, out=np.where(distances == 0, 0.0, np.inf),
                      where=scale > 0)
    return float(np.mean(ratio))


@companion(of="increment_w1_by_separation", kind="curve", coordinate=("separation", "cells"))
def increment_w1_curve(reference: NDArray[np.floating],
                       candidate: NDArray[np.floating]) -> tuple[NDArray, NDArray]:
    """(separations, W1(l)): the transport distance between increment distributions at each
    octave separation, in the field's units. At one cell it is ``increment_w1`` itself."""
    separations = octave_separations(reference.shape[1:])
    return separations, np.array([increment_w1(reference, candidate, separation=int(l))
                                  for l in separations])
