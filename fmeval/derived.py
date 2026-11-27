"""Recomputation of derived fields from their primitives.

**Vorticity cannot be block-averaged like the other observables.** It is the curl of the
velocity, so the coarse-grid vorticity has to be recomputed from the coarse-grid velocity.
Otherwise the "vorticity" on the analysis grid is not the vorticity of the velocity field
on that grid, and every vorticity diagnostic becomes inconsistent with the velocity it is
supposed to describe.

How much this matters, measured on the real 256^2 frame at t=5000 -- recomputed vorticity
against the naive block-averaged vorticity:

===========  ====================
factor       rms relative difference
===========  ====================
2            5.6%
4            18.3%
8            25.9%
===========  ====================

Not a rounding detail, and it grows with exactly the coarsening the analysis grid is for.

Two rules that keep this honest:

**The spacing must be the coarse spacing.** ``dx_coarse = factor * dx_fine``. The vendored
kinet function defaults to ``spacing=1.0``; passing the fine spacing at a coarse grid
inflates the vorticity by *exactly* the factor -- verified at 2x, 4x and 8x. Nothing here
lets the default apply: spacing always comes from the :class:`GridSpec`.

**Never mix a stored derived field with a recomputed one.** The kinet solver wrote
``vorticity`` with a D2Q9 lattice stencil, not a spectral derivative; measured against the
spectral result on the native grid they differ by 8.1% rms (correlation 0.997). Both are
defensible discretisations, but using the stored field at 256^2 and a spectral one at
128^2 would make the grid-independence criterion measure operator mismatch rather than
grid effects. So derived fields are recomputed with *our* operator at every analysis grid,
including the native one; the stored field is only ever read as a cross-check.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from .data.base import DERIVED_FIELDS, Frame, GridSpec, Trajectory
from .external.kinet_spectral import physical_wavenumber_grid, spectral_vorticity

#: Derived field -> the primitives it is computed from. Only kinematic quantities belong
#: here: anything that needs an equation of state, such as pressure, is a property of the
#: solver and is read from the dataset or not at all.
RECIPES: dict[str, tuple[str, ...]] = {
    "vorticity": ("velocity",),
}


def recomputable(name: str, available: Mapping[str, np.ndarray]) -> bool:
    """Whether ``name`` can be recomputed from the fields present in ``available``."""
    inputs = RECIPES.get(name)
    return inputs is not None and all(i in available for i in inputs)


def vorticity_from_velocity(velocity: np.ndarray, grid: GridSpec) -> np.ndarray:
    """Spectral curl of the velocity, on ``grid``.

    Args:
        velocity: ``(D, *spatial)`` with D == grid.n_spatial.
        grid: The grid the velocity lives on. Its spacing is what sets the wavenumbers,
            so this must be the *analysis* grid, not the native one.

    Returns:
        ``(1, *spatial)`` in 2D and ``(3, *spatial)`` in 3D -- the 2D scalar is lifted to a
        channel axis so it matches the canonical ``(C, *spatial)`` layout, exactly as
        kinet's own ``compute_vorticity_slab`` does.
    """
    if velocity.shape[0] != grid.n_spatial:
        raise ValueError(
            f"velocity has {velocity.shape[0]} components but the grid is "
            f"{grid.n_spatial}-dimensional"
        )
    if velocity.shape[1:] != grid.shape:
        raise ValueError(
            f"velocity spatial shape {velocity.shape[1:]} does not match grid {grid.shape}"
        )
    if not grid.is_periodic:
        raise ValueError(
            "spectral vorticity assumes a fully periodic domain; this grid's boundaries are "
            f"{grid.boundary}"
        )
    # spacing=grid.spacing is the whole point: at a coarse grid the fine spacing would
    # scale the result by the coarsening factor.
    omega = spectral_vorticity(velocity, spacing=list(grid.spacing))
    return omega[np.newaxis, ...] if omega.ndim == grid.n_spatial else omega


def helmholtz_split(velocity: np.ndarray, grid: GridSpec) -> tuple[np.ndarray, np.ndarray]:
    """The solenoidal and dilatational parts of a periodic velocity, by Fourier projection.

    Each mode's dilatational part is its projection onto its wavevector,
    ``u_d_hat = k (k . u_hat) / |k|^2``, which is curl-free; the solenoidal part
    ``u - u_d`` is divergence-free and keeps the spatial mean, which belongs to neither
    (the Helmholtz-Hodge decomposition on a periodic domain; Bhatia, Norgard, Pascucci &
    Bremer 2013, IEEE TVCG 19(8), 1386-1404, https://doi.org/10.1109/TVCG.2012.316). The
    two parts are orthogonal mode by mode, so their kinetic energies add.

    Args:
        velocity: ``(D, *spatial)`` with D == grid.n_spatial.
        grid: The periodic grid the velocity lives on; its spacing sets the wavevectors.

    Returns:
        ``(solenoidal, dilatational)``, each shaped like ``velocity``.

    Raises:
        ValueError: On a velocity that is not one component per axis of ``grid``, or a grid
            that is not periodic on every axis.
    """
    if velocity.shape != (grid.n_spatial, *grid.shape) or not grid.is_periodic:
        raise ValueError(f"the Helmholtz split needs a velocity of shape "
                         f"{(grid.n_spatial, *grid.shape)} on a periodic grid, got "
                         f"{velocity.shape} on boundaries {grid.boundary}")
    k = physical_wavenumber_grid(grid.shape, grid.spacing)
    k_squared = sum(component**2 for component in k)
    k_squared[(0,) * grid.n_spatial] = np.inf  # the mean has no dilatational part
    axes = tuple(range(1, velocity.ndim))
    u_hat = np.fft.fftn(velocity, axes=axes)
    projection = sum(component * u for component, u in zip(k, u_hat, strict=True)) / k_squared
    dilatational = np.real(np.fft.ifftn(np.stack([component * projection for component in k]),
                                        axes=axes))
    return velocity - dilatational, dilatational


def recompute(
    name: str, fields: Mapping[str, np.ndarray], grid: GridSpec
) -> np.ndarray:
    """Recompute one derived field from primitives already on ``grid``.

    Raises:
        KeyError: If ``name`` has no recipe or a required primitive is missing.
    """
    if name not in RECIPES:
        raise KeyError(f"no recipe for derived field {name!r}")
    if not recomputable(name, fields):
        missing = [i for i in RECIPES[name] if i not in fields]
        raise KeyError(f"cannot recompute {name!r}: missing {missing}")
    if name == "vorticity":
        return vorticity_from_velocity(fields["velocity"], grid)
    raise KeyError(f"no implementation for derived field {name!r}")


def recompute_frame(frame: Frame) -> Frame:
    """Return a copy of ``frame`` with every derived field recomputed from its primitives.

    Used to put the *native* grid on the same footing as every coarse grid, so a
    grid-independence sweep compares like with like rather than a lattice-stencil
    vorticity against a spectral one. A derived field whose inputs are absent is kept. Every
    ensemble member is recomputed from its own primitives, as :func:`fmeval.remap.remap_frame`
    remaps it.
    """
    targets = [n for n in frame.fields if n in DERIVED_FIELDS and recomputable(n, frame.fields)]
    if not targets:
        return frame
    out = dict(frame.fields)
    for name in targets:
        out[name] = recompute(name, frame.fields, frame.grid)
    members = None
    if frame.has_members:
        per_member = [recompute_frame(Frame(index=frame.index, time=frame.time, grid=frame.grid,
                                            fields={n: m[i] for n, m in frame.members.items()}))
                      .fields for i in range(len(next(iter(frame.members.values()))))]
        members = {n: np.stack([fields[n] for fields in per_member]) for n in frame.members}
    return frame.with_fields(out, frame.grid, members=members)


class RecomputingTrajectory:
    """A trajectory whose stored derived fields are replaced by this module's operators.

    Without this the native grid would carry the solver's lattice-stencil vorticity while
    every coarse grid carries a spectral one, and a grid-independence comparison would be
    measuring the difference between two discretisations rather than between two grids (see the
    module docstring). ``evaluate.py`` wraps every dataset that sets
    ``recompute_derived``; the pipeline reads frames only through :meth:`frame`.
    """

    def __init__(self, inner: Trajectory) -> None:
        self._inner = inner

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def __len__(self) -> int:
        return len(self._inner)

    def frame(self, t: int, fields) -> Frame:
        return recompute_frame(self._inner.frame(t, fields))

    def iter_frames(self, fields, selection=None):
        # Without this, `__getattr__` would hand back the inner trajectory's iterator, whose
        # frames carry the stored derived fields this wrapper exists to replace.
        for frame in self._inner.iter_frames(fields, selection):
            yield recompute_frame(frame)

    def close(self) -> None:
        self._inner.close()
