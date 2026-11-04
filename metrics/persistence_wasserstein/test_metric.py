"""Tests for the 1-Wasserstein distance between persistence diagrams.

The registry-wide contract -- zero on identical fields, symmetry, dtype stability, monotonicity
under blur, the point set's shape and the number read from the cached point set -- lives in
``tests/test_metric_contract.py``, and the diagram itself is tested in
``metrics/persistence_distance``. What is tested here is the worked example printed in the card,
the offset that moves every point, the agreement with an exact optimal-transport solver, the
cellular stability bound, and the order against the bottleneck distance.

Every expected value is derived in the docstring beside it rather than copied from a run.
"""

from __future__ import annotations

from dataclasses import replace

import gudhi
import gudhi.wasserstein
import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from metrics.persistence_distance.metric import persistence_diagram, persistence_distance
from tests.conftest import make_ctx, synthetic_field

from .metric import DELTA, persistence_wasserstein, wasserstein


def wells(shallow: list[tuple[int, int]]) -> np.ndarray:
    """A periodic 4x4 field of ones with a deep well, -1 at cell (0, 0), and a shallow well, 0,
    at each cell of ``shallow``. Cells (0, 0), (2, 2), (0, 2) and (2, 1) are chosen so that no
    two wells used together touch, even at a corner or across the periodic seams."""
    x = np.ones((1, 4, 4))
    x[0, 0, 0] = -1.0
    for cell in shallow:
        x[(0, *cell)] = 0.0
    return x


def test_worked_example_from_the_card():
    """The reference has two shallow wells, so its diagram holds the deep well's piece (-1, inf),
    two pieces (0, 1) that merge into it when everything floods at 1, and the torus's classes
    born at 1: H1 = {(1, inf), (1, inf)}, H2 = {(1, inf)}.

    Filling one shallow well leaves one (0, 1) unmatched; matched to the diagonal it costs half
    its lifetime, 0.5, in both distances. Filling both leaves two unmatched: the bottleneck
    distance reports the worst, 0.5, while the 1-Wasserstein distance adds them, 1.0. Moving a
    shallow well leaves the diagram unchanged: 0 in both.
    """
    reference = wells([(2, 2), (0, 2)])
    np.testing.assert_array_equal(
        persistence_diagram(reference, ctx=make_ctx((4, 4))),
        [[0.0, 1.0, 0], [0.0, 1.0, 0], [-1.0, np.inf, 0], [1.0, np.inf, 1], [1.0, np.inf, 1],
         [1.0, np.inf, 2]])
    cases = {(0.5, 0.5): wells([(2, 2)]), (0.5, 1.0): wells([]),
             (0.0, 0.0): wells([(2, 1), (0, 2)])}
    for (bottleneck, total), candidate in cases.items():
        assert persistence_distance(reference, candidate, ctx=make_ctx((4, 4))) == (
            pytest.approx(bottleneck, abs=1e-12))
        assert persistence_wasserstein(reference, candidate, ctx=make_ctx((4, 4))) == (
            pytest.approx(total, rel=DELTA, abs=1e-12))


def test_an_offset_moves_every_point_and_each_one_counts():
    """Adding c = 0.25 everywhere moves every birth and death by c, so every point moves by c
    in the L-infinity norm. The two finite points (0, 1) live for 1 > 2c, so moving them is
    cheaper than sending both copies to the diagonal (2 x 0.5), and the four points at infinity
    can only move. The bottleneck distance is c = 0.25; the 1-Wasserstein distance is c times
    the six points, 1.5."""
    reference = wells([(2, 2), (0, 2)])
    assert persistence_distance(reference, reference + 0.25, ctx=make_ctx((4, 4))) == (
        pytest.approx(0.25))
    assert persistence_wasserstein(reference, reference + 0.25, ctx=make_ctx((4, 4))) == (
        pytest.approx(1.5, rel=DELTA))


