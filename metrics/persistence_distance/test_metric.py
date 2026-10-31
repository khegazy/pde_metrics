"""Tests for the bottleneck distance between persistence diagrams.

The registry-wide contract -- zero on identical fields, symmetry, dtype stability,
monotonicity under blur, the point set's shape and the number read from the cached point set --
lives in ``tests/test_metric_contract.py``. What is tested here is the worked example printed
in the card, the stability theorem that bounds the metric by the pointwise maximum error, the
invariance to a whole-cell translation on a periodic grid, and that the complex wraps exactly
the axes the grid declares periodic.

Every expected value is derived in the docstring beside it rather than copied from a run.
"""

from __future__ import annotations

from dataclasses import replace

import gudhi
import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from fmeval.data.base import GridSpec
from metrics.max_error.metric import max_error
from tests.conftest import make_ctx, synthetic_field

from .metric import (
    betti_curves,
    euler_characteristic_curve,
    persistence_diagram,
    persistence_distance,
)


def two_wells(shallow: tuple[int, int] | None = (2, 2)) -> np.ndarray:
    """A 4x4 field of ones with a deep well, -1 at cell (0, 0), and a shallow well, 0 at
    ``shallow`` (none if None). Cells (0, 0), (2, 2) and (2, 1) touch neither each other nor,
    across the periodic seams, any common corner."""
    x = np.ones((1, 4, 4))
    x[0, 0, 0] = -1.0
    if shallow is not None:
        x[(0, *shallow)] = 0.0
    return x


def test_worked_example_from_the_card():
    """A displaced well costs nothing; a missing well costs half its lifetime.

    Reference: ``two_wells()`` on the periodic 4x4 grid. Raising the threshold, the deep well
    appears at -1 and the shallow one at 0 as a second connected piece; at 1 every cell enters,
    the two pieces merge (the younger one, born at 0, dies) and the torus is complete. Its
    diagram is H0 = {(-1, inf), (0, 1)}, H1 = {(1, inf), (1, inf)}, H2 = {(1, inf)}.

    Moving the shallow well to (2, 1) gives the same diagram, so the distance is 0, while the
    largest pointwise difference is |1 - 0| = 1 at the two cells it left and entered.

    Filling the shallow well leaves H0 = {(-1, inf)}: the point (0, 1) has no partner and is
    matched to the diagonal, at L-infinity distance (1 - 0)/2 = 0.5, its half-lifetime
    (Cohen-Steiner, Edelsbrunner & Harer 2005, Proc. SoCG, Sect. 3.1); every other point is
    unchanged, so the distance is 0.5. The largest pointwise difference is again 1.
    """
    reference = two_wells()
    np.testing.assert_array_equal(
        persistence_diagram(reference, ctx=make_ctx((4, 4))),
        [[0.0, 1.0, 0], [-1.0, np.inf, 0], [1.0, np.inf, 1], [1.0, np.inf, 1], [1.0, np.inf, 2]])
    moved, filled = two_wells(shallow=(2, 1)), two_wells(shallow=None)
    assert persistence_distance(reference, moved, ctx=make_ctx((4, 4))) == 0.0
    assert max_error(reference, moved) == 1.0
    assert persistence_distance(reference, filled, ctx=make_ctx((4, 4))) == pytest.approx(0.5)
    assert max_error(reference, filled) == 1.0


def test_betti_and_euler_curves_of_the_worked_example():
    """Counting the points of ``two_wells()`` alive on [b, d) at each threshold.

    At t = -1 only (-1, inf) is alive: Betti numbers (1, 0, 0). At t = 0 and t = 0.5, (0, 1) has
    joined it: (2, 0, 0). At t = 1, (0, 1) is dead and the four points born at 1 are alive:
    (1, 2, 1), the torus. The Euler characteristic is 1 - 0 + 0 = 1, then 2, 2, and
    1 - 2 + 1 = 0 at t = 1, the Euler characteristic of the torus.
    """
    diagram = persistence_diagram(two_wells(), ctx=make_ctx((4, 4)))
    thresholds = [-1.0, 0.0, 0.5, 1.0]
    np.testing.assert_array_equal(betti_curves(diagram, thresholds, 3),
                                  [[1, 2, 2, 1], [0, 0, 0, 2], [0, 0, 0, 1]])
    np.testing.assert_array_equal(euler_characteristic_curve(diagram, thresholds, 3),
                                  [1, 2, 2, 0])


def test_the_euler_curve_matches_a_direct_count_of_cells():
    """The Euler-Poincare formula, chi = sum_k (-1)^k beta_k = sum over cells of
    (-1)^dimension, checked at every threshold on a random periodic field.

    The cell count reads gudhi's own filtration of every cell of the complex, where a cell's
    dimension is the number of odd entries of its index; the Betti side reads only the
    persistence diagram. They are computed by different routes, so agreement checks that the
    diagram holds every feature, including the classes that never die.
    """
    x = synthetic_field((8, 6), 1, seed=3)
    diagram = persistence_diagram(x, ctx=make_ctx((8, 6)))
    cells = gudhi.PeriodicCubicalComplex(top_dimensional_cells=x[0],
                                         periodic_dimensions=[True, True]).all_cells()
    index = np.indices(cells.shape)
    sign = (-1.0) ** (index % 2).sum(axis=0)
    thresholds = np.sort(x.ravel())
    direct = [int(sign[cells <= t].sum()) for t in thresholds]
    np.testing.assert_array_equal(euler_characteristic_curve(diagram, thresholds, 3), direct)


