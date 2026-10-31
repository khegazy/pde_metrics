"""Variogram score: does an ensemble get the differences between pairs of points right?

The cell-by-cell ensemble scores (``crps``, ``spread_skill``, ``rank_histogram``) judge each
cell's distribution alone, and the energy score, though it sees the whole field, separates
ensembles that differ only in how their values vary together very weakly (Scheuerer &
Hamill 2015, Sect. 3b). The variogram score targets that structure directly: for every pair
of cells it compares the reference's difference, raised to the power p, with the ensemble's
mean of the same quantity, and sums the squared mismatches with weights that fall with the
distance between the cells.

It is proper but not strictly proper, and it cannot see a bias common to every cell or a sign
flip of the whole field, since every term depends only on the size of a difference. Read it
beside ``crps`` or ``energy_score``, never alone.

The ensemble estimate is the *fair* one, for the reason ``crps`` and ``energy_score`` use
theirs: the plug-in average of Scheuerer & Hamill's Eq. 4, squared, carries an extra variance
over M in every term, which shrinks as the ensemble narrows and so rewards an overconfident
ensemble at small M.
"""

from __future__ import annotations

import itertools

import numpy as np

from .._ensemble import as_ensemble
from ..registry import companion, metric

#: Order of the variogram, the power on each pairwise difference. Scheuerer & Hamill (2015,
#: MWR 143(4)) find p = 0.5 discriminates best among 0.5, 1 and 2 (Sects. 3a, 3c, 3d; tied
#: with p = 1 in Sect. 3b) and use it alone when comparing weights (Sect. 3e).
ORDER = 0.5


@metric(
    name="variogram_score",
    arity="ensemble",
    fields=("*",),
    differentiable=False,     # |a - b|^0.5 has an unbounded gradient where two values agree
    cost="expensive",         # every ordered pair of cells: O(M N^2) for N cells, M members
    higher_is_better=False,
    symmetric=False,          # reference and ensemble are different kinds of object
    units="field/length",     # (field^0.5)^2 per inverse-distance weight
    reduction="sum",
    # Wraps only the axes the grid declares periodic (ctx.grid.boundary); a bounded axis takes
    # pairs inside the domain, so the metric runs on any boundary.
    requires_periodic=False,
)
def variogram_score(reference: np.ndarray, members: np.ndarray, *, ctx) -> float:
    """Fair variogram score of order 0.5 with inverse-distance weights, summed over channels.

    Scheuerer & Hamill (2015, MWR 143(4):1321, Sect. 2, Eq. 3) define, for a vector
    :math:`\\mathbf{y}` and forecast :math:`F`,

    .. math::

        \\mathrm{VS}_p(F, \\mathbf{y}) = \\sum_{i,j=1}^{d} w_{ij}
            \\bigl(|y_i - y_j|^p - \\mathbb{E}_F|X_i - X_j|^p\\bigr)^2.

    It is a kernel score (Allen, Ginsbourger & Ziegel 2023, SIAM/ASA JUQ 11(3):906, Sect. 4.1,
    with their Definition 1, Eq. 3), so its expectations are estimated from the :math:`M`
    members without bias as for any kernel score (Pacchiardi et al. 2024, JMLR 25(45),
    App. C.1.2): with :math:`u_k = |x^{(k)}_i - x^{(k)}_j|^p`, mean :math:`\\bar u` and sample
    variance :math:`s^2` (divisor :math:`M - 1`), each term is
    :math:`(|y_i - y_j|^p - \\bar u)^2 - s^2 / M`. At :math:`M = 1` the correction is empty and
    the term is Scheuerer & Hamill's Eq. 4 estimate. Here the components are the cells of one
    channel, ``p`` is :data:`ORDER` and :math:`w_{ij} = 1/r_{ij}`, the inverse distance between
    the cell centres in the grid's physical units, the weighting Scheuerer & Hamill suggest
    (Sect. 2) and recommend when nothing is known about the correlations (Sect. 3e). On an axis
    the grid declares periodic the separation is the shorter way round, as Pacchiardi et al.
    measure distance on the globe (App. E.4.1); on a bounded axis it is the straight line inside
    the domain. Channels are scored separately and summed, pairs never mixing two components of
    a vector field (this bundle's choice; Sect. 2 calls a score across variables of different
    type doubtful).

    Args:
        reference: Reference realization on the analysis grid, shape ``(C, *spatial)``.
        members: Ensemble members, shape ``(N, C, *spatial)``, member axis leading.
        ctx: Field context; its grid's spacing and boundary set the distances.

    Returns:
        The score, in the field's units per unit length. Zero when every member equals the
        reference; larger is worse. The fair estimate can fall slightly below zero on one draw.

    Raises:
        ValueError: If ``members`` does not carry a leading member axis over an array
            shaped like ``reference``, or if the ensemble is empty.
    """
    return float(variogram_score_map(reference, members, ctx=ctx).sum())


