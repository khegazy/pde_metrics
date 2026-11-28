"""The loader contract, shared across every reader.

The two highest-value tests here are easy to overlook:

* ``test_axis_and_channel_order`` -- fixtures are non-square (16x8) with u=1, v=2, so a
  transposed or channel-swapped reader fails loudly. On the real 256^2 data it would pass
  silently and every figure in every report would be wrong.
* ``test_never_slices_the_time_axis`` -- monkeypatches ``h5py`` to record every key used.
  A one-character slip from ``ds[0, :, t]`` to ``ds[0, :, :]`` turns a 1-second read into
  5 GB of I/O, and no correctness test would notice.

That second test has one blind spot, and it has a sibling elsewhere because of it: it
records only keys long enough to reach the time position of a field read, so a read of the
1-D ``time`` dataset -- key ``(slice(None),)``, length one -- passes straight through it.
Slicing *that* dataset whole is the most expensive read in this package over HTTP.
``test_opening_and_iterating_never_slices_a_chunked_clock`` in tests/test_remote_data.py
covers it.
"""

from __future__ import annotations

import json
import re
import tracemalloc
from pathlib import Path

import h5py
import numpy as np
import pytest

from fmeval import REPO
from fmeval.config import build_job, compose_config
from fmeval.data.base import FIELDS, READERS, GridSpec, TimeSelection, Trajectory
from fmeval.data.convert_kinet import convert_kinet_grouped
from fmeval.data.kinet_raw import KinetRawTrajectory
from fmeval.data.readers import open_trajectory
from fmeval.data.well import WellTrajectory
from fmeval.derived import RecomputingTrajectory
from fmeval.ladder import build_ladder
from fmeval.pipeline import DatasetInfo, run
from metrics import registry as metric_registry
from metrics.shock_set_distance.metric import shock_mask
from tests.fixtures_h5 import (
    N_FRAMES,
    SHAPE,
    write_kinet_grouped,
    write_kinet_raw,
    write_kinet_taylor_green,
    write_well,
)

#: Every layout the contract holds: the writer of its synthetic file, the class that reads it,
#: and the position of the time axis in a field read's h5py key -- ``(sim, C, T, ...)`` in the
#: raw kinet layout, ``(sim, T, ...)`` in the Well layout. ``kinet_grouped`` is kinet's current
#: grouped layout after ``fmeval.data.convert_kinet``, read by the raw reader.
LAYOUTS = {
    "kinet_raw": (write_kinet_raw, KinetRawTrajectory, 2),
    "kinet_grouped": (lambda path: convert_kinet_grouped(
        write_kinet_grouped(path.with_name("grouped.h5")), path), KinetRawTrajectory, 2),
    "well": (write_well, WellTrajectory, 1),
}


@pytest.fixture(params=sorted(LAYOUTS))
def layout(request, tmp_path):
    """``(format name, path to its synthetic file, reader class, time-axis position)``."""
    write, cls, time_position = LAYOUTS[request.param]
    return request.param, write(tmp_path / f"{request.param}.h5"), cls, time_position


@pytest.fixture
def traj(layout):
    _, path, cls, _ = layout
    with cls(path, nan_policy="error") as t:
        yield t


# --- shape, dtype, axis order ------------------------------------------------------


def test_frame_shape_dtype_and_channels(traj):
    frame = traj.frame(1, traj.fields)
    for name, arr in frame.fields.items():
        want_c = FIELDS[name].n_channels(traj.grid.n_spatial)
        assert arr.shape == (want_c, *SHAPE), f"{name} has shape {arr.shape}"
        assert arr.dtype == np.float64, "float32 on disk must be cast to the contract"
        assert np.isfinite(arr).all()


def test_axis_and_channel_order(traj):
    """u=1, v=2 at t=0 on a non-square grid: catches a channel swap AND a transpose.

    The Well file stores velocity channel-last, ``(X, Y, D)``, against the contract's
    ``(D, X, Y)``, so this is also the check of that reader's ``moveaxis``: the one line that
    would be invisible on a square grid.
    """
    vel = traj.frame(0, ["velocity"])["velocity"]
    assert vel.shape == (2, *SHAPE), "spatial axes are transposed (grid is 16x8)"
    assert np.allclose(vel[0], 1.0), "velocity channel 0 is not the x component"
    assert np.allclose(vel[1], 2.0), "velocity channel 1 is not the y component"


def test_grid_spec(traj):
    """The Well reader builds the grid from coordinate arrays and reads periodicity from
    ``boundary_conditions`` rather than assuming it; raw kinet reads its root attributes."""
    g = traj.grid
    assert g.shape == SHAPE
    assert g.dims == ("x", "y")
    assert g.spacing == (1.0, 1.0)
    assert g.boundary == ("periodic", "periodic")
    assert g.n_spatial == 2
    assert g.length == (float(SHAPE[0]), float(SHAPE[1]))


def test_grid_axis_resolution_is_dimension_aware():
    """`axis('x')` must be -2 in 2D and -3 in 3D, never a hardcoded constant."""
    g2 = GridSpec((16, 8), (1.0, 1.0), ("periodic", "periodic"), ("x", "y"), (0.0, 0.0))
    assert g2.axis("x") == -2 and g2.axis("y") == -1
    g3 = GridSpec((4, 5, 6), (1.0,) * 3, ("periodic",) * 3, ("x", "y", "z"), (0.0,) * 3)
    assert g3.axis("x") == -3 and g3.axis("y") == -2 and g3.axis("z") == -1


def test_grid_coarsened_scales_spacing():
    """Spacing must grow by the factor -- forgetting this inflates spectral derivatives."""
    g = GridSpec((16, 8), (0.5, 0.5), ("periodic", "periodic"), ("x", "y"), (0.0, 0.0))
    c = g.coarsened(2)
    assert c.shape == (8, 4)
    assert c.spacing == (1.0, 1.0)
    assert c.length == g.length  # physical extent is unchanged
    with pytest.raises(ValueError, match="does not divide"):
        g.coarsened(3)


def test_grid_refuses_an_unknown_boundary_type():
    with pytest.raises(ValueError, match="unknown boundary"):
        GridSpec((16, 8), (1.0, 1.0), ("periodic", "wall"), ("x", "y"), (0.0, 0.0))


def test_a_neumann_axis_extends_to_its_even_mirror():
    """A zero-gradient wall is extended by appending the axis reversed.

    The result is periodic over twice the length and continuous across both seams -- the
    two cells meeting at each seam are equal -- so an operator that wraps sees no jump at the
    wall. Leading axes (channels, members) and periodic axes are untouched, the spacing is
    kept, cropping recovers the field, and coarsening keeps the boundary types.
    """
    g = GridSpec((16, 8), (1.0, 0.5), ("neumann", "periodic"), ("x", "y"), (0.0, 0.0))
    x = np.random.default_rng(0).standard_normal((3, 2, 16, 8))
    e = g.extend(x)
    assert e.shape == (3, 2, 32, 8)
    assert g.extended == GridSpec((32, 8), (1.0, 0.5), ("periodic", "periodic"), ("x", "y"),
                                  (0.0, 0.0))
    assert np.array_equal(e[..., :16, :], x)
    assert np.array_equal(e[..., 16:, :], x[..., ::-1, :])
    assert np.array_equal(e[..., 15, :], e[..., 16, :]) and np.array_equal(e[..., 31, :],
                                                                          e[..., 0, :])
    assert g.coarsened(2).boundary == g.boundary


