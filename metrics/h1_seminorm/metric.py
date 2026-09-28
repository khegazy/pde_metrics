"""Homogeneous H^1 seminorm of the error: the root-mean-square of its gradient.

The positive-order counterpart of ``h_minus_one``, and the opposite trade. Where a negative
order divides each Fourier mode of the error by its wavenumber and so forgives small-scale
error, order +1 multiplies by it and so punishes small-scale error harder than L2 does.

The tracker rates this Low, and not because the idea is wrong: "the meeting has already
established the answer here: an H^1 penalty helps slightly and still fails at true
discontinuities. The reason is structural, in that a discontinuous function is not an element
of H^1 at all, so the gradient term is dominated by a mesh-resolution artifact rather than by
physics ... record it as tested and insufficient rather than spending further effort."

This bundle is that record. It exists so the claim is backed by a measurement in this
repository rather than by a recollection of a meeting, and so the negative-order norm has its
mirror image to be read against.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import MetricContext
from metrics.registry import metric, pointwise_map


@metric(
    name="h1_seminorm",
    arity="pairwise",
    fields=("*",),
    returns="scalar",
    differentiable=True,
    cost="cheap",
    higher_is_better=False,
    symmetric=True,
    units="field/length",
    reduction="sqrt_mean",
)
def h1_seminorm(
    reference: NDArray[np.floating],
    candidate: NDArray[np.floating],
    *,
    ctx: MetricContext,
) -> float:
    """Root-mean-square gradient of the error, in the field's units per length.

    Normalised as a root *mean* square rather than an integral, matching
    ``h_minus_one`` so that the two sit on one scale: for an error carried by a single mode
    of wavenumber k, this returns k times the rms error and ``h_minus_one`` returns the rms
    error divided by k, so their product is the mean square error regardless of k.

    Derivatives are spectral, using the repository's existing
    ``k_j = 2 pi fftfreq(N_j, dx_j)`` convention; see Pope (2000), "Turbulent Flows",
    Cambridge University Press, DOI 10.1017/CBO9780511840531.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ctx: Supplies the analysis grid, whose spacing sets the wavenumbers.

    Returns:
        Zero for identical fields, unbounded above, and also zero for two fields differing
        by a constant -- a gradient annihilates constants, exactly as the k = 0 exclusion
        does in ``h_minus_one``.
    """
    d = reference - candidate
    return float(np.sqrt(h1_seminorm_map(reference, candidate, ctx=ctx).mean() / d.shape[0]))


@pointwise_map(of="h1_seminorm")
def h1_seminorm_map(
    reference: NDArray[np.floating],
    candidate: NDArray[np.floating],
    *,
    ctx: MetricContext,
) -> NDArray[np.floating]:
    """Per-cell squared error gradient, summed over channels and directions.

    Where ``h_minus_one``'s map smooths a displaced feature's error into a single broad
    lobe, this one sharpens it: the map concentrates on the edges of the displacement, which
    is the picture of why a positive-order norm is the wrong tool for a shifted shock.

    Args:
        reference: The trusted field, shape ``(C, *spatial)``.
        candidate: The field being scored, same shape.
        ctx: Supplies the analysis grid.

    Returns:
        An array of shape ``(*spatial)``: the channel axis is summed away.
    """
    from fmeval.external.kinet_spectral import spectral_derivative

    d = reference - candidate
    spacing = list(ctx.grid.spacing)
    out = np.zeros(d.shape[1:], dtype=np.float64)
    for channel in d:
        for axis in range(channel.ndim):
            out += spectral_derivative(channel, axis, spacing=spacing) ** 2
    return out
