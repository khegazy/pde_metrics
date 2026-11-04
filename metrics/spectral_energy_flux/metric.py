"""Relative L2 distance between the spectral energy flux curves of two velocity fields.

The spectral energy flux Pi(K) is the rate at which the nonlinear term of the momentum equation
moves kinetic energy out of the Fourier modes inside wavenumber K. For a divergence-free velocity
it is the domain average of ``u_<K . (u . grad) u`` (Alexakis & Biferale 2018, Physics Reports
767-769, 1-101, Eq. 18 of the arXiv copy). For a divergent one this module uses Aluie's
sharp-spectral form at uniform density, which keeps the flux a pure exchange between scales: it
sums to zero over all modes (Aluie 2013, Physica D 247, 54-65, Sect. 4.1). It is a triple
correlation of the velocity, so two fields with the same energy spectrum can carry different
fluxes. The curve, at every shell up to half the smallest side of the grid, is the metric's
companion; the registered number is the L2 distance between the candidate's and the reference's
curves at the octave wavenumbers 1, 2, 4, ... divided by the L2 norm of the reference's there. No
source fixes that summary or that sampling: both are repository conventions (``issues/105``).

The flux is computed from the velocity alone, as for uniform density, on a weakly compressible
dataset; the compressible budget's baropycnal and pressure-dilatation terms need density and
pressure together with velocity (``judgements/003``). Nothing here tests the sign of the flux: in
two dimensions energy moves toward large scales, so a sign or constancy test tuned to three
dimensions does not apply, and the metric compares curves instead.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import COMPANION_KEY, FieldContext
from fmeval.external.kinet_spectral import physical_wavenumber_grid, spectral_derivative
from metrics.registry import companion, metric
from metrics.spectrum_l2.metric import OCTAVES, radial_energy_spectrum, radial_shells

#: ``ctx.cache`` key of the reference's flux curve, computed once per frame.
REFERENCE_FLUX = "spectral_energy_flux/reference_flux"


@metric(
    name="spectral_energy_flux",
    arity="pairwise",
    fields=("velocity",),
    differentiable=True,
    cost="moderate",        # 0.15 s a curve on 256 x 256: three inverse transforms per shell
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
    """||Pi_cand - Pi_ref|| / ||Pi_ref|| at the octave wavenumbers; a convention, issues/105.

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
    wavenumbers, flux = (ctx.cache[COMPANION_KEY] if COMPANION_KEY in ctx.cache
                         else energy_flux_curve(candidate, ctx=ctx))
    # The octaves 1, 2, 4, ... of the dense curve: the repository's sampling (issues/105).
    octave = (wavenumbers & (wavenumbers - 1)) == 0
    if REFERENCE_FLUX not in ctx.cache:
        ctx.cache[REFERENCE_FLUX] = energy_flux_curve(reference, ctx=ctx)[1][octave]
    reference_flux = ctx.cache[REFERENCE_FLUX]
    scale = float(np.linalg.norm(reference_flux))
    # Round-off bound: eps * max|u|^3 * pi / min(dx), the agent's own (see the docstring).
    round_off = (np.finfo(np.float64).eps * float(np.abs(reference).max()) ** 3
                 * np.pi / min(ctx.grid.spacing))
    if scale <= round_off:
        return float("nan")
    # Relative L2 distance between the two curves: the repository's convention (issues/105).
    return float(np.linalg.norm(np.asarray(flux)[octave] - reference_flux) / scale)


# Pi(K) changes sign along K (the cited run's clean medians are negative up to K = 8 and
# positive above), so its values are drawn on a symlog axis with the zero line, its wavenumbers
# on a log one, as Alexakis & Biferale (2018) draw fluxes (Figs. 20 and 31, "lin-log").
@companion(of="spectral_energy_flux", kind="curve",
           coordinate=("wavenumber", "cycles per domain"), analysed=OCTAVES,
           scales=("log", "symlog"))
