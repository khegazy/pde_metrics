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
from collections.abc import Sequence
from pathlib import Path

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
        periodic: Sequence[bool] | None = None,
        sim_index: int = 0,
        time_axis: TimeAxisMode = "auto",
    ) -> None:
        """Open a kinet raw HDF5 file, locally or over HTTP.

        Args:
            path: Path to the ``.h5`` file, or an ``https://`` URL of the published copy.
            chunk_cache_mb: h5py chunk cache; see :meth:`HDF5Trajectory._open`.
            nan_policy: ``"error"``, ``"warn"`` or ``"ignore"`` for non-finite values.
            include_redundant: Expose ``pressure`` even though it is ``density * c_s^2``.
            periodic: Per-axis periodicity. Raw kinet files do not record it, so it comes
                from the dataset config; defaults to fully periodic, which is correct for
                the doubly-periodic case family.
            sim_index: Index along the leading simulation axis.
            time_axis: How to read the clock. See ``fmeval.data._timeaxis``; the default
                only changes behaviour for a remote file whose clock is chunked per frame.
        """
        self._open(path, chunk_cache_mb=chunk_cache_mb, nan_policy=nan_policy,
                   sim_index=sim_index)
        disc = json.loads(self._file.attrs["discretization"])
        shape = tuple(int(n) for n in disc["spatial"]["grid"])
        length = tuple(float(v) for v in disc["spatial"]["length"])
        spacing = tuple(l / n for l, n in zip(length, shape))
        n_spatial = len(shape)
        periodic_t = (
            tuple(bool(p) for p in periodic) if periodic is not None
            else (True,) * n_spatial
        )
        self._grid = GridSpec(
            shape=shape,
            spacing=spacing,
            periodic=periodic_t,
            dims=("x", "y", "z")[:n_spatial],
            origin=(0.0,) * n_spatial,
        )
        self._times = read_time_axis(
            self._file["time"], remote=self.is_remote, mode=time_axis
        )
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

    def read_frame(self, t: int, fields: Sequence[str]) -> dict[str, np.ndarray]:
        """Read one frame.

        ``ds[sim, :, t]`` returns ``(C, *spatial)`` directly for every channel count, so
        there is no squeeze, reshape or scalar special case. The time position is always a
        plain int -- never a slice. See the module docstring in ``base.py``.
        """
        out: dict[str, np.ndarray] = {}
        for name in fields:
            ds = self._file[FIELD_MAP[name]]
            out[name] = np.asarray(ds[self._sim, :, t], dtype=np.float64)
        return out
