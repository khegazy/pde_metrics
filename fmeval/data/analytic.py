"""Datasets computed from closed-form solutions, evaluated on the fly.

A reader here opens no file: :meth:`ClosedFormTrajectory.read_frame` evaluates the
solution at the frame's time on the cell centres, so everything downstream -- remap,
calibration, the degradation ladder, metrics -- treats it exactly like a stored trajectory.
Nothing is written to disk; a frame is recomputed whenever it is read, which is exact and
cheap. Measured through ``Trajectory.frame``, validation included, on a NERSC login node:
0.3 ms per frame for Sod on 2048 cells and 1.8 ms for Taylor-Green on 256^2, against about
10 ms of I/O per kinet frame (``fmeval/pipeline.py``). Evaluating Taylor-Green's sines
directly took 7.0 ms, which is why its spatial patterns are computed once.

Neither is **evidence about a flow**. ``sod_shock_tube`` is in ``evidence_datasets`` as an
analytic check, for the metrics that need a shock or pressure; ``taylor_green_2d`` is a
fixture for the harness only (``docs/decisions.md``). Their pages are ``docs/datasets/``.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy.optimize import brentq

from .base import GridSpec, Trajectory, register_reader


class ClosedFormTrajectory(Trajectory):
    """A trajectory evaluated from a closed-form solution at cell centres.

    A subclass sets :attr:`FORMAT` and :attr:`FIELDS`, builds what it needs once in its
    constructor, and implements :meth:`solution`. Frames are evenly spaced in time from
    ``t_start`` to ``t_end`` inclusive.
    """

    reads_from_disk = False
    FORMAT: str
    FIELDS: tuple[str, ...]

    def __init__(self, *, grid: Sequence[int], length: Sequence[float],
                 boundary: Sequence[str], n_frames: int, t_start: float, t_end: float,
                 params: dict[str, Any]) -> None:
        """Build the grid, the cell centres and the time axis.

        Args:
            grid: Cells along each axis, in ``(x, y[, z])`` order.
            length: Physical extent of each axis.
            boundary: Boundary type of each axis, from :data:`fmeval.data.base.BOUNDARIES`.
            n_frames: Number of frames, at least one.
            t_start, t_end: First and last frame time; ``t_start <= t_end``.
            params: The solution's parameters, recorded in :attr:`meta`.

        Raises:
            ValueError: On an empty grid, a non-positive length, no frames, or a reversed
                time window.
        """
        shape = tuple(int(n) for n in grid)
        if len(shape) != len(length) or any(n < 1 for n in shape):
            raise ValueError(f"grid {tuple(grid)} must have one positive extent per axis of "
                             f"length {tuple(length)}")
        if any(float(extent) <= 0 for extent in length):
            raise ValueError(f"every axis length must be positive, got {tuple(length)}")
        if int(n_frames) < 1:
            raise ValueError(f"n_frames must be >= 1, got {n_frames}")
        if not 0.0 <= float(t_start) <= float(t_end):
            raise ValueError(f"need 0 <= t_start <= t_end, got t_start={t_start}, t_end={t_end}")
        n = len(shape)
        spacing = tuple(float(extent) / cells for extent, cells in zip(length, shape))
        self._grid = GridSpec(shape=shape, spacing=spacing, boundary=tuple(boundary),
                              dims=("x", "y", "z")[:n], origin=(0.0,) * n)
        #: Cell-centre coordinates, one array of ``shape`` per axis.
        self.centres = np.meshgrid(*[(np.arange(cells) + 0.5) * dx
                                     for cells, dx in zip(shape, spacing)], indexing="ij")
        self._times = np.linspace(float(t_start), float(t_end), int(n_frames))
        self._meta = {"format": self.FORMAT, "path": None, **params}

    @property
    def fields(self) -> tuple[str, ...]:
        return self.FIELDS

    @property
    def times(self) -> np.ndarray:
        return self._times

    @property
    def grid(self) -> GridSpec:
        return self._grid

    @property
    def meta(self) -> dict[str, Any]:
        return self._meta

    def read_frame(self, t: int, fields: Sequence[str]) -> dict[str, np.ndarray]:
        """Evaluate the solution at ``times[t]`` and return the requested fields."""
        values = self.solution(float(self._times[t]))
        return {name: values[name] for name in fields}

    @abstractmethod
    def solution(self, time: float) -> dict[str, np.ndarray]:
        """Every field of :attr:`FIELDS` at ``time``, as ``(C, *spatial)`` arrays."""


@register_reader("sod_shock_tube")
class SodShockTube(ClosedFormTrajectory):
    """The exact solution of Sod's shock tube: 1D Euler equations, ideal gas, at rest.

    Sod (1978), J. Comput. Phys. 27(1), 1-31, https://doi.org/10.1016/0021-9991(78)90023-2
    poses the problem; the solution is Toro (2009), *Riemann Solvers and Numerical Methods
    for Fluid Dynamics*, 3rd ed., Springer, https://doi.org/10.1007/b79761, chapter 4.
    Equation numbers below are Toro's, verified against the book's text; its Table 4.1
    (Sect. 4.3.3) lists these initial states as Test 1, "the so called Sod test problem", and
    its Table 4.3 gives the exact star state ``p* = 0.30313, u* = 0.92745,
    rho*_L = 0.42632, rho*_R = 0.26557``, which ``tests/test_analytic_datasets.py`` checks.

    The domain is ``[0, 1)`` with the diaphragm at ``x = 0.5``, the high-pressure state on
    the left, and both states at rest. With zero velocities and ``p_left > p_right`` the
    wave pattern is always a left rarefaction, a contact and a right shock, so only those
    two branches are coded. The solution is exact until the first wave reaches an end of
    the domain; the constructor refuses a ``t_end`` at or past that time. Both ends are
    Neumann (zero-gradient) boundaries: no wave reaches them in the window, so the boundary
    type does not change the solution, and Neumann is the condition the kinet Sod runs use.
    """

    FORMAT = "sod_shock_tube"
    FIELDS = ("density", "velocity", "pressure")
    #: The diaphragm position on the unit domain.
    DIAPHRAGM = 0.5

    def __init__(self, path: str | None = None, *, gamma: float = 1.4,
                 left: Sequence[float] = (1.0, 1.0), right: Sequence[float] = (0.125, 0.1),
                 grid: Sequence[int] = (2048,), n_frames: int = 10, t_start: float = 0.1,
                 t_end: float = 0.2) -> None:
        """Solve for the star state once and fix the time window.

        Args:
            path: Ignored; accepted so every reader is constructed the same way.
            gamma: Ratio of specific heats, above 1.
            left, right: ``(density, pressure)`` of each initial state; both at rest.
            grid: Cells along x.
            n_frames: Number of frames.
            t_start, t_end: The window; ``t_start > 0`` because the solution is a function of
                ``(x - x0) / t``.

        Raises:
            ValueError: On a non-physical state, ``p_left <= p_right``, ``t_start <= 0``, or a
                ``t_end`` at or after the first wave reaches a boundary.
        """
        rho_l, p_l = (float(v) for v in left)
        rho_r, p_r = (float(v) for v in right)
        g = float(gamma)
        if g <= 1.0:
            raise ValueError(f"gamma must exceed 1, got {gamma}")
        if min(rho_l, p_l, rho_r, p_r) <= 0:
            raise ValueError(f"densities and pressures must be positive, got left={left}, "
                             f"right={right}")
        if p_l <= p_r:
            raise ValueError(f"the left pressure must exceed the right one for a left "
                             f"rarefaction and a right shock, got {p_l} <= {p_r}")
        if float(t_start) <= 0:
            raise ValueError(f"t_start must be positive, got {t_start}")
        super().__init__(grid=grid, length=(1.0,), boundary=("neumann",), n_frames=n_frames,
                         t_start=t_start, t_end=t_end,
                         params={"gamma": g, "left": [rho_l, p_l], "right": [rho_r, p_r]})

        c_l, c_r = np.sqrt(g * p_l / rho_l), np.sqrt(g * p_r / rho_r)
        a_r, b_r = 2.0 / ((g + 1.0) * rho_r), (g - 1.0) / (g + 1.0) * p_r

        def f_rarefaction(p: float) -> float:
            # Toro (2009) eq. (4.6), rarefaction branch (p <= p_L); a_L is the sound speed.
            return 2.0 * c_l / (g - 1.0) * ((p / p_l) ** ((g - 1.0) / (2.0 * g)) - 1.0)

        def f_shock(p: float) -> float:
            # Toro (2009) eq. (4.7), shock branch (p > p_R), with A_R and B_R of eq. (4.8).
            return (p - p_r) * np.sqrt(a_r / (p + b_r))

        # f is increasing in p, negative at p_r and positive at p_l, so the root is
        # bracketed by the two initial pressures. Toro (2009) eq. (4.5), with du = 0.
        # Star velocity, eq. (4.9): u* = (f_R - f_L)/2 = f_R, because f_L + f_R = 0 at the root.
        p_star = brentq(lambda p: f_rarefaction(p) + f_shock(p), p_r, p_l, xtol=1e-14,
                        rtol=4 * np.finfo(float).eps)
        u_star = float(f_shock(p_star))
        mu = (g - 1.0) / (g + 1.0)
        self.star = {
            "pressure": p_star,
            "velocity": u_star,
            # Toro (2009) eq. (4.53): behind the left rarefaction (isentropic).
            "density_left": rho_l * (p_star / p_l) ** (1.0 / g),
            # Toro (2009) eq. (4.57): behind the right shock.
            "density_right": rho_r * (p_star / p_r + mu) / (mu * p_star / p_r + 1.0),
        }
        self.speeds = {
            # Toro (2009) eq. (4.55), with the star sound speed a*_L of eq. (4.54).
            "head": -c_l,
            "tail": u_star - c_l * (p_star / p_l) ** ((g - 1.0) / (2.0 * g)),
            "contact": u_star,
            # Toro (2009) eq. (4.59).
            "shock": c_r * np.sqrt((g + 1.0) / (2.0 * g) * p_star / p_r + (g - 1.0) / (2.0 * g)),
        }
        self._gamma, self._left, self._right, self._c_left = g, (rho_l, p_l), (rho_r, p_r), c_l

        reach = min(self.DIAPHRAGM, 1.0 - self.DIAPHRAGM)
        t_wall = reach / max(self.speeds["shock"], -self.speeds["head"])
        if float(t_end) >= t_wall:
            raise ValueError(f"t_end={t_end} is at or after t={t_wall:.6g}, when the first "
                             "wave reaches a boundary and the solution is no longer exact")

    def solution(self, time: float) -> dict[str, np.ndarray]:
        """Density, velocity and pressure at ``time`` on the cell centres."""
        g, (rho_l, p_l), (rho_r, p_r), c_l = self._gamma, self._left, self._right, self._c_left
        s = self.speeds
        xi = (self.centres[0] - self.DIAPHRAGM) / time
        # Inside the fan; clipped so the formula is evaluated only where it holds and never
        # raises a negative sound speed to a fractional power elsewhere.
        # Toro (2009) eq. (4.56): the state inside the left rarefaction fan.
        fan = np.clip(xi, s["head"], s["tail"])
        c = 2.0 / (g + 1.0) * (c_l - 0.5 * (g - 1.0) * fan)
        regions = [xi < s["head"], xi < s["tail"], xi < s["contact"], xi < s["shock"]]
        density = np.select(regions, [rho_l, rho_l * (c / c_l) ** (2.0 / (g - 1.0)),
                                      self.star["density_left"], self.star["density_right"]],
                            rho_r)
        velocity = np.select(regions[:2] + regions[3:],
                             [0.0, 2.0 / (g + 1.0) * (c_l + fan), self.star["velocity"]], 0.0)
        pressure = np.select(regions[:2] + regions[3:],
                             [p_l, p_l * (c / c_l) ** (2.0 * g / (g - 1.0)), self.star["pressure"]],
                             p_r)
        return {"density": density[None], "velocity": velocity[None], "pressure": pressure[None]}


@register_reader("taylor_green_2d")
class TaylorGreen2D(ClosedFormTrajectory):
    """The decaying two-dimensional Taylor-Green vortex: incompressible Navier-Stokes.

    Taylor (1923), "On the decay of vortices in a viscous fluid", Phil. Mag. (6) 46(274),
    671-674, https://doi.org/10.1080/14786442308634295, gives the stream function
    ``psi = A cos(pi x/d) cos(pi y/d) exp(-2 pi^2 nu t / d^2)`` (p. 674) with
    ``u = -dpsi/dy, v = dpsi/dx`` (p. 672). With ``d = pi`` and ``A = 1``, Taylor's velocity
    ``(u_T, v_T)`` and the one below satisfy ``u(x, y) = u_T(x - pi/2, y + pi/2)``, likewise
    for ``v``: the same flow, translated (our derivation, checked numerically). Taylor gives no
    pressure; the one here is derived from the momentum equation, as the next paragraph says.
    On ``[0, 2 pi)^2``, density 1::

        u =  sin x cos y e^(-2 nu t),   v = -cos x sin y e^(-2 nu t)
        p = (cos 2x + cos 2y) e^(-4 nu t) / 4
        omega = dv/dx - du/dy = 2 sin x sin y e^(-2 nu t)

    The pressure sign is fixed by the momentum equation: ``(u . grad) u`` has x-component
    ``sin(2x)/2`` at ``t = 0``, so ``-dp/dx = sin(2x)/2``; ``tests/test_analytic_datasets.py``
    checks the full residual. The solution separates into a fixed spatial pattern times a
    decay factor, so the patterns are computed once here and each frame only rescales them.
    Vorticity is the closed form, kept as the cross-check the harness's own recomputation
    from velocity is tested against, exactly as a solver's stored vorticity is.
    """

    FORMAT = "taylor_green_2d"
    FIELDS = ("velocity", "pressure", "vorticity")

    def __init__(self, path: str | None = None, *, nu: float = 0.01,
                 grid: Sequence[int] = (256, 256), n_frames: int = 10, t_start: float = 0.0,
                 t_end: float = 50.0) -> None:
        """Cache the spatial patterns.

        Args:
            path: Ignored; accepted so every reader is constructed the same way.
            nu: Kinematic viscosity, non-negative.
            grid: Cells along ``(x, y)``.
            n_frames: Number of frames.
            t_start, t_end: The window.

        Raises:
            ValueError: On a negative viscosity or an invalid grid or window.
        """
        if float(nu) < 0:
            raise ValueError(f"nu must be non-negative, got {nu}")
        super().__init__(grid=grid, length=(2 * np.pi, 2 * np.pi),
                         boundary=("periodic", "periodic"), n_frames=n_frames,
                         t_start=t_start, t_end=t_end, params={"nu": float(nu)})
        self._nu = float(nu)
        x, y = self.centres
        self._velocity = np.stack([np.sin(x) * np.cos(y), -np.cos(x) * np.sin(y)])
        self._pressure = (0.25 * (np.cos(2 * x) + np.cos(2 * y)))[None]
        self._vorticity = (2.0 * np.sin(x) * np.sin(y))[None]

    def solution(self, time: float) -> dict[str, np.ndarray]:
        """Velocity, pressure and vorticity at ``time`` on the cell centres."""
        decay = np.exp(-2.0 * self._nu * time)
        return {"velocity": self._velocity * decay, "pressure": self._pressure * decay**2,
                "vorticity": self._vorticity * decay}
