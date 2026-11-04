"""Frequency bias of extreme one-cell increments: how often a prediction exceeds the reference's.

A pairwise metric on the same one-cell increments as ``increment_flatness`` and ``tail_index``
(``increment_samples``: on velocity the longitudinal ones). The event is "an absolute increment
at least as large as the k-th largest of the reference's", a threshold set by the reference's own
extremes, so the reference has exactly k events per channel and axis (more only on ties). The
number is the frequency bias of that event, the candidate's count over the reference's: the
forecast-verification score of the same name (JWGFVR, Sect. "Frequency bias"), whose perfect
value is 1, with a threshold taken from the reference's own percentile as the percentile-based
climate-extremes indices take theirs from a base period (ETCCDI, index TX90p).

Below 1 the prediction has fewer extreme increments than the reference, as an over-smoothed
surrogate does; above 1 it has more, as a noisy one does. The order k is ``tail_index``'s,
k = ceil(n ** theta); the curve over theta is the companion and the number registered for the
panel is its point theta = 1/2, a convention (``issues/118``). The same ratio against the
reference's percentile, the threshold as the climate-extremes indices state it, is the companion
``tail_exceedance.percentile``.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import COMPANION_KEY, FieldContext
from metrics.increment_flatness.metric import increment_samples
from metrics.registry import companion, metric
from metrics.tail_index.metric import ANALYSED_THETAS, REGISTERED_THETA, orders

#: ``ctx.cache`` key of the reference's thresholds, one per (pair, order), and its event counts;
#: one entry per curve, the curve's name appended.
REFERENCE_EVENTS = "tail_exceedance/reference_events"

#: The percentile curve's thresholds in hundredths of a percent: 90, 91, ..., 99, then 99.1, ...,
#: 99.9, then 99.91, ..., 99.99, so the reference's exceedance fraction takes one to nine (and
#: ten) times each of 1%, 0.1% and 0.01%. 90, 95 and 99 are the percentiles of the ETCCDI indices
#: (TX90p and its kin, items 10-13; R95pTOT and R99pTOT, items 25-26); the grid between is this
#: bundle's choice.
PERCENTILE_HUNDREDTHS = np.concatenate([np.arange(9000, 10000, 100), np.arange(9910, 10000, 10),
                                        np.arange(9991, 10000)])
PERCENTILES = PERCENTILE_HUNDREDTHS / 100


@metric(
    name="tail_exceedance",
    arity="pairwise",
    fields=("*",),
    differentiable=False,     # a count of cells above a threshold: piecewise constant in the
                              # candidate, so its gradient is zero almost everywhere
    cost="cheap",
    higher_is_better=False,   # required with a target: the analysis orders by distance from 1
    symmetric=False,          # the threshold is the reference's
    units="dimensionless",
    target=1.0,               # JWGFVR, "Frequency bias": perfect score 1
    # A fixed threshold's exceedance count can rise under blur before it falls: one tall jump
    # spread over several cells puts each of them above a low threshold. A 16-cell spike of
    # height 8 on noise of rms 0.01 (seed 0) scores 1, 1, 2, 3, 3.5, 0 at sigma = 0, 0.5, 1, 2,
    # 4, 8 (test_metric.py pins the sequence).
    monotone_under_smoothing=False,
    requires_periodic=True,   # increment_flatness's wrap-around increments
)
def tail_exceedance(reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
                    ctx: FieldContext) -> float:
    """Frequency bias of |one-cell increment| >= the reference's k-th largest, k = ceil(sqrt(n)).

    The frequency bias, forecast events over observed events (JWGFVR, "Forecast verification:
    methods, issues and FAQ", Sect. "Frequency bias (bias score)",
    https://jwgfvr.github.io/forecastverification), with the reference in the place of the
    observation. The registered point theta = 1/2 of :func:`tail_exceedance_curve` is the order of
    ``tail_index``, the largest sqrt(n), which Clauset, Shalizi & Newman (2009, SIAM Rev. 51(4),
    661-703, Sect. 3.5) mention as an alternative way of choosing a tail sample, common in the
    finance literature, not as their recommended method; that this point stands for the curve is
    a convention (``issues/118``).

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ctx: The pipeline's context. Its field name says which increments are read; its cache
            holds this row's curve and the reference's thresholds for the frame, and without the
            curve both are computed here.

    Returns:
        The frequency bias at theta = 1/2: 1 when the candidate has as many extreme increments
        as the reference, 0 when it has none, unbounded above. NaN when the reference is
        constant, so that no threshold is positive.
    """
    thetas, values = (ctx.cache[COMPANION_KEY] if COMPANION_KEY in ctx.cache
                      else tail_exceedance_curve(reference, candidate, ctx=ctx))
    # theta = 1/2, k = ceil(sqrt(n)): the largest-sqrt(n) rule Clauset, Shalizi & Newman (2009),
    # SIAM Rev. 51(4), Sect. 3.5, mention; registering this point is a convention, issues/118.
    return float(np.asarray(values)[np.flatnonzero(np.asarray(thetas) == REGISTERED_THETA)[0]])


@companion(of="tail_exceedance", kind="curve", coordinate=("theta", "log k / log n"),
           scales=("linear", "symlog"))
def tail_exceedance_curve(reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
                          ctx: FieldContext) -> tuple[NDArray, NDArray]:
    """(theta, frequency bias at the reference's k-th largest |increment|, k = ceil(n ** theta)).

    At the nine thetas a tenth apart that ``tail_index``'s curve is analysed at, with ``k`` from
    its :func:`~metrics.tail_index.metric.orders`; :func:`frequency_bias` computes the ratio.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ctx: The pipeline's context; see :func:`frequency_bias`.

    Returns:
        ``(thetas, values)``; a value is NaN where no pair has a positive threshold.
    """
    n = int(np.prod(reference.shape[1:]))
    return np.array(ANALYSED_THETAS), frequency_bias(
        reference, candidate, orders(n, ANALYSED_THETAS), ctx=ctx, curve="theta")


@companion(of="tail_exceedance", name="percentile", kind="curve",
           coordinate=("threshold", "reference percentile"), analysed=(90.0, 95.0, 99.0),
           scales=("linear", "symlog"))
def tail_exceedance_percentile(reference: NDArray[np.floating], candidate: NDArray[np.floating],
                               *, ctx: FieldContext) -> tuple[NDArray, NDArray]:
    """(p, frequency bias at the reference's p-th percentile of |increment|), p from 90 to 99.99.

    The threshold stated as the percentile of the reference sample it is, as the ETCCDI indices
    state theirs ("TX > 90th percentile" of a base period, items 10-13 of the list of the 27 core
    indices), and the score drawn against its threshold, as forecast verification draws one
    (WWRP/WGNE 2004, "Recommendations for the verification and intercomparison of QPFs from
    operational NWP models", Sect. 5(c)). The p-th percentile is the reference's k-th largest
    with k = ceil(n (100 - p) / 100), exactly in integers, so the reference has (100 - p)% of its
    increments at or above it; the event and the ratio are :func:`frequency_bias`'s. The grid is
    :data:`PERCENTILES`.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ctx: The pipeline's context; see :func:`frequency_bias`.

    Returns:
        ``(PERCENTILES, values)``; a value is NaN where no pair has a positive threshold.
    """
    n = int(np.prod(reference.shape[1:]))
    ks = -(-n * (10000 - PERCENTILE_HUNDREDTHS) // 10000)
    return PERCENTILES, frequency_bias(reference, candidate, ks, ctx=ctx, curve="percentile")


def frequency_bias(reference: NDArray[np.floating], candidate: NDArray[np.floating],
                   ks: NDArray[np.int64], *, ctx: FieldContext, curve: str) -> NDArray:
    """Frequency bias of ``|delta| >= X_(k)`` of the reference, at each order in ``ks``.

    For each (channel, axis) pair of :func:`~metrics.increment_flatness.metric.increment_samples`
    (on velocity the longitudinal increments), the reference's absolute one-cell increments
    ``|delta|`` (``n`` of them) are sorted into ``X_(1) >= ... >= X_(n)`` and the threshold at
    each order is ``a = X_(k)``. The event is ``|delta| >= a``: an exceedance of a percentile of
    the reference, as the ETCCDI indices count exceedances of a base period's percentile (TX90p,
    item 13 of https://etccdi.pacificclimate.org/list_27_indices.shtml, which uses a strict ``>``;
    the non-strict inequality here is this bundle's choice, below).
    The frequency bias (JWGFVR, Sect. "Frequency bias (bias score)") pools the counts over pairs:

        B = sum_pairs #{|delta_cand| >= a} / sum_pairs #{|delta_ref| >= a}

    which, with no ties at ``a``, is the mean over pairs of each pair's ratio, since every pair's
    reference count is then ``k``. A pair whose ``a`` is zero, an axis along which the reference
    is constant, has no event and is left out, as ``tail_index`` leaves it out (``issues/103``).
    ``X_(k)`` with ``>=`` rather than ``X_(k+1)`` with ``>`` is this bundle's choice: for a
    reference of n independent values and a candidate drawn independently from the same
    distribution, the expected bias is then n / (n + 1), where the other gives
    n (k + 1) / ((n + 1) k), about 1.25 at the theta curve's first point on 256 x 256 (the
    derivation is the card's, this bundle's own; Zhang et al. 2005, J. Climate 18(11),
    1641-1651, abstract, describe how a percentile threshold's exceedance rate differs inside and
    outside the sample it was estimated from, which they correct with a bootstrap).

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ks: The orders, each between 1 and ``n``.
        ctx: The pipeline's context; its field name says which increments are read, and its
            cache keeps the reference's thresholds and counts for the frame, so they are
            computed once across the ladder. It must belong to this reference.
        curve: The curve's name, which keeps each curve's thresholds apart in the cache.

    Returns:
        One value per order; NaN where no pair has a positive threshold.

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
    key = f"{REFERENCE_EVENTS}/{curve}"
    if key not in ctx.cache:
        # X_(k), the k-th largest |increment| of each pair at each order: a threshold set by a
        # percentile of the reference sample, as the ETCCDI percentile indices set theirs from a
        # base period (TX90p, list of the 27 core indices, item 13). The k-th rather than the
        # (k+1)-th is this bundle's choice (docstring).
        thresholds = np.array([np.sort(size)[::-1][ks - 1]
                               for size in _sizes(reference, ctx.field)])
        ctx.cache[key] = (thresholds, _exceedances(reference, ctx.field, thresholds))
    thresholds, reference_counts = ctx.cache[key]
    candidate_counts = _exceedances(candidate, ctx.field, thresholds)
    # JWGFVR, "Frequency bias (bias score)": forecast events over observed events, the counts
    # summed over the pairs with a positive threshold before the ratio.
    positive = thresholds > 0
    hits = np.where(positive, candidate_counts, 0).sum(axis=0)
    events = np.where(positive, reference_counts, 0).sum(axis=0)
    return np.divide(hits, events, out=np.full(len(ks), np.nan), where=events > 0)


def _sizes(x: NDArray[np.floating], field: str) -> list[NDArray[np.floating]]:
    """The absolute one-cell increments of each pair :func:`increment_samples` reads, flattened,
    in its order, the order of the thresholds."""
    return [np.abs(delta).ravel() for delta in increment_samples(x, field)]


def _exceedances(x: NDArray[np.floating], field: str,
                 thresholds: NDArray[np.floating]) -> NDArray[np.int64]:
    """``#{|delta| >= a}`` for each pair of ``x`` (rows) and each of its thresholds (columns): the
    event count of the frequency bias (JWGFVR, "Frequency bias (bias score)"), the event being an
    exceedance of a reference percentile, as the ETCCDI indices (TX90p) count exceedances of a
    base-period percentile (they with a strict inequality)."""
    # The non-strict inequality is this bundle's choice; with X_(k) it gives an independent
    # candidate an expected bias of n / (n + 1) (card, Equation (5)).
    return np.array([np.count_nonzero(size[:, None] >= row[None, :], axis=0)
                     for size, row in zip(_sizes(x, field), thresholds, strict=True)])
