"""What the HDF5 readers share: opening a local file or its published copy, and the bookkeeping.

``kinet_raw`` and ``well`` differ only in how a file lays its fields out, which each parses in
its own ``__init__`` and :meth:`~fmeval.data.base.Trajectory.read_frame`. Everything else --
opening the file locally or over HTTP, the chunk cache, the ``fields``/``times``/``grid``
properties, the provenance record and closing both handles -- is here, once.

A reader takes a *location*, not a path: a ``Path`` or an ``https://`` URL of the copy published
at ``paths.data_url``. The URL is kept as text in ``source`` and never pushed through ``Path``,
whose ``//`` collapse and ``.exists()`` on a URL are lies the first caller to check would believe.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np

from . import remote as _remote
from .base import GridSpec, NanPolicy, Trajectory
from .locate import is_url


class HDF5Trajectory(Trajectory):
    """A trajectory held in one HDF5 file. Subclasses parse the layout and read frames.

    A subclass calls :meth:`_open` first in its ``__init__``, then sets ``_grid``, ``_times``
    and ``_fields`` from the file, and names its format in :attr:`FORMAT`.
    """

    FORMAT: str = ""
    _grid: GridSpec
    _times: np.ndarray
    _fields: tuple[str, ...]

    def _open(self, path: str | Path, *, chunk_cache_mb: int, nan_policy: NanPolicy,
              sim_index: int) -> None:
        """Open ``path`` -- a local file or a URL -- and record where it came from.

        ``chunk_cache_mb`` sizes h5py's chunk cache. The default h5py cache is 1 MB, which is
        smaller than one velocity chunk (exactly 1 MB at 256^2), so raising it is a free win.
        A remote file also holds the block cache of :class:`~fmeval.data.remote.HTTPRangeFile`.
        """
        self.source = str(path)
        self.is_remote = is_url(path)
        self.location_source = "url" if self.is_remote else "local"
        self.nan_policy = nan_policy
        self._sim = sim_index
        self._remote: _remote.HTTPRangeFile | None = None
        if self.is_remote:
            self.path = None
            self._file, self._remote = _remote.open_h5(self.source,
                                                       chunk_cache_mb=chunk_cache_mb)
        else:
            self.path = Path(path)
            self._file = h5py.File(self.path, "r", rdcc_nbytes=chunk_cache_mb * 2**20,
                                   rdcc_nslots=_remote.CHUNK_CACHE_SLOTS)

    @property
    def fields(self) -> tuple[str, ...]:
        return self._fields

    @property
    def times(self) -> np.ndarray:
        return self._times

    @property
    def grid(self) -> GridSpec:
        return self._grid

    @property
    def meta(self) -> dict[str, Any]:
        """Where the file came from and its root attributes, JSON strings decoded."""
        attrs: dict[str, Any] = {}
        for key, value in self._file.attrs.items():
            if isinstance(value, (bytes, str)):
                text = value.decode() if isinstance(value, bytes) else value
                try:
                    attrs[key] = json.loads(text)
                except (ValueError, TypeError):
                    attrs[key] = text
            elif isinstance(value, np.generic):
                attrs[key] = value.item()
            else:
                attrs[key] = value
        meta: dict[str, Any] = {
            "path": self.source,
            "format": self.FORMAT,
            "n_frames": len(self._times),
            "fields": list(self._fields),
            "source": self.location_source,
            "source_attrs": attrs,
        }
        if self._remote is not None:
            meta["remote"] = self._remote.provenance()
        return meta

    def close(self) -> None:
        if getattr(self, "_file", None) is not None:
            self._file.close()
            self._file = None  # type: ignore[assignment]
        if getattr(self, "_remote", None) is not None:
            self._remote.close()
            self._remote = None
