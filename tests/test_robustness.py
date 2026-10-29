"""Failure-mode tests: what the harness does when a run leaves the well-trodden path.

Each test guards a behaviour that was reproduced, either on the real 256^2 trajectory or
through the real pipeline on synthetic frames. Each one asks the same question the rest of
the suite asks -- *does a wrong number look wrong?* -- but on inputs the other tests do not
reach: a metric that is invariant to the operator the D = 1 anchor is built from, a metric
that improves as damage rises, an analysis grid that the configured ladder does not fit on.

The tests assert the *property*, never the current number, so they survive a change that
moves magnitudes.
"""

from __future__ import annotations

import logging
import subprocess
import sys

import numpy as np
import pytest

from fmeval import REPO
from fmeval import analysis as an
from fmeval.calibration import calibrate
from fmeval.data.base import Frame, GridSpec
from fmeval.data.synthetic_ensemble import SyntheticEnsembleTrajectory
from fmeval.io import RunFolder, write_config, write_results, write_run_meta
from fmeval.ladder import apply_severity_level, build_ladder
from fmeval.pipeline import DatasetInfo, MapRequest, _runnable_levels, run
from fmeval.report.driver import build_context, render
from metrics import registry as metric_registry
from tests.conftest import SyntheticTrajectory, make_frame

# --- the D = 1 anchor ------------------------------------------------------------------
#
# The anchor is built by translating the reference (`random_large_translation`). That is
# exact and cheap for a pointwise metric, and it is *empty* for any metric invariant to
# translation -- which is most of the position-tolerant family this project exists to
# develop: spectra (BD-1), two-point correlations (BD-2), increment PDFs (OT-5, PS-4).


def test_degeneracy_guard_fires_when_most_levels_are_round_off():
    """A metric whose anchor is round-off must be reported as having no dynamic range.

    ``normalisation`` compares the span with the largest value in the group, not the median:
    when most severity levels are round-off the median collapses to round-off with them, and
    a guard scaled by it compares noise against noise -- defeated in exactly the case it
    exists for.
    """
    # One axis with genuine response (a blur, which a spectral metric does see) and three
    # axes at the float64 noise floor (translation, the impostor, and the anchor -- all of
    # which preserve the amplitude spectrum exactly).
    df = make_frame(
        n_frames=6,
        axes={
            "gaussian_blur": [1e-1, 3e-1],
            "translate_x": [1.1e-16, 1.3e-16, 0.9e-16],
            "gaussian_impostor": [1.8e-16],
            "mean_field": [1.5e-16, 1.5e-16, 1.5e-16],
        },
    )
    norm = an.normalisation(df)
    row = norm.iloc[0]

    assert bool(row["degenerate"]), (
        f"span={row['span']:.3e} against a genuine response of "
        f"{df['value'].max():.3e} was not marked degenerate; the damage column is a "
        "ratio of round-off and will be read as a measurement"
    )


def test_damage_is_not_reported_against_an_anchor_the_metric_cannot_see():
    """Damage must be withheld when the anchor is indistinguishable from clean.

    Measured on the real trajectory (t = 5000..6000, vorticity) with a radially averaged
    energy-spectrum metric of the BD-1 family:

        clean value             0.0
        uncorrelated anchor     1.5e-16      <- the whole D = 1 scale
        gaussian_impostor       1.8e-16      -> reported damage 1.17
        translate_x = 4         1.3e-16      -> reported damage 0.86

    An impostor damage of 1.17 would say "worse than two unrelated fields" when the metric
    cannot separate any of them. Read by the rule AGENTS.md gives for the canary column, a
    colleague would conclude the spectral metric passes IN-4 -- the exact inversion the
    canary exists to prevent.

    What is reported in its place is the impostor's response relative to the largest ladder
    response (issues/037), about 1e-15 for a phase-blind metric, and only while the damage is
    withheld: it is never printed beside a usable damage.
    """
    df = make_frame(
        n_frames=6,
        axes={
            "gaussian_blur": [1e-1, 3e-1],
            "gaussian_impostor": [1.8e-16],
            "mean_field": [1.5e-16, 1.5e-16, 1.5e-16],
        },
    )
    norm = an.normalisation(df)
    row = an.probe_summary(df, norm).iloc[0]
    damage = float(row["gaussian_impostor_damage"])

    assert not np.isfinite(damage), (
        f"impostor damage reported as {damage:.3f} against an anchor of "
        f"{norm['value_anchor'].iloc[0]:.3e}, which is round-off. A damage score "
        "computed from an anchor the metric cannot see must be NaN, not a number."
    )
    assert row["gaussian_impostor_relative"] < 1e-12
    usable = make_frame(axes={"a": [2.0, 5.0, 8.0], "gaussian_impostor": [5.0],
                              "mean_field": [10.0, 10.0]})
    row = an.probe_summary(usable, an.normalisation(usable)).iloc[0]
    assert np.isnan(row["gaussian_impostor_relative"]), "never printed beside a usable damage"


