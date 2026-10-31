"""Variogram score: the worked example, the pair sum on bounded and periodic axes, its
invariances, and the fair estimator.

The contract tests already check that a perfect ensemble scores zero, that the per-cell map
sums to the score, and the member-axis validation.
"""

from __future__ import annotations

import dataclasses
import itertools

import numpy as np
import pytest

from degradations._shared.ensemble import scale_spread
from metrics.variogram_score.metric import variogram_score, variogram_score_map
from tests.conftest import exchangeable_ensemble, make_ctx

# The worked example of the card: one channel, three cells in a row, two members.
REFERENCE = np.array([[[0.0], [4.0], [0.0]]])
MEMBERS = np.array([[[[0.0], [1.0], [0.0]]], [[[0.0], [0.0], [0.0]]]])


def _ctx(shape: tuple[int, ...], spacing: tuple[float, ...], boundary: str):
    """A context on ``shape`` with per-axis ``spacing`` and one boundary type on every axis."""
    ctx = make_ctx(shape)
    grid = dataclasses.replace(ctx.grid, spacing=spacing, boundary=(boundary,) * len(shape))
    return dataclasses.replace(ctx, grid=grid)


def _double_sum(reference, members, spacing, periodic):
    """Equation 3 of Scheuerer & Hamill (2015, MWR 143(4)) as a literal loop over ordered pairs.

    The forecast term is the fair kernel-score estimate: the members' mean of |x_i - x_j|^p
    against the reference's, squared, minus the members' sample variance over M (Allen,
    Ginsbourger & Ziegel 2023, Sect. 4.1, the variogram score as a kernel score; the unbiased
    kernel-score estimate of Pacchiardi et al. 2024, App. C.1.2). On a periodic axis the
    separation is the shorter way round.
    """
    shape = reference.shape[1:]
    cells = list(itertools.product(*(range(n) for n in shape)))
    total = 0.0
    for c in range(reference.shape[0]):
        for a, b in itertools.product(cells, cells):
            if a == b:
                continue
            gaps = [abs(i - j) for i, j in zip(a, b)]
            gaps = [min(g, n - g) if periodic else g for g, n in zip(gaps, shape)]
            r = np.sqrt(sum((g * h) ** 2 for g, h in zip(gaps, spacing)))
            observed = abs(reference[c][a] - reference[c][b]) ** 0.5
            forecast = np.array([abs(m[c][a] - m[c][b]) ** 0.5 for m in members])
            mismatch = (observed - forecast.mean()) ** 2 - forecast.var(ddof=1) / len(forecast)
            total += mismatch / r
    return total


def test_worked_example_from_the_card():
    """Reference (0, 4, 0) against members (0, 1, 0) and (0, 0, 0), unit spacing.

    Square roots of the reference's differences: neighbours 2 and 2, ends 0. Member one gives
    1, 1 and 0, member two 0, 0 and 0. For each neighbouring pair the members average 0.5,
    so the squared mismatch is (2 - 0.5)^2 = 2.25; their sample variance is 0.5, and the fair
    correction subtracts 0.5 / M = 0.25, leaving 2. The end pair matches exactly and costs 0.
    Every pair is at distance 1 (the grid is periodic, so the ends are neighbours too).
    Equation 3 sums ordered pairs, so the score is 2 * (2 + 2) = 8.
    """
    ctx = make_ctx(REFERENCE.shape[1:])
    assert variogram_score(REFERENCE, MEMBERS, ctx=ctx) == pytest.approx(8.0, rel=1e-12)


def test_the_map_charges_each_cell_its_pairs():
    """Each ordered pair is charged to its first cell: the ends belong to one mismatched pair
    each, 2; the middle cell to two, 4."""
    ctx = make_ctx(REFERENCE.shape[1:])
    np.testing.assert_allclose(
        variogram_score_map(REFERENCE, MEMBERS, ctx=ctx), [[2.0], [4.0], [2.0]], rtol=1e-12
    )


@pytest.mark.parametrize("boundary", ["neumann", "periodic"])
def test_matches_the_double_sum_over_every_ordered_pair(boundary):
    """The displacement loop against the literal double sum, on bounded and periodic axes.

    A non-square grid with unequal spacing, so a transposed axis or a dropped spacing fails; on
    the periodic grid every separation is the shorter way round.
    """
    rng = np.random.default_rng(2)
    shape, spacing = (5, 4), (0.5, 2.0)
    reference = rng.standard_normal((2, *shape))
    members = rng.standard_normal((4, 2, *shape))
    ctx = _ctx(shape, spacing, boundary)
    expected = _double_sum(reference, members, spacing, periodic=boundary == "periodic")
    assert variogram_score(reference, members, ctx=ctx) == pytest.approx(expected, rel=1e-12)


