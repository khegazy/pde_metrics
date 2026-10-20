"""Evaluate metrics against a degradation ladder and write a run folder per metric.

    python evaluate.py metrics=[mse] dataset=kinet_re5e4_dev
    python evaluate.py 'metrics=[mae,mse,nrmse]' dataset=kinet_re5e4 \\
        dataset.time.reduction=100
    python evaluate.py metrics=[mse] degradation=quick
    python evaluate.py metrics=[mse] analysis_grid.resolution=128

Each metric gets its own ``results/<metric>_<time>/`` folder, all sharing one timestamp so
a multi-metric run is obviously one experiment. The folders carry the raw numbers, the
resolved config and full provenance, so they regenerate their own report without the repo.
"""

from __future__ import annotations

import inspect
import logging
import sys
import time
from pathlib import Path
from typing import Any

import hydra
import pandas as pd
from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig

from fmeval import io as fio
from fmeval.config import Config, build_job
from fmeval.data import (  # noqa: F401  (register the formats)
    kinet_raw,
    synthetic_ensemble,
    well,
)
from fmeval.data.base import READERS, Trajectory
from fmeval.data.locate import resolve_dataset_path, trajectory_provenance
from fmeval.derived import RecomputingTrajectory
from fmeval.ladder import build_ladder, ladder_axes
from fmeval.pipeline import DatasetInfo, parse_map_key, run
from metrics import registry as metric_registry

log = logging.getLogger(__name__)


def open_trajectory(job: Config) -> Trajectory:
    """Construct the reader named by ``dataset.format``.

    Explicit imports (at the top of this file) rather than a package walk: readers are a small
    closed set maintained with the harness, unlike metrics and degradations which are open
    contributor sets.
    """
    fmt = job.dataset.format
    if fmt not in READERS:
        raise KeyError(f"unknown dataset format {fmt!r}; available: {sorted(READERS)}")

    if not READERS[fmt].reads_from_disk:
        return READERS[fmt](Path(job.dataset.path), **job.dataset.reader)

    location = resolve_dataset_path(
        job.dataset.path, job.paths.data, data_url=job.paths.data_url
    )
    if location.source == "url":
        log.info(
            "dataset %s is not on this filesystem; reading the published copy at %s",
            job.dataset.name, location.url,
        )
    return READERS[fmt](location.target, **job.dataset.reader)


def select_fields(job: Config, trajectory: Trajectory,
                  specs: list[metric_registry.MetricSpec]) -> list[str]:
    """Fields to read: the config list if given, else what the metrics actually accept."""
    requested = job.fields or job.dataset.fields
    available = list(trajectory.fields)
    missing = [f for f in requested or () if f not in available]
    if missing:
        raise ValueError(
            f"dataset {job.dataset.name!r} does not provide {missing}; "
            f"it has {available}"
        )
    candidates = list(requested) if requested else available
    wanted = [field for field in candidates if any(s.accepts(field) for s in specs)]
    if not wanted:
        raise ValueError(
            f"no field in {candidates} is accepted by any of "
            f"{[s.name for s in specs]}"
        )
    return wanted


def dataset_info(job: Config) -> DatasetInfo:
    complexity = job.dataset.complexity
    return DatasetInfo(
        name=job.dataset.name,
        trajectory=job.dataset.trajectory,
        family=complexity.family,
        rank=complexity.rank,
        params=complexity.params,
    )


