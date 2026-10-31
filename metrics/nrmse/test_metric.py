"""Tests specific to normalised root mean squared error.

The registry-wide contract is checked in ``tests/test_metric_contract.py``. What is
tested here is what the card claims: the worked example, the scale invariance that makes
the value comparable across fields, the choice to normalise by the fluctuation rather
than the raw RMS, and the uniform-reference case.
"""

from __future__ import annotations

import numpy as np

from tests.conftest import SQUARE_REFERENCE, SQUARE_SHIFTED

from ..rmse.metric import rmse
from .metric import nrmse


def test_worked_example_from_the_card():
    """RMSE is 0.5; the reference fluctuation RMS is sqrt(3)/4, so the ratio is 8/sqrt(3)."""
    expected = 0.5 / np.sqrt(3.0) * 4.0
    assert np.isclose(nrmse(SQUARE_REFERENCE, SQUARE_SHIFTED), expected)


def test_worked_example_of_scale_invariance_from_the_card():
    """The two-row table in the card's Intuition section.

    The same displaced feature, scored as it stands and with both fields multiplied by a
    ten-thousandth. RMSE falls by four orders of magnitude; NRMSE does not move.
    """
    assert rmse(SQUARE_REFERENCE, SQUARE_SHIFTED) == 0.5
    assert np.isclose(rmse(SQUARE_REFERENCE * 1e-4, SQUARE_SHIFTED * 1e-4), 5e-05)
    assert np.isclose(nrmse(SQUARE_REFERENCE, SQUARE_SHIFTED), 1.155, atol=5e-4)
    assert np.isclose(nrmse(SQUARE_REFERENCE * 1e-4, SQUARE_SHIFTED * 1e-4), 1.155, atol=5e-4)


def test_scaling_both_fields_leaves_it_unchanged():
    """The property the card claims makes it readable across fields.

    Multiplying reference and candidate by any constant scales the error and the
    normalising fluctuation equally, so the ratio does not move. This is what MSE, MAE
    and RMSE cannot do.
    """
    plain = nrmse(SQUARE_REFERENCE, SQUARE_SHIFTED)
    for factor in (1e-4, 1e3):
        assert np.isclose(nrmse(SQUARE_REFERENCE * factor, SQUARE_SHIFTED * factor), plain)


def test_adding_a_constant_offset_to_the_reference_leaves_it_unchanged():
    """Normalising by the *fluctuation* is what buys this.

    The kinet density field fluctuates by a few thousandths of its mean of 1.0. Normalising by
    the raw RMS would divide by about one and hide two to three orders of magnitude of relative
    error; removing the spatial mean first is what keeps density and velocity on the same axis.
    """
    plain = nrmse(SQUARE_REFERENCE, SQUARE_SHIFTED)
    assert np.isclose(nrmse(SQUARE_REFERENCE + 1000.0, SQUARE_SHIFTED + 1000.0), plain)


def test_a_uniform_reference_has_no_scale_to_normalise_by():
    """NaN rather than an exception or a silent infinity: there is genuinely no answer."""
    uniform = np.ones((1, 4, 4))
    candidate = uniform.copy()
    candidate[0, 0, 0] = 2.0
    assert np.isnan(nrmse(uniform, candidate))


def test_it_is_not_symmetric():
    """The reference sets the scale, so swapping the arguments changes the value.

    Shown against a damped candidate rather than a displaced one: a translation has the
    same fluctuation RMS as its reference, so swapping those two divides by the same
    number and hides the asymmetry. Halving the amplitude halves the fluctuation, which
    is what makes the direction matter.
    """
    damped = SQUARE_REFERENCE * 0.5
    assert not np.isclose(nrmse(SQUARE_REFERENCE, damped), nrmse(damped, SQUARE_REFERENCE))
    # The reference is the larger field, so normalising by it gives the smaller number.
    assert nrmse(SQUARE_REFERENCE, damped) < nrmse(damped, SQUARE_REFERENCE)
