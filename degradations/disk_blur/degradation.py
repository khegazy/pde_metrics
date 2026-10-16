"""The `disk_blur` degradation.

See ``card.md`` for what this stands in for, how its severity is scaled, and where it
is not a fair imitation of the failure it models.
"""

from __future__ import annotations

import numpy as np

from .._shared.kernels import _radial_blur
from ..registry import degradation


@degradation(
    family="smoothing",
    severity_name="radius",
    severity_units="cells",
    severity_direction="increasing",
    calibration="scale",
    preserves=("spatial_mean",),
)
def disk_blur(x: np.ndarray, severity: float, *, ctx) -> np.ndarray:
    """Isotropic top-hat: a uniform disk, unlike box_blur's square."""
    return _radial_blur(x, severity, ctx, "disk")