# --- rank correlation ------------------------------------------------------------------


def test_rank_correlation_is_withheld_when_the_variation_is_round_off():
    """A rank correlation over values that differ only in the last ulp is not a signal.

    Reproduced end to end with ``evaluate.py metrics=[enstrophy]`` and a translation-only
    ladder on the dev trajectory. ``np.roll`` cannot change enstrophy, but it does change
    the pairwise-summation order inside ``np.mean``, so the severity levels differ by a
    relative 1.6e-16; ranked, they give ``rho_min = 0.707`` on ``translate_x`` -- a number
    that is entirely round-off, and would sit in the monotonicity heatmap next to genuine
    correlations, indistinguishable from them.

    The ``degenerate`` flag covers the *damage* column, not ``rho``, which is what the
    heatmap and the reference thresholds read.
    """
    # Values identical to within float64 round-off, ordered arbitrarily.
    df = make_frame(metric="enstrophy", field="vorticity", n_frames=8, reference=3.7,
                    axes={"translate_x": [3.7] * 4}, noise=3.7 * 2e-16)
    axes = an.summarise_axes(df, n_bootstrap=0)
    rho = float(axes.loc[axes["degradation"] == "translate_x", "rho"].iloc[0])

    assert not np.isfinite(rho), (
        f"rho={rho:.3f} reported for an axis whose values span a relative 2e-16. A "
        "correlation over round-off must be NaN, or it will be read as a real response."
    )


def test_rank_correlation_is_withheld_when_every_value_on_the_axis_is_round_off():
    """Round-off must be judged against the metric's scale, not the axis's own.

    Measured on ``results/comparison_1789632054`` (kinet_re5e4, 161 frames, grid 256):
    ``spectrum_l2`` cannot see a whole-cell translation, and on ``translate_x`` it returned
    medians of 1.3e-16 to 1.9e-16 at every severity level on every field -- while the same
    metric, in the same frames, reached 0.62 under ``gaussian_blur``. Judged against the
    axis's own largest value, which is itself round-off, that noise is measured against
    noise and ranked: ``rho`` reads 0.0 / 0.10 / -0.1 on density / velocity / vorticity,
    and -0.6 to -0.71 on ``translate_subpixel``, whose values are 1e-12. A correlation of
    -0.6 over values twelve orders below the metric's response reads as "gets better as the
    field is displaced".

    The guard test above is the relative case -- every value near 3.7, differing in the
    last bits. This one is the absolute case, where every value on the axis is near zero,
    and it needs the rest of the frame to tell it what zero means.
    """
    rng = np.random.default_rng(0)
    df = make_frame(
        n_frames=8,
        axes={
            "gaussian_blur": [1e-2, 1e-1, 6e-1],
            "translate_x": [1.5e-16, 1.5e-16, 1.5e-16, 1.5e-16],
        },
    )
    on_axis = df["degradation"] == "translate_x"
    df.loc[on_axis, "value"] *= 1.0 + rng.uniform(-0.5, 0.5, on_axis.sum())

    axes = an.summarise_axes(df, n_bootstrap=20)
    row = axes.loc[axes["degradation"] == "translate_x"].iloc[0]

    for column in ("rho", "rho_frame_min", "rho_pooled", "rho_ci_lo", "rho_ci_hi",
                   "monotone_fraction", "separability_auc_min",
                   "sensitivity_level", "saturation_level",
                   "elasticity", "severity_10", "severity_50", "severity_resolution"):
        assert not np.isfinite(float(row[column])), (
            f"{column}={float(row[column]):.3f} reported for an axis whose values are "
            "all ~1.5e-16 while the same metric reaches 0.6 on another axis of the same "
            "frames. That is a statistic computed over round-off."
        )
    assert row["response_shape"] == ""
    blur = axes.loc[axes["degradation"] == "gaussian_blur"].iloc[0]
    assert float(blur["rho"]) == pytest.approx(1.0), "the genuine axis must be untouched"
    assert float(blur["monotone_fraction"]) == pytest.approx(1.0)