def test_a_periodic_grid_is_not_extended():
    g = GridSpec((16, 8), (1.0, 1.0), ("periodic", "periodic"), ("x", "y"), (0.0, 0.0))
    x = np.zeros((1, 16, 8))
    assert g.extend(x) is x and g.extended is g and g.is_periodic


# --- times -------------------------------------------------------------------------


def test_times_are_monotone_finite_and_start_at_zero(traj):
    """The clock is the ``time`` dataset. Raw kinet also stores ``time_scale``, whose first
    entry is NaN in real files: read as a clock it would fail the finiteness check here."""
    times = traj.times
    assert len(times) == N_FRAMES == len(traj)
    assert np.isfinite(times).all()
    assert times[0] == 0.0
    assert np.all(np.diff(times) > 0)


# --- field vocabulary --------------------------------------------------------------


def test_fields_are_canonical(traj):
    assert set(traj.fields) <= set(FIELDS)


def test_degenerate_and_redundant_fields_excluded(traj):
    assert "temperature" not in traj.fields, "spatially degenerate; not a field"
    assert "pressure" not in traj.fields, "redundant with density; excluded by default"


def test_redundant_field_available_on_request(layout):
    _, path, cls, _ = layout
    with cls(path, include_redundant=True) as t:
        assert "pressure" in t.fields
        frame = t.frame(1, ["density", "pressure"])
        assert np.allclose(frame["pressure"], frame["density"] / 3.0)


def test_requesting_unknown_field_raises(traj):
    with pytest.raises(ValueError, match="unknown canonical field"):
        traj.frame(1, ["not_a_field"])


def test_requesting_unavailable_field_raises(traj):
    with pytest.raises(ValueError, match="not available"):
        traj.frame(1, ["pressure"])


# --- NaN policy --------------------------------------------------------------------


def test_nan_policy_error_on_all_nan_frame(kinet_file):
    """t=0 has all-NaN stability fields in real data; here vorticity is fine but we
    exercise the guard through a field the fixture does make non-finite."""
    with KinetRawTrajectory(kinet_file, nan_policy="error") as t:
        frame = t.frame(0, ["density"])
        assert np.isfinite(frame["density"]).all()


def test_nan_policy_warn_and_ignore(tmp_path):
    path = write_kinet_raw(tmp_path / "nan.h5")
    with h5py.File(path, "r+") as f:
        f["density"][0, 0, 0, 0, 0] = np.nan

    with KinetRawTrajectory(path, nan_policy="error") as t:
        with pytest.raises(ValueError, match="non-finite"):
            t.frame(0, ["density"])
    with KinetRawTrajectory(path, nan_policy="warn") as t:
        with pytest.warns(RuntimeWarning, match="non-finite"):
            t.frame(0, ["density"])
    with KinetRawTrajectory(path, nan_policy="ignore") as t:
        assert not np.isfinite(t.frame(0, ["density"])["density"]).all()


# --- time selection ----------------------------------------------------------------


@pytest.mark.parametrize(
    "sel,n,expected",
    [
        (TimeSelection(), 5, [0, 1, 2, 3, 4]),
        (TimeSelection(start=1), 5, [1, 2, 3, 4]),
        (TimeSelection(start=1, reduction=2), 5, [1, 3]),
        (TimeSelection(start=1, reduction=2, max_frames=1), 5, [1]),
        (TimeSelection(start=1, stop=4), 5, [1, 2, 3]),
        (TimeSelection(reduction=10), 5, [0]),
        (TimeSelection(start=99), 5, []),
    ],
)
def test_time_selection_resolves(sel, n, expected):
    assert sel.resolve(n).tolist() == expected


def test_max_frames_applies_after_reduction():
    """Order matters: cap the reduced set, not the raw range."""
    sel = TimeSelection(reduction=3, max_frames=2)
    assert sel.resolve(20).tolist() == [0, 3]


def test_invalid_reduction_raises():
    with pytest.raises(ValueError, match="reduction must be >= 1"):
        TimeSelection(reduction=0)


def test_frame_stride_puts_a_finer_run_on_a_coarser_clock(kinet_file, tmp_path):
    """Frame i of a strided reader is stored frame i * stride, values and clock alike, and a
    stride that does not divide the solver steps is refused rather than dropping the last frame.
    """
    with KinetRawTrajectory(kinet_file) as plain, \
            KinetRawTrajectory(kinet_file, frame_stride=2) as strided:
        assert strided.times.tolist() == plain.times[::2].tolist()
        assert len(strided) == (N_FRAMES - 1) // 2 + 1
        assert np.array_equal(strided.frame(1, ["velocity"])["velocity"],
                              plain.frame(2, ["velocity"])["velocity"])
    for bad in (0, 3):
        with pytest.raises(ValueError, match="frame_stride"):
            KinetRawTrajectory(kinet_file, frame_stride=bad)


def test_cell_reads_a_run_in_units_of_one_cell_and_one_step(kinet_file):
    """``cell`` multiplies the spacing, and the solver step of every frame (``time_index``), by
    ``cell`` and divides vorticity by it, while velocity, density and pressure keep their lattice
    values; it is refused beside ``box`` or when not positive."""
    with KinetRawTrajectory(kinet_file, include_redundant=True) as plain, \
            KinetRawTrajectory(kinet_file, include_redundant=True, cell=0.5) as scaled:
        assert scaled.grid.spacing == tuple(0.5 * s for s in plain.grid.spacing)
        assert scaled.times.tolist() == (0.5 * np.arange(N_FRAMES)).tolist() != plain.times.tolist()
        for name in ("density", "velocity", "pressure"):
            assert np.array_equal(scaled.frame(2, [name])[name], plain.frame(2, [name])[name])
        assert np.array_equal(scaled.frame(2, ["vorticity"])["vorticity"],
                              plain.frame(2, ["vorticity"])["vorticity"] / 0.5)
    for bad in ({"cell": 0.0}, {"cell": 0.5, "box": 1.0}):
        with pytest.raises(ValueError, match="cell="):
            KinetRawTrajectory(kinet_file, **bad)


