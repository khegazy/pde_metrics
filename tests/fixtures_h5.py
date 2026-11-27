"""Builders for tiny synthetic HDF5 files mirroring the real on-disk schemas.

These are deliberately faithful to the *quirks*, not just the shapes: JSON-string root
attributes, all-NaN fields at t=0, the spatially degenerate temperature, and pressure
written as ``density * c_s^2`` rather than ``density / 3`` (they differ in the last ulp).
A fixture that stops reproducing a quirk is itself a signal that the real format has
changed.

Grids are **non-square** (16x8). Every real dataset is square, so a reader that transposes
x and y passes every test on real-shaped data; the fixtures are the only place that bug
can be caught.
"""

from __future__ import annotations

import json
from pathlib import Path

import h5py
import numpy as np

# Imported as a module because conftest imports this one: ``conftest.synthetic_field`` is
# looked up when a writer runs, after both modules have finished importing.
from tests import conftest

#: Non-square on purpose. See the module docstring.
SHAPE: tuple[int, int] = (16, 8)
N_FRAMES: int = 5


def _time_axis(n: int) -> np.ndarray:
    return np.arange(n, dtype=np.float64) * 0.25


def write_kinet_raw(path: Path, shape: tuple[int, ...] = SHAPE,
                    n_frames: int = N_FRAMES, times: np.ndarray | None = None) -> Path:
    """Write a synthetic file in the raw kinet layout ``(1, C, T, *spatial)``.

    Reproduces: JSON-string root attrs, one-frame chunking, all-NaN ``stability_scale``
    at t=0, NaN ``time_scale[0]``, degenerate ``temperature``, ``pressure = density*c_s^2``.
    Velocity channel 0 is constant 1.0 and channel 1 constant 2.0 at t=0 so a channel-swap
    or an x/y transpose is detectable.

    The ``time`` dataset is chunked ``(1,)`` as the real solver writes it, which is what
    makes reading it in full expensive over HTTP. Pass ``times`` to write a deliberately
    non-uniform clock, which the affine reconstruction must refuse rather than smooth over.
    """
    n_spatial = len(shape)
    with h5py.File(path, "w") as f:
        f.attrs["discretization"] = json.dumps(
            {
                "spatial": {
                    "grid": list(shape),
                    "resolution": 1.0,
                    "length": [float(n) for n in shape],
                },
                "temporal": {
                    "grid": n_frames - 1,
                    "resolution": 1.0,
                    "length": float(n_frames - 1),
                },
            }
        )
        f.attrs["characteristic_scales"] = json.dumps(
            {"mass": 1, "length": 1.0, "time": 1.0, "temperature": 1}
        )
        f.attrs["units"] = json.dumps({"system": "dimensionless"})
        f.attrs["kinet_rollout_status"] = "complete"
        f.attrs["kinet_last_completed_step"] = np.int64(n_frames - 1)

        def make(name: str, n_channels: int, gen) -> None:
            data = np.empty((1, n_channels, n_frames, *shape), dtype=np.float64)
            for t in range(n_frames):
                data[0, :, t] = gen(t)
            f.create_dataset(
                name, data=data, chunks=(1, n_channels, 1, *shape)
            ).attrs["units"] = "-"

        density = {}

        def gen_density(t: int) -> np.ndarray:
            arr = 1.0 + 1e-3 * conftest.synthetic_field(shape, 1, seed=100 + t)
            density[t] = arr
            return arr

        make("density", 1, gen_density)
        # The solver writes rho * c_s^2, not rho / 3; those differ in the last ulp and
        # the fixture reproduces the real arithmetic.
        cs2 = np.float64(1.0) / np.float64(3.0)
        make("pressure", 1, lambda t: density[t] * cs2)

        def gen_velocity(t: int) -> np.ndarray:
            if t == 0:
                v = np.empty((n_spatial, *shape))
                for c in range(n_spatial):
                    v[c] = float(c + 1)  # u=1, v=2: catches channel swap and transpose
                return v
            return 0.04 * conftest.synthetic_field(shape, n_spatial, seed=200 + t)

        make("velocity", n_spatial, gen_velocity)
        make("vorticity", 1, lambda t: 0.01 * conftest.synthetic_field(shape, 1, seed=300 + t))
        make("F", 9, lambda t: np.abs(conftest.synthetic_field(shape, 9, seed=400 + t)) + 0.1)

        # All-NaN at t=0, finite after -- exactly as the real solver writes them.
        def gen_stability(t: int) -> np.ndarray:
            if t == 0:
                return np.full((1, *shape), np.nan)
            return np.full((1, *shape), 2.0)

        make("stability_scale", 1, gen_stability)
        make("stabilized_time_scale", 1, gen_stability)

        # Spatially degenerate: stored (1, 1, T, 1, 1).
        temp = np.full((1, 1, n_frames, *([1] * n_spatial)), 1.0 / 3.0)
        f.create_dataset("temperature", data=temp).attrs["units"] = "-"

        clock = _time_axis(n_frames) if times is None else np.asarray(times, dtype=np.float64)
        f.create_dataset("time", data=clock, chunks=(1,)).attrs["units"] = "-"
        f.create_dataset(
            "time_index", data=np.arange(n_frames, dtype=np.float64), chunks=(1,)
        ).attrs["units"] = "-"
        ts = np.full(n_frames, 0.5009)
        ts[0] = np.nan  # NaN at index 0, as in the real file
        f.create_dataset("time_scale", data=ts, chunks=(1,)).attrs["units"] = "-"
    return path


