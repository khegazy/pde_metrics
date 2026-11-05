"""Reader for real forecasts: a prediction paired with its target at every prediction step.

Every other reader supplies one trajectory, which the degradation ladder then damages. A forecast
supplies a *pair*: what a predictor produced and the truth it should have produced, at the same
steps. :class:`ForecastPairs` reads the targets and :meth:`ForecastPairs.predictions` the
predictions, two :class:`~fmeval.data.base.Trajectory` objects over one frame axis, and the
pipeline scores one against the other frame by frame (``fmeval.pipeline.run``, ``prediction=``).

**The layout.** One HDF5 file per forecast, ``<run>/forecast_t0-<start>.h5``, where ``<start>``
is the solver step the forecast starts from. Each field is a group (``rho``, ``u``,
``vorticity``, ...) holding one dataset per prediction step and side, ``pred_<step>`` and
``target_<step>``, each ``(C, X, Y)``, channel-first with ``x`` before ``y`` as in the raw kinet
layout. ``<step>`` counts solver steps of that run from the start. Two more groups, ``t`` and
``t_index``, hold the physical time and the absolute solver step of every dataset. The files carry
no root attributes: nothing records the domain size, so the reader takes it as ``length``, and
nothing records who produced the predictions.

**Several runs at several resolutions.** A dataset may list runs on different grids, so each
file has its own :class:`~fmeval.data.base.GridSpec` and every frame reports its own through
:meth:`grid_at`; the pipeline remaps each to the common analysis grid and refuses to pool frames
that land on different ones. Frames follow the files in the order listed, then the steps, and
:meth:`frame_columns` tells every result row which file and prediction step it came from.

**Three quirks of the real files**, each handled here and reproduced by
``tests.fixtures_h5.write_forecast``:

* The two clocks of a pair can disagree. Both sides of every file name the same absolute solver
  step in ``t_index``, which is checked exactly, but on the coarse runs the target's ``t`` of the
  first forecast lags the prediction's by a constant: 1.1276e-4 at 128^2 and 3.3829e-4 at 64^2,
  half a fine step and one and a half (measured 2026-11-04; the dataset page has the table).
  Both sides are therefore read on the prediction's clock, and the largest disagreement of each
  file is recorded in :attr:`meta`.
* The stored vorticity of the two sides is computed on different grid spacings on the coarse
  runs: the target's matches a spectral curl of its velocity at the physical spacing ``length / n``
  to 2.1% rms at 128^2, the prediction's one at unit spacing to 5.3%, so the stored prediction
  vorticity is about twice the target's for the same velocity (the dataset page has the
  measurement). Vorticity is a derived field and is recomputed from velocity on the analysis grid
  (:mod:`fmeval.derived`), but only when velocity is read beside it (issue 099), so reading
  vorticity without velocity is refused here rather than scored on the stored fields.
* ``stability_scale`` is a solver quantity with no canonical name, and is not read.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

import numpy as np

from . import remote as _remote
from .base import FIELDS, GridSpec, NanPolicy, Trajectory, register_reader
from .hdf5 import HDF5Trajectory

#: Canonical name -> the group a forecast file stores it under.
GROUPS: dict[str, str] = {"density": "rho", "velocity": "u", "vorticity": "vorticity"}

Side = Literal["target", "pred"]

#: The two members of each pair, as the dataset keys name them: ``target_<step>``, ``pred_<step>``.
SIDES: tuple[Side, Side] = ("target", "pred")

#: Relative tolerance of the check that the prediction clock advances by the same time every
#: solver step. On the real files the clock is the step times a constant to the last bit.
CLOCK_RTOL: float = 1e-9


class ForecastFile(HDF5Trajectory):
    """One side of one forecast file: one frame per prediction step, in step order."""

    FORMAT = "forecast_pairs"

    def __init__(
        self,
        path: str | Path,
        *,
        length: Sequence[float],
        side: Side = "target",
        chunk_cache_mb: int = _remote.DEFAULT_CHUNK_CACHE_MB,
        nan_policy: NanPolicy = "error",
    ) -> None:
        """Open one forecast file, locally or over HTTP, and check that its two sides pair up.

        Args:
            path: The ``.h5`` file, or an ``https://`` URL of its published copy.
            length: Physical extent of the domain along each axis; the spacing is
                ``length / n`` on every run, whatever its resolution.
            side: Which member of each pair this object reads.
            chunk_cache_mb: h5py chunk cache; see :meth:`HDF5Trajectory._open`.
            nan_policy: ``"error"``, ``"warn"`` or ``"ignore"`` for non-finite values.

        Raises:
            ValueError: If the two sides hold different steps or name different solver steps,
                the prediction clock does not advance uniformly, or ``length`` does not match
                the grid.
        """
        if side not in SIDES:
            raise ValueError(f"side must be one of {SIDES}, got {side!r}")
        self._open(path, chunk_cache_mb=chunk_cache_mb, nan_policy=nan_policy, sim_index=0)
        self.side = side
        clock, solver_step = self._file["t"], self._file["t_index"]
        steps = {s: sorted(int(k.split("_", 1)[1]) for k in clock if k.startswith(f"{s}_"))
                 for s in SIDES}
        if steps["target"] != steps["pred"] or len(steps["pred"]) < 2:
            raise ValueError(
                f"{self.source}: the targets are at steps {steps['target']} and the predictions "
                f"at {steps['pred']}; a forecast needs the same two or more steps on both sides")
        self.steps = np.asarray(steps["pred"], dtype=int)
        for k in self.steps:
            if int(solver_step[f"target_{k}"][0]) != int(solver_step[f"pred_{k}"][0]):
                raise ValueError(f"{self.source}: at step {k} the target is solver step "
                                 f"{int(solver_step[f'target_{k}'][0])} and the prediction "
                                 f"{int(solver_step[f'pred_{k}'][0])}; they are not a pair")
        times = {s: np.array([float(clock[f"{s}_{k}"][0]) for k in self.steps]) for s in SIDES}
        self._times = times["pred"]
        self.clock_offset = float(np.max(np.abs(times["target"] - times["pred"])))
        #: Physical time per solver step, from the prediction clock: a lead of ``k`` steps is
        #: ``k * step_time`` whatever the run's resolution.
        self.step_time = float(np.ptp(self._times) / np.ptp(self.steps))
        ramp = self._times[0] + (self.steps - self.steps[0]) * self.step_time
        if self.step_time <= 0 or not np.allclose(self._times, ramp, rtol=CLOCK_RTOL, atol=0):
            raise ValueError(f"{self.source}: the prediction clock {self._times.tolist()} does "
                             f"not advance by one time per solver step over steps "
                             f"{self.steps.tolist()}, so a lead time cannot be read from it")

        present = [name for name, group in GROUPS.items() if group in self._file]
        if not present:
            raise ValueError(f"{self.source}: none of the groups {sorted(GROUPS.values())}")
        shape = self._file[GROUPS[present[0]]][f"{side}_{self.steps[0]}"].shape[1:]
        if len(length) != len(shape):
            raise ValueError(f"length {list(length)} has {len(length)} axes; the grid is {shape}")
        self._grid = GridSpec(
            shape=tuple(int(n) for n in shape),
            spacing=tuple(float(extent) / n for extent, n in zip(length, shape)),
            boundary=("periodic",) * len(shape),
            dims=("x", "y", "z")[:len(shape)],
            origin=(0.0,) * len(shape),
        )
        self._fields = tuple(
            name for name in present
            if self._file[GROUPS[name]][f"{side}_{self.steps[0]}"].shape
            == (FIELDS[name].n_channels(len(shape)), *shape))

    def read_frame(self, t: int, fields: Sequence[str]) -> dict[str, np.ndarray]:
        """Read this side of prediction step ``self.steps[t]``; each step is its own dataset."""
        key = f"{self.side}_{self.steps[t]}"
        return {name: np.asarray(self._file[GROUPS[name]][key], dtype=np.float64)
                for name in fields}


@register_reader("forecast_pairs")
class ForecastPairs(Trajectory):
    """The targets of several forecasts, one frame per (run, start, prediction step).

    :meth:`predictions` opens the predictions over the same frames.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        files: Sequence[str],
        length: Sequence[float],
        side: Side = "target",
        chunk_cache_mb: int = _remote.DEFAULT_CHUNK_CACHE_MB,
        nan_policy: NanPolicy = "error",
    ) -> None:
        """Open every forecast file listed.

        Args:
            path: The directory holding one subdirectory per run, or its published URL.
            files: Each forecast file below ``path``, without ``.h5``, as
                ``<run>/forecast_t0-<start>``; its frames follow in this order. Listed rather
                than discovered, so a published copy, which cannot be listed, reads the same
                files, and a list rather than a mapping, so a config override replaces it.
            length: Physical extent of the domain along each axis, shared by every run.
            side: ``"target"``, or ``"pred"`` for the predictions; see :meth:`predictions`.
            chunk_cache_mb: h5py chunk cache of each file.
            nan_policy: ``"error"``, ``"warn"`` or ``"ignore"`` for non-finite values.

        Raises:
            ValueError: If no forecast is listed, or the files do not share a field.
        """
        if not files:
            raise ValueError("files must list at least one forecast file")
        self.source = str(path).rstrip("/")
        self.nan_policy = nan_policy
        self.side = side
        #: ``<run>/forecast_t0-<start>``: the file each frame came from, as its rows record it.
        self.labels: list[str] = [str(f) for f in files]
        self._options = {"files": self.labels, "length": list(length),
                         "chunk_cache_mb": chunk_cache_mb, "nan_policy": nan_policy}
        self._files: list[ForecastFile] = []
        try:
            for label in self.labels:
                self._files.append(ForecastFile(
                    f"{self.source}/{label}.h5", length=length, side=side,
                    chunk_cache_mb=chunk_cache_mb, nan_policy=nan_policy))
        except BaseException:
            self.close()
            raise
        self.location_source = self._files[0].location_source
        self._frames = [(i, j) for i, f in enumerate(self._files) for j in range(len(f))]
        self._times = np.concatenate([f.times for f in self._files])
        self._fields = tuple(name for name in GROUPS
                             if all(name in f.fields for f in self._files))
        if not self._fields:
            raise ValueError(f"the forecast files under {self.source} share no field")

    def predictions(self) -> ForecastPairs:
        """The predictions paired with this reader's targets: same files, same frames."""
        return ForecastPairs(self.source, **self._options, side="pred")

    @property
    def fields(self) -> tuple[str, ...]:
        return self._fields

    @property
    def times(self) -> np.ndarray:
        """The prediction clock of every frame, file after file; not monotone across files."""
        return self._times

    @property
    def grid(self) -> GridSpec:
        """The first file's grid; a frame of another run reports its own through :meth:`grid_at`."""
        return self._files[0].grid

    def grid_at(self, t: int) -> GridSpec:
        return self._files[self._frames[t][0]].grid

    def frame_columns(self, t: int) -> dict[str, Any]:
        """The file, the run's native resolution and the lead of frame ``t``."""
        i, j = self._frames[t]
        f = self._files[i]
        return {"trajectory": self.labels[i], "param_resolution": f.grid.shape[0],
                "lead_step": int(f.steps[j]), "lead_time": float(f.steps[j] * f.step_time)}

    @property
    def meta(self) -> dict[str, Any]:
        """Where each file came from, its steps and the largest disagreement of its two clocks."""
        return {
            "path": self.source,
            "format": ForecastFile.FORMAT,
            "side": self.side,
            "n_frames": len(self._times),
            "fields": list(self._fields),
            "source": self.location_source,
            "files": {label: {"path": f.source, "grid": list(f.grid.shape),
                              "steps": f.steps.tolist(), "clock_offset": f.clock_offset}
                      for label, f in zip(self.labels, self._files)},
        }

    def read_frame(self, t: int, fields: Sequence[str]) -> dict[str, np.ndarray]:
        """Read frame ``t`` from its file.

        Raises:
            ValueError: If vorticity is asked for without velocity; see the module docstring.
        """
        if "vorticity" in fields and "velocity" not in fields:
            raise ValueError(
                "vorticity was requested without velocity. The stored vorticity of the "
                "predictions and of the targets is computed on different grid spacings, so it "
                "is only usable recomputed from velocity, which needs velocity read beside it "
                "(issues/099). Add a metric that accepts velocity to the run.")
        i, j = self._frames[t]
        return self._files[i].read_frame(j, fields)

    def close(self) -> None:
        for f in self._files:
            f.close()