def test_it_agrees_with_the_exact_optimal_transport_solver():
    """GUDHI's optimal-transport route (``gudhi.wasserstein``, exact) on the finite points of
    each dimension, plus the points at infinity matched in order of birth, agree with Hera to
    its relative error. Points at infinity are matched by sorted birth, the optimal matching of
    points on a line under a convex cost."""
    x, y = synthetic_field((16, 8), 1, seed=5), synthetic_field((16, 8), 1, seed=6)
    first, second = (persistence_diagram(f, ctx=make_ctx((16, 8))) for f in (x, y))
    exact = 0.0
    for k in range(3):
        a, b = first[first[:, 2] == k, :2], second[second[:, 2] == k, :2]
        fa, fb = np.isfinite(a[:, 1]), np.isfinite(b[:, 1])
        exact += gudhi.wasserstein.wasserstein_distance(a[fa], b[fb], order=1.0,
                                                        internal_p=np.inf)
        exact += np.abs(np.sort(a[~fa, 0]) - np.sort(b[~fb, 0])).sum()
    assert persistence_wasserstein(x, y, ctx=make_ctx((16, 8))) == pytest.approx(exact,
                                                                                  rel=DELTA)


def test_finite_points_against_points_at_infinity_alone_are_computed():
    """Two finite points against none, with one point at infinity in each diagram: each finite
    point goes to the diagonal at half its lifetime, 0.5 + 0.5, and the points at infinity
    coincide, so the distance is 1. Hera alone, given both parts at once, stops the process
    here; the metric hands it each part separately."""
    a = np.array([[0.0, 1.0], [0.0, 1.0], [-1.0, np.inf]])
    b = np.array([[-1.0, np.inf]])
    assert wasserstein(a, b) == pytest.approx(1.0)
    assert wasserstein(a, np.array([[-1.0, np.inf], [0.0, np.inf]])) == np.inf


@pytest.mark.parametrize("boundary", [("periodic", "periodic"), ("neumann", "periodic")])
def test_the_distance_never_exceeds_the_cellular_stability_bound(boundary):
    """Skraba & Turner (2020, arXiv:2006.16824v7), Theorem 4.6(i) at p = 1: W_1 with the
    L1 ground norm between the diagrams of two monotone functions on one complex is at most the
    sum over every cell of the complex of |f - g|. The L-infinity ground norm gives a smaller
    distance, so the bound holds for this metric too. The cell values are read from gudhi's own
    filtration of every cell, faces included. Checked on blurred, noisy and unrelated
    candidates; the factor 1 + DELTA allows Hera's error."""
    rng = np.random.default_rng(2)
    x = rng.standard_normal((1, 12, 10))
    ctx = replace(make_ctx((12, 10)), grid=replace(make_ctx((12, 10)).grid, boundary=boundary))
    periodic = [b == "periodic" for b in boundary]
    for candidate in (gaussian_filter(x, (0, 1, 1), mode="wrap"),
                      x + 0.3 * rng.standard_normal(x.shape), rng.standard_normal(x.shape)):
        first, second = (gudhi.PeriodicCubicalComplex(
            top_dimensional_cells=f[0], periodic_dimensions=periodic).all_cells()
            for f in (x, candidate))
        bound = np.abs(first - second).sum()
        value = persistence_wasserstein(x, candidate, ctx=replace(ctx, cache={}))
        assert 0.0 < value <= bound * (1 + DELTA)


def test_it_is_never_below_the_bottleneck_distance():
    """In each dimension the sum of the matched costs is at least their largest, and the
    optimal sum at least the optimal largest, so W_1 >= d_B dimension by dimension, and the
    total, a sum over dimensions, is at least their maximum."""
    rng = np.random.default_rng(3)
    x = synthetic_field((16, 8), 1, seed=1)
    for candidate in (x + 0.05 * rng.standard_normal(x.shape), synthetic_field((16, 8), 1, seed=9)):
        assert (persistence_wasserstein(x, candidate, ctx=make_ctx((16, 8)))
                >= persistence_distance(x, candidate, ctx=make_ctx((16, 8))) * (1 - DELTA))
