"""Chi-square statistic of the rank histogram: its distance from flat, scaled by the sample.

The rank histogram (``rank_histogram``) counts where the truth falls among the sorted members
at every cell; an ensemble that is an honest sample of the truth's distribution gives a flat
histogram. Anderson (1996) and Hamill (2001) test that flatness with Pearson's chi-square
statistic, and Jolliffe & Primo (2008) build their decompositions on it. This bundle reports
the statistic itself, beside the reliability index that ``rank_histogram`` reports.

Unlike the reliability index, the statistic grows with the number of draws: at a fixed
histogram shape it is proportional to the number of cells. That is what makes it a test
statistic, and also why the number is comparable only between runs on the same grid and
fields. It is reported raw, without a p-value: the chi-square distribution it would be read
against assumes independent draws, and neighbouring cells of a field are not independent.
"""

from __future__ import annotations

import numpy as np

from fmeval.context import FieldContext

from ..rank_histogram.metric import rank_histogram_curve
from ..registry import metric


@metric(
    name="rank_histogram_chi2",
    arity="ensemble",
    fields=("*",),
    differentiable=False,     # built from integer ranks; no useful gradient
    cost="cheap",
    higher_is_better=False,
    symmetric=False,
    units="dimensionless",
    reduction="mean",
    measures="calibration",
)
def rank_histogram_chi2(reference: np.ndarray, members: np.ndarray, *,
                        ctx: FieldContext | None = None) -> float:
    """Pearson's chi-square statistic of the reference's rank histogram against uniform.

    .. math::

        T = \\sum_{k=1}^{K} \\frac{(n_k - e)^2}{e}, \\qquad e = \\frac{n}{K},

    with :math:`n_k` the draws at rank :math:`k`, :math:`K = N + 1` bins for :math:`N`
    members and :math:`n` draws in all (Jolliffe & Primo 2008, Mon. Wea. Rev. 136:2133,
    Sect. 2, Eq. 1, there with :math:`e_i = n p_0`). From the fractions
    :math:`f_k = n_k / n` that ``rank_histogram_curve`` returns it is
    :math:`T = n K \\sum_k (f_k - 1/K)^2`. The draws are every channel and cell of the frame,
    so :math:`n` is ``reference.size``; ties are broken as ``rank_histogram_curve`` breaks
    them.

    Args:
        reference: Reference realization, shape ``(C, *spatial)``.
        members: Ensemble members, shape ``(N, C, *spatial)``. At least two.
        ctx: Optional field context; only its ``rng`` is used, for tie-breaking.

    Returns:
        The statistic, dimensionless and non-negative. Zero for a flat histogram; with
        independent draws from a calibrated ensemble its expectation is ``N``, the degrees of
        freedom; at most ``n N``, when every draw lands in one bin.

    Raises:
        ValueError: If ``members`` lacks a leading member axis or has fewer than two members.
    """
    _, frequencies = rank_histogram_curve(reference, members, ctx=ctx)
    n_bins = frequencies.size
    # Jolliffe & Primo (2008), Eq. 1, written in the fractions: n_k = n f_k and e = n / K.
    return float(reference.size * n_bins * np.sum((frequencies - 1.0 / n_bins) ** 2))
