"""Relative L2 distance between the spectral energy flux curves of two velocity fields.

The spectral energy flux Pi(K) is the rate at which the nonlinear term of the momentum equation
moves kinetic energy out of the Fourier modes inside wavenumber K. For a divergence-free velocity
it is the domain average of ``u_<K . (u . grad) u`` (Alexakis & Biferale 2018, Physics Reports
767-769, 1-101, Eq. 18 of the arXiv copy). For a divergent one this module uses Aluie's
sharp-spectral form at uniform density, which keeps the flux a pure exchange between scales: it
sums to zero over all modes (Aluie 2013, Physica D 247, 54-65, Sect. 4.1). It is a triple
correlation of the velocity, so two fields with the same energy spectrum can carry different
fluxes. The curve, sampled at the octave wavenumbers 1, 2, 4, ... up to half the smallest side of
the grid, is the metric's companion; the registered number is the L2 distance between the
candidate's and the reference's curves divided by the L2 norm of the reference's. No source fixes
that summary or that sampling: both are repository conventions (``issues/105``).

The flux is computed from the velocity alone, as for uniform density, on a weakly compressible
dataset; the compressible budget's baropycnal and pressure-dilatation terms need density and
pressure together with velocity (``judgements/003``). Nothing here tests the sign of the flux: in
two dimensions energy moves toward large scales, so a sign or constancy test tuned to three
dimensions does not apply, and the metric compares curves instead.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from degradations._shared.filters import _apply_filter
from fmeval.context import COMPANION_KEY, FieldContext
from fmeval.external.kinet_spectral import spectral_derivative
from metrics.registry import companion, metric
from metrics.spectrum_l2.metric import radial_energy_spectrum, radial_shells

#: ``ctx.cache`` key of the reference's flux curve, computed once per frame.
REFERENCE_FLUX = "spectral_energy_flux/reference_flux"


@metric(
    name="spectral_energy_flux",
    arity="pairwise",
    fields=("velocity",),
    differentiable=True,
    cost="moderate",        # about 0.1 s a curve on 256 x 256: a filter and a divergence per octave
    higher_is_better=False,
    symmetric=False,          # the reference's curve sets the scale, as in spectrum_l2
    units="dimensionless",
    requires_periodic=True,   # FFTs and spectral derivatives
)
def spectral_energy_flux(
    reference: NDArray[np.floating],
    candidate: NDArray[np.floating],
    *,
    ctx: FieldContext,
) -> float:
    """||Pi_cand - Pi_ref|| / ||Pi_ref|| over the octave wavenumbers; a convention, issues/105.

    ``Pi`` is the spectral energy flux curve of :func:`energy_flux_curve`. Dividing by the
    reference's norm, as ``spectrum_l2`` does for the energy spectrum, makes the number
    dimensionless; the octave sampling weighs each octave of scale once. Both choices are the
    repository's, not a source's.

    A reference curve no larger than floating-point round-off has nothing to divide by, and the
    result is NaN. Round-off is bounded by machine epsilon times the largest flux the field's
    own scales allow: its largest speed cubed times the grid's highest wavenumber, pi over the
    smallest spacing (my own bound, not a source's). A uniform velocity and the steady
    Taylor-Green vortex, whose advection is a pure gradient, both fall below it.

    Args:
        reference: The trusted velocity, shape ``(D, *spatial)`` with ``D`` spatial axes.
        candidate: The velocity being scored, same shape and grid.
        ctx: The analysis grid; its cache holds the candidate's curve for this variant when the
            pipeline has computed it, and keeps the reference's curve for the frame.

    Returns:
        Dimensionless, zero when the two curves coincide, 1 when the candidate carries no flux
        at all (a uniform velocity). NaN when the reference carries none.

    Raises:
        ValueError: If the shapes differ.
    """
    if reference.shape != candidate.shape:
        raise ValueError(f"spectral_energy_flux needs matching shapes, got {reference.shape} "
                         f"and {candidate.shape}")
    _, flux = (ctx.cache[COMPANION_KEY] if COMPANION_KEY in ctx.cache
               else energy_flux_curve(candidate, ctx=ctx))
    if REFERENCE_FLUX not in ctx.cache:
        ctx.cache[REFERENCE_FLUX] = energy_flux_curve(reference, ctx=ctx)[1]
    reference_flux = ctx.cache[REFERENCE_FLUX]
    scale = float(np.linalg.norm(reference_flux))
    # Round-off bound: eps * max|u|^3 * pi / min(dx), the agent's own (see the docstring).
    round_off = (np.finfo(np.float64).eps * float(np.abs(reference).max()) ** 3
                 * np.pi / min(ctx.grid.spacing))
    if scale <= round_off:
        return float("nan")
    # Relative L2 distance between the two curves: the repository's convention (issues/105).
    return float(np.linalg.norm(np.asarray(flux) - reference_flux) / scale)


@companion(of="spectral_energy_flux", kind="curve",
           coordinate=("wavenumber", "cycles per domain"))
def energy_flux_curve(velocity: NDArray[np.floating], *,
                      ctx: FieldContext) -> tuple[NDArray, NDArray]:
    """(K, Pi(K)): the spectral energy flux of one velocity field at octave wavenumbers K.

    With ``u_<K`` the velocity keeping only the modes in the shells up to K (a sharp spectral
    filter, Aluie 2013, Physica D 247, 54-65, Eq. 21 of arXiv:1012.5877v2),

        Pi(K) = < u_<K . div(u u) > - 1/2 < |u_<K|^2 div(u_<K) >,

    the domain average of the compressible "unsubtracted flux" of Aluie (2013), Sect. 4.1 (an
    unnumbered display), at uniform density. Its average equals that of the deformation work
    of his Eq. 14, because the two differ by a total gradient, and it vanishes once every mode
    is kept. For a divergence-free velocity the second term is zero and ``div(u u) = (u . grad)
    u``, so Pi is the incompressible flux ``<u_<K . (u . grad) u>`` of Alexakis & Biferale
    (2018, Physics Reports 767-769, 1-101, Eqs. 16 and 18 of the arXiv copy) and of the idea
    page's Eq. 1. Positive Pi is energy leaving the modes inside K for smaller scales; negative
    is energy arriving from them, which in two dimensions is the expected direction over the
    inverse-cascade range (Alexakis & Biferale, Sect. 3.2.1, after Kraichnan 1967, Physics of
    Fluids 10(7), 1417-1423).

    Discretisation: the gradients are spectral (``spectral_derivative``, on the analysis grid's
    spacing, which zeroes the Nyquist mode's derivative), and the products are formed in
    physical space without dealiasing. The first term is Parseval's co-spectrum
    ``Re[conj(u_hat) . D_hat] / M^2`` for ``M`` cells, ``D = div(u u)``, binned into
    ``radial_energy_spectrum``'s unit shells ``rint(|k|)`` and summed up to K. The second is
    formed in physical space from the filtered velocity, at each K. The filter keeps the shells
    up to and including K, so Pi(K) is the flux through ``|k| = K + 1/2``. The octaves are 1,
    2, 4, ... up to half the smallest side of the grid: 1 to 128 on 256 x 256, eight
    coordinates (the repository's sampling, issues/105). The shells beyond that, which exist
    only in the corners of the grid, enter only through the flux out of the last octave.

    Args:
        velocity: ``(D, *spatial)``, one component per spatial axis in (x, y, z) order.
        ctx: Supplies the analysis grid: its shape sets the shells and its spacing the
            derivatives.

    Returns:
        The octave wavenumbers, in cycles across the domain, and Pi at each, in velocity cubed
        per unit length (energy per unit mass per unit time).

    Raises:
        ValueError: If the velocity does not have one component per spatial axis, or an axis
            has fewer than two cells.
    """
    n_spatial = ctx.grid.n_spatial
    if velocity.shape[0] != n_spatial or velocity.shape[1:] != tuple(ctx.grid.shape):
        raise ValueError(f"the energy flux needs a velocity of shape (D, *spatial) with "
                         f"D = {n_spatial} on the grid {tuple(ctx.grid.shape)}; got "
                         f"{velocity.shape}")
    largest = min(ctx.grid.shape) // 2
    if largest < 1:
        raise ValueError(f"the energy flux needs at least two cells along every axis; the grid "
                         f"is {tuple(ctx.grid.shape)}")
    spacing = list(ctx.grid.spacing)

    def divergence(field: NDArray[np.floating], i: int | None = None) -> NDArray[np.floating]:
        """sum_j d_j (field_i field_j), or sum_j d_j field_j when ``i`` is None."""
        return sum(spectral_derivative(field[j] if i is None else field[i] * field[j], j,
                                       spacing=spacing) for j in range(n_spatial))

    # D_i = d_j (u_i u_j), the momentum nonlinearity NL_i of Aluie (2013), Sect. 4.1, at
    # uniform density.
    nonlinear = np.stack([divergence(velocity, i) for i in range(n_spatial)])
    # Parseval: <u_<K . D> = sum over shells <= K of Re[conj(u_hat) . D_hat] / M^2 for M cells.
    unsubtracted = np.cumsum(radial_energy_spectrum(velocity, ctx, other=nonlinear)
                             / velocity[0].size ** 2)
    shells = radial_shells(tuple(ctx.grid.shape))
    # Octave sampling up to half the smallest side: the repository's convention (issues/105).
    octaves = 2 ** np.arange(int(np.log2(largest)) + 1)
    flux = []
    for k in octaves:
        low = _apply_filter(velocity, (shells <= k).astype(float))   # u_<K, Aluie Eq. 21
        # The density-equation term -1/2 <|u_<K|^2 div(u_<K)> of Aluie (2013), Sect. 4.1.
        flux.append(unsubtracted[k] - np.mean(np.sum(low ** 2, axis=0) * divergence(low)) / 2)
    return octaves, np.array(flux)
