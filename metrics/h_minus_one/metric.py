"""Homogeneous negative Sobolev norm of the error: ``||reference - candidate||_{H^-1}``.

A dual norm, and therefore *weaker* than L2: it divides each Fourier coefficient of the
error by the magnitude of its wavevector, so an error carried by small-scale modes counts
for less than the same-amplitude error carried by large-scale modes. It stays finite for
rough and discontinuous fields, where the positive-order Sobolev norms do not, and Peyre
(2018) proves it is equivalent to the 2-Wasserstein distance up to constants set by the
density bounds -- which is why it appears in this repository at all: one FFT buys an
approximation to the transport distance that the double-penalty problem actually calls for.

The k = 0 mode is excluded, because ``1 / |k|`` is not defined there. That is not a choice
about this implementation but the definition of the *homogeneous* seminorm, and it has a
consequence worth stating where the code lives: a pure constant offset between the two
fields lies entirely in k = 0, so this metric is exactly blind to it and returns zero for a
uniform bias of any size. The ``bias`` degradation is what measures that.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import MetricContext
from metrics.registry import metric, pointwise_map


def riesz_potential(
    d: NDArray[np.floating], spacing: tuple[float, ...]
) -> NDArray[np.floating]:
    """Apply ``(-Laplacian)^(-1/2)`` to each channel of a periodic field.

    In Fourier space this divides every coefficient by ``|k|`` and sets the k = 0
    coefficient to zero. The result is the field whose mean square is the squared
    H^-1 seminorm, which is what makes a pointwise map possible for a norm that is
    otherwise non-local.

    Wavevectors come from ``physical_wavenumber_grid``, the same
    ``k_j = 2 pi fftfreq(N_j, d=dx_j)`` convention the repository already uses for its
    spectral derivatives -- so H^-1 and the vorticity it may be applied to are built on
    one definition of k. This is deliberately *not* ``fmeval.wavenumbers``, which counts
    whole cycles across the domain because filter cutoffs and the energy calibration must
    agree about which side of an integer shell a mode falls on. Both quantities are needed
    and they are not interchangeable: one is a mode index, this one carries units of
    inverse length.

    Args:
        d: Field of shape ``(C, *spatial)``, assumed periodic on every spatial axis.
        spacing: Cell size along each spatial axis, in ``(x, y, z)`` order. This must come
            from the *analysis* grid: at a coarsened grid the native spacing would scale
            the result by exactly the coarsening factor.

    Returns:
        Real array of shape ``(C, *spatial)``, in the field's units times a length.
    """
    # Imported here rather than at module scope: every metric module is imported on every
    # run, including runs that never call this one.
    from fmeval.external.kinet_spectral import physical_wavenumber_grid

    spatial = d.shape[1:]
    axes = tuple(range(1, d.ndim))
    k_components = physical_wavenumber_grid(spatial, list(spacing))
    k_magnitude = np.sqrt(sum(k**2 for k in k_components))

    inverse_k = np.zeros_like(k_magnitude)
    nonzero = k_magnitude > 0.0
    inverse_k[nonzero] = 1.0 / k_magnitude[nonzero]

    return np.fft.ifftn(np.fft.fftn(d, axes=axes) * inverse_k, axes=axes).real


@metric(
    name="h_minus_one",
    arity="pairwise",
    fields=("*",),
    returns="scalar",
    differentiable=True,
    cost="cheap",
    higher_is_better=False,
    symmetric=True,
    units="field*length",
    reduction="sqrt_mean",
)
def h_minus_one(
    reference: NDArray[np.floating],
    candidate: NDArray[np.floating],
    *,
    ctx: MetricContext,
) -> float:
    """Homogeneous H^-1 seminorm of the error, in the field's units times a length.

    Peyre (2018), ESAIM:COCV 24(4), 1489-1501 (preprint arXiv:1104.4631v2): Equation (5)
    is the infinitesimal linearization ``W_2(mu, mu + dmu) = ||dmu||_{Hdot^-1(mu)} +
    o(dmu)``, and Theorem 1 the non-asymptotic ``W_2(mu, nu) <= 2 ||mu - nu||_
    {Hdot^-1(mu)}``. Read those numbers off the arXiv version; the publisher's page
    returns 403, so the published numbering is unverified here.

    Note which norm those statements use: ``Hdot^-1(mu)``, weighted by the measure. What
    this function computes is the *unweighted* ``Hdot^-1(dx)``, which is what one FFT
    gives and what the tracker asks for. The two are related through bounds on the
    density, and the equivalence degrades as the lower bound approaches zero -- so the
    Wasserstein reading of this number is good for a well-mixed field and poor for one
    with near-vacuum regions. That is a caveat on the interpretation, not on the value.

    Normalised as a root *mean* square rather than an integral, so that at Sobolev order
    zero it would return exactly ``rmse`` and the two are directly comparable.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.
        ctx: Supplies the analysis grid, whose spacing sets the wavenumbers.

    Returns:
        The seminorm of the difference. Zero for identical fields, unbounded above, and
        also zero for two fields differing by a constant -- see the module docstring.
    """
    d = reference - candidate
    return float(np.sqrt(h_minus_one_map(reference, candidate, ctx=ctx).mean() / d.shape[0]))


@pointwise_map(of="h_minus_one")
def h_minus_one_map(
    reference: NDArray[np.floating],
    candidate: NDArray[np.floating],
    *,
    ctx: MetricContext,
) -> NDArray[np.floating]:
    """Per-cell squared smoothed error, summed over channels. Reduces by ``sqrt_mean``.

    Where ``mse``'s map shows a displaced sharp feature as two disjoint lobes -- the double
    penalty -- this map shows the same error after division by ``|k|``, which spreads each
    lobe over the displacement distance and lets the two partially cancel. The picture is
    the mechanism by which this metric is gentler on displacement than a pointwise norm.

    Args:
        reference: The trusted field, shape ``(C, *spatial)``.
        candidate: The field being scored, same shape.
        ctx: Supplies the analysis grid.

    Returns:
        An array of shape ``(*spatial)``: the channel axis is summed away.
    """
    smoothed = riesz_potential(reference - candidate, tuple(ctx.grid.spacing))
    return (smoothed**2).sum(axis=0)
