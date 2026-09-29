"""Palinstrophy: mean squared vorticity gradient, a reference-free physics diagnostic.

A single-field metric, the same shape as ``enstrophy``: it characterises one field rather
than comparing two, and the pipeline derives the drift from the reference downstream.

Where enstrophy weights the vorticity spectrum by k^0 and so measures how much rotational
activity there is, palinstrophy weights it by k^2 and so measures how *sharp* that activity
is. It is the natural quantity for the two-dimensional enstrophy cascade: it is the rate at
which viscosity destroys enstrophy. For any filter whose gain is a non-increasing function of
|k| alone -- a Gaussian, a Butterworth or an ideal low-pass, but not a box or a median, whose
responses are anisotropic or oscillate -- the fraction of palinstrophy removed is at least
the fraction of enstrophy removed. That is Chebyshev's integral inequality under the measure
|omega_hat(k)|^2: the squared gain is non-increasing and the weight |k|^2 increasing, so the
mean of their product is at most the product of their means. It is an inequality, not a
statement of how large the gap is on any particular field.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import MetricContext
from metrics.registry import metric


@metric(
    name="palinstrophy",
    arity="single",
    fields=("vorticity",),
    returns="scalar",
    differentiable=True,
    cost="cheap",
    higher_is_better=False,   # no direction of its own: the drift from the reference is
                              # what is read, exactly as for enstrophy
    symmetric=False,
    units="field^2/length^2",
)
def palinstrophy(x: NDArray[np.floating], *, ctx: MetricContext) -> float:
    """Mean palinstrophy, one half the mean squared vorticity gradient.

    Boffetta & Ecke (2012), Annu. Rev. Fluid Mech. 44, 427, DOI
    10.1146/annurev-fluid-120710-101240, p. 429: enstrophy Omega = (1/2) <omega^2> =
    int k^2 E(k) dk, and palinstrophy P = int k^4 E(k) dk, introduced with their Eq. (6),
    dOmega/dt = -2 nu P. The two definitions together fix P = (1/2) <|grad omega|^2>, the
    factor of one half computed here and the one ``enstrophy`` uses. Their setting is
    two-dimensional; in 3D this sums the squared gradients of all three components, the
    direct generalisation, which is not a definition taken from that paper.

    Derivatives are spectral, taken with the repository's existing
    ``k_j = 2 pi fftfreq(N_j, dx_j)`` routine (Pope 2000, "Turbulent Flows", Cambridge
    University Press, DOI 10.1017/CBO9780511840531, for the convention), so this and the
    vorticity it consumes are
    differentiated the same way. That matters here beyond consistency: ``fmeval.derived``
    records that mixing the solver's lattice-stencil vorticity with a spectral one differs
    by 8.1% rms, and a second derivative convention would add a second such discrepancy.

    Args:
        x: Vorticity on the analysis grid, shape ``(C, *spatial)``. One component in 2D,
            three in 3D; components and gradient directions are both summed before
            averaging over cells.
        ctx: Supplies the analysis grid, whose spacing sets the wavenumbers. Using the
            native spacing on a coarsened grid would scale the result by exactly the
            square of the coarsening factor.

    Returns:
        ``0.5 * <|grad omega|^2>``, in the square of the vorticity units per square length.
    """
    from fmeval.external.kinet_spectral import spectral_derivative

    spacing = list(ctx.grid.spacing)
    total = 0.0
    for channel in x:
        for axis in range(channel.ndim):
            total += float(np.mean(spectral_derivative(channel, axis, spacing=spacing) ** 2))
    return 0.5 * total
