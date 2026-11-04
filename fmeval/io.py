"""Run folders: creation, provenance, and reloading.

One folder per metric under test, named ``<metric>_<time>`` where ``<time>`` is the stamp
the invocation claimed with :func:`claim_stamp`, ``int(time.time())`` unless another invocation
already holds that second. The **same** stamp is used for every metric in one invocation,
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
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from hydra.core.utils import JobReturn, JobStatus
from hydra.experimental.callback import Callback
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
        """Stored per-cell metric maps and point sets, written by :func:`write_maps`."""
        return self.data / "error_maps.npz"

    def create(self) -> RunFolder:
        for path in (self.data, self.plots, self.tables, self.sections, self.figure_data):
            path.mkdir(parents=True, exist_ok=True)
        return self


def claim_stamp(results_root: Path | str) -> int:
    """A run stamp no other invocation holds: ``int(time.time())``, or the next free second.

    Folders are written when a run ends, under the stamp taken when it started, so two
    invocations started in the same second would write the same ``<name>_<stamp>`` folder and
    the later would silently overwrite the earlier. A stamp is claimed by creating the
    directory ``<results_root>/.stamps/<stamp>``, which ``mkdir`` does atomically, so the claim
    holds across processes; a taken stamp moves on to the next second.
    """
    claims = Path(results_root) / ".stamps"
    claims.mkdir(parents=True, exist_ok=True)
    stamp = int(time.time())
    while True:
        try:
            (claims / str(stamp)).mkdir()
        except FileExistsError:
            stamp += 1
        else:
            return stamp


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
    """Write per-cell metric maps and point sets to a compressed npz, or nothing if there are
    none."""
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


#: Result columns read back as text, an empty cell staying ``""``. A calibration-free operator
#: writes ``calibration`` empty, and the default reader would turn that into NaN. Only these
#: columns: read the whole file this way and the empty ``target_value`` cells become strings,
#: which ``summarise_axes`` then fails to convert.
RESULT_TEXT_COLUMNS: tuple[str, ...] = ("calibration", "severity_name", "variant_label")

#: The name of a run's curve-companion rows, ``data/companions.csv``, beside ``results.csv``.
COMPANIONS: str = "companions"


def read_results(folder: RunFolder | Path, name: str = "results", *,
                 missing_ok: bool = False) -> pd.DataFrame | None:
    """Read a tidy frame back, from either the plain or the gzipped form.

    The columns of :data:`RESULT_TEXT_COLUMNS` are read as written, without missing-value
    detection (a ``str`` converter, which is ``keep_default_na=False`` for those columns
    alone); every other column is parsed as usual. A named column a file lacks is skipped.

    Args:
        folder: The run folder.
        name: ``"results"``, or :data:`COMPANIONS` for the curve-companion rows.
        missing_ok: Return None rather than raise when the file is absent, as it is in a run
            whose metrics have no curve companion.
    """
    data = _folder(folder).data
    for suffix in (".csv", ".csv.gz"):
        path = data / f"{name}{suffix}"
        if path.exists():
            return pd.read_csv(path, converters=dict.fromkeys(RESULT_TEXT_COLUMNS, str))
    if missing_ok:
        return None
    raise FileNotFoundError(f"no {name}.csv or {name}.csv.gz in {data}")


def read_run_meta(folder: RunFolder | Path) -> dict[str, Any]:
    """A run's provenance, or an empty mapping for a folder written before it was recorded."""
    path = _folder(folder).meta_path
    return json.loads(path.read_text()) if path.exists() else {}


def read_maps(folder: RunFolder | Path,
              keep: Callable[[str], bool] | None = None) -> dict[str, np.ndarray]:
    """A run's stored maps, point sets and dense curves, by ``error_maps.npz`` key; empty if
    none were stored.

    ``keep`` selects keys before any array is read: the archive decompresses a member only
    when it is accessed, so a card that needs one metric's maps does not read every metric's
    (94 MB on the pinned kinet run).
    """
    path = _folder(folder).maps_path
    if not path.exists():
        return {}
    with np.load(path) as archive:
        return {k: archive[k] for k in archive.files if keep is None or keep(k)}


def read_config(folder: RunFolder | Path) -> dict[str, Any]:
    """A run's resolved configuration, or an empty mapping if the folder has none."""
    return read_yaml(_folder(folder).config_path)


