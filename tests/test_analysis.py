"""The analysis layer: normalisation, per-axis criteria, probes, and flagging.

Built on a hand-made result frame with known answers, so failures point at the statistic
rather than at the simulation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from fmeval import analysis as an
from tests.conftest import make_frame

# --- normalisation --------------------------------------------------------------------


def test_uncorrelated_anchor_is_measured_when_present():
    df = make_frame(axes={"a": [1.0, 2.0], "uncorrelated": [10.0, 10.0, 10.0]})
    norm = an.normalisation(df)
    row = norm.iloc[0]
    assert row["anchor_source"] == "uncorrelated"
    assert row["value_clean"] == 0.0
    assert row["value_uncorrelated"] == pytest.approx(10.0)
    assert row["span"] == pytest.approx(10.0)
    assert not row["degenerate"]


def test_damage_is_one_at_the_anchor_and_zero_when_clean():
    df = make_frame(axes={"a": [1.0, 5.0], "uncorrelated": [10.0, 10.0]})
    scored = an.add_damage(df, an.normalisation(df))
    assert scored.loc[scored["level"] == 0, "damage"].eq(0.0).all()
    unc = scored[scored["degradation"] == "uncorrelated"]
    assert unc["damage"].median() == pytest.approx(1.0)
    a2 = scored[(scored["degradation"] == "a") & (scored["level"] == 2)]
    assert a2["damage"].median() == pytest.approx(0.5)


def test_anchor_falls_back_to_the_largest_translation_and_says_so():
    """Without a measured anchor the fallback understates it, so the source is recorded."""
    df = make_frame(axes={"translate_x": [1.0, 2.0, 6.0]})
    row = an.normalisation(df).iloc[0]
    assert row["anchor_source"] == "translate_x@max"
    assert row["value_uncorrelated"] == pytest.approx(6.0)


def test_a_second_row_under_one_key_is_refused():
    """Two rows for one (frame, field, metric, variant) would be read as one point, merged.

    That is what a metric writing several numbers per evaluation into ``results.csv`` produced:
    every statistic averaged or ranked its components together. The guard names the key.
    """
    df = make_frame(axes={"a": [1.0, 2.0]})
    assert not an.normalisation(df).empty
    with pytest.raises(ValueError, match="share a key"):
        an.normalisation(pd.concat([df, df.iloc[:1]], ignore_index=True))


def test_degenerate_metric_is_marked_and_produces_no_damage():
    df = make_frame(axes={"a": [3.0, 3.0, 3.0]}, reference=3.0)  # constant everywhere
    norm = an.normalisation(df)
    assert bool(norm.iloc[0]["degenerate"])
    assert an.add_damage(df, norm)["damage"].isna().all()


# --- per-axis criteria ------------------------------------------------------------------


def test_perfectly_monotone_axis_scores_one():
    df = make_frame(axes={"a": [1.0, 2.0, 3.0, 4.0]})
    axes = an.summarise_axes(df, n_bootstrap=0)
    row = axes[axes["degradation"] == "a"].iloc[0]
    assert row["rho"] == pytest.approx(1.0)
    assert row["monotone_fraction"] == pytest.approx(1.0)
    assert row["separability_auc_min"] == pytest.approx(1.0)


def test_non_monotone_axis_is_detected():
    df = make_frame(axes={"a": [1.0, 4.0, 2.0, 3.0]})
    row = an.summarise_axes(df, n_bootstrap=0).iloc[0]
    assert row["rho"] < 0.9
    assert row["monotone_fraction"] == pytest.approx(0.0)


def test_overlapping_severity_levels_lower_the_separability_without_hurting_rho():
    """A metric can be monotone in the median and still unable to rank two models."""
    clean = an.summarise_axes(make_frame(axes={"a": [1.0, 2.0]}, noise=0.0),
                              n_bootstrap=0).iloc[0]
    noisy = an.summarise_axes(make_frame(axes={"a": [1.0, 1.05]}, noise=0.5, seed=3),
                              n_bootstrap=0).iloc[0]
    assert clean["separability_auc_min"] == pytest.approx(1.0)
    assert noisy["separability_auc_min"] < 0.8


def test_probe_axes_get_no_rank_correlation():
    """The IN-4 field and the anchor are not severity levels; correlating them would be
    meaningless."""
    df = make_frame(axes={"a": [1.0, 2.0], "gaussian_impostor": [9.0],
                          "uncorrelated": [10.0, 10.0]})
    axes = an.summarise_axes(df, n_bootstrap=0)
    for label in ("gaussian_impostor", "uncorrelated"):
        row = axes[axes["degradation"] == label].iloc[0]
        assert bool(row["is_probe"])
        assert np.isnan(row["rho"])


def test_sensitivity_and_saturation_levels():
    """Span is 1.0, so the thresholds sit at 0.1 and 0.9."""
    df = make_frame(axes={"a": [0.05, 0.2, 0.95, 1.0]})
    row = an.summarise_axes(df, n_bootstrap=0).iloc[0]
    assert row["sensitivity_level"] == 2.0   # level 1 is 0.05, below 0.1; level 2 is 0.2
    assert row["saturation_level"] == 3.0    # level 3 is 0.95, the first at or above 0.9


def test_block_bootstrap_produces_a_bracketing_interval():
    df = make_frame(axes={"a": [1.0, 2.0, 3.0, 4.0]}, noise=0.4, seed=1, n_frames=40)
    row = an.summarise_axes(df, block_length=4, n_bootstrap=80, seed=0).iloc[0]
    assert np.isfinite(row["rho_ci_lo"]) and np.isfinite(row["rho_ci_hi"])
    assert row["rho_ci_lo"] <= row["rho_ci_hi"]
    assert row["rho_ci_lo"] <= row["rho"] + 1e-9


def test_bootstrap_is_skipped_when_there_are_too_few_frames():
    df = make_frame(axes={"a": [1.0, 2.0]}, n_frames=3)
    row = an.summarise_axes(df, block_length=10, n_bootstrap=50).iloc[0]
    assert np.isnan(row["rho_ci_lo"])


# --- probes ------------------------------------------------------------------------------


def test_probe_summary_reports_damage_and_the_nearest_level():
    df = make_frame(
        axes={"a": [2.0, 5.0, 8.0], "gaussian_impostor": [5.0],
              "uncorrelated": [10.0, 10.0]}
    )
    probes = an.probe_summary(df, an.normalisation(df))
    row = probes.iloc[0]
    assert row["gaussian_impostor_damage"] == pytest.approx(0.5)
    assert row["gaussian_impostor_nearest_level"] == "a=2"
    assert row["uncorrelated_damage"] == pytest.approx(1.0)


# --- roll-up and flagging ------------------------------------------------------------------


def _card(axes_values: dict[str, list[float]]) -> pd.DataFrame:
    """The flagged report card of a synthetic run with the given ladder."""
    card = an.analyse(make_frame(axes=axes_values), n_bootstrap=0).card
    return an.flag(card, {"spearman": 0.9, "separability_auc": 0.8, "impostor_damage": 0.5})


def test_report_card_reports_the_worst_axis():
    card = _card({"good": [1.0, 2.0, 3.0], "bad": [1.0, 3.0, 2.0],
                  "uncorrelated": [10.0, 10.0]})
    row = card.iloc[0]
    assert row["worst_axis"] == "bad"
    assert row["rho_min"] < row["rho_median"]
    assert row["n_axes"] == 2


def test_report_card_has_no_verdict_column():
    """The suite reports measurements; the panel decision is made by people."""
    card = _card({"a": [1.0, 2.0], "uncorrelated": [10.0, 10.0]})
    assert "verdict" not in card.columns
    assert "accept" not in " ".join(card.columns)


def test_flags_name_the_thresholds_that_were_not_met():
    card = _card({"a": [1.0, 3.0, 2.0], "uncorrelated": [10.0, 10.0]})
    flags = card.iloc[0]["flags"]
    assert "spearman=" in flags


def test_empty_flags_when_everything_clears_the_thresholds():
    card = _card({"a": [1.0, 2.0, 3.0], "gaussian_impostor": [9.0],
                  "uncorrelated": [10.0, 10.0]})
    assert card.iloc[0]["flags"] == ""


def test_flagging_is_separate_from_computation():
    """Re-flagging with different thresholds must need no recomputation."""
    df = make_frame(axes={"a": [1.0, 2.0, 3.0], "uncorrelated": [10.0, 10.0]})
    norm = an.normalisation(df)
    card = an.report_card(an.summarise_axes(df, n_bootstrap=0),
                          an.probe_summary(df, norm), norm)
    strict = an.flag(card, {"spearman": 1.5})
    loose = an.flag(card, {"spearman": 0.1})
    assert strict.iloc[0]["flags"] != ""
    assert loose.iloc[0]["flags"] == ""
    assert "flags" not in card.columns, "flag() must not mutate its input"


# --- cross-metric --------------------------------------------------------------------------


def test_cross_metric_correlation_finds_duplicates():
    """A redundant pair correlates at +1 and an opposed pair at -1.

    The -1 also shows the reference level is excluded: every pairwise metric is 0 there, so
    keeping it would add a point every pair shares and pull each correlation toward +1.
    """
    a = make_frame(metric="a", axes={"x": [1.0, 2.0, 3.0, 4.0]})
    b = make_frame(metric="b", axes={"x": [2.0, 4.0, 6.0, 8.0]})   # perfectly redundant
    c = make_frame(metric="c", axes={"x": [4.0, 3.0, 2.0, 1.0]})   # anti-correlated
    rho = an.cross_metric_correlation(pd.concat([a, b, c], ignore_index=True))
    assert rho.loc["a", "b"] == pytest.approx(1.0)
    assert rho.loc["a", "c"] == pytest.approx(-1.0)


def test_cross_metric_correlation_needs_two_metrics():
    assert an.cross_metric_correlation(make_frame()).empty


# --- pooled vs per-frame correlation ---------------------------------------------------------


def test_per_frame_correlation_survives_a_trend_in_the_field():
    """The case this statistic exists for.

    A field whose amplitude grows along the trajectory makes the pooled correlation
    meaningless: the worst severity level early is smaller than the mildest severity level late.
    Measured on the real density field, every axis was perfectly ordered within every frame while
    the pooled value read between 0.10 and 0.91.
    """
    df = make_frame(axes={"a": [1.0, 2.0, 3.0, 4.0]}, n_frames=10)
    df["value"] *= 10.0 ** df["frame_index"]   # nine orders of magnitude across the trajectory

    row = an.summarise_axes(df, n_bootstrap=0).iloc[0]
    assert row["rho"] == pytest.approx(1.0), "per-frame correlation must be unaffected"
    assert row["monotone_fraction"] == pytest.approx(1.0)
    assert row["rho_pooled"] < 0.8, (
        "the pooled value should be visibly degraded here; if it is not, this test no "
        "longer demonstrates the difference"
    )


def test_per_frame_correlation_still_detects_a_genuinely_bad_axis():
    """Robustness to a trend must not come at the cost of sensitivity."""
    df = make_frame(axes={"a": [4.0, 3.0, 2.0, 1.0]})   # exactly inverted
    row = an.summarise_axes(df, n_bootstrap=0).iloc[0]
    assert row["rho"] == pytest.approx(-1.0)
    assert row["monotone_fraction"] == pytest.approx(0.0)


# --- response statistics ---------------------------------------------------------------------


def _scored(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    norm = an.normalisation(df)
    return an.add_damage(df, norm), norm


def _axis(axes: pd.DataFrame, label: str = "a") -> pd.Series:
    return axes[axes["degradation"] == label].iloc[0]


def test_golden_rho_ci_is_unchanged():
    """Golden values for the rank-correlation interval.

    Axis ``b`` has a real interval and draws second from the generator every group shares, so this
    fails if anything else consumes that generator or changes the resampling.
    """
    df = make_frame(axes={"a": [1.0, 2.0, 3.0, 4.0], "b": [1.0, 1.2, 1.4, 1.6]},
                    noise=0.5, seed=1, n_frames=40)
    scored, norm = _scored(df)
    for frame in (df, scored):
        axes = an.summarise_axes(frame, norm=norm, block_length=4, n_bootstrap=80, seed=0)
        assert (_axis(axes, "a")["rho_ci_lo"], _axis(axes, "a")["rho_ci_hi"]) == (1.0, 1.0)
        b = _axis(axes, "b")
        assert (b["rho_ci_lo"], b["rho_ci_hi"]) == (0.39999999999999997, 0.7)


def test_response_columns_exist_and_are_withheld_for_probes():
    df = make_frame(axes={"a": [1.0, 2.0, 3.0, 4.0], "gaussian_impostor": [9.0],
                          "uncorrelated": [10.0, 10.0]})
    scored, norm = _scored(df)
    axes = an.summarise_axes(scored, norm=norm, n_bootstrap=0)
    assert set(an.RESPONSE_COLUMNS) <= set(axes.columns)
    for label in ("gaussian_impostor", "uncorrelated"):
        row = _axis(axes, label)
        for column in an.RESPONSE_COLUMNS:
            value = row[column]
            assert value == "" if isinstance(value, str) else np.isnan(value), (
                f"{column} on probe {label} should be withheld, got {value!r}"
            )


def test_quadratic_ladder_has_elasticity_two():
    row = _axis(an.summarise_axes(make_frame(axes={"a": [1.0, 4.0, 9.0, 16.0]}), n_bootstrap=0))
    assert row["elasticity"] == pytest.approx(2.0, abs=1e-9)
    assert row["response_shape"] == "power"
    assert row["elasticity_x"] == "severity (s)"


def test_elasticity_uses_the_mildest_levels():
    """A ladder that saturates at its last level still reads as quadratic at its start."""
    row = _axis(an.summarise_axes(make_frame(axes={"a": [1.0, 4.0, 9.0, 9.5]}), n_bootstrap=0))
    assert row["elasticity"] == pytest.approx(2.0, abs=1e-9)


def _with_severity(df: pd.DataFrame, axis: str, severity: dict[int, float], *,
                   nominal: dict[int, float] | None = None, calibration: str = "",
                   name: str | None = None) -> pd.DataFrame:
    """Rewrite one axis's severities the way a calibrated or decreasing operator records them."""
    out = df.copy()
    out["calibration"] = ""
    out["severity_nominal"] = out["severity"]
    out["severity_name"] = out["severity_name"].astype(str)
    on = out["degradation"] == axis
    out.loc[on, "severity"] = out.loc[on, "level"].map(severity)
    out.loc[on, "severity_nominal"] = out.loc[on, "level"].map(nominal or severity)
    out.loc[on, "calibration"] = calibration
    if name is not None:
        out.loc[on, "severity_name"] = name
    return out


