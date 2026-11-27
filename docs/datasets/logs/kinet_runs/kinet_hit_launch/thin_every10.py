"""Prototype, run-specific: keep every 10th coarse step of a downsampled Re=50k tier.

The Re=12.5k and Re=25k runs saved step 1 and every 10th step (``io.save_every_n=10``)
into a time axis that keeps all 10,000 slots, the unsaved ones NaN and unallocated.
This rewrites a 256x256 tier of a 512x512 Re=50k run, which holds all 10,000 coarse
steps, into that layout: slots 0, 9, 19, ..., 9999 (coarse steps 1, 10, ..., 10000)
are kept, every other slot is left unwritten with a NaN fill, and ``time/time_index``
becomes float64 as in a simulator file so an unsaved slot can be NaN.

The tier's ``VTKHDF`` group is not copied: its virtual datasets point at the deleted
512x512 data and claim its shape, so it was already unreadable.

The thinned file is written next to the original, compared with it (every kept slot
bit-identical, one allocated chunk per kept slot, the other datasets and all attributes
unchanged), and only then moved over it.

Usage: python thin_every10.py <tier rollout.h5> [...]
"""

from __future__ import annotations

import os
import sys

import h5py
import numpy as np

EVERY = 10
TIME_GROUPS = ("observables/", "mesoscopic/", "time/")  # not initial_conditions/
SKIP = "VTKHDF"
BATCH = 100  # kept frames read per call: ~100 MB for the 2-component velocity


def time_axis(name: str, ds: h5py.Dataset, n_time: int) -> int | None:
    """The time axis of a per-step dataset (a 1D series or a 5D field), else None."""
    if not name.startswith(TIME_GROUPS):
        return None
    axis = 0 if ds.ndim == 1 else 2
    if ds.shape[axis] != n_time:
        raise ValueError(f"{name}: time axis {ds.shape} does not have {n_time} slots")
    return axis


def at(axis: int, idx: np.ndarray | int) -> tuple:
    return (slice(None),) * axis + (idx,)


def thin(src_path: str) -> bool:
    """Thin one tier in place; False if it is already thinned (slot 1 unsaved)."""
    tmp_path = src_path + ".thin.tmp"
    with h5py.File(src_path, "r") as src:
        if np.isnan(src["time/time_index"][1]):
            return False
        n_time = src["time/time_index"].shape[0]
        keep = np.r_[0, np.arange(EVERY - 1, n_time, EVERY)]
        if src["time/time_index"][n_time - 1] != n_time:
            raise ValueError(f"{src_path}: not a complete {n_time}-step tier")
        with h5py.File(tmp_path, "w") as dst:
            dst.attrs.update(src.attrs)

            def copy(name: str, obj: h5py.Group | h5py.Dataset) -> None:
                if name == SKIP or name.startswith(SKIP + "/"):
                    return
                if isinstance(obj, h5py.Group):
                    dst.require_group(name).attrs.update(obj.attrs)
                    return
                axis = time_axis(name, obj, n_time)
                if axis is None:
                    src.copy(obj, dst, name=name)
                    return
                out = dst.create_dataset(
                    name, shape=obj.shape, dtype=np.float64, chunks=obj.chunks,
                    fillvalue=np.nan,
                )
                out.attrs.update(obj.attrs)
                for lo in range(0, len(keep), BATCH):
                    idx = keep[lo : lo + BATCH]
                    out[at(axis, idx)] = obj[at(axis, idx)]

            src.visititems(copy)
    verify(src_path, tmp_path, keep, n_time)
    os.replace(tmp_path, src_path)
    return True


def verify(src_path: str, tmp_path: str, keep: np.ndarray, n_time: int) -> None:
    dropped = np.setdiff1d(np.arange(n_time), keep)[[0, -1]]
    with h5py.File(src_path, "r") as src, h5py.File(tmp_path, "r") as dst:
        if src.attrs.keys() != dst.attrs.keys() or any(
            str(src.attrs[k]) != str(dst.attrs[k]) for k in src.attrs
        ):
            raise ValueError("file attributes differ")
        names: list[str] = []
        src.visititems(
            lambda n, o: names.append(n)
            if isinstance(o, h5py.Dataset) and not n.startswith(SKIP + "/")
            else None
        )
        for name in names:
            a, b = src[name], dst[name]
            if dict(a.attrs) != dict(b.attrs):
                raise ValueError(f"{name}: attributes differ")
            axis = time_axis(name, a, n_time)
            if axis is None:
                if not np.array_equal(a[()], b[()]):
                    raise ValueError(f"{name}: copy differs")
                continue
            for lo in range(0, len(keep), BATCH):
                idx = keep[lo : lo + BATCH]
                if not np.array_equal(a[at(axis, idx)], b[at(axis, idx)]):
                    raise ValueError(f"{name}: kept slots differ")
            # A contiguous series (the coarse tier's time/*) has no chunks to count.
            if b.chunks is not None and b.id.get_num_chunks() != len(keep):
                raise ValueError(f"{name}: {b.id.get_num_chunks()} chunks allocated")
            if not np.isnan(b[at(axis, dropped)]).all():
                raise ValueError(f"{name}: a dropped slot is not NaN")
        if SKIP in dst:
            raise ValueError("VTKHDF was copied")


if __name__ == "__main__":
    for path in sys.argv[1:]:
        done = "thinned" if thin(path) else "already thinned"
        print(f"{done} {path}: {os.path.getsize(path) / 1e9:.2f} GB", flush=True)
