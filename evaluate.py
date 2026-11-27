"""Evaluate metrics against a degradation ladder and write a run folder per metric.

    python evaluate.py metrics=[mse] dataset=kinet_re5e4_dev
    python evaluate.py 'metrics=[mae,mse,vrmse]' dataset=kinet_re5e4 \\
        dataset.time.reduction=100
    python evaluate.py metrics=[mse] degradation=quick
    python evaluate.py metrics=[mse] analysis_grid.resolution=128

Each metric gets its own ``results/<metric>_<time>/`` folder, all sharing one timestamp so
a multi-metric run is obviously one experiment. The folders carry the raw numbers, the
resolved config and full provenance, so they regenerate their own report without the repo.
"""

from __future__ import annotations

import dataclasses
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

from fmeval import CONFIGS
from fmeval import io as fio
from fmeval.config import Config, SlowMetric, build_job
from fmeval.data.base import READERS, Trajectory
from fmeval.data.locate import trajectory_provenance
from fmeval.data.readers import open_trajectory
from fmeval.derived import RECIPES, RecomputingTrajectory
from fmeval.ladder import FORECAST_LEVEL, build_ladder, ladder_axes
from fmeval.pipeline import DatasetInfo, PipelineResult, parse_map_key, run
from metrics import registry as metric_registry

log = logging.getLogger(__name__)


def select_fields(job: Config, trajectory: Trajectory,
                  specs: list[metric_registry.MetricSpec]) -> list[str]:
    """Fields to read: the config list if given, else what the metrics actually accept.

    When the dataset recomputes its derived fields, a derived field's inputs
    (``fmeval.derived.RECIPES``) are read too, so the field is recomputed on the analysis grid
    rather than the solver's stored operator being scored; a metric that does not accept an
    input still produces no rows for it.
    """
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
    if job.dataset.recompute_derived:
        wanted += [i for i in dict.fromkeys(i for f in wanted for i in RECIPES.get(f, ()))
                   if i in available and i not in wanted]
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


