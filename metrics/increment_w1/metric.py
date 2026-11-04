"""1-Wasserstein distance between the one-cell increment distributions of two fields.

Rather than transporting the fields themselves, this transports the *distribution* of
their neighbour-to-neighbour differences. That sidesteps the two problems a Wasserstein
distance on the field itself has here -- a signed field is not a measure, and optimal
transport in two dimensions is expensive -- because an increment distribution is
one-dimensional and already a probability measure. In one dimension the transport distance
has a closed form: sort both samples and average the absolute difference of matching
quantiles, so the whole metric is a sort.

What it is sensitive to is the *shape* of the increment distribution, tails included, and
what it is blind to is where in the domain those increments sit. It is therefore
complementary to a pointwise norm by construction rather than by accident: two fields with
identical increment statistics arranged into different structures are at distance zero,
and two fields that differ only by a shift are too.

It is the natural partner of ``increment_flatness``, which summarises the same
distribution by a single moment. This metric compares the whole distribution and so cannot
be fooled by a prediction that matches one moment while getting the rest wrong; the cost
is that it has no absolute anchor the way flatness has its 3.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import FieldContext
from metrics.increment_flatness.metric import (
    SEPARATION_CELLS,
    increment_samples,
    vector_field,
)
from metrics.registry import companion, metric


def sample_w1(a: NDArray[np.floating], b: NDArray[np.floating]) -> float:
    """1-Wasserstein distance between two equally sized samples of increments.

    Both samples have the same number of points, so the quantile form of the 1-Wasserstein
    distance reduces to sorting each and averaging the absolute difference elementwise
    (Peyre & Cuturi 2019, Remark 2.28, Eq. (2.33) with p = 1). That is exact, not an
    approximation: for two empirical measures on the line with equal weights the optimal
    coupling is the monotone one.

    Args:
        a: The reference's increments along one axis of one channel, any shape.
        b: The candidate's matching increments, same size.

    Returns:
        The transport distance, in the field's units. Zero when the two increment
        distributions coincide, which does not require the two fields to coincide.
    """
    return float(np.mean(np.abs(np.sort(a, axis=None) - np.sort(b, axis=None))))


@metric(
    name="increment_w1",
    arity="pairwise",
    fields=("*",),
    differentiable=True,
    cost="cheap",
    higher_is_better=False,
    symmetric=True,
    units="field",
    requires_periodic=True,  # increment_flatness's wrap-around increments
)
def increment_w1(
    reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
    ctx: FieldContext, separation: int = SEPARATION_CELLS, transverse: bool = False,
) -> float:
    """Increment-PDF 1-Wasserstein distance, longitudinal for velocity, averaged over the
    (channel, axis) pairs read.

    The quantile form of the one-dimensional 1-Wasserstein distance (Peyre and Cuturi (2019),
    "Computational Optimal Transport", Foundations and Trends in Machine Learning 11(5-6),
    355-607, DOI 10.1561/2200000073, Remark 2.30, Eq. (2.36), numbered as in arXiv:1803.00567)
    between two empirical measures with equal weights is the mean absolute difference of their
    order statistics (Remark 2.28, Eq. (2.33)).

    Increment statistics are used as physics-based criteria for generative turbulence
    models by Granero-Belinchon and Cabeza Gallucci (2024), Mach. Learn.: Sci. Technol.
    5(2), 025032, DOI 10.1088/2632-2153/ad43b3, on the longitudinal velocity (Sect. 2.1).

    The average runs over the ``(channel, axis)`` pairs of
    :func:`metrics.increment_flatness.metric.increment_samples`, one transport distance each,
    rather than over one pooled sample. Pooling would compare a mixture against a mixture and
    could cancel an error along one axis against an opposite error along another; keeping
    the axes separate cannot. Every pair is included, including one whose increments vanish
    in both fields -- unlike a flatness, a transport distance between two identical
    degenerate distributions is a well-defined zero rather than undefined.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ctx: The pipeline's context; its field name says whether the increments are
            longitudinal.
        separation: The increments' separation in cells. The registered metric is at one cell;
            ``increment_w1_by_separation`` reads the others, so both share this computation.
        transverse: Compare the transverse increments of a vector field instead; the
            ``transverse`` companion reads them.

    Returns:
        Mean transport distance, in the field's units. Zero when every increment
        distribution matches, unbounded above.
    """
    if reference.shape != candidate.shape:
        raise ValueError(
            f"increment_w1 needs matching shapes, got {reference.shape} and "
            f"{candidate.shape}"
        )
    return float(np.mean([
        sample_w1(a, b) for a, b in zip(
            increment_samples(reference, ctx.field, separation, transverse=transverse),
            increment_samples(candidate, ctx.field, separation, transverse=transverse),
            strict=True)
    ]))


@companion(of="increment_w1", name="transverse", kind="curve",
           coordinate=("separation", "cells"))
def increment_w1_transverse(reference: NDArray[np.floating], candidate: NDArray[np.floating],
                            *, ctx: FieldContext) -> tuple[NDArray, NDArray]:
    """(separation, W1_T): the same distance between the transverse increments of a vector
    field, at the registered separation only; its other separations are
    ``increment_w1_by_separation.transverse``. Empty for a field with no transverse
    increments (a scalar, or a one-dimensional vector)."""
    if not vector_field(ctx.field) or reference.ndim < 3:
        return np.array([], dtype=np.int64), np.array([])
    return np.array([SEPARATION_CELLS]), np.array([
        increment_w1(reference, candidate, ctx=ctx, transverse=True)])
