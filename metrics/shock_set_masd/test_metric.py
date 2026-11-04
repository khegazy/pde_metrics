"""Tests for the mean average surface distance between shock sets.

The registry-wide contract lives in ``tests/test_metric_contract.py``, and the detector, the
empty-set conventions and the non-finite rule are tested once, in
``metrics/shock_set_distance``. What is tested here is the worked example of the card, where
the equal weighting of the two directions separates it from the pooled average.
"""

from __future__ import annotations

import pytest

from metrics.shock_set_distance.metric import shock_set_distance
from tests.conftest import SHOCK_STEP, SHOCK_STEP_MOVED, SHOCK_STEP_SPIKE, make_ctx

from .metric import shock_set_masd


def test_worked_example_from_the_card():
    """Moved two cells: each direction's distances are {2, 1}, mean 1.5, so the mean of the two
    means is 1.5, equal to the pooled average 6/4 when both sets have the same size.

    Spike: from the reference's cells {7, 8} the mean distance is 0; from the candidate's
    {0, 2, 7, 8} it is (7 + 5 + 0 + 0) / 4 = 3. The mean of the two is 1.5, where the pooled
    average, which counts the candidate's four cells against the reference's two, is
    12 / 6 = 2.
    """
    assert shock_set_masd(SHOCK_STEP, SHOCK_STEP_MOVED, ctx=make_ctx((16,))) == 1.5
    assert shock_set_masd(SHOCK_STEP, SHOCK_STEP_SPIKE, ctx=make_ctx((16,))) == 1.5
    assert shock_set_distance(SHOCK_STEP, SHOCK_STEP_SPIKE, ctx=make_ctx((16,))) == (
        pytest.approx(2.0))
