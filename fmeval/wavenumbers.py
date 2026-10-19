"""The one definition of wavenumber magnitude, shared by the filters and the calibration.

Both sides must compare a cutoff against the same ``|k|``, or the energy a cutoff removes
according to the calibration is not the energy it actually removes. Binning into shells of
``rint(|k|)`` on one side while comparing the continuous magnitude on the other puts the diagonal
modes on opposite sides of one cutoff -- ``(1, 1)`` has ``|k| = 1.414`` -- and on density, whose
fluctuation energy sits in the lowest shells, that turned a low-pass asked to remove 30% into one
removing 99.997%, with every number in between looking plausible.
"""

from __future__ import annotations

import numpy as np


def wavenumber_magnitude(shape: tuple[int, ...]) -> np.ndarray:
    """Grid of ``|k|`` in integer wavenumber units -- cycles across the domain.

    Args:
        shape: Spatial shape, in the canonical trailing-axes order.

    Returns:
        Array of ``shape`` holding the Euclidean magnitude of each mode's wavevector. Not
        rounded: the magnitudes a filter cutoff is actually compared against.
    """
    axes = np.meshgrid(*[np.fft.fftfreq(n) * n for n in shape], indexing="ij")
    return np.sqrt(sum(a**2 for a in axes))
