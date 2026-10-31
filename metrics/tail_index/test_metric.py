"""Tests for ``tail_index``: the worked example, the power-law case, the invariances and NaN.

The contract tests in ``tests/test_metric_contract.py`` already check one finite float, dtype
stability, the declared non-monotonicity under blur, a fixed curve coordinate and the same number
from the cached curve, so none of that is repeated here.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from .metric import REGISTERED_THETA, THETAS, orders, tail_index, tail_index_curve

#: The card's worked example: a sawtooth down the rows, constant along each row.
SAWTOOTH = np.array([[[0.0, 0.0, 0.0, 0.0],
                      [3.0, 3.0, 3.0, 3.0],
                      [2.0, 2.0, 2.0, 2.0],
                      [1.0, 1.0, 1.0, 1.0]]])
#: The card's second example: rows alternating 0 and 1, so every increment has size 1.
ALTERNATING = np.array([[[0.0, 0.0, 0.0, 0.0],
                         [1.0, 1.0, 1.0, 1.0],
                         [0.0, 0.0, 0.0, 0.0],
                         [1.0, 1.0, 1.0, 1.0]]])


def test_worked_example_matches_the_card():
    """The sawtooth scores ln 3 = 1.0986; the alternating field scores 0.

    Sawtooth, by hand. Down each column the values are 0, 3, 2, 1 and wrap back to 0, so the
    increments are +3, -1, -1, -1 and their sizes 3, 1, 1, 1; the four columns give sixteen
    sizes, four of 3 and twelve of 1. n = 16 cells, so k = ceil(sqrt(16)) = 4: the four largest
    sizes are the four 3s and the fifth largest is 1, and the Hill estimate is
    (1/4)(4 ln 3) - ln 1 = ln 3 = 1.0986. Along each row the field is constant, so the fifth
    largest size there is 0, that axis has no estimate and is left out of the mean.

    Alternating, by hand. Every increment down a column has size 1, so the four largest and the
    fifth largest are all 1 and the estimate is ln 1 = 0.
    """
    assert tail_index(SAWTOOTH) == pytest.approx(1.0986, abs=5e-5)
    assert tail_index(SAWTOOTH) == pytest.approx(math.log(3.0), rel=1e-12)
    assert tail_index(ALTERNATING) == 0.0


def test_distinct_increments_pin_the_order_statistics():
    """A one-dimensional field 0, 1, 3, 7, 15 scores ln(60)/3 = 1.364782.

    By hand. With the wrap from 15 back to 0 the increments are +1, +2, +4, +8, -15, so the sizes
    in decreasing order are 15, 8, 4, 2, 1. n = 5, so k = ceil(sqrt(5)) = 3 and the threshold is
    the fourth largest, 2: (1/3)(ln 15 + ln 8 + ln 4) - ln 2 = (1/3) ln(480 / 8) = ln(60)/3.
    Every size is distinct, so taking X_(k) for X_(k+1), summing k + 1 terms or dividing by k - 1
    each gives a different number, which the tied sawtooth example cannot guarantee.
    """
    assert tail_index(np.array([[0.0, 1.0, 3.0, 7.0, 15.0]])) == pytest.approx(1.364782, abs=5e-7)


def test_orders_are_exact_at_exact_roots():
    """On n = 1024 cells, k = ceil(1024 ** (j/10)) = 2 ** j exactly, for j = 1, ..., 9.

    1024 = 2 ** 10, so 1024 ** (j/10) = 2 ** j, an integer, and its ceiling is itself:
    2, 4, 8, 16, 32, 64, 128, 256, 512 (all below the cap n - 1 = 1023). A floating-point power
    gives 1024 ** 0.4 = 16.000000000000004 and a ceiling of 17. On the 256 x 256 grid,
    n = 65536 = 2 ** 16 and theta = 1/2 gives 2 ** 8 = 256.
    """
    assert orders(1024).tolist() == [2, 4, 8, 16, 32, 64, 128, 256, 512]
    assert orders(65536)[list(THETAS).index(REGISTERED_THETA)] == 256


def test_a_non_finite_field_is_refused():
    """A NaN or an infinity would otherwise make its pair's estimate NaN, and the pair would drop
    out of the mean silently, leaving the other channel's value as the answer."""
    x = np.random.default_rng(2).standard_normal((2, 16, 8))
    for bad in (np.nan, np.inf):
        y = x.copy()
        y[0, 3, 3] = bad
        with pytest.raises(ValueError, match="finite"):
            tail_index(y)


