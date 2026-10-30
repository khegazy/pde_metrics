"""Energy distance between the one-cell increment distributions of two fields.

The energy distance compares two distributions through average distances between their
samples: twice the mean distance between a draw from each, minus the mean distance within
each, and then a square root (Rizzo & Székely 2016). Here the two distributions are those of
the one-cell increments of the reference and of the prediction, exactly the samples
``increment_w1`` transports, so the two metrics differ only in how they weigh a difference of
distributions. On the line both are integrals of the gap between the two cumulative
distribution functions: the 1-Wasserstein distance integrates its absolute value, the energy
distance its square. Squaring a gap that is already small shrinks it further, so a difference
confined to the far tails, where both cumulative functions are close to 0 or 1, counts for
less here than in the transport distance. That contrast is what this metric is for.

Like ``increment_w1`` it is blind to where in the domain the increments sit, and to a
constant added to the field.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy import stats

from metrics.increment_flatness.metric import increments
from metrics.registry import metric


@metric(
    name="energy_distance",
    arity="pairwise",
    fields=("*",),
    differentiable=True,     # the square root of an integral of squared differences of step
                             # functions: smooth in the sample values away from ties and from
                             # identical samples, as rmse is smooth away from identical fields
    cost="cheap",
    higher_is_better=False,
    symmetric=True,          # D(F, G) = D(G, F): Rizzo & Székely (2016), WIREs 8(1), p. 27
    units="field^(1/2)",     # the square root of a mean of |x - y|
    requires_periodic=True,  # increment_flatness's wrap-around increments
)
def energy_distance(reference: NDArray[np.floating],
                    candidate: NDArray[np.floating]) -> float:
    """Energy distance between one-cell increment distributions, averaged over axes and channels.

    For real-valued random variables X ~ F and Y ~ G with independent copies X', Y', the
    squared energy distance is

        D^2(F, G) = 2 E|X - Y| - E|X - X'| - E|Y - Y'|,

    and the energy distance D(F, G) is its square root, which satisfies every axiom of a
    metric on distributions (Rizzo & Székely 2016, WIREs Comput. Stat. 8(1), 27-38, p. 27;
    the review shows no equation numbers there). D^2 is the quantity Székely & Rizzo (2013),
    J. Stat. Plann. Inference 143(8), 1249-1272, Definition 1, Eq. (2.4), call E(X, Y). On the
    line D^2 = 2 * integral of (F(x) - G(x))^2 dx (Székely & Rizzo 2013, the display
    immediately before Eq. (2.3)).

    The two-sample estimate is the V-statistic, every pair including i = j (Székely & Rizzo
    2013, Eq. (6.1)), which is D^2 between the two empirical distributions themselves. By the
    identity above it is exactly 2 * integral of (F_n - G_n)^2 over the two empirical
    cumulative functions, which ``scipy.stats.energy_distance`` evaluates by one merge of the
    sorted samples, returning its square root (SciPy documentation of
    ``scipy.stats.energy_distance``, Notes). The V-statistic rather than an unbiased
    U-statistic is used because it is never negative (Székely & Rizzo 2013, Sect. 1), and it
    is zero for identical samples, where the U-statistic is negative.

    D = sqrt(2) * MMD_b, where MMD_b is the (biased, V-statistic) maximum mean discrepancy of
    Gretton et al. (2012), JMLR 13, 723-773, Eq. (5), for the distance-induced kernel
    k(x, y) = (|x| + |y| - |x - y|) / 2 (Sejdinovic et al. 2013, Ann. Statist. 41(5),
    2263-2291, Eq. (4.2) and Theorem 22). That kernel has no bandwidth: the exponent 1 on
    |x - y| in the definition is the only parameter, and it is fixed.

    The average runs over (channel, axis) pairs, one distance each, as ``increment_w1``
    averages its transport distances, so the two metrics read the same samples in the same
    way. Every pair is included, also one whose increments vanish in both fields, where the
    distance is a well-defined zero.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.

    Returns:
        The mean energy distance, in the square root of the field's units. Zero when every
        increment distribution matches, unbounded above.

    Raises:
        ValueError: If the two fields differ in shape.
    """
    if reference.shape != candidate.shape:
        raise ValueError(f"energy_distance needs matching shapes, got {reference.shape} and "
                         f"{candidate.shape}")
    n_spatial = reference.ndim - 1
    return float(np.mean([
        # D = sqrt(2 * integral (F_n - G_n)^2): Rizzo & Székely (2016), p. 27, with the
        # one-dimensional identity of Székely & Rizzo (2013) before Eq. (2.3), applied to the
        # two empirical distributions as their Eq. (6.1) does.
        stats.energy_distance(increments(ref_c, axis).ravel(), increments(cand_c, axis).ravel())
        for ref_c, cand_c in zip(reference, candidate)
        for axis in range(-n_spatial, 0)
    ]))