def test_calibrated_axis_uses_the_nominal_severity():
    """A low-pass records the resolved cutoff, which FALLS with level (33 -> 4.7 on vorticity in the
    pinned run) and differs per field; a slope against it has the wrong sign and the wrong label."""
    df = _with_severity(make_frame(axes={"a": [1.0, 2.0, 3.0, 4.0], "uncorrelated": [10.0, 10.0]}),
                        "a", {1: 32.0, 2: 16.0, 3: 8.0, 4: 4.0},
                        nominal={1: 0.05, 2: 0.15, 3: 0.30, 4: 0.45},
                        calibration="energy_above", name="energy removed")
    scored, norm = _scored(df)
    row = _axis(an.summarise_axes(scored, norm=norm, n_bootstrap=0))
    assert row["elasticity_x"] == "severity_nominal (energy removed)"
    assert row["elasticity"] > 0, f"a rising response has a positive slope: {row['elasticity']}"
    assert 0.05 <= row["severity_10"] <= 0.45, "the onset is in the units of the nominal severity"


def test_decreasing_absolute_knob_uses_its_reciprocal():
    df = _with_severity(make_frame(axes={"a": [1.0, 2.0, 3.0, 4.0]}), "a",
                        {1: 8.0, 2: 4.0, 3: 2.0, 4: 1.0})
    row = _axis(an.summarise_axes(df, n_bootstrap=0))
    assert row["elasticity_x"].startswith("1/severity")
    assert row["elasticity"] > 0