def test_a_candidate_run_is_scored_against_this_run_block_averaged_onto_its_grid(tmp_path):
    """A 16^2 run and an 8^2 candidate of one vortex (``write_kinet_taylor_green``, the coarse one
    1% too strong), read with ``box``: :meth:`predictions` opens the candidate beside the file with
    the same options, the rows are labelled with its resolution, and through the pipeline on the
    candidate's 8^2 grid its ``rmse`` is the rms of the candidate minus the run averaged over 2 x 2
    blocks, computed here (to 1e-12). On the run's own grid the pair is refused, and without a
    candidate there is none."""
    write_kinet_taylor_green(tmp_path / "N16.h5", 16)
    write_kinet_taylor_green(tmp_path / "N8.h5", 8, amplitude_error=0.01)
    reference = KinetRawTrajectory(tmp_path / "N16.h5", box=2 * np.pi, candidate="N8.h5")
    candidate = reference.predictions()
    assert candidate.source == str(tmp_path / "N8.h5") and candidate.grid.shape == (8, 8)
    assert reference.frame_columns(2) == {"param_resolution": 8, "lead_step": 2,
                                          "lead_time": reference.times[2]}
    with KinetRawTrajectory(tmp_path / "N16.h5") as alone:
        assert alone.predictions() is None and alone.frame_columns(2) == {}

    rows = run(reference, [metric_registry.get("rmse")], build_ladder({}), fields=["velocity"],
               dataset=DatasetInfo(name="pair"), analysis_resolution=8, prediction=candidate).rows
    scored = rows[rows["lead_step"].notna() & (rows["level"] > 0)].sort_values("frame_index")
    expected = []
    for t in range(N_FRAMES):
        fine = reference.frame(t, ["velocity"])["velocity"]
        block = fine.reshape(2, 8, 2, 8, 2).mean(axis=(2, 4))
        expected.append(np.sqrt(np.mean((candidate.frame(t, ["velocity"])["velocity"] - block)**2)))
    assert scored["value"].to_numpy() == pytest.approx(expected, rel=1e-12)
    assert (scored["param_resolution"] == 8).all()
    with pytest.raises(ValueError, match="share its grid"):
        run(reference, [metric_registry.get("rmse")], build_ladder({}), fields=["velocity"],
            dataset=DatasetInfo(name="pair"), prediction=candidate)


def test_under_cell_a_coarser_candidate_spans_the_runs_domain_on_its_clock(tmp_path):
    """A 16 x 8 run whose frames are solver steps 0, 2, ..., 8 and an 8 x 4 candidate whose frames
    are steps 0, 1, ..., 4, read with ``cell``: the candidate's cell and step are twice the run's,
    so its spacing is twice the run's, its clock equals the run's, its velocity keeps its lattice
    values and its vorticity is divided by its own cell. Through the pipeline on the candidate's
    grid its ``rmse`` is the rms of the candidate minus the run averaged over 2 x 2 blocks
    (1e-12). Without ``cell`` the two runs' spacings differ and the pair is refused."""
    write_kinet_raw(tmp_path / "fine.h5")
    with h5py.File(tmp_path / "fine.h5", "r+") as f:
        f["time_index"][:] = 2 * np.arange(N_FRAMES)
    write_kinet_raw(tmp_path / "coarse.h5", shape=(8, 4))
    reference = KinetRawTrajectory(tmp_path / "fine.h5", cell=1.0, candidate="coarse.h5")
    candidate = reference.predictions()
    with KinetRawTrajectory(tmp_path / "coarse.h5") as plain:
        assert candidate.grid.spacing == (2.0, 2.0) and reference.grid.spacing == (1.0, 1.0)
        assert np.array_equal(candidate.times, reference.times)
        assert candidate.times.tolist() == (2.0 * np.arange(N_FRAMES)).tolist()
        assert np.array_equal(candidate.frame(3, ["velocity"])["velocity"],
                              plain.frame(3, ["velocity"])["velocity"])
        assert np.array_equal(candidate.frame(3, ["vorticity"])["vorticity"],
                              plain.frame(3, ["vorticity"])["vorticity"] / 2.0)
    rows = run(reference, [metric_registry.get("rmse")], build_ladder({}), fields=["velocity"],
               dataset=DatasetInfo(name="pair"), analysis_resolution=8, prediction=candidate).rows
    scored = rows[rows["lead_step"].notna() & (rows["level"] > 0)].sort_values("frame_index")
    expected = [np.sqrt(np.mean((candidate.frame(t, ["velocity"])["velocity"] - reference.frame(
        t, ["velocity"])["velocity"].reshape(2, 8, 2, 4, 2).mean(axis=(2, 4)))**2))
        for t in range(N_FRAMES)]
    assert scored["value"].to_numpy() == pytest.approx(expected, rel=1e-12)
    assert (scored["param_resolution"] == 8).all()
    with KinetRawTrajectory(tmp_path / "fine.h5", candidate="coarse.h5") as lattice:
        with pytest.raises(ValueError, match="share its grid"):
            run(lattice, [metric_registry.get("rmse")], build_ladder({}), fields=["velocity"],
                dataset=DatasetInfo(name="pair"), analysis_resolution=8,
                prediction=lattice.predictions())


def test_window_keeps_a_block_of_cells_at_the_runs_coordinates(kinet_file):
    """``window`` reads cells ``[start, stop)`` of each axis: the frame is the plain frame's block,
    the grid's shape is the window's and its origin the window's first cell, the declared
    boundary is the configuration's; a window outside the grid or empty is refused."""
    window = [[2, 10], [1, 7]]
    with KinetRawTrajectory(kinet_file) as plain, \
            KinetRawTrajectory(kinet_file, window=window, cell=0.5,
                               boundary=["neumann", "neumann"]) as cut:
        assert cut.grid.shape == (8, 6) and cut.grid.boundary == ("neumann", "neumann")
        assert cut.grid.origin == (2 * 0.5, 1 * 0.5) and cut.grid.spacing == (0.5, 0.5)
        for name in ("density", "velocity"):
            assert np.array_equal(cut.frame(3, [name])[name], plain.frame(3, [name])[name][
                :, 2:10, 1:7])
    for bad in ([[0, 17], [0, 8]], [[4, 4], [0, 8]], [[0, 16]], [[-1, 4], [0, 8]]):
        with pytest.raises(ValueError, match="window="):
            KinetRawTrajectory(kinet_file, window=bad)


def test_members_assemble_an_ensemble_around_a_truth_from_one_folder(tmp_path):
    """Four runs of one start, told apart by a density offset equal to their index: with
    ``members`` the file opened is the truth, the other three are the members in name order and
    the truth is not among them, and through the pipeline every row records the lead time (time
    since frame 0) and no ``lead_step``; an ensemble metric reads all three members, a
    deterministic one scores their mean. A member on another clock, a glob matching one other
    file, and members beside a candidate are refused."""
    for i in range(4):
        write_kinet_raw(tmp_path / f"member_{i:02d}.h5")
        with h5py.File(tmp_path / f"member_{i:02d}.h5", "r+") as f:
            f["density"][...] += float(i)
    truth = KinetRawTrajectory(tmp_path / "member_02.h5", members="member_*.h5")
    assert truth.is_ensemble and not KinetRawTrajectory(tmp_path / "member_00.h5").is_ensemble
    with KinetRawTrajectory(tmp_path / "member_00.h5") as zero:
        frame, base = truth.frame(3, ["density"]), zero.frame(3, ["density"])["density"]
    assert np.array_equal(frame["density"], base + 2.0)
    assert np.array_equal(frame.members["density"], np.stack([base + i for i in (0.0, 1.0, 3.0)]))
    # Recomputing the derived fields keeps the members, each from its own velocity.
    zero = RecomputingTrajectory(KinetRawTrajectory(tmp_path / "member_00.h5"))
    own = zero.frame(3, ["velocity", "vorticity"])["vorticity"]
    zero.close()
    stored = truth.frame(3, ["velocity", "vorticity"]).members["vorticity"]
    recomputed = RecomputingTrajectory(truth).frame(3, ["velocity", "vorticity"]).members
    assert np.array_equal(recomputed["vorticity"][0], own)
    assert recomputed["vorticity"].shape == stored.shape
    assert not np.array_equal(recomputed["vorticity"], stored)

    rows = run(truth, [metric_registry.get("crps"), metric_registry.get("mse")], build_ladder({}),
               fields=["density"], dataset=DatasetInfo(name="ensemble")).rows
    assert rows["lead_time"].to_numpy() == pytest.approx(
        truth.times[rows["frame_index"].to_numpy()] - truth.times[0], abs=0)
    assert rows["lead_step"].isna().all()
    assert (rows.loc[rows["metric"] == "crps", "n_members"] == 3).all()
    clean = rows[(rows["metric"] == "mse") & (rows["level"] == 0)].set_index("frame_index")
    assert clean.loc[3, "value"] == pytest.approx(np.mean((base + 2.0 - (base + 4.0 / 3.0))**2))
    truth.close()

    with pytest.raises(ValueError, match="matches 1 other"):
        KinetRawTrajectory(tmp_path / "member_02.h5", members="member_0[23].h5")
    with pytest.raises(ValueError, match="no candidate"):
        KinetRawTrajectory(tmp_path / "member_02.h5", members="member_*.h5",
                           candidate="member_00.h5")
    write_kinet_raw(tmp_path / "member_04.h5", times=np.arange(N_FRAMES) * 0.5)
    with pytest.raises(ValueError, match=r"grid, clock and fields: \[.*member_04"):
        KinetRawTrajectory(tmp_path / "member_02.h5", members="member_*.h5")