def energy_flux_curve(velocity: NDArray[np.floating], *,
                      ctx: FieldContext) -> tuple[NDArray, NDArray]:
    """(K, Pi(K)): the spectral energy flux of one velocity field at every shell K up to N/2.

    With ``u_<K`` the velocity keeping only the modes in the shells up to K (a sharp spectral
    filter, Aluie 2013, Physica D 247, 54-65, Eq. 21 of arXiv:1012.5877v2),

        Pi(K) = < u_<K . div(u u) > - 1/2 < |u_<K|^2 div(u_<K) >,

    the domain average of the compressible "unsubtracted flux" of Aluie (2013), Sect. 4.1 (an
    unnumbered display), at uniform density. Its average equals that of the deformation work
    of his Eq. 14, because the two differ by a total gradient, and it vanishes once every mode
    is kept. For a divergence-free velocity the second term is zero and ``div(u u) = (u . grad)
    u``, so Pi is the incompressible flux ``<u_<K . (u . grad) u>`` of Alexakis & Biferale
    (2018, Physics Reports 767-769, 1-101, Eq. 18 of the arXiv copy, with the filter of their
    Eq. 16) and of the idea page's Eq. 1. Positive Pi is energy leaving the modes inside K for
    smaller scales; negative is energy arriving from them, which in two dimensions is the
    expected direction over the inverse-cascade range (Alexakis & Biferale, Eqs. 21-22 and
    Sect. 3.2.1, after Kraichnan 1967, Physics of Fluids 10(7), 1417-1423).

    Discretisation: the gradients are spectral, on the analysis grid's spacing, and give the
    Nyquist mode a zero derivative (``spectral_derivative`` keeps the real part of its inverse
    transform, which drops it; the filtered divergence below zeroes it explicitly, to agree).
    The products are formed in physical space without dealiasing. The first term is Parseval's
    co-spectrum ``Re[conj(u_hat) . D_hat] / M^2`` for ``M`` cells, ``D = div(u u)``, binned into
    ``radial_energy_spectrum``'s unit shells ``rint(|k|)`` and summed up to K. The second is
    formed in physical space from the filtered velocity and its divergence, each one inverse
    real transform of the masked half-spectrum, at each K. The filter keeps the shells up to and
    including K, so Pi(K) is the flux through ``|k| = K + 1/2``. The shells run from 1 to half the
    smallest side of the grid, 128 on 256 x 256; those beyond, which exist only in the corners
    of the grid, enter only through the flux out of the last shell.

    Args:
        velocity: ``(D, *spatial)``, one component per spatial axis in (x, y, z) order.
        ctx: Supplies the analysis grid: its shape sets the shells and its spacing the
            derivatives.

    Returns:
        The wavenumbers 1 to N/2, in cycles across the domain, and Pi at each, in velocity
        cubed per unit length (energy per unit mass per unit time).

    Raises:
        ValueError: If the velocity does not have one component per spatial axis, or an axis
            has fewer than two cells.
    """
    shape = tuple(ctx.grid.shape)
    n_spatial = ctx.grid.n_spatial
    if velocity.shape[0] != n_spatial or velocity.shape[1:] != shape:
        raise ValueError(f"the energy flux needs a velocity of shape (D, *spatial) with "
                         f"D = {n_spatial} on the grid {shape}; got {velocity.shape}")
    largest = min(shape) // 2
    if largest < 1:
        raise ValueError(f"the energy flux needs at least two cells along every axis; the grid "
                         f"is {shape}")
    spacing = list(ctx.grid.spacing)

    # D_i = d_j (u_i u_j), the momentum nonlinearity NL_i of Aluie (2013), Sect. 4.1, at
    # uniform density.
    nonlinear = np.stack([sum(spectral_derivative(velocity[i] * velocity[j], j, spacing=spacing)
                              for j in range(n_spatial)) for i in range(n_spatial)])
    # Parseval: <u_<K . D> = sum over shells <= K of Re[conj(u_hat) . D_hat] / M^2 for M cells.
    unsubtracted = np.cumsum(radial_energy_spectrum(velocity, ctx, other=nonlinear)
                             / velocity[0].size ** 2)

    # The density-equation term -1/2 <|u_<K|^2 div(u_<K)> of Aluie (2013), Sect. 4.1, from one
    # forward transform: the real transform's half-spectrum, masked by the shells up to K
    # (Aluie Eq. 21) and inverted, for u_<K and for its divergence.
    columns = shape[-1] // 2 + 1
    shells = radial_shells(shape)[..., :columns]
    wavevector = physical_wavenumber_grid(shape, spacing)
    for j, size in enumerate(shape):
        if size % 2 == 0:
            wavevector[j][(slice(None),) * j + (size // 2,)] = 0.0   # the Nyquist derivative
    spatial = tuple(range(1, n_spatial + 1))
    velocity_hat = np.fft.rfftn(velocity, axes=spatial)
    divergence_hat = 1j * sum(wavevector[j][..., :columns] * velocity_hat[j]
                              for j in range(n_spatial))
    flux = np.empty(largest)
    for k in range(1, largest + 1):
        keep = shells <= k
        low = np.fft.irfftn(velocity_hat * keep, s=shape, axes=spatial)
        low_divergence = np.fft.irfftn(divergence_hat * keep, s=shape,
                                       axes=tuple(range(n_spatial)))
        flux[k - 1] = unsubtracted[k] - np.mean(np.sum(low ** 2, axis=0) * low_divergence) / 2
    return np.arange(1, largest + 1), flux
