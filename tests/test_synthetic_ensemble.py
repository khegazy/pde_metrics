"""The synthetic ensemble reader.

This dataset exists so probabilistic metrics have a case whose right answer is known in
closed form. That rests entirely on one property -- **exchangeability**: the reference is
drawn from the same process as every member, with the same dispersion, independently. It
is then statistically just one more member, so a calibrated ensemble is the null
hypothesis by construction: rank histograms are uniform, the spread-to-skill ratio is 1,
and CRPS matches the Gaussian closed form.

The tests below check that property directly, at the reader level, without involving any
metric. When a probabilistic metric later disagrees with its analytic target, this file is
what says whether the generator or the metric is at fault.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import integrate, special, stats

from degradations import registry as deg
from fmeval.data.base import READERS
from fmeval.data.synthetic_ensemble import SyntheticEnsembleTrajectory
from fmeval.ladder import build_ladder
from metrics.crps.metric import crps
from metrics.ensemble_mean_rmse.metric import ensemble_mean_rmse
from metrics.variogram_score.metric import variogram_score
from tests.conftest import make_ctx, run_metrics

GRID = (16, 8)
N_MEMBERS = 12


@pytest.fixture
def traj() -> SyntheticEnsembleTrajectory:
    return SyntheticEnsembleTrajectory(
        grid=GRID, n_members=N_MEMBERS, n_frames=6, fields=("density",), sigma=0.2, seed=0
    )


# --- registration and the reader contract -------------------------------------------


def test_is_registered():
    assert READERS["synthetic_ensemble"] is SyntheticEnsembleTrajectory


def test_declares_itself_an_ensemble(traj):
    assert traj.is_ensemble is True


def test_frame_shapes(traj):
    frame = traj.frame(2, ["density"])
    assert frame.fields["density"].shape == (1, *GRID)
    assert frame.members["density"].shape == (N_MEMBERS, 1, *GRID)
    assert frame.members["density"].dtype == np.float64


def test_length_and_times(traj):
    assert len(traj) == 6
    assert traj.times.shape == (6,)


def test_grid_is_periodic_and_non_square(traj):
    assert traj.grid.shape == GRID
    assert traj.grid.boundary == ("periodic", "periodic")


def test_meta_records_ensemble_size(traj):
    assert traj.meta["n_members"] == N_MEMBERS
    assert traj.meta["format"] == "synthetic_ensemble"


def test_supports_multi_channel_fields():
    traj = SyntheticEnsembleTrajectory(
        grid=GRID, n_members=4, n_frames=2, fields=("density", "velocity"), seed=0
    )
    frame = traj.frame(0, ["density", "velocity"])
    assert frame.fields["velocity"].shape == (2, *GRID)
    assert frame.members["velocity"].shape == (4, 2, *GRID)


# --- reproducibility -----------------------------------------------------------------


def test_is_reproducible_from_the_seed(traj):
    other = SyntheticEnsembleTrajectory(
        grid=GRID, n_members=N_MEMBERS, n_frames=6, fields=("density",), sigma=0.2, seed=0
    )
    a, b = traj.frame(3, ["density"]), other.frame(3, ["density"])
    assert np.array_equal(a.fields["density"], b.fields["density"])
    assert np.array_equal(a.members["density"], b.members["density"])


def test_a_different_seed_gives_different_draws(traj):
    other = SyntheticEnsembleTrajectory(
        grid=GRID, n_members=N_MEMBERS, n_frames=6, fields=("density",), sigma=0.2, seed=1
    )
    a, b = traj.frame(3, ["density"]), other.frame(3, ["density"])
    assert not np.allclose(a.members["density"], b.members["density"])


def test_frames_are_independent_draws(traj):
    """Per-frame Spearman needs frames that genuinely differ, not a repeated field."""
    a = traj.frame(1, ["density"])["density"]
    b = traj.frame(2, ["density"])["density"]
    assert not np.allclose(a, b)


def test_members_within_a_frame_are_distinct(traj):
    members = traj.frame(1, ["density"]).members["density"]
    assert not np.allclose(members[0], members[1])


# --- the exchangeability property the analytic targets rest on -----------------------


def test_reference_is_not_the_member_mean(traj):
    """The truth is an independent draw, not the ensemble mean. Documented, and true."""
    frame = traj.frame(1, ["density"])
    assert not np.allclose(
        frame.fields["density"], frame.members["density"].mean(axis=0), atol=1e-8
    )


def test_rank_of_the_reference_is_uniform(traj):
    """Exchangeability, tested where it bites: the rank histogram must be flat.

    Pools every cell of every frame. Under exchangeability the reference is equally
    likely to fall in any of the N+1 gaps between sorted members, so a chi-square
    goodness-of-fit against the uniform must not reject. A generator that drew the
    reference with a different sigma -- the easiest mistake to make here -- produces a
    U-shaped or dome-shaped histogram and fails loudly.
    """
    counts = np.zeros(N_MEMBERS + 1, dtype=int)
    for t in range(len(traj)):
        frame = traj.frame(t, ["density"])
        ref = frame.fields["density"]
        members = frame.members["density"]
        ranks = (members < ref[None]).sum(axis=0)
        counts += np.bincount(ranks.ravel(), minlength=N_MEMBERS + 1)

    expected = counts.sum() / (N_MEMBERS + 1)
    _, p = stats.chisquare(counts, f_exp=np.full(N_MEMBERS + 1, expected))
    assert p > 0.01, f"rank histogram is not uniform (p={p:.4g}); counts={counts}"


def test_spread_matches_skill(traj):
    """The other face of exchangeability: RMS spread equals ensemble-mean RMSE.

    Computed here with the Fortin et al. (2014) estimator and the finite-ensemble
    factor sqrt((N+1)/N) that relates the two under exchangeability, so this is a check
    on the generator, not on any metric implementation.
    """
    variances, sq_errors = [], []
    for t in range(len(traj)):
        frame = traj.frame(t, ["density"])
        members = frame.members["density"]
        variances.append(members.var(axis=0, ddof=1))
        sq_errors.append((members.mean(axis=0) - frame.fields["density"]) ** 2)

    spread = np.sqrt(np.mean(variances))
    skill = np.sqrt(np.mean(sq_errors))
    ratio = spread / skill * np.sqrt((N_MEMBERS + 1) / N_MEMBERS)
    assert ratio == pytest.approx(1.0, abs=0.05), f"spread/skill is {ratio:.4g}, not ~1"


def test_sigma_controls_the_dispersion():
    """A larger sigma must widen the ensemble, so the knob is real and monotone."""
    spreads = []
    for sigma in (0.1, 0.4):
        traj = SyntheticEnsembleTrajectory(
            grid=GRID, n_members=8, n_frames=3, fields=("density",), sigma=sigma, seed=0
        )
        members = traj.frame(1, ["density"]).members["density"]
        spreads.append(np.sqrt(members.var(axis=0, ddof=1).mean()))
    assert spreads[1] > 2 * spreads[0]


# --- the options of dataset_specs/08_synthetic_ensemble_extensions.md -----------------------
#
# Each known answer below is the spec's, checked through the repository's own metrics. A
# statistical answer is asserted within four standard errors measured from the frames, each
# frame being an independent draw; the seeds are fixed, so every test is deterministic.


def _frames(traj: SyntheticEnsembleTrajectory) -> list[tuple[np.ndarray, np.ndarray]]:
    """Every frame's ``(truth, members)`` for density."""
    return [(f["density"], f["density__members"])
            for f in (traj.read_frame(t, ["density"]) for t in range(len(traj)))]


