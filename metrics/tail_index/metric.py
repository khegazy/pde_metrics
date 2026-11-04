"""Hill estimate of the tail index of one-cell increments: how slowly their largest values decay.

A single-field metric, the same shape as ``increment_flatness``: it characterises one field, so
the pipeline evaluates it on the reference and on every degraded variant, and the drift between
them is what is read. Where flatness summarises the whole increment distribution by its fourth
moment, this reads only its largest values. The Hill estimator (Hill 1975) is the mean log-ratio
of the k largest absolute increments to the (k+1)-th largest; for a sample whose tail decays as a
power law it estimates the extreme-value index, the reciprocal of the power. It reads the
increments every increment metric reads (``increment_samples``): on velocity the longitudinal
ones.

The registered number uses the k = ceil(sqrt(n)) largest of the n increments along each axis, one
of the two fixed rules Clauset, Shalizi and Newman (2009, Sect. 3.5) name for choosing k. The
field draws the estimate against its order two ways, both stored: against theta = log k / log n,
the alternative Hill plot (Resnick & Starica 1997; Drees, de Haan & Resnick 2000, Sect. 1), the
curve the number is read from; and against k, the classical Hill plot (Drees, de Haan & Resnick
2000, Sect. 1), the companion ``tail_index.by_order``.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np
from numpy.typing import NDArray

from fmeval.context import COMPANION_KEY, FieldContext
from metrics.increment_flatness.metric import increment_samples
from metrics.registry import companion, metric

#: The alternative Hill plot's coordinates, theta = j / 100 for j = 1, ..., 99, so
#: k = ceil(n ** theta) puts the order on a logarithmic scale across 0 < theta < 1, the range
#: of Drees, de Haan & Resnick (2000), Sect. 1. The spacing is this bundle's choice.
THETAS = np.arange(1, 100) / 100

#: The thetas the per-coordinate analysis reads, a tenth apart, each exactly as THETAS holds it.
ANALYSED_THETAS = tuple((np.arange(1, 10) / 10).tolist())

#: The registered number's exponent: k = ceil(n ** (1/2)), the largest sqrt(n) observations,
#: Clauset, Shalizi & Newman (2009), SIAM Rev. 51(4), Sect. 3.5.
REGISTERED_THETA = 0.5

#: The order the classical Hill plot is analysed at: the ten largest increments. It must lie on
#: that curve, k = 1 to n // 10, on every grid the harness runs, the contract tests' 16 x 8 among
#: them (n // 10 = 12); the choice is this bundle's.
ANALYSED_ORDER = 10


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
def tail_index(x: NDArray[np.floating], *, ctx: FieldContext) -> float:
    """Hill estimate of the extreme-value index of |one-cell increments| at k = ceil(sqrt(n)).

    The Hill estimator (Hill 1975, Ann. Stat. 3(5), 1163-1174), in the form of Drees, de Haan &
    Resnick (2000, Ann. Stat. 28(1), 254-274, Eq. (1.2)) and Boucheron and Thomas (2015,
    Electron. J. Stat. 9(2), 2751-2792, Sect. 1), evaluated at the largest ``ceil(sqrt(n))``
    order statistics, the fixed rule of Clauset, Shalizi and Newman (2009, SIAM Rev. 51(4),
    661-703, Sect. 3.5). It is the point ``theta = 1/2`` of :func:`tail_index_curve`, read from
    ``ctx.cache`` when the pipeline has computed the curve.

    Args:
        x: The field to characterise, shape ``(C, *spatial)`` on the analysis grid.
        ctx: The pipeline's context: its field name says which increments are read, and its
            cache holds this row's curve; without the curve it is computed here.

    Returns:
        The mean over (channel, axis) pairs of the Hill estimate; dimensionless and non-negative.
        NaN when no pair has a positive (k+1)-th largest absolute increment, as on a constant
        field.
    """
    thetas, values = (ctx.cache[COMPANION_KEY] if COMPANION_KEY in ctx.cache
                      else tail_index_curve(x, ctx=ctx))
    return float(np.asarray(values)[np.flatnonzero(np.asarray(thetas) == REGISTERED_THETA)[0]])


@companion(of="tail_index", kind="curve", coordinate=("theta", "log k / log n"),
           analysed=ANALYSED_THETAS, scales=("linear", "linear"))
def tail_index_curve(x: NDArray[np.floating], *, ctx: FieldContext) -> tuple[NDArray, NDArray]:
    """(theta, Hill estimate at k = ceil(n ** theta)): the alternative Hill plot.

    Drees, de Haan & Resnick (2000, Ann. Stat. 28(1), Sect. 1) plot the Hill estimate against
    theta = log k / log n, "a logarithmic scale for the k-axis", which gives the few largest
    order statistics more of the plot (after Resnick & Starica 1997, Adv. Appl. Probab. 29(1)).
    They write the set with the reciprocal estimate, an estimate of alpha, and draw the estimate
    of gamma = 1/alpha; this curve is gamma, the registered number's quantity. ``k`` is
    :func:`orders`; the estimator is :func:`hill_estimates`.

    Args:
        x: The field, shape ``(C, *spatial)`` on the analysis grid.
        ctx: The pipeline's context, whose field name says which increments are read.

    Returns:
        ``(THETAS, values)``; a value is NaN where no pair has a finite estimate.
    """
    return THETAS, hill_estimates(x, ctx.field, orders(int(np.prod(x.shape[1:]))))


@companion(of="tail_index", name="by_order", kind="curve", coordinate=("k", "order statistics"),
           analysed=(ANALYSED_ORDER,), scales=("linear", "linear"))
def tail_index_by_order(x: NDArray[np.floating], *,
                        ctx: FieldContext) -> tuple[NDArray, NDArray]:
    """(k, Hill estimate at k) for k = 1, ..., n // 10: the classical Hill plot.

    Drees, de Haan & Resnick (2000, Ann. Stat. 28(1), Sect. 1) call the plot of the Hill estimate
    against the number of order statistics k "what is usually done in practice", with k on a
    linear axis; Clauset, Shalizi & Newman (2009, SIAM Rev. 51(4), Sect. 3.5) name it the Hill
    plot. It is drawn here to k = n // 10, the larger of the two fixed rules of their Sect. 3.5;
    beyond it the estimate reads the bulk of the distribution. Same estimator as
    :func:`tail_index_curve` (:func:`hill_estimates`).

    Args:
        x: The field, shape ``(C, *spatial)`` on the analysis grid.
        ctx: The pipeline's context, whose field name says which increments are read.

    Returns:
        ``(k, values)`` for k = 1 to n // 10, the k-axis depending on the grid.
    """
    ks = np.arange(1, int(np.prod(x.shape[1:])) // 10 + 1)
    return ks, hill_estimates(x, ctx.field, ks)


def hill_estimates(x: NDArray[np.floating], field: str,
                   ks: NDArray[np.int64]) -> NDArray[np.floating]:
    """Hill estimate of |one-cell increments| at each order in ``ks``, averaged over pairs.

    For each (channel, axis) pair of :func:`~metrics.increment_flatness.metric.increment_samples`
    (on velocity the longitudinal increments) the absolute increments ``|delta|`` (``n`` of them,
    one per cell) are sorted into ``X_(1) >= X_(2) >= ... >= X_(n)``, and

        H(k) = (1/k) * sum_{i=1..k} ln(X_(i) / X_(k+1))

    Drees, de Haan & Resnick (2000, Ann. Stat. 28(1), Eq. (1.2)); Boucheron and Thomas (2015,
    Electron. J. Stat. 9(2), Sect. 1).

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
        field: Its canonical name, which says which increments are read.
        ks: The orders, each between 1 and ``n - 1``.

    Returns:
        One value per order; NaN where no pair has a finite estimate.

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
    estimates = []
    for delta in increment_samples(x, field):
        top = np.sort(np.abs(delta), axis=None)[::-1][: ks.max() + 1]
        with np.errstate(divide="ignore", invalid="ignore"):
            logs = np.log(top)
            # Drees et al. (2000), Eq. (1.2): mean of ln X_(i), i <= k, minus ln X_(k+1).
            hill = np.cumsum(logs)[ks - 1] / ks - logs[ks]
        estimates.append(np.where(top[ks] > 0, hill, np.nan))
    # Mean over the pairs with an estimate (this bundle's choice; the reason is in the
    # docstring); NaN at an order where no pair has one.
    estimates = np.array(estimates)
    defined = np.isfinite(estimates)
    counts = defined.sum(axis=0)
    sums = np.where(defined, estimates, 0.0).sum(axis=0)
    return np.divide(sums, counts, out=np.full(len(ks), np.nan), where=counts > 0)


