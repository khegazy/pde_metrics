"""Run folders: creation, provenance, and reloading.

One folder per metric under test, named ``<metric>_<time>`` where ``<time>`` is
``int(time.time())``. The **same** timestamp is used for every metric in one invocation,
so a multi-metric run produces sibling folders that sort together and are obviously one
experiment.

Everything a folder needs is inside it -- the raw numbers, the resolved config, the
provenance -- so it can be copied to a colleague, attached to an issue, or uploaded to
Overleaf and still regenerate its own report. The rule is that no number appears in the
report without a machine-readable source in the same folder.

CSV rather than Parquet: ``pyarrow`` is not installed and this is a shared environment not
worth fighting. Large frames are gzipped, which pandas handles from the extension alone.
"""

from __future__ import annotations

import hashlib
import json
import logging
import platform
import shutil
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from omegaconf import DictConfig, ListConfig, OmegaConf

from degradations import registry as deg_registry
from metrics import registry as metric_registry

log = logging.getLogger(__name__)

#: Gzip the tidy frame above this many rows.
GZIP_ROWS = 500_000


@dataclass(frozen=True)
class RunFolder:
    """Layout of one ``results/<name>_<time>/`` directory."""

    root: Path

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def plots(self) -> Path:
        return self.root / "plots"

    @property
    def tables(self) -> Path:
        return self.root / "tables"

    @property
    def sections(self) -> Path:
        return self.root / "sections"

    @property
    def figure_data(self) -> Path:
        return self.data / "figure_data"

    @property
    def meta_path(self) -> Path:
        """Provenance, written by :func:`write_run_meta`."""
        return self.data / "run_meta.json"

    @property
    def config_path(self) -> Path:
        """The fully resolved configuration, written by :func:`write_config`."""
        return self.data / "config.yaml"

    @property
    def maps_path(self) -> Path:
        """Stored pointwise metric maps, written by :func:`write_maps`."""
        return self.data / "error_maps.npz"

    def create(self) -> RunFolder:
        for path in (self.data, self.plots, self.tables, self.sections, self.figure_data):
            path.mkdir(parents=True, exist_ok=True)
        return self


def make_run_folder(results_root: Path | str, name: str, stamp: int) -> RunFolder:
    """Create ``<results_root>/<name>_<stamp>/`` with its subdirectories."""
    return RunFolder(Path(results_root) / f"{name}_{stamp}").create()


# --- writing ------------------------------------------------------------------------


def write_results(folder: RunFolder, df: pd.DataFrame, name: str = "results") -> Path:
    """Write the tidy frame, gzipping when it is large."""
    suffix = ".csv.gz" if len(df) > GZIP_ROWS else ".csv"
    path = folder.data / f"{name}{suffix}"
    df.to_csv(path, index=False)
    return path


def write_table(folder: RunFolder, df: pd.DataFrame, name: str) -> Path:
    """Write one analysis table to ``data/`` as CSV."""
    path = folder.data / f"{name}.csv"
    df.to_csv(path, index=False)
    return path


def write_maps(folder: RunFolder, maps: Mapping[str, np.ndarray]) -> Path | None:
    """Write pointwise metric maps to a compressed npz, or nothing if there are none."""
    if not maps:
        return None
    np.savez_compressed(folder.maps_path, **maps)
    return folder.maps_path


def write_config(folder: RunFolder, resolved: Mapping[str, Any],
                 overrides: list[str] | None = None) -> str:
    """Write the config that produced the numbers, and return its hash.

    ``config.yaml`` is the composed tree with every interpolation expanded: each key of the
    schema (``fmeval/config.py``) and each key a config file or override states. Options a
    reader or an operator leaves at its default are not in it; ``run_meta.json`` records those
    as ``reader_options`` and ``registries.degradations.<op>.defaults``. ``config_overrides.yaml``
    keeps just the command-line overrides, which is what you read when diffing two runs.

    Returns:
        Short blake2b hash of the resolved config. Two runs with the same hash used
        identical settings, given the same code (``run_meta.json`` records its git state).
    """
    text = dump_yaml(_plain(resolved))
    folder.config_path.write_text(text)
    (folder.data / "config_overrides.yaml").write_text(dump_yaml(list(overrides or [])))
    digest = hashlib.blake2b(text.encode(), digest_size=8).hexdigest()
    (folder.data / "config_hash.txt").write_text(digest + "\n")
    return digest


def copy_documentation(folder: RunFolder) -> Path | None:
    """Copy TEST_DESCRIPTION.md into the run folder.

    A results directory should explain its own numbers after being sent to a colleague or
    uploaded to Overleaf, without needing the repository alongside it.
    """
    source = Path(__file__).resolve().parent.parent / "TEST_DESCRIPTION.md"
    if not source.exists():  # pragma: no cover - present in a checkout
        return None
    target = folder.root / source.name
    shutil.copy(source, target)
    return target


