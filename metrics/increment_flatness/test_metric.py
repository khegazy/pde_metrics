"""Tests for the increment-flatness metric.

The registry-wide contract -- return type, dtype stability, monotonicity under blur --
lives in ``tests/test_metric_contract.py``. What is tested here is what only this metric
claims: the closed-form value for a lone step, the exact 3 for a Gaussian field, and the
per-axis averaging that keeps that 3 exact when the field is anisotropic.

Every expected value is derived in the docstring beside it rather than copied from a run.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter1d

from tests.conftest import alternating_field, step_field

from .metric import increment_flatness


@pytest.mark.parametrize("n", [
    # The worked example in the card: a single step across a periodic 4-cell axis scores 2.
    pytest.param(4, id="card-4"),
    pytest.param(8, id="8"),
    pytest.param(16, id="16"),
    pytest.param(32, id="32"),
])
def test_a_lone_step_scores_half_the_axis_length(n: int):
    """A lone step along a periodic axis of N cells scores N/2.

    The increment field of a lone step is +1 at the rising edge, -1 where the periodic
    wrap closes it, and 0 at the other N - 2 places. So for a length-N axis

        <d^2> = 2/N,    <d^4> = 2/N,    flatness = (2/N) / (2/N)^2 = N/2

    The y axis is constant, so its increments vanish identically and it contributes
    nothing -- the value is the x axis alone.

    This is the metric's mechanism in closed form: the rarer a jump of given size is, the
    higher the flatness, growing without bound as the same jump is spread over more cells.
    """
    assert increment_flatness(step_field((n, 4))) == pytest.approx(n / 2.0)


def test_an_everywhere_alternating_field_scores_one():
    """Increments of constant magnitude give flatness 1, the floor for a symmetric field.

    With d = +/-1 everywhere, <d^4> = <d^2>^2 = 1. Nothing is rare, so nothing is
    intermittent -- the opposite extreme from the lone step above.
    """
    assert increment_flatness(alternating_field()) == pytest.approx(1.0)


def test_a_constant_field_is_nan_rather_than_a_number():
    """A field with no increments has no increment distribution to have a shape.

    Returning 3 would claim Gaussianity and returning 0 would claim an impossible value;
    both would be inventions, so this reports that it cannot say.
    """
    assert np.isnan(increment_flatness(np.full((1, 8, 8), 2.5)))


def test_a_gaussian_field_scores_three():
    """The anchor the whole metric rests on, checked statistically.

    Flatness is a fourth moment and noisy on one realisation, so this averages over seeds
    and asserts on the mean, with a per-seed bound loose enough not to flake but far
    tighter than the departure any real turbulent field shows.
    """
    seeds = range(12)
    values = []
    for seed in seeds:
        noise = np.random.default_rng(seed).standard_normal((1, 64, 64))
        value = increment_flatness(noise)
        values.append(value)
        assert value == pytest.approx(3.0, abs=0.35), f"seed {seed} gave {value}"
    assert float(np.mean(values)) == pytest.approx(3.0, abs=0.06)


def test_anisotropy_does_not_move_the_gaussian_anchor():
    """A Gaussian field with unequal increment variances per axis still scores 3.

    This is why the implementation averages per-axis flatnesses instead of pooling every
    increment into one sample. Smoothing white noise along y alone leaves the field
    Gaussian but gives its y-increments a smaller variance than its x-increments, and a
    mixture of two zero-mean Gaussians with variances in the ratio r is leptokurtic:

        flatness_pooled = 6 (1 + r^2) / (1 + r)^2

    which is 3 only at r = 1. The averaged value stays at 3; the pooled one does not, and
    this test pins both halves so the docstring's reasoning cannot quietly stop being true.
    """
    averaged, pooled = [], []
    for seed in range(8):
        noise = np.random.default_rng(seed).standard_normal((1, 64, 64))
        field = gaussian_filter1d(noise, 2.0, axis=-1, mode="wrap")
        averaged.append(increment_flatness(field))

        dx = np.roll(field, -1, axis=-2) - field
        dy = np.roll(field, -1, axis=-1) - field
        both = np.concatenate([dx.ravel(), dy.ravel()])
        pooled.append(float(np.mean(both**4) / np.mean(both**2) ** 2))

    assert float(np.mean(averaged)) == pytest.approx(3.0, abs=0.1)
    assert float(np.mean(pooled)) > float(np.mean(averaged)) + 0.5, (
        f"pooling was expected to inflate the flatness of an anisotropic Gaussian field, "
        f"but averaged={np.mean(averaged):.3f} and pooled={np.mean(pooled):.3f}"
    )


def test_channels_are_averaged_not_concatenated():
    """Two channels of different amplitude average their flatnesses.

    Same argument as the axis case: concatenating channels of different variance would
    inflate the result, so a two-channel field of a lone step and an alternating pattern
    must score the mean of 2 and 1 rather than anything larger.
    """
    field = np.concatenate([step_field(), 3.0 * alternating_field()])

    assert increment_flatness(field) == pytest.approx(1.5)
