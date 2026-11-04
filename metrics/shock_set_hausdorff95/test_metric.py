"""Tests for the 95th-percentile Hausdorff distance between shock sets.

The registry-wide contract lives in ``tests/test_metric_contract.py``, and the detector, the
empty-set conventions and the non-finite rule are tested once, in
``metrics/shock_set_distance``. What is tested here is the worked example of the card, which
directions the percentile is taken over, and the bound by the Hausdorff distance.
"""

from __future__ import annotations

import numpy as np
import pytest

from metrics.shock_set_distance.metric import shock_mask, surface_distances
from metrics.shock_set_hausdorff.metric import hausdorff
from tests.conftest import SHOCK_STEP, SHOCK_STEP_MOVED, SHOCK_STEP_SPIKE, make_ctx

from .metric import hausdorff_percentile, shock_set_hausdorff95


def test_worked_example_from_the_card():
    """Moved two cells: each direction's distances are {2, 1}; the 95th percentile with linear
    interpolation between the sorted values 1 and 2 is 1 + 0.95 * (2 - 1) = 1.95 in both, so
    1.95, where the Hausdorff distance is 2.

    Spike: from the reference's cells {7, 8} every distance is 0, so that percentile is 0; from
    the candidate's {0, 2, 7, 8} the distances are {7, 5, 0, 0}, sorted 0, 0, 5, 7, and the 95th
    percentile sits at position 0.95 * 3 = 2.85, 5 + 0.85 * (7 - 5) = 6.7. The larger is 6.7:
    with four cells in a direction, the 95th percentile is close to the maximum, 7.
    """
    assert shock_set_hausdorff95(SHOCK_STEP, SHOCK_STEP_MOVED, ctx=make_ctx((16,))) == (
        pytest.approx(1.95, rel=1e-12))
    assert shock_set_hausdorff95(SHOCK_STEP, SHOCK_STEP_SPIKE, ctx=make_ctx((16,))) == (
        pytest.approx(6.7, rel=1e-12))


def test_the_percentile_is_taken_per_direction_and_not_pooled():
    """Metrics Reloaded takes the percentile of each direction and then the larger; medpy's
    hd95 pools both directions first. On the spike example the pooled distances are
    {0, 0, 7, 5, 0, 0}, whose 95th percentile is at position 0.95 * 5 = 4.75 of the sorted
    0, 0, 0, 0, 5, 7: 5 + 0.75 * 2 = 6.5, not this metric's 6.7."""
    a, b = shock_mask(SHOCK_STEP[0]), shock_mask(SHOCK_STEP_SPIKE[0])
    d_ab, d_ba = surface_distances(a, b, (1.0,))
    assert np.percentile(np.concatenate([d_ab, d_ba]), 95) == pytest.approx(6.5)
    assert hausdorff_percentile(a, b, (1.0,)) == pytest.approx(6.7)


def test_it_never_exceeds_the_hausdorff_distance():
    """A percentile of a set of distances is at most their maximum, so HD95 <= HD, on random
    sets of a 2-D grid."""
    rng = np.random.default_rng(7)
    for _ in range(20):
        a, b = rng.random((10, 7)) < 0.15, rng.random((10, 7)) < 0.15
        a[0, 0] = b[9, 6] = True
        assert hausdorff_percentile(a, b, (1.0, 1.5)) <= hausdorff(a, b, (1.0, 1.5))