@pytest.mark.parametrize("shift", [(1, 0), (3, 5), (7, 2)])
def test_a_whole_cell_translation_on_a_periodic_grid_is_at_distance_zero(shift):
    """A periodic roll relabels the cells of the torus without changing which cells are
    neighbours, so every sublevel set is the same complex moved and the diagram is identical:
    the distance is exactly 0, while the pointwise maximum error is not."""
    x = synthetic_field((16, 8), 1, seed=5)
    moved = np.roll(x, shift, axis=(1, 2))
    assert persistence_distance(x, moved, ctx=make_ctx((16, 8))) == 0.0
    assert max_error(x, moved) > 0.0


@pytest.mark.parametrize("shape, boundary", [
    ((16, 8), ("periodic", "periodic")),
    ((16, 8), ("periodic", "neumann")),
    ((16, 8), ("neumann", "neumann")),
    ((32,), ("periodic",)),
    ((32,), ("neumann",)),
    ((6, 5, 4), ("periodic", "periodic", "periodic")),
    ((6, 5, 4), ("neumann", "periodic", "neumann")),
])
def test_the_distance_never_exceeds_the_largest_pointwise_difference(shape, boundary):
    """The Cellular Wasserstein Stability Theorem of Skraba & Turner (2020, arXiv:2006.16824v7,
    Theorem 4.6(i)) taken to p -> inf: the maximum over k of d_B(D_k(f), D_k(g)) is at most the
    largest difference over the cells of the complex, which for the T-construction is the
    largest difference over the grid cells, ||f - g||_inf.

    Checked on blurred, noisy and unrelated candidates of a random field, on periodic, walled and
    mixed grids in one, two and three dimensions; the factor 1 + 1e-12 allows gudhi's last-bits
    error.
    """
    rng = np.random.default_rng(1)
    x = rng.standard_normal((1, *shape))
    ctx = make_ctx(shape)
    ctx = replace(ctx, grid=replace(ctx.grid, boundary=boundary))
    candidates = [gaussian_filter(x, (0, *(1.5,) * len(shape)), mode="wrap"),
                  x + 0.3 * rng.standard_normal(x.shape),
                  rng.standard_normal(x.shape)]
    for candidate in candidates:
        distance = persistence_distance(x, candidate, ctx=replace(ctx, cache={}))
        assert 0.0 < distance <= max_error(x, candidate) * (1 + 1e-12)


def test_the_first_grid_axis_is_the_first_axis_of_the_complex():
    """A band of zeros down column 0 of a 4 x 4 field of ones, x[0, :, 0] = 0, runs the whole
    length of grid axis 0. On a cylinder that wraps axis 0 the band closes a loop around it at
    threshold 0, so the dimension-1 class that never dies is born at 0: H_1 = [(0, inf)]. On a
    cylinder that wraps axis 1 instead, a loop around axis 1 needs a whole row, which first
    exists at threshold 1: H_1 = [(1, inf)]. The two orders give different diagrams, so this pins
    which axis ``periodic_dimensions`` wraps (the Betti numbers alone, (1, 1, 0) either way,
    cannot)."""
    x = np.ones((1, 4, 4))
    x[0, :, 0] = 0.0
    for boundary, birth in ((("periodic", "neumann"), 0.0), (("neumann", "periodic"), 1.0)):
        ctx = replace(make_ctx((4, 4)), grid=GridSpec((4, 4), (1.0, 1.0), boundary))
        diagram = persistence_diagram(x, ctx=ctx)
        np.testing.assert_array_equal(diagram[diagram[:, 2] == 1, :2], [[birth, np.inf]])


def test_only_the_axes_the_grid_declares_periodic_are_wrapped():
    """The complex of the whole grid is a torus with Betti numbers (1, 2, 1) when both axes
    wrap, a cylinder (1, 1, 0) when one does and a disk (1, 0, 0) when neither does
    (Bleile et al. 2022, Sect. 4.2, for the torus). Read off the diagram above its largest
    value, where only the classes that never die remain."""
    x = synthetic_field((8, 6), 1, seed=2)
    top = [float(x.max()) + 1.0]
    for boundary, betti in ((("periodic", "periodic"), [1, 2, 1]),
                            (("periodic", "neumann"), [1, 1, 0]),
                            (("neumann", "neumann"), [1, 0, 0])):
        ctx = replace(make_ctx((8, 6)), grid=GridSpec((8, 6), (1.0, 1.0), boundary))
        np.testing.assert_array_equal(betti_curves(persistence_diagram(x, ctx=ctx), top, 3)[:, 0],
                                      betti)


def test_a_vector_field_or_a_non_finite_cell_is_refused():
    """A sublevel set needs one finite scalar per cell."""
    with pytest.raises(ValueError, match="one scalar channel"):
        persistence_diagram(np.zeros((2, 4, 4)), ctx=make_ctx((4, 4)))
    field = two_wells()
    field[0, 1, 1] = np.nan
    with pytest.raises(ValueError, match="finite"):
        persistence_distance(two_wells(), field, ctx=make_ctx((4, 4)))
