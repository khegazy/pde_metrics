"""Tests specific to The Well's variance-scaled root mean squared error.

The registry-wide contract is checked in ``tests/test_metric_contract.py``. What is tested here
is what the card claims: the worked example in its Intuition section, The Well's two numerical
conventions (the variance divides by the cell count less one, and 1e-7 is added to it), that
the mean of the reference scores about one, the mean over channels, the asymmetry, the failure
of the triangle inequality, and the uniform reference.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import SQUARE_REFERENCE, SQUARE_SHIFTED, synthetic_field

from .metric import EPSILON, vrmse


def test_worked_example_from_the_card():
    """The moved square: squared error 4/16 = 0.25 over the reference's variance.

    The reference holds four ones and twelve zeros, mean 1/4, so the squared deviations sum to
    4 * (3/4)^2 + 12 * (1/4)^2 = 3, and The Well's variance divides by 16 - 1 = 15: 0.2. The
    value is sqrt(0.25 / (0.2 + 1e-7)) = 1.1180. The population variance, 3/16, would give
    sqrt(4/3) = 1.1547 instead; that difference pins the cell count less one.
    """
    assert vrmse(SQUARE_REFERENCE, SQUARE_SHIFTED) == pytest.approx(
        np.sqrt(0.25 / (0.2 + 1e-7)), rel=1e-12)
    assert not np.isclose(vrmse(SQUARE_REFERENCE, SQUARE_SHIFTED), np.sqrt(4.0 / 3.0))


def test_predicting_the_reference_mean_scores_about_one():
    """The landmark The Well's tables are read against (App. E.3): the field's own mean.

    Its squared error is the population variance, so the value is sqrt((N - 1) / N) below one
    by the cell count, and lower still by the 1e-7. On a 16 x 8 field of variance order one
    that is 0.99609.
    """
    reference = synthetic_field((16, 8), 1, seed=3)
    mean = np.full_like(reference, reference.mean())
    n = reference.size
    expected = np.sqrt(reference.var() / (reference.var(ddof=1) + EPSILON))
    assert vrmse(reference, mean) == pytest.approx(expected, rel=1e-12)
    assert expected == pytest.approx(np.sqrt((n - 1) / n), rel=1e-6)


def test_epsilon_dominates_a_reference_of_tiny_variance():
    """The 1e-7 is in the square of the field's units, so it is not scale-free.

    A reference whose fluctuation has variance far below 1e-7 is divided by sqrt(1e-7), not by
    its own spread: The Well's behaviour, which the card states for this repository's density.
    """
    reference = 1.0 + 1e-6 * SQUARE_REFERENCE
    candidate = 1.0 + 1e-6 * SQUARE_SHIFTED
    rmse = 1e-6 * 0.5
    assert vrmse(reference, candidate) == pytest.approx(
        rmse / np.sqrt(1e-6 ** 2 * 0.2 + EPSILON), rel=1e-6)
    assert vrmse(reference, candidate) < 0.01


def test_a_uniform_reference_gives_a_finite_value():
    """No NaN: a constant channel has variance zero, and the 1e-7 is all that divides."""
    uniform = np.ones((1, 4, 4))
    candidate = uniform.copy()
    candidate[0, 0, 0] = 2.0
    assert vrmse(uniform, candidate) == pytest.approx(np.sqrt(1.0 / 16.0 / EPSILON), rel=1e-12)


def test_channels_are_scaled_separately_and_then_averaged():
    """The first channel is the moved square, 1.1180; the second, a copy scaled by 100 and
    predicted exactly, scores 0. The mean of the two is The Well's average over fields."""
    reference = np.concatenate([SQUARE_REFERENCE, 100.0 * SQUARE_REFERENCE])
    candidate = np.concatenate([SQUARE_SHIFTED, 100.0 * SQUARE_REFERENCE])
    assert vrmse(reference, candidate) == pytest.approx(
        np.sqrt(0.25 / (0.2 + 1e-7)) / 2.0, rel=1e-12)


def test_adding_a_constant_to_both_fields_leaves_it_unchanged():
    """The mean is removed from the denominator, so a background of 1000 changes nothing."""
    reference = synthetic_field((16, 8), 2, seed=1)
    candidate = synthetic_field((16, 8), 2, seed=2)
    assert vrmse(reference + 1000.0, candidate + 1000.0) == pytest.approx(
        vrmse(reference, candidate), rel=1e-9)


def test_it_is_not_symmetric():
    """The reference sets the scale: halving its amplitude quarters its variance."""
    damped = SQUARE_REFERENCE * 0.5
    assert not np.isclose(vrmse(SQUARE_REFERENCE, damped), vrmse(damped, SQUARE_REFERENCE))
    assert vrmse(SQUARE_REFERENCE, damped) < vrmse(damped, SQUARE_REFERENCE)


def test_it_breaks_the_triangle_inequality():
    """Each term is divided by its own first argument's spread, so the inequality can fail.

    With f the square, g twice it and h three times it, d(f, h) is about 1 / 0.447 = 2.236,
    while d(f, g) + d(g, h) is about 0.5 / 0.447 + 0.5 / 0.894 = 1.677.
    """
    f, g, h = SQUARE_REFERENCE, 2.0 * SQUARE_REFERENCE, 3.0 * SQUARE_REFERENCE
    assert vrmse(f, h) > vrmse(f, g) + vrmse(g, h)


def test_mismatched_shapes_are_refused_even_when_they_broadcast():
    with pytest.raises(ValueError, match="matching shapes"):
        vrmse(np.ones((1, 4, 2)), np.zeros((2, 4, 2)))
