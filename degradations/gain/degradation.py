"""The `gain` degradation.

See ``card.md`` for what this stands in for, how its severity is scaled, and where it
is not a fair imitation of the failure it models.
"""

from __future__ import annotations

import numpy as np

from fmeval.context import fluctuation

from ..registry import degradation


@degradation(
    family="pointwise",
    severity_name="gain error",
    severity_units="relative",
    severity_direction="increasing",
    preserves=("spatial_mean", "shape"),
)
def gain(x: np.ndarray, severity: float, *, ctx) -> np.ndarray:
    """Scale the fluctuation by ``1 + severity``, leaving the spatial mean intact.

    Pure amplitude error with zero position error: every feature stays exactly where it
    was and every gradient keeps its sign.
    """
    if severity == 0:
        return x
    return x + severity * fluctuation(x)
