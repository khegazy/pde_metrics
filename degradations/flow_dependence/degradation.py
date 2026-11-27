"""The `flow_dependence` degradation: an ensemble whose spread follows its uncertainty too
weakly or too strongly.

See ``card.md`` for what this stands in for and where it misleads.
"""

from __future__ import annotations

import numpy as np

from .._shared.ensemble import scale_spread
from ..registry import degradation


@degradation(
    family="ensemble",
    severity_name="change of the spread exponent",
    severity_units="",
    severity_direction="increasing",
    ensemble=True,
    preserves=("ensemble_mean",),
)
def flow_dependence(members: np.ndarray, severity: float, *,
                    direction: str = "damp") -> np.ndarray:
    """Raise every cell's spread to a power, keeping the frame's mean variance.

    With s_hat the per-cell sample standard deviation of the members, the spread becomes
    k s_hat^a, with a = 1 - severity (``damp``) or 1 + severity (``amplify``) and k set so the
    frame's mean sample variance is unchanged (spec 08, Eq. 4):

        k^2 = mean(s_hat^2) / mean(s_hat^(2a)),   members' = scale_spread(members, k s_hat^(a-1)).

    The ensemble mean and the mean variance are kept, so only which cells carry the spread
    changes. Damp 1 makes the spread uniform, damp 2 inverts it, amplify 1 squares it.

    Raises:
        ValueError: On an unknown direction, a negative severity, or, where a < 1, a cell
            with no spread to rescale.
    """
    if direction not in ("damp", "amplify"):
        raise ValueError(f"direction must be damp or amplify, got {direction!r}")
    if severity < 0:
        raise ValueError(f"flow_dependence severity must be >= 0, got {severity}")
    if severity == 0:
        return members
    a = 1.0 - severity if direction == "damp" else 1.0 + severity
    spread = members.std(axis=0, ddof=1)
    if a < 1 and spread.min() == 0:
        raise ValueError("flow_dependence: a cell whose members all agree cannot take a "
                         "spread exponent below one")
    k = np.sqrt(np.mean(spread**2) / np.mean(spread ** (2 * a)))
    return scale_spread(members, k * spread ** (a - 1))