def write_kinet_taylor_green(path: Path, cells: int, amplitude_error: float = 0.0) -> Path:
    """A converted kinet ``taylor_green_vortex`` run in lattice units on ``cells``^2 cells.

    The vortex of kinet's case after ``s`` solver steps, ``k = 2 pi / cells``, node ``i`` at
    ``i + 1/2`` cells, ``D = (1 + amplitude_error) u_l exp(-2 nu_l k^2 s)`` (Taylor 1923):
    ``u = D sin kx cos ky``, ``v = -D cos kx sin ky``, vorticity ``2 D k sin kx sin ky``.
    ``Re = u_l cells / nu_l = 50`` with ``u_l = 0.64 / cells``, diffusive scaling as on the
    real runs. The clock is ``time_convection``, ``s u_l / cells``, the same five times on every
    grid, and ``normalization_plan`` holds ``L_l``, ``u_l``, ``nu_l``. Written from lattice
    quantities alone, so a reader's mapping to the box ``2 pi`` is checked, not copied. Square,
    as kinet's case is; ``sin x cos y`` is not symmetric in x and y, so a transpose still shows.
    """
    times = _time_axis(N_FRAMES)
    write_kinet_raw(path, shape=(cells, cells), times=times)
    speed, k = 0.64 / cells, 2 * np.pi / cells
    viscosity = speed * cells / 50.0
    x, y = np.meshgrid(k * (np.arange(cells) + 0.5), k * (np.arange(cells) + 0.5), indexing="ij")
    with h5py.File(path, "r+") as f:
        f.attrs["group"] = "taylor_green_vortex"
        f.attrs["normalization_plan"] = json.dumps(
            {"lattice": {"L_l": float(cells), "u_l": speed, "nu_l": viscosity}})
        f["time"].attrs["source"] = "time_convection"
        for t, clock in enumerate(times):
            amplitude = (1 + amplitude_error) * speed * np.exp(
                -2 * viscosity * k**2 * clock * cells / speed)
            f["velocity"][0, :, t] = amplitude * np.stack([np.sin(x) * np.cos(y),
                                                           -np.cos(x) * np.sin(y)])
            f["vorticity"][0, 0, t] = 2 * amplitude * k * np.sin(x) * np.sin(y)
    return path


def write_kinet_sod(path: Path, nodes: int, steps_per_frame: int = 1) -> Path:
    """A converted kinet ``sod`` run in lattice units on ``nodes`` by 3 nodes that never moves.

    Every frame is the initial condition: Sod's states as Toro (2009) Table 4.1 gives them,
    ``(rho, p) = (1, 1)`` on the left and ``(0.125, 0.1)`` on the right, at rest, ``gamma`` 1.4,
    with node ``i`` on the left where ``i + 1/2 < nodes / 2``, as kinet paints the tube, so for odd
    ``nodes`` the jump is the face ``(nodes - 1) / 2``. Frame ``k`` is solver step
    ``k steps_per_frame`` (``time_index``). A reader's exact solution is checked against Toro's
    numbers and this file's cells, steps and jump, not against these frozen frames.
    """
    write_kinet_raw(path, shape=(nodes, 3))
    left = (np.arange(nodes) + 0.5 < nodes / 2)[None, :, None]
    frames = (N_FRAMES, nodes, 3)
    with h5py.File(path, "r+") as f:
        f.attrs["group"], f.attrs["gamma"] = "sod", 1.4
        f["time_index"][:] = steps_per_frame * np.arange(N_FRAMES)
        f["density"][0, 0] = np.broadcast_to(np.where(left, 1.0, 0.125), frames)
        f["pressure"][0, 0] = np.broadcast_to(np.where(left, 1.0, 0.1), frames)
        f["velocity"][0] = 0.0
    return path