def test_cliffs_delta_is_two_auc_minus_one():
    row = _axis(an.summarise_axes(make_frame(axes={"a": [1.0, 1.05]}, noise=0.5, seed=3),
                                  n_bootstrap=0))
    assert row["cliffs_delta_min"] == pytest.approx(2 * row["separability_auc_min"] - 1)
    perfect = _axis(an.summarise_axes(make_frame(axes={"a": [1.0, 2.0]}), n_bootstrap=0))
    assert perfect["cliffs_delta_min"] == pytest.approx(1.0)


def test_severity_10_and_50_interpolate_in_physical_units():
    df = make_frame(axes={"a": [0.05, 0.2, 0.95, 1.0], "uncorrelated": [1.0, 1.0]})
    scored, norm = _scored(df)
    row = _axis(an.summarise_axes(scored, norm=norm, n_bootstrap=0))
    assert row["severity_10"] == pytest.approx(2 ** (1 / 3)), "log-linear between levels 1 and 2"
    assert 2.0 < row["severity_50"] < 3.0
    short = make_frame(axes={"a": [0.05, 0.1, 0.2, 0.3], "uncorrelated": [1.0, 1.0]})
    scored, norm = _scored(short)
    assert np.isnan(_axis(an.summarise_axes(scored, norm=norm, n_bootstrap=0))["severity_50"])


def test_onset_severities_need_a_damage_scale():
    df = make_frame(axes={"a": [3.0, 3.0, 3.0]}, reference=3.0)
    scored, norm = _scored(df)
    row = _axis(an.summarise_axes(scored, norm=norm, n_bootstrap=0))
    assert np.isnan(row["severity_10"]) and np.isnan(row["severity_50"])


def test_higher_is_better_metric_gets_the_same_onset_as_its_mirror():
    """The onset target must be built from the SIGNED span: for a similarity metric it lies below
    the clean value, and an unsigned span puts it where the clean point already reaches it."""
    error = make_frame(axes={"a": [0.2, 0.4, 0.6, 0.8], "uncorrelated": [1.0, 1.0]})
    similarity = make_frame(axes={"a": [0.8, 0.6, 0.4, 0.2], "uncorrelated": [0.0, 0.0]},
                            reference=1.0)
    similarity["higher_is_better"] = True
    rows = []
    for df in (error, similarity):
        scored, norm = _scored(df)
        rows.append(_axis(an.summarise_axes(scored, norm=norm, n_bootstrap=0)))
    assert rows[1]["severity_10"] == pytest.approx(rows[0]["severity_10"])
    assert rows[1]["severity_10"] > 0
    assert rows[1]["elasticity"] == pytest.approx(rows[0]["elasticity"])


