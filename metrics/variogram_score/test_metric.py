"""Variogram score: the worked example, the pair sum, its blindness to a common offset, and
its dependence on ensemble size.

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


def test_worked_example_from_the_card():
    """Reference (0, 4, 0) against members (0, 1, 0) and (0, 0, 0), unit spacing.

    Square roots of the reference's differences: neighbours 2 and 2, ends 0. Member one gives
    1, 1 and 0, member two 0, 0 and 0, so the ensemble means are 0.5, 0.5 and 0. Each
    neighbouring pair, at distance 1, contributes (2 - 0.5)^2 = 2.25; the end pair, at
    distance 2, contributes 0. Equation 3 sums ordered pairs, so the score is
    2 * (2.25 + 2.25) = 9.
    """
    ctx = make_ctx(REFERENCE.shape[1:])
    assert variogram_score(REFERENCE, MEMBERS, ctx=ctx) == pytest.approx(9.0, rel=1e-12)


def test_the_map_charges_each_cell_its_pairs():
    """Each end cell belongs to one mismatched pair, 2.25; the middle cell to two, 4.5."""
    ctx = make_ctx(REFERENCE.shape[1:])
    np.testing.assert_allclose(
        variogram_score_map(REFERENCE, MEMBERS, ctx=ctx), [[2.25], [4.5], [2.25]], rtol=1e-12
    )


def test_matches_the_double_sum_over_every_ordered_pair():
    """Equation 3 of Scheuerer & Hamill (2015, MWR 143(4)) written as the literal double sum.

    The metric visits each displacement once; this visits each ordered pair of cells, on a
    non-square grid with unequal spacing so a transposed axis or a dropped spacing fails.
    """
    rng = np.random.default_rng(2)
    shape = (5, 3)
    reference = rng.standard_normal((2, *shape))
    members = rng.standard_normal((4, 2, *shape))
    ctx = make_ctx(shape)
    ctx = dataclasses.replace(ctx, grid=dataclasses.replace(ctx.grid, spacing=(0.5, 2.0)))
    cells = list(itertools.product(range(shape[0]), range(shape[1])))
    total = 0.0
    for c in range(2):
        for a, b in itertools.product(cells, cells):
            if a == b:
                continue
            r = np.hypot(0.5 * (a[0] - b[0]), 2.0 * (a[1] - b[1]))
            observed = abs(reference[c][a] - reference[c][b]) ** 0.5
            forecast = np.mean([abs(m[c][a] - m[c][b]) ** 0.5 for m in members])
            total += (observed - forecast) ** 2 / r
    assert variogram_score(reference, members, ctx=ctx) == pytest.approx(total, rel=1e-12)


def test_blind_to_an_offset_common_to_every_cell():
    """Every term depends on differences only (Scheuerer & Hamill 2015, Sect. 2)."""
    truth, members = exchangeable_ensemble(1, (1, 8, 8), 6)
    ctx = make_ctx((8, 8))
    assert variogram_score(truth, members + 3.0, ctx=ctx) == pytest.approx(
        variogram_score(truth, members, ctx=ctx), rel=1e-12
    )


def test_penalises_strong_over_and_under_dispersion():
    """A calibrated ensemble beats one three times wider and one five times narrower."""
    truth, members = exchangeable_ensemble(5, (1, 12, 12), 32)
    ctx = make_ctx((12, 12))
    calibrated = variogram_score(truth, members, ctx=ctx)
    assert variogram_score(truth, scale_spread(members, 3.0), ctx=ctx) > calibrated
    assert variogram_score(truth, scale_spread(members, 0.2), ctx=ctx) > calibrated


def test_a_calibrated_ensemble_scores_better_with_more_members():
    """The ensemble estimate of Eq. 4 is squared in Eq. 3, so the score is not fair.

    Squaring the mean of M draws adds the draws' variance over M to each term in expectation,
    so the same calibrated process scores higher with four members than with sixteen. Measured
    here over 60 draws of a 12 by 12 field: about 1139 against 971, a gap of about twelve
    standard errors; Scheuerer & Hamill (2015, Sect. 3a) report VS values improving with
    ensemble size.
    """
    ctx = make_ctx((12, 12))
    means = []
    for n_members in (4, 16):
        draws = [exchangeable_ensemble(seed, (1, 12, 12), n_members) for seed in range(60)]
        means.append(np.mean([variogram_score(t, m, ctx=ctx) for t, m in draws]))
    assert means[0] > means[1], means
