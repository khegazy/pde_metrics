"""Variogram score: does an ensemble get the differences between pairs of points right?

The cell-by-cell ensemble scores (``crps``, ``spread_skill``, ``rank_histogram``) judge each
cell's distribution alone, and the energy score, though it sees the whole field, separates
ensembles that differ only in how their values vary together very weakly (Scheuerer &
Hamill 2015, Sect. 3b). The variogram score targets that structure directly: for every pair
of cells it compares the reference's difference, raised to the power p, with the ensemble's
mean of the same quantity, and sums the squared mismatches with weights that fall with the
distance between the cells.

It is proper but not strictly proper, and it cannot see a bias common to every cell, since
every term depends only on differences. Read it beside ``crps`` or ``energy_score``, never
alone.
"""

from __future__ import annotations

import itertools

import numpy as np

from .._ensemble import as_ensemble
from ..registry import companion, metric

#: Order of the variogram, the power on each pairwise difference. Scheuerer & Hamill (2015,
#: MWR 143(4), Sect. 3a-3d and 3e) find p = 0.5 discriminates best among 0.5, 1 and 2.
ORDER = 0.5


@metric(
    name="variogram_score",
    arity="ensemble",
    fields=("*",),
    differentiable=False,     # |a - b|^0.5 has an unbounded gradient where two values agree
    cost="expensive",         # every pair of cells: O(M N^2) for N cells, M members
    higher_is_better=False,
    symmetric=False,          # reference and ensemble are different kinds of object
    # Smoothing members that are noisier than the reference first brings their small-scale
    # differences toward the reference's and lowers the score, then overshoots: on the
    # contract test's blur ladder it falls from 109 to 97 before rising to 2065.
    monotone_under_smoothing=False,
    units="field/length",     # (field^0.5)^2 per inverse-distance weight
    reduction="sum",
)
def variogram_score(reference: np.ndarray, members: np.ndarray, *, ctx) -> float:
    """Variogram score of order 0.5 with inverse-distance weights, summed over channels.

    Scheuerer & Hamill (2015, MWR 143(4):1321, Sect. 2, Eq. 3) define, for a vector
    :math:`\\mathbf{y}` and forecast :math:`F`,

    .. math::

        \\mathrm{VS}_p(F, \\mathbf{y}) = \\sum_{i,j=1}^{d} w_{ij}
            \\bigl(|y_i - y_j|^p - \\mathbb{E}_F|X_i - X_j|^p\\bigr)^2,

    with the expectation approximated from the :math:`M` members by
    :math:`\\frac{1}{M}\\sum_k |x^{(k)}_i - x^{(k)}_j|^p` (their Eq. 4). Here the components
    are the cells of one channel, ``p`` is :data:`ORDER` and :math:`w_{ij} = 1/r_{ij}`, the
    inverse Euclidean distance between the cell centres in the grid's physical units, the
    weighting Scheuerer & Hamill suggest (Sect. 2) and recommend when nothing is known about
    the correlations (Sect. 3e). The diagonal terms vanish and carry no weight. Pairs are
    taken inside the domain with the straight-line distance, never wrapped, so a periodic
    grid is treated as unwrapped (this bundle's choice). Channels are scored separately and
    summed, pairs never mixing two components of a vector field (this bundle's choice; Sect.
    2 calls a score across variables of different type doubtful).

    Args:
        reference: Reference realization on the analysis grid, shape ``(C, *spatial)``.
        members: Ensemble members, shape ``(N, C, *spatial)``, member axis leading.
        ctx: Field context; its grid's spacing sets the distances.

    Returns:
        The score, in the field's units per unit length. Zero when every member equals the
        reference; larger is worse.

    Raises:
        ValueError: If ``members`` does not carry a leading member axis over an array
            shaped like ``reference``, or if the ensemble is empty.
    """
    return float(variogram_score_map(reference, members, ctx=ctx).sum())


@companion(of="variogram_score")
def variogram_score_map(reference: np.ndarray, members: np.ndarray, *, ctx) -> np.ndarray:
    """Each cell's share of the score: the weighted terms of every pair it belongs to.

    Every ordered pair (i, j) of Eq. 3 of Scheuerer & Hamill (2015) is charged to cell i, so
    cell i holds :math:`\\sum_j w_{ij}(\\dots)^2`, summed over channels, and the map sums to
    :func:`variogram_score` by the declared ``sum`` reduction. Each unordered pair is computed
    once and charged to both of its cells.
    """
    reference, members = as_ensemble(reference, members, min_members=1, what="variogram_score")
    shape = reference.shape[1:]
    spacing = np.asarray(ctx.grid.spacing, dtype=np.float64)
    out = np.zeros(shape, dtype=np.float64)

    # One displacement per unordered pair direction: keep offsets whose first non-zero
    # component is positive, so (i, j) and (j, i) are visited once.
    for offset in itertools.product(*(range(-(n - 1), n) for n in shape)):
        leading = next((k for k in offset if k != 0), 0)
        if leading <= 0:
            continue
        first = tuple(slice(max(0, -k), n - max(0, k)) for k, n in zip(offset, shape))
        second = tuple(slice(max(0, k), n - max(0, -k)) for k, n in zip(offset, shape))
        # w_ij = 1 / r_ij, inverse distance (Scheuerer & Hamill 2015, Sect. 2).
        weight = 1.0 / float(np.sqrt(np.sum((np.asarray(offset) * spacing) ** 2)))

        # |y_i - y_j|^p and its ensemble mean (Scheuerer & Hamill 2015, Eqs. 3-4).
        observed = np.abs(reference[(slice(None), *first)] - reference[(slice(None), *second)])
        forecast = np.abs(
            members[(slice(None), slice(None), *first)]
            - members[(slice(None), slice(None), *second)]
        )
        term = weight * (observed**ORDER - (forecast**ORDER).mean(axis=0)) ** 2
        term = term.sum(axis=0)  # channels scored separately, then summed
        out[first] += term
        out[second] += term
    return out
