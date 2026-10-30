"""Tests for ``tail_index``: the worked example, the power-law case, the invariances and NaN.

The contract tests in ``tests/test_metric_contract.py`` already check one finite float, dtype
stability, the declared non-monotonicity under blur, a fixed curve coordinate and the same number
from the cached curve, so none of that is repeated here.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from .metric import REGISTERED_THETA, THETAS, tail_index, tail_index_curve

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