def _expected_abs_normal(m: float, v: float) -> float:
    """E|N(m, v)| = m (2 Phi(m / sqrt v) - 1) + 2 sqrt(v) phi(m / sqrt v)."""
    z = m / np.sqrt(v)
    return m * (2 * stats.norm.cdf(z) - 1) + 2 * np.sqrt(v) * stats.norm.pdf(z)


def test_a_sigma_profile_puts_each_cell_on_the_diagonal_of_the_binned_diagram():
    """``sigma_ratio`` (spec 08, Eq. 3) keeps truth and members exchangeable cell by cell, so
    binned by the true noise level the ensemble-mean error is sqrt((M + 1)/M) sigma(x) in every
    bin (Leutbecher & Palmer 2008, J. Comput. Phys. 227(7):3515, Sect. 2.2): the log-log slope
    of error against that spread is one."""
    m = 16
    traj = SyntheticEnsembleTrajectory(grid=(64, 64), n_members=m, n_frames=12, sigma=0.05,
                                       sigma_ratio=4.0)
    w = 0.5 * (1 + np.sin(2 * np.pi * np.arange(64) / 64))
    sigma = np.broadcast_to((0.05 * 4.0**w)[:, None], (64, 64)).ravel()
    err2 = np.concatenate([((ens.mean(axis=0) - y) ** 2).ravel() for y, ens in _frames(traj)])
    bins = np.array_split(np.argsort(np.tile(sigma, len(traj)), kind="stable"), 20)
    spread = [np.sqrt((m + 1) / m) * np.tile(sigma, len(traj))[b].mean() for b in bins]
    error = [np.sqrt(err2[b].mean()) for b in bins]
    assert np.polyfit(np.log(spread), np.log(error), 1)[0] == pytest.approx(1.0, abs=0.05)


