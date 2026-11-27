"""The `gneiting_forecaster` degradation: the three non-ideal forecasters of Gneiting et al.

See ``card.md`` for the experiment it reproduces and the reader settings it presupposes.
"""

from __future__ import annotations

import numpy as np

from fmeval.context import FieldContext

from ..registry import degradation

#: Hamill's forecaster, Gneiting, Balabdaoui & Raftery (2007), Table 1: a mean shift delta and a
#: variance s^2, each pair drawn with probability 1/3.
HAMILL_SHIFTS = np.array([0.5, -0.5, 0.0])
HAMILL_VARIANCES = np.array([1.0, 1.0, 1.69])


@degradation(
    family="ensemble",
    severity_name="n/a",
    severity_units="",
    ordinal=False,         # three forecasters of different kinds, not levels on one axis
    stochastic=True,
    ensemble=True,
    zero_is_identity=False,
)
def gneiting_forecaster(members: np.ndarray, severity: float, *, ctx: FieldContext,
                        kind: str = "climatological") -> np.ndarray:
    """Turn the ideal forecaster's members into the climatological, unfocused or Hamill's.

    Gneiting, Balabdaoui & Raftery (2007, JRSS-B 69(2):243, Sect. 1, Table 1): nature draws a
    case mean mu ~ N(0, 1) and the observation from N(mu, 1). On the ``synthetic_ensemble``
    reader with ``base: case_means`` and ``sigma: 1`` every cell is such a case and the clean
    members are draws from the ideal forecaster N(mu, 1); the constants below presuppose
    exactly those settings. Without knowing mu, each kind is drawn exactly:

    * ``climatological``: N(0, 2), each member redrawn;
    * ``unfocused``: the mixture (N(mu, 1) + N(mu + tau, 1)) / 2, tau = +-1 once per cell:
      an ideal member plus tau B, B in {0, 1} per member and cell;
    * ``hamill``: N(mu + delta, s^2) with (delta, s^2) drawn once per cell from Table 1's
      three pairs: an ideal member plus delta + sqrt(s^2 - 1) zeta, zeta ~ N(0, 1).

    The severity is ignored; a ladder entry runs each kind once at severity 0.

    Args:
        members: The ideal forecaster's members, ``(N, C, *spatial)``.
        severity: Ignored.
        ctx: Its generator draws every random number.
        kind: ``climatological``, ``unfocused`` or ``hamill``.

    Returns:
        The forecaster's members, same shape.

    Raises:
        ValueError: On an unknown kind.
    """
    rng = ctx.rng
    cases = members.shape[1:]
    if kind == "climatological":
        return np.sqrt(2.0) * rng.standard_normal(members.shape)
    if kind == "unfocused":
        tau = rng.choice([-1.0, 1.0], size=cases)
        return members + tau * rng.integers(0, 2, size=members.shape)
    if kind == "hamill":
        pick = rng.integers(0, 3, size=cases)
        return (members + HAMILL_SHIFTS[pick]
                + np.sqrt(HAMILL_VARIANCES[pick] - 1.0) * rng.standard_normal(members.shape))
    raise ValueError(f"kind must be climatological, unfocused or hamill, got {kind!r}")