#: The job's comparison of the shear-layer refinement runs (``compare_shear_layer_refinement.py``).
SHEAR_LAYER = REPO / ("docs/datasets/logs/kinet_runs/_scripts_batch2/"
                      "shear_layer_refinement_differences.json")


@pytest.mark.data
@pytest.mark.parametrize("cells", ["256", "128"])
def test_the_shear_layer_refinement_reproduces_the_jobs_differences(cells):
    """On the evaluated part (every 10th frame from 10) of ``kinet_shear_layer_refinement``, the
    ``rmse`` of the candidate against the 512^2 run, through the pipeline with derived fields
    recomputed as ``evaluate.py`` does, is the job's E_N = RMS over cells of the difference from
    the block-averaged 512^2 run: on density as it is, on velocity times sqrt(2) u_l (the metric
    averages the two channels; ``box`` divides by u_l) and on vorticity, the curl of the
    block-averaged velocity on both sides, times u_l (measured to 2e-14 relative; asserted
    1e-9)."""
    job = build_job(compose_config("dataset=kinet_shear_layer_refinement",
                                   f"dataset.trajectory={cells}", "paths.data_url=null"))
    reference = open_trajectory(job.dataset, job.paths)
    speed = reference.meta["source_attrs"]["normalization_plan"]["lattice"]["u_l"]
    rows = run(RecomputingTrajectory(reference), [metric_registry.get("rmse")], build_ladder({}),
               fields=job.dataset.fields, selection=job.dataset.time,
               dataset=DatasetInfo(name=job.dataset.name),
               analysis_resolution=job.analysis_grid.resolution,
               prediction=RecomputingTrajectory(reference.predictions())).rows
    scored = rows[rows["lead_step"].notna() & (rows["level"] > 0)]
    expected = json.loads(SHEAR_LAYER.read_text())["fields"]
    for field, factor in (("density", 1.0), ("velocity", np.sqrt(2) * speed),
                          ("vorticity", speed)):
        got = scored[scored["field"] == field].sort_values("frame_index")
        assert got["frame_index"].tolist() == list(range(10, 101, 10))
        want = np.array(expected[field][f"E_{cells}"])[got["frame_index"].to_numpy()]
        assert got["value"].to_numpy() * factor == pytest.approx(want, rel=1e-9)


#: The ensemble job's table (``ensemble_checks.py ensemble``), over the 17 runs of each start.
ENSEMBLE = REPO / "docs/datasets/logs/kinet_runs/shear_layer_ensemble/ensemble_results.txt"


@pytest.mark.data
def test_the_shear_layer_ensemble_reproduces_the_jobs_spread_and_single_truth_ratios():
    """``kinet_shear_layer_ensemble``'s truth and 16 members are the job's 17 runs of a start, so
    from the reader's frames: the velocity spread, sqrt of the mean member variance (ddof 1) over
    cells and channels, relative to lead 0 at start 2000 is the job's at leads 1000 to 5000 (three
    significant figures, as printed); over the 51 single truths of the three starts at lead 5000
    the ratio of each one's squared error from the mean of the other 16 to their mean variance
    spans the job's range; pooled over the 17 truths of a start it is 17/16, the identity that
    makes the pooled check vacuous; and the fixed truth's own ratio there is 0.5807 at start 2000
    (recorded in docs/datasets/logs/reynolds_ladder_2d.md)."""
    text = ENSEMBLE.read_text()
    printed = dict(re.findall(r"(\d+):([\d.e+-]+)\(", re.search(
        r"start_02000 velocity +(.*)", text).group(1)))
    low, high = map(float, re.search(r"velocity +lead +5000: .*\{([\d.]+)-([\d.]+)\}",
                                     text).groups())
    ratios, own = [], {}
    for start in ("start_02000", "start_05000", "start_08000"):
        job = build_job(compose_config("dataset=kinet_shear_layer_ensemble",
                                       f"dataset.trajectory={start}", "paths.data_url=null"))
        with open_trajectory(job.dataset, job.paths) as ensemble:
            runs = {}
            for frame in (0, 100, 200, 400, 500):
                read = ensemble.frame(frame, ["velocity"])
                runs[10 * frame] = np.concatenate([read["velocity"][None],
                                                   read.members["velocity"]])
        if start == "start_02000":
            spread = {lead: np.sqrt(np.mean(np.var(x, 0, ddof=1)) * 2) for lead, x in runs.items()}
            for lead in (1000, 2000, 4000, 5000):
                assert spread[lead] / spread[0] == pytest.approx(float(printed[str(lead)]),
                                                                 rel=6e-3)
        x = runs[5000]
        others = (x.sum(0)[None] - x) / (len(x) - 1)
        variance = ((x**2).sum(0)[None] - x**2 - (len(x) - 1) * others**2) / (len(x) - 2)
        error = np.mean((x - others)**2, axis=(1, 2, 3))
        ratios += list(error / np.mean(variance, axis=(1, 2, 3)))
        own[start] = ratios[-len(x)]
        assert error.mean() / np.mean(variance) == pytest.approx(17 / 16, rel=1e-9)
    assert (round(min(ratios), 3), round(max(ratios), 3)) == (low, high)
    assert own["start_02000"] == pytest.approx(0.5807, abs=1e-4)


#: The candidate job's distances (``candidates_checks.py``), per realisation, kind and frame.
CANDIDATES = REPO / "docs/datasets/logs/kinet_runs/isotropic_candidates/candidates_checks.json"


@pytest.mark.data
@pytest.mark.parametrize("reynolds,kind,cells", [
    ("25k", "grid64", 64), ("25k", "grid128", 128), ("25k", "re0.5", 256), ("25k", "bgk", 256),
    ("50k", "control", 256)])