def test_severity_resolution_is_sigma_over_slope():
    noisy = make_frame(axes={"a": [1.0, 2.0, 3.0, 4.0], "uncorrelated": [10.0, 10.0]},
                       noise=0.1, n_frames=40)
    resolution = _axis(an.summarise_axes(noisy, n_bootstrap=0))["severity_resolution"]
    assert 0.05 < resolution < 0.2, f"expected about sqrt(2)*0.1 per unit step, got {resolution}"
    clean = make_frame(axes={"a": [1.0, 2.0, 3.0, 4.0], "uncorrelated": [10.0, 10.0]})
    exact = _axis(an.summarise_axes(clean, n_bootstrap=0))["severity_resolution"]
    assert exact == pytest.approx(0.0, abs=1e-12), "no scatter: only round-off from scaling"
    flat = make_frame(axes={"flat": [1.0, 1.0, 1.0, 1.0], "uncorrelated": [10.0, 10.0]},
                      noise=0.1, n_frames=40)
    assert _axis(an.summarise_axes(flat, n_bootstrap=0), "flat")["severity_resolution"] > 1.0, (
        "an axis the metric does not move along cannot resolve even one ladder step"
    )


def test_field_change_max_is_the_median_energy_changed_at_the_harshest_level():
    df = make_frame(axes={"a": [1.0, 2.0, 3.0, 4.0]})
    df["energy_changed"] = np.where(df["level"] > 0, 0.01 * df["severity"] ** 2, 0.0)
    assert _axis(an.summarise_axes(df, n_bootstrap=0))["field_change_max"] == pytest.approx(0.16)
    assert np.isnan(_axis(an.summarise_axes(make_frame(), n_bootstrap=0))["field_change_max"])


# --- the blindness bound ---------------------------------------------------------------------


def test_flat_axis_is_provably_blind_and_a_responsive_one_is_not():
    axes = an.analyse(make_frame(axes={"flat": [1e-3] * 4, "steep": [1.0, 2.0, 3.0, 4.0],
                                       "uncorrelated": [10.0, 10.0]}, noise=1e-4, n_frames=40),
                      n_bootstrap=100).axes
    flat, steep = _axis(axes, "flat"), _axis(axes, "steep")
    assert flat["damage_max_ucb"] < an.BLINDNESS_MARGIN
    assert flat["blindness_q"] < an.FDR_LEVEL, "no resample reached the margin"
    assert steep["damage_max_ucb"] > an.BLINDNESS_MARGIN
    assert steep["blindness_q"] == pytest.approx(1.0), "every resample reached the margin"


def test_the_margin_sits_below_the_detection_fraction():
    """'Detected' (a tenth of the span) and 'blind' (below the margin) can never both hold."""
    assert an.BLINDNESS_MARGIN < an.SENSITIVITY_FRACTION


def test_bound_is_relative_to_the_largest_response_when_the_anchor_is_degenerate():
    """issues/037: a metric that cannot see the anchor has no damage, yet its blindness to the
    anchor's operator is exactly the finding. The bound is then read against its largest ladder
    response, and the norm frame's `degenerate` says which scale was used."""
    df = make_frame(axes={"gaussian_blur": [0.1, 0.3], "translate_x": [1.5e-16] * 3,
                          "uncorrelated": [1.5e-16] * 3})
    scored, norm = _scored(df)
    assert bool(norm.iloc[0]["degenerate"])
    axes = an.summarise_axes(scored, norm=norm, n_bootstrap=50)
    assert _axis(axes, "translate_x")["blindness_q"] < an.FDR_LEVEL
    assert _axis(axes, "gaussian_blur")["blindness_q"] == pytest.approx(1.0)


def test_bound_is_withheld_for_a_target_valued_metric():
    """Damage is on the raw ratio for a two-sided metric, so a bound on it would not be oriented."""
    df = make_frame(axes={"a": [1.2, 1.5, 2.0, 3.0], "uncorrelated": [3.0, 3.0]}, n_frames=20,
                    reference=1.0)
    df["target_value"] = 1.0
    row = _axis(an.analyse(df, n_bootstrap=100).axes)
    assert np.isnan(row["damage_max_ucb"]) and np.isnan(row["blindness_q"])


def test_blindness_q_grows_with_the_number_of_rows_it_is_adjusted_over():
    """Benjamini-Yekutieli across every row of the run: more rows, a larger adjustment."""
    edge = {"edge": [0.02, 0.03, 0.04, 0.05], "uncorrelated": [1.0, 1.0]}
    alone = make_frame(axes=edge, noise=0.01, n_frames=40, seed=4)
    crowded = pd.concat(
        [alone] + [make_frame(metric=m, axes={"x": [1.0, 2.0], "y": [2.0, 3.0],
                                              "uncorrelated": [1.0, 1.0]}, n_frames=40)
                   for m in ("p", "q", "r")],
        ignore_index=True,
    )
    q_alone = _axis(an.analyse(alone, n_bootstrap=100).axes, "edge")["blindness_q"]
    axes = an.analyse(crowded, n_bootstrap=100).axes
    mine = axes[(axes["metric"] == "m") & (axes["degradation"] == "edge")]
    q_crowded = mine.iloc[0]["blindness_q"]
    assert 0 < q_alone < 1, f"the edge axis should sit near the margin, got q = {q_alone}"
    assert q_crowded >= q_alone


def test_block_length_is_estimated_on_the_frame_scaled_trace():
    """A metric whose magnitude drifts along the trajectory (density grows six orders) must not
    have that drift read as persistence: the block length comes from the frame-scaled trace."""
    df = make_frame(axes={"a": [1.0, 2.0, 3.0, 4.0], "uncorrelated": [10.0, 10.0]}, n_frames=40)
    df["value"] = df["value"] * 1.2 ** df["frame_index"]
    row = _axis(an.analyse(df, n_bootstrap=100).axes)
    assert row["blindness_block_length"] <= 3, (
        f"block length {row['blindness_block_length']} reflects the drift, not the dependence"
    )


# --- per-metric roll-ups ---------------------------------------------------------------------


def _profile_frame(per_unit: dict[str, float]) -> pd.DataFrame:
    """Axes with the same damage but different field change, so damage per unit change differs."""
    ladder = {a: [1.0, 2.0, 3.0, 4.0] for a in per_unit}
    df = make_frame(axes={**ladder, "uncorrelated": [10.0, 10.0]})
    change = df["degradation"].map(per_unit).astype(float)
    df["energy_changed"] = np.where(df["level"] > 0, df["value"] / 10 / change.fillna(1.0), 0.0)
    return df


