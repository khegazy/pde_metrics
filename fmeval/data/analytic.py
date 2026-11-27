"""Datasets computed from closed-form solutions, evaluated on the fly.

A reader here opens no file: :meth:`ClosedFormTrajectory.read_frame` evaluates the
solution at the frame's time on the cell centres, so everything downstream -- remap,
calibration, the degradation ladder, metrics -- treats it exactly like a stored trajectory.
Nothing is written to disk; a frame is recomputed whenever it is read, which is exact and
cheap. Measured through ``Trajectory.frame``, validation included, on a NERSC login node:
0.3 ms per frame for Sod on 2048 cells and 1.8 ms for Taylor-Green on 256^2, against about
10 ms of I/O per kinet frame (``fmeval/pipeline.py``). Evaluating Taylor-Green's sines
directly took 7.0 ms, which is why its spatial patterns are computed once.

A reader may also supply a **candidate**: the same closed form with some of its parameters
changed (``candidate={"nu": 0.02}``), returned by :meth:`ClosedFormTrajectory.predictions` and
scored against the reader's own frames as a forecast is (``evaluate.py``,
``fmeval.pipeline.run(prediction=...)``). Both sides are exact, so the error of every metric at
every step is known in advance.

None is **evidence about a flow**. ``sod_shock_tube`` is in ``evidence_datasets`` as an
analytic check, for the metrics that need a shock or pressure; ``taylor_green_2d`` and
``advecting_blobs`` are fixtures for the harness only (``docs/decisions.md``); ``random_field``
is not registered. Their pages are ``docs/datasets/``.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

import numpy as np
from scipy.optimize import brentq

from degradations._shared.filters import _apply_filter
from fmeval.context import derive_rng
from fmeval.external.kinet_spectral import physical_wavenumber_grid, spectral_derivative
from fmeval.wavenumbers import wavenumber_magnitude

from .base import GridSpec, Trajectory, register_reader


def band_transfer(shape: tuple[int, int], k_min: float, k_max: float, slopes: Sequence[float],
                  k_break: float | None = None, anisotropy: float = 1.0) -> np.ndarray:
    """The transfer function ``T`` that makes ``_apply_filter(w, T)`` of unit white noise ``w`` a
    periodic Gaussian random field of unit expected mean square with a prescribed spectrum.

    On the modes of the band ``0 < k_min <= |k| <= k_max`` (cycles per domain) the per-mode
    variance is, with ``beta_1, beta_2`` the slopes and ``k`` evaluated at the stretched
    wavevector ``(a k_x, k_y / a)``,

        v(k) ~ k^-(beta_1 + 1) (1 + (k / k_break)^2)^(-(beta_2 - beta_1) / 2),

    and zero elsewhere. A shell of radius k holds about 2 pi k modes, so the shell spectrum
    falls as ``k^-beta_1``, and above ``k_break`` as ``k^-beta_2`` (``dataset_specs/09``, Sect.
    3.2; the per-mode form and the smooth break are this function's). One slope is a power law.
    ``slopes = (-1, 2 nu + 1)`` with ``k_break = 1 / (2 pi alpha)`` is the Matern spectral
    density ``(1 + alpha^2 kappa^2)^-(nu + 1)`` of two dimensions, ``kappa = 2 pi k`` on the unit
    domain (Porcu, Bevilacqua, Schaback & Oates 2023, arXiv:2303.02759, Eq. 23). The stretch
    multiplies every correlation length along x by ``a`` and divides those along y by it, a
    change of variables in the Fourier integral (spec 09, Sect. 3.4).

    Unit white noise has ``E|w_k|^2 = M`` over M cells, so the filtered field has expected mean
    square ``(1/M) sum T^2`` and covariance ``ifft(T^2)`` (spec 09, Eq. 2); ``T`` is scaled to
    make the first 1. The result is exactly Gaussian, being linear in ``w``.

    Raises:
        ValueError: If the band holds no mode of the grid or ``k_min <= 0``.
    """
    k = wavenumber_magnitude(shape)
    band = (k >= k_min) & (k <= k_max)
    if not band.any() or k_min <= 0:
        raise ValueError(f"the band 0 < k_min <= |k| <= k_max holds no mode of the grid {shape}, "
                         f"got k_min={k_min}, k_max={k_max}")
    stretched = wavenumber_magnitude(shape, (anisotropy, 1.0 / anisotropy))[band]
    power = np.zeros_like(k)
    power[band] = stretched ** -(slopes[0] + 1.0)
    if len(slopes) == 2:
        power[band] *= (1.0 + (stretched / k_break) ** 2) ** (-(slopes[1] - slopes[0]) / 2.0)
    return np.sqrt(power / power.mean())


def biot_savart(vorticity: np.ndarray, grid: GridSpec) -> np.ndarray:
    """The periodic velocity ``(2, X, Y)`` of a vorticity ``(X, Y)`` of zero mean: the stream
    function solves ``lap psi = -omega`` and ``u = (d_y psi, -d_x psi)``, spectrally
    (``dataset_specs/06``, Eq. 4). It is solenoidal, of zero mean, and its spectral curl returns
    the vorticity wherever no power sits on a Nyquist line."""
    k_squared = sum(k**2 for k in physical_wavenumber_grid(grid.shape, grid.spacing))
    k_squared[0, 0] = np.inf  # psi's mean is free; 1/inf = 0 sets it to zero
    psi = np.real(np.fft.ifftn(np.fft.fftn(vorticity) * (1.0 / k_squared)))
    return np.stack([spectral_derivative(psi, 1, spacing=grid.spacing),
                     -spectral_derivative(psi, 0, spacing=grid.spacing)])


class ClosedFormTrajectory(Trajectory):
    """A trajectory evaluated from a closed-form solution at cell centres.

    A subclass sets :attr:`FORMAT` and :attr:`FIELDS`, builds what it needs once in its
    constructor, and implements :meth:`solution`. Frames are evenly spaced in time from
    ``t_start`` to ``t_end`` inclusive. A subclass that accepts ``candidate`` names each
    parameter in ``params`` as its constructor's keyword, which :meth:`predictions` relies on.
    """

    reads_from_disk = False
    FORMAT: str
    FIELDS: tuple[str, ...]

    def __init__(self, *, grid: Sequence[int], length: Sequence[float],
                 boundary: Sequence[str], n_frames: int, t_start: float, t_end: float,
                 params: dict[str, Any], candidate: Mapping[str, Any] | None = None) -> None:
        """Build the grid, the cell centres and the time axis.

        Args:
            grid: Cells along each axis, in ``(x, y[, z])`` order.
            length: Physical extent of each axis.
            boundary: Boundary type of each axis, from :data:`fmeval.data.base.BOUNDARIES`.
            n_frames: Number of frames, at least one.
            t_start, t_end: First and last frame time; ``t_start <= t_end``.
            params: The solution's parameters, by the constructor's keyword names, recorded in
                :attr:`meta`.
            candidate: Parameters of ``params`` to change for the candidate of
                :meth:`predictions`; None for no candidate.

        Raises:
            ValueError: On an empty grid, a non-positive length, no frames, a reversed time
                window, or a candidate key that is not a parameter of the solution.
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
        unknown = sorted(set(candidate or {}) - set(params))
        if unknown:
            raise ValueError(f"candidate keys {unknown} are not parameters of the solution; "
                             f"it has {sorted(params)}")
        n = len(shape)
        spacing = tuple(float(extent) / cells for extent, cells in zip(length, shape))
        self._grid = GridSpec(shape=shape, spacing=spacing, boundary=tuple(boundary),
                              dims=("x", "y", "z")[:n], origin=(0.0,) * n)
        #: Cell-centre coordinates, one array of ``shape`` per axis.
        self.centres = np.meshgrid(*[(np.arange(cells) + 0.5) * dx
                                     for cells, dx in zip(shape, spacing)], indexing="ij")
        self._times = np.linspace(float(t_start), float(t_end), int(n_frames))
        self._meta = {"format": self.FORMAT, "path": None, **params}
        self._params, self._candidate = params, None if candidate is None else dict(candidate)

    def predictions(self) -> ClosedFormTrajectory | None:
        """The candidate: this solution with the candidate's parameters, on the same grid and
        frames, or None without one. Its constructor validates the changed parameters."""
        if self._candidate is None:
            return None
        return type(self)(grid=self._grid.shape, n_frames=len(self._times),
                          t_start=float(self._times[0]), t_end=float(self._times[-1]),
                          **{**self._params, **self._candidate})

    def frame_columns(self, t: int) -> dict[str, Any]:
        """With a candidate, every row is labelled as a forecast's is (``ForecastPairs``): the
        grid's resolution, and as the lead the frame's step and time since the first frame, the
        start every candidate shares."""
        if self._candidate is None:
            return {}
        return {"param_resolution": self._grid.shape[0], "lead_step": int(t),
                "lead_time": float(self._times[t] - self._times[0])}

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

    ``drift`` translates every field by ``drift * t`` at unchanged amplitude, a phase error
    growing linearly in time; the patterns are then recomputed per frame. It is meant for a
    candidate (``candidate={"drift": [0.01, 0.0]}``): the translated field solves the
    equations only with the uniform flow ``drift`` added, by Galilean invariance, so the
    reader's own frames keep the default of zero. A candidate with another ``nu`` is the
    wrong-viscosity candidate. The error of either against the truth is closed-form
    (``dataset_specs/05_initial_conditions_and_degraded_solver_runs.md``, Sect. 3.3), and
    ``tests/test_analytic_datasets.py`` asserts it for the thirteen per-step metrics.
    """

    FORMAT = "taylor_green_2d"
    FIELDS = ("velocity", "pressure", "vorticity")

    def __init__(self, path: str | None = None, *, nu: float = 0.01,
                 drift: Sequence[float] = (0.0, 0.0), grid: Sequence[int] = (256, 256),
                 n_frames: int = 10, t_start: float = 0.0, t_end: float = 50.0,
                 candidate: Mapping[str, Any] | None = None) -> None:
        """Cache the spatial patterns, unless they drift.

        Args:
            path: Ignored; accepted so every reader is constructed the same way.
            nu: Kinematic viscosity, non-negative.
            drift: Velocity ``(U_x, U_y)`` at which every field is translated.
            grid: Cells along ``(x, y)``.
            n_frames: Number of frames.
            t_start, t_end: The window.
            candidate: ``nu`` and ``drift`` of the candidate (:meth:`predictions`), or None.

        Raises:
            ValueError: On a negative viscosity, a drift that is not a pair, or an invalid
                grid, window or candidate.
        """
        if float(nu) < 0:
            raise ValueError(f"nu must be non-negative, got {nu}")
        if np.shape(drift) != (2,):
            raise ValueError(f"drift must be one (U_x, U_y) pair, got {drift}")
        super().__init__(grid=grid, length=(2 * np.pi, 2 * np.pi),
                         boundary=("periodic", "periodic"), n_frames=n_frames,
                         t_start=t_start, t_end=t_end, candidate=candidate,
                         params={"nu": float(nu), "drift": [float(d) for d in drift]})
        self._nu, self._drift = float(nu), np.asarray(drift, dtype=float)
        self._patterns = None if self._drift.any() else self._patterns_at(0.0)

    def _patterns_at(self, time: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Velocity, pressure and vorticity at unit amplitude, translated by ``drift * time``."""
        x, y = (c - u * time for c, u in zip(self.centres, self._drift, strict=True))
        return (np.stack([np.sin(x) * np.cos(y), -np.cos(x) * np.sin(y)]),
                (0.25 * (np.cos(2 * x) + np.cos(2 * y)))[None],
                (2.0 * np.sin(x) * np.sin(y))[None])

    def solution(self, time: float) -> dict[str, np.ndarray]:
        """Velocity, pressure and vorticity at ``time`` on the cell centres."""
        velocity, pressure, vorticity = self._patterns or self._patterns_at(time)
        decay = np.exp(-2.0 * self._nu * time)
        return {"velocity": velocity * decay, "pressure": pressure * decay**2,
                "vorticity": vorticity * decay}


@register_reader("advecting_blobs")
class AdvectingBlobs(ClosedFormTrajectory):
    """Gaussian density blobs, each carried at its own constant velocity on a periodic square,
    and, through its options, a population of vortices, fronts and bumps.

    A passive density on ``[0, 1)^2``: the uniform value 1 plus one Gaussian bump per velocity,

        rho(x, t) = 1 + a (w^2 / s) * sum_b exp(-|x - c_b - u_b t|^2 / (2 s)),
        s = w^2 + 2 kappa t,

    with ``|.|`` the periodic (minimum-image) distance, the centres ``c_b`` drawn uniformly from
    ``seed``, amplitude ``a``, width ``w`` and diffusivity ``kappa``. Each blob moves rigidly and
    spreads as the heat kernel spreads it: a Gaussian of variance ``w^2`` convolved with the
    kernel of ``d_t rho = kappa lap rho``, a Gaussian of variance ``2 kappa t``, is a Gaussian of
    variance ``s`` holding the same mass ``2 pi a w^2``. So this is the exact solution of the
    advection-diffusion equation for that velocity, blob by blob; a single uniform velocity
    would carry every blob alike. With distinct velocities the blobs' relative positions change,
    so an error measured on it changes from frame to frame; with one blob, or one velocity, it
    would not. It tests the time-dependent machinery, not physics (``docs/decisions.md``), and is
    not an evidence dataset.

    Periodic wrap-around is the minimum image only: at a width of 0.06 the bump has fallen to
    ``exp(-0.5^2 / (2 * 0.06^2)) = 8.3e-16`` of its peak at the half-domain distance, so the
    seam it leaves there is round-off. Diffusion widens the bump and the seam with it, to
    ``exp(-0.5^2 / (2 s))`` of the peak: 5e-15 at ``s = 0.0038``, 2e-10 at ``s = 0.0056``.

    A candidate (:meth:`predictions`) changes any of these parameters: other ``velocities`` are
    a wrong advection speed, another ``diffusivity`` a wrong diffusivity, both with the same
    starting blobs; zero velocities and diffusivity are persistence, and another ``seed`` an
    unrelated realisation (``dataset_specs/05_initial_conditions_and_degraded_solver_runs.md``,
    Sects. 3.1 and 3.4).

    **The feature population** (``dataset_specs/06_feature_population_generator.md``, Sect. 3).
    ``width``, ``amplitude``, ``centres``, ``kinds``, ``aspect``, ``orientation`` and
    ``directions`` are each one value shared by all features or one per velocity, and ``kinds``
    sends each feature to its field: a ``bump`` to density, a ``vortex`` to
    vorticity, a ``front`` to pressure. With ``x', y'`` the minimum-image offset from the
    feature's centre rotated by ``-orientation``, a bump or a vortex is the Gaussian above with
    variances ``s_1 = w^2 + 2 kappa t`` along ``x'`` and ``s_2 = (aspect w)^2 + 2 kappa t`` along
    ``y'``, of peak ``a w^2 aspect / sqrt(s_1 s_2)``; at ``aspect`` 1 and ``orientation`` 0 it is
    the blob, to the bit. A Gaussian vortex whose width grows as ``w^2 + 2 nu t`` is the
    Lamb-Oseen vortex (Gallay & Wayne 2005, Commun. Math. Phys. 255, 97-129,
    https://doi.org/10.1007/s00220-004-1254-9, Eqs. (7)-(8), the viscosity restored), so
    ``diffusivity`` is then the viscosity. A torus holds no net circulation, since the
    circulation round its boundary cancels edge against edge, so the stored vorticity is the sum
    minus its mean, and the velocity is its periodic Biot-Savart inversion, ``lap psi = -omega``,
    ``u = (d_y psi, -d_x psi)``, spectrally (spec 06, Eq. 4). A front adds
    ``a H(-phi / delta)`` to the pressure, ``H(z) = (1 + tanh z) / 2``, with ``delta`` equal to
    ``front_thickness`` cells of the finer axis and ``phi`` a level set negative inside: for a
    closed curve ``sqrt(aspect) (sqrt(x'^2 + (y'/aspect)^2) - w)``, the signed distance from a
    circle of radius ``w`` at ``aspect`` 1; for a straight stripe of half-width ``w`` along the
    coprime integer direction ``(p, q)`` of ``directions``, ``|((d + P/2) mod P) - P/2| - w``
    with ``d`` the offset along the unit normal and ``P = 1/sqrt(p^2 + q^2)`` the spacing of the
    line's periodic images (spec 06, Sect. 3.3). Density and pressure sit on the level 1, and
    ``background`` adds a static Gaussian random field to any of the three (below).

    Single-feature candidates are changed per-feature lists: a new entry of ``centres`` moves
    one feature, of ``velocities`` gives it a wrong speed, of ``amplitude`` rescales it, flips a
    vortex's sign, removes it (amplitude 0, which adds exactly 0.0 to every cell) or adds one
    the reference holds at amplitude 0; ``orientation`` or ``directions`` rotates one. Global
    candidates are degradations (``translate``, ``gain``, ...), not candidates. Features are
    summed wherever they overlap; the known answers of spec 06, Sect. 3.5, assume them isolated,
    and ``tests/test_analytic_datasets.py`` places them so.

    **A manufactured transport pair** (``dataset_specs/07_transport_known_answer_pairs.md``,
    Sect. 3.1). ``potential`` lists modes ``[m_x, m_y, a, phi]`` of a periodic potential

        u(x) = -sum_j (a_j / |k_j|^2) cos(k_j . x + phi_j),   k_j = 2 pi (m_x, m_y),

    (spec 07, Eq. 4), and the density becomes Saumier, Agueh & Khouider's (2015, IMA J. Appl.
    Math. 80(1), 135-157, Eq. 4) source density for the target ``g``, the density above:

        f(x) = g(x + grad u(x)) det(I + D^2 u(x)),

    with ``grad u`` and ``D^2 u`` in closed form and ``g``'s bumps evaluated exactly at the
    displaced points. ``sum_j |a_j| < 1`` bounds the operator norm of ``D^2 u`` below 1, so
    ``|x|^2 / 2 + u`` is convex and ``x + grad u`` is the optimal map from ``f`` to ``g`` on the
    torus, its displacement the shortest one (spec 07, Sect. 3.1, after McCann 2001, Geom.
    Funct. Anal. 11(3), and Cordero-Erausquin 1999, the latter through Saumier et al.'s
    Theorem 2.1). The exact distance is then the ``f``-weighted mean square of
    :attr:`displacement` (Saumier et al., Eq. 3; spec 07, Eq. 3). The candidate
    ``{potential: null}`` is ``g`` itself, and a plain reference with a ``potential`` candidate
    is the pair the other way round. With ``amplitude`` 0, ``g = 1``: one mode gives
    ``f = 1 + a cos(k . x + phi)`` at ``W_2 = a / (sqrt(2) |k|)`` (spec 07, Eq. 5), and two axis
    modes the product ``p(x) q(y)``. Only the density is mapped; vortices and fronts are not.
    """

    FORMAT = "advecting_blobs"
    FIELDS = ("density", "velocity", "vorticity", "pressure")
    #: The field each kind of feature is added to; a vortex's velocity follows from its vorticity.
    KINDS: ClassVar[dict[str, str]] = {"bump": "density", "vortex": "vorticity",
                                       "front": "pressure"}

    def __init__(self, path: str | None = None, *, grid: Sequence[int] = (64, 64),
                 n_frames: int = 21, t_start: float = 0.0, t_end: float = 10.0,
                 velocities: Sequence[Sequence[float]] = ((0.05, 0.0), (0.0, 0.08),
                                                          (-0.06, 0.04)),
                 width: float | Sequence[float] = 0.06,
                 amplitude: float | Sequence[float] = 0.1, diffusivity: float = 0.0,
                 seed: int = 0, centres: Sequence[Sequence[float]] | None = None,
                 kinds: str | Sequence[str] = "bump", aspect: float | Sequence[float] = 1.0,
                 orientation: float | Sequence[float] = 0.0,
                 directions: Sequence[Sequence[int]] | None = None,
                 front_thickness: float = 0.25, background: Mapping[str, Any] | None = None,
                 potential: Sequence[Sequence[float]] | None = None,
                 candidate: Mapping[str, Any] | None = None) -> None:
        """Lay out the features, draw any centres not given and the background.

        Args:
            path: Ignored; accepted so every reader is constructed the same way.
            grid: Cells along ``(x, y)``.
            n_frames: Number of frames.
            t_start, t_end: The window.
            velocities: One ``(u_x, u_y)`` per feature, in domain lengths per unit time; their
                number is the number of features.
            width: ``w``, in domain lengths: a Gaussian's width along ``x'``, a closed front's
                radius along ``x'``, a stripe's half-width.
            amplitude: ``a``: a bump's height or a front's pressure jump, non-negative; a
                vortex's signed peak vorticity.
            diffusivity: ``kappa``, non-negative, in squared domain lengths per unit time; it
                widens the Gaussians and is refused with a front, which it would not keep tanh.
            seed: Draws the starting centres when ``centres`` is None, and the background.
            centres: One starting ``(x, y)`` per feature, or None to draw them.
            kinds: ``bump``, ``vortex`` or ``front``.
            aspect: The width along ``y'`` over the width along ``x'``, positive.
            orientation: The angle of ``x'`` from the x axis, in radians.
            directions: Per front, the coprime integers ``(p, q)`` along which a straight stripe
                runs, or ``(0, 0)`` for a closed curve; None for closed curves only.
            front_thickness: ``delta`` in cells of the finer axis, positive.
            background: None, or ``{rms: {field: value}, slope: beta, k_min, k_max}``: for each
                of density, vorticity and pressure named, a periodic Gaussian random field of
                expected rms ``value`` whose modes with ``k_min <= |k| <= k_max`` (cycles per
                domain) have variance in proportion to ``|k|^-(beta + 1)``, so its shell
                spectrum falls as ``k^-beta`` (spec 06, Eq. 2; :func:`band_transfer` with one
                slope). It is the repository's one random-field draw, ``_apply_filter``
                applied to white noise from ``derive_rng(seed, "background", 0, field)``:
                exactly Gaussian with that covariance. It is static.
            potential: None, or modes ``[m_x, m_y, a, phi]``, integers ``m`` not both zero and
                ``sum |a| < 1``, mapping the density to the source of the transport pair above.
            candidate: Any of the parameters above from ``velocities`` on, changed for the
                candidate (:meth:`predictions`), or None.

        Raises:
            ValueError: On an option that is neither a scalar nor one value per velocity, a
                non-positive width, aspect or thickness, a negative bump or front amplitude, an
                unknown kind, a stripe direction that is not coprime integers on a front, a
                negative diffusivity or one with a front, an invalid background, an invalid
                potential or one with a density background (which has no closed form at the
                displaced points), or an invalid grid, window or candidate.
        """
        speeds = np.asarray(velocities, dtype=float)
        if speeds.ndim != 2 or speeds.shape[1] != 2 or len(speeds) == 0:
            raise ValueError(f"velocities must be one (u_x, u_y) pair per blob, got {velocities}")
        n = len(speeds)
        try:
            widths, amplitudes, aspects, angles = (
                np.broadcast_to(np.asarray(v, dtype=float), (n,))
                for v in (width, amplitude, aspect, orientation))
            kind = np.broadcast_to(np.asarray(kinds, dtype=str), (n,))
            lines = np.broadcast_to(np.asarray((0, 0) if directions is None else directions),
                                    (n, 2))
            starts = (np.random.default_rng(int(seed)).random((n, 2)) if centres is None
                      else np.broadcast_to(np.asarray(centres, dtype=float), (n, 2)))
        except ValueError as error:
            raise ValueError(f"every per-feature option must be a scalar or one value per "
                             f"velocity, of which there are {n}: {error}") from error
        stripe = lines.any(axis=1)
        if min(widths.min(), aspects.min(), float(front_thickness)) <= 0:
            raise ValueError(f"width, aspect and front_thickness must be positive, got {width}, "
                             f"{aspect}, {front_thickness}")
        if not set(kind) <= set(self.KINDS):
            raise ValueError(f"kinds must be among {sorted(self.KINDS)}, got {kinds}")
        if (amplitudes[kind != "vortex"] < 0).any():
            raise ValueError(f"a bump's or a front's amplitude must be non-negative, got "
                             f"{amplitude}")
        if not np.issubdtype(lines.dtype, np.integer) or (stripe & (kind != "front")).any() or (
                np.gcd(lines[stripe, 0], lines[stripe, 1]) != 1).any():
            raise ValueError(f"directions must be coprime integer pairs on fronts, (0, 0) "
                             f"elsewhere, got {directions}")
        if float(diffusivity) < 0 or (float(diffusivity) > 0 and (kind == "front").any()):
            raise ValueError(f"diffusivity must be non-negative, and zero with a front, got "
                             f"{diffusivity}")
        modes = None if potential is None else np.asarray(potential, dtype=float)
        if modes is not None and (
                modes.ndim != 2 or modes.shape[1] != 4 or len(modes) == 0
                or (modes[:, :2] != np.round(modes[:, :2])).any()
                or not modes[:, :2].any(axis=1).all() or np.abs(modes[:, 2]).sum() >= 1
                or "density" in (background or {}).get("rms", {})):
            raise ValueError(f"potential must be modes [m_x, m_y, a, phi] with integers m not both "
                             f"zero and sum |a| < 1, without a density background; got {potential}")
        super().__init__(grid=grid, length=(1.0, 1.0), boundary=("periodic", "periodic"),
                         n_frames=n_frames, t_start=t_start, t_end=t_end, candidate=candidate,
                         params={"velocities": speeds.tolist(),
                                 "width": np.asarray(width, dtype=float).tolist(),
                                 "amplitude": np.asarray(amplitude, dtype=float).tolist(),
                                 "diffusivity": float(diffusivity), "seed": int(seed),
                                 "centres": None if centres is None else starts.tolist(),
                                 "kinds": np.asarray(kinds).tolist(),
                                 "aspect": np.asarray(aspect, dtype=float).tolist(),
                                 "orientation": np.asarray(orientation, dtype=float).tolist(),
                                 "directions": None if directions is None else lines.tolist(),
                                 "front_thickness": float(front_thickness),
                                 "background": None if background is None else dict(background),
                                 "potential": None if modes is None else modes.tolist()})
        self._velocities, self._diffusivity, self._centres = speeds, float(diffusivity), starts
        self._features = list(zip(kind, widths, amplitudes, aspects, angles, lines, strict=True))
        self._thickness = float(front_thickness) * min(self._grid.spacing)

        #: ``grad u`` of ``potential`` at the cell centres, ``(2, X, Y)``; zero without one.
        self.displacement = np.zeros((2, *self._grid.shape))
        self._jacobian: float | np.ndarray = 1.0
        if modes is not None:
            k = 2.0 * np.pi * modes[:, :2]
            phase = np.einsum("jd,dxy->jxy", k, np.stack(self.centres)) + modes[:, 3, None, None]
            weight = modes[:, 2] / (k**2).sum(axis=1)  # a_j / |k_j|^2 of spec 07, Eq. 4
            self.displacement = np.einsum("j,jd,jxy->dxy", weight, k, np.sin(phase))
            hessian = np.einsum("j,jd,je,jxy->dexy", weight, k, k, np.cos(phase))
            self._jacobian = (1.0 + hessian[0, 0]) * (1.0 + hessian[1, 1]) - hessian[0, 1] ** 2
        self._displaced = [c + d for c, d in zip(self.centres, self.displacement, strict=True)]

        self._background: dict[str, np.ndarray] = {}
        if background is not None:
            if set(background) != {"rms", "slope", "k_min", "k_max"} or not (
                    set(background["rms"]) <= {"density", "vorticity", "pressure"}):
                raise ValueError(f"background must be {{rms: {{density|vorticity|pressure: "
                                 f"value}}, slope, k_min, k_max}}, got {background}")
            unit = band_transfer(self._grid.shape, float(background["k_min"]),
                                 float(background["k_max"]), (float(background["slope"]),))
            for name, rms in background["rms"].items():
                white = derive_rng(int(seed), "background", 0, name).standard_normal(
                    (1, *self._grid.shape))
                self._background[name] = _apply_filter(white, unit * float(rms))[0]

    def solution(self, time: float) -> dict[str, np.ndarray]:
        """Density, velocity, vorticity and pressure at ``time`` on the cell centres.

        Raises:
            ValueError: If the density or the pressure is not positive everywhere, which a
                background can cause; neither is then a thermodynamic field.
        """
        fields = {name: np.full_like(self.centres[0], level) + self._background.get(name, 0.0)
                  for name, level in (("density", 1.0), ("vorticity", 0.0), ("pressure", 1.0))}
        spread = 2.0 * self._diffusivity * time
        for (kind, w, a, eps, angle, line), centre, velocity in zip(
                self._features, self._centres, self._velocities, strict=True):
            position = (centre + velocity * time) % 1.0
            # A bump is evaluated at x + grad u, so the density is g(x + grad u) before the
            # Jacobian below (Saumier et al. 2015, Eq. 4); without a potential that is x.
            points = self._displaced if kind == "bump" else self.centres
            dx, dy = (((x - c + 0.5) % 1.0 - 0.5) for x, c in zip(points, position, strict=True))
            along = np.cos(angle) * dx + np.sin(angle) * dy
            across = np.cos(angle) * dy - np.sin(angle) * dx
            if kind != "front":
                # exp(-x'^2/(2 s_1) - y'^2/(2 s_2)), written so that s_1 = s_2 reproduces the
                # blob's exp(-|x|^2/(2 s)) and its peak a w^2/s bit for bit.
                s_1, s_2 = w**2 + spread, (eps * w) ** 2 + spread
                squared = along**2 + across**2 * (s_1 / s_2)
                peak = a * (w**2 / s_1) * np.sqrt(eps**2 * s_1 / s_2)
                fields[self.KINDS[kind]] += peak * np.exp(-squared / (2.0 * s_1))
                continue
            if line.any():
                period = 1.0 / np.hypot(*line)
                normal = (line[1] * dx - line[0] * dy) * period
                level = np.abs((normal + period / 2) % period - period / 2) - w
            else:
                level = np.sqrt(eps) * (np.hypot(along, across / eps) - w)
            fields["pressure"] += a * 0.5 * (1.0 + np.tanh(-level / self._thickness))
        fields["density"] *= self._jacobian  # det(I + D^2 u); exactly 1.0 without a potential
        if min(fields["density"].min(), fields["pressure"].min()) <= 0:
            raise ValueError(f"density or pressure is not positive at t={time}; lower the "
                             "background's rms")
        vorticity = fields["vorticity"] - fields["vorticity"].mean()
        return {"density": fields["density"][None], "velocity": biot_savart(vorticity, self._grid),
                "vorticity": vorticity[None], "pressure": fields["pressure"][None]}


@register_reader("random_field")
class RandomField(ClosedFormTrajectory):
    """Periodic random fields whose statistics are known before any metric is run
    (``dataset_specs/09_random_fields_known_statistics.md``): Gaussian fields of a prescribed
    spectrum, and three non-Gaussian families built from the same draw.

    On the unit square every frame filters unit white noise from
    ``derive_rng(seed, "random_field", frame, field)`` by :func:`band_transfer` through
    ``_apply_filter``, the repository's one random-field draw. That is a linear map of a Gaussian
    vector, so the result ``g`` is exactly Gaussian, with unit expected variance and the
    covariance ``ifft(T^2)`` on the grid itself (spec 09, Eqs. 1-2). Then:

    * **density** is ``1 + sigma g`` (``transform: none``), ``1 + sigma (g^2 - 1)``
      (``hermite2``), whose increments have flatness exactly 9 at every separation (spec 09,
      Eq. 8), or ``exp(sigma g - sigma^2 / 2)`` (``exp``), log-normal, whose increment moments
      are a finite sum (spec 09, Eq. 9);
    * **vorticity** is drawn the same way with the transfer ``|kappa| T`` (``kappa = 2 pi k``),
      and **velocity** is its Biot-Savart inversion (:func:`biot_savart`, through a stream
      function), so the velocity has the spectrum of ``T``, mean square ``velocity_rms^2`` per
      component when isotropic, zero divergence, and a spectral curl equal to the vorticity:
      ``k_max`` below every Nyquist line keeps that exact;
    * ``multifractal_lambda`` lambda > 0 replaces the vorticity's white noise by
      ``s exp(omega - V)``, with ``s`` independent white noise and ``omega`` a Gaussian field
      of per-mode variance ``v_k / M^2 = lambda / (2 pi (1 + |k|^2))``, whose covariance is
      ``lambda K_0(2 pi r)``, about ``-lambda ln r`` below the box size, and ``V`` its variance
      (spec 09, Sect. 3.6; the construction of Lakhal, Ponson, Benzaquen & Bouchaud 2025, Phys.
      Rev. Research 7, L012003, Eqs. 1-4 with their lambda, after Bacry, Delour & Muzy 2001,
      Phys. Rev. E 64, 026103, Eqs. 7-10). Being uncorrelated from cell to cell with unit
      variance, the noise keeps the Gaussian field's expected spectrum, and the flatness of the
      increments at every separation is a finite sum (spec 09, Eq. 11). Density is not changed;
    * ``spikes`` adds to the density, in each frame, ``floor`` times a Pareto variable of index
      ``alpha`` (``P(A > a) = a^-alpha`` for ``a >= 1``) at ``round(fraction M)`` cells drawn
      without replacement from ``derive_rng(seed, "spikes", frame, "density")``. Positive, so
      the density stays positive; each spike still makes one-cell increments of both signs. With
      the fraction at least ``2 / sqrt(M)`` and the floor above the largest Gaussian increment,
      the Hill estimate at ``k = sqrt(M)`` reads ``1 / alpha`` (spec 09, Sect. 3.7, measured
      there: at ``1 / (2 sqrt(M))`` it fails).

    **Frames.** With ``tau`` 0 every frame is an independent draw. With ``tau > 0`` each
    Fourier mode is an Ornstein-Uhlenbeck process of correlation time
    ``tau_k = tau (|k| / k_min)^-tau_exponent``, sampled exactly at the frame spacing ``dt``:
    ``g_{n+1} = a g_n + sqrt(1 - a^2) T w_{n+1}`` per mode, ``a = exp(-dt / tau_k)``, from the
    stationary law (spec 09, Eq. 7, its author's derivation from the process's Gaussian
    transition; Gillespie 1996, Phys. Rev. E 54, 2084). Every frame then has the law of an
    independent one, and each mode's correlation at a lag of n frames is ``a^n``; ``tau = inf``
    repeats the first frame, the persistence candidate. ``tau = 0`` is the same recursion with
    ``a = 0``. A frame is stepped forward from the last one read, so reading frames in order
    costs one step each; reading an earlier frame restarts from frame 0.

    One spectrum serves density and velocity: Eqs. (8), (9) and (11) of spec 09 are exact for
    any spectrum, so a second option would add no known answer. Not a flow: no cascade, flux
    or coherent structure (spec 09, Sect. 3.9); the known answers live in
    ``tests/test_analytic_datasets.py``.
    """

    FORMAT = "random_field"
    FIELDS = ("density", "velocity", "vorticity")
    TRANSFORMS: ClassVar[tuple[str, ...]] = ("none", "hermite2", "exp")

    def __init__(self, path: str | None = None, *, grid: Sequence[int] = (256, 256),
                 n_frames: int = 33, t_start: float = 0.0, t_end: float = 32.0,
                 slopes: float | Sequence[float] = (5.0 / 3.0,), k_break: float | None = None,
                 k_min: float = 4.0, k_max: float = 120.0, anisotropy: float = 1.0,
                 density_sigma: float = 0.05, transform: str = "none",
                 velocity_rms: float = 0.1, multifractal_lambda: float = 0.0,
                 tau: float = 0.0, tau_exponent: float = 2.0 / 3.0,
                 spikes: Mapping[str, float] | None = None, seed: int = 0,
                 candidate: Mapping[str, Any] | None = None) -> None:
        """Build the transfer functions and the per-mode decay; nothing is drawn yet.

        Args:
            path: Ignored; accepted so every reader is constructed the same way.
            grid: Cells along ``(x, y)`` of the unit square.
            n_frames: Number of frames.
            t_start, t_end: The window; only the frame spacing matters, and only with ``tau``.
            slopes: The shell spectrum's slope ``beta_1``, or ``(beta_1, beta_2)`` with
                ``k_break`` (:func:`band_transfer`). A Matern field of smoothness ``nu`` and
                length ``rho`` cells on N cells is ``(-1, 2 nu + 1)`` with
                ``k_break = N sqrt(2 nu) / (2 pi rho)``.
            k_break: The break, in cycles per domain, positive; None with one slope.
            k_min, k_max: The band, in cycles per domain; ``0 < k_min``, ``k_max`` below half the
                smaller grid extent, so no power sits on a Nyquist line.
            anisotropy: ``a`` of :func:`band_transfer`, positive; 1 is isotropic.
            density_sigma: ``sigma``, the density fluctuation's scale, non-negative.
            transform: ``none``, ``hermite2`` or ``exp``.
            velocity_rms: The velocity's root mean square per component when isotropic.
            multifractal_lambda: ``lambda``, non-negative; 0 keeps the velocity Gaussian.
            tau: The correlation time at ``k_min``, non-negative; 0 for independent frames.
            tau_exponent: ``p`` of the correlation time ``tau (|k| / k_min)^-p``.
            spikes: None, or ``{fraction, alpha, floor}``, each positive, fraction at most 1.
            seed: Draws every frame.
            candidate: Any parameter above from ``slopes`` on, changed for the candidate
                (:meth:`predictions`), or None.

        Raises:
            ValueError: On an option outside the ranges above, an unknown transform, a nonzero
                ``tau`` with a multifractal velocity (the recursion would mix independent
                chaos fields, whose law is not the one Eq. 11 describes), or an invalid band,
                grid, window or candidate.
        """
        slope_list = [float(b) for b in np.atleast_1d(slopes)]
        if len(slope_list) not in (1, 2) or (len(slope_list) == 2) != (k_break is not None) or (
                k_break is not None and float(k_break) <= 0):
            raise ValueError(f"slopes must be one value, or two with a positive k_break; got "
                             f"slopes={slopes}, k_break={k_break}")
        if not float(k_max) < min(int(n) for n in grid) / 2:
            raise ValueError(f"k_max={k_max} must lie below half the smaller extent of the grid "
                             f"{tuple(grid)}, or a spectral derivative meets a Nyquist line")
        if transform not in self.TRANSFORMS:
            raise ValueError(f"transform must be one of {self.TRANSFORMS}, got {transform!r}")
        if min(float(density_sigma), float(velocity_rms), float(multifractal_lambda),
               float(tau)) < 0 or float(anisotropy) <= 0:
            raise ValueError(f"density_sigma, velocity_rms, multifractal_lambda and tau must be "
                             f"non-negative and anisotropy positive, got {density_sigma}, "
                             f"{velocity_rms}, {multifractal_lambda}, {tau}, {anisotropy}")
        if float(tau) > 0 and float(multifractal_lambda) > 0:
            raise ValueError("tau > 0 is refused with a multifractal velocity")
        if spikes is not None and (set(spikes) != {"fraction", "alpha", "floor"} or min(
                float(v) for v in spikes.values()) <= 0 or float(spikes["fraction"]) > 1):
            raise ValueError(f"spikes must be {{fraction, alpha, floor}}, each positive and the "
                             f"fraction at most 1, got {spikes}")
        super().__init__(grid=grid, length=(1.0, 1.0), boundary=("periodic", "periodic"),
                         n_frames=n_frames, t_start=t_start, t_end=t_end, candidate=candidate,
                         params={"slopes": slope_list,
                                 "k_break": None if k_break is None else float(k_break),
                                 "k_min": float(k_min), "k_max": float(k_max),
                                 "anisotropy": float(anisotropy),
                                 "density_sigma": float(density_sigma), "transform": transform,
                                 "velocity_rms": float(velocity_rms),
                                 "multifractal_lambda": float(multifractal_lambda),
                                 "tau": float(tau), "tau_exponent": float(tau_exponent),
                                 "spikes": None if spikes is None else
                                 {key: float(value) for key, value in spikes.items()},
                                 "seed": int(seed)})
        shape = self._grid.shape
        k = wavenumber_magnitude(shape)
        unit = band_transfer(shape, float(k_min), float(k_max), slope_list,
                             None if k_break is None else float(k_break), float(anisotropy))
        #: The transfer function of each field's Gaussian draw, from which every second-order
        #: statistic follows: covariance ``ifft(T^2)``, spec 09, Eq. 2.
        self.transfers = {"density": unit,
                          "vorticity": 2.0 * np.pi * k * unit * np.sqrt(2.0) * float(velocity_rms)}
        #: The transfer function of the log-volatility ``omega``, or None for a Gaussian velocity.
        self.chaos_transfer = None
        if float(multifractal_lambda) > 0:
            self.chaos_transfer = np.sqrt(k.size * float(multifractal_lambda)
                                          / (2.0 * np.pi * (1.0 + k**2)))
            self.chaos_transfer[0, 0] = 0.0
        spacing = self._times[1] - self._times[0] if len(self._times) > 1 else 0.0
        #: Each mode's correlation from one frame to the next, ``exp(-dt / tau_k)``.
        self.decay = np.zeros_like(k)
        if float(tau) > 0:
            with np.errstate(divide="ignore"):
                correlation_time = float(tau) * (np.maximum(k, float(k_min)) / float(k_min)) ** (
                    -float(tau_exponent))
                self.decay = np.exp(-spacing / correlation_time)
        self._sigma, self._transform = float(density_sigma), transform
        self._spikes, self._seed = self._params["spikes"], int(seed)
        self._state: tuple[int, dict[str, np.ndarray]] | None = None

    def _noise(self, frame: int, name: str) -> np.ndarray:
        """The unit-variance noise ``(1, X, Y)`` a field's draw filters at ``frame``: white, or for
        a multifractal vorticity ``s exp(omega - V)`` from the same generator."""
        rng = derive_rng(self._seed, "random_field", frame, name)
        white = rng.standard_normal((1, *self._grid.shape))
        if name == "density" or self.chaos_transfer is None:
            return white
        omega = _apply_filter(rng.standard_normal((1, *self._grid.shape)), self.chaos_transfer)
        return white * np.exp(omega - np.mean(self.chaos_transfer**2))

    def solution(self, time: float) -> dict[str, np.ndarray]:
        """Density, velocity and vorticity of the frame at ``time``.

        Raises:
            ValueError: If the density is not positive everywhere, which a ``sigma`` too large
                for ``transform: none`` causes.
        """
        index = int(np.searchsorted(self._times, time))
        start = 0 if self.decay.any() else index
        if self._state is None or not start <= self._state[0] <= index:
            self._state = (start, {name: _apply_filter(self._noise(start, name), transfer)
                                   for name, transfer in self.transfers.items()})
        frame, gaussians = self._state
        innovation = np.sqrt(1.0 - self.decay**2)
        while frame < index:
            frame += 1
            gaussians = {name: _apply_filter(gaussians[name], self.decay) + _apply_filter(
                self._noise(frame, name), innovation * transfer)
                for name, transfer in self.transfers.items()}
        self._state = (frame, gaussians)

        g, sigma = gaussians["density"][0], self._sigma
        density = (1.0 + sigma * g if self._transform == "none"
                   else 1.0 + sigma * (g**2 - 1.0) if self._transform == "hermite2"
                   else np.exp(sigma * g - sigma**2 / 2.0))
        if self._spikes is not None:
            rng = derive_rng(self._seed, "spikes", index, "density")
            count = round(self._spikes["fraction"] * density.size)
            cells = rng.choice(density.size, count, replace=False)
            density.flat[cells] += self._spikes["floor"] * (rng.pareto(self._spikes["alpha"],
                                                                       count) + 1.0)
        if density.min() <= 0:
            raise ValueError(f"density is not positive at t={time}; lower density_sigma or use "
                             "transform: exp")
        vorticity = gaussians["vorticity"][0]
        return {"density": density[None], "velocity": biot_savart(vorticity, self._grid),
                "vorticity": vorticity[None]}