def test_the_isotropic_candidates_reproduce_the_jobs_distances(reynolds, kind, cells):
    """On the evaluated frames of ``kinet_hit_re<Re>_candidates`` (frames 3 to 11, the
    realisation's frames 150 to 550), the candidate scored through the pipeline on its own grid,
    derived fields recomputed as ``evaluate.py`` does, is at the job's relative L2 distances from
    the realisation block-averaged onto that grid: ``nrmse`` on vorticity is d_w, and ``mse`` on
    velocity times the two channels and the cells, over the reference's squared norm, is d_u
    squared (the job printed five significant figures; asserted 1e-4)."""
    job = build_job(compose_config(f"dataset=kinet_hit_re{reynolds}_candidates",
                                   f"dataset.reader.candidate={kind}.h5",
                                   f"dataset.analysis_resolution={cells}", "paths.data_url=null"))
    reference = open_trajectory(job.dataset, job.paths)
    rows = run(RecomputingTrajectory(reference),
               [metric_registry.get("mse"), metric_registry.get("nrmse")], build_ladder({}),
               fields=["velocity", "vorticity"], selection=job.dataset.time,
               dataset=DatasetInfo(name=job.dataset.name), analysis_resolution=cells,
               prediction=RecomputingTrajectory(reference.predictions())).rows
    scored = rows[rows["lead_step"].notna() & (rows["level"] > 0)].set_index(
        ["metric", "field", "frame_index"])["value"]
    expected = json.loads(CANDIDATES.read_text())["Re"][reynolds][job.dataset.trajectory][kind]
    factor = 256 // cells
    for t in range(3, 12):
        want = expected["series"][str(50 * t)]
        fine = reference.frame(t, ["velocity"])["velocity"]
        norm = np.sum(fine.reshape(2, cells, factor, cells, factor).mean(axis=(2, 4))**2)
        assert np.sqrt(scored["mse", "velocity", t] * 2 * cells**2 / norm) == pytest.approx(
            want["d_u"], rel=1e-4)
        assert scored["nrmse", "vorticity", t] == pytest.approx(want["d_w"], rel=1e-4)
    assert (rows.loc[rows["lead_step"].notna(), "param_resolution"] == cells).all()


#: The job's check of the forced run, one row per 1000 steps (``check_forced.py``).
FORCED_CHECK = REPO / "docs/datasets/logs/kinet_runs/forced_turbulence_2d/checks/final_220000.txt"


@pytest.mark.data
def test_the_forced_run_reproduces_the_jobs_check_on_its_evaluated_frames():
    """On every evaluated frame of ``kinet_forced_re40k`` (steps 140 000 to 220 000, 4000 apart,
    read in solver steps), ``kinetic_energy`` and ``enstrophy`` through the pipeline on the native
    grid, vorticity recomputed spectrally as ``evaluate.py`` does, and the density's extremes are
    the job's E, Z, rho_min and rho_max at that step. The job printed six significant figures
    and removed the mean velocity, which is 6e-6 here, so 1e-5 relative bounds both."""
    job = build_job(compose_config("dataset=kinet_forced_re40k", "paths.data_url=null"))
    check = {int(row[0]): row for row in (
        [float(v) for v in line.split()] for line in FORCED_CHECK.read_text().splitlines()
        if re.fullmatch(r"\d+( \S+){9}", line))}
    trajectory = open_trajectory(job.dataset, job.paths)
    frames = job.dataset.time.resolve(len(trajectory))
    assert len(frames) == 21 and trajectory.grid.shape == (1024, 1024)
    rows = run(RecomputingTrajectory(trajectory),
               [metric_registry.get("kinetic_energy"), metric_registry.get("enstrophy")],
               build_ladder({}), fields=["velocity", "vorticity"], selection=job.dataset.time,
               dataset=DatasetInfo(name=job.dataset.name), analysis_resolution=None).rows
    value = rows[rows["level"] == 0].set_index(["metric", "frame_index"])["value"]
    for t in frames:
        step = int(trajectory.times[t])
        assert step == 4000 * t and 140_000 <= step <= 220_000
        _, energy, enstrophy, *_, rho_min, rho_max = check[step][:7]
        assert value["kinetic_energy", t] == pytest.approx(energy, rel=1e-5)
        assert value["enstrophy", t] == pytest.approx(enstrophy, rel=1e-5)
        density = trajectory.frame(int(t), ["density"])["density"]
        assert (density.min(), density.max()) == (pytest.approx(rho_min, abs=6e-6),
                                                  pytest.approx(rho_max, abs=6e-6))


#: The cylinder of the supersonic run: centre and radius in nodes
#: (docs/datasets/supersonic_cylinder.md, from the rollout's solid mask).
CYLINDER_CENTRE, CYLINDER_RADIUS = (166.5, 150.5), 20.0


@pytest.mark.data
def test_the_cylinder_window_holds_the_bow_shock_and_none_of_the_body():
    """On the evaluated frames of ``kinet_supersonic_cylinder`` (the window x < 144, 6 <= y < 294
    upstream of the body), the shock detector of ``shock_set_distance`` flags 40 to 60 cells, all on the bow
    shock's normal part (x 105 to 112, symmetric about the centre line within two cells) and every
    one at least 30 nodes from the cylinder's outline, so none on the body (on the whole domain
    178 of about 230 flagged nodes lie within two nodes of it)."""
    job = build_job(compose_config("dataset=kinet_supersonic_cylinder", "paths.data_url=null"))
    with open_trajectory(job.dataset, job.paths) as cylinder:
        assert cylinder.grid.shape == (144, 288) and cylinder.grid.origin == (0.0, 6.0)
        for t in job.dataset.time.resolve(len(cylinder)):
            flagged = shock_mask(cylinder.frame(int(t), ["pressure"])["pressure"][0])
            x, y = np.nonzero(flagged)
            y = y + 6  # the run's node index
            assert 40 <= len(x) <= 60 and x.min() >= 105 and x.max() <= 112
            assert abs((y.min() + y.max()) / 2 - CYLINDER_CENTRE[1]) <= 2
            outline = np.hypot(x - CYLINDER_CENTRE[0], y - CYLINDER_CENTRE[1]) - CYLINDER_RADIUS
            assert outline.min() >= 30


#: The incident shock's foot measured by ``check_dmr.py`` on the coarse-grained 960 x 240 run
#: (``check_dmr_N240.txt`` under docs/datasets/logs/kinet_runs/shocks_2d/checks/), by frame of the
#: converted file and row index (rows 72, 84, 96, 108 are y = 0.6042, 0.7042, 0.8042, 0.9042).
DMR_FRONT = {2: {72: 2.0876, 84: 2.1441, 96: 2.2003, 108: 2.2582},
             3: {72: 2.8169, 84: 2.8737, 96: 2.9314, 108: 2.9884}}


