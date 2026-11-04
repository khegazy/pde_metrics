"""Rank histogram reliability index: the shape of the ensemble's mistakes.

Where the spread-to-skill ratio asks whether the ensemble is the right *size*, this asks
whether it is the right *shape*. Sort the members at a cell and ask where the truth falls
among them. If the ensemble is an honest sample of the forecast distribution, the truth is
just one more draw and equally likely to land in any of the N+1 gaps, so the histogram of
those positions over many cells is flat. The characteristic failures each bend it a
different way, and the shape names the fault: a U means the members huddle too closely and
the truth keeps falling outside them; a dome means they are spread too widely; a slope to
one side means bias.

That diagnosis is the reason this metric is worth having beside the others. An ensemble
can be rescaled about its own mean without moving that mean at all, leaving every
mean-based score exactly where it was while the forecast's honesty changes completely --
a test in this bundle pins that contrast against ``ensemble_mean_rmse``.

The reported number is the **reliability index**, the total absolute deviation of the
histogram from flat (Delle Monache et al. 2006). It is bounded, dimensionless, zero when
calibrated, and does not grow with the number of cells. The chi-square statistic, the other
summary the field reports, is the sibling bundle ``rank_histogram_chi2``, which imports the
histogram from here. Neither computes a p-value: the cells of one frame are spatially
correlated, and a test that assumes independent draws would be far too confident.

The histogram itself, the object the field draws (Hamill 2001, Fig. 1), is this metric's
curve companion: the relative frequency of each rank, stored on every row.
"""

from __future__ import annotations

import numpy as np

from fmeval.context import COMPANION_KEY, FieldContext

from .._ensemble import as_ensemble
from ..registry import companion, metric


def reliability_index(counts: np.ndarray) -> float:
    """Total absolute deviation of a rank histogram from uniform.

    .. math::

        \\Delta = \\sum_{k=1}^{N+1} \\Bigl| f_k - \\frac{1}{N+1} \\Bigr|,

    with :math:`f_k` the fraction of draws in bin :math:`k` (Delle Monache et al. 2006,
    J. Geophys. Res. 111, D24307, Eq. 1 of the preprint read, which multiplies by 100 to
    give a percentage). Zero for a flat histogram, and at most :math:`2N/(N+1)` when every
    draw lands in one bin.

    Args:
        counts: Draws per bin, or their fractions, length ``N + 1``.

    Returns:
        The index, dimensionless.
    """
    counts = np.asarray(counts, dtype=np.float64)
    total = counts.sum()
    if total <= 0:
        return 0.0
    n_bins = counts.size
    return float(np.abs(counts / total - 1.0 / n_bins).sum())


@metric(
    name="rank_histogram",
    arity="ensemble",
    fields=("*",),
    differentiable=False,     # ranks are integer-valued; no useful gradient
    cost="cheap",
    higher_is_better=False,
    symmetric=False,
    units="dimensionless",
    reduction="mean",
    measures="calibration",
)
def rank_histogram(reference: np.ndarray, members: np.ndarray, *,
                   ctx: FieldContext | None = None) -> float:
    """Reliability index of the reference's rank histogram within the ensemble.

    The histogram is :func:`rank_histogram_curve`, read from the pipeline's cache when it has
    computed it for this row and computed here otherwise; :func:`reliability_index` compares it
    with the uniform one.

    Args:
        reference: Reference realization, shape ``(C, *spatial)``.
        members: Ensemble members, shape ``(N, C, *spatial)``. At least two.
        ctx: Optional field context: its cache may hold this row's histogram, and its ``rng``
            breaks ties.

    Returns:
        The reliability index. Zero for a flat histogram, at most ``2N/(N+1)``.

    Raises:
        ValueError: If ``members`` lacks a leading member axis or has fewer than two
            members, which would leave only two bins and no shape to speak of.
    """
    cache = ctx.cache if ctx is not None else {}
    _, frequencies = (cache[COMPANION_KEY] if COMPANION_KEY in cache
                      else rank_histogram_curve(reference, members, ctx=ctx))
    return reliability_index(frequencies)


# A histogram over the fixed ranks 0 .. N, drawn as bars as its field draws it.
@companion(of="rank_histogram", kind="curve", coordinate=("rank", "members below"),
           style="bars")
def rank_histogram_curve(reference: np.ndarray, members: np.ndarray, *,
                         ctx: FieldContext | None = None) -> tuple[np.ndarray, np.ndarray]:
    """The rank histogram: the fraction of draws at each rank ``0 .. N``.

    At every cell and channel the rank is the number of members below the reference, an
    integer in ``0 .. N``; the histogram pools every channel and cell of the frame. The values
    are relative frequencies, as Hamill (2001, Mon. Wea. Rev. 129:550, Fig. 1) draws them, so a
    flat histogram sits at ``1/(N+1)`` whatever the grid.

    **Ties are broken at random**, which matters more than it looks. Where several members
    equal the reference exactly -- a collapsed ensemble, or a field quantised coarsely enough
    for exact repeats -- always counting "members strictly below" would put every tied draw in
    the lowest bin and manufacture a spike that reads as bias where there is none. Hamill
    (2001, Sect. 2) notes that ties need a special rule; the one here draws the rank uniformly
    from the ranks the tie spans, which keeps an exchangeable but discrete forecast flat,
    because the reference is then equally likely to sit anywhere in the tied run. The draw
    uses the context's seeded generator, so a run is reproducible; without a context the
    midpoint of the tied range is used instead, which is deterministic and adequate for a
    direct call.

    Args:
        reference: Reference realization, shape ``(C, *spatial)``.
        members: Ensemble members, shape ``(N, C, *spatial)``. At least two.
        ctx: Optional field context; only its ``rng`` is used, for tie-breaking.

    Returns:
        ``(ranks, frequencies)``: the ranks ``0 .. N`` and the fraction of draws at each,
        summing to one.

    Raises:
        ValueError: If ``members`` lacks a leading member axis or has fewer than two members.
    """
    reference, members = as_ensemble(
        reference, members, min_members=2, what="rank_histogram"
    )
    n_members = members.shape[0]

    below = (members < reference[None]).sum(axis=0)
    tied = (members == reference[None]).sum(axis=0)

    if tied.any():
        if ctx is not None and getattr(ctx, "rng", None) is not None:
            # Uniform over the ranks the tie spans: below .. below + tied.
            offset = ctx.rng.integers(0, tied + 1)
        else:
            offset = tied // 2
        ranks = below + offset
    else:
        ranks = below

    counts = np.bincount(ranks.ravel(), minlength=n_members + 1)
    return np.arange(n_members + 1), counts / counts.sum()
