"""The pure estimators behind the response statistics, on hand-built arrays with known answers.

Every function in :mod:`fmeval.stats` returns NaN on degenerate input rather than raising, so each
test pins both the value on a clean case and the refusal on a degenerate one.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import spearmanr

from fmeval import stats

# Median MSE on vorticity over the six translate_subpixel levels (0.125 ... 4 cells) of the pinned
# run results/comparison_1790639359 (kinet_re5e4, start 2000, reduction 50, 161 frames). Measured.
SUBPIXEL_SHIFT = np.array([0.125, 0.25, 0.5, 1.0, 2.0, 4.0])
SUBPIXEL_MSE_VORTICITY = np.array(
    [6.916023e-09, 2.755466e-08, 1.084920e-07, 4.063476e-07, 1.291071e-06, 2.708145e-06]
)


def _ar1(phi: float, n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = np.empty(n)
    x[0] = rng.standard_normal()
    for t in range(1, n):
        x[t] = phi * x[t - 1] + rng.standard_normal()
    return x


# --- elasticity ------------------------------------------------------------------------


def test_elasticity_recovers_a_power_law_exponent():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    assert stats.elasticity(x, x**2) == pytest.approx(2.0, abs=1e-9)
    assert stats.elasticity(x, 3 * x) == pytest.approx(1.0, abs=1e-9)
    assert stats.elasticity(x, np.full(4, 5.0)) == pytest.approx(0.0, abs=1e-9)


def test_elasticity_drops_non_positive_points_and_refuses_too_few():
    with_zero = stats.elasticity(np.array([0.0, 1, 2, 4]), np.array([0.0, 1, 4, 16]))
    assert with_zero == pytest.approx(2.0)
    assert np.isnan(stats.elasticity(np.array([1.0, 2.0]), np.array([1.0, 4.0])))
    assert np.isnan(stats.elasticity(np.array([2.0, 2.0, 2.0]), np.array([1.0, 2.0, 3.0])))


def test_elasticity_over_the_mildest_levels_recovers_the_small_shift_exponent():
    """The global slope on a saturating ladder understates the small-displacement exponent."""
    whole = stats.elasticity(SUBPIXEL_SHIFT, SUBPIXEL_MSE_VORTICITY)
    mildest = stats.elasticity(SUBPIXEL_SHIFT[:3], SUBPIXEL_MSE_VORTICITY[:3])
    assert 1.6 < whole < 1.85, f"global slope {whole:.3f}: the ladder saturates, so it is below 2"
    assert 1.9 < mildest < 2.05, f"mildest-three slope {mildest:.3f}: quadratic in a small shift"


# --- severity_at -----------------------------------------------------------------------


def test_severity_at_interpolates_log_linearly_between_positive_levels():
    x = np.array([0.0, 1.0, 2.0, 4.0])
    y = np.array([0.0, 0.1, 0.4, 1.6])
    assert stats.severity_at(x, y, 0.4) == pytest.approx(2.0)
    assert stats.severity_at(x, y, 0.2) == pytest.approx(2 ** (1 / 3))
    assert stats.severity_at(x, y, 0.05) == pytest.approx(0.5), "linear on the segment from zero"
    assert stats.severity_at(x, y, 0.0) == pytest.approx(0.0)
    assert np.isnan(stats.severity_at(x, y, 2.0)), "never reached within the ladder"


# --- fit_response_shape ----------------------------------------------------------------


def test_response_shape_names_the_generating_form():
    x = np.arange(1.0, 5.0)
    label, params = stats.fit_response_shape(x, x**2)
    assert label == "power" and params["b"] == pytest.approx(2.0, abs=1e-3)
    assert stats.fit_response_shape(x, 2 * x)[0] == "linear"
    x5 = np.arange(1.0, 6.0)
    assert stats.fit_response_shape(x5, 1 - np.exp(-x5 / 1.5))[0] == "saturating"


def test_response_shape_is_undetermined_when_only_one_candidate_can_fit():
    """Three levels admit only the line, so naming it would report a default, not a finding."""
    three = np.arange(1.0, 4.0)
    assert stats.fit_response_shape(three, three**2)[0] == "undetermined"
    assert stats.fit_response_shape(np.arange(1.0, 5.0), np.zeros(4))[0] == "undetermined"


# --- fisher_severity_resolution --------------------------------------------------------


def test_fisher_resolution_is_the_scatter_of_paired_steps_over_their_mean():
    x = np.array([1.0, 2.0, 3.0])
    clean = np.tile(x, (40, 1))
    assert np.allclose(stats.fisher_severity_resolution(x, clean), 0.0)
    noisy = clean + 0.1 * np.random.default_rng(0).standard_normal(clean.shape)
    res = stats.fisher_severity_resolution(x, noisy)
    assert res.shape == (2,)
    assert np.all((res > 0.05) & (res < 0.3)), f"expected about sqrt(2)*0.1 per step, got {res}"


def test_fisher_resolution_is_infinite_on_a_flat_noisy_step_and_undefined_on_a_flat_quiet_one():
    x = np.array([1.0, 2.0])
    flat_noisy = np.array([[0.0, 0.1], [0.0, -0.1]] * 5)       # steps +0.1, -0.1: mean exactly 0
    assert np.isinf(stats.fisher_severity_resolution(x, flat_noisy)[0])
    assert np.isnan(stats.fisher_severity_resolution(x, np.zeros((10, 2)))[0])


# --- treves_rolls_sparseness -----------------------------------------------------------


def test_treves_rolls_sparseness_runs_from_one_over_n_to_one():
    assert stats.treves_rolls_sparseness(np.ones(4)) == pytest.approx(1.0)
    assert stats.treves_rolls_sparseness(np.array([1.0, 0, 0, 0])) == pytest.approx(0.25)
    clipped = stats.treves_rolls_sparseness(np.array([-1.0, 1.0]))
    assert clipped == pytest.approx(0.5), "negative entries clip to zero"
    assert np.isnan(stats.treves_rolls_sparseness(np.array([1.0])))
    assert np.isnan(stats.treves_rolls_sparseness(np.zeros(3)))


# --- lins_ccc --------------------------------------------------------------------------


def test_lins_concordance_penalises_scale_where_spearman_does_not():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    assert stats.lins_ccc(x, x) == pytest.approx(1.0)
    assert spearmanr(x, 2 * x).statistic == pytest.approx(1.0)
    assert stats.lins_ccc(x, 2 * x) == pytest.approx(0.4), "rho_c of (x, 2x) on 1..4 is exactly 0.4"
    assert stats.lins_ccc(x, -x) < 0
    assert np.isnan(stats.lins_ccc(np.ones(4), np.ones(4)))


def test_lins_concordance_uses_pairwise_complete_entries():
    x = np.array([1.0, 2.0, np.nan, 4.0])
    assert stats.lins_ccc(x, np.array([1.0, 2.0, 3.0, 4.0])) == pytest.approx(1.0)


# --- politis_white_block_length --------------------------------------------------------


def test_block_length_is_short_for_white_noise_and_long_for_a_persistent_series():
    white = [stats.politis_white_block_length(_ar1(0.0, 400, s)) for s in range(5)]
    persistent = [stats.politis_white_block_length(_ar1(0.9, 400, s)) for s in range(5)]
    assert max(white) <= 3, f"white noise needs no blocks, got {white}"
    assert min(persistent) >= 10, f"AR(1), phi=0.9, decorrelates over ~10 steps; got {persistent}"


def test_block_length_grows_with_persistence_on_average():
    means = [np.mean([stats.politis_white_block_length(_ar1(phi, 400, s)) for s in range(10)])
             for phi in (0.0, 0.5, 0.9)]
    assert means[0] < means[1] < means[2], f"mean block lengths {means} should rise with phi"


def test_block_length_refuses_degenerate_series_and_respects_its_cap():
    assert stats.politis_white_block_length(np.full(100, 3.0)) == 1
    assert stats.politis_white_block_length(np.arange(8.0)) == 1
    with_nan = _ar1(0.9, 400, 0)
    with_nan[::7] = np.nan
    assert stats.politis_white_block_length(with_nan) >= 1
    noise = np.random.default_rng(0).standard_normal(161)
    trended = np.linspace(0.0, 10.0, 161) + noise
    assert stats.politis_white_block_length(noise) <= 3
    assert stats.politis_white_block_length(trended) >= 15, (
        "a trend has no decaying autocorrelation and inflates the block length far above that of "
        "the same noise without it (measured 1 against 22 on 161 frames) -- which is why callers "
        "remove the trend before estimating"
    )
    for s in range(5):
        assert stats.politis_white_block_length(_ar1(0.99, 60, s)) <= 60 // 4


# --- block_bootstrap -------------------------------------------------------------------


def test_block_bootstrap_draws_contiguous_blocks_covering_the_series():
    draws = list(stats.block_bootstrap(10, 3, 5, np.random.default_rng(0)))
    assert len(draws) == 5
    for idx in draws:
        assert len(idx) == 12 and idx.min() >= 0 and idx.max() < 10
        blocks = idx.reshape(4, 3)
        assert np.all(np.diff(blocks, axis=1) == 1), "each block is three consecutive frames"


def test_block_bootstrap_matches_the_existing_moving_block_construction():
    """Pinned so the rho interval, which uses this construction, cannot drift if it moves here."""
    idx = next(stats.block_bootstrap(10, 3, 1, np.random.default_rng(7)))
    starts = np.random.default_rng(7).choice(np.arange(8), size=4)
    assert np.array_equal(idx, np.concatenate([np.arange(s, s + 3) for s in starts]))
    whole = next(stats.block_bootstrap(5, 9, 1, np.random.default_rng(0)))
    assert np.array_equal(whole, np.arange(5)), "a block longer than the series is the series"
