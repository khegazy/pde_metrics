"""Hill estimate of the tail index of one-cell increments: how slowly their largest values decay.

A single-field metric, the same shape as ``increment_flatness``: it characterises one field, so
the pipeline evaluates it on the reference and on every degraded variant, and the drift between
them is what is read. Where flatness summarises the whole increment distribution by its fourth
moment, this reads only its largest values. The Hill estimator (Hill 1975) is the mean log-ratio
of the k largest absolute increments to the (k+1)-th largest; for a sample whose tail decays as a
power law it estimates the extreme-value index, the reciprocal of the power.

The registered number uses the k = ceil(sqrt(n)) largest of the n increments along each axis, one
of the two fixed rules Clauset, Shalizi and Newman (2009, Sect. 3.5) name for choosing k. The
curve behind it, the Hill estimate against k on a logarithmic scale, is the companion.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import COMPANION_KEY, FieldContext
from metrics.increment_flatness.metric import increments
from metrics.registry import companion, metric

#: Coordinates of the curve: k = ceil(n ** theta) order statistics at theta = 0.1, 0.2, ..., 0.9,
#: the order on a logarithmic scale. The spacing of a tenth is this bundle's choice; theta = 1/2
#: is the registered number's k.
THETAS = np.arange(1, 10) / 10

#: The registered number's exponent: k = ceil(n ** (1/2)), the largest sqrt(n) observations,
#: Clauset, Shalizi & Newman (2009), SIAM Rev. 51(4), Sect. 3.5.
REGISTERED_THETA = 0.5


@metric(
    name="tail_index",
    arity="single",
    fields=("*",),
    differentiable=True,      # a sort and logarithms: piecewise smooth, as increment_w1's sort
    cost="cheap",
    higher_is_better=False,   # no direction of its own: the drift from the reference is what is
                              # read, in either direction, as for increment_flatness
    symmetric=False,
    units="dimensionless",
    # A statistic of the shape of the largest increments, which smoothing has no reason to move
    # one way. On the contract test's synthetic blur ladder (sigma = 0, 0.5, 1, 2, 4 cells) it
    # reads 0.114, 0.131, 0.113, 0.106, 0.082: up, then down.
    monotone_under_smoothing=False,
    requires_periodic=True,   # increment_flatness's wrap-around increments
)
def tail_index(x: NDArray[np.floating], *, ctx: FieldContext | None = None) -> float:
    """Hill estimate of the extreme-value index of |one-cell increments| at k = ceil(sqrt(n)).

    The Hill estimator (Hill 1975, Ann. Stat. 3(5), 1163-1174), in the form of Boucheron and
    Thomas (2015, Electron. J. Stat. 9(2), 2751-2792, Sect. 1), evaluated at the largest
    ``ceil(sqrt(n))`` order statistics, the fixed rule of Clauset, Shalizi and Newman (2009,
    SIAM Rev. 51(4), 661-703, Sect. 3.5). It is the point ``theta = 1/2`` of
    :func:`tail_index_curve`, read from ``ctx.cache`` when the pipeline has computed the curve.

    Args:
        x: The field to characterise, shape ``(C, *spatial)`` on the analysis grid.
        ctx: The pipeline's context, whose cache holds this row's curve; without it the curve is
            computed here.

    Returns:
        The mean over (channel, axis) pairs of the Hill estimate; dimensionless and non-negative.
        NaN when no pair has a positive (k+1)-th largest absolute increment, as on a constant
        field.
    """
    cache = ctx.cache if ctx is not None else {}
    thetas, values = cache[COMPANION_KEY] if COMPANION_KEY in cache else tail_index_curve(x)
    return float(np.asarray(values)[np.flatnonzero(np.asarray(thetas) == REGISTERED_THETA)[0]])


@companion(of="tail_index", kind="curve", coordinate=("theta", "log k / log n"))
def tail_index_curve(x: NDArray[np.floating]) -> tuple[NDArray, NDArray]:
    """(theta, Hill estimate at k = ceil(n ** theta)): the Hill plot with the order on a log scale.

    For each channel and each spatial axis the absolute one-cell increments ``|delta|`` (``n`` of
    them, one per cell) are sorted into ``X_(1) >= X_(2) >= ... >= X_(n)``, and

        H(k) = (1/k) * sum_{i=1..k} ln(X_(i) / X_(k+1))

    the Hill estimator in the form of Boucheron and Thomas (2015, Electron. J. Stat. 9(2),
    2751-2792, Sect. 1; Hill 1975, Ann. Stat. 3(5), 1163-1174). ``k`` is ``ceil(n ** theta)``,
    capped at ``n - 1`` so that ``X_(k+1)`` exists. A pair whose ``X_(k+1)`` is zero has no
    finite estimate at that ``k`` and is left out of the mean over pairs, as
    ``increment_flatness`` leaves out an axis with no increments; the mean over pairs, rather than
    one pooled sample, is that bundle's rule too, so an anisotropic field is not read as a mixture.

    Args:
        x: The field, shape ``(C, *spatial)`` on the analysis grid.

    Returns:
        ``(THETAS, values)``; a value is NaN where no pair has a finite estimate.

    Raises:
        ValueError: If the field has fewer than two cells, so no k can be formed.
    """
    n = int(np.prod(x.shape[1:]))
    if n < 2:
        raise ValueError(f"the Hill estimator needs at least two cells; the spatial shape is "
                         f"{tuple(x.shape[1:])}")
    # k = ceil(n^theta), capped so X_(k+1) exists (this bundle's choice); theta = 1/2 is the
    # largest-sqrt(n) rule of Clauset, Shalizi & Newman (2009), SIAM Rev. 51(4), Sect. 3.5.
    ks = np.minimum(np.ceil(n ** THETAS).astype(int), n - 1)
    estimates = []
    for channel in x:
        for axis in range(-(x.ndim - 1), 0):
            top = np.sort(np.abs(increments(channel, axis)), axis=None)[::-1][: ks.max() + 1]
            with np.errstate(divide="ignore", invalid="ignore"):
                logs = np.log(top)
                # Boucheron & Thomas (2015), Sect. 1: mean of ln X_(i), i <= k, minus ln X_(k+1).
                hill = np.cumsum(logs)[ks - 1] / ks - logs[ks]
            estimates.append(np.where(top[ks] > 0, hill, np.nan))
    # Mean over the pairs with an estimate, increment_flatness's Eq. (3) rule (this bundle's
    # choice to follow it); NaN at a theta where no pair has one.
    estimates = np.array(estimates)
    defined = np.isfinite(estimates)
    counts = defined.sum(axis=0)
    sums = np.where(defined, estimates, 0.0).sum(axis=0)
    values = np.divide(sums, counts, out=np.full(len(THETAS), np.nan), where=counts > 0)
    return THETAS, values