@hydra.main(version_base=None, config_path="configs", config_name="config")
def main(cfg: DictConfig) -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stdout, force=True,
    )
    started = time.perf_counter()
    stamp = int(time.time())     # stamps every folder this invocation writes
    # Every value is read from `job`, the config built into its schema (fmeval/config.py), so a
    # missing, misspelt or refused key stops the run here, before any data is read. `cfg` is
    # kept only to record the composed config.
    job = build_job(cfg)

    specs = [metric_registry.get(name) for name in job.metrics]
    severity_levels = build_ladder(job.degradation)
    axes = sorted(ladder_axes(severity_levels))
    log.info("ladder: %d severity levels over %d axes", len(severity_levels), len(axes))
    # The analysis reads both back from run_meta.json: which entry defines D = 1, and which
    # entries are probes rather than monotone axes (declared ordinal=False by their operator).
    anchor = job.analysis.anchor
    probes = sorted({r.label for r in severity_levels if not r.ordinal})
    if anchor not in {r.label for r in severity_levels}:
        log.warning("analysis.anchor=%r is not an entry of this ladder; the analysis will fall "
                    "back to the largest translation and record that in anchor_source", anchor)
    elif anchor not in probes:
        log.warning("analysis.anchor=%r is an ordinal axis: D = 1 would be the median over all "
                    "its levels. Anchor on an entry whose operator is ordinal=False.", anchor)

    trajectory = open_trajectory(job)
    # Every reader option the run used, defaults included. The recorded config states only what
    # a file or an override changed, and a reader's defaults belong to its code, which can move.
    reader = inspect.signature(READERS[job.dataset.format]).bind_partial(**job.dataset.reader)
    reader.apply_defaults()
    try:
        fields = select_fields(job, trajectory, specs)
        selection = job.dataset.time
        trajectory_frames = len(trajectory)
        n_frames = len(selection.resolve(trajectory_frames))
        log.info(
            "dataset %s: %d of %d frames (reduction %d), fields %s",
            job.dataset.name, n_frames, trajectory_frames, selection.reduction, fields,
        )

        if job.dataset.recompute_derived:
            trajectory = RecomputingTrajectory(trajectory)

        result = run(
            trajectory,
            specs,
            severity_levels,
            fields=fields,
            selection=selection,
            dataset=dataset_info(job),
            seed=job.seed,
            analysis_resolution=job.analysis_grid.resolution,
            remap_method=job.analysis_grid.method,
            maps=job.report.error_map,
        )
        # Before the `finally`: the request counters live on the HTTP file object, which
        # close() releases.
        data_source = trajectory_provenance(trajectory)
    finally:
        trajectory.close()

    elapsed = time.perf_counter() - started
    log.info(
        "%d rows on a %d-cell analysis grid in %.1fs (io %.1fs, degrade %.1fs, metrics %.1fs)",
        len(result.rows), result.analysis_grid, elapsed, result.io_seconds,
        result.degrade_seconds, result.metric_seconds,
    )

    # The severity calibration is part of a run's identity: a calibrated axis means nothing
    # without the measured field properties it was resolved against, and two datasets are only
    # comparable on such an axis if their calibrations are recorded alongside the numbers.
    calibration_table = pd.DataFrame(result.calibration.summary())
    spectrum_table = pd.DataFrame(result.calibration.spectrum_frame())

    overrides = _overrides()

    def write_folder(name: str, rows: pd.DataFrame, maps: dict, **meta: Any) -> Path:
        """One self-contained run folder: numbers, calibration, config, maps, provenance."""
        folder = fio.make_run_folder(job.paths.results, name, stamp)
        fio.write_results(folder, rows)
        fio.write_table(folder, calibration_table, "calibration")
        fio.write_table(folder, spectrum_table, "calibration_spectrum")
        digest = fio.write_config(folder, cfg, overrides)
        fio.write_maps(folder, maps)
        fio.copy_documentation(folder)
        fio.write_run_meta(
            folder,
            run_id=stamp,
            config_hash=digest,
            dataset=job.dataset.name,
            dataset_label=job.dataset.complexity.label,
            dataset_notes=job.dataset.notes,
            data_source=data_source,
            n_frames=result.n_frames,
            trajectory_frames=trajectory_frames,
            reader_options={k: v for k, v in reader.arguments.items() if k != "path"},
            n_rows=len(rows),
            fields=fields,
            analysis_grid=result.analysis_grid,
            ladder_axes=axes,
            n_severity_levels=len(severity_levels),
            anchor_label=anchor,
            probe_labels=probes,
            seed=job.seed,
            command=" ".join(sys.argv),
            **meta,
        )
        return folder.root

    timings = {"total_s": elapsed, "io_s": result.io_seconds,
               "degrade_s": result.degrade_seconds, "metric_s": result.metric_seconds}
    written = [
        write_folder(spec.name, result.rows[result.rows["metric"] == spec.name],
                     {k: v for k, v in result.maps.items() if parse_map_key(k)[0] == spec.name},
                     metric=spec.name, timings=timings)
        for spec in specs
    ]
    # Cross-metric figures -- redundancy, the selectivity comparison, the cost frontier --
    # are meaningless inside a single-metric folder and are skipped there by their own
    # preconditions. They live in one comparison folder holding every metric's rows.
    if len(specs) > 1:
        written.append(write_folder("comparison", result.rows, result.maps,
                                    metric=", ".join(s.name for s in specs), comparison=True))

    for path in written:
        log.info("wrote %s", path)


def _overrides() -> list[str]:
    try:
        return list(HydraConfig.get().overrides.task)
    except Exception:  # noqa: BLE001  # pragma: no cover - outside a Hydra run
        return []


if __name__ == "__main__":
    main()
