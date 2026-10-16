"""Tests for this bundle's degradation.

The contract every degradation must satisfy -- shape and dtype preserved, severity zero
being a no-op where that is meant to hold, the declared severity direction actually being
true -- is checked for the whole registry in ``tests/test_degradation_contract.py``. Do
not repeat it here. Test what is specific to this operator: the property that makes it
the degradation it claims to be.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import members

from .degradation import spread_deflate


def _ensemble(n_members: int = 8, seed: int = 0) -> np.ndarray:
    """Pure unit-variance noise members on a non-square grid."""
    return members(np.zeros((1, 8, 4)), n_members=n_members, seed=seed, scale=1.0)


def test_severity_is_the_fraction_of_spread_removed():
    """Severity 0.75 leaves a quarter of the dispersion."""
    members = _ensemble()
    base = members.std(axis=0, ddof=1).mean()
    narrowed = spread_deflate(members, 0.75).std(axis=0, ddof=1).mean()
    assert narrowed == pytest.approx(0.25 * base, rel=1e-12)


def test_full_severity_collapses_the_ensemble_onto_its_mean():
    """The limit case: a forecast claiming perfect certainty."""
    members = _ensemble()
    collapsed = spread_deflate(members, 1.0)
    assert collapsed.std(axis=0, ddof=1) == pytest.approx(0.0, abs=1e-12)
    assert collapsed[0] == pytest.approx(members.mean(axis=0), rel=1e-12)


def test_a_severity_outside_the_unit_interval_is_refused():
    """Severity is a fraction removed, so above one it would invert the ensemble."""
    members = _ensemble()
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        spread_deflate(members, 1.5)
