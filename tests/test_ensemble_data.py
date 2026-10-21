"""The ensemble extension to the data contract.

An ensemble trajectory carries, beside each field's reference realization, a stack of
``(N, C, *spatial)`` members standing in for a predictive distribution. Two things matter
enough to test directly:

* the validation of that member stack is as strict as the validation of a field -- a
  reader that returns the member axis in the wrong place must fail loudly, because a
  ``(C, N, *spatial)`` stack would silently make every probabilistic metric average over
  the wrong axis and still return a plausible number;
* the deterministic path is untouched. Every deterministic reader declares
  ``is_ensemble = False``, and a frame it produces carries no members at all.
"""

from __future__ import annotations

import numpy as np
import pytest

from fmeval.data.base import Frame, GridSpec, Trajectory

SHAPE = (16, 8)
N_MEMBERS = 5


class _DeterministicStub(Trajectory):
    """Minimal in-memory deterministic reader, for exercising the base-class contract."""

    @property
    def fields(self) -> tuple[str, ...]:
        return ("density",)

    @property
    def times(self) -> np.ndarray:
        return np.arange(3, dtype=float)

    @property
    def grid(self) -> GridSpec:
        return GridSpec(shape=SHAPE, spacing=(1.0, 1.0), boundary=("periodic", "periodic"))

    @property
    def meta(self) -> dict:
        return {"format": "stub"}

    def read_frame(self, t, fields):
        return {name: np.full((1, *SHAPE), float(t)) for name in fields}


class _EnsembleStub(_DeterministicStub):
    """The same reader with a member stack of ``members_shape`` beside every field."""

    is_ensemble = True

    def __init__(self, *, members_shape: tuple[int, ...] = (N_MEMBERS, 1, *SHAPE)) -> None:
        self._members_shape = members_shape

    def read_frame(self, t, fields):
        out = super().read_frame(t, fields)
        for name in fields:
            out[f"{name}__members"] = np.arange(
                int(np.prod(self._members_shape)), dtype=float
            ).reshape(self._members_shape)
        return out


# --- the deterministic path is unchanged -------------------------------------------


def test_trajectory_is_deterministic_by_default():
    """``is_ensemble`` defaults False, so no existing reader opts in by accident."""
    assert Trajectory.is_ensemble is False
    assert _DeterministicStub().is_ensemble is False


def test_deterministic_frame_has_no_members():
    frame = _DeterministicStub().frame(1, ["density"])
    assert frame.members is None
    assert frame.has_members is False


def test_frame_members_default_to_none():
    """Every existing Frame construction site omits members and must keep working."""
    grid = GridSpec(shape=SHAPE, spacing=(1.0, 1.0), boundary=("periodic", "periodic"))
    frame = Frame(index=0, time=0.0, fields={"density": np.zeros((1, *SHAPE))}, grid=grid)
    assert frame.members is None
    assert frame.has_members is False


# --- the ensemble path ---------------------------------------------------------------


def test_ensemble_frame_carries_members():
    frame = _EnsembleStub().frame(1, ["density"])
    assert frame.has_members
    assert set(frame.members) == {"density"}
    assert frame.members["density"].shape == (N_MEMBERS, 1, *SHAPE)
    assert frame.members["density"].dtype == np.float64


def test_members_do_not_leak_into_fields():
    """The ``__members`` sentinel key is consumed by the validator, not passed through."""
    frame = _EnsembleStub().frame(1, ["density"])
    assert set(frame.fields) == {"density"}


@pytest.mark.parametrize("members_shape", [
    # ``(C, N, *spatial)`` must raise: it is the silent-wrong-answer shape, on which every
    # probabilistic metric would average over the channel axis and still return a number.
    pytest.param((1, N_MEMBERS, *SHAPE), id="transposed-member-axis"),
    # A member stack on a different grid from its field.
    pytest.param((N_MEMBERS, 1, SHAPE[0], SHAPE[1] + 2), id="wrong-grid"),
    # A stack with no member axis at all, shaped like the field itself.
    pytest.param((1, *SHAPE), id="no-member-axis"),
])
def test_rejects_a_misshapen_member_stack(members_shape):
    """A member stack must be ``(N, C, *spatial)`` on the field's grid, or the frame fails."""
    with pytest.raises(ValueError, match="members"):
        _EnsembleStub(members_shape=members_shape).frame(1, ["density"])


def test_rejects_non_finite_members():
    class _NaNStub(_EnsembleStub):
        def read_frame(self, t, fields):
            out = super().read_frame(t, fields)
            for name in fields:
                out[f"{name}__members"][0, 0, 0, 0] = np.nan
            return out

    with pytest.raises(ValueError, match="non-finite"):
        _NaNStub().frame(1, ["density"])


def test_with_fields_drops_members_unless_carried():
    """A shape-changing operation must not silently keep a stale member stack."""
    frame = _EnsembleStub().frame(1, ["density"])
    grid = frame.grid
    replaced = frame.with_fields({"density": np.zeros((1, *SHAPE))}, grid)
    assert replaced.members is None

    carried = frame.with_fields(
        {"density": np.zeros((1, *SHAPE))}, grid, members=frame.members
    )
    assert carried.has_members
    assert carried.members["density"].shape == (N_MEMBERS, 1, *SHAPE)
