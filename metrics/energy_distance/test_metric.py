"""Tests for the energy distance between increment distributions.

The registry-wide contract -- symmetry, zero on identical fields, shape rejection, dtype
stability, monotonicity under blur -- lives in ``tests/test_metric_contract.py``. What is
tested here is the worked example printed in the card, the contrast with ``increment_w1`` that
the card's Limitations section states, and the invariances and scaling the card claims.

Every expected value is derived in the docstring beside it rather than copied from a run. The
derivations use the one-dimensional form of the squared energy distance, twice the integral of
the squared difference of the two cumulative distribution functions (Székely & Rizzo 2013,
J. Stat. Plann. Inference 143(8), 1249-1272, the display immediately before Eq. (2.3)); the
energy distance is its square root (Rizzo & Székely 2016, WIREs Comput. Stat. 8(1), p. 27).
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from metrics.increment_w1.metric import increment_w1
from tests.conftest import alternating_field, step_field

from .metric import energy_distance


def test_worked_example_from_the_card():
    """The 4x4 pair in the card's Intuition section scores 0.25.

    Down each column the reference increments are ``+1, 0, 0, -1`` and the candidate's are
    ``+1, -1, +1, -1``. Pooled over the four columns, the reference's sample is four ``-1``,
    eight ``0`` and four ``+1``, so its cumulative distribution is 1/4 on [-1, 0), 3/4 on
    [0, 1) and 1 from 1 on; the candidate's is eight ``-1`` and eight ``+1``, so its
    cumulative distribution is 1/2 on [-1, 1). The two differ by 1/4 on each of the two unit
    intervals, so the squared gap integrates to 2 * (1/4)^2 = 1/8 and the squared energy
    distance along x is 2 * 1/8 = 1/4. The same from the mean distances of Székely & Rizzo
    (2013), Eq. (2.4): the mean cross distance is 1, the candidate's mean within-sample
    distance is 1 and the reference's is 3/4, so 2 * 1 - 3/4 - 1 = 1/4. Its square root is
    0.5.

    Across each row both fields are constant, both samples are all zeros and that axis
    contributes 0. The reported value averages the two axes: (0.5 + 0) / 2 = 0.25.
    """
    assert energy_distance(step_field(), alternating_field()) == pytest.approx(0.25)


def test_a_rare_extreme_increment_costs_less_than_a_broad_change_of_equal_transport_cost():
    """Two candidates both at increment_w1 = 0.5 score 0.5 and sqrt(1/8)/2 = 0.1768.

    Every column of the 16x4 reference alternates 0, 1, 0, 1, ..., so its 16 increments along
    x are eight +1 and eight -1. Candidate A alternates 0, 2: eight +2 and eight -2, every
    atom moved by 1, a transport distance of 1 along x. Candidate B keeps the reference but
    raises one cell per column from 1 to 9: two of the 16 increments become +9 and -9, each
    moved by 8, a transport distance of 2 * 8 / 16 = 1 along x. Along y all three fields are
    constant, so with the average over the two axes both candidates score 0.5 in
    increment_w1.

    For A the two cumulative functions differ by 1/2 on [-2, -1) and on [1, 2), so the
    squared energy distance along x is 2 * 2 * (1/2)^2 = 1 and its root is 1, averaging to
    0.5. For B they differ by 1/16 on [-9, -1) and on [1, 9), a total length of 16, so the
    squared distance is 2 * 16 * (1/16)^2 = 1/8, its root sqrt(1/8) = 0.35355, averaging to
    0.17678. For the tail change the squared distance over the transport distance is
    2/N = 1/8 for N = 16 increments, whatever the size of the move. For this two-valued
    reference the broad change happens to have the ratio 1 (gap 1/2 over a length of 2 * 1);
    that is a property of the example, not of broad changes in general, which the next test
    shows are suppressed too.
    """
    reference = np.tile(np.array([0.0, 1.0] * 8)[None, :, None], (1, 1, 4))
    broad = 2.0 * reference
    rare = reference.copy()
    rare[0, 1, :] = 9.0
    assert increment_w1(reference, broad) == pytest.approx(0.5)
    assert increment_w1(reference, rare) == pytest.approx(0.5)
    assert energy_distance(reference, broad) == pytest.approx(0.5)
    assert energy_distance(reference, rare) == pytest.approx(np.sqrt(1 / 8) / 2)


def test_on_a_gaussian_bulk_a_tail_change_costs_4_sqrt2_over_n_eps_of_an_equal_cost_stretch():
    """At equal transport cost, D^2 charges the tail change 4 sqrt(2)/(N eps) of a stretch.

    The reference's N = 1024 increments along x are the centred Gaussian quantiles
    Phi^-1((i + 1/2)/N), in a fixed random order; the field is their running sum down a column,
    copied into two identical columns, so along y every increment is 0 and the registered
    value is half the x-axis distance.

    Broad change: every increment stretched by 1 + eps, eps = 0.05. The cumulative function
    moves by about eps x f(x), so D^2 = 2 eps^2 integral x^2 f^2 dx = 2 eps^2 / (4 sqrt(pi)),
    while W1 = eps E|X| = eps sqrt(2/pi); hence D^2 / W1 = eps / (2 sqrt 2) = 0.017678 (this
    uses integral x^2 phi(x)^2 dx = 1 / (4 sqrt(pi)) and E|X| = sqrt(2/pi) for the unit
    Gaussian). The derivation is the agent's own, the small-eps limit of Eq. (3) of the card.

    Tail change of the same transport cost: the largest and smallest increments moved outward
    by h = N W1 / 2, so W1 = 2h/N is equal and D^2 = 4h/N^2, D^2 / W1 = 2/N. The ratio of the
    two squared distances is (2/N) / (eps / (2 sqrt 2)) = 4 sqrt(2) / (1024 * 0.05) = 0.11049.

    Both are first-order approximations in eps and the quantiles are discrete, so the
    tolerance is 5%; measured 0.01731 and 0.1128. A statement that the tail change costs only
    2/N = 0.00195 of a broad change would fail here by a factor of about 57.
    """
    n, eps = 1024, 0.05
    quantiles = stats.norm.ppf((np.arange(n) + 0.5) / n)
    order = np.random.default_rng(0).permutation(quantiles - quantiles.mean())

    def field(increments_x):
        column = np.concatenate([[0.0], np.cumsum(increments_x)[:-1]])
        return np.tile(column[None, :, None], (1, 1, 2))

    reference, broad = field(order), field((1 + eps) * order)
    w1_broad = 2 * increment_w1(reference, broad)
    tail = order.copy()
    tail[np.argmax(order)] += n * w1_broad / 2
    tail[np.argmin(order)] -= n * w1_broad / 2
    rare = field(tail)
    d2_broad = (2 * energy_distance(reference, broad)) ** 2
    d2_rare = (2 * energy_distance(reference, rare)) ** 2
    assert 2 * increment_w1(reference, rare) == pytest.approx(w1_broad)
    assert d2_broad / w1_broad == pytest.approx(0.017678, rel=0.05)
    assert d2_rare / d2_broad == pytest.approx(0.11049, rel=0.05)


def test_translation_and_a_constant_offset_are_invisible():
    """Rolling the field permutes its increments; adding a constant cancels in each one.

    Either way the two increment samples are the same multiset, so their empirical
    distributions coincide and the energy distance is zero.
    """
    rng = np.random.default_rng(0)
    field = rng.standard_normal((1, 16, 8))
    for axis in (-2, -1):
        assert energy_distance(field, np.roll(field, 3, axis=axis)) == 0.0
    assert energy_distance(field, field + 12.5) == pytest.approx(0.0, abs=1e-6)


def test_scaling_both_fields_scales_the_distance_by_the_root_of_the_factor():
    """Multiplying both fields by c multiplies the energy distance by sqrt(|c|).

    Every term of the squared distance is a mean of |x - y|, homogeneous of degree one, so
    D^2(cX, cY) = |c| D^2(X, Y) and D scales by sqrt(|c|): with c = -4 the value doubles.
    This is why the value is in the square root of the field's units.
    """
    rng = np.random.default_rng(1)
    a, b = rng.standard_normal((2, 2, 16, 8))
    assert energy_distance(-4.0 * a, -4.0 * b) == pytest.approx(2.0 * energy_distance(a, b))