@companion(of="variogram_score")
def variogram_score_map(reference: np.ndarray, members: np.ndarray, *, ctx) -> np.ndarray:
    """Each cell's share of the score: the weighted terms of the ordered pairs it starts.

    Every ordered pair (i, j) of Eq. 3 of Scheuerer & Hamill (2015) is charged to cell i, so
    cell i holds :math:`\\sum_j w_{ij}(\\dots)` summed over channels, and the map sums to
    :func:`variogram_score` by the declared ``sum`` reduction.
    """
    reference, members = as_ensemble(reference, members, min_members=1, what="variogram_score")
    n_members = members.shape[0]
    shape = reference.shape[1:]
    if ctx.grid.shape != shape:
        raise ValueError(f"variogram_score: field has spatial shape {shape}, the context's "
                         f"grid {ctx.grid.shape}")
    spacing = np.asarray(ctx.grid.spacing, dtype=np.float64)
    periodic = [b == "periodic" for b in ctx.grid.boundary]
    out = np.zeros(shape, dtype=np.float64)

    # Two copies end to end along every periodic axis, so a wrapped partner is a plain slice.
    reference_ext, members_ext = reference, members
    for axis, wraps in enumerate(periodic):
        if wraps:
            reference_ext = np.concatenate((reference_ext, reference_ext), axis=axis + 1)
            members_ext = np.concatenate((members_ext, members_ext), axis=axis + 2)

    # Each ordered pair once, by its offset j - i along every axis: 0 .. n-1 with the partner
    # wrapped on a periodic axis, -(n-1) .. n-1 with both cells inside the domain otherwise.
    ranges = [range(n) if wraps else range(-(n - 1), n) for n, wraps in zip(shape, periodic)]
    for offset in itertools.product(*ranges):
        if not any(offset):
            continue
        first, second, gaps = [], [], []
        for k, n, wraps in zip(offset, shape, periodic):
            if wraps:
                first.append(slice(0, n))
                second.append(slice(k, k + n))
                gaps.append(min(k, n - k))           # the shorter way round
            else:
                first.append(slice(max(0, -k), n - max(0, k)))
                second.append(slice(max(0, k), n - max(0, -k)))
                gaps.append(k)
        # w_ij = 1 / r_ij, inverse distance (Scheuerer & Hamill 2015, Sect. 2).
        weight = 1.0 / float(np.sqrt(np.sum((np.asarray(gaps) * spacing) ** 2)))

        # |y_i - y_j|^p and, member by member, |x_i - x_j|^p (Scheuerer & Hamill 2015, Eq. 3).
        observed = np.abs(reference[(slice(None), *first)]
                          - reference_ext[(slice(None), *second)]) ** ORDER
        forecast = np.abs(members[(slice(None), slice(None), *first)]
                          - members_ext[(slice(None), slice(None), *second)]) ** ORDER
        # Fair kernel-score estimate of (observed - E u)^2: the squared mismatch of the member
        # mean less the sample variance over M (Allen et al. 2023, Sect. 4.1; Pacchiardi et
        # al. 2024, App. C.1.2). Empty at M = 1.
        mismatch = (observed - forecast.mean(axis=0)) ** 2
        if n_members > 1:
            mismatch -= forecast.var(axis=0, ddof=1) / n_members
        out[tuple(first)] += weight * mismatch.sum(axis=0)  # channels scored, then summed
    return out
