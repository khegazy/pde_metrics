"""CRPS skill score: the climatological reference and the ratio, pinned by hand.

The number is ``1 - crps / UNC``, so the tests pin the one new ingredient, the climatological
score UNC, against a hand count and against a brute-force mean of the empirical
distribution's CRPS over the observations, and then the ratio on the card's worked example.
"""

from __future__ import annotations

import numpy as np
import pytest

from metrics.crps.metric import crps
from metrics.crps_skill_score.metric import crps_skill_score
from tests.conftest import exchangeable_ensemble

#: One channel of two cells, reference 0 and 2; two members per cell.
WORKED_REFERENCE = np.array([[0.0, 2.0]])
WORKED_MEMBERS = np.array([[[1.0, 2.0]], [[1.0, 4.0]]])


def _climatological_crps(reference: np.ndarray) -> float:
    """Brute force: the mean over every observation of the CRPS of the empirical distribution
    of all of them, per channel, averaged over channels. Uses the kernel form E|X - y| -
    E|X - X'|/2 with the expectations taken exactly over the n values."""
    per_channel = []
    for y in reference.reshape(reference.shape[0], -1):
        gaps = np.abs(y[:, None] - y[None, :])
        per_channel.append(np.mean(gaps.mean(axis=0) - 0.5 * gaps.mean()))
    return float(np.mean(per_channel))


def test_worked_example_from_the_card():
    """Climatology of the values 0 and 2: UNC = (|0-2| + |2-0|) / (2 * 2^2) = 0.5.

    Cell 1, members 1 and 1 against 0: CRPS = 1 - 0 = 1. Cell 2, members 2 and 4 against 2:
    the distance term is (0 + 2)/2 = 1 and the fair spread credit (2 + 2)/(2*2*1) = 1, so
    CRPS = 0. The mean CRPS is 0.5, equal to UNC, and the skill score is 1 - 0.5/0.5 = 0: this
    ensemble is exactly as good as climatology.
    """
    assert crps(WORKED_REFERENCE, WORKED_MEMBERS) == pytest.approx(0.5)
    assert crps_skill_score(WORKED_REFERENCE, WORKED_MEMBERS) == pytest.approx(0.0, abs=1e-15)


def test_the_reference_score_is_the_climatological_crps():
    """1 - CRPSS times UNC gives back crps, with UNC the brute-force climatological score."""
    reference, members = exchangeable_ensemble(0, (2, 9, 7), 5)
    uncertainty = _climatological_crps(reference)
    assert crps_skill_score(reference, members) == pytest.approx(
        1.0 - crps(reference, members) / uncertainty, rel=1e-12)


def test_a_perfect_ensemble_scores_one():
    reference = np.arange(12.0).reshape(1, 3, 4)
    assert crps_skill_score(reference, np.repeat(reference[None], 4, axis=0)) == 1.0


def test_an_ensemble_of_the_climatological_values_scores_one_over_n_minus_one():
    """Members equal to all n reference values at every cell. Their fair CRPS averages to
    S/n^2 - S/(2n(n-1)) for S the double sum, against UNC = S/(2n^2), so the skill score is
    1/(n-1), not 0: the fair estimator treats the members as a sample of a wider distribution,
    while the climatological score is that of the n values themselves."""
    reference = np.array([[0.0, 1.0, 3.0, 7.0]])
    n = reference.size
    members = np.broadcast_to(reference.reshape(n, 1, 1), (n, 1, n)).copy()
    assert crps_skill_score(reference, members) == pytest.approx(1.0 / (n - 1), rel=1e-12)


def test_each_channel_has_its_own_climatology():
    """Two channels far apart in value: pooling them into one climatology would widen it and
    inflate the skill. Per channel, offsetting one channel by a constant changes nothing."""
    reference, members = exchangeable_ensemble(1, (2, 8, 8), 6)
    offset = np.array([0.0, 100.0]).reshape(2, 1, 1)
    assert crps_skill_score(reference + offset, members + offset) == pytest.approx(
        crps_skill_score(reference, members), rel=1e-12)


def test_is_undefined_on_a_constant_reference():
    reference = np.ones((1, 4, 4))
    members = np.stack([reference, reference + 1.0])
    assert np.isnan(crps_skill_score(reference, members))
