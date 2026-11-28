"""Rewrite one rollout of kinet's grouped HDF5 layout into the flat layout ``kinet_raw`` reads.

    python -m fmeval.data.convert_kinet SOURCE.h5 DESTINATION.h5

Research-grade. This is a tool, not a reader: the converted file is opened by
:class:`~fmeval.data.kinet_raw.KinetRawTrajectory` exactly as the shear-layer files are. The
grouped layout (``dataset_specs/00_how_to_use_kinet.md``, Section 5) differs from the flat one
in four ways, each handled here:

* The fields sit under ``observables/`` with one slot per solver step, step ``s`` in slot
  ``s - 1``, and the initial condition sits apart under ``initial_conditions/``. It becomes
  frame 0, as in the flat files.
* A run saved every Nth step leaves NaN in each unsaved slot of ``time/time_index``; only the
  finite slots are kept. Step 1 is always saved, so such a run holds steps 1, N, 2N, ...; step 1
  is dropped when that makes the frames evenly spaced, which ``frame_stride`` and
  ``dataset.time.reduction`` assume. Any other uneven cadence (a resume that changed it) is
  refused, except on a run with an adaptive time step (``discretization.temporal.type`` is
  ``adaptive``: kinet's finite-volume PonD solver), whose frames are evenly spaced in neither
  steps nor time and whose last frame is the step that lands on the end time, off the cadence.
* The clock is ``time/time_convection``, in domain crossings L/(Ma c_s), the unit of the flat
  files' ``time``; ``time/time`` counts lattice steps. A rollout written before kinet recorded
  ``time_convection`` (the Sod and obstacle runs of 2026-05) has only ``time/time``, which there
  is kinet's nondimensional clock (step / 5 on the 3001 x 5 Sod runs), and that is carried. An
  adaptive run's ``time/time`` is the case's own physical time (its last entry is the configured
  end time, despite its ``step`` unit label), and that is carried, so the converted file is read
  in the case's units: lengths from ``discretization.spatial.length``, velocity as stored.
* ``pressure`` is carried only under ``pressure_convention == "absolute"`` (kinet's compressible
  physics). The weakly compressible physics stores the gauge ``(rho - 1) c_s^2``
  (kinet ``kinet/io/rollout/attrs.py``, ``PRESSURE_CONVENTION_ATTR``), which is not a pressure.
  A rollout older than that attribute has its pressure taken as absolute only if its initial
  condition satisfies kinet's ideal-gas law ``p = rho T``, which a gauge field does not.
  The populations, the temperature, the energy and the stability fields are dropped.

Only the ``kinet_raw`` layout is written. The candidate layout of ``fmeval/data/forecast.py``
shares everything up to the frame selection, which is split out of this function when that
second writer is added.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np

from .kinet_raw import FIELD_MAP, KinetRawTrajectory

#: kinet's values of the ``pressure_convention`` root attribute; only the first is a pressure.
PRESSURE_CONVENTIONS = ("absolute", "fluctuation_referenced")


def convert_kinet_grouped(source: str | Path, destination: str | Path, every: int = 1,
                          times: list[float] | None = None) -> Path:
    """Write the grouped rollout ``source`` to ``destination`` in the flat ``kinet_raw`` layout.

    Every root attribute is copied, so the identity key and its digests travel with the data.
    ``discretization.temporal`` is rewritten to count the frames written (``grid`` is the
    number of frames minus one, ``resolution`` the solver steps between frames), the solver
    step of every frame is written as the 1-D ``time_index`` dataset the older flat files also
    hold, and ``converted_from`` records the source path. Fields are chunked one frame per
    chunk, as kinet writes them. The file is written as ``<destination>.partial`` and renamed
    only once ``KinetRawTrajectory`` has opened it, so an interrupted conversion never leaves a
    file that reads.

    Args:
        source: A grouped ``rollout.h5`` written by kinet. Read only.
        destination: The flat file to create. Its folders are created; the file is not
            overwritten.
        every: Keep the initial condition, the last saved frame and every ``every``-th frame
            before it, so that only the frames a dataset evaluates are stored. On a fixed-step
            run it must divide the number of frames after the initial condition, so the kept
            frames stay evenly spaced from the initial condition on.
        times: In place of ``every``, on a run with an adaptive step only: keep the initial
            condition and, for each of these times, the saved frame nearest it on the clock.
            Such runs save at different times on different grids, so this is how a finer run
            is stored at the times a coarser one holds.

    Returns:
        ``destination``.

    Raises:
        FileExistsError: If ``destination`` or its ``.partial`` file exists.
        ValueError: If the rollout is incomplete, its slots and step counts disagree, its saved
            steps are unevenly spaced, ``every`` does not divide them, its clock does not
            increase, a field is not float64 on the declared grid, or its pressure convention
            is unknown.
    """
    source, destination = Path(source), Path(destination)
    partial = destination.with_name(destination.name + ".partial")
    for path in (destination, partial):
        if path.exists():
            raise FileExistsError(f"{path} exists; a conversion never overwrites a file.")

    with h5py.File(source, "r") as src:
        attrs = dict(src.attrs)
        if attrs.get("kinet_rollout_status") != "complete":
            raise ValueError(f"{source}: kinet_rollout_status is "
                             f"{attrs.get('kinet_rollout_status')!r}, not 'complete'.")
        disc = json.loads(attrs["discretization"])
        adaptive = disc["temporal"].get("type") == "adaptive"
        step = src["time/time_index"][:]
        clock_name = "time_convection" if "time/time_convection" in src and not adaptive else "time"
        clock = src[f"time/{clock_name}"][:]
        saved = np.flatnonzero(np.isfinite(step))
        if (len(step) != int(disc["temporal"]["grid"])
                or not np.array_equal(saved, np.flatnonzero(np.isfinite(clock)))
                or not np.array_equal(step[saved], saved + 1)):
            raise ValueError(
                f"{source}: the {len(step)} time slots, discretization.temporal.grid "
                f"({disc['temporal']['grid']}) and the finite entries of time_index and "
                f"time/{clock_name} do not agree that solver step s is slot s - 1.")
        frame_step = np.concatenate([[0], saved + 1])
        if len(np.unique(np.diff(frame_step))) > 1 and frame_step[1] == 1:
            frame_step, saved = np.delete(frame_step, 1), saved[1:]
        cadence = np.unique(np.diff(frame_step))
        if len(cadence) != 1 and not adaptive:
            raise ValueError(f"{source}: the saved steps {frame_step[:6].tolist()}... are not "
                             "evenly spaced, so no frame_stride or reduction would be uniform.")
        if times is not None:
            if not adaptive or every != 1:
                raise ValueError(f"{source}: times= selects frames of an adaptive-step run "
                                 "only, and replaces every=.")
            saved = np.unique([saved[np.abs(clock[saved] - t).argmin()] for t in times])
        elif every < 1 or (len(saved) % every and not adaptive):
            raise ValueError(f"{source}: every={every} must be a positive divisor of the "
                             f"{len(saved)} saved frames after the initial condition.")
        saved = saved[::-1][::every][::-1]
        frame_step = np.concatenate([[0], saved + 1])
        times = np.concatenate([src[f"initial_conditions/time/{clock_name}"][:], clock[saved]])
        if not np.all(np.diff(times) > 0):
            raise ValueError(f"{source}: the clock time/{clock_name} does not increase.")

        convention = attrs.get("pressure_convention")
        ic = src["initial_conditions/observables"]
        if convention is None and {"pressure", "temperature"} <= set(ic) and np.allclose(
                ic["pressure"][:], ic["density"][:] * ic["temperature"][:], rtol=1e-12, atol=0):
            convention = "absolute"
        if "observables/pressure" in src and convention not in PRESSURE_CONVENTIONS:
            raise ValueError(f"{source}: pressure_convention {convention!r} is none of "
                             f"{PRESSURE_CONVENTIONS} (a missing one is absolute only where the "
                             "initial p = rho T), so the stored pressure cannot be read.")
        names = [name for name in FIELD_MAP.values() if f"observables/{name}" in src
                 and (name != "pressure" or convention == "absolute")]
        grid = tuple(int(n) for n in disc["spatial"]["grid"])
        for name in names:
            ds = src[f"observables/{name}"]
            if ds.dtype != np.float64 or ds.shape[2:] != (len(step), *grid):
                raise ValueError(f"{source}: observables/{name} is {ds.dtype} {ds.shape}; "
                                 f"expected float64 (N, C, {len(step)}, *{grid}).")

        disc["temporal"]["grid"] = len(times) - 1
        if not adaptive:
            disc["temporal"]["resolution"] = float(cadence[0] * every) * disc["temporal"][
                "resolution"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        with h5py.File(partial, "w-") as dst:
            dst.attrs.update(attrs)
            dst.attrs["discretization"] = json.dumps(disc)
            dst.attrs["converted_from"] = str(source.resolve())
            dst.create_dataset("time", data=times).attrs.update(units="-", source=clock_name)
            dst.create_dataset("time_index", data=frame_step.astype(np.float64))
            for name in names:
                ds = src[f"observables/{name}"]
                out = dst.create_dataset(name, shape=(*ds.shape[:2], len(times), *grid),
                                         dtype=np.float64, chunks=(1, ds.shape[1], 1, *grid))
                out.attrs.update(ds.attrs)
                out[:, :, 0] = src[f"initial_conditions/observables/{name}"][:, :, 0]
                for frame, slot in enumerate(saved, start=1):
                    out[:, :, frame] = ds[:, :, int(slot)]
    KinetRawTrajectory(partial).close()
    partial.rename(destination)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="grouped rollout.h5 written by kinet")
    parser.add_argument("destination", type=Path, help="flat .h5 file to create")
    parser.add_argument("--every", type=int, default=1,
                        help="keep the initial condition and every Nth frame after it")
    parser.add_argument("--times", type=float, nargs="+",
                        help="adaptive-step runs: keep the saved frame nearest each time instead")
    args = parser.parse_args()
    print(convert_kinet_grouped(args.source, args.destination, args.every, args.times))