def test_threshold_levels_are_withheld_when_the_anchor_span_is_round_off():
    """A tenth of a round-off span is not a detection threshold.

    Measured on ``comparison_1789632054``: ``spectrum_l2``'s unrelated-field anchor is
    1.6e-16, because the anchor is built from translations and the metric cannot see them.
    ``normalisation`` marks that span degenerate and withholds damage, and the threshold
    levels must be withheld with it: any genuine response clears a tenth of 1.6e-16, so the
    card would read "first strength detected: level 1" on every family and every field, a
    detection claim measured against nothing.
    """
    df = make_frame(
        n_frames=6,
        axes={
            "gaussian_blur": [1e-2, 1e-1, 6e-1],
            "mean_field": [1.5e-16, 1.6e-16, 1.4e-16],
        },
    )
    norm = an.normalisation(df)
    assert bool(norm["degenerate"].iloc[0])
    axes = an.summarise_axes(df, norm=norm, n_bootstrap=0)
    blur = axes.loc[axes["degradation"] == "gaussian_blur"].iloc[0]

    assert float(blur["rho"]) == pytest.approx(1.0), "ordering does not need the anchor"
    for column in ("sensitivity_level", "saturation_level"):
        assert not np.isfinite(float(blur[column])), (
            f"{column}={float(blur[column])} reported against an anchor span of "
            f"{float(norm['span'].iloc[0]):.1e}, which is round-off"
        )


def test_report_card_survives_an_all_nan_rank_correlation():
    """A metric constant on every ordinal axis must produce a card, not an exception.

    Every ordinal axis then has an undefined correlation -- which happens whenever a metric
    is exactly invariant to every operator in the ladder, e.g. a single-field invariant
    against a translation-only ladder -- and the worst axis cannot be picked with a plain
    ``groupby(...)['rho'].idxmin()``, which raises ``ValueError: Encountered all NA values``.

    A failure there would be fatal rather than cosmetic: ``build_context`` computes the card
    before any renderer runs, so it would take down the whole report rather than costing one
    figure, *after* the expensive evaluation has been paid for.
    """
    df = make_frame(metric="enstrophy", field="vorticity", n_frames=6, reference=1.0,
                    axes={"translate_x": [1.0] * 3, "mean_field": [1.0] * 2})
    norm = an.normalisation(df)
    axes = an.summarise_axes(df, norm=norm, n_bootstrap=0)
    probes = an.probe_summary(df, norm)

    card = an.report_card(axes, probes, norm)   # must not raise
    assert len(card) == 1
    assert not np.isfinite(card["rho_min"].iloc[0])


# --- direction ---------------------------------------------------------------------------


