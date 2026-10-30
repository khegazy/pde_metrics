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

#: The curve's coordinates in tenths: theta = j / 10 for j = 1, ..., 9, so k = ceil(n ** theta)
#: puts the order on a logarithmic scale. The coordinate and its spacing are this bundle's choice;
#: theta = 1/2 is the registered number's k.
THETA_TENTHS = np.arange(1, 10)
THETAS = THETA_TENTHS / 10

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
    2751-2792, Sect. 1; Hill 1975, Ann. Stat. 3(5), 1163-1174). ``k`` is :func:`orders`.

    A pair whose ``X_(k+1)`` is exactly zero has no finite estimate at that ``k`` and is left out
    of the mean over pairs, as ``increment_flatness`` leaves out an axis with no increments. The
    rule is discontinuous: an axis along which the field is constant up to round-off is not left
    out, and its estimate, which is scale-free, counts as much as any other (``issues/103``).

    The mean over pairs, rather than one estimate from every pair's increments pooled, gives each
    channel and axis an equal say. Pooled, the k largest values come from whichever pair has the
    largest increments: on kinet velocity at frames 2000 and 8000 a single pair supplies all of
    them. Averaging over pairs whose estimates differ (0.018 to 0.121 across the four velocity
    pairs at frame 2000) is itself a mixture, which the card states.

    Args:
        x: The field, shape ``(C, *spatial)`` on the analysis grid.

    Returns:
        ``(THETAS, values)``; a value is NaN where no pair has a finite estimate.

    Raises:
        ValueError: If the field has fewer than two cells, so no k can be formed, or holds a
            non-finite value, which would otherwise silently remove its pair from the mean.
    """
    n = int(np.prod(x.shape[1:]))
    if n < 2:
        raise ValueError(f"the Hill estimator needs at least two cells; the spatial shape is "
                         f"{tuple(x.shape[1:])}")
    if not np.isfinite(x).all():
        bad = int(np.size(x) - np.isfinite(x).sum())
        raise ValueError(f"tail_index needs a finite field; {bad} of {np.size(x)} values are "
                         f"NaN or infinite")
    ks = orders(n)
    estimates = []
    for channel in x:
        for axis in range(-(x.ndim - 1), 0):
            top = np.sort(np.abs(increments(channel, axis)), axis=None)[::-1][: ks.max() + 1]
            with np.errstate(divide="ignore", invalid="ignore"):
                logs = np.log(top)
                # Boucheron & Thomas (2015), Sect. 1: mean of ln X_(i), i <= k, minus ln X_(k+1).
                hill = np.cumsum(logs)[ks - 1] / ks - logs[ks]
            estimates.append(np.where(top[ks] > 0, hill, np.nan))
    # Mean over the pairs with an estimate (this bundle's choice; the reason is in the
    # docstring); NaN at a theta where no pair has one.
    estimates = np.array(estimates)
    defined = np.isfinite(estimates)
    counts = defined.sum(axis=0)
    sums = np.where(defined, estimates, 0.0).sum(axis=0)
    values = np.divide(sums, counts, out=np.full(len(THETAS), np.nan), where=counts > 0)
    return THETAS, values


def orders(n: int) -> NDArray[np.int64]:
    """The order k = ceil(n ** theta) at each theta of ``THETAS``, exactly, capped at ``n - 1``.

    For theta = j/10, ``ceil(n ** theta)`` is the least integer k with ``k ** 10 >= n ** j``,
    found here in Python integers. A floating-point power can land just above an exact root
    (``1024 ** 0.4`` evaluates to 16.000000000000004), and its ceiling is then one too large. The
    cap leaves an ``X_(k+1)`` to divide by. theta = 1/2 is the largest-sqrt(n) rule of Clauset,
    Shalizi & Newman (2009), SIAM Rev. 51(4), 661-703, Sect. 3.5; the cap and the theta grid are
    this bundle's choice.

    Args:
        n: The number of increments per (channel, axis) pair, at least 2.

    Returns:
        One order per theta, as integers.
    """
    ks = []
    for j in THETA_TENTHS.tolist():
        k = int(np.ceil(n ** (j / 10)))   # within one of the exact value; corrected below
        while k > 1 and (k - 1) ** 10 >= n ** j:
            k -= 1
        while k ** 10 < n ** j:
            k += 1
        ks.append(min(k, n - 1))
    return np.array(ks, dtype=np.int64)
