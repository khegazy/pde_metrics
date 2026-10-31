"""Energy score: a proper score for an ensemble forecast of a whole field at once.

The continuous ranked probability score (``crps``) judges an ensemble one cell at a time,
so it sees only the marginal distribution at each cell. The energy score treats the whole
field, every channel of every cell, as one vector and compares the ensemble with the
reference in the Euclidean norm of that vector. It is strictly proper for the joint
distribution (Gneiting & Raftery 2007), so in expectation no forecast beats the true
distribution of the field, and in one dimension it is exactly the CRPS.

The estimator is the *fair* one, with the pair term averaged over distinct members only,
for the same reason ``crps`` uses it: the plug-in average over all pairs, self-pairs
included, is biased by an amount that depends on the ensemble size.
"""

from __future__ import annotations

import numpy as np

from .._ensemble import as_ensemble
from ..registry import metric


@metric(
    name="energy_score",
    arity="ensemble",
    fields=("*",),
    differentiable=True,      # a sum of Euclidean norms; subgradient where a norm is zero
    cost="cheap",             # M(M+1)/2 norms of one field each
    higher_is_better=False,
    symmetric=False,          # reference and ensemble are different kinds of object
    units="field",
)
def energy_score(reference: np.ndarray, members: np.ndarray) -> float:
    """Fair ensemble energy score of the whole field, with index beta = 1.

    The energy score of a predictive distribution :math:`F` for a vector :math:`\\mathbf{y}`
    is (Gneiting & Raftery 2007, JASA 102(477):359, Section 4.3, Eq. 22, there with the
    opposite sign, larger is better)

    .. math::

        \\mathrm{ES}(F, \\mathbf{y}) = \\mathbb{E}\\|\\mathbf{X} - \\mathbf{y}\\|
            - \\tfrac{1}{2}\\mathbb{E}\\|\\mathbf{X} - \\mathbf{X}'\\|,

    with :math:`\\mathbf{X}, \\mathbf{X}'` independent draws from :math:`F`, the Euclidean
    norm, and the index beta = 1, which Section 4.3 states reduces Eq. 22 to the CRPS kernel
    form (Eq. 21) in one dimension. Here the vector is the whole field: every channel of every
    cell, flattened. For :math:`M \\ge 2` both expectations are estimated without bias from the
    members (Pacchiardi et al. 2024, JMLR 25(45), Appendix C.1.1, there for twice this score),

    .. math::

        \\widehat{\\mathrm{ES}} = \\frac{1}{M}\\sum_i \\|\\mathbf{x}_i - \\mathbf{y}\\|
            - \\frac{1}{2M(M-1)}\\sum_{i \\ne j} \\|\\mathbf{x}_i - \\mathbf{x}_j\\|,

    which on a single cell is the fair CRPS of ``metrics/crps`` (Ferro 2014, QJRMS
    140(683):1917). At :math:`M = 1` the pair term cannot be estimated and is dropped, as
    ``crps`` does: the score is :math:`\\|\\mathbf{x}_1 - \\mathbf{y}\\|`, which is neither fair
    nor proper (Ferro 2014, Sect. 2.1: no non-trivial score is fair at one member), and for a
    calibrated forecast is twice the score the same forecast gets with two or more members.

    Args:
        reference: Reference realization on the analysis grid, shape ``(C, *spatial)``.
        members: Ensemble members, shape ``(N, C, *spatial)``, member axis leading.

    Returns:
        The score in the field's own units. Zero when every member equals the reference;
        larger is worse. It grows with the square root of the number of values in the
        field, so it compares predictions only on the same grid.

    Raises:
        ValueError: If ``members`` does not carry a leading member axis over an array
            shaped like ``reference``, or if the ensemble is empty.
    """
    reference, members = as_ensemble(reference, members, min_members=1, what="energy_score")
    n_members = members.shape[0]
    vectors = members.reshape(n_members, -1)

    # E||X - y||, the sample mean over members (Gneiting & Raftery 2007, Eq. 22, first term).
    skill = float(np.linalg.norm(vectors - reference.reshape(1, -1), axis=1).mean())
    if n_members == 1:
        return skill

    # Sum of ||x_i - x_j|| over unordered pairs i < j: half the sum over ordered pairs i != j.
    pair_sum = sum(
        float(np.linalg.norm(vectors[i + 1:] - vectors[i], axis=1).sum())
        for i in range(n_members - 1)
    )
    # Fair pair term, 1/(2M(M-1)) over ordered pairs i != j (Pacchiardi et al. 2024,
    # Appendix C.1.1); with the unordered sum the factor is 1/(M(M-1)).
    spread = pair_sum / (n_members * (n_members - 1))
    return skill - spread