def test_a_similarity_metric_is_scored_in_its_own_direction():
    """A metric where *larger is better* must not be scored as non-monotone.

    Three statistics are one-sided, and each takes the metric's direction from
    ``analysis.response_direction`` rather than assuming damage makes the value rise:

    * the monotone fraction counts steps with ``diff(value) > 0``;
    * the adjacent-level AUC is a one-sided Mann-Whitney test;
    * the threshold level is the first level with ``median >= clean + f * span``.

    Scored as if it rose with damage, a synthetic axis that falls perfectly from 1.0 to 0.2
    -- the shape of any correlation-, SSIM- or skill-score-style metric -- measures:

        rho                    -1.0   (perfectly ordered, reported as anti-correlated)
        monotone_fraction       0.0   (it is monotone on every frame)
        separability_auc_min    0.0   (adjacent severity levels are perfectly separable)
        saturation_level        1.0   (fires at severity level 1, meaninglessly)

    Every one of those trips a configured threshold, so a correct metric would arrive in
    the report card flagged on three criteria at once.
    """
    df = make_frame(metric="similarity", field="v", n_frames=8, reference=1.0,
                    axes={"gaussian_blur": [0.8, 0.6, 0.4, 0.2], "mean_field": [0.0]})
    # A small per-frame offset on the ladder, so the ranks are well defined.
    df["value"] += np.where(df["degradation"] == "mean_field", 0.0, 0.001 * df["frame_index"])
    # No declared direction, as in a folder that predates the column, so it is measured from
    # the anchor: the case with nothing to lean on.
    df = df.drop(columns="higher_is_better")
    norm = an.normalisation(df)
    axes = an.summarise_axes(df, norm=norm, n_bootstrap=0)
    blur = axes[axes["degradation"] == "gaussian_blur"].iloc[0]

    assert blur["monotone_fraction"] == pytest.approx(1.0), (
        f"monotone_fraction={blur['monotone_fraction']} for an axis that is perfectly "
        "ordered on every frame, because the ordering test assumes the value rises"
    )
    assert blur["separability_auc_min"] >= 0.9, (
        f"separability_auc_min={blur['separability_auc_min']} for perfectly separated "
        "severity levels, because the Mann-Whitney alternative is hardcoded to 'greater'"
    )


# --- the degradation contract ------------------------------------------------------------


def test_whole_frame_degradation_receives_the_field_dict(temporary_degradation):
    """An operator declaring ``whole_frame=True`` receives the whole field dict.

    ``degradations/registry.py`` and AGENTS.md section 4 both say so. No shipped operator
    declares it, so this test is the only thing exercising it, and the operators that most
    need it are the physically interesting ones -- a Leray projection (issue 024), a rotation
    that must rotate velocity components (issue 015), a density-weighted remap (issue 016).
    Each would otherwise receive an array where it expected a dict, with a message pointing
    at numpy rather than at the declaration that was ignored.
    """

    @temporary_degradation(name="_probe_whole_frame", family="pointwise",
                           whole_frame=True)
    def _probe_whole_frame(fields, severity, *, ctx):
        """Returns its input unchanged; fails loudly if it is not a mapping."""
        assert isinstance(fields, dict), (
            f"declared whole_frame=True but received {type(fields).__name__}"
        )
        return dict(fields)

    frame = SyntheticTrajectory().frame(1, ["density"])
    # Built through build_ladder rather than the SeverityLevel constructor, so this test keeps
    # testing whole_frame rather than turning into a signature check whenever a field is
    # added to SeverityLevel.
    severity_level = build_ladder(
        {"probe": {"op": "_probe_whole_frame", "severities": [1.0]}},
        include_reference=False,
    )[0]

    applied = apply_severity_level(severity_level, frame, ["density"], seed=0)
    assert set(applied.fields) == {"density"}
    # The operator returned its input unchanged, so the harness must see that and say so
    # rather than counting the severity level as an experiment.
    assert "density" in applied.unchanged


# --- the analysis grid as a size knob ------------------------------------------------------
#
# `analysis_grid.resolution` is documented in CLAUDE.md and AGENTS.md as one of the two
# size knobs. Nothing checks the configured ladder against the grid it will run on.