@pytest.mark.data
def test_the_double_mach_window_reproduces_the_incident_shock_and_leaves_out_still_gas():
    """``kinet_double_mach_reflection`` reads the window x < 3.2 of the 960 x 240 run block-averaged
    to 480 x 120, in the case's units (cells 1/120, the clock the physical time), at the saved
    frames nearest 0.0708 and 0.1368. On each checked row the right-most crossing of the density
    level 4.7, between the pre-shock 1.4 and the post-shock 8, interpolated between cell centres as
    ``check_dmr.py`` does, is its measured foot of the incident shock (given to four decimals). The
    96 columns left out hold the undisturbed pre-shock state (1.4, 0, 0, 1) at every kept frame
    (measured within 2.3e-16)."""
    job = build_job(compose_config("dataset=kinet_double_mach_reflection", "paths.data_url=null"))
    with open_trajectory(job.dataset, job.paths) as run, \
            KinetRawTrajectory(job.dataset.path, include_redundant=True) as whole:
        assert run.grid.shape == (384, 120) and run.grid.spacing == pytest.approx((1 / 120,) * 2)
        assert run.grid.boundary == ("neumann", "neumann")
        assert run.times[1:] == pytest.approx([0.070835, 0.136744, 0.2], abs=5e-7)
        x = (np.arange(384) + 0.5) / 120
        for t, rows in DMR_FRONT.items():
            density = run.frame(t, ["density"])["density"][0]
            for j, expected in rows.items():
                above = density[:, j] >= 4.7
                i = np.flatnonzero(above[:-1] & ~above[1:])[-1]
                foot = x[i] + (density[i, j] - 4.7) / (density[i, j] - density[i + 1, j]) / 120
                assert foot == pytest.approx(expected, abs=6e-5), (t, j)
        for t in range(1, len(whole)):
            beyond = whole.frame(t, ["density", "velocity", "pressure"])
            for name, state in (("density", 1.4), ("velocity", 0.0), ("pressure", 1.0)):
                assert np.abs(beyond[name][:, 384:] - state).max() < 1e-7, (t, name)


def test_iter_frames_is_ascending(traj):
    idx = [f.index for f in traj.iter_frames(["density"], TimeSelection(start=1))]
    assert idx == sorted(idx) == [1, 2, 3, 4]


# --- the time-axis-slicing guard ---------------------------------------------------


def test_frame_rejects_non_integer_index(traj):
    for bad in (slice(0, 2), 1.0, [0, 1], np.array([0, 1])):
        with pytest.raises(TypeError, match="must be an int"):
            traj.frame(bad, ["density"])


def test_never_slices_the_time_axis(layout, traj, monkeypatch):
    """Record every h5py key used and assert the time position is always an int.

    This is the only guard against a one-character edit turning a 1-second read into a
    multi-gigabyte one, and it is invisible to any correctness test.
    """
    _, _, _, time_position = layout
    seen: list[tuple] = []
    original = h5py.Dataset.__getitem__

    def spy(self, key):
        seen.append(key if isinstance(key, tuple) else (key,))
        return original(self, key)

    monkeypatch.setattr(h5py.Dataset, "__getitem__", spy)
    for _ in traj.iter_frames(traj.fields):
        pass

    time_keys = [k[time_position] for k in seen if len(k) > time_position]
    assert time_keys, "no multi-axis reads recorded; the spy did not fire"
    for k in time_keys:
        assert isinstance(k, (int, np.integer)), (
            f"time axis indexed with {k!r} ({type(k).__name__}); must be a plain int"
        )


def test_memory_stays_bounded(traj):
    """Peak allocation over a full pass must stay near one frame, not the whole file."""
    tracemalloc.start()
    for _ in traj.iter_frames(["density", "velocity", "vorticity"]):
        pass
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    one_frame = 4 * np.prod(SHAPE) * 8  # density + 2 velocity + vorticity, float64
    assert peak < 50 * one_frame, f"peak {peak} B is far above one frame ({one_frame} B)"


# --- provenance ---------------------------------------------------------------------


def test_meta_carries_provenance(layout, traj):
    _, _, cls, _ = layout
    meta = traj.meta
    assert meta["format"] == cls.FORMAT
    assert meta["n_frames"] == N_FRAMES
    assert meta["path"].endswith(".h5")
    attrs = meta["source_attrs"]
    if cls is KinetRawTrajectory:
        # JSON-string attributes must come back parsed, not as raw strings.
        assert attrs["discretization"]["spatial"]["grid"] == list(SHAPE)
    else:
        # NumPy scalar attributes must come back as Python scalars.
        assert attrs["n_spatial_dims"] == 2 and type(attrs["n_spatial_dims"]) is int


def test_reader_is_registered(layout):
    _, _, cls, _ = layout
    assert READERS[cls.FORMAT] is cls
    assert issubclass(cls, Trajectory)


def test_close_is_idempotent(layout):
    _, path, cls, _ = layout
    t = cls(path)
    t.close()
    t.close()


def test_well_rejects_an_unexpected_spatial_order(tmp_path):
    """A different axis order would need a transpose, so it must fail rather than guess."""
    path = write_well(tmp_path / "swapped.h5")
    with h5py.File(path, "r+") as f:
        f["dimensions"].attrs["spatial_dims"] = ["y", "x"]
    with pytest.raises(ValueError, match="spatial_dims"):
        WellTrajectory(path)


@pytest.mark.parametrize("bc_type", ["WALL", "OPEN"])
def test_well_reads_a_wall_or_open_axis_as_neumann(tmp_path, bc_type):
    """Both non-periodic types the published 2D sets use extend evenly; the periodic axis and
    the fields are unaffected."""
    with WellTrajectory(write_well(tmp_path / "f.h5", bc_types=("PERIODIC", bc_type))) as traj:
        assert traj.grid.boundary == ("periodic", "neumann")
        assert traj.frame(0, ["velocity"])["velocity"].shape == (2, *SHAPE)


@pytest.mark.parametrize("bc_type", ["SYMMETRIC", None])
def test_well_refuses_an_unmapped_or_undeclared_axis(tmp_path, bc_type):
    """A type the mapping lacks, or an axis no group names, fails rather than being guessed."""
    with pytest.raises(ValueError, match="BOUNDARY_MAP"):
        WellTrajectory(write_well(tmp_path / "f.h5", bc_types=("PERIODIC", bc_type)))


def test_well_coordinates_spanning_the_domain_give_n_cells(tmp_path):
    """The fixture's coordinates are 0, 1, ..., N-1: a unit step by default, and N cells over
    the span N - 1 when they are declared to run from bound to bound."""
    path = write_well(tmp_path / "f.h5")
    with WellTrajectory(path) as traj:
        assert traj.grid.spacing == (1.0, 1.0)
    with WellTrajectory(path, coordinates_span_domain=True) as traj:
        assert traj.grid.spacing == pytest.approx(tuple((n - 1) / n for n in SHAPE), rel=1e-12)


def test_well_refuses_a_non_uniform_coordinate(tmp_path):
    """GridSpec holds one spacing per axis, so stretched coordinates cannot be represented."""
    path = write_well(tmp_path / "f.h5")
    with h5py.File(path, "r+") as f:
        del f["dimensions/y"]
        f["dimensions"].create_dataset("y", data=np.arange(SHAPE[1], dtype=np.float64) ** 2)
    with pytest.raises(ValueError, match="not uniformly spaced"):
        WellTrajectory(path)


# --- converting kinet's grouped layout ------------------------------------------------