def write_kinet_grouped(path: Path, save_every: int = 3,
                        pressure_convention: str = "absolute") -> Path:
    """Write the frames of :func:`write_kinet_raw` in the grouped layout of the current kinet.

    Frame 0 goes under ``initial_conditions/`` and frame ``k`` to solver step ``k *
    save_every``, in slot ``step - 1`` of a time axis whose other slots are NaN; the clock is
    ``time/time_convection``. Reproduces: step 1 saved off the cadence, with values no flat
    frame holds, so a conversion that keeps it fails; pressure labelled by
    ``pressure_convention``; the degenerate ``temperature``. A correct conversion of this file
    is therefore the flat fixture itself, value for value. The flat file is left beside it.
    """
    flat = write_kinet_raw(path.with_name(path.stem + "_flat.h5"))
    n_steps = (N_FRAMES - 1) * save_every
    slots = np.arange(1, N_FRAMES) * save_every - 1
    step = np.full(n_steps, np.nan)
    step[slots] = slots + 1
    step[0] = 1.0
    with h5py.File(flat, "r") as src, h5py.File(path, "w") as f:
        f.attrs.update(src.attrs)
        disc = json.loads(src.attrs["discretization"])
        disc["temporal"].update(grid=n_steps, length=float(n_steps))
        f.attrs["discretization"] = json.dumps(disc)
        f.attrs["pressure_convention"] = pressure_convention
        f.attrs["identity_key"] = "0f1x7e"
        for name in ("density", "velocity", "vorticity", "pressure", "temperature"):
            data = src[name][:]
            slotted = np.full((*data.shape[:2], n_steps, *data.shape[3:]), np.nan)
            slotted[:, :, slots] = data[:, :, 1:]
            slotted[:, :, 0] = data[:, :, 1] + 0.5
            f.create_dataset(f"observables/{name}", data=slotted,
                             chunks=(*data.shape[:2], 1, *data.shape[3:]))
            f.create_dataset(f"initial_conditions/observables/{name}", data=data[:, :, :1])
        # The flat clock is 0.25 per frame; step / save_every is exact for every saved step.
        f.create_dataset("time/time_index", data=step, chunks=(1,))
        f.create_dataset("time/time", data=step, chunks=(1,))
        f.create_dataset("time/time_convection", data=step / save_every * 0.25, chunks=(1,))
        for name in ("time_index", "time", "time_convection"):
            f.create_dataset(f"initial_conditions/time/{name}", data=np.zeros(1))
    return path