@pytest.mark.parametrize("resolution", [32, 8])
def test_the_default_ladder_runs_at_every_analysis_resolution(resolution):
    """Turning down the analysis grid must not abort the run.

    The default ladder coarsens by up to 16, so at ``analysis_grid.resolution=8``
    ``coarsen`` at 16 cannot run: ``ValueError: factor 16 does not divide grid (8, 8)``.
    Raised inside the frame loop, that would name the operator but not the knob that caused
    it, after the I/O for a long trajectory had been paid. The severity is dropped with a
    warning instead (``test_a_severity_the_grid_cannot_support_is_still_dropped_with_a_warning``)
    and the rest of the ladder runs.
    """
    ladder = build_ladder(
        {"coarsen": {"severities": [2, 4, 8, 16]},
         "gaussian_blur": {"severities": [1.0, 2.0]}}
    )

    # 32x16 native: every configured coarsening factor fits at the native resolution, so
    # the only thing under test is what the analysis grid does to the ladder.
    result = run(
        SyntheticTrajectory((32, 16)), [metric_registry.get("mse")], ladder,
        fields=["density"], dataset=DatasetInfo(name="synthetic"), seed=0,
        analysis_resolution=resolution,
    )
    assert len(result.rows) > 0


def test_a_no_op_level_is_flagged_and_excluded_on_an_absolute_severity_axis():
    """The degenerate-severity level detector must cover uncalibrated operators too.

    ``severity_degenerate`` flags a severity level that resolves to a severity at which the
    operator does nothing, or that repeats a milder severity level's experiment, and
    ``summarise_axes`` drops it before any acceptance statistic is computed. Scoring such a
    severity level would read as agreement in the rank correlation and would compare a
    distribution against itself in the separability.

    The calibrated spectral and smoothing axes are where such levels usually arise. This
    checks the same guarantee on an axis whose severities stay absolute cell counts by design,
    where the no-op arises from the analysis grid rather than from the field's spectrum:
    ``translate_x`` runs to 16 cells in the shipped ladder, and on a periodic 16-cell axis
    ``np.roll(x, 16)`` is exactly ``x``. ``analysis_grid.resolution`` is a documented knob,
    so this configuration is reachable without editing the ladder at all.

    Measured here: level 5 records ``value = 0.0`` and ``energy_changed = 0.0``, is flagged,
    and is logged as "resolve[d] to a severity at which the operator leaves the field
    unchanged". Levels 1-4 are untouched. The detector is measurement-based rather than
    operator-declared, which is why it generalises to an operator that knows nothing about
    calibration -- and that generality is the thing worth pinning.
    """
    ladder = build_ladder(
        {"translate_x": {"op": "translate", "severities": [1, 2, 4, 8, 16],
                         "options": {"axis": "x"}}}
    )
    result = run(
        SyntheticTrajectory((16, 8)), [metric_registry.get("mse")], ladder,
        fields=["density"], dataset=DatasetInfo(name="synthetic"), seed=0,
    )
    rows = result.rows[result.rows["degradation"] == "translate_x"]
    by_level = rows.groupby(["level"], observed=True).agg(
        value=("value", "median"), flagged=("severity_degenerate", "max")
    )

    no_ops = by_level.index[by_level["value"] == 0.0].tolist()
    assert no_ops == [5], (
        f"expected only the 16-cell severity_level to be a no-op on a 16-cell axis, got {no_ops}"
    )
    assert bool(by_level.loc[5, "flagged"]), (
        "the 16-cell severity level reproduces the reference bit for bit but was not flagged "
        "severity_degenerate, so its exact tie with level 0 would be scored as agreement"
    )
    assert not by_level.loc[[1, 2, 3, 4], "flagged"].any(), (
        "a severity level that does real damage was flagged degenerate"
    )

    # And the exclusion actually reaches the acceptance statistics.
    axes = an.summarise_axes(result.rows, n_bootstrap=0)
    measured = int(axes.loc[axes["degradation"] == "translate_x", "n_levels"].iloc[0])
    assert measured == 4, (
        f"summarise_axes reports n_levels={measured}; the flagged severity_level was not dropped"
    )


# --- the report request --------------------------------------------------------------------