def _as_older_rollout(f: h5py.File) -> None:
    """Rewrite a grouped fixture as kinet wrote it before ``pressure_convention`` and
    ``time_convection`` existed (the Sod runs): no convention, the clock in ``time/time``."""
    del f.attrs["pressure_convention"]
    for group in ("time", "initial_conditions/time"):
        f[f"{group}/time"][...] = f[f"{group}/time_convection"][...]
        del f[f"{group}/time_convection"]


@pytest.mark.parametrize("older", [False, True], ids=["current", "older"])
def test_a_converted_grouped_rollout_is_the_flat_file_it_was_built_from(older, tmp_path):
    """The grouped fixture holds the flat fixture's frames, its initial condition apart, NaN in
    the unsaved slots and an off-cadence step 1; converting it must give back every frame and
    the clock exactly, the solver step of every frame, and the source's identity. An older
    rollout's clock is its ``time/time``, and its pressure, which satisfies ``p = rho T``, is
    carried as absolute."""
    grouped = write_kinet_grouped(tmp_path / "grouped.h5", save_every=3)
    if older:
        with h5py.File(grouped, "r+") as f:
            _as_older_rollout(f)
    converted = convert_kinet_grouped(grouped, tmp_path / "out" / "converted.h5")
    with KinetRawTrajectory(tmp_path / "grouped_flat.h5", include_redundant=True) as want, \
            KinetRawTrajectory(converted, include_redundant=True) as got:
        assert got.fields == ("density", "velocity", "vorticity", "pressure"), "the populations "\
            "are not observables, and an absolute pressure is carried"
        assert np.array_equal(got.times, want.times)
        for t in range(len(want)):
            a, b = want.frame(t, got.fields), got.frame(t, got.fields)
            for name in got.fields:
                assert np.array_equal(a[name], b[name]), f"{name} differs at frame {t}"
        attrs = got.meta["source_attrs"]
        assert attrs["identity_key"] == "0f1x7e"
        assert attrs["converted_from"] == str(grouped.resolve())
        assert attrs["discretization"]["temporal"]["resolution"] == 3.0
    with h5py.File(converted, "r") as f:
        assert f["time_index"][:].tolist() == [0, 3, 6, 9, 12]
    with pytest.raises(FileExistsError):
        convert_kinet_grouped(grouped, converted)


def test_every_keeps_the_initial_condition_and_every_nth_frame_after_it(tmp_path):
    """``every=2`` on the grouped fixture (frames 0 to 4 at steps 0, 3, ..., 12) keeps frames 0, 2
    and 4 of the flat fixture, values and clock alike, at steps 0, 6, 12, with the temporal grid
    and resolution counting the frames kept; a value that does not divide the four frames after
    the initial condition is refused and leaves nothing behind."""
    grouped = write_kinet_grouped(tmp_path / "grouped.h5", save_every=3)
    converted = convert_kinet_grouped(grouped, tmp_path / "converted.h5", every=2)
    with KinetRawTrajectory(tmp_path / "grouped_flat.h5") as want, \
            KinetRawTrajectory(converted) as got:
        assert np.array_equal(got.times, want.times[::2])
        for t in range(len(got)):
            a, b = want.frame(2 * t, got.fields), got.frame(t, got.fields)
            for name in got.fields:
                assert np.array_equal(a[name], b[name]), f"{name} differs at frame {t}"
        temporal = got.meta["source_attrs"]["discretization"]["temporal"]
        assert (temporal["grid"], temporal["resolution"]) == (2, 6.0)
    with h5py.File(converted, "r") as f:
        assert f["time_index"][:].tolist() == [0, 6, 12]
    for bad in (0, 3):
        with pytest.raises(ValueError, match="every="):
            convert_kinet_grouped(grouped, tmp_path / f"bad{bad}.h5", every=bad)
        assert not list(tmp_path.glob(f"bad{bad}.h5*"))


def test_an_adaptive_rollout_keeps_its_physical_clock_and_its_last_step(tmp_path):
    """A PonD rollout (``write_kinet_grouped(adaptive=True)``: an adaptive step, the last frame
    one step off the cadence, the physical time in ``time/time``) converts to the flat fixture's
    frames and clock, not ``time_convection``, at steps 0, 3, 6, 9, 11, with no temporal
    resolution; ``every=2`` keeps the last frame and every second before it, steps 0, 6, 11,
    though 2 does not divide the four frames. ``times`` keeps the frame nearest each time, a
    frame two times select only once, and is refused on a fixed-step run."""
    grouped = write_kinet_grouped(tmp_path / "grouped.h5", save_every=3, adaptive=True)
    for every, frames, steps in ((1, [0, 1, 2, 3, 4], [0, 3, 6, 9, 11]), (2, [0, 2, 4], [0, 6, 11])):
        converted = convert_kinet_grouped(grouped, tmp_path / f"every{every}.h5", every=every)
        with KinetRawTrajectory(tmp_path / "grouped_flat.h5") as want, \
                KinetRawTrajectory(converted) as got:
            assert np.array_equal(got.times, want.times[frames])
            for t, source in enumerate(frames):
                a, b = want.frame(source, got.fields), got.frame(t, got.fields)
                assert all(np.array_equal(a[name], b[name]) for name in got.fields), t
            temporal = got.meta["source_attrs"]["discretization"]["temporal"]
            assert temporal["grid"] == len(frames) - 1 and "resolution" not in temporal
        with h5py.File(converted, "r") as f:
            assert f["time_index"][:].tolist() == steps
            assert f["time"].attrs["source"] == "time"
    with KinetRawTrajectory(tmp_path / "grouped_flat.h5") as want:
        near = [want.times[2] * 1.01, want.times[3] * 0.99, want.times[3]]
        expected = want.times[[0, 2, 3]]
    with KinetRawTrajectory(convert_kinet_grouped(grouped, tmp_path / "times.h5",
                                                  times=near)) as got:
        assert np.array_equal(got.times, expected), "the frame nearest each time, once each"
    with pytest.raises(ValueError, match="times="):
        convert_kinet_grouped(write_kinet_grouped(tmp_path / "fixed.h5"), tmp_path / "no.h5",
                              times=near)


@pytest.mark.parametrize("change,match", [
    (lambda f: f.attrs.__setitem__("kinet_rollout_status", "running"), "complete"),
    (lambda f: f.attrs.__setitem__("pressure_convention", "gauge"), "pressure_convention"),
    (lambda f: [f[f"time/{n}"].__setitem__(4, 5.0) for n in ("time_index", "time_convection")],
     "evenly spaced"),
    (lambda f: f["time/time_index"].__setitem__(4, 5.0), "slot s - 1"),
    (lambda f: [_as_older_rollout(f), f["initial_conditions/observables/pressure"].__setitem__(
        Ellipsis, 0.0)], "pressure_convention"),
])
def test_a_grouped_rollout_that_cannot_be_converted_exactly_is_refused(change, match, tmp_path):
    """An unfinished run, an unknown pressure, a saved step off the cadence, a clock that
    disagrees with the steps, and an older rollout whose pressure is not rho T are refused, and
    nothing is left at the destination."""
    grouped = write_kinet_grouped(tmp_path / "grouped.h5")
    with h5py.File(grouped, "r+") as f:
        change(f)
    with pytest.raises(ValueError, match=match):
        convert_kinet_grouped(grouped, tmp_path / "converted.h5")
    assert not list(tmp_path.glob("converted.h5*"))


