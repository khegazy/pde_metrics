"""Grid expansion, shared by the resolution operators. Coarsening lives in `fmeval.remap`."""

from __future__ import annotations

import numpy as np


def _upsample(x: np.ndarray, factor: int) -> np.ndarray:
    """Nearest-neighbour expansion back to the original grid.

    Nearest rather than bilinear on purpose: it reintroduces no information and no new
    smoothing, so the damage measured is resolution loss alone rather than resolution loss
    convolved with an interpolation kernel.
    """
    out = x
    for axis in range(1, x.ndim):
        out = np.repeat(out, factor, axis=axis)
    return out
