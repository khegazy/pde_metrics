"""Spectral filtering, shared by the low-pass, high-pass and band operators.

The wavenumber magnitude is NOT defined here: every filter imports it from
:mod:`fmeval.wavenumbers`, because the filters and the severity calibration once used two
definitions and disagreed about which side of a cutoff the diagonal modes fell on.
"""

from __future__ import annotations

import numpy as np


def _apply_filter(x: np.ndarray, transfer: np.ndarray,
                  *, keep_mean: bool = False) -> np.ndarray:
    """Multiply each channel's spectrum by a real transfer function.

    Args:
        x: Field, ``(C, *spatial)``.
        transfer: Real transfer function on the spatial wavenumber grid.
        keep_mean: Force the k=0 mode through unchanged, preserving the spatial mean.
            Required for the high-pass family; see the note there.
    """
    spatial = tuple(range(1, x.ndim))
    if keep_mean:
        transfer = transfer.copy()
        transfer[(0,) * transfer.ndim] = 1.0
    spectrum = np.fft.fftn(x, axes=spatial)
    return np.real(np.fft.ifftn(spectrum * transfer, axes=spatial))


def butterworth(k: np.ndarray, cutoff: float, order: int) -> np.ndarray:
    """Low-pass Butterworth transfer ``1 / (1 + (k / k_c)^(2n))``; a high-pass is one minus it.

    The cutoff is floored at 1e-12 so a zero cutoff means "remove everything above k = 0" rather
    than a division by zero; the overflow that floor produces at large ``k`` is the intended
    limit of zero gain and is silenced.
    """
    with np.errstate(divide="ignore", over="ignore"):
        return 1.0 / (1.0 + (k / max(cutoff, 1e-12)) ** (2 * order))