def test_correlated_noise_has_the_declared_covariance():
    """``noise_length`` colours white noise into a field with covariance exp(-r / l)
    (Scheuerer & Hamill 2015, Eq. 5) and unit variance per cell. Lag correlations pooled over
    the 17 draws of four 64^2 frames, against the closed form; the sampling error of each is
    below 0.01 here."""
    traj = SyntheticEnsembleTrajectory(grid=(64, 64), n_members=16, n_frames=4, base="zero",
                                       sigma=1.0, noise_length=3.0)
    draws = np.concatenate([np.concatenate([y[None], ens]) for y, ens in _frames(traj)])
    assert draws.var() == pytest.approx(1.0, abs=0.03)
    for lag in (1, 2, 4):
        measured = np.mean(draws * np.roll(draws, lag, axis=-2))
        assert measured == pytest.approx(np.exp(-lag / 3.0), abs=0.03), lag


def test_a_covariance_that_is_not_positive_definite_is_refused():
    with pytest.raises(ValueError, match="positive definite"):
        SyntheticEnsembleTrajectory(grid=(8, 8), base="zero", noise_length=40.0,
                                    noise_covariance="rational")


def test_the_positive_variant_keeps_every_rank():
    """``log_amplitude`` applies a monotone map to truth and members, so the rank of the truth
    among the members is the same in every cell (spec 08, Sect. 3.6, item 1), and the field is
    positive."""
    kw = dict(grid=GRID, n_members=N_MEMBERS, n_frames=2, sigma=0.2, seed=0)
    plain, positive = (SyntheticEnsembleTrajectory(**kw, log_amplitude=lam) for lam in (0, 0.1))
    for (y0, m0), (y1, m1) in zip(_frames(plain), _frames(positive)):
        assert (y1 > 0).all() and (m1 > 0).all()
        np.testing.assert_array_equal((m0 < y0).sum(axis=0), (m1 < y1).sum(axis=0))


def test_a_member_offset_moves_only_the_members():
    """``member_offset`` shifts the members by delta sigma and leaves the truth's draw alone."""
    kw = dict(grid=GRID, n_members=N_MEMBERS, n_frames=1, sigma=0.2, seed=0)
    (y0, m0), = _frames(SyntheticEnsembleTrajectory(**kw))
    (y1, m1), = _frames(SyntheticEnsembleTrajectory(**kw, member_offset=1.0))
    np.testing.assert_array_equal(y0, y1)
    np.testing.assert_allclose(m1 - m0, 0.2, rtol=1e-12)


#: Exact expected CRPS of the four forecasters of Gneiting, Balabdaoui & Raftery (2007, JRSS-B
#: 69(2):243, Table 1), from the kernel form CRPS = E|X - y| - E|X - X'| / 2 (spec 08, Eq. 2).
GNEITING_CRPS = {
    "ideal": _expected_abs_normal(0, 2) / 2,                              # 1/sqrt(pi) = 0.5642
    "hamill": np.mean([_expected_abs_normal(d, s2 + 1) - _expected_abs_normal(0, 2 * s2) / 2
                       for d, s2 in ((0.5, 1.0), (-0.5, 1.0), (0.0, 1.69))]),          # 0.6144
    "unfocused": (_expected_abs_normal(0, 2) + _expected_abs_normal(1, 2)) / 4,       # 0.6319
    "climatological": _expected_abs_normal(0, 4) / 2,                     # sqrt(2/pi) = 0.7979
}