def test_a_map_frame_position_outside_the_selection_is_reported_clearly():
    """An out-of-range error-map position must name the config key, not numpy's axis 0.

    ``report.error_map.frames`` holds positions *within the selected frames*, so what is
    valid depends on ``dataset.time.reduction`` and on the trajectory length. Raising
    ``dataset.time.reduction`` far enough shrinks the selection under a configured
    position, and without a check ``pipeline.run`` would fail with

        IndexError: index 7 is out of bounds for axis 0 with size 4

    which names neither ``report.error_map.frames`` nor the reduction that shrank the
    selection.
    """
    ladder = build_ladder({"gaussian_blur": {"severities": [1.0, 2.0]}})

    with pytest.raises(ValueError, match=r"error_map|frames"):
        run(
            SyntheticTrajectory(n_frames=4), [metric_registry.get("mse")], ladder,
            fields=["density"], dataset=DatasetInfo(name="synthetic"), seed=0,
            maps=MapRequest(enabled=True, frames=[0, 7]),
        )


# --- the report renderers ---------------------------------------------------------------


def test_the_displacement_figure_declines_rather_than_crashes_without_damage(tmp_path):
    """A degenerate metric must skip the displacement figure, not error on it.

    AGENTS.md section 3 states that a single-field metric legitimately has no dynamic
    range and that ``rho = -1`` there "is correct, not a bug you should try to fix". With
    the damage column all-NaN there is no positive data for the displacement figure's log
    axis, where matplotlib would raise

        ValueError: Data cannot be log-scaled because all values are <= 0

    and a documented-correct configuration would put an error in the manifest. The renderer
    contract in AGENTS.md section 6 requires unavailability to be declared with
    ``ctx.require`` instead.
    """
    # A metric that cannot tell the anchor from clean: span = 0, so damage is all NaN.
    df = make_frame(metric="enstrophy", field="vorticity", n_frames=8,
                    axes={"translate_x": [1.0] * 4, "mean_field": [1.0] * 3})
    folder = RunFolder(tmp_path / "enstrophy_1").create()
    write_results(folder, df)
    digest = write_config(folder, {"metrics": ["enstrophy"], "seed": 1}, [])
    write_run_meta(folder, run_id=1, config_hash=digest, metric="enstrophy",
                   dataset="synthetic", n_frames=8, fields=["vorticity"],
                   analysis_grid=16, ladder_axes=["translate_x"], n_severity_levels=6, seed=1,
                   command="evaluate.py metrics=[enstrophy]")
    ctx = build_context(folder, thresholds={}, bootstrap=0)
    rendered = render(folder, ctx, formats=("png",))

    errored = [(r.name, r.reason) for r in rendered if r.status == "error"]
    assert not errored, (
        f"renderer(s) raised on a metric with no dynamic range: {errored}. "
        "AGENTS.md section 6 requires unavailability to be declared with ctx.require."
    )


# --------------------------------------------------------------------------------------
# A broken operator must stop the run, not quietly shrink the ladder
# --------------------------------------------------------------------------------------


def test_a_broken_operator_stops_the_run_rather_than_dropping_its_axis(temporary_degradation):
    """A defect in an operator is not the same as a severity this grid cannot support.

    Dropping an unsupported severity is right: it is one missing experiment and the rest
    are still worth having. Dropping a *broken* operator is wrong, because the run then
    completes, reports fewer rows, and gives a reader no reason to suspect an axis is
    missing rather than merely quiet. A ``NameError`` from a private helper lost when a
    module is split is exactly such a defect (AGENTS.md section 9); reported as "cannot run
    on the 16-cell analysis grid; raise analysis_grid.resolution" it would point at a knob
    with nothing to do with it.
    """
    @temporary_degradation(name="_broken_for_test", family="smoothing",
                           severity_name="width", severity_units="cells")
    def _broken_for_test(x, severity, *, ctx):
        return _missing_helper(x, severity)   # noqa: F821

    grid = GridSpec(shape=(16, 16), spacing=(1.0, 1.0), boundary=("periodic", "periodic"))
    data = np.random.default_rng(0).normal(size=(1, 16, 16))
    frame = Frame(index=0, time=0.0, grid=grid, fields={"vorticity": data})
    calibration = calibrate({"vorticity": [data]}, grid, ["vorticity"])
    levels = build_ladder({"_broken_for_test": {"severities": [1.0]}})

    with pytest.raises(RuntimeError, match="operator is broken"):
        _runnable_levels(levels, frame, ["vorticity"], seed=1, calibration=calibration,
                         analysis_grid=16)


