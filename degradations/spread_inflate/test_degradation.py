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

from .degradation import spread_inflate


def _ensemble(n_members: int = 8, seed: int = 0) -> np.ndarray:
    """Pure unit-variance noise members on a non-square grid."""
    return members(np.zeros((1, 8, 4)), n_members=n_members, seed=seed, scale=1.0)


def test_severity_is_the_excess_dispersion():
    """Severity one doubles the spread; severity three quadruples it."""
    members = _ensemble()
    base = members.std(axis=0, ddof=1).mean()
    for severity, factor in ((1.0, 2.0), (3.0, 4.0)):
        widened = spread_inflate(members, severity).std(axis=0, ddof=1).mean()
        assert widened == pytest.approx(factor * base, rel=1e-12)