def test_spatial_clustering_lowers_the_estimate_of_a_power_law_field():
    """Blurring an independent Pareto field (alpha = 1) lowers the estimate, though the tail is the
    same power law: the k largest increments then sit side by side around a few large values.

    Measured on 128 x 64, eight seeds: the unblurred mean is 1.039, and a Gaussian blur of 2 cells
    lowers every seed's value, to a mean of 0.481. So a low value on a spatially correlated field
    does not by itself mean a light tail; the card's Limitations say so.
    """
    raw, blurred = [], []
    for seed in range(8):
        x = np.random.default_rng(seed).pareto(1.0, (1, 128, 64)) + 1.0
        raw.append(tail_index(x))
        blurred.append(tail_index(gaussian_filter(x, (0, 2, 2), mode="wrap")))
    assert all(b < r for r, b in zip(raw, blurred)), (raw, blurred)
    assert np.mean(raw) == pytest.approx(1.0, abs=0.1)
    assert np.mean(blurred) < 0.7, blurred


@pytest.mark.xfail(strict=True, reason="issues/103: an axis is left out only when exactly "
                   "constant, so round-off on it enters the mean at full weight")
def test_round_off_on_a_constant_axis_does_not_change_the_value():
    """A 64 x 32 field varying only along x, and the same field plus noise of size 1e-12.

    Measured: 0.0937 exactly constant along y, 0.1215 with the perturbation, because the y pair
    is then pure round-off and its scale-free estimate counts as much as the x pair's.
    """
    profile = (np.sin(2 * np.pi * np.arange(64) / 64)
               + 0.05 * np.random.default_rng(0).standard_normal(64))
    x = np.broadcast_to(profile[:, None], (64, 32))[None].copy()
    perturbed = x + 1e-12 * np.random.default_rng(1).standard_normal(x.shape)
    assert tail_index(perturbed) == pytest.approx(tail_index(x), rel=1e-6)


def test_the_registered_number_is_the_curve_at_theta_one_half():
    """The metric is one point of its companion, at k = ceil(n ** 0.5)."""
    x = np.random.default_rng(0).standard_normal((2, 16, 8))
    thetas, values = tail_index_curve(x)
    assert np.array_equal(thetas, THETAS)
    assert tail_index(x) == values[list(thetas).index(REGISTERED_THETA)]


@pytest.mark.parametrize("alpha", [1.0, 2.0])
def test_estimates_the_inverse_power_of_a_power_law_tail(alpha: float):
    """On a field of independent Pareto values with P(X > x) = x^-alpha, the estimate is 1/alpha.

    Boucheron & Thomas (2015), Electron. J. Stat. 9(2), 2751-2792, Sect. 1: for a tail in the
    max-domain of attraction with index gamma > 0 the Hill estimator converges to gamma as
    k -> infinity with k/n -> 0. The increment of two independent Pareto values has the same
    power-law tail. Measured over 16 seeds on 128 x 64 (k = 91 of 8192): mean 1.003 for
    alpha = 1 and 0.545 for alpha = 2, so the mean is asserted within 0.1 of 1/alpha.
    """
    values = [tail_index(np.random.default_rng(seed).pareto(alpha, (1, 128, 64)) + 1.0)
              for seed in range(16)]
    assert np.mean(values) == pytest.approx(1.0 / alpha, abs=0.1), values


def test_a_heavier_tail_scores_higher():
    """Pareto alpha = 1 above Pareto alpha = 2 above a Gaussian field, on every one of 8 seeds."""
    for seed in range(8):
        rng = np.random.default_rng(seed)
        heavy, medium = (tail_index(rng.pareto(a, (1, 128, 64)) + 1.0) for a in (1.0, 2.0))
        gaussian = tail_index(rng.standard_normal((1, 128, 64)))
        assert heavy > medium > gaussian, (seed, heavy, medium, gaussian)


def test_invariant_to_scale_offset_and_periodic_shift():
    """Hill's estimator uses ratios of increments: scaling, adding a constant and an integer
    periodic shift leave every ratio, and so the value, unchanged."""
    x = np.random.default_rng(1).standard_normal((1, 16, 8))
    base = tail_index(x)
    assert tail_index(7.5 * x) == pytest.approx(base, rel=1e-12)
    assert tail_index(x + 3.0) == pytest.approx(base, rel=1e-12)
    assert tail_index(np.roll(x, 5, axis=-2)) == pytest.approx(base, rel=1e-12)


def test_a_constant_field_is_nan():
    """No increment is positive, so no k has a positive (k+1)-th largest: NaN, as
    increment_flatness is on a constant field."""
    assert math.isnan(tail_index(np.full((1, 16, 8), 2.0)))


def test_a_single_cell_is_refused():
    with pytest.raises(ValueError, match="at least two cells"):
        tail_index_curve(np.ones((1, 1, 1)))