def test_a_severity_the_grid_cannot_support_is_still_dropped_with_a_warning(caplog):
    """The legitimate case: warn, drop, and carry on.

    Coarsening by a factor that does not divide the grid is a limit of this run's
    configuration, not a defect, so the other severities are still worth measuring.
    """
    grid = GridSpec(shape=(8, 8), spacing=(1.0, 1.0), boundary=("periodic", "periodic"))
    data = np.random.default_rng(0).normal(size=(1, 8, 8))
    frame = Frame(index=0, time=0.0, grid=grid, fields={"vorticity": data})
    calibration = calibrate({"vorticity": [data]}, grid, ["vorticity"])
    levels = build_ladder({"coarsen": {"severities": [2.0, 16.0]}})

    with caplog.at_level(logging.WARNING):
        kept = _runnable_levels(levels, frame, ["vorticity"], seed=1, calibration=calibration,
                                analysis_grid=8)

    assert [level.severity for level in kept if level.label == "coarsen"] == [2.0]
    assert any("cannot run on the 8-cell analysis grid" in r.message for r in caplog.records)
    assert any("will not appear in the results" in r.message for r in caplog.records)


@pytest.mark.parametrize("first_import", ["evaluate", "metrics.registry", "degradations.registry",
                                          "fmeval"])
def test_the_card_validator_survives_every_import_order(first_import):
    """Whatever is imported first, both registries end up enforcing cards at `get()`.

    `fmeval/__init__` installs the validator onto the registry modules. A registry that
    imported `fmeval` while it was itself half-imported would then overwrite the hook with its
    own `CARD_VALIDATOR = None`, switching card validation off for every `evaluate.py` run
    while the suite still passed. Run in a fresh interpreter, because this process imported
    everything long ago.
    """
    code = (f"import {first_import}\n"
            "import fmeval, metrics.registry as m, degradations.registry as d\n"
            "assert m.CARD_VALIDATOR is not None, 'metric registry lost its card validator'\n"
            "assert d.CARD_VALIDATOR is not None, 'degradation registry lost its validator'\n")
    result = subprocess.run([sys.executable, "-c", code], cwd=REPO, capture_output=True,
                            text=True, timeout=120)
    assert result.returncode == 0, result.stderr[-2000:]


@pytest.mark.parametrize("ensemble", [False, True], ids=["deterministic", "ensemble"])
def test_a_field_the_operator_does_not_accept_records_no_energy(temporary_degradation,
                                                                ensemble):
    """Nothing was applied to that field, so it has no energy entry and its rows read NaN.

    The same convention on both kinds of frame: an energy of 0.0 would claim a measurement of
    an operator that never ran.
    """

    @temporary_degradation(name="_density_only", family="pointwise", fields=("density",))
    def _density_only(x, severity):
        """Adds a constant to density; declares no other field."""
        return x + severity

    fields = ["density", "velocity"]
    frame = SyntheticEnsembleTrajectory(grid=(16, 8), n_members=3, n_frames=2,
                                        fields=tuple(fields), seed=0).frame(1, fields)
    if not ensemble:
        frame = frame.with_fields(frame.fields, frame.grid)  # drops the members
    level = build_ladder({"probe": {"op": "_density_only", "severities": [1.0]}},
                         include_reference=False)[0]
    applied = apply_severity_level(level, frame, fields, seed=0)

    assert set(applied.energy_removed) == set(applied.energy_changed) == {"density"}
    assert "velocity" not in applied.resolved and set(applied.fields) == set(fields)
