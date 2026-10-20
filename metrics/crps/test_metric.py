"""CRPS: the identities that pin the estimator.

The two tests that carry the most weight here are the ones that tie this implementation
to something already trusted or already known:

* at one member the fair estimator collapses to mean absolute error exactly, checked
  against this repository's own ``mae``, so the degenerate case cannot drift;
* at large ensemble size it converges to the closed form for a normal predictive
  distribution, which is what makes the number meaningful rather than merely
  self-consistent.

The fair estimator is also visibly *not* the plug-in one on the worked example -- 0.1667
against 0.5 -- so a silent substitution of the biased form fails immediately.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from degradations._shared.ensemble import scale_spread
from metrics.crps.metric import crps
from metrics.mae.metric import mae
from tests.conftest import exchangeable_ensemble


def gaussian_crps(mu: float, sigma: float, y: float) -> float:
    """Closed-form CRPS of ``N(mu, sigma^2)`` against observation ``y``.

    Used only as an independent reference in these tests, never by the metric itself.
    """
    z = (y - mu) / sigma
    return float(
        sigma * (z * (2 * stats.norm.cdf(z) - 1) + 2 * stats.norm.pdf(z) - 1 / np.sqrt(np.pi))
    )


# --- worked example and estimator identity ------------------------------------------


def test_worked_example_from_the_card():
    """Three members at -1, 0.5, 2 against a reference of 0, on a single cell.

    Skill term ``mean|x_i - y|`` is 7/6; the pair sum is 12, so the fair correction is
    12 / (2*3*2) = 1, giving 7/6 - 1 = 1/6. The plug-in estimator would divide by
    2*N^2 = 18 instead and give 1/2, three times larger.
    """
    reference = np.zeros((1, 1, 1))
    members = np.array([-1.0, 0.5, 2.0]).reshape(3, 1, 1, 1)
    assert crps(reference, members) == pytest.approx(1.0 / 6.0)


def test_single_member_equals_mae():
    """At N=1 the pair term vanishes and CRPS is exactly mean absolute error."""
    rng = np.random.default_rng(0)
    reference = rng.standard_normal((2, 8, 4))
    member = rng.standard_normal((2, 8, 4))
    assert crps(reference, member[None]) == pytest.approx(mae(reference, member), rel=1e-12)


def test_identical_members_equal_mae_against_that_member():
    """A zero-spread ensemble is a deterministic forecast, and scores like one."""
    rng = np.random.default_rng(1)
    reference = rng.standard_normal((1, 6, 4))
    member = rng.standard_normal((1, 6, 4))
    members = np.repeat(member[None], 5, axis=0)
    assert crps(reference, members) == pytest.approx(mae(reference, member), rel=1e-12)


# --- convergence to the closed form --------------------------------------------------


@pytest.mark.parametrize("y", [0.0, 0.5, 1.5])
def test_matches_the_gaussian_closed_form_at_large_ensemble_size(y):
    """A large standard-normal ensemble against a fixed observation.

    The fair estimator is unbiased for the population CRPS, so the residual is sampling
    noise falling as 1/sqrt(N). Rather than lean on one lucky seed, the ensemble is
    spread over many cells -- 200 000 draws in total -- which shrinks the standard error
    to about 0.1% and lets the tolerance be tight enough to catch a wrong constant or a
    dropped factor, the errors this test exists for.
    """
    rng = np.random.default_rng(7)
    reference = np.full((1, 20, 10), y)
    members = rng.standard_normal((1000, 1, 20, 10))
    assert crps(reference, members) == pytest.approx(
        gaussian_crps(0.0, 1.0, y), rel=0.01
    )


def test_scales_linearly_with_the_field_units():
    """CRPS is in the units of the field, so scaling both scales the score."""
    rng = np.random.default_rng(3)
    reference = rng.standard_normal((1, 8, 4))
    members = rng.standard_normal((6, 1, 8, 4))
    assert crps(3.0 * reference, 3.0 * members) == pytest.approx(
        3.0 * crps(reference, members), rel=1e-12
    )


# --- response to miscalibration ------------------------------------------------------


def test_penalises_both_over_and_under_dispersion():
    """CRPS is proper: the calibrated ensemble beats both wider and narrower ones.

    Propriety is a statement about the *true* predictive distribution, so the reference
    here is an independent draw from the same process as the members, not the ensemble's
    own centre; ``exchangeable_ensemble`` says why the other construction would make a
    correct metric look non-proper.
    """
    truth, members = exchangeable_ensemble(5, (1, 16, 16), 64)
    calibrated = crps(truth, members)
    assert crps(truth, scale_spread(members, 3.0)) > calibrated, "over-dispersion"
    assert crps(truth, scale_spread(members, 0.2)) > calibrated, "under-dispersion"


# --- shape handling ------------------------------------------------------------------


def test_averages_over_channels_and_cells():
    """Two channels whose scores are known separately average to the reported value."""
    reference = np.zeros((2, 1, 1))
    members = np.stack(
        [np.array([[[0.0]], [[0.0]]]), np.array([[[2.0]], [[4.0]]])]
    )  # (2 members, 2 channels, 1, 1)
    per_channel = [
        crps(reference[:1], members[:, :1]),
        crps(reference[1:], members[:, 1:]),
    ]
    assert crps(reference, members) == pytest.approx(np.mean(per_channel))


def test_rejects_an_empty_ensemble():
    reference = np.zeros((1, 4, 4))
    with pytest.raises(ValueError):
        crps(reference, np.zeros((0, 1, 4, 4)))