def read_yaml(path: Path) -> dict[str, Any]:
    """A YAML file's contents, or an empty mapping if the file does not exist."""
    return yaml.safe_load(path.read_text()) if path.exists() else {}


def dump_yaml(data: Any) -> str:
    """YAML text as every file here is written: block style, keys sorted."""
    return yaml.safe_dump(data, sort_keys=True, default_flow_style=False)


def load_runs(folders: Iterable[Path | str], name: str = "results") -> pd.DataFrame:
    """Concatenate the results of several run folders, tagged by folder name.

    How a multirun sweep becomes one cross-dataset or cross-metric table, e.g.
    ``load_runs(sorted(Path("results").glob("mse_*")))``.

    Args:
        folders: Run folders; one without a ``data/`` directory or without the file is
            skipped with a warning.
        name: ``"results"``, or :data:`COMPANIONS` for the curve-companion rows.

    Raises:
        FileNotFoundError: If no folder held the file.
    """
    frames = []
    folders = [Path(f) for f in folders]
    for folder in sorted(folders):
        df = read_results(folder, name, missing_ok=True) if (folder / "data").is_dir() else None
        if df is None:
            log.warning("no %s in %s; skipping", name, folder)
            continue
        df["run_dir"] = folder.name
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no {name} in any of {[str(f) for f in folders]}")
    return pd.concat(frames, ignore_index=True)


#: Provenance that must be the same in every member of a combined folder: the report reads it
#: once for all of them, and a damage means the same thing in two members only if the ladder,
#: the anchor and the analysis grid agree.
SHARED_META: tuple[str, ...] = ("metric", "fields", "analysis_grid", "ladder_axes",
                                "n_severity_levels", "anchor_label", "probe_labels", "seed",
                                "boundary")


#: Provenance a run records for itself alone; a combined folder does not copy it from a member.
_OWN_META: tuple[str, ...] = ("git", "host", "python", "platform", "packages", "registries",
                              "run_id", "config_hash", "metric", "n_rows", "command", "timings",
                              "comparison", "members")


