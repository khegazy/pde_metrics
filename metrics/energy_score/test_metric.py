"""Energy score: the worked example, the reduction to CRPS, and the fair estimator.

The contract tests in ``tests/test_metric_contract.py`` already check that a perfect ensemble
scores zero, that the member axis is validated, and that a blurred ensemble ranks; these test
what is specific to the energy score.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.special import gamma

from degradations._shared.ensemble import scale_spread
from metrics.crps.metric import crps
from metrics.energy_score.metric import energy_score
from tests.conftest import exchangeable_ensemble

# The worked example of the card: one channel, two cells, two members.
REFERENCE = np.array([[0.0, 0.0]])
MEMBERS = np.array([[[3.0, 4.0]], [[0.0, 4.0]]])


def test_worked_example_from_the_card():
    """A two-cell reference (0, 0) against members (3, 4) and (0, 4).

    The members lie at distances 5 and 4 from the reference, so the first term is
    (5 + 4) / 2 = 4.5. The members are 3 apart; the pair term sums the two ordered pairs,
    3 + 3 = 6, and divides by 2M(M-1) = 4, giving 1.5. The score is 4.5 - 1.5 = 3.
    """
    assert energy_score(REFERENCE, MEMBERS) == pytest.approx(3.0, rel=1e-12)


def test_the_worked_example_is_not_the_mean_crps():
    """Cell by cell the same ensemble scores a mean CRPS of 2, not 3.

    Cell one: members 3 and 0 against 0 give (3 + 0)/2 - (3 + 3)/4 = 0. Cell two: members 4
    and 4 against 0 give 4 - 0 = 4. The mean is 2. The energy score differs because it
    measures each member's distance over the whole field before averaging.
    """
    assert crps(REFERENCE, MEMBERS) == pytest.approx(2.0, rel=1e-12)
    assert energy_score(REFERENCE, MEMBERS) != pytest.approx(crps(REFERENCE, MEMBERS))


def test_one_cell_is_the_crps():
    """With one value per field the norm is an absolute value and the score is the CRPS.

    Gneiting & Raftery (2007, JASA 102(477), Section 4.3): Eq. 22 reduces to the CRPS
    (Eq. 21) when beta = 1 and the dimension is one; both estimators are the fair one.
    """
    rng = np.random.default_rng(4)
    reference = rng.standard_normal((1, 1))
    members = rng.standard_normal((7, 1, 1))
    assert energy_score(reference, members) == pytest.approx(crps(reference, members), rel=1e-12)


def test_one_member_is_the_euclidean_distance():
    """At M = 1 the pair term is empty and the score is the L2 norm of the difference."""
    rng = np.random.default_rng(5)
    reference = rng.standard_normal((2, 6, 4))
    member = rng.standard_normal((2, 6, 4))
    assert energy_score(reference, member[None]) == pytest.approx(
        np.linalg.norm(member - reference), rel=1e-12
    )


@pytest.mark.parametrize("n_members", [2, 8])
def test_the_fair_estimator_is_unbiased_at_any_ensemble_size(n_members):
    """Reference and members drawn independently from N(0, I) in four dimensions.

    The difference of two independent draws is N(0, 2I), whose norm has mean
    sqrt(2) * sqrt(2) * Gamma(5/2) / Gamma(2) (the mean of a chi distribution with four
    degrees of freedom, times sqrt(2)). Both expectations in the score are that number, so
    the score's expectation is half of it, Gamma(5/2) = 3 sqrt(pi) / 4 = 1.3293, whatever
    the ensemble size. The plug-in estimator, dividing the pair sum by 2M^2, would give
    1.994 at M = 2. The mean over 20 000 independent cases has a standard error near 0.5%.
    """
    rng = np.random.default_rng(11)
    cases = 20_000
    references = rng.standard_normal((cases, 1, 4))
    ensembles = rng.standard_normal((cases, n_members, 1, 4))
    mean = np.mean([energy_score(references[k], ensembles[k]) for k in range(cases)])
    assert mean == pytest.approx(float(gamma(2.5)), rel=0.02)


def test_an_imperfect_ensemble_can_reach_the_floor_of_zero():
    """One cell, members -1, 0 and 1 against a reference of 0.

    The distance term is (1 + 0 + 1) / 3 = 2/3. The ordered pairs sum to 2 * (1 + 2 + 1) = 8,
    and 8 / (2M(M-1)) = 8 / 12 = 2/3 is the pair credit, so the score is exactly 0, the
    value of a perfect ensemble.
    """
    members = np.array([-1.0, 0.0, 1.0]).reshape(3, 1, 1)
    assert energy_score(np.zeros((1, 1)), members) == pytest.approx(0.0, abs=1e-15)


def test_the_fair_score_is_never_negative():
    """The triangle inequality bounds the pair credit by the distance term.

    ||x_i - x_j|| <= ||x_i - y|| + ||x_j - y||; summed over the M(M-1) ordered pairs the
    right side is 2(M-1) sum_i ||x_i - y||, so the pair credit, that sum over 2M(M-1), is at
    most the mean distance. Checked on draws with the reference inside the ensemble's range,
    where the score is smallest.
    """
    rng = np.random.default_rng(9)
    for _ in range(500):
        members = rng.standard_normal((4, 1, 3))
        reference = members.mean(axis=0)
        assert energy_score(reference, members) >= 0.0


def test_scales_linearly_with_the_field_units():
    """The score is in the field's units: scaling every value scales it."""
    rng = np.random.default_rng(3)
    reference = rng.standard_normal((1, 8, 4))
    members = rng.standard_normal((6, 1, 8, 4))
    assert energy_score(3.0 * reference, 3.0 * members) == pytest.approx(
        3.0 * energy_score(reference, members), rel=1e-12
    )


def test_penalises_both_over_and_under_dispersion():
    """Propriety: the calibrated ensemble beats a wider and a narrower one.

    The reference is an independent draw from the members' own process, as
    ``exchangeable_ensemble`` explains.
    """
    truth, members = exchangeable_ensemble(5, (1, 16, 16), 64)
    calibrated = energy_score(truth, members)
    assert energy_score(truth, scale_spread(members, 3.0)) > calibrated, "over-dispersion"
    assert energy_score(truth, scale_spread(members, 0.2)) > calibrated, "under-dispersion"


def test_rejects_an_empty_ensemble():
    with pytest.raises(ValueError):
        energy_score(np.zeros((1, 4, 4)), np.zeros((0, 1, 4, 4)))
