"""Reader for raw kinet solver output.

Layout is a flat HDF5 file (no groups) of ``(N_sim, C, T, X, Y)`` float64 datasets, chunked
one frame per chunk. Root attributes are JSON strings. Verified against
``D2Q9_shape-256-256_T-10000_H-dc804f.h5`` (167 GiB) and its 1.7 GB T=101 sibling.

Three quirks of this format, each handled below:

* ``temperature`` is stored ``(1, 1, T, 1, 1)`` -- spatially degenerate and constant at
  1/3. It is a solver parameter, not a field, and is excluded.
* ``pressure`` is bitwise ``density * float64(1/3)`` (isothermal D2Q9, ``c_s^2 = 1/3``);
  it differs from ``density / 3`` only by the last ulp, since multiply and divide round
  differently. Verified across t = 1, 5000, 10000. Carrying both doubles the I/O for no
  information and injects a guaranteed rho=1.0 pair into the cross-metric correlation
  matrix used for pruning, so it is excluded unless asked for.
* ``stability_scale`` and ``stabilized_time_scale`` are all-NaN at t=0, and
  ``time_scale[0]`` is NaN. Start at t=1. Never use ``time_scale`` as a clock -- it is a
  solver stability quantity, roughly constant at 0.5; use the ``time`` dataset.
"""

from __future__ import annotations

import json
import posixpath
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from . import remote as _remote
from ._timeaxis import TimeAxisMode, read_time_axis
from .base import FIELDS, REDUNDANT_FIELDS, GridSpec, NanPolicy, register_reader
from .hdf5 import HDF5Trajectory

#: Canonical name -> dataset name in the file.
FIELD_MAP: dict[str, str] = {
    "density": "density",
    "velocity": "velocity",
    "vorticity": "vorticity",
    "pressure": "pressure",
    "distribution": "F",
}