def combine_runs(folders: Sequence[Path | str], stamp: int, *,
                 across: str = "dataset") -> RunFolder:
    """Write one folder holding the rows of several runs that differ only in ``across``.

    ``across="dataset"``: one run per dataset of a family, for section 12. The combined folder
    is ``<family>_<stamp>`` beside the first; it holds every member's rows and companion rows,
    their calibration tables with a ``dataset`` column, and a ``run_meta.json`` whose
    ``members`` maps each dataset to its own folder's provenance. Error maps are not carried:
    their keys do not name the dataset. A member's own folder remains its full report.

    ``across="metrics"``: the shards of one evaluation, each run with a different set of metrics
    on the same dataset, ladder, grid and commit, so it can be spread over several processes.
    The combined folder is ``comparison_<stamp>`` beside the first and is the folder one process
    running every metric would have written: every row, companion row and stored map, the
    calibration once (it depends on the dataset and ladder only, and is checked equal), and the
    first member's provenance, including its git state, with ``metric`` naming every metric.

    Raises:
        ValueError: On fewer than two members; members whose configurations differ in anything
            but ``across``, or whose provenance differs in a :data:`SHARED_META` key (for
            shards, also in git state or calibration): their damages would not be on one
            scale. For datasets, a member holding several datasets or one the others hold too,
            or members of different families; for metrics, two members sharing a metric.
    """
    if across not in ("dataset", "metrics"):
        raise ValueError(f"across must be 'dataset' or 'metrics', got {across!r}")
    members = [_folder(f) for f in folders]
    if len(members) < 2:
        raise ValueError(f"a comparison needs at least two runs, got {len(members)}")
    configs = [read_config(m) for m in members]
    metas = [read_run_meta(m) for m in members]
    shared = [k for k in SHARED_META if not (across == "metrics" and k == "metric")]
    if across == "metrics":
        shared.append("git")
    for member, config, meta in zip(members[1:], configs[1:], metas[1:], strict=True):
        differ = sorted(k for k in {*configs[0], *config} - {across}
                        if config.get(k) != configs[0].get(k))
        differ += [f"run_meta.{k}" for k in shared if meta.get(k) != metas[0].get(k)]
        if differ:
            raise ValueError(
                f"{member.root.name} differs from {members[0].root.name} in {differ}; the "
                f"members of one comparison may differ only in {across}"
            )
    rows = load_runs(m.root for m in members)
    if across == "dataset":
        datasets = rows.groupby("run_dir", observed=True)["dataset"].unique()
        if any(len(d) != 1 for d in datasets) or len({d[0] for d in datasets}) != len(members):
            raise ValueError(f"each member must hold one dataset of its own: {datasets.to_dict()}")
        families = rows["dataset_family"].dropna().unique()
        if len(families) != 1 or not families[0]:
            raise ValueError(f"the members must belong to one dataset family, got {list(families)}")
        name = str(families[0])
    else:
        metrics = rows.groupby("run_dir", observed=True)["metric"].unique()
        if sum(len(m) for m in metrics) != len({x for m in metrics for x in m}):
            raise ValueError(f"each member must hold metrics of its own: {metrics.to_dict()}")
        name = "comparison"

    folder = make_run_folder(members[0].root.parent, name, stamp)
    write_results(folder, rows.drop(columns="run_dir"))
    if any((m.data / f"{COMPANIONS}.csv").exists() or (m.data / f"{COMPANIONS}.csv.gz").exists()
           for m in members):
        write_results(folder, load_runs((m.root for m in members), COMPANIONS)
                      .drop(columns="run_dir"), name=COMPANIONS)
    for table in ("calibration", "calibration_spectrum"):
        frames = [pd.read_csv(m.data / f"{table}.csv") for m in members
                  if (m.data / f"{table}.csv").exists()]
        if not frames:
            continue
        if across == "dataset":
            write_table(folder, pd.concat(
                [f.assign(dataset=meta["dataset"]) for f, meta in zip(frames, metas, strict=True)],
                ignore_index=True), table)
        else:
            if any(not f.equals(frames[0]) for f in frames[1:]):
                raise ValueError(f"the shards' {table} tables differ; they did not run one ladder")
            write_table(folder, frames[0], table)
    if across == "dataset":
        digest = write_config(folder, {**configs[0], "dataset": {
            meta["dataset"]: config["dataset"]
            for config, meta in zip(configs, metas, strict=True)}})
        meta_extra = {**{k: metas[0][k] for k in SHARED_META if k in metas[0]},
                      "n_frames": sum(int(meta.get("n_frames", 0)) for meta in metas),
                      "dataset": ", ".join(meta["dataset"] for meta in metas),
                      "dataset_family": name,
                      "members": {meta["dataset"]: {"run": m.root.name, **meta}
                                  for m, meta in zip(members, metas, strict=True)}}
    else:
        ran = [x for config in configs for x in config["metrics"]]
        digest = write_config(folder, {**configs[0], "metrics": ran})
        maps = {k: v for m in members for k, v in read_maps(m).items()}
        write_maps(folder, maps)
        meta_extra = {**{k: v for k, v in metas[0].items() if k not in _OWN_META},
                      "git": metas[0].get("git"), "registries": metas[0].get("registries"),
                      "metric": ", ".join(ran),
                      "n_rows": len(rows),
                      "members": {m.root.name: meta.get("metric")
                                  for m, meta in zip(members, metas, strict=True)}}
    copy_documentation(folder)
    write_run_meta(folder, run_id=stamp, config_hash=digest, comparison=True, **meta_extra)
    return folder


class FamilyComparison(Callback):
    """Gather the jobs of a family multirun into one folder (:func:`combine_runs`).

    Named in ``hydra.callbacks`` by a ``configs/dataset_family/`` option. Each job returns the
    folder holding all of its metrics' rows (``evaluate.main``); the callback collects them as
    the jobs end and combines them once the sweep is over. A job that failed contributes
    nothing, and the comparison is then not written, since it would silently lack a member.
    """

    def __init__(self) -> None:
        self.folders: list[Path] = []
        self.failed = 0

    def on_job_end(self, config: DictConfig, job_return: JobReturn, **kwargs: Any) -> None:
        if job_return.status == JobStatus.COMPLETED:
            self.folders.append(Path(job_return.return_value))
        else:
            self.failed += 1

    def on_multirun_end(self, config: DictConfig, **kwargs: Any) -> None:
        if self.failed:
            log.error("%d member job(s) failed; no comparison folder written", self.failed)
            return
        folder = combine_runs(self.folders, claim_stamp(self.folders[0].parent))
        log.info("wrote %s", folder.root)


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
