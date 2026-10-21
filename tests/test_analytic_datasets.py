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
"""

from __future__ import annotations

import subprocess
import sys

import numpy as np
import pytest

from fmeval import CONFIGS, REPO
from fmeval.config import build_job, compose_config
from fmeval.data.analytic import SodShockTube, TaylorGreen2D
from fmeval.data.base import READERS
from fmeval.data.readers import open_trajectory
from fmeval.derived import RecomputingTrajectory
from fmeval.external.kinet_spectral import divergence, spectral_derivative
from fmeval.ladder import build_ladder
from fmeval.pipeline import DatasetInfo, run
from metrics import registry as metric_registry
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


@pytest.fixture(scope="module")
def sod() -> SodShockTube:
    return SodShockTube()


def test_sod_star_state_matches_the_published_exact_solution(sod):
    """Toro (2009), Table 4.3, Test 1 (Sod's data, Table 4.1): p*, u*, rho*_L, rho*_R to the
    five decimals printed. Marzouk (2020), Table 2: the fan head and tail and the shock
    speed, to the five decimals printed."""
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
    g, s = 1.4, sod.speeds["shock"]

    def balance(rho, u, p):
        energy = p / (g - 1) + 0.5 * rho * u**2
        return np.array([rho * u - s * rho,
                         rho * u**2 + p - s * rho * u,
                         (energy + p) * u - s * energy])

    star = balance(sod.star["density_right"], sod.star["velocity"], sod.star["pressure"])
    assert star == pytest.approx(balance(0.125, 0.0, 0.1), rel=1e-12, abs=1e-12)


def test_sod_rarefaction_keeps_its_invariants(sod):
    """Across the left rarefaction the flow is isentropic and the Riemann invariant
    ``u + 2a/(gamma - 1)`` is carried unchanged from the left state: the relations behind
    Toro (2009) eqs. (4.53)-(4.56), Sects. 4.4-4.5. Checked cell by cell inside the fan."""
    g = 1.4
    frame = sod.frame(len(sod) - 1, ["density", "velocity", "pressure"])
    xi = (sod.centres[0] - sod.DIAPHRAGM) / frame.time
    fan = (xi > sod.speeds["head"]) & (xi < sod.speeds["tail"])
    rho, u, p = (frame[name][0][fan] for name in ("density", "velocity", "pressure"))
    a = np.sqrt(g * p / rho)
    assert fan.sum() > 100, "the fan is barely resolved, so this checks little"
    assert u + 2 * a / (g - 1) == pytest.approx(2 * np.sqrt(g) / (g - 1), rel=1e-12)
    assert p / rho**g == pytest.approx(1.0, rel=1e-12)


def test_sod_waves_sit_where_their_speeds_put_them(sod):
    """Every cell more than one cell from a wave holds the state of its region: left state,
    fan, star left, star right, right state, separated by the fan head and tail (Toro (2009)
    eq. (4.55)), the contact at u*, and the shock (eq. (4.59)); sampled as in Sect. 4.5."""
    frame = sod.frame(len(sod) - 1, ["density", "velocity", "pressure"])
    x, t, s = sod.centres[0], frame.time, sod.speeds
    edges = [sod.DIAPHRAGM + t * s[k] for k in ("head", "tail", "contact", "shock")]
    far = np.min([np.abs(x - e) for e in edges], axis=0) > sod.grid.spacing[0]
    expected = {
        "density": (1.0, None, sod.star["density_left"], sod.star["density_right"], 0.125),
        "pressure": (1.0, None, sod.star["pressure"], sod.star["pressure"], 0.1),
        "velocity": (0.0, None, sod.star["velocity"], sod.star["velocity"], 0.0),
    }
    region = np.searchsorted(edges, x)
    for name, values in expected.items():
        for r, value in enumerate(values):
            cells = far & (region == r)
            if value is not None:
                assert cells.sum() > 50, f"region {r} is too narrow to test"
                assert np.allclose(frame[name][0][cells], value, rtol=0, atol=1e-15), (name, r)


def test_sod_conserves_mass_and_energy_and_gains_momentum_from_the_pressure_difference():
    """The Euler equations in conservation form (Toro (2009), Sect. 3.1): with both ends at
    rest, no mass or energy crosses them, while the momentum grows at ``p_L - p_R`` per unit
    time. Integrated on 32768 cells, where point sampling misplaces each of the two
    discontinuities (the contact and the shock; the fan is continuous) by at most half a
    cell, 1.5e-5. Every jump is below 0.9, which bounds the error at 2.7e-5, inside the
    tolerance of 1e-4."""
    fine = SodShockTube(grid=(32768,), n_frames=5)
    g, length = 1.4, 1.0
    totals = []
    for t in range(len(fine)):
        f = fine.frame(t, ["density", "velocity", "pressure"])
        rho, u, p = f["density"][0], f["velocity"][0], f["pressure"][0]
        totals.append([rho.mean() * length, (rho * u).mean() * length,
                       (p / (g - 1) + 0.5 * rho * u**2).mean() * length, f.time])
    mass0 = 0.5 * (1.0 + 0.125)
    energy0 = 0.5 * (1.0 + 0.1) / (g - 1)
    for mass, momentum, energy, time in totals:
        assert mass == pytest.approx(mass0, abs=1e-4)
        assert energy == pytest.approx(energy0, abs=1e-4)
        assert momentum == pytest.approx((1.0 - 0.1) * time, abs=1e-4)


@pytest.mark.parametrize("kwargs, match", [
    ({"t_end": 0.29}, "reaches a boundary"),
    ({"left": (1.0, 0.1), "right": (0.125, 1.0)}, "must exceed"),
    ({"t_start": 0.0}, "positive"),
    ({"gamma": 1.0}, "gamma"),
    ({"left": (-1.0, 1.0)}, "positive"),
])
def test_sod_refuses_a_case_its_closed_form_does_not_cover(kwargs, match):
    with pytest.raises(ValueError, match=match):
        SodShockTube(**kwargs)


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
    one metric left there is no comparison folder either."""
    subprocess.run(
        [sys.executable, str(REPO / "evaluate.py"), "dataset=sod_shock_tube",
         "degradation=quick", "metrics=[mse,h1_seminorm]", "+dataset.reader.grid=[64]",
         "+dataset.reader.n_frames=3", f"paths.results={tmp_path}",
         f"hydra.run.dir={tmp_path}/h"],
        check=True, capture_output=True, cwd=tmp_path,
    )
    assert [p.name.split("_")[0] for p in tmp_path.glob("*_*") if p.is_dir()] == ["mse"]

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


def test_taylor_green_grid_is_periodic_and_frames_decay_together():
    tg = TaylorGreen2D(grid=GRID)
    assert tg.grid.boundary == ("periodic", "periodic")
    first, last = (tg.frame(i, ["velocity"])["velocity"] for i in (0, len(tg) - 1))
    ratio = np.exp(-2 * 0.01 * (tg.times[-1] - tg.times[0]))
    assert last == pytest.approx(ratio * first, rel=1e-12, abs=1e-15)
