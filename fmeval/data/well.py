"""Reader for the PolymathicAI *Well* layout.

The second format, and therefore the test of whether the data contract actually holds. The
whole reader is one method plus four properties; the evaluator, the pipeline, the
degradations and every metric are untouched by its existence.

Three differences from the raw kinet layout have to be absorbed here and nowhere else:

* **float32 rather than float64.** Cast on read; the canonical contract is float64.
* **No channel axis on scalars.** ``t0_fields/density`` is ``(sim, T, X, Y)``, so a channel
  axis of length one is inserted.
* **Velocity is channel-LAST**, ``t1_fields/velocity`` is ``(sim, T, X, Y, D)``. A
  ``moveaxis`` fixes it. This is the one line where a mistake would be invisible on square
  data, which is why the fixtures write u = 1 and v = 2 and the grids are non-square.

The spatial axis order is the same as kinet's: the file declares
``dimensions.attrs["spatial_dims"] = ["x", "y"]`` and stores them in that order, so no
transpose is needed -- only the channel move.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from . import remote as _remote
from ._timeaxis import TimeAxisMode, read_time_axis
from .base import (
    DEGENERATE_FIELDS,
    FIELDS,
    REDUNDANT_FIELDS,
    GridSpec,
    NanPolicy,
    register_reader,
)
from .hdf5 import HDF5Trajectory

#: Canonical name -> (group, dataset). Velocity lives in the rank-1 group.
FIELD_MAP: dict[str, tuple[str, str]] = {
    "density": ("t0_fields", "density"),
    "pressure": ("t0_fields", "pressure"),
    "temperature": ("t0_fields", "temperature"),
    "vorticity": ("t0_fields", "vorticity"),
    "velocity": ("t1_fields", "velocity"),
}




@register_reader("well")
class WellTrajectory(HDF5Trajectory):
    """One rollout from a Well-format HDF5 file."""

    FORMAT = "well"

    def __init__(
        self,
        path: str | Path,
        *,
        chunk_cache_mb: int = _remote.DEFAULT_CHUNK_CACHE_MB,
        nan_policy: NanPolicy = "error",
        include_redundant: bool = False,
        include_degenerate: bool = False,
        sim_index: int = 0,
        time_axis: TimeAxisMode = "auto",
    ) -> None:
        """Open a Well-format file, locally or over HTTP.

        Args:
            path: Path to the ``.h5`` file, or an ``https://`` URL of the published copy.
            chunk_cache_mb: h5py chunk cache size.
            nan_policy: ``"error"``, ``"warn"`` or ``"ignore"`` for non-finite values.
            include_redundant: Expose ``pressure``.
            include_degenerate: Expose ``temperature``, which is constant for an
                isothermal run and therefore not a field in any useful sense.
            sim_index: Index along the leading trajectory axis.
            time_axis: How to read the clock. See ``fmeval.data._timeaxis``. This layout
                stores it contiguously, so the default reads it directly either way.
        """
        self._open(path, chunk_cache_mb=chunk_cache_mb, nan_policy=nan_policy,
                   sim_index=sim_index)

        dims = self._file["dimensions"]
        names = [_text(n) for n in dims.attrs.get("spatial_dims", ["x", "y"])]
        expected = ("x", "y", "z")[: len(names)]
        if tuple(names) != expected:
            raise ValueError(
                f"{self.source}: spatial_dims is {names}, expected {list(expected)}. "
                "A different order would need a transpose, which this reader does not do."
            )
        coords = [np.asarray(dims[name][:], dtype=np.float64) for name in names]
        shape = tuple(len(c) for c in coords)
        spacing = tuple(
            float(c[1] - c[0]) if len(c) > 1 else 1.0 for c in coords
        )
        periodic = tuple(
            f"{name}_periodic" in self._file.get("boundary_conditions", {})
            for name in names
        )
        self._grid = GridSpec(
            shape=shape,
            spacing=spacing,
            periodic=periodic,
            dims=tuple(names),
            origin=tuple(float(c[0]) for c in coords),
        )
        self._times = read_time_axis(
            dims["time"], remote=self.is_remote, mode=time_axis
        )

        available = []
        for canonical, (group, dataset) in FIELD_MAP.items():
            # Unlike the raw format, the Well writer broadcasts temperature to the full grid,
            # so it cannot be detected by shape and is excluded by name.
            if canonical in DEGENERATE_FIELDS and not include_degenerate:
                continue
            if canonical in REDUNDANT_FIELDS and not include_redundant:
                continue
            if group not in self._file or dataset not in self._file[group]:
                continue
            ds = self._file[group][dataset]
            n_channels = FIELDS[canonical].n_channels(len(shape))
            # Rank-0 fields: (sim, T, *spatial). Rank-1: (sim, T, *spatial, D).
            wanted = 2 + len(shape) + (1 if n_channels > 1 else 0)
            if ds.ndim != wanted:
                continue
            if n_channels > 1 and ds.shape[-1] != n_channels:
                continue
            available.append(canonical)
        self._fields = tuple(available)

    def read_frame(self, t: int, fields: Sequence[str]) -> dict[str, np.ndarray]:
        """Read one frame, normalising channel placement and dtype.

        The time position is always a plain int, never a slice -- the same invariant the raw
        reader observes, for the same reason.
        """
        out: dict[str, np.ndarray] = {}
        for name in fields:
            group, dataset = FIELD_MAP[name]
            ds = self._file[group][dataset]
            if FIELDS[name].n_channels(self._grid.n_spatial) > 1:
                # (X, Y, D) -> (D, X, Y). The one line where an error would be invisible
                # on a square grid.
                out[name] = np.moveaxis(
                    np.asarray(ds[self._sim, t], dtype=np.float64), -1, 0
                )
            else:
                out[name] = np.asarray(ds[self._sim, t], dtype=np.float64)[np.newaxis]
        return out


def _text(value: object) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)
