"""The `median_blur` degradation.

See ``card.md`` for what this stands in for, how its severity is scaled, and where it
is not a fair imitation of the failure it models.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import median_filter

from .._shared.kernels import _window_filter
from ..registry import degradation


@degradation(
    family="smoothing",
    severity_name="width",
    severity_units="cells",
    severity_direction="increasing",
    calibration="scale",
)
def median_blur(x: np.ndarray, severity: float, *, ctx) -> np.ndarray:
    """Median filter: nonlinear, and edge-preserving where a Gaussian smears.

    The interesting contrast for this project. A metric that scores median and Gaussian
    smoothing the same at matched width is not seeing the sharp structure that the
    shock-oriented metrics are supposed to target.
    """
    return _window_filter(x, severity, ctx, median_filter)