def write_well(path: Path, shape: tuple[int, int] = SHAPE,
               n_frames: int = N_FRAMES,
               bc_types: tuple[str | None, str | None] = ("PERIODIC", "PERIODIC")) -> Path:
    """Write a synthetic file in the PolymathicAI *Well* layout.

    Differs from raw kinet in three ways the reader must absorb: float32, no leading
    channel axis on scalars, and ``t1_fields/velocity`` is **channel-last**
    ``(1, T, *spatial, D)``. Velocity is u=1, v=2 at t=0, so a missed ``moveaxis`` shows up
    immediately. ``bc_types`` gives each axis's ``bc_type`` (``PERIODIC``, ``WALL``,
    ``OPEN``, ...), or None to leave the axis undeclared.
    """
    with h5py.File(path, "w") as f:
        f.attrs["dataset_name"] = "synthetic"
        f.attrs["grid_type"] = "cartesian"
        f.attrs["n_spatial_dims"] = len(shape)
        f.attrs["n_trajectories"] = 1

        dims = f.create_group("dimensions")
        dims.attrs["spatial_dims"] = ["x", "y"]
        dims.create_dataset("time", data=_time_axis(n_frames))
        dims.create_dataset("x", data=np.arange(shape[0], dtype=np.float64))
        dims.create_dataset("y", data=np.arange(shape[1], dtype=np.float64))

        t0 = f.create_group("t0_fields")
        t0.attrs["field_names"] = ["density", "pressure", "vorticity"]
        dens = np.stack(
            [1.0 + 1e-3 * conftest.synthetic_field(shape, 1, seed=100 + t)[0]
             for t in range(n_frames)]
        )[None]
        t0.create_dataset("density", data=dens.astype(np.float32))
        t0.create_dataset("pressure", data=(dens / 3.0).astype(np.float32))
        vort = np.stack(
            [0.01 * conftest.synthetic_field(shape, 1, seed=300 + t)[0] for t in range(n_frames)]
        )[None]
        t0.create_dataset("vorticity", data=vort.astype(np.float32))

        t1 = f.create_group("t1_fields")
        t1.attrs["field_names"] = ["velocity"]
        vel = np.empty((1, n_frames, *shape, len(shape)), dtype=np.float32)
        for t in range(n_frames):
            if t == 0:
                for c in range(len(shape)):
                    vel[0, t, ..., c] = float(c + 1)
            else:
                v = 0.04 * conftest.synthetic_field(shape, len(shape), seed=200 + t)
                vel[0, t] = np.moveaxis(v, 0, -1)
        t1.create_dataset("velocity", data=vel)

        bc = f.create_group("boundary_conditions")
        for i, (dim, bc_type) in enumerate(zip(("x", "y"), bc_types)):
            if bc_type is None:  # an axis no group declares
                continue
            g = bc.create_group(f"{dim}_{bc_type.lower()}")
            g.attrs["bc_type"] = bc_type
            g.attrs["associated_dims"] = [dim]
            g.create_dataset("mask", data=np.zeros(shape[i], dtype=np.int8))
    return path


def write_forecast(root: Path, run: str, start: int, shape: tuple[int, int] = SHAPE, *,
                   steps: tuple[int, ...] = (2, 4, 6), step_time: float = 0.25,
                   target_lag: float = 0.0) -> Path:
    """Write ``root/run/forecast_t0-<start>.h5`` in the layout of the real forecast files.

    One group per field, ``rho``, ``u``, ``vorticity`` and ``stability_scale``, each holding
    ``pred_<step>`` and ``target_<step>`` as ``(C, X, Y)``, plus ``t`` and ``t_index`` holding the
    physical time and the absolute solver step of each; no root attributes.

    Reproduces: the target's clock lagging the prediction's by ``target_lag`` while ``t_index``
    agrees, and a stored prediction vorticity on a different spacing from the target's, written
    here as twice the target's so that scoring the stored field instead of a recomputed one shows.
    The target's velocity at the first step is u=1, v=2, so a channel swap or a transpose fails.
    """
    path = root / run / f"forecast_t0-{start}.h5"
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as f:
        groups = {name: f.create_group(name)
                  for name in ("rho", "u", "vorticity", "stability_scale", "t", "t_index")}
        for i, step in enumerate(steps):
            target = {"rho": 1.0 + 1e-3 * conftest.synthetic_field(shape, 1, seed=100 + start + i),
                      "u": 0.04 * conftest.synthetic_field(shape, 2, seed=200 + start + i),
                      "vorticity": 0.01 * conftest.synthetic_field(shape, 1, seed=300 + start + i)}
            if i == 0:
                target["u"] = np.stack([np.full(shape, 1.0), np.full(shape, 2.0)])
            # The prediction drifts away from the target as the lead grows.
            pred = {name: value + 1e-3 * (i + 1) * conftest.synthetic_field(
                        shape, value.shape[0], seed=400 + start + i, noise=0.5)
                    for name, value in target.items()}
            pred["vorticity"] = 2.0 * target["vorticity"]
            for name in ("rho", "u", "vorticity"):
                groups[name].create_dataset(f"target_{step}", data=target[name])
                groups[name].create_dataset(f"pred_{step}", data=pred[name])
            for side in ("target", "pred"):
                groups["stability_scale"].create_dataset(f"{side}_{step}",
                                                         data=np.ones((1, *shape)))
                groups["t_index"].create_dataset(f"{side}_{step}",
                                                 data=np.array([start + step], dtype=np.int64))
            clock = (start + step) * step_time
            groups["t"].create_dataset(f"pred_{step}", data=np.array([clock]))
            groups["t"].create_dataset(f"target_{step}", data=np.array([clock - target_lag]))
    return path
