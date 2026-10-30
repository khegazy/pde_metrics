"""Tests for spectral_energy_flux: a hand-derived flux, energy conservation and invariances.

The contract tests (zero on identical fields, one value per fixed coordinate of the curve, the
same number from the cached curve, monotone under a synthetic blur) run over the registry in
``tests/test_metric_contract.py`` and are not repeated here.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import make_ctx

from .metric import energy_flux_curve, spectral_energy_flux

#: Non-square on purpose: a swap of the x and y axes moves the profile onto y, where the
#: x-velocity has no x-derivative, and the flux would vanish.
SHAPE = (8, 4)


def burgers_velocity(a: float) -> np.ndarray:
    """u_x = sin(kx) + a sin(2kx), u_y = 0, with k = 2 pi / 8: one compressive triad."""
    x = np.broadcast_to(np.arange(SHAPE[0])[:, None], SHAPE)
    kappa = 2.0 * np.pi / SHAPE[0]
    return np.stack([np.sin(kappa * x) + a * np.sin(2.0 * kappa * x), np.zeros(SHAPE)])


def band_limited_solenoidal(n: int = 32, k_max: float = 5.0, seed: int = 0) -> np.ndarray:
    """A random divergence-free velocity on an n x n grid with every mode inside k_max."""
    rng = np.random.default_rng(seed)
    k = np.fft.fftfreq(n) * n
    kx, ky = np.meshgrid(k, k, indexing="ij")
    psi = np.fft.ifft2((rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n)))
                       * (np.hypot(kx, ky) <= k_max)).real
    psi_hat, unit = np.fft.fft2(psi), 2.0 * np.pi / n
    velocity = np.stack([np.fft.ifft2(1j * unit * ky * psi_hat).real,       # u = d psi / dy
                         np.fft.ifft2(-1j * unit * kx * psi_hat).real])     # v = -d psi / dx
    return velocity / velocity.std()


def test_worked_example_matches_the_card():
    """The example in the card's Intuition section, derived by hand.

    With u_x = f(x) = sin(kx) + a sin(2kx) and u_y = 0, the advection is f f', and expanding
    the products of sines and cosines gives

        f f' = k [ -(a/2) sin(kx) + (1/2) sin(2kx) + (3a/2) sin(3kx) + a^2 sin(4kx) ].

    Only the modes of u, at k and 2k, enter the flux. The average of u_<1 . (u . grad) u keeps
    the sin(kx) parts: <sin(kx) * -(a k/2) sin(kx)> = -a k / 4, so Pi(1) = -a k / 4. Adding the
    shell at 2k gives <a sin(2kx) * (k/2) sin(2kx)> = a k / 4 and Pi(2) = 0: the nonlinear term
    only moves energy between the two modes. With k = 2 pi / 8 and a = 1,
    Pi(1) = -pi / 16 = -0.19634954; negative, energy arriving at the larger scale. Halving a
    halves Pi(1), so the candidate a = 1/2 against the reference a = 1 scores
    |-pi/32 + pi/16| / (pi/16) = 0.5.
    """
    wavenumbers, flux = energy_flux_curve(burgers_velocity(1.0), ctx=make_ctx(SHAPE))
    assert list(wavenumbers) == [1, 2]
    assert flux == pytest.approx([-0.19634954084936207, 0.0], abs=1e-12)
    value = spectral_energy_flux(burgers_velocity(1.0), burgers_velocity(0.5),
                                 ctx=make_ctx(SHAPE))
    assert value == pytest.approx(0.5, abs=1e-12)


def test_the_nonlinear_term_conserves_energy_on_a_divergence_free_field():
    """Summed over every mode, <u . (u . grad) u> vanishes for a divergence-free velocity
    (it is the average of u . grad(|u|^2 / 2)), so the flux through a wavenumber outside every
    mode of the field is zero: the term moves energy between scales and creates none
    (Alexakis & Biferale 2018, Physics Reports 767-769, 1-101, Eq. 18 of the arXiv copy)."""
    wavenumbers, flux = energy_flux_curve(band_limited_solenoidal(), ctx=make_ctx((32, 32)))
    assert np.abs(flux).max() > 1e-3, f"the field carries no flux to test: {flux}"
    assert abs(flux[wavenumbers >= 16][0]) < 1e-12 * np.abs(flux).max()


def test_the_flux_ignores_translation_and_a_uniform_velocity():
    """A translation multiplies each Fourier mode of u and of (u . grad) u by the same phase,
    and a uniform velocity U adds i (k . U) |u_hat|^2, which is imaginary, to each mode's
    co-spectrum: neither changes the flux."""
    velocity = band_limited_solenoidal()
    ctx = make_ctx((32, 32))
    _, flux = energy_flux_curve(velocity, ctx=ctx)
    _, moved = energy_flux_curve(np.roll(velocity, (5, -3), axis=(1, 2)), ctx=ctx)
    _, boosted = energy_flux_curve(velocity + np.array([0.7, -0.3])[:, None, None], ctx=ctx)
    assert moved == pytest.approx(flux, abs=1e-12)
    assert boosted == pytest.approx(flux, abs=1e-12)


def test_the_curve_carries_an_inverse_length_and_the_number_none():
    """Pi has the units of velocity cubed per length, so doubling the cell size halves it;
    the ratio of two curves on one grid does not change."""
    velocity, candidate = band_limited_solenoidal(seed=0), band_limited_solenoidal(seed=1)
    _, unit = energy_flux_curve(velocity, ctx=make_ctx((32, 32), spacing=1.0))
    _, doubled = energy_flux_curve(velocity, ctx=make_ctx((32, 32), spacing=2.0))
    assert doubled == pytest.approx(0.5 * unit, abs=1e-14)
    assert spectral_energy_flux(velocity, candidate, ctx=make_ctx((32, 32), spacing=2.0)) == \
        pytest.approx(spectral_energy_flux(velocity, candidate, ctx=make_ctx((32, 32))))


def test_a_uniform_candidate_scores_one_and_a_uniform_reference_nan():
    """A uniform velocity has no fluctuation and carries no flux: as a candidate its distance is
    the reference's whole curve, 1; as a reference there is nothing to divide by."""
    velocity = band_limited_solenoidal()
    uniform = np.full_like(velocity, 0.5)
    assert spectral_energy_flux(velocity, uniform, ctx=make_ctx((32, 32))) == \
        pytest.approx(1.0, abs=1e-12)
    assert np.isnan(spectral_energy_flux(uniform, velocity, ctx=make_ctx((32, 32))))


def test_a_velocity_without_one_component_per_axis_is_refused():
    with pytest.raises(ValueError, match="shape"):
        energy_flux_curve(np.zeros((1, *SHAPE)), ctx=make_ctx(SHAPE))
