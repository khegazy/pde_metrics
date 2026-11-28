"""What each kinet rollout file holds, its storage by group, and what its clock measures (prototype).

Usage (kinet's .venv, env.sh sourced):
    python -B file_anatomy.py ROLLOUT.h5 [ROLLOUT.h5 ...]

For every file it prints: the file size on disk; every dataset outside the VTKHDF view with its
shape, dtype, compression, units attribute and bytes stored (``h5py`` ``get_storage_size``);
the bytes stored per top-level group (``observables``, ``mesoscopic``, ``initial_conditions``,
``time``, ``geometry``, ``VTKHDF``) and each as a fraction of the file; and the clock check:
the last stored ``time/time`` against the configured end time ``temporal.length`` of the saved
config, the ratio ``time_convection / time`` on the stored slots (constant if one is a rescaling
of the other), and the boundary-conditions attribute.
"""

import json
import os
import sys
from collections import defaultdict

import hdf5plugin  # noqa: F401  (registers blosc2 before h5py opens a PonD rollout)
import h5py
import numpy as np
import yaml


def main(paths: list[str]) -> None:
    """Print the anatomy of each file."""
    for path in paths:
        identity = os.path.dirname(os.path.dirname(os.path.dirname(path)))
        with open(os.path.join(identity, "config.yaml")) as fh:
            t_end = float(yaml.safe_load(fh)["case"]["discretization"]["temporal"]["length"])
        size = os.path.getsize(path)
        groups: dict[str, int] = defaultdict(int)
        with h5py.File(path, "r") as f:
            print(f"\n== {path}\n   file bytes {size} ({size / 2**20:.1f} MiB)")

            def visit(name: str, obj: object) -> None:
                if isinstance(obj, h5py.Dataset):
                    stored = obj.id.get_storage_size()
                    groups[name.split("/")[0]] += stored
                    if not name.startswith("VTKHDF"):
                        print(f"   {name:48s} {str(obj.shape):26s} {str(obj.dtype):8s} "
                              f"compression={obj.compression} units={obj.attrs.get('units')} stored={stored}")

            f.visititems(visit)
            for g, b in sorted(groups.items()):
                print(f"   group {g:20s} stored {b:12d} bytes = {b / size:.3f} of the file")
            time = f["time/time"][:]
            conv = f["time/time_convection"][:]
            ok = np.isfinite(time) & (time > 0)
            ratio = conv[ok] / time[ok]
            print(f"   clock: last time/time={time[ok][-1]!r} (units attribute {f['time/time'].attrs.get('units')!r}), "
                  f"configured end time temporal.length={t_end!r}, equal={bool(np.isclose(time[ok][-1], t_end, rtol=1e-12, atol=0))}; "
                  f"time_convection/time min={ratio.min():.10g} max={ratio.max():.10g} (1/ratio={1 / ratio.mean():.10g})")
            print(f"   boundary_conditions attribute: {f.attrs.get('boundary_conditions')}")
            print(f"   discretization attribute: {json.loads(f.attrs['discretization'])}")


if __name__ == "__main__":
    main(sys.argv[1:])
