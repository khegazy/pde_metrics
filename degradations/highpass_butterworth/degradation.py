"""The `highpass_butterworth` degradation.

See ``card.md`` for what this stands in for, how its severity is scaled, and where it
is not a fair imitation of the failure it models.
"""

from __future__ import annotations

import numpy as np

from fmeval.wavenumbers import wavenumber_magnitude

from .._shared.filters import _apply_filter, butterworth
from ..registry import degradation


@degradation(
    family="spectral",
    severity_name="energy removed",
    severity_units="fraction",
    severity_direction="increasing",
    calibration="energy_below",
    preserves=("spatial_mean",),
    zero_is_identity=False,
)
def highpass_butterworth(
    x: np.ndarray, severity: float, *, ctx, order: int = 4
) -> np.ndarray:
    """Smooth high-pass, ``1 - 1/(1 + (k/k_c)^(2n))``, keeping the spatial mean.

    The k=0 mode is preserved for the same reason as in :func:`highpass_ideal`.
    """
    transfer = 1.0 - butterworth(wavenumber_magnitude(ctx.grid.shape), severity, order)
    return _apply_filter(x, transfer, keep_mean=True)