def test_selectivity_is_zero_when_every_degradation_costs_the_same_per_unit_change():
    """Mean squared error's own profile: damage in proportion to field change on every axis."""
    card = an.analyse(_profile_frame({"a": 1.0, "b": 1.0, "c": 1.0}), n_bootstrap=0).card.iloc[0]
    assert card["selectivity"] == pytest.approx(0.0, abs=1e-12)


def test_selectivity_is_high_when_one_degradation_dominates_per_unit_change():
    card = an.analyse(_profile_frame({"a": 10.0, "b": 1.0, "c": 1.0}), n_bootstrap=0).card.iloc[0]
    assert card["selectivity"] > 0.5
    assert card["most_sensitive_axis"] == "a"
    assert card["least_sensitive_axis"] in {"b", "c"}


def test_blind_axes_lists_only_axes_below_the_fdr_level():
    card = an.analyse(make_frame(axes={"flat": [1e-3] * 4, "steep": [1.0, 2.0, 3.0, 4.0],
                                       "uncorrelated": [10.0, 10.0]}, noise=1e-4, n_frames=40),
                      n_bootstrap=100).card.iloc[0]
    assert card["blind_axes"] == "flat"
    none = an.analyse(make_frame(axes={"steep": [1.0, 2.0, 3.0, 4.0],
                                       "uncorrelated": [10.0, 10.0]}, noise=1e-4, n_frames=40),
                      n_bootstrap=100).card.iloc[0]
    assert none["blind_axes"] == ""


def test_elasticity_displacement_reads_translate_subpixel():
    card = an.analyse(make_frame(axes={"translate_subpixel": [1.0, 4.0, 9.0, 16.0],
                                       "uncorrelated": [100.0, 100.0]}), n_bootstrap=0).card
    assert card.iloc[0]["elasticity_displacement"] == pytest.approx(2.0, abs=1e-9)
    other = an.analyse(make_frame(axes={"a": [1.0, 2.0], "uncorrelated": [9.0, 9.0]}),
                       n_bootstrap=0).card
    assert np.isnan(other.iloc[0]["elasticity_displacement"])


def test_report_card_survives_an_all_nan_damage_profile():
    df = make_frame(axes={"a": [3.0, 3.0, 3.0], "b": [3.0, 3.0]}, reference=3.0)
    card = an.analyse(df, n_bootstrap=0).card.iloc[0]
    assert np.isnan(card["selectivity"])
    assert pd.isna(card["most_sensitive_axis"]) and pd.isna(card["least_sensitive_axis"])


def test_analyse_returns_what_both_call_sites_need():
    df = make_frame(axes={"a": [1.0, 2.0, 3.0], "gaussian_impostor": [9.0],
                          "uncorrelated": [10.0, 10.0]})
    result = an.analyse(df, n_bootstrap=0)
    assert "damage" in result.scored.columns
    assert set(an.RESPONSE_COLUMNS) <= set(result.axes.columns)
    assert "gaussian_impostor_damage" in result.probes.columns
    assert "selectivity" in result.card.columns
    assert "flags" not in result.card.columns, "flagging is the report's business, not the cards'"


# --- agreement in magnitude ------------------------------------------------------------------


def _two_metrics(a: dict, b: dict, **kwargs) -> pd.DataFrame:
    return pd.concat([make_frame(metric="a", axes=a, **kwargs),
                      make_frame(metric="b", axes=b, **kwargs)], ignore_index=True)


def test_damage_by_level_has_one_row_per_level_and_one_column_per_metric():
    df = _two_metrics({"x": [1.0, 2.0], "translate_x": [3.0, 4.0], "uncorrelated": [10.0, 10.0]},
                      {"x": [2.0, 4.0], "translate_x": [6.0, 8.0], "uncorrelated": [20.0, 20.0]})
    wide = an.damage_by_level(_scored(df)[0])
    assert {"field", "degradation", "level", "severity", "a", "b"} <= set(wide.columns)
    assert (wide["level"] > 0).all()
    assert set(wide["degradation"]) == {"x", "translate_x"}, "probes are not ladder levels"
    assert wide.loc[wide["degradation"] == "x", "a"].tolist() == pytest.approx([0.1, 0.2])
    geometric = an.damage_by_level(_scored(df)[0], family="geometric")
    assert set(geometric["degradation"]) == {"translate_x"}


def test_per_level_response_records_every_level_once_with_its_quartiles():
    """The curve record a figure draws: one row per field, degradation and level, probes out."""
    df = _two_metrics({"x": [1.0, 2.0, 3.0], "translate_x": [3.0, 4.0],
                       "gaussian_impostor": [9.0], "uncorrelated": [10.0, 10.0]},
                      {"x": [2.0, 4.0, 6.0], "translate_x": [6.0, 8.0],
                       "gaussian_impostor": [9.0], "uncorrelated": [20.0, 20.0]},
                      noise=0.05, seed=3)
    curve = an.per_level_response(_scored(df)[0], metric="a")
    keys = curve[["field", "degradation", "level"]].apply(tuple, axis=1)
    assert keys.is_unique and len(curve) == 5
    assert set(curve["degradation"]) == {"x", "translate_x"}, "probes are not ladder levels"
    assert (curve["level"] > 0).all() and curve["level"].dtype.kind == "i"
    assert (curve["damage_q25"] <= curve["damage_median"]).all()
    assert (curve["damage_median"] <= curve["damage_q75"]).all()
    assert (curve["value_q25"] <= curve["value_median"]).all()
    assert (curve["n_frames"] == 12).all()
    assert list(curve.columns[:4]) == list(an.RESPONSE_KEYS)
    assert not curve["severity_degenerate"].any()


def test_per_level_response_agrees_with_damage_by_level():
    """Two ways to get a median per level is how a figure and its table drift apart."""
    df = _two_metrics({"x": [1.0, 2.0], "translate_x": [3.0, 4.0], "uncorrelated": [10.0, 10.0]},
                      {"x": [2.0, 4.0], "translate_x": [6.0, 8.0], "uncorrelated": [20.0, 20.0]},
                      noise=0.1, seed=5)
    scored = _scored(df)[0]
    scored.loc[(scored["degradation"] == "x") & (scored["level"] == 2),
               "severity_degenerate"] = True
    wide = an.damage_by_level(scored)
    for metric in ("a", "b"):
        curve = an.per_level_response(scored, metric=metric)
        assert curve["severity_degenerate"].sum() == 1, "the flagged level is kept and flagged"
        kept = curve[~curve["severity_degenerate"]]
        merged = kept.merge(wide, on=["field", "degradation", "level"], suffixes=("", "_wide"))
        assert len(merged) == len(kept) == len(wide)
        assert merged["damage_median"].to_numpy() == pytest.approx(merged[metric].to_numpy())