def test_the_gneiting_forecasters_score_their_exact_crps():
    """The ideal forecaster is the clean ensemble of ``base: case_means, sigma: 1``; the other
    three are ``gneiting_forecaster`` probes run through the ladder. Each mean over 12 frames
    of 64^2 cases (16 members) lies within four standard errors of the exact value. The
    standard error, about 0.0025, is measured from the frames; it is smaller than the gaps
    between the four values, so the test also fixes their order. Gneiting et al.'s Table 5
    reports 0.56, 0.61, 0.63 and 0.78 from 10 000 cases."""
    assert [round(GNEITING_CRPS[k], 4) for k in GNEITING_CRPS] == [0.5642, 0.6144, 0.6319, 0.7979]
    traj = SyntheticEnsembleTrajectory(grid=(64, 64), n_members=16, n_frames=12,
                                       base="case_means", sigma=1.0)
    ladder = build_ladder({kind: {"op": "gneiting_forecaster", "severities": [0],
                                  "options": {"kind": kind}}
                           for kind in ("hamill", "unfocused", "climatological")},
                          include_reference=True)
    rows = run_metrics(traj, ["crps"], ladder).rows
    for kind, exact in GNEITING_CRPS.items():
        values = rows.loc[rows["degradation"] == ("identity" if kind == "ideal" else kind),
                          "value"].to_numpy()
        assert len(values) == 12, kind
        standard_error = values.std(ddof=1) / np.sqrt(len(values))
        assert abs(values.mean() - exact) < 4 * standard_error, (kind, values.mean(), exact)


@pytest.mark.parametrize("op, options, severities", [
    ("flow_dependence", {"direction": "damp"}, [0.5, 1.0, 2.0]),
    ("flow_dependence", {"direction": "amplify"}, [1.0]),
    ("member_shape", {"family": "student_t"}, [0.1, 0.4]),
    ("member_shape", {"family": "two_piece"}, [0.2, 0.8]),
])
def test_mean_preserving_operators_leave_spread_skill_and_ensemble_mean_rmse_unchanged(
        op, options, severities):
    """Both operators keep the ensemble mean cell by cell and the frame's mean sample variance
    (``member_shape`` every cell's variance), so ``ensemble_mean_rmse`` and ``spread_skill``
    are unchanged to round-off in every frame (spec 08, Sects. 3.2 and 3.4), while ``crps``
    moves."""
    traj = SyntheticEnsembleTrajectory(grid=(32, 32), n_members=16, n_frames=3, sigma=0.05,
                                       sigma_ratio=4.0)
    ladder = build_ladder({op: {"severities": severities, "options": options}},
                          include_reference=True)
    rows = run_metrics(traj, ["ensemble_mean_rmse", "spread_skill", "crps"], ladder).rows
    for metric in ("ensemble_mean_rmse", "spread_skill", "crps"):
        table = rows[rows["metric"] == metric].pivot(index="frame_index", columns="level",
                                                     values="value")
        clean, degraded = table[0].to_numpy()[:, None], table.drop(columns=0).to_numpy()
        if metric == "crps":
            assert (np.abs(degraded - clean) > 1e-6 * clean).all(), (op, options)
        else:
            np.testing.assert_allclose(degraded, np.broadcast_to(clean, degraded.shape),
                                       rtol=1e-12, err_msg=f"{op} {options} {metric}")


def test_flow_dependence_divides_the_binned_spread_error_slope_by_its_exponent():
    """Leutbecher & Palmer's diagram (2008, Sect. 2.2): 20 equally populated bins of the
    members' per-cell spread, log RMS ensemble-mean error against log sqrt((M + 1)/M) times
    the bin's RMS spread. ``flow_dependence`` maps each spread to k s^a monotonically and
    keeps every error, so the bins keep their cells and the slope becomes the calibrated slope
    over a (spec 08, Sect. 3.2, item 3); a < 0 reverses the bins. Asserted to 1%: within a bin
    the RMS of k s^a is k (RMS s)^a only approximately, which costs 0.3% here (measured). At
    a = 0 (damp 1) every cell of a frame carries the same spread. The calibrated slope, about
    0.87, is below one because large sample spreads overstate the true one."""
    m = 16
    traj = SyntheticEnsembleTrajectory(grid=(64, 64), n_members=m, n_frames=12, sigma=0.05,
                                       sigma_ratio=4.0)
    frames = _frames(traj)
    flow = deg.get("flow_dependence").fn
    err2 = np.concatenate([((ens.mean(axis=0) - y) ** 2).ravel() for y, ens in frames])

    def slope(spread: np.ndarray) -> float:
        bins = np.array_split(np.argsort(spread, kind="stable"), 20)
        x = [np.sqrt((m + 1) / m * np.mean(spread[b] ** 2)) for b in bins]
        return float(np.polyfit(np.log(x), np.log([np.sqrt(err2[b].mean()) for b in bins]),
                                1)[0])

    calibrated = slope(np.concatenate([ens.std(axis=0, ddof=1).ravel() for _, ens in frames]))
    assert 0.8 < calibrated < 0.95
    for direction, severity, a in (("damp", 0.5, 0.5), ("damp", 2.0, -1.0),
                                   ("amplify", 1.0, 2.0)):
        spread = np.concatenate([flow(ens, severity, direction=direction).std(axis=0, ddof=1)
                                 .ravel() for _, ens in frames])
        assert slope(spread) * a == pytest.approx(calibrated, rel=0.01), (direction, severity)
    for _, ens in frames:
        flat = flow(ens, 1.0, direction="damp").std(axis=0, ddof=1)
        np.testing.assert_allclose(flat, flat.flat[0], rtol=1e-10)


