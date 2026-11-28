"""Datasets computed from closed-form solutions, evaluated on the fly.

A reader here opens no file: :meth:`ClosedFormTrajectory.read_frame` evaluates the
solution at the frame's time on the cell centres, so everything downstream -- remap,
calibration, the degradation ladder, metrics -- treats it exactly like a stored trajectory.
Nothing is written to disk; a frame is recomputed whenever it is read, which is exact and
cheap. Measured through ``Trajectory.frame``, validation included, on a NERSC login node:
0.3 ms per frame for Sod on 2048 cells and 1.8 ms for Taylor-Green on 256^2, against about
10 ms of I/O per kinet frame (``fmeval/pipeline.py``). Evaluating Taylor-Green's sines
directly took 7.0 ms, which is why its spatial patterns are computed once. The two exceptions
are ``taylor_green_kinet`` and ``sod_kinet``, which take their cells and clock from a kinet run of
the problem and open that run as their candidate.

A reader may also supply a **candidate**: the same closed form with some of its parameters
changed (``candidate={"nu": 0.02}``), returned by :meth:`ClosedFormTrajectory.predictions` and
scored against the reader's own frames as a forecast is (``evaluate.py``,
``fmeval.pipeline.run(prediction=...)``). Both sides are exact, so the error of every metric at
every step is known in advance.

None is **evidence about a flow**. ``sod_shock_tube``, ``burgers``, ``sedov_taylor``, ``noh``,
``random_field``, ``advecting_blobs`` and the ``feature_population``, ``transport_pairs`` and
``helmholtz_mixture_2d`` configurations are in ``evidence_datasets``, each under a label saying
it is an analytic check or a known-statistics null and nothing about turbulence;
``taylor_green_2d`` is a fixture for the harness only (``docs/decisions.md``). The
``taylor_green_kinet`` and ``sod_kinet`` configurations are evidence of a solver's observed order
on a grid sequence. Their pages are ``docs/datasets/``.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from scipy.special import ive

from degradations._shared.filters import _apply_filter
from fmeval.context import derive_rng
from fmeval.external.kinet_spectral import physical_wavenumber_grid, spectral_derivative
from fmeval.wavenumbers import wavenumber_magnitude

from .base import GridSpec, Trajectory, register_reader
from .kinet_raw import KinetRawTrajectory


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
        """With a candidate, every row is labelled as a forecast's, with this grid's resolution."""
        return {} if self._candidate is None else self._candidate_columns(t, self._grid.shape[0])

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

    ``time_offset`` evaluates every frame at ``t + time_offset``: the diaphragm burst at
    ``-time_offset``. As a candidate (``candidate={"time_offset": dt}``) it is the exact solution
    at a shifted time, so every jump keeps its exact size and each wave is displaced by its own
    speed times ``dt`` (``dataset_specs/03_two_dimensional_shocks.md``, Sect. 3.6).
    """

    FORMAT = "sod_shock_tube"
    FIELDS = ("density", "velocity", "pressure")
    #: The diaphragm position on the unit domain.
    DIAPHRAGM = 0.5

    def __init__(self, path: str | None = None, *, gamma: float = 1.4,
                 left: Sequence[float] = (1.0, 1.0), right: Sequence[float] = (0.125, 0.1),
                 time_offset: float = 0.0, grid: Sequence[int] = (2048,), n_frames: int = 10,
                 t_start: float = 0.1, t_end: float = 0.2,
                 candidate: Mapping[str, Any] | None = None) -> None:
        """Solve for the star state once and fix the time window.

        Args:
            path: Ignored; accepted so every reader is constructed the same way.
            gamma: Ratio of specific heats, above 1.
            left, right: ``(density, pressure)`` of each initial state; both at rest.
            time_offset: Added to every frame's time before the solution is evaluated.
            grid: Cells along x.
            n_frames: Number of frames.
            t_start, t_end: The window; ``t_start + time_offset > 0`` because the solution is a
                function of ``(x - x0) / t``.
            candidate: Any of ``gamma``, ``left``, ``right``, ``time_offset``, changed for the
                candidate (:meth:`predictions`), or None.

        Raises:
            ValueError: On a non-physical state, ``p_left <= p_right``,
                ``t_start + time_offset <= 0``, a ``t_end + time_offset`` at or after the first
                wave reaches a boundary, or an invalid candidate.
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
        offset = float(time_offset)
        if float(t_start) + offset <= 0:
            raise ValueError(f"t_start + time_offset must be positive, got {t_start} + {offset}")
        super().__init__(grid=grid, length=(1.0,), boundary=("neumann",), n_frames=n_frames,
                         t_start=t_start, t_end=t_end, candidate=candidate,
                         params={"gamma": g, "left": [rho_l, p_l], "right": [rho_r, p_r],
                                 "time_offset": offset})
        self._offset = offset

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
        if float(t_end) + offset >= t_wall:
            raise ValueError(f"t_end + time_offset = {float(t_end) + offset} is at or after "
                             f"t={t_wall:.6g}, when the first wave reaches a boundary and the "
                             "solution is no longer exact")

    def solution(self, time: float) -> dict[str, np.ndarray]:
        """Density, velocity and pressure at ``time + time_offset`` on the cell centres."""
        g, (rho_l, p_l), (rho_r, p_r), c_l = self._gamma, self._left, self._right, self._c_left
        s = self.speeds
        xi = (self.centres[0] - self.DIAPHRAGM) / (time + self._offset)
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


@register_reader("sod_kinet")
class SodKinet(SodShockTube):
    """The exact Sod solution on the cells and clock of a kinet run of it, the run its candidate.

    kinet's ``sod`` cases fill a tube of ``N`` by a few transverse nodes, cell ``i`` centred at
    ``i + 1/2`` cells, with the left state where ``i + 1/2 < N / 2``: for odd ``N`` the diaphragm
    is the face ``x0 = (N - 1) / 2``, half a cell left of the tube's middle (read here from the
    stored initial density and refused elsewhere). Both states are at rest and every field is
    uniform across the tube, with no transverse velocity. Read with
    ``KinetRawTrajectory(cell=1 / (N - 1))``, the run is in units where ``N - 1`` cells and
    ``N - 1`` solver steps are one, so the diaphragm sits at :attr:`DIAPHRAGM` 0.5, the waves
    keep their lattice speeds, and runs on ``N = 751, 1501, 3001`` nodes are nested grids of
    exactly halved cells whose frames ``k`` share one time. The exact solution is a function of
    ``(x - 0.5) / t = (i + 1/2 - x0) / s`` after ``s`` steps (Toro 2009, Sect. 4.2), so it is
    evaluated at the run's cell centres and times with the run's own initial states and
    ``gamma``, and :meth:`predictions` is the run, scored against it as a candidate is, its rows
    labelled with ``param_resolution`` N. The tube reaches 1 + 1/(N - 1), so the wall check of
    :class:`SodShockTube` (the first wave at 0 or 1) holds with room on the right.

    Frame 0 is the run's initial condition, where the solution is the bare jump: ``(x - 0.5) / 0``
    is infinite on every cell, since no cell centre is the face 0.5.
    """

    reads_from_disk = True
    FORMAT = "sod_kinet"
    #: The tube: kinet's ``neuman`` faces at both ends; across it, which kinet's ``sod`` cases
    #: leave periodic, every field is uniform, so any extension is exact.
    BOUNDARY: ClassVar[tuple[str, str]] = ("neumann", "periodic")

    def __init__(self, path: str | Path) -> None:
        """Read the run's states, diaphragm, cells and clock, and the exact solution on them.

        Args:
            path: A kinet ``sod`` run in the flat layout, converted by
                ``fmeval.data.convert_kinet``, or its published URL.

        Raises:
            ValueError: If the run is not kinet's two-dimensional Sod tube, its initial density
                is not one jump at the face ``(N - 1) / 2``, or :class:`SodShockTube` refuses
                its states or its last time.
        """
        with KinetRawTrajectory(path, include_redundant=True) as lattice:
            group, n = lattice.meta["source_attrs"].get("group"), lattice.grid.shape[0]
            gamma = lattice.meta["source_attrs"].get("gamma")
            start = lattice.frame(0, ["density", "pressure"]).fields
        density, pressure = start["density"][0, :, 0], start["pressure"][0, :, 0]
        right = np.flatnonzero(density != density[0])
        if (group != "sod" or gamma is None or lattice.grid.n_spatial != 2 or n % 2 == 0
                or not np.array_equal(right, np.arange((n - 1) // 2, n))):
            raise ValueError(f"{path}: a kinet sod run on an odd number of nodes with one jump "
                             f"at the face (N - 1) / 2 is needed; this is {group!r} on "
                             f"{lattice.grid.shape} with the right state from node "
                             f"{right[:1].tolist()}")
        self._path, self._cell = path, 1.0 / (n - 1)
        with self.predictions() as run:
            # t_start is the first time after the jump, for the parent's checks; the frames are
            # the run's own, frame 0 included, because the pipeline pairs equal clocks only.
            super().__init__(gamma=gamma, left=(density[0], pressure[0]),
                             right=(density[-1], pressure[-1]), grid=(n,), n_frames=len(run),
                             t_start=float(run.times[1]), t_end=float(run.times[-1]),
                             candidate={})  # an empty candidate labels the rows as a candidate's
            self._grid, self._times = run.grid, run.times
        self.centres = [np.broadcast_to(((np.arange(n) + 0.5) * self._cell)[:, None],
                                        self._grid.shape)]
        self._meta["path"] = str(path)

    def solution(self, time: float) -> dict[str, np.ndarray]:
        """The tube's solution on every transverse node, with a zero transverse velocity."""
        with np.errstate(divide="ignore"):  # at t = 0, the jump (class docstring)
            fields = super().solution(time)
        fields["velocity"] = np.concatenate([fields["velocity"], 0 * fields["velocity"]])
        return fields

    def predictions(self) -> KinetRawTrajectory:
        """The run, on this reader's cells and clock and in its units."""
        return KinetRawTrajectory(self._path, include_redundant=True, boundary=self.BOUNDARY,
                                  cell=self._cell)