def test_a_gauge_pressure_is_not_converted(tmp_path):
    """The weakly compressible physics stores (rho - 1) c_s^2, which is not a pressure."""
    grouped = write_kinet_grouped(tmp_path / "grouped.h5",
                                  pressure_convention="fluctuation_referenced")
    with h5py.File(convert_kinet_grouped(grouped, tmp_path / "converted.h5"), "r") as f:
        assert "pressure" not in f and {"density", "velocity", "vorticity"} <= set(f)


# --- the abstraction validated against ground truth ----------------------------------


DATA_ROOT = "datasets/kinet/doubly_periodic/weakly_compressible_isoT_fluids/sys_Re-5e4_Ma-1en1"
RAW = f"{DATA_ROOT}/D2Q9_shape-256-256_T-10000_H-dc804f.h5"
WELL = f"{DATA_ROOT}/D2Q9_shape-256-256_T-10000_H-dc804f_well-format.h5"


@pytest.mark.data
def test_raw_and_well_readers_agree_on_the_same_simulation():
    """The same rollout in two containers must come back identical.

    This is what validates the whole data abstraction against ground truth rather than
    against a synthetic fixture. The Well file stores float32, so the tolerance is
    single-precision; the axis and channel conventions must match exactly.
    """
    for path in (RAW, WELL):
        if not Path(path).exists():
            pytest.skip(f"{path} not available")

    with KinetRawTrajectory(RAW) as raw, WellTrajectory(WELL) as well:
        assert raw.grid.shape == well.grid.shape
        assert raw.grid.dims == well.grid.dims
        assert raw.grid.spacing == pytest.approx(well.grid.spacing)
        np.testing.assert_allclose(raw.times[:50], well.times[:50], rtol=1e-12)

        shared = sorted(set(raw.fields) & set(well.fields))
        assert {"density", "velocity", "vorticity"} <= set(shared)
        for t in (1, 2500, 5000):
            a = raw.frame(t, shared)
            b = well.frame(t, shared)
            for name in shared:
                np.testing.assert_allclose(
                    a[name], b[name], rtol=1e-6, atol=1e-8,
                    err_msg=f"{name} differs at t={t} between the raw and Well readers",
                )


WELL_DATA = "datasets/well/datasets"
RADIATIVE = f"{WELL_DATA}/turbulent_radiative_layer_2D/data/test/turbulent_radiative_layer_tcool_0.32.hdf5"
CONVECTION = f"{WELL_DATA}/rayleigh_benard/data/test/rayleigh_benard_Rayleigh_1e6_Prandtl_1.hdf5"


@pytest.mark.data
def test_well_radiative_layer_reads_with_square_cells_and_an_open_y_axis():
    """128 x 384 on [-0.5, 0.5] x [-1, 2]: cells of 1/128 on both axes only when N cells span
    each domain (configs/dataset/well_radiative_layer_tcool0p32.yaml)."""
    if not Path(RADIATIVE).exists():
        pytest.skip(f"{RADIATIVE} not available")
    with WellTrajectory(RADIATIVE, include_redundant=True, coordinates_span_domain=True) as traj:
        assert traj.grid.shape == (128, 384)
        assert traj.grid.boundary == ("periodic", "neumann")
        assert traj.grid.spacing == pytest.approx((1 / 128, 1 / 128), rel=1e-6)
        assert set(traj.fields) == {"density", "pressure", "velocity"}
        for t in (0, 1):
            assert traj.frame(t, list(traj.fields))["velocity"].shape == (2, 128, 384)
        # The initial condition: the dense layer (density 100) below y = 0, the dilute one above.
        rho = traj.frame(0, ["density"])["density"][0]
        assert rho[:, 0].mean() == pytest.approx(100.0) and rho[:, -1].mean() == pytest.approx(1.0)


@pytest.mark.data
def test_well_rayleigh_benard_rows_are_not_on_its_uniform_y_coordinate():
    """The file's y array is uniform on [0, 1], but its rows lie on Gauss-Chebyshev nodes.

    The reader opens the file (periodic x, WALL y as neumann), but no option reads its grid
    correctly. Near a wall the mean buoyancy is linear in the true height (a conductive
    sublayer), and on the nodes y_j = (1 - cos(pi (j + 1/2) / N)) / 2 the height grows as
    (j + 1/2)^2, so the steps between the first rows grow as 1 : 2 : 3 : 4. On uniform rows they
    would be equal. dataset_specs/11_regime_data.md Sect. 3.3 has the flux check behind this.
    """
    if not Path(CONVECTION).exists():
        pytest.skip(f"{CONVECTION} not available")
    with WellTrajectory(CONVECTION) as traj:
        assert traj.grid.shape == (512, 128)
        assert traj.grid.boundary == ("periodic", "neumann")
        assert traj.fields == ("velocity",)  # buoyancy is unmapped, pressure redundant by default
        assert traj.frame(0, ["velocity"])["velocity"].shape == (2, 512, 128)
    with h5py.File(CONVECTION, "r") as f:
        profile = np.asarray(f["t0_fields/buoyancy"][1, 199], dtype=np.float64).mean(axis=0)
    steps = -np.diff(profile[:5])
    np.testing.assert_allclose(steps / steps[0], [1, 2, 3, 4], rtol=0.03)


HIT_GROUPED = ("datasets/neurde/hit_scaling/Re-25k_Ma-1en1_2d/004ae2/tiers/full/rollout.h5")
HIT_RAW = ("datasets/kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids/"
           "sys_Re-25k_Ma-1en1/004ae2.h5")
SOD = "datasets/kinet/sod/compressible_fluids/Pr-71en2_vuy-1.4_visc-1en4/D2Q9_shape-3001-5_T-1000_H-d17baf"


@pytest.mark.data
@pytest.mark.parametrize("grouped,flat,clock", [
    (HIT_GROUPED, HIT_RAW, "time_convection"),
    (f"{SOD}.h5", f"{SOD}_flat.h5", "time"),
], ids=["isotropic", "sod"])
def test_a_converted_rollout_matches_its_grouped_source(grouped, flat, clock):
    """Every frame of a converted trajectory (the Re 25k isotropic one; the gamma = 1.4 Sod run,
    an older rollout with its absolute pressure), read by the raw reader, is the grouped
    source's initial condition or its slot ``step - 1``, value for value, on its clock."""
    for path in (grouped, flat):
        if not Path(path).exists():
            pytest.skip(f"{path} not available")
    with h5py.File(grouped, "r") as src, KinetRawTrajectory(flat, include_redundant=True) as raw:
        steps = raw._file["time_index"][:].astype(int)
        assert steps[0] == 0 and len(raw) == len(steps) == 1001
        assert np.array_equal(raw.times[1:], src[f"time/{clock}"][steps[1:] - 1])
        for t, step in enumerate(steps):
            got = raw.frame(t, raw.fields)
            for name in raw.fields:
                want = (src[f"initial_conditions/observables/{name}"][0, :, 0] if t == 0
                        else src[f"observables/{name}"][0, :, step - 1])
                assert np.array_equal(got[name], want), f"{name} differs at step {step}"
