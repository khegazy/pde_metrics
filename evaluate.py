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

import logging
import sys
import time
from pathlib import Path
from typing import Any

import hydra
import pandas as pd
from omegaconf import DictConfig, OmegaConf

from degradations import registry as deg_registry
from fmeval import io as fio
from fmeval.data.base import READERS, TimeSelection, Trajectory
from fmeval.data.locate import resolve_dataset_path, trajectory_provenance
from fmeval.derived import RecomputingTrajectory
from fmeval.ladder import build_ladder, ladder_axes
from fmeval.pipeline import DatasetInfo, MapRequest, parse_map_key, run
from metrics import registry as metric_registry

log = logging.getLogger(__name__)


def open_trajectory(cfg: DictConfig) -> Trajectory:
    """Construct the reader named by ``dataset.format``.

    Explicit imports rather than a package walk: readers are a small closed set maintained
    with the harness, unlike metrics and degradations which are open contributor sets.
    """
    from fmeval.data import (  # noqa: F401  (register the formats)
        kinet_raw,
        synthetic_ensemble,
        well,
    )

    fmt = cfg.dataset.format
    if fmt not in READERS:
        raise KeyError(f"unknown dataset format {fmt!r}; available: {sorted(READERS)}")

    reader_kwargs = OmegaConf.to_container(cfg.dataset.get("reader", {}), resolve=True)
    if not READERS[fmt].reads_from_disk:
        return READERS[fmt](Path(cfg.dataset.path), **reader_kwargs)

    location = resolve_dataset_path(
        cfg.dataset.path, cfg.paths.data, data_url=cfg.paths.get("data_url")
    )
    if location.source == "url":
        log.info(
            "dataset %s is not on this filesystem; reading the published copy at %s",
            cfg.dataset.name, location.url,
        )
    return READERS[fmt](location.target, **reader_kwargs)


def select_fields(cfg: DictConfig, trajectory: Trajectory,
                  specs: list[metric_registry.MetricSpec]) -> list[str]:
    """Fields to read: the config list if given, else what the metrics actually accept."""
    requested = cfg.get("fields") or cfg.dataset.get("fields")
    available = list(trajectory.fields)
    if requested:
        missing = [f for f in requested if f not in available]
        if missing:
            raise ValueError(
                f"dataset {cfg.dataset.name!r} does not provide {missing}; "
                f"it has {available}"
            )
        candidates = list(requested)
    else:
        candidates = available

    wanted: list[str] = []
    for field in candidates:
        if any(s.accepts(field) for s in specs):
            wanted.append(field)
    if not wanted:
        raise ValueError(
            f"no field in {candidates} is accepted by any of "
            f"{[s.name for s in specs]}"
        )
    return wanted


def dataset_info(cfg: DictConfig) -> DatasetInfo:
    complexity = cfg.dataset.get("complexity") or {}
    return DatasetInfo(
        name=cfg.dataset.name,
        trajectory=cfg.dataset.get("trajectory", ""),
        family=complexity.get("family", ""),
        rank=complexity.get("rank"),
        params=OmegaConf.to_container(complexity.get("params", {}), resolve=True) or {},
    )


@hydra.main(version_base=None, config_path="configs", config_name="config")
def main(cfg: DictConfig) -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stdout, force=True,
    )
    started = time.perf_counter()
    stamp = int(time.time())     # stamps every folder this invocation writes

    specs = [metric_registry.get(name) for name in cfg.metrics]
    deg_registry.discover()
    severity_levels = build_ladder(
        OmegaConf.to_container(cfg.degradation.ladder, resolve=True),
        include_reference=bool(cfg.degradation.include_reference),
        only=list(cfg.degradation.get("only") or []),
        skip=list(cfg.degradation.get("skip") or []),
    )
    axes = sorted(ladder_axes(severity_levels))
    log.info("ladder: %d severity levels over %d axes", len(severity_levels), len(axes))
    # The analysis reads both back from run_meta.json: which entry defines D = 1, and which
    # entries are probes rather than monotone axes (declared ordinal=False by their operator).
    anchor = str(cfg.analysis.anchor)
    probes = sorted({r.label for r in severity_levels if not r.ordinal})
    if anchor not in {r.label for r in severity_levels}:
        log.warning("analysis.anchor=%r is not an entry of this ladder; the analysis will fall "
                    "back to the largest translation and record that in anchor_source", anchor)
    elif anchor not in probes:
        log.warning("analysis.anchor=%r is an ordinal axis: D = 1 would be the median over all "
                    "its levels. Anchor on an entry whose operator is ordinal=False.", anchor)

    trajectory = open_trajectory(cfg)
    try:
        fields = select_fields(cfg, trajectory, specs)
        selection = TimeSelection(**OmegaConf.to_container(cfg.dataset.time, resolve=True))
        n_frames = len(selection.resolve(len(trajectory)))
        resolution = cfg.analysis_grid.get("resolution")
        analysis_grid = resolution or trajectory.grid.shape[0]
        log.info(
            "dataset %s: %d of %d frames (reduction %d), fields %s, analysis grid %s",
            cfg.dataset.name, n_frames, len(trajectory), selection.reduction, fields,
            analysis_grid,
        )

        if cfg.dataset.recompute_derived:
            trajectory = RecomputingTrajectory(trajectory)

        maps = MapRequest(**OmegaConf.to_container(cfg.report.error_map, resolve=True))

        result = run(
            trajectory,
            specs,
            severity_levels,
            fields=fields,
            selection=selection,
            dataset=dataset_info(cfg),
            seed=int(cfg.seed),
            analysis_resolution=resolution,
            remap_method=cfg.analysis_grid.method,
            maps=maps,
        )
        # Before the `finally`: the request counters live on the HTTP file object, which
        # close() releases.
        data_source = trajectory_provenance(trajectory)
    finally:
        trajectory.close()

    elapsed = time.perf_counter() - started
    log.info(
        "%d rows in %.1fs (io %.1fs, degrade %.1fs, metrics %.1fs)",
        len(result.rows), elapsed, result.io_seconds, result.degrade_seconds,
        result.metric_seconds,
    )

    # The severity calibration is part of a run's identity: a calibrated axis means nothing
    # without the measured field properties it was resolved against, and two datasets are only
    # comparable on such an axis if their calibrations are recorded alongside the numbers.
    calibration_table = pd.DataFrame(result.calibration.summary())
    spectrum_table = pd.DataFrame(result.calibration.spectrum_frame())

    overrides = _overrides()
    complexity = cfg.dataset.get("complexity") or {}

    def write_folder(name: str, rows: pd.DataFrame, maps: dict, **meta: Any) -> Path:
        """One self-contained run folder: numbers, calibration, config, maps, provenance."""
        folder = fio.make_run_folder(cfg.paths.results, name, stamp)
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
            dataset=cfg.dataset.name,
            dataset_label=str(complexity.get("label", "")),
            dataset_notes=str(cfg.dataset.get("notes", "")),
            data_source=data_source,
            n_frames=result.n_frames,
            n_rows=len(rows),
            fields=fields,
            analysis_grid=analysis_grid,
            ladder_axes=axes,
            n_severity_levels=len(severity_levels),
            anchor_label=anchor,
            probe_labels=probes,
            seed=int(cfg.seed),
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
        from hydra.core.hydra_config import HydraConfig

        return list(HydraConfig.get().overrides.task)
    except Exception:  # noqa: BLE001  # pragma: no cover - outside a Hydra run
        return []


if __name__ == "__main__":
    main()
