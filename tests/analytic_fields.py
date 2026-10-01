"""A test-only trajectory whose fields have metric responses known in closed form.

Three kinds, each a single feature on a non-square periodic grid ``(Nx, Ny)`` with unit spacing,
height ``h`` above a background, translated along x by ``d`` cells:

* ``bump`` -- a Gaussian of width ``w``, periodised over the nearest images so it is smooth and
  periodic. Its autocorrelation is Gaussian, ``C(d) = C0 exp(-d^2 / 4w^2)`` with
  ``C0 = pi w^2 h^2 / (Nx Ny)``, so ``MSE(d) = 2 (C(0) - C(d)) = 2 C0 (1 - exp(-d^2 / 4w^2))``,
  which is ``d^2 <(dg/dx)^2>`` for small d: quadratic. To leading order
  ``MAE(d) = d <|dg/dx|> = d * 2 sqrt(2 pi) h w / (Nx Ny)``: linear.
* ``step`` -- a stripe of ``width`` cells raised by h, constant along y: a minimal shock with two
  edges. An integer shift ``d <= min(width, Nx - width)`` changes exactly ``2 d Ny`` cells by h, so
  ``MSE = 2 h^2 d / Nx`` and ``MAE = 2 h d / Nx``: both linear. (The research memo's ``h^2 d / L``
  counts one edge.) A fractional Fourier shift of a step rings, so only integer d has this form.
* ``mode`` -- ``h sin(k x)`` with ``k = 2 pi m / Nx``, constant along y.
  ``MSE = h^2 (1 - cos k d)``, quadratic for small ``k d`` and then saturating;
  ``MAE = (4 h / pi) sin(k d / 2)``. Under a periodic Gaussian blur the mode is multiplied by
  ``a = sum_j K_j cos(k j)`` over scipy's truncated, normalised kernel ``K``, so
  ``MSE = h^2 (1 - a)^2 / 2``.

Every frame is an integer roll of one canonical field, so every metric value is exactly the same in
every frame. A test fixture, not evidence: nothing measured on it says anything about turbulence.
"""

from __future__ import annotations

import numpy as np

from fmeval.context import derive_rng
from fmeval.data.base import GridSpec, Trajectory

KINDS = ("bump", "step", "mode")
SHAPE = (64, 32)

#: scipy.ndimage.gaussian_filter's default truncation, in standard deviations.
GAUSSIAN_TRUNCATE = 4.0


def _check(kind: str) -> None:
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r}; expected one of {KINDS}")


def _width(kind: str, width: float | None, shape: tuple[int, int]) -> float:
    """The bump's width in cells, or the stripe's plateau in cells."""
    if width is not None:
        return float(width)
    return 3.0 if kind == "bump" else float(shape[0] // 2)


def canonical_field(kind: str, shape: tuple[int, int] = SHAPE, *, width: float | None = None,
                    wavenumber: int = 3, height: float = 1.0,
                    background: float = 1.0) -> np.ndarray:
    """The field at offset zero, ``(1, Nx, Ny)``; every frame of the trajectory is a roll of it."""
    _check(kind)
    nx, ny = shape
    x = np.arange(nx, dtype=float)[:, None]
    y = np.arange(ny, dtype=float)[None, :]
    w = _width(kind, width, shape)
    if kind == "bump":
        feature = sum(
            np.exp(-((x - nx // 2 + a * nx) ** 2 + (y - ny // 2 + b * ny) ** 2) / (2 * w**2))
            for a in (-1, 0, 1) for b in (-1, 0, 1)
        )
    elif kind == "step":
        if not 0 < w < nx:
            raise ValueError(f"step width must lie strictly between 0 and {nx}; got {w}")
        feature = np.broadcast_to(((x >= 0) & (x < w)).astype(float), shape)
    else:
        if not 0 < wavenumber < nx / 2:
            raise ValueError(
                f"wavenumber must lie strictly between 0 and {nx / 2}; got {wavenumber}"
            )
        feature = np.broadcast_to(np.sin(2 * np.pi * wavenumber * x / nx), shape)
    return (background + height * feature)[None].astype(np.float64)


def _gaussian_attenuation(sigma: float, k: float) -> float:
    """The factor a periodic Gaussian blur multiplies cos(k x) by, with scipy's truncated kernel."""
    radius = int(GAUSSIAN_TRUNCATE * sigma + 0.5)
    j = np.arange(-radius, radius + 1)
    kernel = np.exp(-0.5 * j**2 / sigma**2)
    return float(np.sum(kernel / kernel.sum() * np.cos(k * j)))


def expected_response(kind: str, metric: str, degradation: str, severity: float, *,
                      shape: tuple[int, int] = SHAPE, width: float | None = None,
                      wavenumber: int = 3, height: float = 1.0) -> float:
    """The closed-form MSE or MAE of the displaced (or blurred) field against the canonical one."""
    _check(kind)
    nx, ny = shape
    k = 2 * np.pi * wavenumber / nx
    d = float(severity)
    if degradation == "translate_subpixel":
        if kind == "bump":
            w = _width(kind, width, shape)
            if metric == "mse":
                c0 = np.pi * w**2 * height**2 / (nx * ny)
                return float(2 * c0 * (1 - np.exp(-(d**2) / (4 * w**2))))
            return float(d * 2 * np.sqrt(2 * np.pi) * height * w / (nx * ny))
        if kind == "step":
            return float(2 * height**2 * d / nx if metric == "mse" else 2 * height * d / nx)
        if metric == "mse":
            return float(height**2 * (1 - np.cos(k * d)))
        return float(4 * height / np.pi * np.sin(k * d / 2))
    if degradation == "gaussian_blur" and kind == "mode" and metric == "mse":
        return float(height**2 * (1 - _gaussian_attenuation(d, k)) ** 2 / 2)
    raise ValueError(f"no closed form for {kind} / {metric} / {degradation}")


class AnalyticTrajectory(Trajectory):
    """An in-memory trajectory of integer rolls of :func:`canonical_field`, for the oracle tests."""

    def __init__(self, kind: str, *, grid: tuple[int, int] = SHAPE, n_frames: int = 4,
                 seed: int = 0, **field_params) -> None:
        _check(kind)
        self._kind, self._seed, self._n = kind, seed, n_frames
        self._canonical = canonical_field(kind, grid, **field_params)
        self._grid = GridSpec(tuple(grid), (1.0, 1.0), (True, True), ("x", "y"), (0.0, 0.0))

    @property
    def fields(self) -> tuple[str, ...]:
        return ("density",)

    @property
    def times(self) -> np.ndarray:
        return np.arange(self._n, dtype=np.float64)

    @property
    def grid(self) -> GridSpec:
        return self._grid

    @property
    def meta(self) -> dict:
        return {"format": "analytic", "kind": self._kind}

    def offset(self, t: int) -> tuple[int, int]:
        """The integer roll applied to frame ``t``."""
        rng = derive_rng(self._seed, "offset", t, self._kind)
        return int(rng.integers(self._grid.shape[0])), int(rng.integers(self._grid.shape[1]))

    def read_frame(self, t: int, fields):
        return {"density": np.roll(self._canonical, self.offset(t), axis=(1, 2))}
