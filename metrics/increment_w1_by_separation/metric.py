"""1-Wasserstein distance between increment distributions at every separation, and one number.

``increment_w1`` compares the distributions of one-cell increments. This metric compares them at
every octave of separation, 1, 2, 4, ... cells up to half the smallest side of the grid, so the
scale at which a prediction's increment statistics depart from the reference's is visible: the
curve of distances is the metric's companion, stored on every row in the field's units, exactly
as the transport distance is defined. The number registered for the panel is the mean over
separations of each distance divided by the reference's mean absolute increment at that
separation. No source fixes that summary: it is a repository convention (``issues/098``), chosen
because the increments grow with separation, so a plain mean would be carried by the largest
separations, the ones a blur changes least. For velocity the increments are the longitudinal ones,
and the transverse curve is a second companion.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import COMPANION_KEY, FieldContext
from metrics.increment_flatness.metric import increment_samples, octave_separations, vector_field
from metrics.increment_w1.metric import increment_w1
from metrics.registry import companion, metric

#: ``ctx.cache`` key of the reference's mean absolute increment at each separation.
REFERENCE_SCALE = "increment_w1_by_separation/reference_scale"


def mean_absolute_increment(x: NDArray[np.floating], separations: NDArray[np.int64],
                            field: str) -> NDArray[np.float64]:
    """The mean of ``|x(r + l) - x(r)|`` at each separation ``l``, averaged over the
    (channel, axis) pairs ``increment_w1`` reads, longitudinal for velocity."""
    return np.array([np.mean([np.mean(np.abs(d))
                              for d in increment_samples(x, field, int(l))])
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
                               *, ctx: FieldContext) -> float:
    """Mean over octave separations of W1(l) / <|delta_l u_ref|>; a convention, issues/098.

    ``W1(l)`` is the 1-Wasserstein distance between the increment distributions at separation
    ``l``, longitudinal for velocity (:func:`increment_w1_curve`); ``<|delta_l u_ref|>`` the
    reference's mean absolute increment there, over the same increments. Each separation is
    made dimensionless against the reference at that separation before the mean, so every
    separation weighs alike. A separation at which the reference has no increments at all
    contributes 0 when the candidate has none either and is infinite otherwise.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ctx: The pipeline's context. Its field name says whether the increments are
            longitudinal; its cache supplies the curve for this variant and keeps the
            reference's increment scale for the frame.

    Returns:
        A dimensionless number, zero when every increment distribution matches.
    """
    separations, distances = (ctx.cache[COMPANION_KEY] if COMPANION_KEY in ctx.cache
                              else increment_w1_curve(reference, candidate, ctx=ctx))
    if REFERENCE_SCALE not in ctx.cache:
        ctx.cache[REFERENCE_SCALE] = mean_absolute_increment(reference, separations, ctx.field)
    scale = ctx.cache[REFERENCE_SCALE]
    distances = np.asarray(distances, dtype=float)
    ratio = np.divide(distances, scale, out=np.where(distances == 0, 0.0, np.inf),
                      where=scale > 0)
    return float(np.mean(ratio))


@companion(of="increment_w1_by_separation", kind="curve", coordinate=("separation", "cells"))
def increment_w1_curve(reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
                       ctx: FieldContext) -> tuple[NDArray, NDArray]:
    """(separations, W1(l)): the transport distance between increment distributions, longitudinal
    for velocity, at each octave separation, 1, 2, 4, ... cells up to half the smallest side of
    the grid (:func:`~metrics.increment_flatness.metric.octave_separations`, which refuses a grid
    with an axis of one cell), in the field's units. At one cell it is ``increment_w1`` itself."""
    separations = octave_separations(reference.shape[1:])
    return separations, np.array([increment_w1(reference, candidate, ctx=ctx, separation=int(l))
                                  for l in separations])


@companion(of="increment_w1_by_separation", name="transverse", kind="curve",
           coordinate=("separation", "cells"))
def increment_w1_curve_transverse(reference: NDArray[np.floating],
                                  candidate: NDArray[np.floating], *,
                                  ctx: FieldContext) -> tuple[NDArray, NDArray]:
    """(separations, W1_T(l)): the same curve for the transverse increments of a vector field.
    Empty for a field with no transverse increments (a scalar, or a one-dimensional vector)."""
    if not vector_field(ctx.field) or reference.ndim < 3:
        return np.array([], dtype=np.int64), np.array([])
    separations = octave_separations(reference.shape[1:])
    return separations, np.array([
        increment_w1(reference, candidate, ctx=ctx, separation=int(l), transverse=True)
        for l in separations])
