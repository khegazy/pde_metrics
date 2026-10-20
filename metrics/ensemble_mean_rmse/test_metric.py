"""Ensemble-mean RMSE: the deterministic control for the probabilistic family.

Its job is to be boring in a specific way. It collapses the ensemble to its mean and
scores that with the existing RMSE, so it sees accuracy and is blind to dispersion --
which is exactly what makes it the right thing to read CRPS against. The test that earns
its place here is the one showing that blindness explicitly.
"""

from __future__ import annotations

import numpy as np
import pytest

from degradations._shared.ensemble import scale_spread
from metrics.ensemble_mean_rmse.metric import ensemble_mean_rmse
from metrics.rmse.metric import rmse


def test_worked_example_from_the_card():
    """Two members at 0 and 4 against a reference of 1, on a 2x2 field.

    The ensemble mean is 2 everywhere, the error is 1 everywhere, so the RMSE is 1.
    """
    reference = np.ones((1, 2, 2))
    members = np.stack([np.zeros((1, 2, 2)), np.full((1, 2, 2), 4.0)])
    assert ensemble_mean_rmse(reference, members) == pytest.approx(1.0)


@pytest.mark.parametrize("n_members", [
    # A single member is its own mean, so the score is exactly that member's RMSE.
    pytest.param(1, id="one-member"),
    # Six members, where the mean is a genuine average over the member axis.
    pytest.param(6, id="six-members"),
])
def test_equals_rmse_of_the_member_mean(n_members: int):
    """The definition, checked against this repository's own RMSE.

    Also the test that catches an axis slip: averaging over channels instead of members
    would still return a number of the right order.
    """
    rng = np.random.default_rng(0)
    reference = rng.standard_normal((2, 8, 4))
    members = rng.standard_normal((n_members, 2, 8, 4))
    assert ensemble_mean_rmse(reference, members) == pytest.approx(
        rmse(reference, members.mean(axis=0)), rel=1e-12
    )


def test_is_zero_when_the_mean_is_the_reference():
    reference = np.linspace(0, 1, 24).reshape(1, 6, 4)
    members = np.stack([reference - 0.5, reference + 0.5])
    assert ensemble_mean_rmse(reference, members) == pytest.approx(0.0, abs=1e-12)


def test_is_blind_to_dispersion_about_a_fixed_mean():
    """The control's defining property: inflating the spread leaves it unchanged.

    This is what separates it from CRPS and from the spread-to-skill ratio. A panel that
    reported only this number could not tell a confident ensemble from a vague one.
    """
    rng = np.random.default_rng(2)
    reference = rng.standard_normal((1, 10, 6))
    members = rng.standard_normal((12, 1, 10, 6))
    baseline = ensemble_mean_rmse(reference, members)
    for factor in (0.1, 0.5, 2.0, 5.0):
        assert ensemble_mean_rmse(reference, scale_spread(members, factor)) == pytest.approx(
            baseline, rel=1e-12
        )


def test_rejects_an_empty_ensemble():
    with pytest.raises(ValueError):
        ensemble_mean_rmse(np.zeros((1, 4, 4)), np.zeros((0, 1, 4, 4)))
