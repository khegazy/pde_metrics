"""The datasets computed from closed-form solutions (``fmeval/data/analytic.py``).

Each test checks the solution against an independent statement of the physics, cited where
it comes from, rather than against numbers this code produced: the published exact star
state, the jump conditions across the shock, the invariants through the rarefaction, the
conservation laws, and the momentum equation itself. A wrong sign or a swapped branch fails
one of them; a test that compared the reader with a copy of its own formula would not.

Sources cited below:

* Toro (2009), *Riemann Solvers and Numerical Methods for Fluid Dynamics*, 3rd ed., Springer,
  https://doi.org/10.1007/b79761.
* Marzouk (2020), "The Sod gasdynamics problem as a tool for benchmarking face flux
  construction in the finite volume method", Scientific African 10, e00573,
  https://doi.org/10.1016/j.sciaf.2020.e00573 (arXiv:2108.01709).
* Taylor (1923), "On the decay of vortices in a viscous fluid", Phil. Mag. (6) 46(274),
  671-674, https://doi.org/10.1080/14786442308634295.
* Boffetta & Ecke (2012), "Two-dimensional turbulence", Annu. Rev. Fluid Mech. 44, 427-451,
  https://doi.org/10.1146/annurev-fluid-120710-101240.
* Porcu, Bevilacqua, Schaback & Oates (2023), "The Matern model: a journey through statistics,
  numerical analysis and machine learning", arXiv:2303.02759.
* Hill (1975), "A simple general approach to inference about the tail of a distribution",
  Ann. Stat. 3(5), 1163-1174, https://doi.org/10.1214/aos/1176343247.
* Saumier, Agueh & Khouider (2015), "An efficient numerical algorithm for the L2 optimal
  transport problem with periodic densities", IMA J. Appl. Math. 80(1), 135-157,
  https://doi.org/10.1093/imamat/hxt032 (arXiv:1009.6039).
* Kamm & Timmes (2007), "On efficient generation of numerically robust Sedov solutions",
  Los Alamos report LA-UR-07-2849, https://cococubed.com/papers/la-ur-07-2849.pdf.
* Sutherland (2010), "A new computational fluid dynamics code I: Fyris Alpha", Astrophys. Space
  Sci. 327, 173-206, arXiv:1003.0724 (the cylindrical Noh problem, Sect. 6.1.6, Tables 9, 10).
* Roy (2005), "Review of code and solution verification procedures for computational
  simulation", J. Comput. Phys. 205(1), 131-156, https://doi.org/10.1016/j.jcp.2004.10.036
  (the observed order, Eqs. 5, 7 and 8, as read for ``dataset_specs/02``).

The candidate tests check the closed-form error curves of
``dataset_specs/05_initial_conditions_and_degraded_solver_runs.md`` (Sects. 3.1 and 3.3; the
derivations there are its author's), re-derived in each test's docstring. The random-field tests
check the known statistics of ``dataset_specs/09_random_fields_known_statistics.md`` (Eqs. 2-11,
also its author's derivations), each restated where it is used. Those answers are expectations
over draws, so their tolerances are a few standard errors of a frame mean, each stated. The
transport pairs check the exact distances of ``dataset_specs/07_transport_known_answer_pairs.md``
(Eqs. 3, 5, 6 and 8), against closed forms and the exact circle solver ``circle_w2``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Sequence
from math import comb

import numpy as np
import pandas as pd
import pytest
from scipy import integrate, stats

from fmeval import CONFIGS, REPO
from fmeval.analysis import MEAN_FIELD_LABEL, observed_order
from fmeval.cards import dataset_figures
from fmeval.config import build_job, compose_config
from fmeval.data.analytic import (
    AdvectingBlobs,
    Burgers,
    ClosedFormTrajectory,
    Noh,
    RandomField,
    SedovTaylor,
    SodShockTube,
    TaylorGreen2D,
    biot_savart,
    polar,
)
from fmeval.data.base import READERS
from fmeval.data.readers import open_trajectory
from fmeval.derived import RecomputingTrajectory, helmholtz_split
from fmeval.external.kinet_spectral import divergence, spectral_derivative, spectral_vorticity
from fmeval.io import read_maps, read_results, read_run_meta
from fmeval.ladder import build_ladder
from fmeval.pipeline import DatasetInfo, parse_map_key, run
from fmeval.wavenumbers import wavenumber_magnitude
from metrics import registry as metric_registry
from metrics.shock_set_distance.metric import shock_mask, surface_distances
from metrics.vrmse.metric import EPSILON
from tests.analytic_fields import circle_w2, gaussian_mean_square
from tests.conftest import GRID

#: Every dataset config whose reader computes its frames rather than reading a file.
GENERATED = [name for name in sorted(p.stem for p in (CONFIGS / "dataset").glob("*.yaml"))
             if not name.startswith("_")
             and not READERS[compose_config(f"dataset={name}").dataset.format].reads_from_disk]

#: The quick ladder, as configs/degradation/quick.yaml; tests that need other axes say so.
QUICK = {
    "gaussian_blur": {"severities": [0.05, 0.20]},
    "translate_subpixel": {"severities": [0.5, 2.0]},
    "gaussian_impostor": {"severities": [0]},
    "uncorrelated": {"op": "random_large_translation", "severities": [0, 1, 2]},
}


@pytest.mark.parametrize("name", GENERATED)
def test_every_generated_dataset_opens_from_its_config(name):
    """The config composes, every reader option it states is accepted, and a frame reads."""
    job = build_job(compose_config(f"dataset={name}"))
    trajectory = open_trajectory(job.dataset, job.paths)
    frame = trajectory.frame(int(job.dataset.time.resolve(len(trajectory))[0]),
                             job.dataset.fields)
    assert set(frame.fields) == set(job.dataset.fields)
    assert all(np.isfinite(a).all() for a in frame.fields.values())


def test_the_analytic_datasets_are_among_the_generated_ones():
    assert {"sod_shock_tube", "taylor_green_2d"} <= set(GENERATED)


# --- Sod shock tube -------------------------------------------------------------------


#: Sod's data (the reader's defaults), and the states of the kinet runs with gamma = 2 that
#: ``docs/datasets/sod_shock_tube.md`` lists, read from their initial conditions: there the
#: denser gas is on the right and the fan head, not the shock, reaches a wall first. A formula
#: that hard-codes gamma = 1.4 or one of Sod's states passes the first case and fails the
#: second. The finer grid resolves that case's narrower fan (146 cells at t = 0.2).
SOD_CASES = {
    "sod": {},
    "kinet_gamma_2": {"gamma": 2.0, "left": (0.5, 0.1), "right": (2.0, 0.05), "grid": (8192,)},
}


@pytest.fixture(scope="module", params=list(SOD_CASES))
def sod(request) -> SodShockTube:
    return SodShockTube(**SOD_CASES[request.param])


def test_sod_star_state_matches_the_published_exact_solution():
    """Toro (2009), Table 4.3, Test 1 (Sod's data, Table 4.1): p*, u*, rho*_L, rho*_R to the
    five decimals printed. Marzouk (2020), Table 2: the fan head and tail and the shock
    speed, to the five decimals printed."""
    sod = SodShockTube()
    assert sod.star["pressure"] == pytest.approx(0.30313, abs=5e-6)
    assert sod.star["velocity"] == pytest.approx(0.92745, abs=5e-6)
    assert sod.star["density_left"] == pytest.approx(0.42632, abs=5e-6)
    assert sod.star["density_right"] == pytest.approx(0.26557, abs=5e-6)
    assert sod.speeds["head"] == pytest.approx(-1.18322, abs=5e-6)
    assert sod.speeds["tail"] == pytest.approx(-0.07027, abs=5e-6)
    assert sod.speeds["shock"] == pytest.approx(1.75216, abs=5e-6)


def test_sod_shock_satisfies_the_rankine_hugoniot_conditions(sod):
    """Mass, momentum and energy fluxes balance across the right shock in the frame moving
    with it: Toro (2009), Sect. 3.1.3, eqs. (3.42)-(3.44), written here in the lab frame as
    ``F(W*) - S W* = F(W_R) - S W_R``."""
    g, s = sod.meta["gamma"], sod.speeds["shock"]
    rho_r, p_r = sod.meta["right"]

    def balance(rho, u, p):
        energy = p / (g - 1) + 0.5 * rho * u**2
        return np.array([rho * u - s * rho,
                         rho * u**2 + p - s * rho * u,
                         (energy + p) * u - s * energy])

    star = balance(sod.star["density_right"], sod.star["velocity"], sod.star["pressure"])
    assert star == pytest.approx(balance(rho_r, 0.0, p_r), rel=1e-12, abs=1e-12)


def test_sod_rarefaction_keeps_its_invariants(sod):
    """Across the left rarefaction the flow is isentropic and the Riemann invariant
    ``u + 2a/(gamma - 1)`` is carried unchanged from the left state: the relations behind
    Toro (2009) eqs. (4.53)-(4.56), Sects. 4.4-4.5. Checked cell by cell inside the fan."""
    g, (rho_l, p_l) = sod.meta["gamma"], sod.meta["left"]
    frame = sod.frame(len(sod) - 1, ["density", "velocity", "pressure"])
    xi = (sod.centres[0] - sod.DIAPHRAGM) / frame.time
    fan = (xi > sod.speeds["head"]) & (xi < sod.speeds["tail"])
    rho, u, p = (frame[name][0][fan] for name in ("density", "velocity", "pressure"))
    a = np.sqrt(g * p / rho)
    assert fan.sum() > 100, "the fan is barely resolved, so this checks little"
    a_l = np.sqrt(g * p_l / rho_l)
    assert u + 2 * a / (g - 1) == pytest.approx(2 * a_l / (g - 1), rel=1e-12)
    assert p / rho**g == pytest.approx(p_l / rho_l**g, rel=1e-12)


def test_sod_waves_sit_where_their_speeds_put_them(sod):
    """Every cell more than one cell from a wave holds the state of its region: left state,
    fan, star left, star right, right state, separated by the fan head and tail (Toro (2009)
    eq. (4.55)), the contact at u*, and the shock (eq. (4.59)); sampled as in Sect. 4.5."""
    frame = sod.frame(len(sod) - 1, ["density", "velocity", "pressure"])
    x, t, s = sod.centres[0], frame.time, sod.speeds
    edges = [sod.DIAPHRAGM + t * s[k] for k in ("head", "tail", "contact", "shock")]
    far = np.min([np.abs(x - e) for e in edges], axis=0) > sod.grid.spacing[0]
    (rho_l, p_l), (rho_r, p_r) = sod.meta["left"], sod.meta["right"]
    expected = {
        "density": (rho_l, None, sod.star["density_left"], sod.star["density_right"], rho_r),
        "pressure": (p_l, None, sod.star["pressure"], sod.star["pressure"], p_r),
        "velocity": (0.0, None, sod.star["velocity"], sod.star["velocity"], 0.0),
    }
    region = np.searchsorted(edges, x)
    for name, values in expected.items():
        for r, value in enumerate(values):
            cells = far & (region == r)
            if value is not None:
                assert cells.sum() > 50, f"region {r} is too narrow to test"
                assert np.allclose(frame[name][0][cells], value, rtol=0, atol=1e-15), (name, r)


@pytest.mark.parametrize("case", list(SOD_CASES))
def test_sod_conserves_mass_and_energy_and_gains_momentum_from_the_pressure_difference(case):
    """The Euler equations in conservation form (Toro (2009), Sect. 3.1): with both ends at
    rest, no mass or energy crosses them, while the momentum grows at ``p_L - p_R`` per unit
    time. Integrated on 32768 cells, where point sampling misplaces each of the two
    discontinuities (the contact and the shock; the fan is continuous) by at most half a
    cell, 1.5e-5. The error is then at most that times the sum of a quantity's two jumps;
    the largest sum, density's in the gamma = 2 case, is 2.66, which bounds the error at
    4.1e-5, inside the tolerance of 1e-4."""
    fine = SodShockTube(**{**SOD_CASES[case], "grid": (32768,), "n_frames": 5})
    g, (rho_l, p_l), (rho_r, p_r) = fine.meta["gamma"], fine.meta["left"], fine.meta["right"]
    length = 1.0
    totals = []
    for t in range(len(fine)):
        f = fine.frame(t, ["density", "velocity", "pressure"])
        rho, u, p = f["density"][0], f["velocity"][0], f["pressure"][0]
        totals.append([rho.mean() * length, (rho * u).mean() * length,
                       (p / (g - 1) + 0.5 * rho * u**2).mean() * length, f.time])
    mass0 = 0.5 * (rho_l + rho_r)
    energy0 = 0.5 * (p_l + p_r) / (g - 1)
    for mass, momentum, energy, time in totals:
        assert mass == pytest.approx(mass0, abs=1e-4)
        assert energy == pytest.approx(energy0, abs=1e-4)
        assert momentum == pytest.approx((p_l - p_r) * time, abs=1e-4)


@pytest.mark.parametrize("kwargs, match", [
    ({"t_end": 0.29}, "reaches a boundary"),
    # The fan head reaches x = 0 first, at t = 0.5 / a_L = 0.79: the other branch of the check.
    ({"gamma": 2.0, "left": (0.5, 0.1), "right": (2.0, 0.05), "t_end": 0.8},
     "reaches a boundary"),
    ({"left": (1.0, 0.1), "right": (0.125, 1.0)}, "must exceed"),
    ({"t_start": 0.0}, "positive"),
    ({"gamma": 1.0}, "gamma"),
    ({"left": (-1.0, 1.0)}, "positive"),
    ({"time_offset": -0.1}, "positive"),
    ({"time_offset": 0.09}, "reaches a boundary"),
    ({"candidate": {"time_offset": 0.09}}, "reaches a boundary"),
    ({"candidate": {"t_end": 0.15}}, "not parameters"),
])
def test_sod_refuses_a_case_its_closed_form_does_not_cover(kwargs, match):
    with pytest.raises(ValueError, match=match):
        SodShockTube(**kwargs).predictions()


@pytest.mark.parametrize("dt", [0.001, 0.003, 0.01])
def test_sod_at_a_shifted_time_moves_the_shock_by_its_speed_and_keeps_its_jumps(dt):
    """The exact solution at t + dt against the one at t, scored through the pipeline at four
    times on 2048 cells (``proposals/EXP-sod_evidence-sod-time-offset.md``; spec 03, Sect. 3.6).

    The shock sits at x_s = 0.5 + S_R t (Toro (2009) eq. (4.59)); the detector flags the two cells
    straddling it, i and i + 1 with i = floor(x_s / dx - 1/2), and nothing else (the contact has
    no pressure jump, the fan no jump at all). The candidate's pair is s = i(t + dt) - i(t) cells
    further right, so ``shock_set_distance`` is (s - 1/2) dx and ``shock_set_hausdorff`` s dx
    exactly (the card's Eq. 3), and s dx is S_R dt to within one cell, S_R dt being 3.6, 10.8 and
    35.9 cells here. The jumps keep their exact sizes, which ``max_error`` reads: between the two
    shock positions the pressure differs by p* - p_R and the velocity by u*, while the fan, the
    only other place the two differ, differs by less (at most 0.101 in pressure and 0.089 in
    velocity, at dt = 0.01 and t = 0.1, measured; the fan widens as t, so its difference falls
    with t) and the contact moves no pressure or velocity. So
    ``max_error`` is the shock's jump at every offset, unchanged as the displacement grows: the
    double penalty in its plainest form. Exact multiples of dx and differences of the exact
    states; tolerance 1e-12."""
    truth = SodShockTube(n_frames=4, candidate={"time_offset": dt})
    rows = run(truth, [metric_registry.get(n) for n in
                       ("shock_set_distance", "shock_set_hausdorff", "max_error")],
               build_ladder({}), fields=["pressure", "velocity"],
               dataset=DatasetInfo(name="sod_shock_tube"), prediction=truth.predictions()).rows
    assert (rows.loc[rows["degradation"] == "identity", "value"] == 0).all()
    forecast = rows[rows["degradation"] == "forecast"]
    pressure = forecast[forecast["field"] == "pressure"].pivot(index="time", columns="metric",
                                                               values="value")
    dx, speed, t = truth.grid.spacing[0], truth.speeds["shock"], pressure.index.to_numpy()
    cell = np.floor((0.5 + speed * np.stack([t, t + dt])) / dx - 0.5)
    s = cell[1] - cell[0]
    assert np.abs(s * dx - speed * dt).max() <= dx
    assert pressure["shock_set_distance"].to_numpy() == pytest.approx((s - 0.5) * dx, rel=1e-12)
    assert pressure["shock_set_hausdorff"].to_numpy() == pytest.approx(s * dx, rel=1e-12)
    assert pressure["max_error"].to_numpy() == pytest.approx(
        truth.star["pressure"] - truth.meta["right"][1], rel=1e-12)
    velocity = forecast.loc[(forecast["field"] == "velocity")
                            & (forecast["metric"] == "max_error"), "value"].to_numpy()
    assert velocity == pytest.approx(truth.star["velocity"], rel=1e-12)


def test_sod_runs_through_the_pipeline_without_its_periodic_only_metrics():
    """A bounded domain end to end: the boundary-aware ladder runs, pointwise metrics score,
    and a metric that needs a periodic domain produces no rows."""
    result = run(SodShockTube(grid=(64,), n_frames=3), [metric_registry.get(n) for n in
                                                        ("mse", "h1_seminorm")],
                 build_ladder(QUICK), fields=["density", "velocity", "pressure"],
                 dataset=DatasetInfo(name="sod_shock_tube"))
    assert set(result.rows["metric"].astype(str)) == {"mse"}
    assert set(result.rows["field"].astype(str)) == {"density", "velocity", "pressure"}
    assert np.isfinite(result.rows["value"]).all()
    assert (result.rows.loc[result.rows["level"] == 0, "value"] == 0).all()



def test_evaluate_writes_no_folder_for_a_metric_it_did_not_run(tmp_path):
    """End to end through ``evaluate.py``: on the bounded Sod domain the periodic-only metric is
    not run, so it gets no run folder -- a folder without rows would fail its report -- and with
    one metric left there is no comparison folder either. The folder records the dataset's
    boundaries, which the report reads before quoting any operator's invariants."""
    subprocess.run(
        [sys.executable, str(REPO / "evaluate.py"), "dataset=sod_shock_tube",
         "degradation=quick", "metrics=[mse,h1_seminorm]", "+dataset.reader.grid=[64]",
         "+dataset.reader.n_frames=3", f"paths.results={tmp_path}",
         f"hydra.run.dir={tmp_path}/h"],
        check=True, capture_output=True, cwd=tmp_path,
    )
    folders = [p for p in tmp_path.glob("*_*") if p.is_dir()]
    assert [p.name.split("_")[0] for p in folders] == ["mse"]
    assert read_run_meta(folders[0])["boundary"] == ["neumann"]


def test_a_metric_run_alone_keeps_its_named_companions(tmp_path):
    """A metric's own folder holds its named companions (``shock_set_distance.profile``) as the
    comparison folder does; a run of that metric alone writes only its own folder."""
    subprocess.run(
        [sys.executable, str(REPO / "evaluate.py"), "dataset=sod_shock_tube",
         "degradation=quick", "metrics=[shock_set_distance]", "+dataset.reader.grid=[64]",
         "+dataset.reader.n_frames=3", f"paths.results={tmp_path}",
         f"hydra.run.dir={tmp_path}/h"],
        check=True, capture_output=True, cwd=tmp_path,
    )
    (folder,) = [p for p in tmp_path.glob("shock_set_distance_*") if p.is_dir()]
    stored = {parse_map_key(k)[0] for k in read_maps(folder)}
    assert "shock_set_distance.profile" in stored, stored


def test_evaluate_fails_when_no_metric_produced_a_row(tmp_path):
    """An ensemble metric on the deterministic Sod dataset produces no rows, so nothing is
    written; the run must say so and exit non-zero rather than succeed with no output."""
    done = subprocess.run(
        [sys.executable, str(REPO / "evaluate.py"), "dataset=sod_shock_tube",
         "degradation=quick", "metrics=[crps]", "+dataset.reader.grid=[64]",
         "+dataset.reader.n_frames=3", f"paths.results={tmp_path}",
         f"hydra.run.dir={tmp_path}/h"],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert done.returncode != 0, done.stderr[-2000:]
    assert "no metric produced a row" in done.stderr, done.stderr[-2000:]
    assert not [p for p in tmp_path.glob("crps_*")]


# --- Viscous Burgers (dataset_specs/02, Sect. 4.5) -----------------------------------------


@pytest.mark.parametrize("nu, tolerance", [(0.1, 1e-11), (Burgers.MIN_NU, 1e-7)])
def test_burgers_starts_from_minus_sin_x(nu, tolerance):
    """At t = 0 the series is -sin x, to its round-off: 1.3e-12 at nu = 0.1 and 2.1e-8 at the
    smallest admitted viscosity, where the series cancels most (measured)."""
    start = Burgers(nu=nu, grid=(96,), n_frames=1, t_start=0.0, t_end=0.0)
    u = start.frame(0, ["velocity"])["velocity"][0]
    assert u == pytest.approx(-np.sin(start.centres[0]), rel=0, abs=tolerance)


@pytest.mark.parametrize("time", [0.5, 1.0, 2.0])
def test_burgers_solves_the_viscous_burgers_equation(time):
    """The residual of u_t + u u_x - nu u_xx by centred differences in time and space, on the
    reader's frames at t - dt, t, t + dt. Every stencil is second order, so on an exact solution
    the residual is their truncation error alone, O(h^2 + dt^2): it falls by 4 when h and dt
    halve, and a wrong solution leaves a residual that does not fall. Measured on 512 and 1024
    cells with dt = 8e-3 and 4e-3: ratios 3.994 to 3.9995, the finer residual at most 2.7e-4 of
    max |u u_x| (about 1). Asserted: a ratio within 4 +- 0.1, and a finer residual below 1e-3 of
    max |u u_x|. At nu = 0.05 the series' round-off of 2e-8, over h^2, would dominate."""
    nu, residuals, scales = 0.1, [], []
    for cells, dt in ((512, 8e-3), (1024, 4e-3)):
        burgers = Burgers(nu=nu, grid=(cells,), n_frames=3, t_start=time - dt, t_end=time + dt)
        before, u, after = (burgers.frame(i, ["velocity"])["velocity"][0] for i in range(3))
        h, right, left = burgers.grid.spacing[0], np.roll(u, -1), np.roll(u, 1)
        advection = u * (right - left) / (2 * h)
        residual = (after - before) / (2 * dt) + advection - nu * (right - 2 * u + left) / h**2
        residuals.append(np.abs(residual).max())
        scales.append(np.abs(advection).max())
    assert residuals[0] / residuals[1] == pytest.approx(4.0, abs=0.1), residuals
    assert residuals[1] < 1e-3 * scales[1], (residuals, scales)


def test_the_central_scheme_has_its_observed_order_of_two_through_the_pipeline():
    """The second-order scheme against the exact solution, each grid scored on its own cells
    through ``pipeline.run``'s prediction path, on 64, 128, 256 and 512 cells (ratio 2), at
    t = 0.5, 1, 1.5, 2. The observed order of each pair of grids is p = ln(L_k / L_{k+1}) / ln 2
    (Roy 2005, J. Comput. Phys. 205(1), 131-156, Eq. 8), for L = ``rmse`` (Roy's L2, Eq. 7) and
    ``max_error`` (his L-infinity). The formal order is 2; p departs from it by the
    higher-order terms Roy's Eq. 5 neglects, which shrink with h. Measured: 1.93 to 2.02 on
    (64, 128), 1.997 to 2.005 on (128, 256), 1.995 to 2.001 on (256, 512). Asserted: within
    0.1 of 2 on the coarsest pair and 0.01 on the two finer ones, read by the analysis
    (``fmeval.analysis.observed_order``) from the four runs' rows together."""
    runs = []
    for cells in (64, 128, 256, 512):
        truth = Burgers(grid=(cells,), candidate={"scheme": "central"})
        runs.append(run(truth, [metric_registry.get(n) for n in ("rmse", "max_error")],
                        build_ladder({}), fields=["velocity"], dataset=DatasetInfo(name="burgers"),
                        prediction=truth.predictions()).rows)
        assert (runs[-1]["param_resolution"] == cells).all()
    order = observed_order(pd.concat(runs, ignore_index=True), anchor_label=MEAN_FIELD_LABEL)
    assert len(order) == 2 * 4 * 3, "two metrics, four times, three pairs of grids"
    assert (order["ratio"] == 2).all()
    for coarse, tolerance in ((64, 0.1), (128, 0.01), (256, 0.01)):
        pair = order[order["resolution_coarse"] == coarse]
        assert (pair["order"] - 2).abs().max() <= tolerance, f"{coarse}:\n{pair}"


@pytest.mark.parametrize("kwargs, match", [
    ({"nu": 0.03}, "at least"),
    ({"nu": 0.0}, "at least"),
    ({"scheme": "upwind"}, "scheme must be"),
    ({"candidate": {"scheme": "spectral"}}, "scheme must be"),
    ({"candidate": {"nu": 0.01}}, "at least"),
    ({"candidate": {"grid": [128]}}, "not parameters"),
])
def test_burgers_refuses_what_it_cannot_compute(kwargs, match):
    with pytest.raises(ValueError, match=match):
        Burgers(**kwargs).predictions()


# --- Cylindrical blast waves: Sedov-Taylor and Noh ------------------------------------


def radial_profile(line: ClosedFormTrajectory, time: float) -> tuple[np.ndarray, ...]:
    """``r`` and the density, radial velocity and pressure there, from a reader on a single row
    of cells through the centre of its 2 x 2 domain: the one cell across sits at y = 1, so the
    cells at x > 1 sample the solution at r = x - 1 along +x."""
    x = line.centres[0][:, 0] - 1.0
    frame = line.solution(time)
    return (x[x > 0], *(frame[name][0][:, 0][x > 0] for name in ("density", "velocity",
                                                                    "pressure")))


@pytest.mark.parametrize("gamma", [1.4, 5.0 / 3.0])
def test_sedov_solves_the_euler_equations_behind_the_front(gamma):
    """The cylindrical Euler equations of an ideal gas (Kamm & Timmes 2007, Eqs. 1-3 at j = 2),
    continuity ``rho_t + (rho u)_r + rho u / r = 0``, momentum ``u_t + u u_r + p_r / rho = 0``
    and the entropy ``(d_t + u d_r) ln(p / rho^gamma) = 0``, hold between 0.2 r_2 and 0.95 r_2:
    derivatives by second-order differences on 20000 cells of the radius (dr = 5e-5) and a
    centred difference of the reader in time (h = 1e-5). Each residual is measured against the
    largest term it balances: 3e-7 at most (gamma 1.4), the differencing error; tolerance 1e-5.
    The axis, where the density vanishes as lambda^(2/(gamma - 1)), and the front are left out
    of the differences, not of the solution."""
    line = SedovTaylor(gamma=gamma, grid=(40000, 1), n_frames=2, t_start=0.5)
    t, h = 0.8, 1e-5
    r, rho, u, p = radial_profile(line, t)
    _, rho_up, u_up, p_up = radial_profile(line, t + h)
    _, rho_down, u_down, p_down = radial_profile(line, t - h)
    keep = (r > 0.2 * line.front(t)) & (r < 0.95 * line.front(t))

    def d(q):
        return np.gradient(q, r[1] - r[0])

    def entropy(rho_, p_):
        return np.log(p_) - gamma * np.log(rho_)

    residuals = {
        "continuity": ((rho_up - rho_down) / (2 * h) + d(rho * u) + rho * u / r, d(rho * u)),
        "momentum": ((u_up - u_down) / (2 * h) + u * d(u) + d(p) / rho, d(p) / rho),
        "entropy": ((entropy(rho_up, p_up) - entropy(rho_down, p_down)) / (2 * h)
                    + u * d(entropy(rho, p)), u * d(entropy(rho, p))),
    }
    for name, (residual, term) in residuals.items():
        assert np.abs(residual[keep]).max() < 1e-5 * np.abs(term[keep]).max(), name


@pytest.mark.parametrize("gamma", [1.4, 5.0 / 3.0])
def test_sedov_conserves_mass_and_its_front_carries_the_strong_shock_jump(gamma):
    """Three statements independent of the reader's formulas.

    1. Mass: the gas swept up, ``rho_0 pi r_2^2``, is all behind the front. Integrated by the
       midpoint rule on 20000 cells of the radius at a time that puts the front on a cell face,
       so no cell straddles it: 3e-8 relative, the rule's error near the axis; tolerance 1e-6.
    2. The jump: a cell 1e-9 behind the front holds the strong-shock state, which balances
       the fluxes of mass, momentum and energy into the shock moving at ``u_s = dr_2/dt``
       against cold gas at rest (Kamm & Timmes 2007, Sect. 2, "an infinitely strong shock";
       u_s by a centred difference of the reader's front, h = 1e-6). The cell's own offset from
       the front costs 1.1e-8 at most, measured; tolerance 1e-6.
    3. At gamma = 1.4, Kamm & Timmes's standard cylindrical energy 0.311357 puts the front at
       0.75 at t = 1 (their Sect. 4.1, as ``dataset_specs/03``, Sect. 3.1 reads it): 0.749994
       here, the printed energy's six digits allowing 4e-7; tolerance 1e-5 (the reader's
       docstring records the 8e-6 gap)."""
    line = SedovTaylor(gamma=gamma, grid=(40000, 1), n_frames=2, t_start=0.5)
    r = radial_profile(line, 1.0)[0]
    dr, energy = r[1] - r[0], line.meta["energy"]
    face = 15000 * dr  # cell centres sit at (m + 1/2) dr from the axis
    t_face = face**2 * np.sqrt(line.alpha / energy)  # r_2(t) = (E t^2 / alpha)^(1/4), rho_0 = 1
    assert line.front(t_face) == pytest.approx(face, rel=1e-14)
    _, rho, _, _ = radial_profile(line, t_face)
    mass = np.sum(rho[r < face] * 2 * np.pi * r[r < face]) * dr
    assert mass == pytest.approx(np.pi * face**2, rel=1e-6)

    cell = r[12000]
    t_jump = (cell + 1e-9) ** 2 * np.sqrt(line.alpha / energy)
    _, rho, u, p = (q[12000] for q in radial_profile(line, t_jump))
    shock = (line.front(t_jump + 1e-6) - line.front(t_jump - 1e-6)) / 2e-6
    w = shock - u  # the gas's speed relative to the shock, behind it
    assert rho * w == pytest.approx(shock, rel=1e-6)
    assert rho * w**2 + p == pytest.approx(shock**2, rel=1e-6)
    assert 0.5 * w**2 + gamma * p / ((gamma - 1) * rho) == pytest.approx(0.5 * shock**2, rel=1e-6)
    if gamma == 1.4:
        assert line.front(1.0) == pytest.approx(0.75, rel=1e-5)


def test_noh_has_sutherlands_exact_solution_and_its_jump_and_inflow_obey_the_euler_equations():
    """Sutherland (2010), Table 9: at gamma = 5/3 the post-shock state is rho = 16, p = 16/3 at
    rest, the shock moves at 1/3, and ahead of it rho = 1 + t/r, u_r = -1. For gamma = 1.4 the
    reader's general construction (D = 0.2, rho_2 = 36, p_2 = 7.2) is checked the same way:
    the fluxes of mass, momentum and energy across the shock balance in the lab frame,
    ``F(W_2) - D W_2 = F(W_1) - D W_1`` (Toro (2009) eqs. (3.42)-(3.44), radially), with the
    inflow's state read from a cell 1e-9 ahead of the front and the post-shock state from the
    cell behind; ahead of the shock the continuity equation ``rho_t + (r rho u)_r / r = 0``
    holds to differencing error (3e-11 of its terms, measured; tolerance 1e-6). The ambient
    pressure is set to 1e-300, so the flux balance is exact to the cell's offset: 1.4e-9,
    measured; tolerance 1e-7. At t = 0 there is no shock, and the detector flags nothing."""
    sutherland = Noh()
    assert sutherland.shock_speed == pytest.approx(1 / 3, rel=1e-15)
    assert sutherland.post_shock == pytest.approx({"density": 16.0, "pressure": 16 / 3},
                                                  rel=1e-15)
    frame = sutherland.solution(1.5)
    radius, direction = polar(sutherland.centres, 2.0)
    outside = radius > sutherland.front(1.5)
    assert frame["density"][0][outside] == pytest.approx(1 + 1.5 / radius[outside], rel=1e-15)
    radial = np.einsum("cxy,cxy->xy", frame["velocity"], direction)
    assert radial[outside] == pytest.approx(-1.0, rel=1e-15)
    assert not shock_mask(Noh(t_start=0.0).solution(0.0)["pressure"][0]).any()

    for gamma in (5.0 / 3.0, 1.4):
        line = Noh(gamma=gamma, pressure=1e-300, grid=(40000, 1), n_frames=2)
        r = radial_profile(line, 1.0)[0]
        t = (r[12000] - 1e-9) / line.shock_speed
        _, rho, u, p = radial_profile(line, t)

        def flux_minus_shock(i):
            energy = p[i] / (gamma - 1) + 0.5 * rho[i] * u[i] ** 2
            return np.array([rho[i] * u[i], rho[i] * u[i] ** 2 + p[i], (energy + p[i]) * u[i]]
                            ) - line.shock_speed * np.array([rho[i], rho[i] * u[i], energy])

        assert flux_minus_shock(11999) == pytest.approx(flux_minus_shock(12000), rel=1e-7)
        t, h = 1.5, 1e-5
        r, rho, u, _ = radial_profile(line, t)
        rho_t = (radial_profile(line, t + h)[1] - radial_profile(line, t - h)[1]) / (2 * h)
        flux = np.gradient(r * rho * u, r[1] - r[0]) / r
        ahead = r > line.front(t) + 0.01
        assert np.abs(rho_t + flux)[ahead].max() < 1e-6 * np.abs(flux[ahead]).max()


@pytest.mark.parametrize("grid", [(128, 96), (96, 160)])
@pytest.mark.parametrize("reader, candidate", [
    (SedovTaylor, {"time_offset": 0.2}),     # the front moves out by r_2(t + 0.2) - r_2(t)
    (SedovTaylor, {"energy": 0.6}),          # a pure size error, (0.6 / 0.311357)^(1/4) r_2
    (Noh, {"time_offset": 0.3}),             # the front moves out by 0.3 / 3 at every time
], ids=["sedov_time", "sedov_energy", "noh_time"])
def test_a_circular_front_displaced_radially_is_read_by_the_shock_metrics(reader, candidate,
                                                                          grid):
    """A candidate whose circular front lies a known Delta r = r_c(t) - r(t) outside the
    reference's at every point, scored through the pipeline at four times (spec 03,
    Sect. 3.8: for a circle enlarged from r to r', every distance is r' - r).

    The detector flags a cell when its two neighbours along an axis straddle the front, so each
    flagged cell lies within one spacing (the larger, dx) of its circle: measured 0.994 dx at
    most. Every point of one set is then at least Delta r - 2 dx from the other set (measured
    Delta r - 1.88 dx), and in the measurements at most Delta r + 0.46 dx; the flagged cells
    cover every sixteenth of the circle. ``shock_set_distance`` and ``shock_set_hausdorff`` are
    each within one dx of Delta r (measured: the average 0.44 to 0.60 dx below it, the maximum
    0.18 to 0.46 dx above), the resolution of a front sampled on cells, as a straight front's
    (s - 1/2) dx and s dx are (the card's Eq. 3). Delta r is 3.2 to 6.4 cells here, so the two
    bands never touch. Two non-square grids, one taller than wide, catch a swapped axis."""
    truth = reader(grid=grid, candidate=candidate)
    other = truth.predictions()
    rows = run(truth, [metric_registry.get(n) for n in ("shock_set_distance",
                                                        "shock_set_hausdorff")],
               build_ladder({}), fields=["pressure"], dataset=DatasetInfo(name=truth.FORMAT),
               prediction=other).rows
    scores = rows[rows["degradation"] == "forecast"].pivot(index="time", columns="metric",
                                                           values="value")
    dx = max(truth.grid.spacing)
    delta = np.array([other.front(t) - truth.front(t) for t in scores.index])
    assert delta.min() > 3 * dx, "the two bands must not touch for these bounds"
    assert np.abs(scores["shock_set_distance"].to_numpy() - delta).max() < dx
    assert np.abs(scores["shock_set_hausdorff"].to_numpy() - delta).max() < dx
    for t, step in zip(scores.index, delta, strict=True):
        masks = [shock_mask(side.solution(t)["pressure"][0]) for side in (truth, other)]
        for side, mask in zip((truth, other), masks, strict=True):
            assert np.abs(polar(side.centres, 2.0)[0][mask] - side.front(t)).max() < dx
            x, y = (c[mask] - 1.0 for c in side.centres)
            assert np.unique(np.floor((np.arctan2(y, x) + np.pi) / (np.pi / 8))).size == 16
        distances = np.concatenate(surface_distances(*masks, truth.grid.spacing))
        assert step - 2 * dx <= distances.min() and distances.max() <= step + dx


@pytest.mark.parametrize("reader, kwargs, match", [
    (SedovTaylor, {"gamma": 2.0}, "gamma"),
    (SedovTaylor, {"energy": -1.0}, "positive"),
    (SedovTaylor, {"pressure": 0.0}, "positive"),
    (SedovTaylor, {"time_offset": -0.25}, "positive"),
    (SedovTaylor, {"t_end": 2.0}, "edge"),
    (SedovTaylor, {"candidate": {"energy": 1.0}}, "edge"),
    (Noh, {"gamma": 1.0}, "gamma"),
    (Noh, {"speed": 0.0}, "positive"),
    (Noh, {"time_offset": -1.0}, "non-negative"),
    (Noh, {"t_end": 3.0}, "edge"),
    (Noh, {"candidate": {"grid": [64, 64]}}, "not parameters"),
])
def test_the_blast_waves_refuse_what_their_closed_forms_do_not_cover(reader, kwargs, match):
    with pytest.raises(ValueError, match=match):
        reader(**kwargs).predictions()


# --- Taylor-Green vortex ---------------------------------------------------------------


def test_taylor_green_solves_the_incompressible_navier_stokes_equations():
    """The velocity is divergence-free and the momentum residual
    ``du/dt + (u . grad) u + grad p - nu lap u`` vanishes, with spatial derivatives taken
    spectrally and du/dt by a central difference of the reader in time. That one check pins
    the pressure's sign and both decay exponents independently of any formula in the reader
    (Taylor (1923) gives the stream function only; the pressure is derived). A non-square grid
    with unequal spacing catches a swapped axis."""
    nu, t, h = 0.01, 3.0, 1e-3
    tg = TaylorGreen2D(nu=nu, grid=(48, 32))
    dx = tg.grid.spacing
    now = tg.solution(t)
    u, p = now["velocity"], now["pressure"][0]
    dudt = (tg.solution(t + h)["velocity"] - tg.solution(t - h)["velocity"]) / (2 * h)

    def d(f, axis):
        return spectral_derivative(f, axis, spacing=dx)

    for c in range(2):
        advection = u[0] * d(u[c], 0) + u[1] * d(u[c], 1)
        laplacian = d(d(u[c], 0), 0) + d(d(u[c], 1), 1)
        residual = dudt[c] + advection + d(p, c) - nu * laplacian
        assert np.abs(residual).max() < 1e-10, f"momentum residual in component {c}"
    assert np.abs(divergence(u, spacing=dx)).max() < 1e-12


def test_taylor_green_runs_through_the_pipeline_and_its_single_mode_collapses_the_filters():
    """All the energy of velocity and vorticity sits at |k| = sqrt(2), so every calibrated
    ideal cutoff falls between the shells at 1 and sqrt(2). Measured on 32^2: every high-pass
    level then removes nothing and is flagged as doing nothing, and every low-pass level after
    the first removes everything, repeats the first, and is flagged as a repeat. That is a fact
    about this dataset, recorded on its page."""
    ladder = build_ladder({**QUICK,
                           "lowpass_ideal": {"severities": [0.05, 0.2, 0.45]},
                           "highpass_ideal": {"severities": [0.45, 0.7, 0.9]}})
    result = run(RecomputingTrajectory(TaylorGreen2D(grid=(32, 32), n_frames=3)),
                 [metric_registry.get("mse")], ladder,
                 fields=["velocity", "pressure", "vorticity"],
                 dataset=DatasetInfo(name="taylor_green_2d"))
    rows = result.rows[result.rows["field"] == "velocity"]
    flagged = rows.groupby(["degradation", "level"], observed=True)["severity_degenerate"].all()
    assert flagged["highpass_ideal"].all()
    assert list(flagged["lowpass_ideal"]) == [False, True, True]
    assert np.isfinite(result.rows["value"]).all()


@pytest.mark.parametrize("grid", [(48, 32), (25, 64)])
def test_taylor_green_fixes_the_energy_enstrophy_and_palinstrophy_budgets(grid):
    """``kinetic_energy``, ``enstrophy`` and ``palinstrophy``, run by the pipeline on the
    reader's frames with vorticity recomputed from velocity, take the closed-form values, and
    with them Boffetta & Ecke (2012) Eqs. (5) and (6), dE/dt = -2 nu Omega and
    dOmega/dt = -2 nu P (no forcing, no friction), hold exactly.

    With D = exp(-2 nu t), u = D (sin x cos y, -cos x sin y) and omega = 2 D sin x sin y, and
    each cell-centre mean of sin^2 or cos^2 over a whole period equal to 1/2 (any N >= 3):
    E = (1/2) <|u|^2> = D^2/4, Omega = (1/2) <omega^2> = D^2/2, and
    P = (1/2) <|grad omega|^2> = (1/2) 4 D^2 <cos^2 x sin^2 y + sin^2 x cos^2 y> = D^2. Then
    dE/dt = -nu D^2 = -2 nu Omega and dOmega/dt = -2 nu D^2 = -2 nu P. Both derivatives (the
    curl and the palinstrophy gradient) are spectral, exact for a resolved single mode, so the
    only error is round-off and the tolerance is 1e-12 relative. A centred difference would
    instead multiply Omega by (sin h / h)^2, h = 2 pi / N. Two non-square grids, one with an
    odd count, catch a swapped axis or an odd-length wavenumber error."""
    nu = 0.01
    result = run(RecomputingTrajectory(TaylorGreen2D(nu=nu, grid=grid, n_frames=4, t_end=60.0)),
                 [metric_registry.get(n) for n in ("kinetic_energy", "enstrophy", "palinstrophy")],
                 build_ladder({}), fields=["velocity", "vorticity"],
                 dataset=DatasetInfo(name="taylor_green_2d"))
    values = result.rows.pivot(index="time", columns="metric", values="value")
    d2 = np.exp(-4.0 * nu * values.index.to_numpy())
    energy, enstrophy, palinstrophy = (values[n].to_numpy()
                                       for n in ("kinetic_energy", "enstrophy", "palinstrophy"))
    assert energy == pytest.approx(d2 / 4, rel=1e-12), f"kinetic_energy {energy} is not D^2/4"
    assert enstrophy == pytest.approx(d2 / 2, rel=1e-12), f"enstrophy {enstrophy} is not D^2/2"
    assert palinstrophy == pytest.approx(d2, rel=1e-12), f"palinstrophy {palinstrophy} is not D^2"
    # The exact time derivatives of the closed forms D^2/4 and D^2/2, against the bundles.
    assert -2.0 * nu * enstrophy == pytest.approx(-nu * d2, rel=1e-12), (
        "dE/dt = -2 nu Omega fails: the enstrophy normalisation disagrees with kinetic_energy's")
    assert -2.0 * nu * palinstrophy == pytest.approx(-2.0 * nu * d2, rel=1e-12), (
        "dOmega/dt = -2 nu P fails: the palinstrophy normalisation disagrees with enstrophy's")


#: The thirteen metrics whose cards report them per step of a candidate trajectory.
PER_STEP = ("mse", "mae", "rmse", "rmse_channel_mean", "nrmse", "vrmse", "max_error",
            "max_error_channel_mean", "h1_relative", "spectrum_l2", "kinetic_energy", "enstrophy",
            "palinstrophy")


def scored_candidate(truth: ClosedFormTrajectory, metrics: Sequence[str] = PER_STEP,
                     fields: Sequence[str] = ("velocity", "vorticity")) -> dict[str, pd.DataFrame]:
    """Each metric on the truth (``identity``) and on its candidate (``forecast``), indexed by
    field and time, through the pipeline's prediction path with vorticity recomputed from
    velocity, as ``evaluate.py`` does."""
    rows = run(RecomputingTrajectory(truth), [metric_registry.get(n) for n in metrics],
               build_ladder({}), fields=list(fields), dataset=DatasetInfo(name=truth.FORMAT),
               prediction=RecomputingTrajectory(truth.predictions())).rows
    assert (rows["lead_step"] == rows["frame_index"]).all(), "the lead is the frame's step"
    return {side: rows[rows["degradation"] == side].pivot(index=["field", "time"],
                                                          columns="metric", values="value")
            for side in ("identity", "forecast")}


@pytest.mark.parametrize("grid", [(48, 32), (25, 64)])
def test_taylor_green_with_a_wrong_viscosity_has_a_closed_form_error_in_every_per_step_metric(
        grid):
    """The candidate with viscosity nu' is the truth times r = D'/D, D = exp(-2 nu t), so every
    error is |1 - r| times a property of the truth's pattern (spec 05, Sect. 3.3, table):

    * velocity's mean square per channel is D^2/4 (cell-centre means of sin^2 cos^2 are 1/4 on
      any N >= 3), so mse = (D - D')^2/4, rmse = rmse_channel_mean = |D - D'|/2, nrmse =
      |1 - r|, and vrmse = (|D - D'|/2) / sqrt(M/(M-1) D^2/4 + 1e-7) over M cells, the sample
      variance with ddof = 1 and the card's epsilon (``metrics/vrmse/card.md``);
    * h1_relative = 2 |1 - r|, one ratio per channel, and spectrum_l2 = |1 - r^2|, all energy
      in one shell;
    * the single-field metrics take the candidate's own closed forms, E = D'^2/4,
      Omega = D'^2/2, P = D'^2 (as in the budget test above);
    * mae and the maxima separate into one factor per axis, |sin| or |cos| at the cell centres
      of that axis. The spec's max_error cos^2(pi/N) |D - D'| holds only when 4 divides N: with
      N = 25 a centre lies a quarter cell from the peak of sin x, so the factor is
      cos(pi/50), which the 25-cell grid checks.

    Tolerance 1e-12 relative: both sides are evaluated in closed form and every derivative is
    spectral. h1_relative adds the library's 1e-8 to sqrt of the reference's H^1 sum, at least
    sqrt(M/4) D, about 10 here, so its bias is below 1e-9 and its tolerance 1e-8."""
    nu, nu_candidate = 0.01, 0.025
    truth = TaylorGreen2D(nu=nu, grid=grid, n_frames=4, t_end=30.0,
                          candidate={"nu": nu_candidate})
    got = scored_candidate(truth)["forecast"]
    velocity, vorticity = got.loc["velocity"], got.loc["vorticity"]
    t = velocity.index.to_numpy()
    d, d_candidate = np.exp(-2 * nu * t), np.exp(-2 * nu_candidate * t)
    gap, r, cells = np.abs(d - d_candidate), d_candidate / d, grid[0] * grid[1]
    sin_x, cos_x, sin_y, cos_y = (np.abs(f((np.arange(n) + 0.5) * 2 * np.pi / n))
                                  for n in grid for f in (np.sin, np.cos))
    peaks = np.array([sin_x.max() * cos_y.max(), cos_x.max() * sin_y.max()])
    expected = {
        "mse": gap**2 / 4, "rmse": gap / 2, "rmse_channel_mean": gap / 2,
        "nrmse": np.abs(1 - r),
        "vrmse": gap / 2 / np.sqrt(cells / (cells - 1) * d**2 / 4 + EPSILON),
        "spectrum_l2": np.abs(1 - r**2), "kinetic_energy": d_candidate**2 / 4,
        "mae": gap * (sin_x.mean() * cos_y.mean() + cos_x.mean() * sin_y.mean()) / 2,
        "max_error": gap * peaks.max(), "max_error_channel_mean": gap * peaks.mean(),
    }
    for name, value in expected.items():
        assert velocity[name].to_numpy() == pytest.approx(value, rel=1e-12), name
    assert velocity["h1_relative"].to_numpy() == pytest.approx(2 * np.abs(1 - r), rel=1e-8)
    assert vorticity["enstrophy"].to_numpy() == pytest.approx(d_candidate**2 / 2, rel=1e-12)
    assert vorticity["palinstrophy"].to_numpy() == pytest.approx(d_candidate**2, rel=1e-12)


@pytest.mark.parametrize("grid", [(48, 32), (25, 64)])
def test_taylor_green_with_a_phase_drift_is_seen_by_pointwise_errors_only(grid):
    """The candidate is the truth translated by delta = U t at unchanged amplitude. For
    f = sin x cos y the cell-centre mean of f(x) f(x - delta) is cos(dx) cos(dy) / 4 (any
    N >= 3), and likewise for the other channel, so each channel's mean squared error is
    D^2 (1 - cos dx cos dy) / 2: mse is that, rmse its root and nrmse = sqrt(2 (1 - cos dx
    cos dy)) (spec 05, Sect. 3.3). A translation keeps every Fourier amplitude, so
    kinetic_energy, enstrophy, palinstrophy and spectrum_l2 equal the truth's at every lead:
    position-blind. Tolerance 1e-12 relative, or 1e-12 absolute where the value is zero."""
    nu, drift = 0.01, np.array([0.03, -0.05])
    truth = TaylorGreen2D(nu=nu, grid=grid, n_frames=4, t_end=30.0,
                          candidate={"drift": drift.tolist()})
    scored = scored_candidate(truth)
    got, clean = scored["forecast"], scored["identity"]
    t = got.loc["velocity"].index.to_numpy()
    mse = np.exp(-4 * nu * t) * (1 - np.cos(drift[0] * t) * np.cos(drift[1] * t)) / 2
    assert got.loc["velocity", "mse"].to_numpy() == pytest.approx(mse, rel=1e-12)
    assert got.loc["velocity", "rmse"].to_numpy() == pytest.approx(np.sqrt(mse), rel=1e-12)
    assert got.loc["velocity", "nrmse"].to_numpy() == pytest.approx(
        np.sqrt(2 * (1 - np.cos(drift[0] * t) * np.cos(drift[1] * t))), rel=1e-12)
    assert (mse[1:] > 1e-3).all(), "the drift must be large enough to be seen"
    blind = got[["kinetic_energy", "enstrophy", "palinstrophy"]].dropna(how="all")
    assert blind.to_numpy() == pytest.approx(
        clean.loc[blind.index, blind.columns].to_numpy(), rel=1e-12, nan_ok=True)
    assert got["spectrum_l2"].to_numpy() == pytest.approx(0.0, abs=1e-12)


def test_evaluate_scores_a_closed_form_candidate_in_place_of_the_ladder(tmp_path):
    """End to end: a reader option selects the candidate, ``evaluate.py`` scores the reader's
    ``predictions()`` as it scores a forecast's, keeps only the clean entry and the anchor of
    the ladder, labels every row with its lead and resolution as a forecast's rows are (the
    forecast figure reads both), and nrmse on velocity is |1 - D'/D|."""
    subprocess.run(
        [sys.executable, str(REPO / "evaluate.py"), "dataset=taylor_green_2d", "metrics=[nrmse]",
         "+dataset.reader.candidate={nu:0.02}", "+dataset.reader.grid=[48,32]",
         "+dataset.reader.n_frames=4", "dataset.fields=[velocity]",
         f"paths.results={tmp_path}", f"hydra.run.dir={tmp_path}/h"],
        check=True, capture_output=True, cwd=tmp_path,
    )
    (folder,) = [p for p in tmp_path.glob("nrmse_*") if p.is_dir()]
    rows = read_results(folder)
    assert set(rows["degradation"]) == {"identity", "mean_field", "forecast"}
    assert (rows["lead_step"] == rows["frame_index"]).all()
    assert (rows["param_resolution"] == 48).all()
    forecast = rows[rows["degradation"] == "forecast"].sort_values("time")
    t = forecast["time"].to_numpy()
    assert forecast["value"].to_numpy() == pytest.approx(np.abs(1 - np.exp(-0.02 * t)),
                                                          rel=1e-12)
    assert read_run_meta(folder)["reader_options"]["candidate"] == {"nu": 0.02}


@pytest.mark.parametrize("kwargs, match", [
    ({"candidate": {"viscosity": 0.02}}, "not parameters of the solution"),
    ({"candidate": {"grid": [8, 8]}}, "not parameters of the solution"),
    ({"drift": (0.1,)}, "pair"),
    ({"acoustic": [{"kind": "potential", "mode": [1, 1], "amplitude": 1.0}]}, "sound_speed"),
    ({"sound_speed": 2.0, "acoustic": [{"kind": "wave", "mode": [1, 0], "amplitude": 1.0}]},
     "acoustic entry"),
    ({"sound_speed": 2.0, "acoustic": [{"kind": "plane", "mode": [0.5, 1], "amplitude": 1.0}]},
     "two integers"),
    ({"sound_speed": 2.0, "acoustic": [{"kind": "pulse", "centre": [1.0, 1.0], "width": 0.05,
                                        "amplitude": 0.1}]}, "pulse width"),
    # nu_L = 2 nu = 0.02 and |k| up to 181 on 256^2 cells: 3.6 > 2 c.
    ({"sound_speed": 1.0}, "damped past oscillation"),
])
def test_taylor_green_refuses_a_candidate_it_cannot_build(kwargs, match):
    with pytest.raises(ValueError, match=match):
        TaylorGreen2D(**kwargs)


def test_taylor_green_grid_is_periodic_and_frames_decay_together():
    tg = TaylorGreen2D(grid=GRID)
    assert tg.grid.boundary == ("periodic", "periodic")
    first, last = (tg.frame(i, ["velocity"])["velocity"] for i in (0, len(tg) - 1))
    ratio = np.exp(-2 * 0.01 * (tg.times[-1] - tg.times[0]))
    assert last == pytest.approx(ratio * first, rel=1e-12, abs=1e-15)


# --- Taylor-Green with an acoustic part (dataset_specs/10, Sect. 3) ---------------------------


#: The vortex's mirror image (spec 10, Sect. 3.3, item 2): phi = A cos x cos y at rest density,
#: whose velocity at t = 0 is -A (sin x cos y, cos x sin y). With nu = 0.01 the default
#: nu_L = 2 nu = 0.02.
TWIN = {"nu": 0.01, "n_frames": 4, "t_end": 30.0, "sound_speed": 2.0,
        "acoustic": [{"kind": "potential", "mode": [1, 1], "amplitude": 0.7}]}


def twin_factor(t: np.ndarray, c: float, nu_l: float = 0.02) -> np.ndarray:
    """The twin's dilatational velocity over its starting value, f(t) = e^(-gamma t)
    (cos Omega t - (gamma / Omega) sin Omega t) with |k|^2 = 2, gamma = nu_L |k|^2 / 2 and
    Omega^2 = c^2 |k|^2 - gamma^2: spec 10, Eq. 3 with rho_0 = 0. Cell-centre means of
    sin^2 cos^2 are 1/4 on any N >= 3, so its energy is E_d = A^2 f^2 / 4."""
    gamma = nu_l
    omega = np.sqrt(2 * c**2 - gamma**2)
    return np.exp(-gamma * t) * (np.cos(omega * t) - gamma / omega * np.sin(omega * t))


@pytest.mark.parametrize("nu_l", [0.03, 0.0])
def test_the_acoustic_part_solves_the_linearised_equations_and_keeps_its_energy(nu_l):
    """A potential, an oblique plane wave and a pulse at once, with no vortex, satisfy the
    linearised isothermal equations of spec 10, Eq. (1), at rest density 1,

        d_t rho' + div u = 0,   d_t u = -c^2 grad rho' + nu_L grad(div u),

    with rho' = p / c^2 read from the pressure, space derivatives spectral and time
    derivatives by the fourth-order centred difference of step h = 1e-3, whose truncation
    h^4 omega^5 / 30 is below 1e-10 of each term at the frequencies c |k| that carry the
    energy, and whose round-off is about 1e-16 / h. Measured: at most 5e-11 of the largest
    term, so 1e-9. The velocity is curl-free (spectral curl below 1e-12; measured 7e-15). At
    nu_L = 0 the acoustic energy <|u|^2 / 2 + c^2 rho'^2 / 2> is constant, each mode being an
    undamped oscillator (measured to 1.3e-15 relative over t = 0..50, so 1e-12). A grid of
    96 x 64 holds the pulse of width 0.33 inside the reader's bounds [3 dx, 0.35]."""
    c = 1.3
    tg = TaylorGreen2D(amplitude=0.0, sound_speed=c, longitudinal_viscosity=nu_l, grid=(96, 64),
                       acoustic=[{"kind": "potential", "mode": [1, 1], "amplitude": 0.4},
                                 {"kind": "plane", "mode": [3, -2], "amplitude": 0.05},
                                 {"kind": "pulse", "centre": [2.0, 4.0], "width": 0.33,
                                  "amplitude": 0.2}])
    dx, t, h = tg.grid.spacing, 1.7, 1e-3

    def d(f, axis):
        return spectral_derivative(f, axis, spacing=dx)

    def d_dt(name):
        s = [tg.solution(t + j * h)[name] for j in (-2, -1, 1, 2)]
        return (s[0] - 8 * s[1] + 8 * s[2] - s[3]) / (12 * h)

    now = tg.solution(t)
    u, rho = now["velocity"], now["pressure"][0] / c**2
    drho, du = d_dt("pressure")[0] / c**2, d_dt("velocity")
    div = divergence(u, spacing=dx)
    assert np.abs(drho + div).max() < 1e-9 * np.abs(drho).max(), "continuity"
    for a in range(2):
        residual = du[a] + c**2 * d(rho, a) - nu_l * d(div, a)
        assert np.abs(residual).max() < 1e-9 * np.abs(du).max(), f"momentum, component {a}"
    assert np.abs(spectral_vorticity(u, spacing=list(dx))).max() < 1e-12
    if nu_l == 0:
        energy = np.array([0.5 * (s["velocity"] ** 2).sum(axis=0).mean()
                           + 0.5 * (s["pressure"][0] ** 2).mean() / c**2
                           for s in (tg.solution(time) for time in tg.times)])
        assert energy == pytest.approx(energy[0], rel=1e-12)


def test_a_travelling_plane_wave_moves_at_the_sound_speed():
    """Without viscosity the plane-wave start is the travelling wave of linear acoustics,
    rho' = eps cos(k . x - c |k| t) and u = eps c k_hat cos(k . x - c |k| t) (spec 10, Sect.
    3.3, item 1), here along (3, -2) on 48 x 32 cells, to 1e-13 absolute (measured 2.5e-15 on
    a pressure of size 0.085). A wrong sign of the phase speed or of the potential fails it."""
    c, eps, m = 1.3, 0.05, np.array([3, -2])
    tg = TaylorGreen2D(amplitude=0.0, sound_speed=c, longitudinal_viscosity=0.0, grid=(48, 32),
                       acoustic=[{"kind": "plane", "mode": m.tolist(), "amplitude": eps}])
    k = np.hypot(*m)
    for t in tg.times:
        s = tg.solution(t)
        wave = np.cos(m[0] * tg.centres[0] + m[1] * tg.centres[1] - c * k * t)
        assert np.abs(s["pressure"][0] - c**2 * eps * wave).max() < 1e-13
        for a in range(2):
            assert np.abs(s["velocity"][a] - eps * c * m[a] / k * wave).max() < 1e-13


@pytest.mark.parametrize("grid", [(48, 32), (25, 64)])
def test_curl_metrics_read_only_the_vortex_and_the_energies_of_the_two_parts_add(grid):
    """Through the pipeline, vorticity recomputed from velocity:

    * the twin alone (U = 0) has `enstrophy` and `palinstrophy` 0 (below 1e-24; the curl is
      round-off) and `kinetic_energy` E_d = A^2 f^2 / 4 (:func:`twin_factor`);
    * with the vortex added, `kinetic_energy` is E_s + E_d, E_s = e^(-4 nu t) / 4, because the
      parts are orthogonal mode by mode, and `enstrophy` stays the vortex's e^(-4 nu t) / 2;
    * the Fourier projection `helmholtz_split` returns each part, the vortex alone and the twin
      alone, to 1e-14 (measured 9e-16).

    Tolerance 1e-12 relative: closed forms against spectral operators on single modes."""
    mixture = TaylorGreen2D(grid=grid, **TWIN)
    twin = TaylorGreen2D(grid=grid, amplitude=0.0, **TWIN)
    metrics = [metric_registry.get(n) for n in ("kinetic_energy", "enstrophy", "palinstrophy")]
    values = {name: run(RecomputingTrajectory(reader), metrics, build_ladder({}),
                        fields=["velocity", "vorticity"],
                        dataset=DatasetInfo(name="taylor_green_2d")).rows.pivot(
                            index="time", columns="metric", values="value")
              for name, reader in (("mixture", mixture), ("twin", twin))}
    t = values["twin"].index.to_numpy()
    e_s, e_d = np.exp(-4 * 0.01 * t) / 4, 0.7**2 * twin_factor(t, 2.0) ** 2 / 4
    assert values["twin"]["kinetic_energy"].to_numpy() == pytest.approx(e_d, rel=1e-12)
    assert values["twin"][["enstrophy", "palinstrophy"]].abs().to_numpy().max() < 1e-24
    assert values["mixture"]["kinetic_energy"].to_numpy() == pytest.approx(e_s + e_d, rel=1e-12)
    assert values["mixture"]["enstrophy"].to_numpy() == pytest.approx(2 * e_s, rel=1e-12)
    vortex = TaylorGreen2D(grid=grid, **{k: TWIN[k] for k in ("nu", "n_frames", "t_end")})
    for i in range(len(mixture)):
        solenoidal, dilatational = helmholtz_split(mixture.frame(i, ["velocity"])["velocity"],
                                                   mixture.grid)
        assert np.abs(solenoidal - vortex.frame(i, ["velocity"])["velocity"]).max() < 1e-14
        assert np.abs(dilatational - twin.frame(i, ["velocity"])["velocity"]).max() < 1e-14


@pytest.mark.parametrize("grid", [(48, 32), (25, 64)])
def test_scale_dilatational_keeps_the_vorticity_and_scales_the_dilatational_energy(grid):
    """On the vortex plus its twin, the operator multiplies the dilatational part by
    lambda = 1 + delta (delta = -s, or +s with ``amplify``) and touches nothing else (spec 10,
    Sect. 3.6): `kinetic_energy` = E_s + lambda^2 E_d, `mse` on velocity = delta^2 E_d (the
    error delta u_d, averaged over two components), and vorticity is passed through, so its
    `mse` is exactly 0 and `enstrophy` is the reference's. Tolerance 1e-12 relative."""
    ladder = build_ladder({
        "down": {"op": "scale_dilatational", "severities": [0.5, 1.0]},
        "up": {"op": "scale_dilatational", "severities": [0.5], "options": {"amplify": True}}})
    rows = run(RecomputingTrajectory(TaylorGreen2D(grid=grid, **TWIN)),
               [metric_registry.get(n) for n in ("kinetic_energy", "enstrophy", "mse")], ladder,
               fields=["velocity", "vorticity"], dataset=DatasetInfo(name="taylor_green_2d")).rows
    t = np.sort(rows["time"].unique())
    e_s, e_d = np.exp(-4 * 0.01 * t) / 4, 0.7**2 * twin_factor(t, 2.0) ** 2 / 4
    values = rows.pivot(index=["degradation", "severity", "field", "time"], columns="metric",
                        values="value")
    for degradation, delta in (("down", -0.5), ("down", -1.0), ("up", 0.5)):
        velocity = values.loc[(degradation, abs(delta), "velocity")]
        vorticity = values.loc[(degradation, abs(delta), "vorticity")]
        assert velocity["kinetic_energy"].to_numpy() == pytest.approx(
            e_s + (1 + delta) ** 2 * e_d, rel=1e-12), (degradation, delta)
        assert velocity["mse"].to_numpy() == pytest.approx(delta**2 * e_d, rel=1e-12)
        assert (vorticity["mse"] == 0).all()
        assert vorticity["enstrophy"].to_numpy() == pytest.approx(2 * e_s, rel=1e-12)


@pytest.mark.parametrize("grid", [(48, 32), (25, 64)])
def test_a_wrong_sound_speed_is_an_error_in_the_dilatational_part_only(grid):
    """The candidate ``{sound_speed: 2.5}`` keeps the vortex and the twin's starting potential,
    so its error is the twin's at the wrong frequency: `mse` on velocity is
    A^2 (f_c - f_c')^2 / 4 (:func:`twin_factor`), `mse` on vorticity is round-off (below 1e-28)
    and `enstrophy` equals the truth's, and the error field has no solenoidal part (below
    1e-14). Tolerance 1e-12 relative, 1e-15 absolute at t = 0 where both errors vanish."""
    truth = TaylorGreen2D(grid=grid, **TWIN, candidate={"sound_speed": 2.5})
    scored = scored_candidate(truth, ("mse", "enstrophy"))
    got = scored["forecast"]
    t = got.loc["velocity"].index.to_numpy()
    mse = 0.7**2 * (twin_factor(t, 2.0) - twin_factor(t, 2.5)) ** 2 / 4
    assert got.loc["velocity", "mse"].to_numpy() == pytest.approx(mse, rel=1e-12, abs=1e-15)
    assert (mse[1:] > 1e-3).all(), "the frequency error must be large enough to be seen"
    assert got.loc["vorticity", "mse"].max() < 1e-28
    assert got.loc["vorticity", "enstrophy"].to_numpy() == pytest.approx(
        scored["identity"].loc["vorticity", "enstrophy"].to_numpy(), rel=1e-12)
    candidate = truth.predictions()
    for i in range(len(truth)):
        error = (candidate.frame(i, ["velocity"])["velocity"]
                 - truth.frame(i, ["velocity"])["velocity"])
        assert np.abs(helmholtz_split(error, truth.grid)[0]).max() < 1e-14



@pytest.mark.parametrize("name, figures", [
    ("sod_shock_tube", ["sod_shock_tube"]),
    ("taylor_green_2d", [f"taylor_green_2d_{f}" for f in
                         ("velocity_x", "velocity_y", "pressure", "vorticity")]),
])
def test_the_dynamics_figures_are_drawn_with_their_numbers(name, figures, tmp_path):
    """`python -m fmeval.cards dynamics` draws one figure per field (per component of a
    vector), or one for every field of a 1D dataset, each with its numbers beside it."""
    written = dataset_figures.generate(name, out=tmp_path)
    assert sorted(p.stem for p in written) == sorted(figures)
    for path in written:
        record = json.loads(path.with_suffix(".json").read_text())
        assert record["dataset"] == name and record["panels"]
        assert len(record["time"]) == dataset_figures.N_SNAPSHOTS


# --- advecting blobs: the time-dependent test bed --------------------------------------------


def test_a_blob_is_carried_rigidly_at_its_velocity():
    """Exact advection: at 0.125 domain lengths per unit time on 16 cells along x, one unit of
    time later the field is the first frame shifted by exactly two cells."""
    blob = AdvectingBlobs(grid=(16, 8), n_frames=3, t_end=2.0, velocities=((0.125, 0.0),),
                          width=0.1)
    first, later = (blob.frame(i, ["density"])["density"] for i in (0, 1))
    assert later == pytest.approx(np.roll(first, 2, axis=-2), rel=1e-12)
    assert blob.grid.boundary == ("periodic", "periodic")


@pytest.mark.parametrize("candidate", [
    {"velocities": [[0.07, 0.0]]},                             # a wrong speed
    {"diffusivity": 1e-5},                                     # a wrong diffusivity
    {"velocities": [[0.03, 0.04]], "diffusivity": 1e-5},       # both
])
def test_a_blob_candidate_with_a_wrong_speed_or_diffusivity_has_its_closed_form_mse(candidate):
    """Two Gaussians g_i = a_i exp(-|x - c_i|^2 / (2 s_i)) on the unit square, with
    s_i = w^2 + 2 kappa_i t and a_i = a w^2 / s_i (the reader's solution), centres Delta =
    (u' - u) t apart: from int g_i^2 = pi a_i^2 s_i and int g_1 g_2 = 2 pi a_1 a_2 s_1 s_2 /
    (s_1 + s_2) exp(-|Delta|^2 / (2 (s_1 + s_2))) (our derivation, the product of two
    Gaussians), MSE = pi a_1^2 s_1 + pi a_2^2 s_2 - 4 pi a_1 a_2 s_1 s_2 / (s_1 + s_2)
    exp(-|Delta|^2 / (2 (s_1 + s_2))). The cell-centre mean is the integral to within
    exp(-2 pi^2 s / (2 h^2)) < 1e-30 for a resolved Gaussian, and the minimum-image seam is
    below 5e-15 of the peak here (s <= 0.0038). The density is 1 plus the bump, so each cell's
    difference carries an absolute round-off of 1e-16 against bumps whose difference is
    1e-4 under the wrong diffusivity: measured relative error 2e-12, tolerance 1e-10."""
    a, w = 0.1, 0.06
    truth = AdvectingBlobs(grid=(64, 48), n_frames=6, t_end=10.0, velocities=[[0.05, 0.02]],
                           amplitude=a, width=w, candidate=candidate)
    rows = run(truth, [metric_registry.get("mse")], build_ladder({}), fields=["density"],
               dataset=DatasetInfo(name="advecting_blobs"), prediction=truth.predictions()).rows
    forecast = rows[rows["degradation"] == "forecast"]
    t = forecast["time"].to_numpy()
    s1, s2 = (w**2 + 2 * kappa * t for kappa in
              (truth.meta["diffusivity"], candidate.get("diffusivity", 0.0)))
    a1, a2 = a * w**2 / s1, a * w**2 / s2
    shift = np.subtract(candidate.get("velocities", truth.meta["velocities"])[0],
                        truth.meta["velocities"][0])
    mse = (np.pi * a1**2 * s1 + np.pi * a2**2 * s2 - 4 * np.pi * a1 * a2 * s1 * s2 / (s1 + s2)
           * np.exp(-(shift @ shift) * t**2 / (2 * (s1 + s2))))
    assert forecast["value"].to_numpy() == pytest.approx(mse, rel=1e-10, abs=1e-20)
    assert (forecast["value"].to_numpy()[1:] > 0).all()


def test_blobs_at_distinct_speeds_change_the_error_from_frame_to_frame():
    """The reason for three blobs: with distinct velocities their relative positions change, so
    one blur costs a different amount in each frame, while one blob gives the same error in
    every frame. Measured with the defaults, MSE under this blur varies by 7.5% across frames."""
    ladder = build_ladder({"gaussian_blur": {"severities": [0.25]}})

    def spread(trajectory):
        rows = run(trajectory, [metric_registry.get("mse")], ladder, fields=["density"],
                   dataset=DatasetInfo(name="advecting_blobs")).rows
        values = rows.loc[rows["degradation"] == "gaussian_blur", "value"].to_numpy()
        return values.std() / values.mean()

    assert spread(AdvectingBlobs()) > 0.01
    assert spread(AdvectingBlobs(velocities=((0.05, 0.02),))) < 1e-9


def test_per_unit_time_grows_the_applied_severity_linearly_in_time():
    """A rate times the time since the trajectory's first frame, recorded beside the rate; on that
    frame it does nothing and the rows say so, whatever the first frame's time."""
    ladder = build_ladder({"drift": {"op": "translate_subpixel", "severities": [0.5, 1.0],
                                     "per_unit_time": True}})
    rows = run(AdvectingBlobs(n_frames=5, t_start=2.0, t_end=6.0), [metric_registry.get("mse")],
               ladder, fields=["density"], dataset=DatasetInfo(name="advecting_blobs")).rows
    drift = rows[rows["degradation"] == "drift"]
    assert drift["severity"].to_numpy() == pytest.approx(
        (drift["severity_nominal"] * (drift["time"] - 2.0)).to_numpy(), rel=1e-12)
    assert drift.loc[drift["time"] == 2.0, "severity_degenerate"].all()
    assert not drift.loc[drift["time"] > 2.0, "severity_degenerate"].any(), (
        "a level that is a no-op only on the first frame must not be excluded at later times")


@pytest.mark.parametrize("op, reason", [
    ("gaussian_blur", "calibrated"),                # a fraction of a spectrum, not a rate
    ("band_attenuate", "unchanged at severity 0"),  # severity 0 damages; damage falls with it
    ("gaussian_impostor", "not ordinal"),           # a probe's severity is not a strength
])
def test_per_unit_time_is_refused_where_a_rate_times_a_time_is_no_strength(op, reason):
    """Only an ordinal, uncalibrated operator whose severity 0 is the identity and whose damage
    grows with its severity starts undamaged and is damaged more as time passes."""
    with pytest.raises(ValueError, match=reason):
        build_ladder({"grow": {"op": op, "severities": [0.1], "per_unit_time": True}})


def test_a_per_unit_time_strength_the_grid_cannot_take_is_dropped_before_the_run():
    """Coarsening by 2 per unit time reaches a factor of 3 at t = 1.5, which does not divide the
    64-cell grid. The level is tried at every frame's time before the loop and dropped, as any
    unsupported strength is, rather than stopping the run inside it at that frame."""
    ladder = build_ladder({"grow": {"op": "coarsen", "severities": [2.0], "per_unit_time": True},
                           "translate_x": {"op": "translate", "severities": [1]}})
    rows = run(AdvectingBlobs(n_frames=4, t_end=1.5), [metric_registry.get("mse")], ladder,
               fields=["density"], dataset=DatasetInfo(name="advecting_blobs")).rows
    assert "grow" not in set(rows["degradation"].astype(str))
    assert "translate_x" in set(rows["degradation"].astype(str))


# --- the feature population: advecting_blobs' options (dataset_specs/06, Sect. 3.5) ---------

#: A non-square grid whose cell centres are dyadic, so a whole-cell move changes no bit of a
#: feature's values, and four of its cell centres 0.5 apart. At ``WIDTH`` that is 20 widths, so
#: a Gaussian's tail at the midpoint is e^-50 of its peak, below the round-off of a field of
#: order 1: the features are isolated to the bit (at the 12 widths of spec 06, Sect. 3.3, the
#: tails overlap at 1.5e-8, which measurably breaks the exact answers below). ``WIDTH`` is 6.4 by
#: 3.2 cells, so the cell-centre mean of a product of two Gaussians is its integral to within
#: e^(-pi^2 (w/h)^2) = e^-101 (Poisson summation), and the Fourier amplitude at the Nyquist
#: wavenumber, e^(-pi^2 (w/h)^2 / 2) = e^-50, leaves the spectral Biot-Savart inversion exact.
POPULATION = {"grid": (256, 128), "n_frames": 1, "t_end": 0.0, "velocities": [[0.0, 0.0]] * 4,
              "centres": [[(64.5 + 128 * i) / 256, (32.5 + 64 * j) / 128]
                          for j in (0, 1) for i in (0, 1)],
              "width": 0.025}
WIDTH = POPULATION["width"]


def test_the_blob_defaults_are_the_closed_form_bit_for_bit():
    """With none of the population's options set, the reader is the three advected blobs of its
    docstring's equation, evaluated in that order, to the last bit: the population's Gaussian
    reduces to the blob's at aspect 1 and orientation 0 operation by operation. The fields the
    options add are empty: no velocity, no vorticity, a uniform pressure of 1."""
    blobs = AdvectingBlobs(grid=(48, 32))
    x, y = blobs.centres
    starts = np.random.default_rng(0).random((3, 2))
    for t in (0, 7, len(blobs) - 1):
        frame = blobs.frame(t, list(AdvectingBlobs.FIELDS))
        expected = np.ones_like(x)
        for centre, velocity in zip(starts, np.asarray(blobs.meta["velocities"]), strict=True):
            cx, cy = (centre + velocity * blobs.times[t]) % 1.0
            squared = ((x - cx + 0.5) % 1.0 - 0.5) ** 2 + ((y - cy + 0.5) % 1.0 - 0.5) ** 2
            expected += 0.1 * (0.06**2 / 0.06**2) * np.exp(-squared / (2.0 * 0.06**2))
        assert np.array_equal(frame["density"][0], expected), f"frame {t} moved off eq. (1)"
        assert not frame["velocity"].any() and not frame["vorticity"].any()
        assert (frame["pressure"] == 1.0).all()


def test_a_vortex_population_carries_the_biot_savart_velocity_of_its_vorticity():
    """The stored vorticity has zero mean (a torus holds no net circulation), and the harness's
    own spectral curl of the stored velocity returns it, with zero divergence and zero mean
    velocity: on a periodic domain those three fix the velocity uniquely, so the inversion and
    its sign are right. A positive vortex turns counter-clockwise: the flow is up (+y) on its
    +x side and down on its -x side. Measured curl error 1.8e-13 of a peak of 1, the round-off
    of two spectral derivatives at |k| up to pi/h; tolerance 1e-12."""
    vortices = AdvectingBlobs(**POPULATION, kinds="vortex", amplitude=[1.0, -1.0, 0.5, -0.5])
    frame = vortices.frame(0, ["velocity", "vorticity"])
    spacing = vortices.grid.spacing
    assert abs(frame["vorticity"].mean()) < 1e-15
    assert np.abs(spectral_vorticity(frame["velocity"], spacing=spacing)
                  - frame["vorticity"][0]).max() < 1e-12
    assert np.abs(divergence(frame["velocity"], spacing=spacing)).max() < 1e-12
    assert np.abs(frame["velocity"].mean(axis=(1, 2))).max() < 1e-15
    i, j = 64, 32  # the cell of the first, positive, vortex
    assert frame["velocity"][1, i + 4, j] > 0 > frame["velocity"][1, i - 4, j]


def test_moving_one_bump_past_1_665_widths_costs_more_than_removing_it():
    """The double penalty in closed form (spec 06, Sect. 3.5, Eq. 5): the other bump cancels in
    the difference, so a bump of height a moved by s costs MSE = 2 pi w^2 a^2 (1 - e^(-s^2/4w^2))
    (the overlap integral of two Gaussians), and removing it costs pi w^2 a^2. The move costs
    more once s > 2 sqrt(ln 2) w = 1.665 w. The candidate gives the first bump a speed of w/2 per
    unit time, so the frames sweep s from 0 to 4 w across the crossover. Measured error 2e-15
    relative, the round-off of the density's level 1 against a difference of order a; the
    cell-centre mean equals the integral far below it (``POPULATION``). Tolerance 1e-12."""
    a, speed, frames = 0.5, WIDTH / 2, {"n_frames": 9, "t_end": 8.0}
    pair = {**POPULATION, **frames, "velocities": [[0.0, 0.0]] * 2,
            "centres": POPULATION["centres"][:2], "amplitude": [a, 0.8]}
    moved, removed = (scored_candidate(AdvectingBlobs(**pair, candidate=candidate), ("mse",),
                                       ("density",))["forecast"].loc["density", "mse"]
                      for candidate in ({"velocities": [[speed, 0.0], [0.0, 0.0]]},
                                        {"amplitude": [0.0, 0.8]}))
    s = speed * moved.index.to_numpy()
    assert moved.to_numpy() == pytest.approx(
        2 * np.pi * WIDTH**2 * a**2 * (1 - np.exp(-(s**2) / (4 * WIDTH**2))), rel=1e-12, abs=0)
    assert removed.to_numpy() == pytest.approx(np.pi * WIDTH**2 * a**2, rel=1e-12)
    crossover = 2 * np.sqrt(np.log(2)) * WIDTH
    assert (s < crossover).any() and (s > crossover).any(), "the frames must straddle it"
    assert ((moved.to_numpy() > removed.to_numpy()) == (s > crossover)).all()


#: The second bump moved by three cells along x and two along y, to cell centres again.
MOVED = [POPULATION["centres"][0], [195.5 / 256, 34.5 / 128], *POPULATION["centres"][2:]]


@pytest.mark.parametrize("candidate, distance", [
    ({"amplitude": [1.0, 0.0, 0.0, 0.6]}, 0.15),  # remove the bump of height 0.3
    ({"amplitude": [1.0, 0.3, 0.2, 0.6]}, 0.10),  # add one of height 0.2 at the empty site
    ({"centres": MOVED}, 0.0),                    # move one by whole cells
], ids=["remove", "add", "move"])
def test_removing_or_adding_a_bump_moves_the_persistence_diagram_by_half_its_height(candidate,
                                                                                     distance):
    """Sublevel sets of bumps on the level 1 of a torus (spec 06, Sect. 3.5, measured there):
    every bump but the tallest is one finite point (1, 1 + a) of the diagram, whose L-infinity
    distance to the diagonal is a/2. Removing a bump that is not the tallest, or adding one, adds
    or deletes only that point, so the bottleneck distance is half its height; a whole-cell move
    changes no value, so no point moves. The bumps sit on cell centres, so each sampled peak is
    its height exactly. Tolerance 1e-12, above gudhi's precision of a few bits (measured
    1.3e-16)."""
    truth = AdvectingBlobs(**POPULATION, amplitude=[1.0, 0.3, 0.0, 0.6], candidate=candidate)
    got = scored_candidate(truth, ("persistence_distance",), ("density",))["forecast"]
    assert got["persistence_distance"].to_numpy() == pytest.approx([distance], abs=1e-12)


def test_increment_w1_is_blind_to_a_whole_cell_move_and_to_a_centred_vortex_flip():
    """Three answers of spec 06, Sect. 3.5, for the one-cell increments.

    * A whole-cell move of one isolated bump permutes the increments, so W1 = 0; with dyadic cell
      centres every value is reproduced to the bit and the zero is exact.
    * Removing the bump of height a sends each of its increments to zero. On each axis the
      monotone coupling then costs the mean absolute increment, and a unimodal periodic row
      varies by twice its peak, so W1 along x is (2 / M) sum over rows of the row's peak,
      a exp(-dy^2 / 2w^2), over M cells; the metric averages the two axes. Measured 4e-16
      relative; tolerance 1e-12.
    * Flipping a vortex centred on a cell centre negates its increments, and a Gaussian symmetric
      about a cell centre has a multiset of increments closed under negation, so W1 = 0; the mean
      the flip shifts is a constant, which only rounds. Each increment is a difference of values
      of order 1, so the rounding is a few units of 2.2e-16 at most; measured 3e-19, tolerance
      1e-15. MSE shows the flip happened: the stored vorticity changes by -2 g + 2 Gamma, with
      Gamma = 2 pi w^2 |a| the vortex's circulation, so MSE = 4 pi w^2 a^2 - 4 Gamma^2 (spec 06,
      Sect. 3.5); measured equal to double precision on the vorticity recomputed from the
      velocity, tolerance 1e-12."""
    bumps = {**POPULATION, "amplitude": [1.0, 0.3, 0.0, 0.6]}
    moved, removed = (scored_candidate(AdvectingBlobs(**bumps, candidate=candidate),
                                       ("increment_w1",), ("density",))["forecast"]
                      for candidate in ({"centres": MOVED}, {"amplitude": [1.0, 0.0, 0.0, 0.6]}))
    assert moved["increment_w1"].to_numpy() == [0.0]
    (nx, ny), (cx, cy) = POPULATION["grid"], POPULATION["centres"][1]
    peaks = [0.3 * np.exp(-(((np.arange(n) + 0.5) / n - c + 0.5) % 1.0 - 0.5) ** 2
                          / (2 * WIDTH**2)) for n, c in ((ny, cy), (nx, cx))]
    expected = (peaks[0].sum() + peaks[1].sum()) / (nx * ny)  # (W1_x + W1_y) / 2
    assert removed["increment_w1"].to_numpy() == pytest.approx([expected], rel=1e-12)

    a = 0.5
    flipped = scored_candidate(
        AdvectingBlobs(**POPULATION, kinds="vortex", amplitude=[1.0, -1.0, a, -a],
                       candidate={"amplitude": [1.0, -1.0, -a, -a]}),
        ("increment_w1", "mse"), ("vorticity",))["forecast"]
    assert flipped["increment_w1"].to_numpy() == pytest.approx([0.0], abs=1e-15)
    circulation = 2 * np.pi * WIDTH**2 * a
    assert flipped["mse"].to_numpy() == pytest.approx(
        [4 * np.pi * WIDTH**2 * a**2 - 4 * circulation**2], rel=1e-12)


@pytest.mark.parametrize("cells", [1, 3])
@pytest.mark.parametrize("placement, centre, assd_offset", [
    ("faces", 0.5, 0.5),            # fronts at x = 24/64 and 40/64, both cell faces
    ("centres", 32.5 / 64, 0.0),    # fronts through the centres of cells 24 and 40
])
def test_a_straight_front_moved_by_whole_cells_has_its_shock_set_distance(placement, centre,
                                                                          assd_offset, cells):
    """A stripe of half-width 8 cells running along y, raising the pressure from 1 to 2.5 across
    a tanh of a quarter cell, moved by s whole cells along x. The detector flags a cell whose
    two neighbours along an axis differ by the ratio 1.805 (``shock_set_distance`` card, Eq. 1).
    A front on a cell face flags the cell on each side of it, ratios 2.47 and 2.43, so each
    flagged cell's partner is s - 1 or s cells away and ASSD = (s - 1/2) dx (card, Eq. 3); a front
    through a cell centre flags that cell only (its neighbours see 1.75 and 1.43), so
    ASSD = s dx. The Hausdorff distance is s dx in both. The two fronts of the stripe are 16
    cells apart, more than twice the move, so each finds its own partner (spec 06, Sect. 3.5).
    The distances are exact multiples of the spacing; tolerance 1e-12."""
    dx = 1 / 64
    truth = AdvectingBlobs(grid=(64, 48), n_frames=1, t_end=0.0, velocities=[[0.0, 0.0]],
                           centres=[[centre, 0.5]], kinds="front", directions=[[0, 1]],
                           width=8 * dx, amplitude=1.5,
                           candidate={"centres": [[centre + cells * dx, 0.5]]})
    got = scored_candidate(truth, ("shock_set_distance", "shock_set_hausdorff"),
                           ("pressure",))["forecast"]
    assert got["shock_set_distance"].to_numpy() == pytest.approx(
        [(cells - assd_offset) * dx], rel=1e-12), placement
    assert got["shock_set_hausdorff"].to_numpy() == pytest.approx([cells * dx], rel=1e-12)


def test_a_background_is_band_limited_has_its_rms_and_cancels_from_a_pointwise_error():
    """The background is ``_apply_filter`` on seeded white noise, so it holds no power outside
    its band (exact, up to the round-off of two FFTs), its expected mean square is rms^2, and,
    being the same in the truth and the candidate, it cancels from a pointwise error, which keeps
    the flat background's closed form (spec 06, Sect. 3.5): removing a bump of height a costs
    pi w^2 a^2 (measured to 2e-16; tolerance 1e-12). With a flat spectrum over the band
    1 <= |k| <= 64 (slope -1) about 1.3e4 modes, half of them independent, carry the variance,
    so one draw's mean square scatters by about sqrt(2 / 6.4e3) = 1.8%; the tolerance of 10%
    on the rms is over five standard deviations."""
    band = {"slope": -1.0, "k_min": 1, "k_max": 64}
    flat = AdvectingBlobs(**POPULATION, amplitude=0.0, seed=3,
                          background={"rms": {"density": 0.05, "pressure": 0.2}, **band})
    frame = flat.frame(0, ["density", "pressure"])
    for name, rms in (("density", 0.05), ("pressure", 0.2)):
        b = frame[name][0] - 1.0
        power = np.abs(np.fft.fftn(b)) ** 2
        outside = (wavenumber_magnitude(b.shape) < 1) | (wavenumber_magnitude(b.shape) > 64)
        assert power[outside].sum() < 1e-20 * power.sum(), f"{name} has power outside its band"
        assert np.sqrt(np.mean(b**2)) == pytest.approx(rms, rel=0.1), name
    a = 0.3
    truth = AdvectingBlobs(**POPULATION, amplitude=[1.0, a, 0.0, 0.6], seed=3,
                           background={"rms": {"density": 0.05}, **band},
                           candidate={"amplitude": [1.0, 0.0, 0.0, 0.6]})
    got = scored_candidate(truth, ("mse",), ("density",))["forecast"]
    assert got["mse"].to_numpy() == pytest.approx([np.pi * WIDTH**2 * a**2], rel=1e-12)


@pytest.mark.parametrize("options, match", [
    ({"kinds": "blob"}, "kinds"),
    ({"amplitude": [-0.1, 0.1, 0.1]}, "non-negative"),
    ({"width": [0.06, 0.06]}, "one value per velocity"),
    ({"aspect": 0.0}, "positive"),
    ({"kinds": "front", "directions": [[2, 2], [0, 1], [0, 0]]}, "coprime"),
    ({"directions": [[0, 1], [0, 0], [0, 0]]}, "coprime"),        # a stripe on a bump
    ({"kinds": "front", "diffusivity": 1e-5}, "zero with a front"),
    ({"background": {"rms": {"velocity": 0.1}, "slope": 3, "k_min": 1, "k_max": 8}},
     "background"),
    ({"background": {"rms": {"density": 0.1}, "slope": 3, "k_min": 0, "k_max": 0.5}}, "band"),
])
def test_the_population_refuses_what_it_cannot_build(options, match):
    with pytest.raises(ValueError, match=match):
        AdvectingBlobs(**options)


def test_a_background_that_makes_the_density_non_positive_is_refused_when_read():
    blobs = AdvectingBlobs(background={"rms": {"density": 2.0}, "slope": 0, "k_min": 1,
                                       "k_max": 8})
    with pytest.raises(ValueError, match="not positive"):
        blobs.frame(0, ["density"])


# --- transport pairs with a known distance: advecting_blobs' potential (dataset_specs/07) -------

#: One static frame without blobs (``g = 1``) on a non-square grid.
UNIFORM = {"grid": (64, 48), "n_frames": 1, "t_end": 0.0, "amplitude": 0.0}
#: Saumier, Agueh & Khouider (2015), Sect. 5.1: u = (1/k) cos(2 pi x) sin(2 pi y), which is
#: (1/2k) [sin(k_+ . x) - sin(k_- . x)] with k_+- = 2 pi (1, +-1): the two oblique modes of
#: spec 07, Eq. 4, each with |a| = lambda = (2 pi)^2 / k, here 0.45.
SAUMIER = [[1, 1, 0.45, np.pi / 2], [1, -1, -0.45, np.pi / 2]]
#: Mass levels of 2^16 sub-cells, on which ``circle_w2`` of a smooth profile is within 4e-10 of
#: the continuous distance (spec 07, Sect. 3.2: the cell-constant reading converges as h^2).
LEVELS = (np.arange(2**16) + 0.5) / 2**16


def transport(truth: AdvectingBlobs) -> pd.DataFrame:
    """``wasserstein`` and ``h_minus_one`` on the reader's candidate, by time, through the
    pipeline's prediction path."""
    return scored_candidate(truth, ("wasserstein", "h_minus_one"), ("density",))[
        "forecast"].loc["density"]


def axis_profile(mode: Sequence[float], shift: float = 0.0) -> np.ndarray:
    """``1 + a cos(2 pi m (x - shift) + phi)`` on ``LEVELS``, for an axis mode
    ``[m_x, m_y, a, phi]`` with one of ``m_x, m_y`` zero."""
    return 1.0 + mode[2] * np.cos(2 * np.pi * (mode[0] + mode[1]) * (LEVELS - shift) + mode[3])


@pytest.mark.parametrize("mode", [(1, 0), (2, 1)], ids=["axis", "oblique"])
def test_one_mode_against_the_uniform_density_is_at_w2_equal_to_h_minus_one(mode):
    """Spec 07, Eq. 5: with ``g = 1`` and one mode, ``f = 1 + a cos(k . x + phi)`` and the
    displacement is ``(a / |k|) |sin|``, so W_2 = a / (sqrt(2) |k|) for every lattice wavevector;
    H^-1 of ``a cos(k . x)`` is the same number (the ``h_minus_one`` card, Eq. 3), so the two
    metrics agree exactly at every amplitude. From the deformed side the solve is one Laplacian
    step (the ``wasserstein`` worked example), exact to round-off up to a = 0.998, a density
    ratio of 999; measured 4e-16, tolerance 1e-12. From the uniform side it iterates and
    interpolates: measured 1.3e-7 and 2.3e-6 on 64 x 48 at a = 0.3, falling 15 to 16 times on
    128 x 96 (fourth order in the cell size); tolerance 1e-5, and at least a tenfold fall.
    ``h_minus_one`` is a difference, exact both ways (measured 3e-16)."""
    k = 2 * np.pi * np.hypot(*mode)
    for a in (0.3, 0.998):
        got = transport(AdvectingBlobs(**UNIFORM, potential=[[*mode, a, 0.4]],
                                       candidate={"potential": None}))
        assert got.to_numpy() == pytest.approx(a / (np.sqrt(2) * k), rel=1e-12), a
    errors = []
    for grid in ((64, 48), (128, 96)):
        got = transport(AdvectingBlobs(**{**UNIFORM, "grid": grid},
                                       candidate={"potential": [[*mode, 0.3, 0.4]]}))
        exact = 0.3 / (np.sqrt(2) * k)
        assert got["h_minus_one"].to_numpy() == pytest.approx(exact, rel=1e-12)
        errors.append(abs(got["wasserstein"].iloc[0] / exact - 1))
    assert errors[0] < 1e-5 and errors[1] < errors[0] / 10, f"relative errors {errors}"


@pytest.mark.parametrize("amplitude", [0.0, 3.0], ids=["uniform_target", "blob_target"])
def test_saumiers_manufactured_map_has_its_exact_distance_both_ways(amplitude):
    """Saumier et al.'s example: ``f = g(x + grad u) det(I + D^2 u)`` is carried to ``g`` by
    the optimal map ``x + grad u`` (convex, lambda < 1/2 within the reader's bound), so
    W_2^2 = <f |grad u|^2> / <f> (Saumier et al., Eq. 3; spec 07, Eq. 3), evaluated by
    quadrature on the grid refined four times, where it agrees with eight times to 2e-16. With
    ``g = 1`` that is lambda / (sqrt(2) 2 pi) (spec 07, Eq. 6), to 1e-14; with the three moving
    blobs at amplitude 3, ``f`` ranges over a factor of 25 and the distance changes from frame
    to frame. ``wasserstein`` from ``f`` to ``g = 1`` measured 8.6e-14 (tolerance 1e-12);
    otherwise 2e-7 to 1e-6 on 64 x 48, either way round (tolerance 1e-5)."""
    options = {"grid": (64, 48), "n_frames": 3, "t_end": 10.0, "amplitude": amplitude}
    fine = AdvectingBlobs(**{**options, "grid": (256, 192)}, potential=SAUMIER)
    exact = []
    for t in range(len(fine)):
        f = fine.frame(t, ["density"])["density"][0]
        exact.append(np.sqrt(np.mean(f * (fine.displacement**2).sum(axis=0)) / f.mean()))
    if amplitude == 0:
        assert exact == pytest.approx([0.45 / (np.sqrt(2) * 2 * np.pi)] * 3, rel=1e-14)
    else:
        assert np.ptp(exact) > 1e-3 * np.mean(exact), "the blobs must change the distance"
    forward = transport(AdvectingBlobs(**options, potential=SAUMIER,
                                       candidate={"potential": None}))["wasserstein"]
    reverse = transport(AdvectingBlobs(**options, candidate={"potential": SAUMIER}))[
        "wasserstein"]
    assert forward.to_numpy() == pytest.approx(exact, rel=1e-12 if amplitude == 0 else 1e-5)
    assert reverse.to_numpy() == pytest.approx(exact, rel=1e-5)


def test_a_product_pair_is_at_the_sum_of_its_two_circle_distances():
    """Two axis modes make ``D^2 u`` diagonal, so with ``g = 1`` the density is the product
    ``p(x) q(y)`` of two one-mode profiles. The squared torus distance is the sum of the squared
    circle distances along the axes, and the product of the two optimal circle plans attains
    the lower bound that sum gives, so W_2^2(p q, p' q') = W_2^2(p, p') + W_2^2(q, q') (spec 07,
    Eq. 8, its author's derivation), each from ``circle_w2``. Measured 8e-8 and 5e-7 on 64 x 48,
    the two ways round; tolerance 1e-5."""
    reference, candidate = [[1, 0, 0.5, 0.0], [0, 2, 0.3, 1.0]], [[1, 0, 0.2, 2.0], [0, 1, 0.4, 0.0]]
    pair = AdvectingBlobs(**UNIFORM, potential=reference, candidate={"potential": candidate})
    x, y = pair.centres
    assert pair.frame(0, ["density"])["density"][0] == pytest.approx(
        (1 + 0.5 * np.cos(2 * np.pi * x)) * (1 + 0.3 * np.cos(4 * np.pi * y + 1.0)), rel=1e-14)
    exact = np.hypot(*(circle_w2(axis_profile(r), axis_profile(c))
                       for r, c in zip(reference, candidate, strict=True)))
    swapped = AdvectingBlobs(**UNIFORM, potential=candidate, candidate={"potential": reference})
    for truth in (pair, swapped):
        assert transport(truth)["wasserstein"].to_numpy() == pytest.approx([exact], rel=1e-5)


def test_a_translation_keeps_its_circle_distance_on_a_product_and_its_bracket_on_blobs():
    """The ``translate`` degradation moves the field by whole cells, s along one axis.

    * A product ``p(x) q(y)`` moved along x is at the circle distance of ``p`` from its
      translate, and along y of ``q`` (spec 07, Eq. 8 with one factor unchanged), computed for
      the analytic profile shifted by s; measured 4e-8 to 7e-8, tolerance 1e-5. On the torus
      that is below s for a positive density (spec 07, Sect. 3.3).
    * The radial blobs have no closed form, but a certified bracket: projecting to one axis
      does not increase distances, so W_2 is at least the circle distance of the x-marginals,
      and the translation plan bounds it by s (spec 07, Sect. 3.3). Measured inside it with a
      margin of 23% or more below; the marginal is summed on 16384 cells along x."""
    ladder = build_ladder({"translate_x": {"op": "translate", "severities": [1, 4, 16]},
                           "translate_y": {"op": "translate", "severities": [2],
                                           "options": {"axis": "y"}}})
    product = [[1, 0, 0.5, 0.0], [0, 2, 0.3, 1.0]]
    rows = run(AdvectingBlobs(**UNIFORM, potential=product), [metric_registry.get("wasserstein")],
               ladder, fields=["density"], dataset=DatasetInfo(name="advecting_blobs")).rows
    moved = rows[rows["degradation"].astype(str).str.startswith("translate")]
    assert len(moved) == 4
    for row in moved.itertuples():
        axis = 0 if row.degradation == "translate_x" else 1
        s = row.severity / UNIFORM["grid"][axis]
        exact = circle_w2(axis_profile(product[axis]), axis_profile(product[axis], s))
        assert row.value == pytest.approx(exact, rel=1e-5), (row.degradation, row.severity)
        assert exact < s

    blobs = {"n_frames": 3, "t_end": 10.0, "amplitude": 3.0}
    rows = run(AdvectingBlobs(**blobs, grid=(64, 48)), [metric_registry.get("wasserstein")],
               ladder, fields=["density"], dataset=DatasetInfo(name="advecting_blobs")).rows
    fine = AdvectingBlobs(**blobs, grid=(16384, 48))
    for row in rows[rows["degradation"] == "translate_x"].itertuples():
        marginal = fine.frame(row.frame_index, ["density"])["density"][0].sum(axis=1)
        cells = int(row.severity) * 16384 // 64
        assert circle_w2(marginal, np.roll(marginal, cells)) < row.value < row.severity / 64


@pytest.mark.parametrize("options", [
    {"potential": [[1, 1, 0.6, 0.0], [1, -1, 0.4, 0.0]]},  # sum |a| = 1: convexity not certain
    {"potential": [[0, 0, 0.3, 0.0]]},                       # k = 0 is not a mode
    {"potential": [[0.5, 1, 0.3, 0.0]]},                     # not periodic on the unit square
    {"potential": [[1, 1, 0.3]]},                            # a mode is [m_x, m_y, a, phi]
    {"potential": [[1, 0, 0.3, 0.0]],                        # no closed form at x + grad u
     "background": {"rms": {"density": 0.01}, "slope": 0, "k_min": 1, "k_max": 8}},
])
def test_the_transport_pair_refuses_a_potential_without_a_known_optimal_map(options):
    with pytest.raises(ValueError, match="potential"):
        AdvectingBlobs(**options)


# --- random fields with known statistics (dataset_specs/09) -----------------------------------

#: A Gaussian field with the broken power law of spec 09's first configuration (shell slopes 5/3
#: then 3, broken at k = 16) on a non-square grid, every frame an independent draw.
BROKEN = {"grid": (128, 96), "slopes": [5 / 3, 3.0], "k_break": 16.0, "k_min": 4.0,
          "k_max": 40.0, "n_frames": 12}


def matern(grid: tuple[int, int], rho: float, nu: float = 1.0) -> dict:
    """``RandomField`` options of a Matern field of smoothness ``nu`` and length ``rho`` cells of
    the x axis, on every mode below the smaller Nyquist line."""
    return {"grid": grid, "slopes": [-1.0, 2 * nu + 1], "k_min": 1.0,
            "k_break": grid[0] * np.sqrt(2 * nu) / (2 * np.pi * rho), "k_max": min(grid) // 2 - 1}


def separation_curves(result) -> pd.DataFrame:
    """Frame mean of ``increment_flatness.by_separation``, by field and separation."""
    curves = result.companions[result.companions["metric"] == "increment_flatness.by_separation"]
    return curves.groupby(["field", "coordinate"], observed=True)["value"].mean()


def test_a_random_field_has_its_spectrum_and_a_solenoidal_velocity_whose_curl_it_stores():
    """The draw puts power only on the band, in the prescribed shape: a power law
    ``v ~ |k|^-(beta + 1)`` (a shell spectrum ``k^-beta``, spec 09, Sect. 3.2), and the Matern
    density ``(1 + alpha^2 kappa^2)^-(nu + 1)`` of Porcu et al. (2023), Eq. 23, with
    ``alpha = rho / sqrt(2 nu)`` and ``kappa = 2 pi k`` on the unit square. The harness's own
    spectral curl of the velocity returns the stored vorticity and its divergence vanishes; both
    are round-off of two spectral derivatives at |kappa| up to 2 pi 40, measured 1e-14 of the
    vorticity's largest value; tolerance 1e-12."""
    power_law = RandomField(grid=(128, 96), slopes=[5 / 3], k_min=4.0, k_max=40.0, n_frames=1)
    k = wavenumber_magnitude((128, 96))
    band = (k >= 4) & (k <= 40)
    t2 = power_law.transfers["density"] ** 2
    assert not t2[~band].any(), "power outside the band"
    assert t2[band] / t2[band].max() == pytest.approx((k[band] / 4.0) ** -(5 / 3 + 1), rel=1e-12)

    rho, nu = 6.0, 1.5
    options = matern((128, 96), rho, nu)
    alpha = rho / 128 / np.sqrt(2 * nu)  # rho cells of the x axis, in domain lengths
    density = RandomField(**options, n_frames=1).transfers["density"] ** 2
    shape = (1 + alpha**2 * (2 * np.pi * k) ** 2) ** -(nu + 1)
    inside = (k >= 1) & (k <= options["k_max"])
    assert density[inside] / density[inside].max() == pytest.approx(
        shape[inside] / shape[inside].max(), rel=1e-12)

    frame = RandomField(**BROKEN).frame(3, ["velocity", "vorticity"])
    spacing = power_law.grid.spacing
    scale = np.abs(frame["vorticity"]).max()
    assert np.abs(spectral_vorticity(frame["velocity"], spacing=spacing)
                  - frame["vorticity"][0]).max() < 1e-12 * scale
    assert np.abs(divergence(frame["velocity"], spacing=spacing)).max() < 1e-12 * scale


@pytest.mark.parametrize("options", [BROKEN, {**matern((192, 128), 8.0), "anisotropy": 2.0,
                                               "n_frames": 12}], ids=["broken", "anisotropic"])
def test_a_gaussian_field_has_flatness_3_and_its_exact_increment_variance_along_each_axis(
        options):
    """Every increment of a Gaussian field is Gaussian, so the increment flatness is 3 on every
    field and axis, before and after a whole-cell translation. A translation by l cells along
    axis j makes the MSE the empirical increment variance, whose expectation is spec 09, Eq. 3,
    ``S_2(l) = sum_k q_k`` with ``q_k = sigma^2 T_k^2 / M * 2 (1 - cos(2 pi k_j l / N_j))``
    for density (``T`` the reader's transfer; vorticity likewise with its own), and whose
    spread is :func:`gaussian_mean_square`'s. The anisotropic Matern field (a = 2: correlation
    lengths 16 and 4 cells of the x axis along x and y) has a different correlation function
    along each axis, so this pins both correlation lengths.

    Tolerances: the frame mean of the MSE within four of its exact standard errors; the frame
    mean of the flatness within 0.08 of 3, four standard errors of a 12-frame mean at the largest
    per-frame spread measured, 0.07 (0.02 to 0.07 across fields, spectra and six seeds, whose
    12-frame means all lay within 0.03 of 3)."""
    shifts = [1, 4, 16]
    ladder = build_ladder({"shift_x": {"op": "translate", "severities": shifts},
                           "shift_y": {"op": "translate", "severities": shifts,
                                       "options": {"axis": "y"}}})
    field = RandomField(**options)
    result = run(RecomputingTrajectory(field), [metric_registry.get(n) for n in
                                                ("mse", "increment_flatness")],
                 ladder, fields=["density", "velocity", "vorticity"],
                 dataset=DatasetInfo(name="random_field"))
    rows = result.rows
    flatness = rows[rows["metric"] == "increment_flatness"].groupby(
        ["field", "degradation", "level"], observed=True)["value"].mean()
    assert np.abs(flatness - 3.0).max() < 0.08, flatness.to_string()

    mse = rows[rows["metric"] == "mse"].groupby(["field", "degradation", "level"],
                                                observed=True)["value"].mean()
    m_x, m_y = np.meshgrid(*[np.fft.fftfreq(n) * n for n in field.grid.shape], indexing="ij")
    scales = {"density": field.meta["density_sigma"] ** 2, "vorticity": 1.0}
    for name, scale in scales.items():
        per_mode = scale * field.transfers[name] ** 2 / m_x.size
        for label, m, n in (("shift_x", m_x, field.grid.shape[0]),
                            ("shift_y", m_y, field.grid.shape[1])):
            for level, shift in enumerate(shifts, start=1):
                expected, spread = gaussian_mean_square(
                    per_mode * 2 * (1 - np.cos(2 * np.pi * m * shift / n)))
                got = mse[name, label, level]
                assert abs(got - expected) < 4 * spread / np.sqrt(len(field)), (
                    f"{name} {label} {shift}: MSE {got:.6g}, Eq. 3 gives {expected:.6g} "
                    f"+- {spread / np.sqrt(len(field)):.2g}")


def test_two_gaussian_fields_are_their_amplitude_gap_apart_in_increment_w1():
    """On the line the 1-Wasserstein distance is the L1 distance of the quantile functions
    (Peyre & Cuturi 2019, Remark 2.30, Eq. 2.36, as ``increment_w1`` cites), and those of two
    centred normals are ``s_i Phi^-1``, so ``W1 = |s_1 - s_2| sqrt(2/pi)`` (spec 09, Eq. 5). The
    candidate is an independent realisation (another seed) at 1.5 times the density amplitude;
    along axis j both increments have standard deviation ``sigma_i sqrt(S_2(1))``, and the
    metric averages the two axes. Measured per-frame spread 5.4%, so a 12-frame mean has a
    standard error of 1.6%; tolerance 6%."""
    truth = RandomField(**BROKEN, candidate={"seed": 1, "density_sigma": 0.075})
    rows = run(truth, [metric_registry.get("increment_w1")], build_ladder({}),
               fields=["density"], dataset=DatasetInfo(name="random_field"),
               prediction=truth.predictions()).rows
    got = rows.loc[rows["degradation"] == "forecast", "value"].mean()
    covariance = np.fft.ifft2(truth.transfers["density"] ** 2).real
    s2 = 2 * (covariance[0, 0] - np.array([covariance[1, 0], covariance[0, 1]]))
    expected = np.mean(abs(0.05 - 0.075) * np.sqrt(s2)) * np.sqrt(2 / np.pi)
    assert got == pytest.approx(expected, rel=0.06)


def test_the_hill_estimate_of_a_gaussian_field_is_its_population_value():
    """A Gaussian has extreme-value index 0, but at a fixed order k of n the Hill estimate
    (Hill 1975; ``tail_index`` card, Eq. 2) converges to ``E[ln(X / u) | X > u]`` for
    ``X = |Z|`` and ``u`` its upper ``p = k/n`` quantile (spec 09, Sect. 3.2). That depends on
    neither the spectrum nor the amplitude, since every increment is a scaled normal and the
    estimate is scale-free: 0.0928 at ``k = 256 = sqrt(n)`` on 256^2, the registered order.
    Measured per-frame spread 0.0027 (spec 09 and here), so an 8-frame mean has a standard
    error of 0.001; tolerance 0.004."""
    n = 256 * 256
    p = np.ceil(np.sqrt(n)) / n
    u = stats.norm.isf(p / 2)
    population = integrate.quad(lambda x: np.log(x / u) * 2 * stats.norm.pdf(x), u,
                                np.inf)[0] / p
    assert population == pytest.approx(0.0928, abs=5e-5)
    rows = run(RandomField(grid=(256, 256), n_frames=8), [metric_registry.get("tail_index")],
               build_ladder({}), fields=["density"], dataset=DatasetInfo(name="random_field")).rows
    assert rows["value"].mean() == pytest.approx(population, abs=0.004)


@pytest.mark.parametrize("alpha", [2.0, 4.0])
def test_pareto_spikes_give_the_hill_estimate_their_tail_index(alpha):
    """Spikes of Pareto size ``floor (1 + Lomax(alpha))`` on a fraction 2/sqrt(n) of the cells:
    each makes two one-cell increments per axis of about its own size, so when the k + 1
    largest increments are all spike increments the Hill estimate is a mean of log-ratios of
    Pareto values, exponential with mean 1/alpha (spec 09, Sect. 3.7). That needs more than
    k/2 spikes, a fraction of 1/(2 sqrt(n)), which fails as the catalog's G2 reviewer found; 2/
    sqrt(n) is the margin the catalog asks for, and the floor must exceed the largest Gaussian
    increment, checked here. Measured on 256 x 192 over four seeds: 24-frame means 4.6% low to
    0.6% high at alpha = 2 and 5.2% low to 0.4% high at alpha = 4, with a per-frame spread of 7%
    to 10% (a standard error of 2% at most); tolerance 7%."""
    grid, floor = (256, 192), 0.3
    plain = RandomField(grid=grid, k_max=95, n_frames=24)
    gaussian = plain.frame(0, ["density"])["density"][0]
    assert floor > max(np.abs(np.roll(gaussian, -1, axis) - gaussian).max() for axis in (0, 1))
    spiked = RandomField(grid=grid, k_max=95, n_frames=24, spikes={
        "fraction": 2 / np.sqrt(grid[0] * grid[1]), "alpha": alpha, "floor": floor})
    rows = run(spiked, [metric_registry.get("tail_index")], build_ladder({}),
               fields=["density"], dataset=DatasetInfo(name="random_field")).rows
    assert rows["value"].mean() == pytest.approx(1 / alpha, rel=0.07)


@pytest.mark.parametrize("transform, sigma, tolerance", [("hermite2", 0.3, 0.08),
                                                         ("exp", 0.5, 0.12)])
def test_intermittent_fields_have_their_exact_flatness_at_every_separation(transform, sigma,
                                                                           tolerance):
    """Three non-Gaussian increment laws with exact flatness at every separation l, read from
    ``increment_flatness.by_separation`` and averaged over frames, on the Matern field
    (rho = 4 cells, nu = 1) whose correlation ``c(l)`` per axis is ``ifft(T^2)``:

    * density ``1 + sigma (g^2 - 1)``: the increment is a product of two independent normals,
      so its flatness is exactly 9 at every l (spec 09, Eq. 8);
    * density ``exp(sigma g - sigma^2/2)``: from the bivariate normal's moment generating
      function, ``E[d^q] = sum_j C(q, j) (-1)^j exp(sigma^2/2 ((q-j)^2 + j^2 + 2 (q-j) j c))``
      (spec 09, Eq. 9), so the flatness rises from about 5.9 at large l to 7.9 at one cell;
    * multifractal vorticity and velocity (lambda = 0.05): conditional on the log-volatility
      the increment is Gaussian with variance ``sum_y A_l(y) e^(2(omega - V))``, with
      ``A_l = (K(y + l e_j) - K(y))^2`` for the field's kernel K, so the flatness is
      ``3 sum A A' e^(4 C_omega) / (sum A)^2``, two FFTs (spec 09, Eq. 11; the construction of
      Lakhal et al. 2025, Eqs. 1-4). Velocity is read longitudinally; its kernel is the
      Biot-Savart velocity of the vorticity's.

    The metric averages the per-axis flatnesses, so the target is the mean over axes. A sample
    flatness of heavy-tailed increments is a noisy ratio, biased low on few independent areas
    (spec 09, Sect. 3.5), so the frame mean is compared at a stated tolerance: over eight seeds
    of 48 frames the 48-frame means lay between -2.0% and +4.4% of the exact value (hermite2),
    -2.2% and +7.2% (exp), and -4.5% and +1.5% (multifractal, both fields, both transforms);
    tolerances 8%, 12% and 8%."""
    field = RandomField(**matern((256, 192), 4.0), n_frames=48, transform=transform,
                        density_sigma=sigma, multifractal_lambda=0.05)
    result = run(RecomputingTrajectory(field), [metric_registry.get("increment_flatness")],
                 build_ladder({}), fields=["density", "velocity", "vorticity"],
                 dataset=DatasetInfo(name="random_field"))
    curves = separation_curves(result)

    correlation = np.fft.ifft2(field.transfers["density"] ** 2).real
    weight = np.exp(4 * np.fft.ifft2(field.chaos_transfer**2).real)
    vorticity = np.fft.ifft2(field.transfers["vorticity"]).real
    kernels = {"vorticity": [(vorticity, 0), (vorticity, 1)],
               "velocity": list(zip(biot_savart(vorticity, field.grid), (0, 1), strict=True))}

    def moment(q: int, c: float) -> float:
        return sum(comb(q, j) * (-1) ** j * np.exp(sigma**2 / 2 * ((q - j) ** 2 + j**2
                                                                   + 2 * (q - j) * j * c))
                   for j in range(q + 1))

    for (name, separation), got in curves.items():
        lag = int(separation)
        if name == "density":
            per_axis = [9.0 if transform == "hermite2"
                        else moment(4, c) / moment(2, c) ** 2
                        for c in (correlation[lag, 0], correlation[0, lag])]
            limit = tolerance
        else:
            per_axis = []
            for kernel, axis in kernels[name]:
                a = (np.roll(kernel, -lag, axis) - kernel) ** 2
                per_axis.append(3 * np.sum(a * np.fft.ifft2(np.fft.fft2(a) * np.fft.fft2(
                    weight)).real) / a.sum() ** 2)
            limit = 0.08
        assert got == pytest.approx(np.mean(per_axis), rel=limit), (
            f"{name} at {lag} cells: frame-mean flatness {got:.3f}, exact {np.mean(per_axis):.3f}")
    density = curves["density"].to_numpy()
    if transform == "exp":
        assert density[0] > density[-1] + 1, "the log-normal flatness must rise as l falls"


def test_an_ornstein_uhlenbeck_field_decorrelates_mode_by_mode():
    """Each Fourier mode follows an Ornstein-Uhlenbeck process sampled exactly (spec 09, Eq. 7),
    so its correlation at a lag of n frames is ``a_k^n``, ``a_k = exp(-dt / tau_k)``, with
    ``tau_k = tau (|k| / k_min)^-p``. The candidate ``tau = inf`` repeats the first frame (the
    persistence candidate), so the MSE against frame n is the mean square of
    ``g_n - g_0``, whose modes are Gaussian of variance ``2 v_k (1 - a_k^n)``: expectation and
    spread from :func:`gaussian_mean_square`. A flat spectrum spreads the variance over all
    3e3 modes of the band, so one frame's MSE scatters by a few percent. Frames are correlated
    in time, so each frame is held to four of its own standard errors; the first frame is the
    candidate's own, an MSE of zero."""
    truth = RandomField(grid=(96, 64), slopes=[-1.0], k_min=1.0, k_max=31.0, n_frames=9,
                        t_end=8.0, tau=4.0, candidate={"tau": float("inf")})
    rows = run(truth, [metric_registry.get("mse")], build_ladder({}), fields=["density"],
               dataset=DatasetInfo(name="random_field"), prediction=truth.predictions()).rows
    forecast = rows[rows["degradation"] == "forecast"].sort_values("frame_index")
    per_mode = truth.meta["density_sigma"] ** 2 * truth.transfers["density"] ** 2 / 96 / 64
    assert forecast["value"].iloc[0] < 1e-30
    for n, got in enumerate(forecast["value"].to_numpy()[1:], start=1):
        expected, spread = gaussian_mean_square(2 * per_mode * (1 - truth.decay**n))
        assert abs(got - expected) < 4 * spread, (
            f"lag {n}: MSE {got:.4g}, the correlation a^n gives {expected:.4g} +- {spread:.2g}")


#: The default ladder's linear, shift-invariant operators, and noise added to a Gaussian field:
#: each leaves a Gaussian field Gaussian (spec 09, Sect. 3.8).
LINEAR = ["gaussian_blur", "box_blur", "disk_blur", "epanechnikov_blur", "lowpass_ideal",
          "lowpass_butterworth", "highpass_ideal", "highpass_butterworth", "band_attenuate",
          "translate_subpixel", "additive_noise", "gaussian_impostor"]


def test_linear_degradations_keep_a_gaussian_field_gaussian():
    """A linear shift-invariant operator maps a Gaussian field to a Gaussian field with per-mode
    variance ``|T_k|^2 v_k``, and adding independent Gaussian noise or randomising the phases of
    complex Gaussian coefficients does too (spec 09, Sect. 3.8), so the increment flatness stays
    3 on every severity level of the default ladder: a blind axis with an exact answer. Smoothing
    lengthens the correlation and so widens the frame-to-frame spread, measured 0.03 to 0.28 per
    frame on 128 x 96, so each level is held to four standard errors of its own 12-frame mean,
    and the spread must stay small enough that this still separates 3 from a non-Gaussian law."""
    rows = run(RandomField(**BROKEN), [metric_registry.get("increment_flatness")],
               build_ladder(build_job(compose_config()).degradation, only=LINEAR),
               fields=["density"], dataset=DatasetInfo(name="random_field")).rows
    assert set(rows["degradation"].astype(str)) == {"identity", *LINEAR}
    levels = rows.groupby(["degradation", "level"], observed=True)["value"].agg(
        ["mean", "std", "count"])
    error = levels["std"] / np.sqrt(levels["count"])
    assert (error < 0.1).all(), levels.to_string()
    assert (np.abs(levels["mean"] - 3.0) < 4 * error).all(), levels.to_string()


@pytest.mark.parametrize("options, match", [
    ({"slopes": [5 / 3, 3]}, "k_break"),
    ({"slopes": [5 / 3], "k_break": 16.0}, "k_break"),
    ({"k_max": 128}, "Nyquist"),
    ({"transform": "square"}, "transform"),
    ({"anisotropy": 0.0}, "anisotropy"),
    ({"tau": 1.0, "multifractal_lambda": 0.05}, "multifractal"),
    ({"spikes": {"fraction": 0.01, "alpha": 2.0}}, "spikes"),
    ({"k_min": 0.0}, "band"),
])
def test_the_random_field_refuses_what_it_cannot_build(options, match):
    with pytest.raises(ValueError, match=match):
        RandomField(**options)