def test_per_level_response_without_a_damage_scale_still_records_the_value():
    scored = _scored(_single_field({"blur": [1.0, 2.0, 3.0]}))[0]
    curve = an.per_level_response(scored, metric="m")
    assert curve["damage_median"].isna().all(), "no span between clean and the anchor"
    assert np.isfinite(curve["value_median"]).all()
    assert (curve["value_median"].diff().dropna() > 0).all()


def test_per_level_response_needs_the_damage_column():
    with pytest.raises(KeyError, match="add_damage"):
        an.per_level_response(make_frame(), metric="m")


def test_damage_by_level_needs_the_damage_column():
    with pytest.raises(KeyError, match="add_damage"):
        an.damage_by_level(make_frame())


def test_concordance_penalises_shape_disagreement_where_spearman_does_not():
    """MAE and MSE on the pinned run: rank correlation 0.986, concordance 0.699. The same pattern
    in miniature: b is a monotone but curved function of a."""
    x = [1.0, 2.0, 3.0, 4.0]
    df = _two_metrics({"s": x, "uncorrelated": [10.0, 10.0]},
                      {"s": list(np.sqrt(x)), "uncorrelated": [np.sqrt(10.0)] * 2})
    rho = an.cross_metric_correlation(df)
    rc = an.concordance_matrix(_scored(df)[0])
    assert rho.loc["a", "b"] == pytest.approx(1.0)
    assert rc.loc["a", "b"] < 0.99
    assert rc.loc["a", "b"] == pytest.approx(rc.loc["b", "a"])
    assert rc.loc["a", "a"] == pytest.approx(1.0)


def test_concordance_is_one_for_a_proportional_twin():
    """A metric that is exactly twice another, anchor included, has identical damage: the scale
    removes the factor. Pinned so nobody 'fixes' a concordance test by breaking D = 1."""
    x = [1.0, 2.0, 3.0, 4.0]
    df = _two_metrics({"s": x, "uncorrelated": [10.0, 10.0]},
                      {"s": [2 * v for v in x], "uncorrelated": [20.0, 20.0]})
    assert an.concordance_matrix(_scored(df)[0]).loc["a", "b"] == pytest.approx(1.0)


def test_concordance_and_participation_ratio_tolerate_a_missing_level():
    x = [1.0, 2.0, 3.0, 4.0]
    df = _two_metrics({"s": x, "t": x, "uncorrelated": [10.0, 10.0]},
                      {"s": list(np.sqrt(x)), "t": x, "uncorrelated": [10.0, 10.0]})
    df = df[~((df["metric"] == "b") & (df["degradation"] == "s") & (df["level"] == 2))]
    scored = _scored(df)[0]
    assert np.isfinite(an.concordance_matrix(scored).loc["a", "b"])
    assert np.isfinite(an.participation_ratio_of_metrics(scored))


def test_participation_ratio_counts_independent_responses():
    same = _two_metrics({"p": [1.0, 2.0, 3.0, 4.0], "uncorrelated": [10.0, 10.0]},
                        {"p": [1.0, 2.0, 3.0, 4.0], "uncorrelated": [10.0, 10.0]})
    apart = _two_metrics({"p": [1.0, 2.0, 3.0, 4.0], "q": [0.0] * 4, "uncorrelated": [10.0] * 2},
                         {"p": [0.0] * 4, "q": [1.0, 2.0, 3.0, 4.0], "uncorrelated": [10.0] * 2})
    one = an.participation_ratio_of_metrics(_scored(same)[0])
    two = an.participation_ratio_of_metrics(_scored(apart)[0])
    assert one == pytest.approx(1.0, abs=0.05), "identical responses span one direction"
    assert one < two <= 2.0
    assert np.isnan(an.participation_ratio_of_metrics(_scored(make_frame(
        axes={"p": [1.0, 2.0, 3.0], "uncorrelated": [9.0, 9.0]}))[0]))


# --- the declared anchor ---------------------------------------------------------------------


def test_a_probe_under_a_new_label_is_not_ranked_as_an_axis():
    df = make_frame(axes={"a": [1.0, 2.0], "flat": [9.0, 10.0]})
    default = an.summarise_axes(df, n_bootstrap=0)
    assert not bool(_axis(default, "flat")["is_probe"]), "undeclared, a new label is an axis"
    declared = an.summarise_axes(df, n_bootstrap=0, probe_labels=frozenset({"flat"}))
    row = _axis(declared, "flat")
    assert bool(row["is_probe"]) and np.isnan(row["rho"]), (
        "an anchor declared non-ordinal was scored as a monotone axis")


def test_probe_summary_follows_the_declared_anchor():
    df = make_frame(axes={"a": [2.0, 5.0], "gaussian_impostor": [5.0], "flat": [10.0, 10.0]})
    labels = frozenset({"gaussian_impostor", "flat"})
    norm = an.normalisation(df, uncorrelated_label="flat", probe_labels=labels)
    row = an.probe_summary(df, norm, uncorrelated_label="flat", probe_labels=labels).iloc[0]
    assert row["flat_damage"] == pytest.approx(1.0)
    assert "flat_nearest_level" not in row.index, "the anchor's nearest level carries nothing"
    assert row["gaussian_impostor_nearest_level"] == "a=2"


def test_run_labels_fall_back_for_folders_that_predate_the_declaration():
    assert an.run_labels({}) == ("uncorrelated", an.PROBE_LABELS)
    declared = an.run_labels({"anchor_label": "flat", "probe_labels": ["flat"]})
    assert declared == ("flat", frozenset({"flat"}))
    assert an.run_labels({}, {"analysis": {"anchor": "flat"}})[0] == "flat"


def test_analyse_follows_the_run_declaration():
    df = make_frame(axes={"a": [1.0, 2.0], "flat": [10.0, 10.0]})
    result = an.analyse(df, meta={"anchor_label": "flat", "probe_labels": ["flat"]},
                        n_bootstrap=0)
    assert result.anchor_label == "flat" and result.probe_labels == frozenset({"flat"})
    assert result.norm.iloc[0]["anchor_source"] == "flat"
    assert bool(_axis(result.axes, "flat")["is_probe"])


