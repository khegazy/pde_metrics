"""The `translate_subpixel` degradation.

See ``card.md`` for what this stands in for, how its severity is scaled, and where it
is not a fair imitation of the failure it models.
"""

from __future__ import annotations

import numpy as np

from .._shared.geometry import _axes_for
from ..registry import degradation


@degradation(
    family="geometric",
    severity_name="distance",
    severity_units="cells",
    severity_direction="increasing",
    defaults={"axis": "x"},
    preserves=("spatial_mean",),
)
def translate_subpixel(
    x: np.ndarray, severity: float, *, ctx, axis: str = "x"
) -> np.ndarray:
    """Fractional translation by a Fourier phase shift -- exact on a periodic grid.

    Resolves the sub-cell region where the double-penalty curve actually distinguishes
    metrics. At integer distances it reproduces ``np.roll`` to floating-point tolerance,
    which the contract test pins.

    Exact except at the Nyquist mode of an even grid: a fractional shift makes that component
    imaginary and the real part discards it, so it declares only ``spatial_mean``. Measured:
    1.7e-2 of the amplitude of a white-noise test field at half a cell, and at most 8.2e-11 of
    the fluctuation energy of frame 5000 of kinet_re5e4, which has almost nothing at the grid
    scale (issues/041).
    """
    if severity == 0:
        return x
    axes = _axes_for(axis, ctx)
    spatial = tuple(range(1, x.ndim))
    spectrum = np.fft.fftn(x, axes=spatial)

    for ax in axes:
        n = x.shape[ax]
        freq = np.fft.fftfreq(n)
        # Broadcast the phase ramp along this axis only.
        shape = [1] * x.ndim
        shape[ax] = n
        phase = np.exp(-2j * np.pi * freq.reshape(shape) * severity)
        spectrum = spectrum * phase

    return np.real(np.fft.ifftn(spectrum, axes=spatial))
