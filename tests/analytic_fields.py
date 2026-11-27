"""A test-only trajectory whose fields have metric responses known in closed form.

Three kinds, each a single feature on a non-square periodic grid ``(Nx, Ny)`` with unit spacing,
height ``h`` above a background, translated along x by ``d`` cells:

* ``bump`` -- a Gaussian of width ``w``, the reader's own (``AdvectingBlobs``, minimum image), so
  the repository has one definition of it. Its autocorrelation is Gaussian,
  ``C(d) = C0 exp(-d^2 / 4w^2)`` with ``C0 = pi w^2 h^2 / (Nx Ny)``, so
  ``MSE(d) = 2 (C(0) - C(d)) = 2 C0 (1 - exp(-d^2 / 4w^2))``, which is ``d^2 <(dg/dx)^2>`` for
  small d: quadratic. To leading order
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
from scipy import optimize

from fmeval.context import derive_rng
from fmeval.data.analytic import AdvectingBlobs
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
    w = _width(kind, width, shape)
    if kind == "bump":
        # Centred on cell (nx // 2, ny // 2). The reader's square is [0, 1)^2, where a cell is 1/nx
        # by 1/ny, so w cells is a width w/nx along x and an aspect nx/ny makes it w/ny along y.
        unit = AdvectingBlobs(grid=shape, n_frames=1, t_end=0.0, velocities=[(0.0, 0.0)],
                              centres=[((nx // 2 + 0.5) / nx, (ny // 2 + 0.5) / ny)],
                              width=w / nx, aspect=nx / ny, amplitude=1.0)
        feature = unit.frame(0, ["density"])["density"][0] - 1.0
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


def gaussian_mean_square(per_mode: np.ndarray) -> tuple[float, float]:
    """Expectation and standard deviation of the cell mean of ``f^2`` for one draw of a periodic
    stationary Gaussian field ``f`` with ``E|f_k|^2 / M^2 = per_mode`` and no power on a
    self-conjugate mode (k = 0 or a Nyquist corner), as a ``random_field`` draw has.

    By Parseval the cell mean is ``sum_k |f_k|^2 / M^2``. The modes k and -k carry one complex
    Gaussian coefficient between them, whose squared modulus is exponential with variance equal
    to its mean squared, and distinct pairs are independent; so the sum has mean
    ``sum q_k`` and variance ``sum over pairs (2 q_k)^2 = 2 sum_k q_k^2`` (our derivation,
    ``dataset_specs/09_random_fields_known_statistics.md``, Sect. 3.2, "Spectrum").
    """
    return float(per_mode.sum()), float(np.sqrt(2.0 * np.sum(per_mode**2)))


def circle_w2(f: np.ndarray, g: np.ndarray, length: float = 1.0) -> float:
    """The exact quadratic Wasserstein distance between two densities on a circle of ``length``,
    each read as constant on its cells (``len(f)`` equal cells, cell 0 starting at 0).

    Lift each cumulative distribution function to the line with ``F(x + L) = F(x) + 1``. The
    transport cost on the circle is the minimum over the rotation ``theta`` of mass levels of
    ``C(theta) = int_0^1 |F^-1(v) - G^-1(v + theta)|^2 dv`` (Delon, Salomon & Sobolevski 2010,
    SIAM J. Appl. Math. 70(7), 2239-2258, Eq. 14, convex in theta by the lemma opening their
    Sect. 5; Rabin, Delon & Gousseau 2011, J. Math. Imaging Vis. 41, Eq. 9). A cell-constant
    density has a quantile function linear between the cumulative cell masses, so on each
    interval between the merged knots of ``F^-1(v)`` and ``G^-1(v + theta)`` the difference is
    linear and its square integrates exactly, ``(v1 - v0)(d0^2 + d0 d1 + d1^2) / 3``. Each piece
    is evaluated from the cell its interval's midpoint falls in, so an empty cell, where the
    quantile function jumps, is exact too (``dataset_specs/07_transport_known_answer_pairs.md``,
    Sect. 3.2). The convex ``C`` is minimised by bounded Brent search over ``|theta| <= 1.5``,
    which holds the minimum (our argument): at the optimum the lift is the nearest one, so no
    mass moves more than ``L / 2``, which puts ``G^-1(theta)`` above ``-L / 2`` and
    ``G^-1(1 + theta)`` below ``3L / 2``, hence ``|theta| < 1``.

    Raises:
        ValueError: If the profiles differ in length, are not 1-D, or are negative or empty of
            mass.
    """
    f, g = (np.asarray(p, dtype=float) for p in (f, g))
    if f.ndim != 1 or f.shape != g.shape or min(f.min(), g.min()) < 0 or min(f.sum(), g.sum()) <= 0:
        raise ValueError(f"need two non-negative 1-D profiles of one length with mass, got shapes "
                         f"{f.shape} and {g.shape}")
    n, width = len(f), length / len(f)
    # Per profile, the cells whose mass the cumulative masses resolve: their indices and the mass
    # levels they span. A cell lighter than the round-off of a level near 1 counts as empty.
    cells = []
    for p in (f, g):
        c = np.concatenate([[0.0], np.cumsum(p)])
        c /= c[-1]  # by the running sum's own end, so the levels end at exactly 1
        kept = np.flatnonzero(np.diff(c) > 0)
        cells.append((kept, c[kept], c[kept + 1]))

    def piece(profile: int, middle: np.ndarray, ends: tuple[np.ndarray, ...]) -> list:
        """The lifted quantile function of ``profile``, on the linear piece holding mass level
        ``middle``, at each of ``ends``. The ends lie in that piece's cell; clipping the fraction
        of the cell to [0, 1] removes the round-off of ``ends`` against a cell of tiny mass."""
        kept, start, stop = cells[profile]
        period = np.floor(middle)
        j = np.clip(np.searchsorted(start, middle - period, side="right") - 1, 0, len(kept) - 1)
        return [(kept[j] + np.clip((e - period - start[j]) / (stop[j] - start[j]), 0.0, 1.0)
                 + period * n) * width for e in ends]

    def cost(theta: float) -> float:
        levels = [np.concatenate([[0.0], stop]) for _, _, stop in cells]
        lifted = (levels[1][None, :] - theta + np.arange(-2, 3)[:, None]).ravel()
        knots = np.unique(np.concatenate([levels[0], lifted[(lifted > 0) & (lifted < 1)]]))
        lo, hi = knots[:-1], knots[1:]
        f0, f1 = piece(0, (lo + hi) / 2, (lo, hi))
        g0, g1 = piece(1, (lo + hi) / 2 + theta, (lo + theta, hi + theta))
        d0, d1 = f0 - g0, f1 - g1
        return float(np.sum((hi - lo) * (d0**2 + d0 * d1 + d1**2)) / 3.0)

    best = optimize.minimize_scalar(cost, bounds=(-1.5, 1.5), method="bounded",
                                    options={"xatol": 1e-13})
    return float(np.sqrt(best.fun))


class AnalyticTrajectory(Trajectory):
    """An in-memory trajectory of integer rolls of :func:`canonical_field`, for the oracle tests."""

    def __init__(self, kind: str, *, grid: tuple[int, int] = SHAPE, n_frames: int = 4,
                 seed: int = 0, **field_params) -> None:
        _check(kind)
        self._kind, self._seed, self._n = kind, seed, n_frames
        self._canonical = canonical_field(kind, grid, **field_params)
        self._grid = GridSpec(tuple(grid), (1.0, 1.0), ("periodic", "periodic"), ("x", "y"),
                              (0.0, 0.0))

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
