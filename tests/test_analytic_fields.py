"""Closed-form oracles for the response statistics: fields whose metric response is known exactly.

Three fields, each run through the real pipeline with a real ladder: a Gaussian bump (smooth, so a
small displacement costs MSE quadratically), a top-hat stripe (a minimal shock, so the same
displacement costs MSE linearly), and a single Fourier mode (quadratic at first, then saturating).
The closed forms are in ``tests/analytic_fields.py``; each is first checked against a direct
computation, then used to check what the pipeline and the analysis report.

These are fixtures, not evidence: nothing measured here may be quoted about turbulence.
"""

from __future__ import annotations

import numpy as np
import pytest

from fmeval import analysis as an
from fmeval import stats
from fmeval.ladder import build_ladder
from fmeval.pipeline import DatasetInfo, run
from metrics import registry as metric_registry
from tests.analytic_fields import AnalyticTrajectory, canonical_field, expected_response

SHAPE = (64, 32)


def _evaluate(kind: str, ladder: dict, **field_params):
    trajectory = AnalyticTrajectory(kind, **field_params)
    specs = [metric_registry.get(name) for name in ("mse", "mae")]
    result = run(trajectory, specs, build_ladder(ladder), fields=["density"],
                 dataset=DatasetInfo(name=f"analytic_{kind}"), seed=0)
    return result.rows


def _medians(rows, metric: str, axis: str) -> tuple[np.ndarray, np.ndarray]:
    sub = rows[(rows["metric"] == metric) & (rows["degradation"] == axis)]
    medians = sub.groupby("level", observed=True)[["severity", "value"]].median()
    return medians["severity"].to_numpy(), medians["value"].to_numpy()


def _translation(severities):
    return {"translate_subpixel": {"severities": list(severities), "options": {"axis": "x"}}}


# --- the fields themselves ---------------------------------------------------------------


def test_bump_has_its_height_at_the_centre_and_falls_by_exp_half_at_one_width():
    f = canonical_field("bump", SHAPE, width=3.0, height=1.0, background=1.0)
    cx, cy = SHAPE[0] // 2, SHAPE[1] // 2
    assert f.shape == (1, *SHAPE)
    assert f[0, cx, cy] == pytest.approx(2.0, rel=1e-12)
    assert f[0, cx + 3, cy] == pytest.approx(1.0 + np.exp(-0.5), rel=1e-12)
    assert f[0, cx, cy - 10] == pytest.approx(f[0, cx, cy + 10], rel=1e-12), "periodic symmetry"


def test_step_raises_exactly_its_plateau():
    f = canonical_field("step", SHAPE, width=32, height=2.0, background=1.0)
    assert set(np.unique(f)) == {1.0, 3.0}
    assert int((f == 3.0).sum()) == 32 * SHAPE[1]


def test_mode_has_one_wavenumber_and_the_expected_moments():
    f = canonical_field("mode", SHAPE, wavenumber=3, height=1.0, background=1.0)
    assert f.mean() == pytest.approx(1.0, abs=1e-12)
    assert f.var() == pytest.approx(0.5, rel=1e-12)
    amplitude = np.abs(np.fft.fft(f[0, :, 0]))
    assert set(np.flatnonzero(amplitude > 1e-9)) == {0, 3, SHAPE[0] - 3}


def test_frames_are_integer_rolls_of_one_field_and_differ():
    trajectory = AnalyticTrajectory("bump", n_frames=4, seed=0)
    canonical = canonical_field("bump", SHAPE)
    frames = [trajectory.frame(t, ["density"]).fields["density"] for t in range(4)]
    assert frames[0].shape == (1, *SHAPE), "non-square, channel first: a transpose would fail here"
    for t, frame in enumerate(frames):
        assert np.array_equal(frame, np.roll(canonical, trajectory.offset(t), axis=(1, 2)))
    assert not np.array_equal(frames[0], frames[1])
    again = AnalyticTrajectory("bump", n_frames=4, seed=0).frame(2, ["density"]).fields["density"]
    assert np.array_equal(again, frames[2]), "same seed, same frames"


@pytest.mark.parametrize("kind,params", [("step", {"width": 32, "height": 2.0}),
                                         ("mode", {"wavenumber": 3, "height": 1.0})])
@pytest.mark.parametrize("metric", ["mse", "mae"])
def test_the_translation_oracle_matches_a_direct_roll(kind, params, metric):
    """The closed form is checked against an independent computation before it checks anything."""
    f = canonical_field(kind, SHAPE, **params)
    for d in (1, 2, 4):
        diff = np.roll(f, d, axis=1) - f
        direct = float(np.mean(diff**2) if metric == "mse" else np.mean(np.abs(diff)))
        oracle = expected_response(kind, metric, "translate_subpixel", d, shape=SHAPE, **params)
        # MAE of a mode integrates a kinked |cos|, so its 64-sample mean carries ~(1/64)^2 error.
        tolerance = 1e-3 if (kind, metric) == ("mode", "mae") else 1e-12
        assert oracle == pytest.approx(direct, rel=tolerance)


def test_unknown_kind_is_rejected_by_name():
    with pytest.raises(ValueError, match="kind"):
        AnalyticTrajectory("shock")


# --- through the pipeline ------------------------------------------------------------------