@register_reader("kinet_raw")
class KinetRawTrajectory(HDF5Trajectory):
    """One rollout from a flat kinet HDF5 file."""

    FORMAT = "kinet_raw"

    def __init__(
        self,
        path: str | Path,
        *,
        chunk_cache_mb: int = _remote.DEFAULT_CHUNK_CACHE_MB,
        nan_policy: NanPolicy = "error",
        include_redundant: bool = False,
        boundary: Sequence[str] | None = None,
        sim_index: int = 0,
        time_axis: TimeAxisMode = "auto",
        frame_stride: int = 1,
        box: float | None = None,
        cell: float | None = None,
        candidate: str | None = None,
    ) -> None:
        """Open a kinet raw HDF5 file, locally or over HTTP.

        Args:
            path: Path to the ``.h5`` file, or an ``https://`` URL of the published copy.
            chunk_cache_mb: h5py chunk cache; see :meth:`HDF5Trajectory._open`.
            nan_policy: ``"error"``, ``"warn"`` or ``"ignore"`` for non-finite values.
            include_redundant: Expose ``pressure`` even though it is ``density * c_s^2``.
            boundary: Boundary type of each axis (``fmeval.data.base.BOUNDARIES``). Raw kinet
                files do not record it, so it comes from the dataset config; defaults to
                periodic on every axis, which is correct for the doubly-periodic case family.
            sim_index: Index along the leading simulation axis.
            time_axis: How to read the clock. See ``fmeval.data._timeaxis``; the default
                only changes behaviour for a remote file whose clock is chunked per frame.
            frame_stride: Expose every ``frame_stride``-th stored frame as one frame. The
                runs of one family take a solver step proportional to the cell size at a
                fixed Mach number, so a 1024^2 run stores four frames per frame of a 256^2
                run over the same physical time. With the stride that makes them equal,
                frame ``i`` is the same physical time on every member and one
                ``dataset.time`` selection serves the whole family. The stride must divide
                the number of solver steps, so the last stored frame stays on the clock.
            box: Read the run in units where kinet's reference length ``L_l`` (the box side, in
                cells) is ``box`` and its reference velocity ``u_l`` is 1, instead of in cells
                and solver steps; both are the file's ``normalization_plan.lattice``. A cell is
                then ``h = box / L_l`` long and a step lasts ``u_l h``, so the spacing is
                multiplied by ``h``, velocity divided by ``u_l``, vorticity by ``u_l h``,
                pressure by ``u_l^2``, and the clock, which a converted file holds in
                ``L_l / u_l`` (``time/time_convection``), multiplied by ``box``.
                :attr:`viscosity` is then the run's kinematic viscosity in these units,
                ``nu_l h / u_l``. None reads lattice units.
            cell: Read the run in units where a cell is ``cell`` long and a solver step lasts
                ``cell``, so velocity, density and pressure keep their lattice values: the
                spacing is multiplied by ``cell``, vorticity divided by it, and the clock is the
                solver step of each frame (the ``time_index`` a converted file holds) times
                ``cell``. For runs that store no reference length and velocity, which ``box``
                needs: kinet's Sod tubes of N nodes, whose diaphragm is the face (N - 1) / 2, are
                nested and share one clock with ``cell = 1 / (N - 1)``. At most one of ``box``
                and ``cell``.
            candidate: The file name of another run of the same problem in this file's folder,
                on its own grid: :meth:`predictions` opens it with every other option given here,
                and the pipeline scores it against this run remapped onto the analysis grid,
                which must be the candidate's (``dataset.analysis_resolution``). Its rows are
                labelled as a forecast's, with the candidate's resolution.

        Raises:
            ValueError: If the clock disagrees with ``discretization``, ``frame_stride`` does
                not divide the steps, ``box`` is given for a file whose clock is not
                ``time_convection``, or ``box`` and ``cell`` are both given or ``cell`` is not
                positive.
        """
        if cell is not None and (box is not None or cell <= 0):
            raise ValueError(f"cell={cell} must be positive and not given with box={box}")
        self._open(path, chunk_cache_mb=chunk_cache_mb, nan_policy=nan_policy,
                   sim_index=sim_index)
        disc = json.loads(self._file.attrs["discretization"])
        shape = tuple(int(n) for n in disc["spatial"]["grid"])
        length = tuple(float(v) for v in disc["spatial"]["length"])
        spacing = tuple(l / n for l, n in zip(length, shape))
        n_spatial = len(shape)
        #: Field -> the factor its stored values are multiplied by; 1 for a field not named.
        self._scale: dict[str, float] = {}
        #: The run's kinematic viscosity in the units ``box`` sets; None in lattice units.
        self.viscosity: float | None = None
        if box is not None:
            if self._file["time"].attrs.get("source") != "time_convection":
                raise ValueError(f"{self.source}: box needs the clock in L_l / u_l, which a "
                                 "file converted from time/time_convection holds; this one's "
                                 f"is {self._file['time'].attrs.get('source')!r}")
            lattice = json.loads(self._file.attrs["normalization_plan"])["lattice"]
            h, speed = float(box) / lattice["L_l"], lattice["u_l"]
            self.viscosity = lattice["nu_l"] * h / speed
        elif cell is not None:
            h, speed = float(cell), 1.0
        if box is not None or cell is not None:
            spacing = tuple(s * h for s in spacing)
            self._scale = {"velocity": 1 / speed, "vorticity": 1 / (speed * h),
                           "pressure": 1 / speed**2}
        boundary_t = (
            tuple(str(b) for b in boundary) if boundary is not None
            else ("periodic",) * n_spatial
        )
        self._grid = GridSpec(
            shape=shape,
            spacing=spacing,
            boundary=boundary_t,
            dims=("x", "y", "z")[:n_spatial],
            origin=(0.0,) * n_spatial,
        )
        self._times = read_time_axis(
            self._file["time" if cell is None else "time_index"], remote=self.is_remote,
            mode=time_axis,
        ) * float(box or cell or 1.0)
        n_frames = len(self._times)
        # A cross-check of the frame count, not its source: `time.shape[0]` is the length of
        # the very axis being described, so it cannot be off by one. `temporal.grid` counts
        # solver *steps* and frame 0 is the initial condition, so a file holds one more frame
        # than it has steps -- measured on D2Q9_shape-256-256_T-10000_H-dc804f.h5, grid 10000
        # against time.shape (10001,). The attribute cannot supply the clock either:
        # `temporal.length` is 10000.0 in lattice-step units while the physical timestep is
        # 2.2552744890219753e-4.
        temporal = disc.get("temporal")
        if isinstance(temporal, dict) and "grid" in temporal:
            declared = int(temporal["grid"]) + 1
            if declared != n_frames:
                raise ValueError(
                    f"{self.source}: the `time` dataset has {n_frames} entries but "
                    f"discretization.temporal.grid implies {declared}. A wrong frame count "
                    "silently corrupts every dataset.time selection downstream."
                )

        available = []
        for canonical, dataset in FIELD_MAP.items():
            if canonical in REDUNDANT_FIELDS and not include_redundant:
                continue
            if dataset not in self._file:
                continue
            ds = self._file[dataset]
            if ds.ndim != n_spatial + 3:  # (N, C, T, *spatial)
                continue
            if ds.shape[1] != FIELDS[canonical].n_channels(n_spatial):
                continue
            if ds.shape[2] != n_frames:
                raise ValueError(
                    f"{self.source}: {dataset} has {ds.shape[2]} frames but the `time` "
                    f"dataset has {n_frames}."
                )
            available.append(canonical)
        self._fields = tuple(available)
        if frame_stride < 1 or (n_frames - 1) % frame_stride:
            raise ValueError(
                f"{self.source}: frame_stride={frame_stride} must be a positive divisor of "
                f"the {n_frames - 1} solver steps, so the strided frames end on the last one."
            )
        self._stride = frame_stride
        self._times = self._times[::frame_stride]
        #: Every option but ``candidate``, which :meth:`predictions` opens the candidate with.
        self._options = {"chunk_cache_mb": chunk_cache_mb, "nan_policy": nan_policy,
                         "include_redundant": include_redundant, "boundary": boundary,
                         "sim_index": sim_index, "time_axis": time_axis,
                         "frame_stride": frame_stride, "box": box, "cell": cell}
        #: The candidate run's location, beside this file (a path or a URL), or None.
        self._candidate = (None if candidate is None
                           else posixpath.join(posixpath.dirname(self.source), candidate))
        if self._candidate is not None:
            with self.predictions() as run:
                self._candidate_resolution = run.grid.shape[0]

    def predictions(self) -> KinetRawTrajectory | None:
        """The candidate run, opened with this run's options, or None without one."""
        if self._candidate is None:
            return None
        return KinetRawTrajectory(self._candidate, **self._options)

    def frame_columns(self, t: int) -> dict[str, Any]:
        """With a candidate, every row is labelled as a forecast's, with the candidate's
        resolution."""
        return ({} if self._candidate is None
                else self._candidate_columns(t, self._candidate_resolution))

    def read_frame(self, t: int, fields: Sequence[str]) -> dict[str, np.ndarray]:
        """Read one frame.

        ``ds[sim, :, t]`` returns ``(C, *spatial)`` directly for every channel count, so
        there is no squeeze, reshape or scalar special case. The time position is always a
        plain int -- never a slice. See the module docstring in ``base.py``. Frame ``t`` is
        stored frame ``t * frame_stride``.
        """
        out: dict[str, np.ndarray] = {}
        for name in fields:
            ds = self._file[FIELD_MAP[name]]
            out[name] = np.asarray(ds[self._sim, :, int(t) * self._stride],
                                   dtype=np.float64) * self._scale.get(name, 1.0)
        return out