@hydra.main(version_base=None, config_path=str(CONFIGS), config_name="config")
def main(cfg: DictConfig) -> Path:
    """Run one evaluation and return the folder holding every metric's rows.

    That is the comparison folder when several metrics ran and the one metric's folder
    otherwise; a dataset-family multirun gathers these (``fmeval.io.FamilyComparison``).
    """
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stdout, force=True,
    )
    started = time.perf_counter()
    # Every value is read from `job`, the config built into its schema (fmeval/config.py), so a
    # missing, misspelt or refused key stops the run here, before any data is read. `cfg` is
    # kept only to record the composed config.
    job = build_job(cfg)
    stamp = fio.claim_stamp(job.paths.results)  # stamps every folder this invocation writes

    specs = [metric_registry.get(name) for name in job.metrics]
    severity_levels = build_ladder(job.degradation)
    # Entries undefined or pathological on this dataset are dropped with the dataset's reason,
    # logged and recorded, never silently; an exclusion the ladder does not hold is not one.
    excluded = {label: reason for label, reason in job.dataset.exclude_degradations.items()
                if any(level.label == label for level in severity_levels)}
    for label, reason in excluded.items():
        log.warning("dataset %s excludes ladder entry %s: %s", job.dataset.name, label, reason)
    severity_levels = [level for level in severity_levels if level.label not in excluded]
    # Metrics the dataset evaluates more cheaply (dataset.slow_metrics), checked before any data
    # is read: a misspelt name or a grid finer than the run's is refused, not ignored.
    slow = {name: SlowMetric(**options) for name, options in job.dataset.slow_metrics.items()}
    for name, setting in slow.items():
        metric_registry.get(name)
        if (setting.analysis_resolution is not None and job.analysis_grid.resolution is not None
                and setting.analysis_resolution > job.analysis_grid.resolution):
            raise ValueError(
                f"dataset.slow_metrics.{name}.analysis_resolution={setting.analysis_resolution} "
                f"is finer than the run's analysis grid {job.analysis_grid.resolution}")
    anchor = job.analysis.anchor
    trajectory = open_trajectory(job.dataset, job.paths)
    prediction = trajectory.predictions() if hasattr(trajectory, "predictions") else None
    if prediction is not None:
        # The predictor's own errors replace the ladder. The anchor entry stays, so the damage
        # D keeps its meaning: the forecast's error as a fraction of the anchor's.
        dropped = [r.label for r in severity_levels if not (r.is_reference or r.label == anchor)]
        severity_levels = [r for r in severity_levels if r.is_reference or r.label == anchor]
        log.info("dataset %s pairs every frame with a prediction, which is scored in place of "
                 "the ladder; %d ladder severity levels not run, the anchor %r kept",
                 job.dataset.name, len(dropped), anchor)
    recorded = severity_levels + ([FORECAST_LEVEL] if prediction is not None else [])
    axes = sorted(ladder_axes(recorded))
    log.info("ladder: %d severity levels over %d axes", len(recorded), len(axes))
    # The analysis reads both back from run_meta.json: which entry defines D = 1, and which
    # entries are probes rather than monotone axes (declared ordinal=False by their operator).
    probes = sorted({r.label for r in recorded if not r.ordinal})
    if anchor not in {r.label for r in severity_levels}:
        log.warning("analysis.anchor=%r is not an entry of this ladder; the analysis will fall "
                    "back to the largest translation, or without one to the harshest level "
                    "of an ordinal axis, and record that in anchor_source", anchor)
    elif anchor not in probes:
        log.warning("analysis.anchor=%r is an ordinal axis: D = 1 would be the median over all "
                    "its levels. Anchor on an entry whose operator is ordinal=False.", anchor)

    # Every reader option the run used, defaults included. The recorded config states only what
    # a file or an override changed, and a reader's defaults belong to its code, which can move.
    reader = inspect.signature(READERS[job.dataset.format]).bind_partial(**job.dataset.reader)
    reader.apply_defaults()
    try:
        fields = select_fields(job, trajectory, specs)
        selection = job.dataset.time
        trajectory_frames = len(trajectory)
        n_frames = len(selection.part(selection.resolve(trajectory_frames)))
        log.info(
            "dataset %s: %d of %d frames (reduction %d), fields %s",
            job.dataset.name, n_frames, trajectory_frames, selection.reduction, fields,
        )

        if job.dataset.recompute_derived:
            trajectory = RecomputingTrajectory(trajectory)
            if prediction is not None:
                prediction = RecomputingTrajectory(prediction)

        # A slow metric on a coarser grid (dataset.slow_metrics) is a pass of the pipeline of its
        # own at that grid, with the ladder applied there; one on fewer frames is thinned inside
        # the pass of its grid. Every other metric runs in the pass at the run's grid.
        passes: dict[int | None, list[metric_registry.MetricSpec]] = {}
        for spec in specs:
            own = slow[spec.name].analysis_resolution if spec.name in slow else None
            passes.setdefault(job.analysis_grid.resolution if own is None else own,
                              []).append(spec)
        results = {
            grid: run(
                trajectory,
                group,
                severity_levels,
                fields=fields,
                selection=selection,
                dataset=dataset_info(job),
                seed=job.seed,
                analysis_resolution=grid,
                remap_method=job.analysis_grid.method,
                maps=job.report.error_map,
                prediction=prediction,
                every={name: setting.every for name, setting in slow.items()},
            )
            for grid, group in passes.items()
        }
        # Before the `finally`: the request counters live on the HTTP file object, which
        # close() releases.
        data_source = trajectory_provenance(trajectory)
    finally:
        trajectory.close()
        if prediction is not None:
            prediction.close()

    elapsed = time.perf_counter() - started
    for result in results.values():
        log.info("%d rows on a %d-cell analysis grid (io %.1fs, degrade %.1fs, metrics %.1fs)",
                 len(result.rows), result.analysis_grid, result.io_seconds,
                 result.degrade_seconds, result.metric_seconds)
    log.info("finished in %.1fs", elapsed)
    result_of = {spec.name: results[grid] for grid, group in passes.items() for spec in group}

    overrides = _overrides()

    def write_folder(name: str, result: PipelineResult, rows: pd.DataFrame, maps: dict,
                     companions: pd.DataFrame, **meta: Any) -> Path:
        """One self-contained run folder: numbers, calibration, config, maps, provenance.

        The severity calibration is part of a run's identity: a calibrated axis means nothing
        without the measured field properties it was resolved against, and two datasets are only
        comparable on such an axis if their calibrations are recorded alongside the numbers.
        ``result`` is the pass of the pipeline the rows come from, which measured it.
        """
        folder = fio.make_run_folder(job.paths.results, name, stamp)
        fio.write_results(folder, rows)
        if not companions.empty:
            fio.write_results(folder, companions, name=fio.COMPANIONS)
        if result.calibration.fields:       # none on a forecast, which runs no ladder
            fio.write_table(folder, pd.DataFrame(result.calibration.summary()), "calibration")
            fio.write_table(folder, pd.DataFrame(result.calibration.spectrum_frame()),
                            "calibration_spectrum")
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
            n_frames=int(rows["frame_index"].nunique()),
            trajectory_frames=trajectory_frames,
            reader_options={k: v for k, v in reader.arguments.items() if k != "path"},
            boundary=list(trajectory.grid.boundary),
            n_rows=len(rows),
            fields=fields,
            analysis_grid=result.analysis_grid,
            ladder_axes=axes,
            n_severity_levels=len(recorded),
            excluded_degradations=excluded,
            slow_metrics={name: dataclasses.asdict(setting) for name, setting in slow.items()},
            anchor_label=anchor,
            probe_labels=probes,
            seed=job.seed,
            command=" ".join(sys.argv),
            **meta,
        )
        return folder.root

    timings = {"total_s": elapsed,
               **{key: sum(getattr(r, attribute) for r in results.values())
                  for key, attribute in (("io_s", "io_seconds"), ("degrade_s", "degrade_seconds"),
                                         ("metric_s", "metric_seconds"))}}
    # A metric the pipeline did not run on this dataset -- an ensemble metric on one
    # realization, a periodic-only metric on a bounded domain -- has no rows, and a folder
    # without rows is not a run: its report would fail. The pipeline logged why. A run in which
    # no metric produced a row wrote nothing, so it fails rather than exiting as a success.
    ran = [spec.name for spec in specs
           if (result_of[spec.name].rows["metric"] == spec.name).any()]
    if not ran:
        raise ValueError(
            f"no metric produced a row on dataset {job.dataset.name!r} "
            f"({', '.join(spec.name for spec in specs)}), so no run folder was written; "
            "the log above says why"
        )
    def labels(name: str) -> set[str]:
        """The metric's own label and every companion's (``name.<companion>``), so a metric's
        folder keeps its named companions' rows and maps as the comparison folder does."""
        spec = metric_registry.get(name)
        return {name} | {metric_registry.companion_label(name, c.name) for c in spec.companions}

    written = []
    for name in ran:
        result = result_of[name]
        written.append(write_folder(
            name, result, result.rows[result.rows["metric"] == name],
            {k: v for k, v in result.maps.items() if parse_map_key(k)[0] in labels(name)},
            (result.companions[result.companions["metric"].isin(labels(name))]
             if not result.companions.empty else result.companions),
            metric=name, timings=timings))
    # Cross-metric figures -- redundancy, the selectivity comparison, the cost frontier --
    # are meaningless inside a single-metric folder and are skipped there by their own
    # preconditions. They live in one comparison folder holding the rows of every metric scored
    # on the run's own grid; a slow metric on a coarser grid answered a different ladder and is
    # compared with nothing, which its own folder's slow_metrics records.
    if job.analysis_grid.resolution in results:
        main = results[job.analysis_grid.resolution]
        compared = [name for name in ran if result_of[name] is main]
        if len(compared) > 1:
            written.append(write_folder("comparison", main, main.rows, main.maps,
                                        main.companions, metric=", ".join(compared),
                                        comparison=True))

    for path in written:
        log.info("wrote %s", path)
    return written[-1]


def _overrides() -> list[str]:
    try:
        return list(HydraConfig.get().overrides.task)
    except Exception:  # noqa: BLE001  # pragma: no cover - outside a Hydra run
        return []


if __name__ == "__main__":
    main()