def test_variogram_score_sees_a_wrong_correlation_that_the_per_cell_scores_do_not():
    """Truth with exp(-r / 3) noise; a calibrated ensemble with the same, and one whose members
    are independent cell by cell (Scheuerer & Hamill 2015, Sect. 3b, the experiment on a
    32^2 grid). Every member's marginal at every cell is N(0, 1) in both, so ``crps`` and
    ``ensemble_mean_rmse`` have equal expectations (spec 08, Sect. 3.3, item 1), while
    ``variogram_score`` must rise. The two runs share the truth and every white-noise draw, so
    the frames are paired: the variogram score's paired t statistic must exceed 5 (measured
    7.0 over 12 frames), and the per-cell scores' must stay below 3 in magnitude, the 99.3%
    range of a t distribution with 11 degrees of freedom."""
    kw = dict(grid=(32, 32), n_members=16, n_frames=12, base="zero", sigma=1.0,
              noise_length=3.0)
    calibrated = _frames(SyntheticEnsembleTrajectory(**kw))
    independent = _frames(SyntheticEnsembleTrajectory(**kw, member_noise_length=0.0))
    ctx = make_ctx((32, 32), field="density")
    scores = {"variogram_score": lambda y, ens: variogram_score(y, ens, ctx=ctx),
              "crps": crps, "ensemble_mean_rmse": ensemble_mean_rmse}
    t_stat = {}
    for name, score in scores.items():
        diff = np.array([score(y, wrong) - score(y2, right)
                         for (y, wrong), (y2, right) in zip(independent, calibrated)])
        t_stat[name] = diff.mean() / (diff.std(ddof=1) / np.sqrt(len(diff)))
    assert t_stat["variogram_score"] > 5, t_stat
    assert abs(t_stat["crps"]) < 3 and abs(t_stat["ensemble_mean_rmse"]) < 3, t_stat


def _student_t_crps(y: np.ndarray, nu: float) -> np.ndarray:
    """CRPS of the standard Student-t with nu > 1 degrees of freedom at y (Jordan, Krueger &
    Lerch 2019, J. Stat. Softw. 90(12), App. A.2.5)."""
    return (y * (2 * stats.t.cdf(y, nu) - 1)
            + 2 * stats.t.pdf(y, nu) * (nu + y**2) / (nu - 1)
            - 2 * np.sqrt(nu) * special.beta(0.5, nu - 0.5)
            / ((nu - 1) * special.beta(0.5, nu / 2) ** 2))


@pytest.mark.parametrize("severity, limit", [(0.2, 0.5666), (0.4, 0.5914)])
def test_student_t_members_score_the_closed_form_crps(severity, limit):
    """The limit ``member_shape`` approaches as M grows (spec 08, Sect. 3.4, item 3): members
    drawn from the unit-variance Student-t at nu = 1 / severity, scored against an N(0, 1)
    truth. The expected CRPS is Jordan et al.'s closed form integrated over the truth,
    0.5666 at nu = 5 and 0.5914 at nu = 2.5 against 0.5642 for the normal; the fair estimator
    is unbiased for independent members, so ``crps`` over 12 frames of 64^2 cases matches it
    within four standard errors (about 0.0015 each). The finite ``member_shape`` ensemble does
    not reach the limit at small nu (spec 08, Sect. 3.4) and is not asserted against it."""
    nu = 1.0 / severity
    scale = np.sqrt((nu - 2) / nu)
    expected = integrate.quad(lambda y: scale * _student_t_crps(y / scale, nu)
                              * stats.norm.pdf(y), -np.inf, np.inf)[0]
    assert expected == pytest.approx(limit, abs=5e-5)
    traj = SyntheticEnsembleTrajectory(grid=(64, 64), n_members=16, n_frames=12, base="zero",
                                       sigma=1.0)
    rng = np.random.default_rng(0)
    values = np.array([crps(y, scale * rng.standard_t(nu, ens.shape)) for y, ens in _frames(traj)])
    assert abs(values.mean() - expected) < 4 * values.std(ddof=1) / np.sqrt(len(values))