@pytest.mark.parametrize("kind", ["bump", "step", "mode"])
def test_reference_level_is_zero_and_values_are_frame_independent(kind):
    rows = _evaluate(kind, _translation([1, 2]))
    assert rows.loc[rows["level"] == 0, "value"].eq(0.0).all()
    for (_metric, _level), g in rows.groupby(["metric", "level"], observed=True):
        values = g["value"].to_numpy()
        if values.max() > 0:
            assert np.ptp(values) / values.max() < 1e-9, (
                "the closed form is a property of the field, not of where the feature sits"
            )


def test_bump_translation_matches_the_gaussian_autocorrelation():
    """Measured on this fixture: MSE slope 1.9947, MAE slope 1.0043 over w/16 to w/4."""
    shifts = [0.1875, 0.375, 0.75]                       # w/16, w/8, w/4 for w = 3
    rows = _evaluate("bump", _translation(shifts))
    d, mse = _medians(rows, "mse", "translate_subpixel")
    expected = [expected_response("bump", "mse", "translate_subpixel", s, shape=SHAPE) for s in d]
    assert mse == pytest.approx(expected, rel=1e-6)
    _, mae = _medians(rows, "mae", "translate_subpixel")
    slope_mse, slope_mae = stats.elasticity(d, mse), stats.elasticity(d, mae)
    assert slope_mse == pytest.approx(2.0, rel=0.05), f"MSE slope {slope_mse:.4f} on a smooth bump"
    assert slope_mae == pytest.approx(1.0, rel=0.05), f"MAE slope {slope_mae:.4f} on a smooth bump"


def test_step_translation_is_linear_in_the_displacement():
    rows = _evaluate("step", _translation([1, 2, 4]), width=32, height=2.0)
    d, mse = _medians(rows, "mse", "translate_subpixel")
    _, mae = _medians(rows, "mae", "translate_subpixel")
    assert mse == pytest.approx(d / 8, rel=1e-7)
    assert mae == pytest.approx(d / 16, rel=1e-7)
    slope = stats.elasticity(d, mse)
    assert slope == pytest.approx(1.0, abs=1e-4), (
        f"MSE slope {slope:.5f}: MSE is not quadratic on a shock -- a pointwise metric's "
        "elasticity depends on the field"
    )
    assert stats.elasticity(d, mae) == pytest.approx(1.0, abs=1e-4)


def test_mode_translation_accelerates_then_saturates():
    rows = _evaluate("mode", _translation([0.25, 0.5, 1, 2, 4, 8]))
    d, mse = _medians(rows, "mse", "translate_subpixel")
    _, mae = _medians(rows, "mae", "translate_subpixel")
    oracle = [expected_response("mode", "mse", "translate_subpixel", s, shape=SHAPE) for s in d]
    assert mse == pytest.approx(oracle, rel=1e-8)
    oracle_mae = [expected_response("mode", "mae", "translate_subpixel", s, shape=SHAPE) for s in d]
    assert mae == pytest.approx(oracle_mae, rel=1e-3)
    assert stats.elasticity(d[:3], mse[:3]) == pytest.approx(2.0, rel=0.02)
    def slope(y, i):
        return np.log(y[i + 1] / y[i]) / np.log(d[i + 1] / d[i])

    early, late = slope(mse, 0), slope(mse, len(d) - 2)
    assert late == pytest.approx(slope(oracle, len(d) - 2), rel=1e-6)
    assert early > 1.95 and late < 1.6, (
        f"local slopes {early:.3f} early and {late:.3f} late: quadratic at first, then saturating "
        "(the closed form gives 1.467 between shifts of 4 and 8 cells)"
    )


def test_mode_blur_matches_the_discrete_attenuation():
    """The scale calibration resolves 0.05 / 0.10 / 0.20 to sigma = 1.0667 / 2.1333 / 4.2667 cells
    (the mode's characteristic scale is Nx / m = 64 / 3), and the MSE slope in sigma over those is
    3.504 -- not the asymptotic 4, so the test compares with the closed form's own slope."""
    rows = _evaluate("mode", {"gaussian_blur": {"severities": [0.05, 0.10, 0.20]}})
    sigma, mse = _medians(rows, "mse", "gaussian_blur")
    oracle = np.array([expected_response("mode", "mse", "gaussian_blur", s, shape=SHAPE)
                       for s in sigma])
    assert mse == pytest.approx(oracle, rel=1e-8)
    assert stats.elasticity(sigma, mse) == pytest.approx(stats.elasticity(sigma, oracle), rel=0.02)


@pytest.mark.parametrize("kind,params", [("bump", {}), ("step", {"width": 32}), ("mode", {})])
def test_translation_axis_is_perfectly_ordered_on_every_kind(kind, params):
    rows = _evaluate(kind, _translation([1, 2, 4]), **params)
    axes = an.summarise_axes(rows, n_bootstrap=0)
    for _, row in axes.iterrows():
        assert row["rho"] == pytest.approx(1.0)
        assert row["monotone_fraction"] == pytest.approx(1.0)
        assert row["separability_auc_min"] == pytest.approx(1.0)


def test_a_translated_anchor_is_unreliable_on_a_single_mode():
    """The failure random_large_translation documents, measured: on one mode the residual
    correlation after a shift is cos(k d), so the 'unrelated field' value swings between draws.
    This is why the oracle tests above assert on values and never on damage."""
    rows = _evaluate("mode", {"uncorrelated": {"op": "random_large_translation",
                                               "severities": [0, 1, 2, 3, 4, 5]}})
    anchor = rows[(rows["metric"] == "mse") & (rows["degradation"] == "uncorrelated")]["value"]
    assert np.ptp(anchor.to_numpy()) > 1.0, f"anchor values span only {np.ptp(anchor):.3f}"
