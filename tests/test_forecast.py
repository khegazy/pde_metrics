"""Real forecasts: the pair reader, the pipeline's prediction path, its analysis and its figure.

The fixture holds two runs at two resolutions, each non-square (16x8 and 8x4), so a reader that
transposes x and y, or a pipeline that pools frames of different grids, fails here. Its coarse
run takes steps twice as long, so both runs reach the same lead times, as the real ones do.
"""

from __future__ import annotations

import json
import subprocess
import sys

import h5py
import numpy as np
import pandas as pd
import pytest

from fmeval import REPO
from fmeval import analysis as an
from fmeval.data.base import READERS
from fmeval.data.forecast import ForecastPairs
from fmeval.derived import RecomputingTrajectory, vorticity_from_velocity
from fmeval.io import (
    RunFolder,
    read_results,
    read_run_meta,
    write_config,
    write_results,
    write_run_meta,
)
from fmeval.ladder import FORECAST_LEVEL, build_ladder
from fmeval.pipeline import DatasetInfo, run
from fmeval.report.driver import build_context, render
from metrics import registry as metric_registry
from tests.fixtures_h5 import SHAPE, write_forecast

COARSE = (SHAPE[0] // 2, SHAPE[1] // 2)
LENGTH = [float(n) for n in SHAPE]
FINE_FILES = ["fine/forecast_t0-0", "fine/forecast_t0-12"]
FILES = [*FINE_FILES, "coarse/forecast_t0-0", "coarse/forecast_t0-6"]
#: The coarse run's target clock lags its prediction's, as on the real coarse runs.
LAG = 0.125


@pytest.fixture
def root(tmp_path):
    """Two runs, two forecasts each, with the same lead times on both grids."""
    for start in (0, 12):
        write_forecast(tmp_path, "fine", start, SHAPE, steps=(2, 4, 6), step_time=0.25)
    for start, lag in ((0, LAG), (6, 0.0)):
        write_forecast(tmp_path, "coarse", start, COARSE, steps=(1, 2, 3), step_time=0.5,
                       target_lag=lag)
    return tmp_path


@pytest.fixture
def pairs(root):
    with ForecastPairs(root, files=FILES, length=LENGTH) as targets:
        yield targets


def evaluate(targets, names=("mse", "enstrophy", "crps"), **kw):
    """The prediction path of the pipeline, with the anchor as the only ladder entry."""
    prediction = RecomputingTrajectory(targets.predictions())
    try:
        return run(RecomputingTrajectory(targets), [metric_registry.get(n) for n in names],
                   build_ladder({"mean_field": {"severities": [0]}}),
                   fields=["density", "velocity", "vorticity"],
                   dataset=DatasetInfo(name="forecast_fixture"), prediction=prediction, **kw)
    finally:
        prediction.close()


# --- the reader ---------------------------------------------------------------------------


def test_the_reader_is_registered_and_reads_every_frame_of_every_file(pairs):
    assert READERS["forecast_pairs"] is ForecastPairs
    assert len(pairs) == 12 and pairs.fields == ("density", "velocity", "vorticity")
    assert pairs.labels == FILES
    assert [pairs.grid_at(t).shape for t in (0, 5, 6, 11)] == [SHAPE, SHAPE, COARSE, COARSE]
    assert pairs.grid_at(6).spacing == (2.0, 2.0), "spacing is length / n on every run"


def test_axis_and_channel_order_on_a_non_square_grid(pairs):
    """u=1, v=2 at the first target step: a transpose or a channel swap fails."""
    velocity = pairs.frame(0, ["velocity"])["velocity"]
    assert velocity.shape == (2, *SHAPE)
    assert np.all(velocity[0] == 1.0) and np.all(velocity[1] == 2.0)


def test_each_frame_says_which_file_and_lead_it_is(pairs):
    """Both runs reach the same lead times with steps of different lengths."""
    assert pairs.frame_columns(0) == {"trajectory": "fine/forecast_t0-0", "param_resolution": 16,
                                      "lead_step": 2, "lead_time": 0.5}
    assert pairs.frame_columns(10) == {"trajectory": "coarse/forecast_t0-6",
                                       "param_resolution": 8, "lead_step": 2, "lead_time": 1.0}
    assert [pairs.frame_columns(t)["lead_time"] for t in (3, 9)] == [0.5, 0.5]


def test_both_sides_read_on_the_prediction_clock_and_the_lag_is_recorded(pairs):
    with pairs.predictions() as predictions:
        assert np.array_equal(predictions.times, pairs.times)
        assert pairs.times[6] == pytest.approx(0.5), "the prediction's clock, not the target's"
        offsets = {label: f["clock_offset"] for label, f in pairs.meta["files"].items()}
        assert offsets["coarse/forecast_t0-0"] == pytest.approx(LAG)
        assert offsets["fine/forecast_t0-0"] == 0.0
        target, predicted = pairs.frame(4, ["density"]), predictions.frame(4, ["density"])
        assert not np.array_equal(target["density"], predicted["density"])


def test_vorticity_without_velocity_is_refused(pairs):
    """The stored vorticity of the two sides is on different spacings; only a curl recomputed
    from velocity is comparable, and that needs velocity read beside it (issue 099)."""
    with pytest.raises(ValueError, match="without velocity"):
        pairs.frame(0, ["vorticity"])


@pytest.mark.parametrize("damage,match", [
    (lambda f: f["t_index"]["pred_4"].__setitem__(0, 99), "not a pair"),
    (lambda f: f["t"]["pred_4"].__setitem__(0, 9.0), "does not advance"),
    (lambda f: [f[g].__delitem__("target_6") for g in ("rho", "u", "vorticity", "stability_scale",
                                                       "t", "t_index")], "same two or more"),
])
def test_a_file_whose_sides_do_not_pair_is_refused(root, damage, match):
    with h5py.File(root / "fine" / "forecast_t0-0.h5", "r+") as f:
        damage(f)
    with pytest.raises(ValueError, match=match):
        ForecastPairs(root, files=FILES, length=LENGTH)


# --- the pipeline -------------------------------------------------------------------------


def test_the_prediction_is_scored_against_its_target_on_every_frame(root):
    with (ForecastPairs(root, files=FINE_FILES, length=LENGTH) as targets,
          targets.predictions() as predictions):
        rows = evaluate(targets).rows
        target, predicted = targets.frame(1, ["density"]), predictions.frame(1, ["density"])
    assert set(rows["degradation"]) == {"identity", "mean_field", FORECAST_LEVEL.label}
    assert "crps" not in set(rows["metric"]), "an ensemble metric needs members"
    forecast = rows[rows["degradation"] == FORECAST_LEVEL.label]
    assert set(forecast["level"]) == {1} and not forecast["severity_degenerate"].any()
    mse = forecast[(forecast["metric"] == "mse") & (forecast["field"] == "density")
                   & (forecast["frame_index"] == 1)]["value"].item()
    assert mse == pytest.approx(metric_registry.get("mse").fn(target["density"],
                                                              predicted["density"]), rel=1e-12)
    reference = rows[(rows["level"] == 0) & (rows["metric"] == "mse")]
    assert (reference["value"] == 0.0).all()
    assert forecast[["lead_step", "lead_time", "trajectory"]].notna().all().all()
    assert set(forecast["trajectory"]) == set(FINE_FILES)


def test_the_prediction_vorticity_is_recomputed_from_its_velocity(root):
    """The stored prediction vorticity is twice the target's; the scored one is the curl."""
    with (ForecastPairs(root, files=FINE_FILES[:1], length=LENGTH) as targets,
          targets.predictions() as predictions):
        rows = evaluate(targets, names=("enstrophy", "mse")).rows
        predicted = predictions.frame(2, ["velocity", "vorticity"])
    curl = vorticity_from_velocity(predicted["velocity"], predicted.grid)
    enstrophy = metric_registry.get("enstrophy").fn
    scored = rows[(rows["metric"] == "enstrophy") & (rows["frame_index"] == 2)
                  & (rows["degradation"] == FORECAST_LEVEL.label)]["value"].item()
    assert scored == pytest.approx(enstrophy(curl), rel=1e-12)
    assert scored != pytest.approx(enstrophy(predicted["vorticity"]), rel=1e-3)


def test_frames_on_different_grids_need_a_common_analysis_grid(pairs):
    with pytest.raises(ValueError, match=r"analysis_grid\.resolution"):
        evaluate(pairs, names=("mse",))
    rows = evaluate(pairs, names=("mse",), analysis_resolution=COARSE[0]).rows
    assert set(rows["analysis_grid"]) == {COARSE[0]}
    assert set(rows["param_resolution"]) == {SHAPE[0], COARSE[0]}


def test_the_analysis_withholds_ordering_statistics_on_a_forecast(root):
    """The forecast has one prediction per frame: it is read as a probe, never ranked."""
    with ForecastPairs(root, files=FINE_FILES, length=LENGTH) as targets:
        rows = evaluate(targets, names=("mse",)).rows
    analysis = an.analyse(rows, meta={"anchor_label": an.MEAN_FIELD_LABEL,
                                      "probe_labels": [an.MEAN_FIELD_LABEL,
                                                       FORECAST_LEVEL.label]}, n_bootstrap=0)
    forecast = analysis.axes[analysis.axes["degradation"] == FORECAST_LEVEL.label]
    assert forecast["is_probe"].all() and forecast["rho"].isna().all()
    assert analysis.norm["anchor_source"].eq(an.MEAN_FIELD_LABEL).all()
    assert not any(c.startswith(FORECAST_LEVEL.label) for c in analysis.probes.columns), (
        "a forecast is reported step by step, never as one median over every step")


def test_each_prediction_step_is_scaled_by_its_own_target(root):
    """A forecast's damage is its error over the anchor's in the same frame: for mse, the
    prediction's error over the target's variance, step by step; the table of every prediction
    carries it unpooled, with the target's own value beside a single-field quantity's."""
    with ForecastPairs(root, files=FILES, length=LENGTH) as targets:
        rows = evaluate(targets, names=("mse", "enstrophy"), analysis_resolution=COARSE[0]).rows
    analysis = an.analyse(rows, meta={"anchor_label": an.MEAN_FIELD_LABEL,
                                      "probe_labels": [an.MEAN_FIELD_LABEL,
                                                       FORECAST_LEVEL.label]}, n_bootstrap=0)
    keys = ["field", "frame_index"]
    scored = analysis.scored[analysis.scored["metric"] == "mse"]
    anchor = scored[scored["degradation"] == an.MEAN_FIELD_LABEL].set_index(keys)["value"]
    lead = an.forecast_by_lead(analysis.scored, metric="mse", anchor_label=an.MEAN_FIELD_LABEL)
    predicted = scored[scored["degradation"] == FORECAST_LEVEL.label].set_index(keys)
    assert len(lead) == len(predicted) == 12 * 3, "every step of every forecast, one row each"
    own = anchor[predicted.index].to_numpy()
    assert predicted["damage"][own == 0].isna().all() and (own == 0).any(), (
        "a uniform target has no scale of its own, so no damage")
    np.testing.assert_allclose(predicted["damage"][own > 0],
                               predicted["value"][own > 0] / own[own > 0], rtol=1e-12)
    assert anchor.groupby("field").nunique().gt(1).all(), "the anchor differs between frames"
    assert set(lead["trajectory"]) == set(FILES) and lead["value_on_target"].eq(0).all()
    single = an.forecast_by_lead(analysis.scored, metric="enstrophy",
                                 anchor_label=an.MEAN_FIELD_LABEL)
    assert len(single) == 12 and single["value_on_target"].gt(0).any(), "the target's own value"
    assert sorted(single["lead_time"].unique()) == [0.5, 1.0, 1.5]


def test_the_error_is_drawn_against_lead_time_one_line_per_forecast(pairs, tmp_path):
    result = evaluate(pairs, names=("mse", "enstrophy"), analysis_resolution=COARSE[0])
    folder = RunFolder(tmp_path / "comparison_1").create()
    write_results(folder, result.rows)
    write_config(folder, {"metrics": ["mse", "enstrophy"], "seed": 0}, [])
    write_run_meta(folder, run_id=1, metric="mse, enstrophy", dataset="forecast_fixture",
                   anchor_label=an.MEAN_FIELD_LABEL,
                   probe_labels=[an.MEAN_FIELD_LABEL, FORECAST_LEVEL.label])
    outcome = {r.name: r for r in render(folder, build_context(folder, bootstrap=0),
                                         only=["response_along_time"], formats=("png",))}[
        "response_along_time"]
    assert outcome.status == "ok", outcome.reason
    data = pd.read_csv(folder.figure_data
                       / "response_along_time__metric-mse__field-density__along-lead.csv")
    assert set(data["trajectory"]) == set(FILES) and set(data["side"]) == {"prediction"}
    assert sorted(data["lead_time"].unique()) == [0.5, 1.0, 1.5]
    single = pd.read_csv(folder.figure_data
                         / "response_along_time__metric-enstrophy__field-vorticity__along-lead.csv")
    assert set(single["side"]) == {"prediction", "target"}, "a single-field quantity's truth too"


def test_evaluate_scores_the_forecast_in_place_of_the_ladder(root, tmp_path):
    """End to end: the ladder is cut to the anchor, the forecast is recorded as a probe, and no
    severity calibration is measured or written, since no ladder operator needs one."""
    out = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(REPO / "evaluate.py"), "dataset=forecast_re5e4", "metrics=[mse]",
         f"dataset.path={root}", f"dataset.reader.files=[{','.join(FINE_FILES)}]",
         f"dataset.reader.length=[{LENGTH[0]},{LENGTH[1]}]", "paths.data_url=null",
         f"paths.results={out}", f"hydra.run.dir={tmp_path}/h"],
        check=True, capture_output=True, cwd=tmp_path)
    (folder,) = out.glob("mse_*")
    meta = read_run_meta(folder)
    assert FORECAST_LEVEL.label in meta["probe_labels"] and meta["ladder_axes"] == [
        FORECAST_LEVEL.label, an.MEAN_FIELD_LABEL]
    rows = read_results(folder)
    assert set(rows["degradation"]) == {"identity", an.MEAN_FIELD_LABEL, FORECAST_LEVEL.label}
    assert json.dumps(meta["reader_options"]["files"]) == json.dumps(FINE_FILES)
    assert not list(folder.glob("data/calibration*")), "a forecast calibrates nothing"


# --- the real files -----------------------------------------------------------------------


@pytest.mark.data
def test_the_finest_targets_are_frames_of_the_production_trajectory():
    """Ground truth: the 256^2 targets are kinet_re5e4 at the same solver step."""
    root = REPO / "datasets" / "results" / "entropic_D2Q9"
    production = (REPO / "datasets" / "kinet" / "doubly_periodic"
                  / "weakly_compressible_isoT_fluids"
                  / "sys_Re-5e4_Ma-1en1" / "D2Q9_shape-256-256_T-10000_H-dc804f.h5")
    with (ForecastPairs(root, files=["F-906861_64/forecast_t0-5000"],
                        length=[256.0, 256.0]) as targets,
          h5py.File(production, "r") as kinet):
        for t in (0, 9):
            step = 5000 + targets.frame_columns(t)["lead_step"]
            frame = targets.frame(t, ["density", "velocity"])
            assert frame.time == pytest.approx(kinet["time"][step], rel=1e-12)
            np.testing.assert_allclose(frame["density"], kinet["density"][0, :, step], atol=1e-8)
            np.testing.assert_allclose(frame["velocity"], kinet["velocity"][0, :, step],
                                       atol=1e-7)
