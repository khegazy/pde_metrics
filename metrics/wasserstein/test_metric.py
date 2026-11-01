"""Tests for the periodic quadratic Wasserstein distance between densities.

The registry-wide contract -- zero on identical fields, one finite float, dtype stability,
monotonicity under blur, the map reducing to the metric, the spacing scaling -- lives in
``tests/test_metric_contract.py``. What is tested here is the worked example printed in the
card, agreement with the exact one-dimensional solution on a target that is not uniform, the
bound against ``h_minus_one`` that the card quotes, and what the metric does outside its
domain and under a change of total mass.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import ndimage, optimize

from metrics.h_minus_one.metric import h_minus_one
from tests.conftest import cosine_mode, make_ctx

from .metric import wasserstein


def test_worked_example_from_the_card():
    """Columns at 1.5, 1, 0.5 and 1 times the mean density, against a uniform density: 0.225.

    The density varies along x only, so the transport is one-dimensional: on a circle of
    length L, the density f(x) = 1 + a cos(2 pi x / L) against the uniform one. On the line the
    optimal map is the monotone one, T(x) = G^-1(F(x)) (Peyre & Cuturi 2019, Eq. 2.36 and
    Remark 2.30); on the circle it is the monotone map after the best rotation of mass levels
    (Delon, Salomon & Sobolevski 2010, Sect. 2), and here the best rotation is zero because the
    problem is unchanged by the reflection x -> -x, which reverses the rotation, and the cost is
    convex in it. With F(x) = x / L + (a / 2 pi) sin(2 pi x / L) and G(y) = y / L,
    T(x) = x + (a L / 2 pi) sin(2 pi x / L). The squared distance is the f-weighted mean of the
    squared displacement, (a L / 2 pi)^2 times the mean of sin^2 (1 + a cos), which is 1/2, so
    W_2 = a L / (2 pi sqrt 2). With a = 0.5 and L = 4 cells: W_2 = 1 / (pi sqrt 2) = 0.225079
    cells. The grid sees this exactly: sin^2 at the four columns is 0, 1, 0, 1, so its
    f-weighted mean is (1.5 * 0 + 1 * 1 + 0.5 * 0 + 1 * 1) / 4 = 1/2, and the displacement is a
    single Fourier mode, which the spectral derivatives represent without error.
    """
    reference = 1.0 + 0.5 * cosine_mode((4, 4), mode=1)   # columns 1.5, 1, 0.5, 1
    uniform = np.ones((1, 4, 4))
    assert reference[0, :, 0] == pytest.approx([1.5, 1.0, 0.5, 1.0])
    assert wasserstein(reference, uniform, ctx=make_ctx((4, 4))) == pytest.approx(
        0.225079, abs=1e-6)


def test_agrees_with_the_exact_solution_on_the_circle_for_a_shifted_density():
    """A density varying along x only, against itself moved by an eighth of the domain.

    The optimal map then acts along x only, so the two-dimensional solve must equal the
    transport distance on the circle. Delon, Salomon & Sobolevski (2010), SIAM J. Appl. Math.
    70(7), Sect. 2, give it exactly: lift both cumulative distribution functions to the line
    with F(x + L) = F(x) + 1, couple mass level v of the reference with mass level v + theta of
    the candidate, and minimise the mean squared distance between the two quantile functions
    over the rotation theta, a convex function of theta. Evaluated here on a fine quantile
    grid, with each density read as constant on its cell. That is an independent algorithm,
    with neither a Monge-Ampere solve nor a spline, and on this smooth profile the two
    readings of the cells differ by less than the tolerance.
    """
    n = 256
    x = np.arange(n)
    f = 1.0 + 0.3 * np.cos(2 * np.pi * x / n) + 0.1 * np.sin(6 * np.pi * x / n)
    g = np.roll(f, n // 8)
    field = lambda profile: np.broadcast_to(profile[:, None], (n, 4))[None].copy()  # noqa: E731
    got = wasserstein(field(f), field(g), ctx=make_ctx((n, 4)))

    edges = np.arange(n + 1) - 0.5   # cell edges; cell centres sit on the integers
    cdf = [np.concatenate([[0.0], np.cumsum(p) / p.sum()]) for p in (f, g)]
    v = (np.arange(100_000) + 0.5) / 100_000

    def quantile(c: np.ndarray, levels: np.ndarray) -> np.ndarray:
        """The inverse of the lifted distribution function: one period further per unit."""
        return np.interp(levels % 1.0, c, edges) + n * np.floor(levels)

    def cost(theta: float) -> float:
        return float(np.mean((quantile(cdf[0], v) - quantile(cdf[1], v + theta)) ** 2))

    exact = np.sqrt(optimize.minimize_scalar(cost, bounds=(-0.5, 0.5), method="bounded",
                                             options={"xatol": 1e-10}).fun)
    assert got == pytest.approx(exact, rel=2e-4)


def test_lies_within_the_h_minus_one_bounds():
    """b^(-1/2) H <= W_2 <= 2 a^(-1/2) H for densities between a and b, with H the H^-1
    seminorm of the difference of the mass-normalised densities.

    The upper bound is Peyre (2018), ESAIM:COCV 24(4), Corollary 3, for a source density at
    least a. The lower bound is his Theorem 5, Eq. (17), on a flat torus: H is at most
    2 (b0^(1/2) - b1^(1/2)) / ln(b0 / b1) times W_2 for densities at most b0 and b1, and that
    logarithmic mean of the square roots is at most b^(1/2) with b the larger of the two.
    ``h_minus_one`` returns the seminorm as a root mean square over the grid, the
    normalisation in which a probability density on the torus has mean 1, so the bounds
    apply to it directly. The pair is a smooth density and its blurred copy, both between
    0.5 and 1.5 times their mean.
    """
    rng = np.random.default_rng(0)
    noise = ndimage.gaussian_filter(rng.standard_normal((32, 32)), 3, mode="wrap")
    reference = (1.0 + 0.5 * noise / np.abs(noise).max())[None]
    candidate = ndimage.gaussian_filter(reference, (0, 2, 2), mode="wrap")
    ctx = make_ctx((32, 32))
    normalised = [x / x.mean() for x in (reference, candidate)]
    low, high = min(x.min() for x in normalised), max(x.max() for x in normalised)
    seminorm = h_minus_one(*normalised, ctx=ctx)
    w2 = wasserstein(reference, candidate, ctx=ctx)
    assert high ** -0.5 * seminorm <= w2 <= 2.0 * low ** -0.5 * seminorm


def test_total_mass_is_normalised_away():
    """Each density is divided by its own mean, so a constant factor on either is invisible.

    That is the price of comparing probability measures: a prediction with the right
    arrangement of mass and the wrong total scores zero (Engquist & Froese 2014, Sect. 2.2).
    """
    reference = 1.0 + 0.5 * cosine_mode((8, 8), mode=1)
    ctx = make_ctx((8, 8))
    assert wasserstein(reference, 3.0 * reference, ctx=ctx) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("bad", [0.0, -1.0, np.nan])
def test_a_field_with_a_cell_that_is_not_a_positive_density_scores_nan(bad: float):
    """A transport distance is defined between measures; a cell at zero, below it or missing
    makes the field something else, and the metric says so rather than inventing a value."""
    reference = 1.0 + 0.5 * cosine_mode((8, 8), mode=1)
    candidate = reference.copy()
    candidate[0, 2, 3] = bad
    ctx = make_ctx((8, 8))
    assert np.isnan(wasserstein(reference, candidate, ctx=ctx))
    assert np.isnan(wasserstein(candidate, reference, ctx=ctx))