def write_run_meta(folder: RunFolder, **extra: Any) -> Path:
    """Write provenance: git state, environment, package versions, registry snapshot.

    The registry snapshot matters more than it looks: six months from now you need to know
    whether ``nrmse`` meant "normalised by the raw RMS" or "by the fluctuation RMS" when
    that CSV was written.
    """
    meta: dict[str, Any] = {
        "git": _git_state(),
        "host": platform.node(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": _package_versions(),
        "registries": _registry_snapshot(),
        **extra,
    }
    folder.meta_path.write_text(json.dumps(meta, indent=2, default=str) + "\n")
    return folder.meta_path


# --- reading ------------------------------------------------------------------------


def _folder(folder: RunFolder | Path) -> RunFolder:
    return folder if isinstance(folder, RunFolder) else RunFolder(Path(folder))


def read_results(folder: RunFolder | Path, name: str = "results") -> pd.DataFrame:
    """Read a tidy frame back, from either the plain or the gzipped form."""
    data = _folder(folder).data
    for suffix in (".csv", ".csv.gz"):
        path = data / f"{name}{suffix}"
        if path.exists():
            return pd.read_csv(path)
    raise FileNotFoundError(f"no {name}.csv or {name}.csv.gz in {data}")


def read_run_meta(folder: RunFolder | Path) -> dict[str, Any]:
    """A run's provenance, or an empty mapping for a folder written before it was recorded."""
    path = _folder(folder).meta_path
    return json.loads(path.read_text()) if path.exists() else {}


def read_config(folder: RunFolder | Path) -> dict[str, Any]:
    """A run's resolved configuration, or an empty mapping if the folder has none."""
    return read_yaml(_folder(folder).config_path)


def read_yaml(path: Path) -> dict[str, Any]:
    """A YAML file's contents, or an empty mapping if the file does not exist."""
    return yaml.safe_load(path.read_text()) if path.exists() else {}


def dump_yaml(data: Any) -> str:
    """YAML text as every file here is written: block style, keys sorted."""
    return yaml.safe_dump(data, sort_keys=True, default_flow_style=False)


def load_runs(pattern: str, root: Path | str = "results") -> pd.DataFrame:
    """Concatenate the results of several run folders, tagged by folder name.

    How a multirun sweep becomes one cross-dataset or cross-metric table.

    Args:
        pattern: Glob relative to ``root``, e.g. ``"mse_*"`` or ``"*_1786224531"``.
        root: Results directory.
    """
    frames = []
    for folder in sorted(Path(root).glob(pattern)):
        if not (folder / "data").is_dir():
            continue
        try:
            df = read_results(folder)
        except FileNotFoundError:
            log.warning("no results in %s; skipping", folder)
            continue
        df["run_dir"] = folder.name
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no run folders matching {pattern!r} under {root}")
    return pd.concat(frames, ignore_index=True)


# --- provenance helpers ---------------------------------------------------------------


def _plain(obj: Any) -> Any:
    """Convert OmegaConf containers and numpy scalars into plain YAML-safe Python."""
    if isinstance(obj, (DictConfig, ListConfig)):
        return OmegaConf.to_container(obj, resolve=True)
    if isinstance(obj, Mapping):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    if isinstance(obj, np.generic):
        return obj.item()
    return obj


def _git_state() -> dict[str, Any]:
    def _run(*args: str) -> str | None:
        try:
            out = subprocess.run(
                ["git", *args], capture_output=True, text=True, timeout=10,
                cwd=Path(__file__).resolve().parent.parent,
            )
            return out.stdout.strip() if out.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None

    status = _run("status", "--porcelain")
    return {
        "sha": _run("rev-parse", "HEAD"),
        "branch": _run("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(status) if status is not None else None,
    }


def _package_versions() -> dict[str, str]:
    out = {}
    for name in ("numpy", "scipy", "h5py", "pandas", "matplotlib", "hydra-core",
                 "omegaconf"):
        try:
            out[name] = version(name)
        except PackageNotFoundError:  # pragma: no cover
            pass
    return out


def _registry_snapshot() -> dict[str, Any]:
    """What each registered metric and degradation meant at the time of the run."""
    metric_registry.discover()
    deg_registry.discover()

    def provenance(spec) -> dict[str, Any]:
        return {**spec.describe(), "module": spec.module,
                "doc": spec.doc.splitlines()[0] if spec.doc else ""}

    return {
        "metrics": {s.name: provenance(s) for s in metric_registry.REGISTRY.values()},
        "degradations": {s.name: provenance(s) for s in deg_registry.REGISTRY.values()},
    }
