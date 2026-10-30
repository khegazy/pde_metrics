"""Tests for spectral_energy_flux: a hand-derived flux, energy conservation and invariances.

The contract tests (zero on identical fields, one value per fixed coordinate of the curve, the
same number from the cached curve, monotone under a synthetic blur) run over the registry in
``tests/test_metric_contract.py`` and are not repeated here.
"""

from __future__ import annotations

import numpy as np
import pytest

from fmeval.external.kinet_spectral import spectral_derivative
from tests.conftest import make_ctx, synthetic_field

from .metric import energy_flux_curve, spectral_energy_flux

#: Non-square on purpose: a swap of the x and y axes moves the profile onto y, where the
#: x-velocity has no x-derivative, and the flux would vanish.
SHAPE = (8, 4)


def burgers_velocity(a: float) -> np.ndarray:
    """u_x = sin(kx) + a sin(2kx), u_y = 0, with k = 2 pi / 8: one compressive triad."""
    x = np.broadcast_to(np.arange(SHAPE[0])[:, None], SHAPE)
    kappa = 2.0 * np.pi / SHAPE[0]
    return np.stack([np.sin(kappa * x) + a * np.sin(2.0 * kappa * x), np.zeros(SHAPE)])


def band_limited(n: int = 32, k_max: float = 5.0, seed: int = 0,
                 compressive: float = 0.0) -> np.ndarray:
    """A random velocity on an n x n grid with every mode inside k_max, unit RMS.

    The rotational part comes from a random stream function, and ``compressive`` times a
    divergent part from a random potential.
    """
    rng = np.random.default_rng(seed)
    k = np.fft.fftfreq(n) * n
    kx, ky = np.meshgrid(k, k, indexing="ij")
    band = np.hypot(kx, ky) <= k_max
    psi, phi = (np.fft.fft2(np.fft.ifft2((rng.standard_normal((n, n))
                                          + 1j * rng.standard_normal((n, n))) * band).real)
                for _ in range(2))
    unit = 2.0 * np.pi / n
    velocity = np.stack([
        np.fft.ifft2(1j * unit * (ky * psi + compressive * kx * phi)).real,   # psi_y + c phi_x
        np.fft.ifft2(1j * unit * (-kx * psi + compressive * ky * phi)).real])  # -psi_x + c phi_y
    return velocity / velocity.std()


def test_worked_example_matches_the_card():
    """The example in the card's Intuition section, derived by hand.

    With u_x = f(x) = sin(kx) + a sin(2kx) and u_y = 0, the momentum nonlinearity is
    d_x(f^2) = 2 f f', and expanding the products of sines and cosines gives

        f f' = k [ -(a/2) sin(kx) + (1/2) sin(2kx) + (3a/2) sin(3kx) + a^2 sin(4kx) ].

    At K = 1 the filtered velocity is sin(kx), so <u_<1 d_x(f^2)> = 2 <sin(kx) * -(a k/2)
    sin(kx)> = -a k / 2, and the density-equation term -1/2 <sin^2(kx) * k cos(kx)> is zero:
    Pi(1) = -a k / 2. At K = 2 every mode is kept, and both terms are averages of exact
    derivatives, <2 f^2 f'> and <f^2 f'>, so Pi(2) = 0: the nonlinear term only moves energy
    between the two modes. With k = 2 pi / 8 and a = 1, Pi(1) = -pi / 8 = -0.39269908;
    negative, energy arriving at the larger scale. Halving a halves Pi(1), so the candidate
    a = 1/2 against the reference a = 1 scores |-pi/16 + pi/8| / (pi/8) = 0.5.
    """
    wavenumbers, flux = energy_flux_curve(burgers_velocity(1.0), ctx=make_ctx(SHAPE))
    assert list(wavenumbers) == [1, 2]
    assert flux == pytest.approx([-0.39269908169872414, 0.0], abs=1e-12)
    value = spectral_energy_flux(burgers_velocity(1.0), burgers_velocity(0.5),
                                 ctx=make_ctx(SHAPE))
    assert value == pytest.approx(0.5, abs=1e-12)


def test_the_nonlinear_term_conserves_energy_on_a_divergence_free_field():
    """Summed over every mode, <u . (u . grad) u> vanishes for a divergence-free velocity
    (it is the average of u . grad(|u|^2 / 2)), so the flux through a wavenumber outside every
    mode of the field is zero: the term moves energy between scales and creates none
    (Alexakis & Biferale 2018, Physics Reports 767-769, 1-101, Eq. 18 of the arXiv copy)."""
    wavenumbers, flux = energy_flux_curve(band_limited(), ctx=make_ctx((32, 32)))
    assert np.abs(flux).max() > 1e-3, f"the field carries no flux to test: {flux}"
    assert abs(flux[wavenumbers >= 16][0]) < 1e-12 * np.abs(flux).max()