def test_impostor_relative_response_is_a_fraction_of_the_largest_ladder_response():
    df = make_frame(n_frames=6, axes={"gaussian_blur": [0.1, 0.3], "gaussian_impostor": [0.15],
                                      "uncorrelated": [1.5e-16] * 3})
    row = an.probe_summary(df, an.normalisation(df)).iloc[0]
    assert row["gaussian_impostor_relative"] == pytest.approx(0.5)


# --- the bound is two-sided and paired within each frame -------------------------------------


def _single_field(axes: dict, clean: float = 5.0, drift: float = 1.0, n_frames: int = 40,
                  noise: float = 1e-3) -> pd.DataFrame:
    """A single-field quantity: nonzero clean value, anchor equal to clean (no damage scale),
    optionally drifting along the trajectory by a factor ``drift`` per frame."""
    df = make_frame(axes={**axes, "uncorrelated": [0.0, 0.0]}, n_frames=n_frames, noise=noise)
    df["value"] = (df["value"] + clean) * drift ** df["frame_index"]
    # A translated copy has exactly the clean value of a single-field quantity in every frame.
    clean_by_frame = df[df["level"] == 0].set_index("frame_index")["value"]
    anchor = df["degradation"] == "uncorrelated"
    df.loc[anchor, "value"] = df.loc[anchor, "frame_index"].map(clean_by_frame).to_numpy()
    return df


def test_a_response_that_falls_is_not_reported_as_blindness():
    """Equivalence is two-sided: a large fall is a response. A one-sided bound would list
    enstrophy's high-pass response on the pinned run (a bound of -1.13) as provably below 0.05."""
    axes = an.analyse(_single_field({"falls": [-1.0, -2.0, -3.0, -4.0], "flat": [0.0] * 4}),
                      n_bootstrap=100).axes
    assert _axis(axes, "falls")["blindness_q"] == pytest.approx(1.0)
    assert _axis(axes, "falls")["damage_max_ucb"] > an.BLINDNESS_MARGIN
    assert _axis(axes, "flat")["blindness_q"] < an.FDR_LEVEL


def test_the_relative_bound_is_paired_within_each_frame():
    """A quantity that drifts along the trajectory (enstrophy decays) must be compared with its own
    clean value in the same frame. Against the trajectory's median clean value, the drift itself
    reads as a response and an axis that changes nothing is not found blind."""
    axes = an.analyse(_single_field({"responds": [-1.0, -2.0, -3.0, -4.0], "nothing": [0.0] * 4},
                                    drift=1.05), n_bootstrap=100).axes
    assert _axis(axes, "nothing")["blindness_q"] < an.FDR_LEVEL, "the drift is not a response"
    assert _axis(axes, "responds")["blindness_q"] == pytest.approx(1.0)


def test_negative_damage_on_an_error_metric_is_a_response():
    df = make_frame(axes={"below": [-3.0] * 4, "uncorrelated": [10.0, 10.0]}, noise=1e-3,
                    n_frames=40)
    assert _axis(an.analyse(df, n_bootstrap=100).axes, "below")["blindness_q"] == pytest.approx(1.0)


def test_impostor_relative_response_is_paired_within_each_frame():
    df = _single_field({"blur": [-1.0, -2.0], "gaussian_impostor": [0.0]}, drift=1.05)
    row = an.probe_summary(df, an.normalisation(df)).iloc[0]
    assert abs(row["gaussian_impostor_relative"]) < 1e-2, (
        "an impostor that changes nothing in any frame has no relative response, drift or not")


# --- selectivity, onset and severity orientation ---------------------------------------------


def test_one_outlier_frame_does_not_move_selectivity():
    """The profile is median damage over field change at the harshest level, so one frame cannot
    move it: on the pinned run, one early frame of MSE on velocity under coarsen_bandlimited alone
    would read selectivity 0.285, against 6e-7 from the medians."""
    df = _profile_frame({"a": 1.0, "b": 1.0, "c": 1.0})
    spike = (df["degradation"] == "b") & (df["level"] == 4) & (df["frame_index"] == 0)
    df.loc[spike, "value"] *= 3.0
    card = an.analyse(df, n_bootstrap=0).card.iloc[0]
    assert card["selectivity"] == pytest.approx(0.0, abs=1e-3), (
        f"one frame of twelve moved selectivity to {card['selectivity']:.3f}")


def test_onset_is_never_below_the_mildest_strength_tested():
    """A coarsening factor's identity is 1, not 0: interpolating from a clean point at strength 0
    would print factors of 0.18 to 0.88 on the pinned run. The crossing is read between measured
    levels."""
    ladder = {"coarsen": [0.5, 0.6, 0.7, 0.8], "uncorrelated": [1.0, 1.0]}
    df = _with_severity(make_frame(axes=ladder), "coarsen", {1: 2.0, 2: 4.0, 3: 8.0, 4: 16.0})
    scored, norm = _scored(df)
    row = _axis(an.summarise_axes(scored, norm=norm, n_bootstrap=0), "coarsen")
    assert row["severity_10"] == 2.0


def test_damage_profile_is_withheld_for_a_target_valued_metric():
    df = _profile_frame({"a": 1.0, "b": 10.0})
    df["target_value"] = 1.0
    card = an.analyse(df, n_bootstrap=0).card.iloc[0]
    assert np.isnan(card["selectivity"]) and pd.isna(card["most_sensitive_axis"])


def test_a_falling_response_has_an_elasticity():
    """A single-field quantity falls under smoothing; the exponent of the size of that fall is as
    meaningful as that of a rise, and the ``direction`` column gives which way it went."""
    axes = an.summarise_axes(_single_field({"falls": [-1.0, -2.0, -3.0, -4.0]}, drift=1.05),
                             n_bootstrap=0)
    row = _axis(axes, "falls")
    assert row["elasticity"] == pytest.approx(1.0, abs=0.02)
    assert row["response_shape"] == "linear"


def test_a_retained_fraction_is_read_as_the_fraction_removed():
    """band_attenuate's severity is the fraction of a band retained, falling to 0 at its harshest
    level. Read through its reciprocal, that level would be infinite and drop out of the onset and
    the slope; its complement, the fraction removed, is finite and rises with damage."""
    df = _with_severity(make_frame(axes={"band": [0.01, 0.02, 0.05, 0.5],
                                         "uncorrelated": [1.0, 1.0]}),
                        "band", {1: 0.8, 2: 0.5, 3: 0.2, 4: 0.0})
    scored, norm = _scored(df)
    row = _axis(an.summarise_axes(scored, norm=norm, n_bootstrap=0), "band")
    assert row["elasticity_x"] == "1 - severity (s)"
    assert 0.8 < row["severity_10"] <= 1.0, "the crossing lies at the harshest level"


