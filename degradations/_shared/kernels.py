"""Kernel construction and convolution, shared by the smoothing operators.

Every kernel here wraps at the boundary, matching the doubly periodic domain.
"""

from __future__ import annotations

import numpy as np


def _radial_kernel(radius: float, n_spatial: int, profile: str) -> np.ndarray:
    """Build a normalised isotropic kernel of the given profile."""
    r = int(np.ceil(radius))
    axes = np.meshgrid(*[np.arange(-r, r + 1)] * n_spatial, indexing="ij")
    dist = np.sqrt(sum(a.astype(float) ** 2 for a in axes))
    u = dist / radius
    if profile == "disk":
        k = (u <= 1.0).astype(float)
    elif profile == "epanechnikov":
        # Epanechnikov: 3/4 (1 - u^2) on |u| <= 1; the MSE-optimal smoothing kernel.
        k = np.where(u <= 1.0, 0.75 * (1.0 - u**2), 0.0)
    else:  # pragma: no cover - guarded by the caller
        raise ValueError(f"unknown kernel profile {profile!r}")
    total = k.sum()
    if total == 0:
        raise ValueError(f"kernel with radius {radius} is empty")
    return k / total


def _window_filter(x: np.ndarray, severity: float, ctx, filt) -> np.ndarray:
    """Apply a ``scipy.ndimage`` window filter of odd width over the spatial axes, wrapping.

    ``filt`` is ``uniform_filter`` or ``median_filter``. The calibrated width ``severity`` is
    rounded to the nearest integer and an even result is raised by one, so the window is always
    odd; a width of one or less is the identity.

    A window of even width has no centre cell, so ``uniform_filter`` and ``median_filter``
    place it asymmetrically and the output is displaced by half a cell. For a project whose
    central concern is that metrics over-punish displacement, that shift dominates: measured on
    vorticity, windows of 2, 3, 6 and 13 cells give damage 0.0121, 0.0041, 0.0338, 0.0880 --
    non-monotone, because each even window carries a half-cell shift the odd ones do not.
    Rounding to odd removes the artefact and the axis is monotone.
    """
    width = int(round(severity))
    if width <= 1:
        return x
    width += 1 - width % 2
    size = [1] * x.ndim
    for axis in ctx.spatial_axes:
        size[axis] = width
    return filt(x, size=size, mode="wrap")


def _radial_blur(x: np.ndarray, severity: float, ctx, profile: str) -> np.ndarray:
    """Convolve with a normalised isotropic kernel of radius ``severity``; identity below 1.

    The boundary wraps, so the convolution is circular and is computed by FFT: the centred
    kernel is folded onto the periodic grid (offsets taken modulo each axis's length, so a
    kernel wider than the grid wraps as it does in a direct periodic convolution) and
    multiplied in Fourier space, channel by channel. A direct convolution gives the same field
    to round-off at a cost growing with the kernel's area; on 256^2 with a radius of 47 cells it
    took about 4.4 s per frame.
    """
    if severity < 1:
        return x
    kernel = _radial_kernel(severity, ctx.grid.n_spatial, profile)
    spatial = x.shape[1:]
    offsets = np.indices(kernel.shape).reshape(kernel.ndim, -1) \
        - (np.array(kernel.shape) // 2)[:, None]
    folded = np.zeros(spatial)
    np.add.at(folded, tuple(offsets % np.array(spatial)[:, None]), kernel.ravel())
    axes = tuple(range(1, x.ndim))
    return np.fft.irfftn(np.fft.rfftn(x, axes=axes) * np.fft.rfftn(folded)[None],
                         s=spatial, axes=axes)