def test_the_flux_of_a_divergent_velocity_also_sums_to_zero():
    """The flux stays an exchange between scales when the velocity diverges.

    The plain advective form <u_<K . (u . grad) u> would end at -<div(u) |u|^2> / 2 once every
    mode is kept, a residual that is no transfer at all. Aluie's unsubtracted flux, whose
    average equals that of the deformation work (Aluie 2013, Physica D 247, 54-65, Sect. 4.1
    and Eq. 14), "should vanish in the absence of fluctuations at scales smaller than l", and
    it does: the field here has every mode inside |k| = 5, so Pi(16) is zero.
    """
    velocity = band_limited(compressive=1.0)
    wavenumbers, flux = energy_flux_curve(velocity, ctx=make_ctx((32, 32)))
    residual = -np.mean(sum(spectral_derivative(velocity[j], j) for j in range(2))
                        * np.sum(velocity ** 2, axis=0)) / 2
    assert abs(residual) > 1e-3, f"the field has no divergence residual to test: {residual}"
    assert abs(flux[wavenumbers >= 16][0]) < 1e-12 * np.abs(flux).max()


def test_on_a_divergence_free_field_the_flux_is_the_advective_form():
    """For div(u) = 0, div(u u) = (u . grad) u and the second term vanishes, so the flux is
    <u_<K . (u . grad) u> (Alexakis & Biferale 2018, Eqs. 16 and 18 of the arXiv copy),
    rebuilt here in physical space with an explicit sharp filter."""
    velocity = band_limited()
    wavenumbers, flux = energy_flux_curve(velocity, ctx=make_ctx((32, 32)))
    advection = np.stack([sum(velocity[j] * spectral_derivative(c, j) for j in range(2))
                          for c in velocity])
    k = np.fft.fftfreq(32) * 32
    shells = np.rint(np.hypot(*np.meshgrid(k, k, indexing="ij")))
    expected = [np.mean(np.sum(np.fft.ifft2(np.fft.fft2(velocity) * (shells <= K)).real
                               * advection, axis=0)) for K in wavenumbers]
    assert flux == pytest.approx(expected, abs=1e-14)


def test_the_flux_ignores_translation_and_a_uniform_velocity():
    """A translation multiplies each Fourier mode by a phase that cancels in every average, and
    a uniform velocity changes the flux only by averages of exact derivatives, which vanish:
    neither changes the curve."""
    velocity = band_limited(compressive=0.5)
    ctx = make_ctx((32, 32))
    _, flux = energy_flux_curve(velocity, ctx=ctx)
    _, moved = energy_flux_curve(np.roll(velocity, (5, -3), axis=(1, 2)), ctx=ctx)
    _, boosted = energy_flux_curve(velocity + np.array([0.7, -0.3])[:, None, None], ctx=ctx)
    assert moved == pytest.approx(flux, abs=1e-12)
    assert boosted == pytest.approx(flux, abs=1e-12)


def test_the_curve_carries_an_inverse_length_and_the_number_none():
    """Pi has the units of velocity cubed per length, so doubling the cell size halves it;
    the ratio of two curves on one grid does not change."""
    velocity, candidate = band_limited(seed=0), band_limited(seed=1)
    _, unit = energy_flux_curve(velocity, ctx=make_ctx((32, 32), spacing=1.0))
    _, doubled = energy_flux_curve(velocity, ctx=make_ctx((32, 32), spacing=2.0))
    assert doubled == pytest.approx(0.5 * unit, abs=1e-14)
    assert spectral_energy_flux(velocity, candidate, ctx=make_ctx((32, 32), spacing=2.0)) == \
        pytest.approx(spectral_energy_flux(velocity, candidate, ctx=make_ctx((32, 32))))


@pytest.mark.parametrize("shape", [(32, 32), (30, 34)])
def test_a_uniform_candidate_scores_one_and_a_uniform_reference_nan(shape):
    """A uniform velocity has no fluctuation and carries no flux: as a candidate its distance is
    the reference's whole curve, 1; as a reference there is nothing to divide by. On a 30 x 34
    grid the mean of 0.1 is not exact in floating point, so the uniform reference carries a
    round-off flux, which must still read as none."""
    velocity = synthetic_field(shape, 2, seed=0)
    uniform = np.stack([np.full(shape, 0.1), np.full(shape, 0.7)])
    assert spectral_energy_flux(velocity, uniform, ctx=make_ctx(shape)) == \
        pytest.approx(1.0, abs=1e-12)
    assert np.isnan(spectral_energy_flux(uniform, velocity, ctx=make_ctx(shape)))


def test_a_reference_whose_flux_is_round_off_scores_nan():
    """The steady Taylor-Green vortex u = (sin x cos y, -cos x sin y) has advection
    (u . grad) u = -grad(cos 2x + cos 2y)/4, a pure gradient, so no mode exchanges energy and
    its flux is zero up to round-off: the number is NaN, not a ratio of round-off."""
    x = 2.0 * np.pi * np.arange(16) / 16
    gx, gy = np.meshgrid(x, x, indexing="ij")
    vortex = np.stack([np.sin(gx) * np.cos(gy), -np.cos(gx) * np.sin(gy)])
    assert np.isnan(spectral_energy_flux(vortex, band_limited(n=16), ctx=make_ctx((16, 16))))


def test_a_velocity_without_one_component_per_axis_is_refused():
    with pytest.raises(ValueError, match="shape"):
        energy_flux_curve(np.zeros((1, *SHAPE)), ctx=make_ctx(SHAPE))
