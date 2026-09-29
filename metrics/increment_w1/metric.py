"""1-Wasserstein distance between the one-cell increment distributions of two fields.

Rather than transporting the fields themselves, this transports the *distribution* of
their neighbour-to-neighbour differences. That sidesteps the two problems a Wasserstein
distance on the field itself has here -- a signed field is not a measure, and optimal
transport in two dimensions is expensive -- because an increment distribution is
one-dimensional and already a probability measure. In one dimension the transport distance
has a closed form: sort both samples and average the absolute difference of matching
quantiles, so the whole metric is a sort.

What it is sensitive to is the *shape* of the increment distribution, tails included, and
what it is blind to is where in the domain those increments sit. It is therefore
complementary to a pointwise norm by construction rather than by accident: two fields with
identical increment statistics arranged into different structures are at distance zero,
and two fields that differ only by a shift are too.

It is the natural partner of ``increment_flatness``, which summarises the same
distribution by a single moment. This metric compares the whole distribution and so cannot
be fooled by a prediction that matches one moment while getting the rest wrong; the cost
is that it has no absolute anchor the way flatness has its 3.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from metrics.increment_flatness.metric import increments
from metrics.registry import metric


def axis_w1(a: NDArray[np.floating], b: NDArray[np.floating], axis: int) -> float:
    """1-Wasserstein distance between the increment distributions of ``a`` and ``b``.

    Both samples have the same number of points, so the quantile form of the 1-Wasserstein
    distance reduces to sorting each and averaging the absolute difference elementwise.
    That is exact, not an approximation: for two empirical measures on the line with equal
    weights the optimal coupling is the monotone one.

    Args:
        a: One channel of the reference field, shape ``(*spatial)``.
        b: The matching channel of the candidate, same shape.
        axis: Which spatial axis to take increments along, as a negative index.

    Returns:
        The transport distance, in the field's units. Zero when the two increment
        distributions coincide, which does not require the two fields to coincide.
    """
    return float(
        np.mean(
            np.abs(
                np.sort(increments(a, axis), axis=None)
                - np.sort(increments(b, axis), axis=None)
            )
        )
    )


@metric(
    name="increment_w1",
    arity="pairwise",
    fields=("*",),
    returns="scalar",
    differentiable=True,
    cost="cheap",
    higher_is_better=False,
    symmetric=True,
    units="field",
)
def increment_w1(
    reference: NDArray[np.floating], candidate: NDArray[np.floating]
) -> float:
    """Increment-PDF 1-Wasserstein distance, averaged over spatial axes and channels.

    The quantile form of the one-dimensional 1-Wasserstein distance between two empirical
    measures with equal weights is the mean absolute difference of their order statistics.
    The general treatment is Peyre and Cuturi (2019), "Computational Optimal Transport",
    Foundations and Trends in Machine Learning 11(5-6), 355-607, DOI 10.1561/2200000073,
    Chapter 2. No equation number is given here on purpose: the copy that could be read
    did not show the numbering, and a plausible-looking one would be worse than none. The
    result is short enough to derive instead, and the card's Definition does so -- the
    cost |x - y| is convex, so by the rearrangement inequality the monotone coupling is
    optimal, and for equal weights the monotone coupling is exactly "sort both".

    Increment statistics are used as physics-based criteria for generative turbulence
    models by Granero-Belinchon and Cabeza Gallucci (2024), Mach. Learn.: Sci. Technol.
    5(2), 025032, DOI 10.1088/2632-2153/ad43b3.

    The average runs over ``(channel, axis)`` pairs, one transport distance each, rather
    than over one pooled sample. Pooling would compare a mixture against a mixture and
    could cancel an error along one axis against an opposite error along another; keeping
    the axes separate cannot. Every pair is included, including one whose increments vanish
    in both fields -- unlike a flatness, a transport distance between two identical
    degenerate distributions is a well-defined zero rather than undefined.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.

    Returns:
        Mean transport distance, in the field's units. Zero when every increment
        distribution matches, unbounded above.
    """
    if reference.shape != candidate.shape:
        raise ValueError(
            f"increment_w1 needs matching shapes, got {reference.shape} and "
            f"{candidate.shape}"
        )
    n_spatial = reference.ndim - 1
    return float(
        np.mean([
            axis_w1(ref_c, cand_c, axis=axis)
            for ref_c, cand_c in zip(reference, candidate)
            for axis in range(-n_spatial, 0)
        ])
    )
