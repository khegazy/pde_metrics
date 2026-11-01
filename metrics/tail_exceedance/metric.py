"""Frequency bias of extreme one-cell increments: how often a prediction exceeds the reference's.

A pairwise metric on the same one-cell increments as ``increment_flatness`` and ``tail_index``.
The event is "an absolute increment at least as large as the k-th largest of the reference's",
a threshold set by the reference's own extremes, so the reference has exactly k events per channel
and axis (more only on ties). The number is the frequency bias of that event, the candidate's count
over the reference's: the forecast-verification score of the same name (JWGFVR, Sect. "Frequency
bias"), whose perfect value is 1, with a threshold taken from the reference's own percentile as the
percentile-based climate-extremes indices take theirs from a base period (ETCCDI, index TX90p).

Below 1 the prediction has fewer extreme increments than the reference, as an over-smoothed
surrogate does; above 1 it has more, as a noisy one does. The order k is ``tail_index``'s,
k = ceil(n ** theta); the curve over theta is the companion and the number registered for the
panel is its point theta = 1/2, a convention (``issues/118``).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import COMPANION_KEY, FieldContext
from metrics.increment_flatness.metric import increments
from metrics.registry import companion, metric
from metrics.tail_index.metric import REGISTERED_THETA, THETAS, orders

#: ``ctx.cache`` key of the reference's thresholds, one per (pair, theta), and its event counts.
REFERENCE_EVENTS = "tail_exceedance/reference_events"


@metric(
    name="tail_exceedance",
    arity="pairwise",
    fields=("*",),
    differentiable=False,     # a count of cells above a threshold: piecewise constant in the
                              # candidate, so its gradient is zero almost everywhere
    cost="cheap",
    higher_is_better=False,   # required with a target: the analysis orders by |log(value / 1)|
    symmetric=False,          # the threshold is the reference's
    units="dimensionless",
    target=1.0,               # JWGFVR, "Frequency bias": perfect score 1
    # A fixed threshold's exceedance count can rise under blur before it falls: one tall jump
    # spread over several cells puts each of them above a low threshold. A 16-cell spike of
    # height 8 on noise of rms 0.01 scores 1, 1.25, 2, 3, 3.5, 0 at sigma = 0, 0.5, 1, 2, 4, 8
    # (test_metric.py pins the rise and the fall).
    monotone_under_smoothing=False,
    requires_periodic=True,   # increment_flatness's wrap-around increments
)
def tail_exceedance(reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
                    ctx: FieldContext | None = None) -> float:
    """Frequency bias of |one-cell increment| >= the reference's k-th largest, k = ceil(sqrt(n)).

    The frequency bias, forecast events over observed events (JWGFVR, "Forecast verification:
    methods, issues and FAQ", Sect. "Frequency bias (bias score)",
    https://jwgfvr.github.io/forecastverification), with the reference in the place of the
    observation. The registered point theta = 1/2 of :func:`tail_exceedance_curve` is the order of
    ``tail_index``, the largest sqrt(n) of Clauset, Shalizi & Newman (2009, SIAM Rev. 51(4),
    661-703, Sect. 3.5); that this point stands for the curve is a convention (``issues/118``).

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ctx: The pipeline's context. Its cache holds this row's curve and the reference's
            thresholds for the frame; without it both are computed here.

    Returns:
        The frequency bias at theta = 1/2: 1 when the candidate has as many extreme increments
        as the reference, 0 when it has none, unbounded above. NaN when the reference is
        constant, so that no threshold is positive.
    """
    thetas, values = (ctx.cache[COMPANION_KEY] if ctx is not None and COMPANION_KEY in ctx.cache
                      else tail_exceedance_curve(reference, candidate, ctx=ctx))
    # theta = 1/2, k = ceil(sqrt(n)): the largest-sqrt(n) rule of Clauset, Shalizi & Newman
    # (2009), SIAM Rev. 51(4), Sect. 3.5; registering this point is a convention, issues/118.
    return float(np.asarray(values)[np.flatnonzero(np.asarray(thetas) == REGISTERED_THETA)[0]])


@companion(of="tail_exceedance", kind="curve", coordinate=("theta", "log k / log n"))
def tail_exceedance_curve(reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
                          ctx: FieldContext | None = None) -> tuple[NDArray, NDArray]:
    """(theta, frequency bias at the reference's k-th largest |increment|, k = ceil(n ** theta)).

    For each channel and spatial axis, the reference's absolute one-cell increments ``|delta|``
    (``n`` of them) are sorted into ``X_(1) >= ... >= X_(n)`` and the threshold at each theta is
    ``a = X_(k)``, ``k`` from ``tail_index``'s :func:`~metrics.tail_index.metric.orders`. The
    event is ``|delta| >= a`` (the percentile-threshold event of the ETCCDI indices, e.g. TX90p,
    https://etccdi.pacificclimate.org/list_27_indices.shtml, with the reference as base period).
    The frequency bias (JWGFVR, Sect. "Frequency bias (bias score)") pools the counts over pairs:

        B(theta) = sum_pairs #{|delta_cand| >= a} / sum_pairs #{|delta_ref| >= a}

    which, with no ties at ``a``, is the mean over pairs of each pair's ratio, since every pair's
    reference count is then ``k``. A pair whose ``a`` is zero, an axis along which the reference
    is constant, has no event and is left out, as ``tail_index`` leaves it out (``issues/103``).
    ``X_(k)`` with ``>=`` rather than ``X_(k+1)`` with ``>`` is this bundle's choice: for a
    candidate drawn independently from the reference's distribution the expected bias is then
    n / (n + 1), where the other gives (k + 1) / k, 1.25 at the curve's first point on 256 x 256
    (the derivation is on the card; Zhang et al. 2005, J. Climate 18(11), 1641-1651, abstract,
    describe the same in-sample/out-of-sample effect of a percentile threshold).

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ctx: The pipeline's context; its cache keeps the reference's thresholds and counts for
            the frame, so they are computed once across the ladder. It must belong to this
            reference.

    Returns:
        ``(THETAS, values)``; a value is NaN where no pair has a positive threshold.

    Raises:
        ValueError: If the shapes differ, the field has fewer than two cells, or either field
            holds a non-finite value, which would otherwise silently change a count.
    """
    if reference.shape != candidate.shape:
        raise ValueError(f"tail_exceedance needs matching shapes, got {reference.shape} and "
                         f"{candidate.shape}")
    n = int(np.prod(reference.shape[1:]))
    if n < 2:
        raise ValueError(f"tail_exceedance needs at least two cells; the spatial shape is "
                         f"{tuple(reference.shape[1:])}")
    for name, x in (("reference", reference), ("candidate", candidate)):
        if not np.isfinite(x).all():
            bad = int(np.size(x) - np.isfinite(x).sum())
            raise ValueError(f"tail_exceedance needs a finite {name}; {bad} of {np.size(x)} "
                             f"values are NaN or infinite")
    cache = ctx.cache if ctx is not None else {}
    if REFERENCE_EVENTS not in cache:
        ks = orders(n)
        # X_(k), the k-th largest |increment| of each (channel, axis) pair at each theta: a
        # threshold set by a percentile of the reference sample, as the ETCCDI percentile indices
        # set theirs from a base period (TX90p, list of the 27 core indices, item 13). The k-th
        # rather than the (k+1)-th is this bundle's choice (docstring; Zhang et al. 2005).
        thresholds = np.array([np.sort(size)[::-1][ks - 1] for size in _sizes(reference)])
        cache[REFERENCE_EVENTS] = (thresholds, _exceedances(reference, thresholds))
    thresholds, reference_counts = cache[REFERENCE_EVENTS]
    candidate_counts = _exceedances(candidate, thresholds)
    # JWGFVR, "Frequency bias (bias score)": forecast events over observed events, the counts
    # summed over the pairs with a positive threshold before the ratio.
    positive = thresholds > 0
    hits = np.where(positive, candidate_counts, 0).sum(axis=0)
    events = np.where(positive, reference_counts, 0).sum(axis=0)
    values = np.divide(hits, events, out=np.full(len(THETAS), np.nan), where=events > 0)
    return THETAS, values


def _sizes(x: NDArray[np.floating]) -> list[NDArray[np.floating]]:
    """The absolute one-cell increments of each (channel, spatial axis) pair, flattened, in the
    order channel-major then axis, the order of the thresholds."""
    return [np.abs(increments(channel, axis)).ravel()
            for channel in x for axis in range(-(x.ndim - 1), 0)]


def _exceedances(x: NDArray[np.floating], thresholds: NDArray[np.floating]) -> NDArray[np.int64]:
    """``#{|delta| >= a}`` for each pair of ``x`` (rows) and each of its thresholds (columns): the
    event count of the frequency bias (JWGFVR, "Frequency bias (bias score)"), the event being an
    exceedance of a reference percentile as in the ETCCDI indices (TX90p)."""
    # The non-strict inequality is this bundle's choice; with X_(k) it gives an independent
    # candidate an expected bias of n / (n + 1) (card, Equation (5)).
    return np.array([np.count_nonzero(size[:, None] >= row[None, :], axis=0)
                     for size, row in zip(_sizes(x), thresholds, strict=True)])