@register_reader("burgers")
class Burgers(ClosedFormTrajectory):
    """Viscous Burgers' equation ``u_t + u u_x = nu u_xx`` on the periodic ``[0, 2 pi)``, from
    ``u(x, 0) = -sin x``, solved exactly by the Cole-Hopf transformation.

    ``u = -2 nu psi_x / psi`` maps every positive solution of the heat equation
    ``psi_t = nu psi_xx`` to a solution of Burgers' equation (Gesztesy & Holden 1998, "The
    Cole-Hopf and Miura transformations revisited", arXiv:solv-int/9812025, Lemma 3.1 and
    Eqs. 3.1-3.2). The initial condition needs ``psi(x, 0) = exp(-cos x / (2 nu))``, which with
    ``a = 1 / (2 nu)`` is ``exp(a cos(x - pi))`` and so, by the expansion
    ``exp(z cos theta) = I_0(z) + 2 sum_n I_n(z) cos(n theta)`` (DLMF 10.35.2), a Fourier
    series whose modes the heat equation damps one by one::

        psi = I_0(a) + 2 sum_{n>=1} (-1)^n I_n(a) exp(-nu n^2 t) cos(n x)
        u   = 4 nu sum_{n>=1} n (-1)^n I_n(a) exp(-nu n^2 t) sin(n x) / psi

    (``dataset_specs/02_grid_refinement_known_solution.md``, Sect. 4.5; the series is that
    spec author's derivation, re-derived here). The Bessel functions enter only as ratios
    ``I_n(a) / I_0(a)``, computed from the scaled ``ive`` so nothing overflows; the first
    :attr:`TERMS` modes are kept. Checked against the heat-kernel integral of the same
    transformation by quadrature (max difference 5e-13 at ``nu = 0.1``, t = 0.5 to 2), and
    ``tests/test_analytic_datasets.py`` checks the equation's residual.

    The series cancels: at ``t = 0`` the denominator falls to ``exp(-2a)`` of its largest
    term, so round-off grows as ``eps exp(1 / nu)``. Measured at ``nu = 0.1``, 0.05 and 0.03:
    1e-12, 2e-8 and 7e-4 against ``-sin x`` at ``t = 0``, and 5e-13, 9e-9 and 1e-3 against the
    quadrature at ``t = 0.5``; so the reader refuses a viscosity below :attr:`MIN_NU`.

    ``scheme="central"`` replaces the closed form with a numerical solution on the reader's own
    cells, as a candidate (``candidate={"scheme": "central"}``) whose order of accuracy is
    known: second-order centred differences of the flux ``u^2 / 2`` and of ``u_xx``, whose
    truncation errors are ``h^2 (u^2/2)''' / 6`` and ``nu h^2 u'''' / 12``, integrated in time
    by ``solve_ivp`` (DOP853) at a tolerance whose time error, 7e-12 at t = 2 on 512 cells, is
    far below the spatial one, 5e-5. Its error against the exact solution falls as ``h^2``, so
    the observed order (Roy 2005, J. Comput. Phys. 205(1), 131-156, Eq. 8) of ``rmse`` and
    ``max_error`` over a grid sequence of ratio 2 is 2. It is the degraded-solver candidate of
    ``dataset_specs/05_initial_conditions_and_degraded_solver_runs.md`` in miniature.
    """

    FORMAT = "burgers"
    FIELDS = ("velocity",)
    #: Fourier modes kept: at ``nu = MIN_NU`` the next ratio ``I_60(10) / I_0(10)`` is 6e-44.
    TERMS = 60
    #: The smallest viscosity at which the series' round-off stays near 2e-8 (see above).
    MIN_NU = 0.05
    SCHEMES = ("exact", "central")

    def __init__(self, path: str | None = None, *, nu: float = 0.1, scheme: str = "exact",
                 grid: Sequence[int] = (256,), n_frames: int = 4, t_start: float = 0.5,
                 t_end: float = 2.0, candidate: Mapping[str, Any] | None = None) -> None:
        """Compute the series' coefficients once.

        Args:
            path: Ignored; accepted so every reader is constructed the same way.
            nu: Viscosity, at least :attr:`MIN_NU`.
            scheme: ``"exact"`` for the closed form, ``"central"`` for the numerical solution.
            grid: Cells along x.
            n_frames: Number of frames.
            t_start, t_end: The window.
            candidate: ``nu`` or ``scheme`` changed for the candidate (:meth:`predictions`).

        Raises:
            ValueError: On a viscosity below :attr:`MIN_NU`, an unknown scheme, or an invalid
                candidate.
        """
        if not float(nu) >= self.MIN_NU:
            raise ValueError(f"nu must be at least {self.MIN_NU}, below which the series loses "
                             f"its precision to cancellation, got {nu}")
        if scheme not in self.SCHEMES:
            raise ValueError(f"scheme must be one of {self.SCHEMES}, got {scheme!r}")
        super().__init__(grid=grid, length=(2.0 * np.pi,), boundary=("periodic",),
                         n_frames=n_frames, t_start=t_start, t_end=t_end, candidate=candidate,
                         params={"nu": float(nu), "scheme": scheme})
        a = 1.0 / (2.0 * float(nu))
        self._modes = np.arange(1, self.TERMS + 1)
        self._ratios = (-1.0) ** self._modes * ive(self._modes, a) / ive(0, a)
        self._nu, self._scheme = float(nu), scheme

    def solution(self, time: float) -> dict[str, np.ndarray]:
        """Velocity at ``time`` on the cell centres, exact or by the scheme."""
        x, nu, h, n = self.centres[0], self._nu, self._grid.spacing[0], self._modes
        if self._scheme == "central":
            def rhs(_: float, u: np.ndarray) -> np.ndarray:
                right, left = np.roll(u, -1), np.roll(u, 1)
                return -(right**2 - left**2) / (4.0 * h) + nu * (right - 2.0 * u + left) / h**2

            u = solve_ivp(rhs, (0.0, time), -np.sin(x), method="DOP853", rtol=1e-10,
                          atol=1e-12).y[:, -1]
        else:
            damped = self._ratios * np.exp(-nu * n**2 * time)
            u = (4.0 * nu * (n * damped) @ np.sin(np.outer(n, x))
                 / (1.0 + 2.0 * damped @ np.cos(np.outer(n, x))))
        return {"velocity": u[None]}


