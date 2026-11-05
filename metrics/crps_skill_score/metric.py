"""CRPS skill score: the ensemble's CRPS as a fraction of what climatology would score.

The continuous ranked probability score (``crps``) is in the field's units, so its size says
nothing until it is compared with something. The forecast-verification field compares it
with a reference forecast, typically climatology, the unconditional distribution of the
observations, and reports the skill score: one minus the ratio of the two mean scores
(Gneiting & Raftery 2007, Sect. 2.3, Eq. 8). One is a perfect forecast, zero is no better
than climatology, and a negative value is worse.

**What climatology is here.** The climatological forecast at every cell is the empirical
distribution of the reference's own values over the whole domain of the same frame and
channel (``judgements/011``). Its mean CRPS over those values is the uncertainty term
``UNC_0`` of the CRPS decompositions (Arnold, Walz, Ziegel & Gneiting 2024, Electron. J.
Stat. 18(2):4992, Eq. 10 of the published version, Eq. 11 of arXiv:2311.14122v1): the mean
score of the forecast that knows the distribution of the field's values but not where each
value sits.
"""

from __future__ import annotations

import numpy as np

from ..crps.metric import crps, half_pair_sum
from ..registry import metric


@metric(
    name="crps_skill_score",
    arity="ensemble",
    fields=("*",),
    differentiable=True,      # crps divided by a constant of the reference
    cost="cheap",
    higher_is_better=True,
    symmetric=False,          # reference and ensemble are different kinds of object
    units="dimensionless",
    reduction="mean",
)
def crps_skill_score(reference: np.ndarray, members: np.ndarray) -> float:
    """``1 - CRPS / UNC``: the fair ensemble CRPS against the climatological one.

    With :math:`y_{c,1} \\dots y_{c,n}` the reference's values in channel :math:`c`, the
    climatological forecast is their empirical distribution, and its mean CRPS over the same
    values is

    .. math::

        \\mathrm{UNC}_c = \\frac{1}{2n^2}\\sum_{i=1}^{n}\\sum_{j=1}^{n} |y_{c,i} - y_{c,j}|,

    the mean of Eq. 2 of the ``crps`` card with :math:`F` the empirical distribution itself
    (the uncertainty component ``UNC_0`` of Arnold et al. 2024, Eq. 10). It is computed
    exactly, with the self-pairs, because the empirical distribution is the forecast here
    rather than a sample of one. The skill score is (Gneiting & Raftery 2007, JASA 102:359,
    Sect. 2.3, Eq. 8, with the optimum score zero for a negatively oriented score)

    .. math::

        \\mathrm{CRPSS} = 1 - \\frac{\\overline{\\mathrm{CRPS}}}{\\overline{\\mathrm{UNC}}},

    a ratio of means: :math:`\\overline{\\mathrm{CRPS}}` is ``crps``, the fair score averaged
    over channels and cells, and :math:`\\overline{\\mathrm{UNC}}` the average of
    :math:`\\mathrm{UNC}_c` over channels. Each channel has its own climatology, so the two
    components of a velocity are never pooled into one distribution.

    Args:
        reference: Reference realization on the analysis grid, shape ``(C, *spatial)``.
        members: Ensemble members, shape ``(N, C, *spatial)``, member axis leading.

    Returns:
        The skill score, dimensionless. One when every member equals the reference, zero at
        the climatological score, negative below it, unbounded below. NaN when every channel
        of the reference is constant, where climatology is exact and the ratio is undefined.

    Raises:
        ValueError: If ``members`` does not carry a leading member axis over an array
            shaped like ``reference``, or if the ensemble is empty.
    """
    score = crps(reference, members)          # validates the pair
    values = np.asarray(reference, dtype=np.float64).reshape(reference.shape[0], -1).T
    n = values.shape[0]
    # (1/(2n^2)) sum_ij |y_i - y_j| = half_pair_sum / n^2, per channel, then averaged.
    uncertainty = float((half_pair_sum(values) / n**2).mean())
    if uncertainty == 0.0:
        return float("nan")
    return 1.0 - score / uncertainty
