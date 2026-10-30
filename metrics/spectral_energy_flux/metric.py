"""Relative L2 distance between the spectral energy flux curves of two velocity fields.

The spectral energy flux Pi(K) is the rate at which the nonlinear term of the momentum equation
moves kinetic energy out of the Fourier modes inside wavenumber K, the domain average of
``u_<K . (u . grad) u`` (Alexakis & Biferale 2018, Physics Reports 767-769, 1-101, Eq. 18 of
the arXiv copy). It is a triple correlation of the velocity, so two fields with the same energy
spectrum can carry different fluxes, and a field with random Fourier phases carries none on
average. The curve, sampled at the octave wavenumbers 1, 2, 4, ... up to half the smallest side
of the grid, is the metric's companion; the registered number is the L2 distance between the
candidate's and the reference's curves divided by the L2 norm of the reference's. No source fixes
that summary or that sampling: both are repository conventions (``issues/105``).

The flux is computed from the velocity alone, as for constant-density flow, on a weakly
compressible dataset whose density varies by a few percent; the compressible budget's other
terms need density and pressure together with velocity (``judgements/003``). Nothing here tests
the sign of the flux: in two dimensions energy moves toward large scales, so a sign or constancy
test tuned to three dimensions does not apply, and the metric compares curves instead.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import COMPANION_KEY, FieldContext
from fmeval.external.kinet_spectral import spectral_derivative
from metrics.registry import companion, metric
from metrics.spectrum_l2.metric import radial_energy_spectrum

#: ``ctx.cache`` key of the reference's flux curve, computed once per frame.
REFERENCE_FLUX = "spectral_energy_flux/reference_flux"


@metric(
    name="spectral_energy_flux",
    arity="pairwise",
    fields=("velocity",),
    differentiable=True,
    cost="cheap",
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

    ``Pi`` is the spectral energy flux curve of :func:`energy_flux_curve` (Alexakis & Biferale
    2018, Physics Reports 767-769, 1-101, Eq. 18 of the arXiv copy). Dividing by the
    reference's norm, as ``spectrum_l2`` does for the energy spectrum, makes the number
    dimensionless; the octave sampling weighs each octave of scale once. Both choices are the
    repository's, not a source's.

    Args:
        reference: The trusted velocity, shape ``(D, *spatial)`` with ``D`` spatial axes.
        candidate: The velocity being scored, same shape and grid.
        ctx: The analysis grid; its cache holds the candidate's curve for this variant when the
            pipeline has computed it, and keeps the reference's curve for the frame.

    Returns:
        Dimensionless, zero when the two curves coincide, 1 when the candidate carries no flux
        at all (a uniform velocity). NaN when the reference carries none, which leaves nothing
        to divide by.

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
    if scale == 0.0:
        return float("nan")
    # Relative L2 distance between the two curves: the repository's convention (issues/105).
    return float(np.linalg.norm(np.asarray(flux) - reference_flux) / scale)


@companion(of="spectral_energy_flux", kind="curve",
           coordinate=("wavenumber", "cycles per domain"))
def energy_flux_curve(velocity: NDArray[np.floating], *,
                      ctx: FieldContext) -> tuple[NDArray, NDArray]:
    """(K, Pi(K)): the spectral energy flux of one velocity field at octave wavenumbers K.

    Pi(K) is the domain average of ``u_<K . (u . grad) u``, with ``u_<K`` the velocity keeping
    only the modes inside K (Alexakis & Biferale 2018, Physics Reports 767-769, 1-101, Eqs. 16
    and 18 of the arXiv copy; the incompressible flux of the idea page's Eq. 1). Positive Pi is
    energy leaving the modes inside K for smaller scales; negative is energy arriving from
    them, which in two dimensions is the expected direction over the inverse-cascade range (the
    same review, Sect. 3.2.1, after Kraichnan 1967, Physics of Fluids 10(7), 1417-1423).

    Discretisation: the gradients are spectral (``spectral_derivative``, on the analysis grid's
    spacing), the advective product is formed in physical space without dealiasing, and
    Parseval's relation turns the average into the co-spectrum of the velocity and the
    advection, ``Re[conj(u_hat) . N_hat] / M^2`` for ``M`` cells, binned into
    ``radial_energy_spectrum``'s unit shells ``rint(|k|)``. Pi(K) sums the shells up to and
    including K, so it is the flux through ``|k| = K + 1/2``. The k = 0 shell carries nothing,
    because both fields' means are removed. The octaves are 1, 2, 4, ... up to half the
    smallest side of the grid: 1 to 128 on 256 x 256, eight coordinates (the repository's
    sampling, issues/105).

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
    # The advective term N_i = sum_j u_j d_j u_i, (u . grad) u in Eq. 18 of Alexakis & Biferale
    # (2018), with spectral derivatives.
    advection = np.stack([
        sum(velocity[j] * spectral_derivative(component, j, spacing=spacing)
            for j in range(n_spatial))
        for component in velocity])
    # Parseval: <u_<K . N> = sum over |k| <= K of Re[conj(u_hat) . N_hat] / M^2 for M cells,
    # so each shell's co-spectrum is the energy transfer T of Eq. 18; Pi(K) is its running sum
    # (Alexakis & Biferale 2018, Eq. 18 of the arXiv copy).
    transfer = radial_energy_spectrum(velocity, ctx, other=advection) / velocity[0].size ** 2
    flux = np.cumsum(transfer)
    # Octave sampling up to half the smallest side: the repository's convention (issues/105).
    octaves = 2 ** np.arange(int(np.log2(largest)) + 1)
    return octaves, flux[octaves]