def orders(n: int, thetas: NDArray[np.floating] = THETAS) -> NDArray[np.int64]:
    """The order k = ceil(n ** theta) at each of ``thetas``, exactly, capped at ``n - 1``.

    Each theta is read as the decimal it prints as, p / q, and ``ceil(n ** theta)`` is the least
    integer k with ``k ** q >= n ** p``, found in Python integers. A floating-point power can land
    just above an exact root (``1024 ** 0.4`` evaluates to 16.000000000000004), and its ceiling is
    then one too large. The cap leaves an ``X_(k+1)`` to divide by. theta = 1/2 is the
    largest-sqrt(n) rule of Clauset, Shalizi & Newman (2009), SIAM Rev. 51(4), 661-703,
    Sect. 3.5; the cap and the theta grid are this bundle's choice.

    Args:
        n: The number of increments per (channel, axis) pair, at least 2.
        thetas: Exponents between 0 and 1.

    Returns:
        One order per theta, as integers.
    """
    ks = []
    for theta in np.asarray(thetas, dtype=float).tolist():
        exact = Fraction(str(theta))
        p, q = exact.numerator, exact.denominator
        k = int(np.ceil(n ** theta))   # within one of the exact value; corrected below
        while k > 1 and (k - 1) ** q >= n ** p:
            k -= 1
        while k ** q < n ** p:
            k += 1
        ks.append(min(k, n - 1))
    return np.array(ks, dtype=np.int64)