# --- the trend rule: a departure from clean, in one measured direction per degradation -----


_TREND = ("rho", "rho_frame_min", "monotone_fraction", "separability_auc_min", "cliffs_delta_min")


def test_scatter_around_clean_scores_far_below_a_real_response():
    """A response that only scatters, more widely at each level, is not a trend (the design's D1).

    Ranking the *absolute* departure would pick a sign per point and read this null as ordered,
    because the spread grows with the level. One sign per degradation cannot follow the scatter.
    """
    rng = np.random.default_rng(3)
    df = _single_field({"scatter": [0.0] * 4, "real": [0.1, 0.2, 0.3, 0.4]}, n_frames=80)
    null = (df["degradation"] == "scatter").to_numpy()
    df.loc[null, "value"] += (10.0 ** df.loc[null, "level"] * 1e-4
                              * rng.standard_normal(int(null.sum())))
    axes = an.summarise_axes(df, n_bootstrap=0)
    scatter, real = _axis(axes, "scatter"), _axis(axes, "real")
    assert real["rho"] == pytest.approx(1.0) and real["monotone_fraction"] == pytest.approx(1.0)
    assert abs(scatter["rho"]) < 0.5 and scatter["monotone_fraction"] < 0.3, (
        f"a pure scatter null scored rho={scatter['rho']:.2f}, monotone fraction "
        f"{scatter['monotone_fraction']:.2f}; the trend is reading scatter as order")


def test_a_falling_and_a_rising_response_both_follow_their_degradation():
    """Which way a metric moves carries no weight (D6): falling under one degradation and rising
    under another both score a perfect trend, and ``direction`` records which it was."""
    axes = an.summarise_axes(_single_field({"blur": [-0.4, -0.8, -1.2, -1.6],
                                            "noise": [0.4, 0.8, 1.2, 1.6]}), n_bootstrap=0)
    for label, sign in (("blur", -1), ("noise", 1)):
        row = _axis(axes, label)
        assert row["direction"] == sign, f"{label}: direction {row['direction']}, expected {sign}"
        for column in _TREND:
            assert row[column] == pytest.approx(1.0), f"{label}: {column} = {row[column]}"


def test_a_steady_response_that_crosses_its_clean_value_follows_the_trend():
    """The clean level is not a point of the trend (D9). Palinstrophy under coarsening moves
    +77%, +20%, -25%, -53% from clean on the pinned run: steadily one way, through clean."""
    df = _single_field({"coarsen": [0.77 * 5, 0.20 * 5, -0.25 * 5, -0.53 * 5]})
    row = _axis(an.summarise_axes(df, n_bootstrap=0), "coarsen")
    assert row["direction"] == -1
    assert row["rho"] == pytest.approx(1.0) and row["monotone_fraction"] == pytest.approx(1.0)


def test_a_two_field_error_metric_is_unchanged_by_the_departure_rule():
    """An error metric is exactly zero on the clean field, so its departure is its value and its
    direction +1: every trend statistic equals the one computed on the raw values."""
    df = make_frame(axes={"a": [1.0, 2.0, 2.5, 4.0]}, noise=0.4, n_frames=30, seed=4)
    ladder = df[df["level"] > 0]
    row = _axis(an.summarise_axes(df, n_bootstrap=0))
    rho = np.nanmedian(list(an._per_frame_rho(ladder).values()))
    assert row["direction"] == 1
    assert row["rho"] == pytest.approx(rho, rel=1e-12)
    assert row["monotone_fraction"] == pytest.approx(an._monotone_fraction(ladder), rel=1e-12)
    assert row["separability_auc_min"] == pytest.approx(an._min_adjacent_auc(ladder), rel=1e-12)


@pytest.mark.parametrize("transform", [np.log, np.sqrt, lambda v: -1.0 / v, lambda v: np.exp(-v)],
                         ids=["log", "sqrt", "minus-reciprocal", "decreasing-exp"])
def test_a_monotone_re_expression_leaves_the_trend_unchanged(transform):
    """A metric and any monotone function of it, increasing or decreasing, carry the same trend.

    Holds exactly for the statistics read within a frame. Those pooled over frames
    (separability, Cliff's delta) compare departures from different frames' clean values, which a
    non-linear map can reorder when the clean value drifts; on an error metric, whose clean value
    is the same zero in every frame, they are invariant too (the second case below).
    """
    single = _single_field({"a": [-0.5, -1.0, -1.5, -2.0]}, drift=1.02, noise=0.05)
    error = make_frame(axes={"a": [1.0, 2.0, 2.5, 4.0]}, noise=0.4, n_frames=30, seed=4)
    error["value"] += 1.0      # keep the log and the reciprocal finite; clean is 1 everywhere
    for df, columns in ((single, ("rho", "rho_frame_min", "monotone_fraction")), (error, _TREND)):
        before = _axis(an.summarise_axes(df, n_bootstrap=0))
        after = _axis(an.summarise_axes(df.assign(value=transform(df["value"])), n_bootstrap=0))
        for column in columns:
            assert after[column] == pytest.approx(before[column], rel=1e-12), (
                f"{column}: {before[column]} became {after[column]} under a monotone map")


def test_relative_change_is_measured_from_the_clean_value_of_the_same_frame():
    """Equation (2): ``(v - v0) / |v0|``. Defined for a single-field quantity, absent for an error
    metric whose clean value is zero."""
    single = _single_field({"a": [0.5, 1.0, 2.5]}, clean=5.0, drift=1.1, noise=0.0)
    row = _axis(an.summarise_axes(single, n_bootstrap=0))
    assert row["relative_change_max"] == pytest.approx(0.5, rel=1e-9), "drift cancels per frame"
    scored, _ = _scored(single)
    curve = an.per_level_response(scored, metric="m")
    assert curve.loc[curve["degradation"] == "a", "relative_change_median"].to_numpy() == \
        pytest.approx([0.1, 0.2, 0.5], rel=1e-9)
    error = _axis(an.summarise_axes(make_frame(axes={"a": [1.0, 2.0]}), n_bootstrap=0))
    assert np.isnan(error["relative_change_max"]), "an error metric's clean value is zero"