def polar(centres: Sequence[np.ndarray], length: float) -> tuple[np.ndarray, np.ndarray]:
    """The distance ``r`` of every cell centre from the centre of the square ``[0, length)^2``,
    and the radial unit vector ``(2, X, Y)``, zero where ``r = 0``: the geometry of a
    cylindrical blast or implosion at the centre of the domain."""
    offsets = np.stack([c - 0.5 * length for c in centres])
    radius = np.hypot(*offsets)
    return radius, offsets / np.where(radius > 0, radius, 1.0)


@register_reader("sedov_taylor")
class SedovTaylor(ClosedFormTrajectory):
    """The cylindrical Sedov-Taylor blast wave: energy ``E`` per unit length released on an axis
    in an ideal gas of density ``rho_0`` at rest, a self-similar solution of the 2D Euler
    equations (Sedov 1959; Taylor 1950).

    Formulas are those of Kamm & Timmes (2007), "On efficient generation of numerically robust
    Sedov solutions", Los Alamos report LA-UR-07-2849, https://cococubed.com/papers/la-ur-07-2849.pdf,
    as implemented in Timmes's public ``sedov_library_qp.f90`` (https://cococubed.com/codes/sedov/),
    whose comments number them as Kamm's equations; the report's PDF could not be rendered here,
    so the numbers are the code's. With geometry ``j = 2``, uniform ambient density
    (``omega = 0``) and ``gamma`` in ``(1, 2)`` the solution is the "standard" case, nonzero from
    the shock to the axis, where the pressure is finite. In the similarity variable ``V`` running
    from ``V_0 = 1/(2 gamma)`` at the axis to ``V_2 = 1/(gamma + 1)`` at the shock (Eqs. 18, 28)
    and ``s = 2 gamma V - 1``, the combinations of Eqs. 29-37 and exponents of Eqs. 42-47
    specialise at ``j = 2, omega = 0`` to (our algebra, checked against the general expressions
    to 2e-15 at gamma = 1.2, 1.4 and 5/3)::

        x_1 = (gamma + 1) V,  x_2 = (gamma + 1) s / (gamma - 1),
        x_3 = (gamma + 1)(1 - gamma V),  x_4 = (gamma + 1)(1 - 2 V) / (gamma - 1),
        lambda = r / r_2 = x_1^(-1/2) x_2^((gamma - 1)/(2 gamma)) x_3^(-1/2)     (Eq. 38)
        u / u_2 = x_1 lambda,   rho / rho_2 = x_2^(1/gamma) (x_3/x_4)^(2/(2 - gamma)),
        p / p_2 = x_1 (x_3/x_4)^(gamma/(2 - gamma))                            (Eqs. 39-41)

    ``lambda`` increases from 0 to 1 with ``s``; the reader inverts it by bisection in
    ``log s``, which resolves the axis, where ``lambda ~ s^((gamma - 1)/(2 gamma))`` (s ~ 1e-21
    at lambda = 1e-3 for gamma = 1.4), in double precision. The shock radius and the
    strong-shock jump are Kamm & Timmes's Eqs. 12-16 at ``j = 2``::

        r_2 = (E t^2 / (alpha rho_0))^(1/4),  u_s = r_2 / (2 t),
        rho_2 = rho_0 (gamma + 1)/(gamma - 1),  u_2 = 2 u_s / (gamma + 1),
        p_2 = 2 rho_0 u_s^2 / (gamma + 1),

    and ``alpha`` makes the energy inside the front ``E``; equating ``E`` with
    ``int (rho u^2 / 2 + p / (gamma - 1)) 2 pi r dr`` gives (our algebra; it equals the code's
    ``(j - 1) pi (J_1 + 2 J_2 / (gamma - 1))``, Eq. 57)

        alpha = pi / (gamma^2 - 1) int_0^1 (g f^2 + h) lambda d lambda,

    with ``f, g, h`` the three profiles above, integrated by 128-point Gauss-Legendre in
    ``lambda``. At gamma = 1.4, ``alpha = 0.9840740`` (``tests/test_analytic_datasets.py``; the
    same integral at ``j = 3`` reproduces Kamm & Timmes's spherical 0.851072 to 7 digits). Their
    standard cylindrical energy ``E = 0.311357`` (Sect. 4.1, as ``dataset_specs/03``, Sect. 3.1
    reads it), the default, puts the front at ``r_2 = 0.749994`` at ``t = 1``, not their stated
    0.75: the printed energy implies ``alpha = 0.98404``, 3.3e-5 below this integral.

    The similarity solution is the limit of zero ambient pressure. The shock detector needs a
    positive one (``dataset_specs/03``, Sect. 2), so ``pressure`` ``p_0`` fills the gas ahead of
    the front; behind it the profile is the zero-pressure one. The mismatch is of order
    ``p_0 / p_2`` (1e-5 at the defaults' last frame). The blast sits at the centre of the
    square ``[0, length)^2``; both axes are Neumann, and the constructor refuses a window in
    which the front reaches the edge, so the gas at the boundary is at rest and uniform.
    ``time_offset`` evaluates every frame at ``t + time_offset``, so the candidate
    ``{time_offset: dt}`` displaces every point of the front radially by
    ``r_2(t + dt) - r_2(t)``, and ``{energy: E'}`` is a pure size error.
    """

    FORMAT = "sedov_taylor"
    FIELDS = ("density", "velocity", "pressure")

    def __init__(self, path: str | None = None, *, energy: float = 0.311357,
                 density: float = 1.0, pressure: float = 1e-6, gamma: float = 1.4,
                 time_offset: float = 0.0, length: float = 2.0,
                 grid: Sequence[int] = (128, 128), n_frames: int = 4, t_start: float = 0.25,
                 t_end: float = 1.0, candidate: Mapping[str, Any] | None = None) -> None:
        """Integrate ``alpha`` once and fix the window.

        Args:
            path: Ignored; accepted so every reader is constructed the same way.
            energy: ``E``, the energy per unit length, positive.
            density: ``rho_0``, the ambient density, positive.
            pressure: ``p_0``, the ambient pressure ahead of the front, positive.
            gamma: Ratio of specific heats, in ``(1, 2)``; at 2 the ``x_3 / x_4`` exponents are
                singular (Kamm & Timmes's removable case ``omega_3``), which is not coded.
            time_offset: Added to every frame's time.
            length: Side of the square domain; the blast is at its centre.
            grid: Cells along ``(x, y)``.
            n_frames: Number of frames.
            t_start, t_end: The window; ``t_start + time_offset > 0``.
            candidate: Any parameter above from ``energy`` to ``length``, changed for the
                candidate (:meth:`predictions`), or None.

        Raises:
            ValueError: On ``gamma`` outside ``(1, 2)``, a non-positive energy, density,
                pressure or length, ``t_start + time_offset <= 0``, a front that reaches the
                edge of the domain by ``t_end``, or an invalid grid, window or candidate.
        """
        g, offset = float(gamma), float(time_offset)
        if not 1.0 < g < 2.0:
            raise ValueError(f"gamma must lie in (1, 2), got {gamma}")
        if min(float(energy), float(density), float(pressure), float(length)) <= 0:
            raise ValueError(f"energy, density, pressure and length must be positive, got "
                             f"{energy}, {density}, {pressure}, {length}")
        if float(t_start) + offset <= 0:
            raise ValueError(f"t_start + time_offset must be positive, got {t_start} + {offset}")
        super().__init__(grid=grid, length=(float(length),) * 2,
                         boundary=("neumann", "neumann"), n_frames=n_frames, t_start=t_start,
                         t_end=t_end, candidate=candidate,
                         params={"energy": float(energy), "density": float(density),
                                 "pressure": float(pressure), "gamma": g, "time_offset": offset,
                                 "length": float(length)})
        self._gamma, self._offset = g, offset
        self._radius, self._direction = polar(self.centres, float(length))
        nodes, weights = np.polynomial.legendre.leggauss(128)
        lam = 0.5 * (nodes + 1.0)
        f, rho, p = self.profile(lam)
        #: The dimensionless energy integral: E = alpha rho_0 r_2^4 / t^2.
        self.alpha = float(np.pi / (g**2 - 1.0) * 0.5 * np.sum(weights * (rho * f**2 + p) * lam))
        if self.front(float(t_end)) >= 0.5 * float(length):
            raise ValueError(f"the front reaches the edge of the domain by t_end={t_end} "
                             f"(r_2 = {self.front(float(t_end)):.4g} >= {0.5 * float(length)})")

    def front(self, time: float) -> float:
        """The shock radius ``r_2`` at frame time ``time`` (Kamm & Timmes, Eq. 12, j = 2)."""
        p = self._params
        return float((p["energy"] * (time + self._offset) ** 2 / (self.alpha * p["density"]))
                     ** 0.25)

    def profile(self, lam: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """``u / u_2``, ``rho / rho_2`` and ``p / p_2`` at ``lambda = r / r_2`` in ``[0, 1]``.

        Bisection in ``log s`` over ``[log 1e-300, log s_2]``, ``s_2 = (gamma - 1)/(gamma + 1)``
        at the shock: 100 halvings of an interval of width 700 leave 6e-28 in ``log s``, so
        ``lambda`` is matched to round-off. ``lambda = 0`` maps to ``s = 1e-300``, where
        ``lambda`` is below 1e-42, so the axis takes the limit of the profiles.
        """
        g = self._gamma

        def combinations(s: np.ndarray) -> tuple[np.ndarray, ...]:
            v = (1.0 + s) / (2.0 * g)
            x1, x2 = (g + 1.0) * v, (g + 1.0) / (g - 1.0) * s
            x3, x4 = (g + 1.0) * (1.0 - g * v), (g + 1.0) / (g - 1.0) * (1.0 - 2.0 * v)
            return x1, x2, x3, x4

        def log_lambda(s: np.ndarray) -> np.ndarray:
            x1, x2, x3, _ = combinations(s)
            return -0.5 * np.log(x1) + (g - 1.0) / (2.0 * g) * np.log(x2) - 0.5 * np.log(x3)

        target = np.log(np.maximum(lam, np.finfo(float).tiny))
        low = np.full(np.shape(lam), np.log(1e-300))
        high = np.full(np.shape(lam), np.log((g - 1.0) / (g + 1.0)))
        for _ in range(100):
            middle = 0.5 * (low + high)
            below = log_lambda(np.exp(middle)) < target
            low, high = np.where(below, middle, low), np.where(below, high, middle)
        s = np.exp(0.5 * (low + high))
        x1, x2, x3, x4 = combinations(s)
        ratio = x3 / x4
        return (x1 * np.exp(log_lambda(s)), x2 ** (1.0 / g) * ratio ** (2.0 / (2.0 - g)),
                x1 * ratio ** (g / (2.0 - g)))

    def solution(self, time: float) -> dict[str, np.ndarray]:
        """Density, velocity and pressure at ``time + time_offset`` on the cell centres."""
        g, p, t = self._gamma, self._params, time + self._offset
        r_2 = self.front(time)
        speed = r_2 / (2.0 * t)  # u_s = dr_2/dt, Kamm & Timmes Eq. 13 at j = 2
        inside = self._radius < r_2
        f, rho, pressure_ratio = self.profile(self._radius[inside] / r_2)
        density = np.full_like(self._radius, p["density"])
        density[inside] = p["density"] * (g + 1.0) / (g - 1.0) * rho
        pressure = np.full_like(self._radius, p["pressure"])
        pressure[inside] = 2.0 * p["density"] * speed**2 / (g + 1.0) * pressure_ratio
        radial = np.zeros_like(self._radius)
        radial[inside] = 2.0 * speed / (g + 1.0) * f
        return {"density": density[None], "velocity": radial * self._direction,
                "pressure": pressure[None]}


@register_reader("noh")
class Noh(ClosedFormTrajectory):
    """The cylindrical Noh implosion: an ideal gas of density ``rho_0`` streaming radially
    inward at speed ``u_0`` with zero pressure stagnates behind a circular shock moving out at
    constant speed (Noh 1987, J. Comput. Phys. 72(1), 78-120,
    https://doi.org/10.1016/0021-9991(87)90074-X, not opened).

    At ``gamma = 5/3``, ``rho_0 = u_0 = 1``, Sutherland (2010), Astrophys. Space Sci. 327,
    173-206, arXiv:1003.0724, Sect. 6.1.6, Table 9, prints the exact solution in the plane::

        r < t/3:  rho = 16,          u = 0,     p = 16/3
        r > t/3:  rho = 1 + t / r,   u_r = -1,  p = 0,      shock speed 1/3,

    and his Table 10 sets the initial pressure to 1e-6 "as an approximation to zero pressure",
    the reader's default ``pressure`` ahead of the shock (``dataset_specs/03``, Sect. 3.4; the
    detector needs a positive pressure). For other ``gamma``, ``rho_0`` and ``u_0`` the same
    construction (our derivation, which the tests check against the Rankine-Hugoniot conditions
    and the continuity equation): the inflow keeps its speed, since it feels no pressure, so
    mass conservation gives ``rho = rho_0 (1 + u_0 t / r)`` ahead of the shock; a shock at
    ``r = D t`` bringing the gas to rest needs, by the jump in mass, momentum and energy,

        D = (gamma - 1) u_0 / 2,  rho_2 = rho_0 ((gamma + 1)/(gamma - 1))^2,  p_2 = rho_2 D u_0,

    which is 1/3, 16 and 16/3 at Sutherland's values. The post-shock state is the same at every
    time, so the pressure jump the detector reads never changes. The implosion sits at the
    centre of the square ``[0, length)^2``; both axes are Neumann, though the exact solution at
    the edge is the inflow itself, which a solver imposes as a boundary condition (Sutherland's
    Table 10). The constructor refuses a window in which the shock reaches the edge. At
    ``t = 0`` there is no shock: a no-shock frame (spec 03, Sect. 2, need (d)). ``time_offset``
    evaluates every frame at ``t + time_offset``, so the candidate ``{time_offset: dt}``
    displaces every point of the front radially by ``D dt``.
    """

    FORMAT = "noh"
    FIELDS = ("density", "velocity", "pressure")

    def __init__(self, path: str | None = None, *, gamma: float = 5.0 / 3.0,
                 density: float = 1.0, speed: float = 1.0, pressure: float = 1e-6,
                 time_offset: float = 0.0, length: float = 2.0,
                 grid: Sequence[int] = (128, 128), n_frames: int = 4, t_start: float = 0.5,
                 t_end: float = 2.0, candidate: Mapping[str, Any] | None = None) -> None:
        """Fix the shock speed and the post-shock state.

        Args:
            path: Ignored; accepted so every reader is constructed the same way.
            gamma: Ratio of specific heats, above 1.
            density: ``rho_0``, the inflow's density at ``t = 0``, positive.
            speed: ``u_0``, the inflow speed, positive.
            pressure: ``p_0``, the pressure ahead of the shock, positive.
            time_offset: Added to every frame's time.
            length: Side of the square domain; the implosion is at its centre.
            grid: Cells along ``(x, y)``.
            n_frames: Number of frames.
            t_start, t_end: The window; ``t_start + time_offset >= 0``.
            candidate: Any parameter above from ``gamma`` to ``length``, changed for the
                candidate (:meth:`predictions`), or None.

        Raises:
            ValueError: On ``gamma <= 1``, a non-positive density, speed, pressure or length,
                ``t_start + time_offset < 0``, a shock that reaches the edge of the domain by
                ``t_end``, or an invalid grid, window or candidate.
        """
        g, offset = float(gamma), float(time_offset)
        if g <= 1.0:
            raise ValueError(f"gamma must exceed 1, got {gamma}")
        if min(float(density), float(speed), float(pressure), float(length)) <= 0:
            raise ValueError(f"density, speed, pressure and length must be positive, got "
                             f"{density}, {speed}, {pressure}, {length}")
        if float(t_start) + offset < 0:
            raise ValueError(f"t_start + time_offset must be non-negative, got {t_start} + "
                             f"{offset}")
        super().__init__(grid=grid, length=(float(length),) * 2,
                         boundary=("neumann", "neumann"), n_frames=n_frames, t_start=t_start,
                         t_end=t_end, candidate=candidate,
                         params={"gamma": g, "density": float(density), "speed": float(speed),
                                 "pressure": float(pressure), "time_offset": offset,
                                 "length": float(length)})
        self._offset = offset
        self._radius, self._direction = polar(self.centres, float(length))
        #: The shock speed D.
        self.shock_speed = (g - 1.0) / 2.0 * float(speed)
        #: The state behind the shock, at rest.
        self.post_shock = {"density": float(density) * ((g + 1.0) / (g - 1.0)) ** 2}
        self.post_shock["pressure"] = self.post_shock["density"] * self.shock_speed * float(speed)
        if self.front(float(t_end)) >= 0.5 * float(length):
            raise ValueError(f"the shock reaches the edge of the domain by t_end={t_end}")

    def front(self, time: float) -> float:
        """The shock radius ``D (time + time_offset)`` at frame time ``time``."""
        return self.shock_speed * (time + self._offset)

    def solution(self, time: float) -> dict[str, np.ndarray]:
        """Density, velocity and pressure at ``time + time_offset`` on the cell centres."""
        p, t, r = self._params, time + self._offset, self._radius
        inside = r < self.front(time)
        inflow = p["density"] * (1.0 + np.divide(p["speed"] * t, r, out=np.zeros_like(r),
                                                 where=r > 0))
        density = np.where(inside, self.post_shock["density"], inflow)
        pressure = np.where(inside, self.post_shock["pressure"], p["pressure"])
        return {"density": density[None],
                "velocity": np.where(inside, 0.0, -p["speed"]) * self._direction,
                "pressure": pressure[None]}


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

    **An acoustic part** (``dataset_specs/10_acoustic_and_helmholtz_fields.md``, Sect. 3).
    ``amplitude`` ``U`` scales the vortex (0 removes it), and a ``sound_speed`` ``c`` with a
    list ``acoustic`` adds an exact curl-free velocity ``u_d = grad phi`` and a density
    perturbation ``rho'``, solving the linearised isothermal equations about rest at density 1,

        d_t rho' = -lap phi,   d_t phi = -c^2 rho' + nu_L lap phi,

    the sound mode of the split of the linearised compressible equations into uncoupled
    vorticity and sound modes (Chu & Kovasznay 1958, J. Fluid Mech. 3(5), 494-514,
    https://doi.org/10.1017/S0022112058000148, abstract; the isothermal gas has no entropy
    mode). ``nu_L``, the ``longitudinal_viscosity``, damps compression; its default ``2 nu`` is
    the D2Q9 BGK lattice-Boltzmann value kinet measures (spec 10, Sect. 3.1). Each Fourier mode
    is a 2x2 linear system solved exactly by its matrix exponential (spec 10, Eq. 3). The vortex
    solves ``d_t u_s = nu lap u_s`` exactly and has no density in linear theory, so the sum is
    an exact solution of the linear equations with the vortical and acoustic parts exact
    separately; the vortex's own pressure is kept, and the acoustic part adds ``c^2 rho'``. Each
    entry of ``acoustic`` is a starting condition sampled at the cell centres:

    * ``{kind: plane, mode: [m, n], amplitude: eps}``: the travelling wave
      ``rho' = eps cos(k . x - c |k| t)``, ``u = eps c k_hat cos(k . x - c |k| t)`` without
      viscosity, ``k = (m, n)``; a standing wave is two of them with opposite modes;
    * ``{kind: potential, mode: [m, n], amplitude: A}``: ``phi = A cos(m x) cos(n y)`` at rest
      density; at ``m = n = 1`` and ``A = U`` the mirror image of the vortex's velocity;
    * ``{kind: pulse, centre: [x, y], width: sigma, amplitude: eps}``:
      ``rho' = eps exp(-r^2 / (2 sigma^2))`` at rest, ``r`` the minimum-image distance, the
      Gaussian pulse of the first computational-aeroacoustics workshop (spec 10, Sect. 3.3,
      item 3), including every periodic image.

    Every option is a candidate parameter, so ``{sound_speed: c'}`` is a candidate whose error
    lies wholly in the dilatational part. ``drift`` translates the acoustic part with the vortex.
    """

    FORMAT = "taylor_green_2d"
    FIELDS = ("velocity", "pressure", "vorticity")
    #: The side of the periodic box, on both axes.
    BOX: ClassVar[float] = 2 * np.pi
    #: The keys of each kind of entry of ``acoustic``.
    ACOUSTIC: ClassVar[dict[str, set[str]]] = {
        "plane": {"kind", "mode", "amplitude"}, "potential": {"kind", "mode", "amplitude"},
        "pulse": {"kind", "centre", "width", "amplitude"}}

    def __init__(self, path: str | None = None, *, nu: float = 0.01,
                 drift: Sequence[float] = (0.0, 0.0), amplitude: float = 1.0,
                 sound_speed: float | None = None, longitudinal_viscosity: float | None = None,
                 acoustic: Sequence[Mapping[str, Any]] = (), grid: Sequence[int] = (256, 256),
                 n_frames: int = 10, t_start: float = 0.0, t_end: float = 50.0,
                 candidate: Mapping[str, Any] | None = None) -> None:
        """Cache the spatial patterns, unless they drift, and the acoustic starting spectra.

        Args:
            path: Ignored; accepted so every reader is constructed the same way.
            nu: Kinematic viscosity, non-negative.
            drift: Velocity ``(U_x, U_y)`` at which every field is translated.
            amplitude: ``U``, the vortex's velocity amplitude.
            sound_speed: ``c``, positive, or None for no acoustic part.
            longitudinal_viscosity: ``nu_L``, non-negative, or None for ``2 nu``.
            acoustic: The starting conditions above; empty without a sound speed.
            grid: Cells along ``(x, y)``.
            n_frames: Number of frames.
            t_start, t_end: The window.
            candidate: Any parameter above from ``nu`` on, changed for the candidate
                (:meth:`predictions`), or None.

        Raises:
            ValueError: On a negative viscosity, a drift that is not a pair, an acoustic option
                without a positive sound speed, an entry of ``acoustic`` of an unknown kind or
                keys, a mode that is not two integers not both zero, a pulse width outside
                ``[3 dx, 0.35]`` (the bounds that keep its sampling and its minimum image
                exact to round-off, spec 10, Sect. 3.3), a mode on the grid damped past
                oscillation (``nu_L |k| >= 2 c``), or an invalid grid, window or candidate.
        """
        if float(nu) < 0:
            raise ValueError(f"nu must be non-negative, got {nu}")
        if np.shape(drift) != (2,):
            raise ValueError(f"drift must be one (U_x, U_y) pair, got {drift}")
        if (sound_speed is None and (acoustic or longitudinal_viscosity is not None)) or (
                sound_speed is not None and float(sound_speed) <= 0) or (
                longitudinal_viscosity is not None and float(longitudinal_viscosity) < 0):
            raise ValueError(f"acoustic and longitudinal_viscosity need a positive sound_speed, "
                             f"and nu_L must be non-negative; got sound_speed={sound_speed}, "
                             f"longitudinal_viscosity={longitudinal_viscosity}")
        waves = [{key: str(value) if key == "kind" else np.asarray(value, dtype=float).tolist()
                  for key, value in wave.items()} for wave in acoustic]
        for wave in waves:
            if set(wave) != self.ACOUSTIC.get(wave.get("kind"), set()) or ("mode" in wave and (
                    np.shape(wave["mode"]) != (2,) or not any(wave["mode"])
                    or wave["mode"] != np.round(wave["mode"]).tolist())):
                raise ValueError(f"each acoustic entry must be one of {self.ACOUSTIC}, with a "
                                 f"mode of two integers not both zero; got {wave}")
        super().__init__(grid=grid, length=(self.BOX, self.BOX),
                         boundary=("periodic", "periodic"), n_frames=n_frames,
                         t_start=t_start, t_end=t_end, candidate=candidate,
                         params={"nu": float(nu), "drift": [float(d) for d in drift],
                                 "amplitude": float(amplitude),
                                 "sound_speed": None if sound_speed is None else float(sound_speed),
                                 "longitudinal_viscosity": None if longitudinal_viscosity is None
                                 else float(longitudinal_viscosity), "acoustic": waves})
        self._nu, self._drift = float(nu), np.asarray(drift, dtype=float)
        self._amplitude, self._sound_speed = float(amplitude), sound_speed
        self._patterns = None if self._drift.any() else self._patterns_at(0.0)
        if sound_speed is None:
            return
        c = float(sound_speed)
        nu_l = 2.0 * self._nu if longitudinal_viscosity is None else float(longitudinal_viscosity)
        x, y = self.centres
        rho, phi = np.zeros_like(x), np.zeros_like(x)
        for wave in waves:
            if wave["kind"] == "pulse":
                if not 3.0 * max(self._grid.spacing) <= wave["width"] <= 0.35:
                    raise ValueError(f"a pulse width must lie in [3 dx, 0.35] = "
                                     f"[{3.0 * max(self._grid.spacing):.4g}, 0.35], got {wave}")
                squared = sum(((p - q + np.pi) % (2 * np.pi) - np.pi) ** 2
                              for p, q in zip(self.centres, wave["centre"], strict=True))
                rho += wave["amplitude"] * np.exp(-squared / (2.0 * wave["width"] ** 2))
                continue
            m, n = wave["mode"]
            if wave["kind"] == "plane":
                rho += wave["amplitude"] * np.cos(m * x + n * y)
                phi += wave["amplitude"] * c / np.hypot(m, n) * np.sin(m * x + n * y)
            else:
                phi += wave["amplitude"] * np.cos(m * x) * np.cos(n * y)
        #: Wavevector components on the 2 pi box, integers.
        self._k = physical_wavenumber_grid(self._grid.shape, self._grid.spacing)
        k_squared = self._k[0] ** 2 + self._k[1] ** 2
        gamma = 0.5 * nu_l * k_squared
        if (gamma[k_squared > 0] ** 2 >= c**2 * k_squared[k_squared > 0]).any():
            raise ValueError(f"nu_L |k| >= 2 c on this grid (nu_L={nu_l}, c={c}): a mode is "
                             "damped past oscillation; lower nu_L or raise c")
        self._acoustic = (np.fft.fft2(rho), np.fft.fft2(phi), k_squared, gamma,
                          np.sqrt(c**2 * k_squared - gamma**2), c**2)

    def _patterns_at(self, time: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Velocity, pressure and vorticity at unit amplitude, translated by ``drift * time``."""
        x, y = (c - u * time for c, u in zip(self.centres, self._drift, strict=True))
        return (np.stack([np.sin(x) * np.cos(y), -np.cos(x) * np.sin(y)]),
                (0.25 * (np.cos(2 * x) + np.cos(2 * y)))[None],
                (2.0 * np.sin(x) * np.sin(y))[None])

    def solution(self, time: float) -> dict[str, np.ndarray]:
        """Velocity, pressure and vorticity at ``time`` on the cell centres."""
        velocity, pressure, vorticity = self._patterns or self._patterns_at(time)
        decay = self._amplitude * np.exp(-2.0 * self._nu * time)
        fields = {"velocity": velocity * decay, "pressure": pressure * decay**2,
                  "vorticity": vorticity * decay}
        if self._sound_speed is None:
            return fields
        rho_0, phi_0, k_squared, gamma, omega, c_squared = self._acoustic
        # Spec 10, Eq. (3): the matrix exponential of [[0, k^2], [-c^2, -2 gamma]], gamma =
        # nu_L k^2 / 2, Omega^2 = c^2 k^2 - gamma^2 (its author's derivation; the trace and
        # determinant fix it). sin(Omega t) / Omega = t sinc(Omega t / pi) is t at Omega = 0.
        # The drift translates by drift * t, a phase exp(-i k . drift t) on every mode.
        cos, sin_over = np.cos(omega * time), time * np.sinc(omega * time / np.pi)
        factor = np.exp(-gamma * time - 1j * time * (self._k[0] * self._drift[0]
                                                     + self._k[1] * self._drift[1]))
        rho = factor * (rho_0 * cos + (gamma * rho_0 + k_squared * phi_0) * sin_over)
        phi = factor * (phi_0 * cos - (gamma * phi_0 + c_squared * rho_0) * sin_over)
        fields["velocity"] = fields["velocity"] + np.real(np.fft.ifft2(1j * np.stack(self._k)
                                                                        * phi))
        fields["pressure"] = fields["pressure"] + c_squared * np.real(np.fft.ifft2(rho))[None]
        return fields


@register_reader("taylor_green_kinet")
class TaylorGreenKinet(TaylorGreen2D):
    """The exact vortex on the cells and clock of a kinet run of it, the run its candidate.

    kinet's ``taylor_green_vortex`` case starts from ``u = u_l sin(kx) cos(ky)``,
    ``v = -u_l cos(kx) sin(ky)``, ``k = 2 pi / N``, with node ``i`` at ``i + 1/2`` cells: eq. (3)
    of ``docs/datasets/taylor_green_vortex.md`` with ``U0 = u_l`` at ``x = (i + 1/2) 2 pi / N``
    (checked by the job that ran it, ``docs/datasets/logs/kinet_runs/taylor_green_re50/
    _scripts/compare_tg.py``). Read with ``KinetRawTrajectory(box=2 pi)``, the run is in this
    reader's units, box ``2 pi`` and ``U0 = 1``: a cell is ``2 pi / N``, the velocity is divided
    by ``u_l``, the time is ``2 pi`` times kinet's ``time_convection`` (steps ``u_l / N``), and
    the viscosity is ``nu = 2 pi nu_l / (N u_l) = 2 pi / Re``, with ``Re = u_l N / nu_l`` kinet's
    Reynolds number on the box side. This reader's frames are the exact solution at the run's
    cell centres and times with that viscosity; :meth:`predictions` is the run, scored against
    them as a candidate is, its rows labelled with ``param_resolution`` N, so a grid sequence of
    runs gives the solver's observed order (``fmeval.analysis.observed_order``). Pressure is left
    out: the converted run stores none (``fmeval.data.convert_kinet``).

    A registered format rather than an option of :class:`TaylorGreen2D`, because a dataset of it
    reads a file: ``reads_from_disk`` is a property of the format, which ``open_trajectory`` uses
    to resolve ``path`` (locally or at ``paths.data_url``) and the tests to mark it ``data``.
    """

    reads_from_disk = True
    FORMAT = "taylor_green_kinet"
    FIELDS = ("velocity", "vorticity")

    def __init__(self, path: str | Path) -> None:
        """Read the run's grid, clock and viscosity, and evaluate the exact solution on them.

        Args:
            path: A kinet ``taylor_green_vortex`` run in the flat layout, converted by
                ``fmeval.data.convert_kinet``, or its published URL.

        Raises:
            ValueError: If the run is not kinet's Taylor-Green vortex on a square grid, or
                :class:`KinetRawTrajectory` refuses it.
        """
        with KinetRawTrajectory(path, box=self.BOX) as run:
            group = run.meta["source_attrs"].get("group")
            if group != "taylor_green_vortex" or len(set(run.grid.shape)) != 1:
                raise ValueError(f"{path}: a kinet taylor_green_vortex run on a square grid is "
                                 f"needed; this is {group!r} on {run.grid.shape}")
            super().__init__(nu=run.viscosity, grid=run.grid.shape, n_frames=len(run),
                             t_start=float(run.times[0]), t_end=float(run.times[-1]),
                             candidate={})  # an empty candidate labels the rows as a candidate's
            # The run's clock itself: the pipeline pairs two trajectories only on equal times.
            self._times = run.times
        self._path = path
        self._meta["path"] = str(path)

    def predictions(self) -> KinetRawTrajectory:
        """The run, on this reader's cells and clock and in its units."""
        return KinetRawTrajectory(self._path, box=self.BOX)


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
    would not. It tests the time-dependent machinery, not physics (``docs/decisions.md``), and the
    ``advecting_blobs`` configuration is not an evidence dataset.

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