def test_a_periodic_grid_has_no_preferred_origin():
    """Shifting reference and members together round a periodic grid leaves the score fixed.

    On a torus every cell has the same neighbours, so a cyclic shift is a relabelling of the
    cells. Straight-line distances across the unwrapped array would break this, treating cells
    one spacing apart across the boundary as a domain width apart.
    """
    truth, members = exchangeable_ensemble(3, (1, 9, 6), 5)
    ctx = make_ctx((9, 6))
    shifted = variogram_score(
        np.roll(truth, (4, 2), axis=(1, 2)), np.roll(members, (4, 2), axis=(2, 3)), ctx=ctx
    )
    assert shifted == pytest.approx(variogram_score(truth, members, ctx=ctx), rel=1e-12)


def test_blind_to_an_offset_common_to_every_cell():
    """Every term depends on differences only (Scheuerer & Hamill 2015, Sect. 2)."""
    truth, members = exchangeable_ensemble(1, (1, 8, 8), 6)
    ctx = make_ctx((8, 8))
    assert variogram_score(truth, members + 3.0, ctx=ctx) == pytest.approx(
        variogram_score(truth, members, ctx=ctx), rel=1e-12
    )


def test_blind_to_a_sign_flip_of_the_members():
    """|(-a) - (-b)| = |a - b|: a mirrored ensemble scores the same (Pacchiardi et al. 2024,
    JMLR 25(45), Sect. 3.2.1, below Eq. 11)."""
    truth, members = exchangeable_ensemble(4, (1, 8, 8), 6)
    ctx = make_ctx((8, 8))
    assert variogram_score(truth, -members, ctx=ctx) == pytest.approx(
        variogram_score(truth, members, ctx=ctx), rel=1e-12
    )


def test_penalises_strong_over_and_under_dispersion():
    """A calibrated ensemble beats one three times wider and one five times narrower."""
    truth, members = exchangeable_ensemble(5, (1, 12, 12), 32)
    ctx = make_ctx((12, 12))
    calibrated = variogram_score(truth, members, ctx=ctx)
    assert variogram_score(truth, scale_spread(members, 3.0), ctx=ctx) > calibrated
    assert variogram_score(truth, scale_spread(members, 0.2), ctx=ctx) > calibrated


def _calibrated_and_narrowed(n_members: int, factor: float, draws: int, n: int = 10):
    """Paired scores of a calibrated ensemble and one narrowed by ``factor`` about the true base.

    The reference is base + N(0, 1) and the members base + factor * N(0, 1), so ``factor`` = 1
    is calibrated. Scaling about the true base rather than the sample mean keeps the sample
    mean's own error out of the comparison.
    """
    ctx = make_ctx((n, n))
    pairs = []
    for seed in range(draws):
        rng = np.random.default_rng(seed)
        base = rng.standard_normal((1, n, n))
        truth = base + rng.standard_normal((1, n, n))
        noise = rng.standard_normal((n_members, 1, n, n))
        pairs.append((variogram_score(truth, base[None] + noise, ctx=ctx),
                      variogram_score(truth, base[None] + factor * noise, ctx=ctx)))
    return np.array(pairs)


def test_a_narrowed_two_member_ensemble_does_not_beat_the_calibrated_one():
    """Fairness at the smallest ensemble, where the plug-in estimate fails worst.

    With the plug-in estimate of Scheuerer & Hamill's Eq. 4 the squared mean carries an extra
    Var(|X_i - X_j|^p) / M per term, which shrinks as the ensemble narrows: at two members a
    20% narrower ensemble scored better than the calibrated one by about 49 standard errors in
    the adversarial review. The fair estimate removes that term, so narrowing must cost.
    """
    scores = _calibrated_and_narrowed(n_members=2, factor=0.8, draws=200)
    difference = scores[:, 1] - scores[:, 0]
    standard_error = difference.std(ddof=1) / np.sqrt(len(difference))
    assert difference.mean() > 3 * standard_error, (difference.mean(), standard_error)


def test_a_calibrated_ensemble_scores_the_same_at_any_size_from_two():
    """The fair estimate's expectation does not depend on the number of members.

    The plug-in estimate scored a calibrated process about 1139 at four members against 971 at
    sixteen on these draws, twelve standard errors apart. Here the two means must agree within
    four combined standard errors.
    """
    ctx = make_ctx((12, 12))
    means, errors = [], []
    for n_members in (4, 16):
        draws = [exchangeable_ensemble(seed, (1, 12, 12), n_members) for seed in range(60)]
        values = np.array([variogram_score(t, m, ctx=ctx) for t, m in draws])
        means.append(values.mean())
        errors.append(values.std(ddof=1) / np.sqrt(len(values)))
    assert abs(means[0] - means[1]) < 4 * np.hypot(*errors), (means, errors)
