"""Shared fixtures.

Two conventions here are load-bearing and deliberate:

**Fields are non-square.** Every synthetic grid is 16x8, never 16x16. kinet stores data as
``(C, X, Y, Z)`` and every real dataset is square (256^2, 512^2), so a reader or operator
that transposes X and Y passes every test on square data and produces silently wrong
pictures forever. Non-square fixtures are the only place that bug can be caught.

**Fields have real structure.** A field of pure noise makes blur, coarsening and low-pass
indistinguishable, so the synthetic field is a two-scale sine plus a seeded noise floor:
smoothing operators bite the small scale first, which is what makes a synthetic
degradation ladder monotone the way a real one is.

Every helper shared by more than one test file lives here or in a helper module that is
not itself a test module (``fixtures_h5``, ``analytic_fields``, ``http_fixture``), so a test
file never imports from another test file: a test module is collected by pytest, not a
library, and a helper copied into a second file drifts from the first without any test
noticing.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hydra import compose, initialize_config_dir
from hydra.core.hydra_config import HydraConfig

from degradations import registry as deg_registry
from fmeval import pipeline
from fmeval.context import FieldContext, derive_rng, fluctuation_rms
from fmeval.data.base import GridSpec, Trajectory
from fmeval.data.synthetic_ensemble import SyntheticEnsembleTrajectory
from fmeval.ladder import SeverityLevel
from metrics import registry as metric_registry
from tests import fixtures_h5

#: The repository root, for tests that read committed files.
REPO = Path(__file__).resolve().parent.parent

#: Deliberately non-square. See the module docstring.
GRID: tuple[int, int] = (16, 8)


def synthetic_field(
    shape: tuple[int, ...] = GRID,
    n_channels: int = 1,
    *,
    seed: int = 0,
    noise: float = 0.05,
) -> np.ndarray:
    """A periodic, two-scale, mildly noisy field of shape ``(n_channels, *shape)``.

    Args:
        shape: Spatial extents, in ``(x, y[, z])`` order.
        n_channels: Number of channels; each gets a different phase offset.
        seed: RNG seed for the noise floor.
        noise: Noise amplitude relative to the deterministic part.

    Returns:
        Array of shape ``(n_channels, *shape)``, float64, periodic on every axis.
    """
    rng = np.random.default_rng(seed)
    coords = np.meshgrid(
        *[2 * np.pi * np.arange(n) / n for n in shape], indexing="ij"
    )
    out = np.empty((n_channels, *shape), dtype=np.float64)
    for c in range(n_channels):
        phase = 0.7 * c
        large = np.sin(coords[0] + phase)
        small = 0.35 * np.cos(4 * coords[0] + phase)
        for axis in coords[1:]:
            large = large * np.cos(axis + phase)
            small = small + 0.35 * np.sin(3 * axis + phase)
        out[c] = large + small + noise * rng.standard_normal(shape)
    return out


@pytest.fixture
def field() -> np.ndarray:
    """Single-channel non-square field, ``(1, 16, 8)``."""
    return synthetic_field(GRID, 1, seed=0)


@pytest.fixture
def field2() -> np.ndarray:
    """A *different* single-channel field, for symmetry and ordering checks."""
    return synthetic_field(GRID, 1, seed=1)


@pytest.fixture
def vector_field() -> np.ndarray:
    """Two-channel non-square field, ``(2, 16, 8)`` — stands in for velocity."""
    return synthetic_field(GRID, 2, seed=2)



def cosine_mode(shape: tuple[int, int], mode: int, phase: float = 0.0) -> np.ndarray:
    """``cos(2 pi m x / L + phase)`` along x, constant along y, as a ``(1, *shape)`` field.

    x is the first *spatial* axis, per the canonical trailing-axes layout. The profile does
    not depend on the grid spacing, which only the context carries.
    """
    x = np.arange(shape[0])
    profile = np.cos(2.0 * np.pi * mode * x / shape[0] + phase)
    return np.broadcast_to(profile[:, None], shape).copy()[np.newaxis, ...]


# The pointwise metrics' worked example, used by their tests and quoted in their cards: a sharp
# feature on a 4x4 grid, and two ways of getting it wrong -- moving it by one cell, and halving
# its amplitude where it stands.
SQUARE_REFERENCE = np.array([[[0.0, 0.0, 0.0, 0.0],
                              [0.0, 1.0, 1.0, 0.0],
                              [0.0, 1.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0, 0.0]]])

SQUARE_SHIFTED = np.array([[[0.0, 0.0, 0.0, 0.0],
                            [0.0, 0.0, 1.0, 1.0],
                            [0.0, 0.0, 1.0, 1.0],
                            [0.0, 0.0, 0.0, 0.0]]])

SQUARE_HALF_AMPLITUDE = np.array([[[0.0, 0.0, 0.0, 0.0],
                                   [0.0, 0.5, 0.5, 0.0],
                                   [0.0, 0.5, 0.5, 0.0],
                                   [0.0, 0.0, 0.0, 0.0]]])

# --- grids, contexts and ensembles ----------------------------------------------------


def unit_grid(shape: tuple[int, ...], spacing: float = 1.0) -> GridSpec:
    """A periodic grid with the same spacing on every axis, axes named ``x, y[, z]``."""
    n = len(shape)
    return GridSpec(tuple(shape), (float(spacing),) * n, (True,) * n, ("x", "y", "z")[:n],
                    (0.0,) * n)


def make_ctx(x: np.ndarray | tuple[int, ...], *, field: str = "vorticity",
             spacing: float = 1.0, seed: int = 0, label: str = "t") -> FieldContext:
    """The context the pipeline would hand an operator or metric for ``x``.

    Pass the field itself and its fluctuation RMS is measured, as the pipeline does; pass a
    spatial shape and the RMS is 1, for a metric that reads only the grid. The generator is
    derived exactly as the pipeline derives it, from ``(seed, label, frame 0, field)``.
    """
    shape = tuple(x) if isinstance(x, tuple) else x.shape[1:]
    return FieldContext(
        field=field, grid=unit_grid(shape, spacing), frame_index=0, time=0.0,
        fluctuation_rms=1.0 if isinstance(x, tuple) else fluctuation_rms(x),
        rng=derive_rng(seed, label, 0, field),
    )


#: Ensemble size for tests that need a member stack.
N_MEMBERS = 6


def members(x: np.ndarray, *, n_members: int = N_MEMBERS, seed: int = 0,
            scale: float | None = None) -> np.ndarray:
    """Scatter a field into an ``(N, C, *spatial)`` ensemble centred on it.

    ``scale`` defaults to 0.3 of the field's fluctuation RMS. Ensemble operators change
    dispersion, so they need something to disperse: N identical copies would make every
    severity a no-op and every direction test pass vacuously.
    """
    rng = np.random.default_rng(seed)
    scale = 0.3 * fluctuation_rms(x) if scale is None else scale
    return x[None] + scale * rng.standard_normal((n_members, *x.shape))


@pytest.fixture
def ensemble_traj() -> SyntheticEnsembleTrajectory:
    """A four-frame synthetic density ensemble of ``N_MEMBERS`` members."""
    return SyntheticEnsembleTrajectory(
        grid=(16, 16), n_members=N_MEMBERS, n_frames=4, fields=("density",), sigma=0.2, seed=0
    )


def run_metrics(traj: Trajectory, names: Sequence[str], levels: Sequence[SeverityLevel],
                fields: Sequence[str] = ("density",)) -> pipeline.PipelineResult:
    """Run the named metrics over the severity levels of ``traj`` through the pipeline."""
    return pipeline.run(
        traj, [metric_registry.get(n) for n in names], levels, fields=list(fields),
        dataset=pipeline.DatasetInfo(name="synthetic_ensemble_test", trajectory="test"), seed=0,
    )


class SyntheticTrajectory(Trajectory):
    """A four-frame in-memory trajectory, so pipeline tests need no files and no CFS."""

    def __init__(self, shape: tuple[int, ...] = GRID, n_frames: int = 4) -> None:
        self._shape = shape
        self._n = n_frames
        self._grid = unit_grid(shape)

    @property
    def fields(self) -> tuple[str, ...]:
        return ("density",)

    @property
    def times(self) -> np.ndarray:
        return np.arange(self._n, dtype=np.float64)

    @property
    def grid(self) -> GridSpec:
        return self._grid

    @property
    def meta(self) -> dict:
        return {"format": "synthetic"}

    def read_frame(self, t: int, fields):
        # Density-like: 1.0 with small fluctuations, matching the real data's scale, so
        # relative-severity operators behave as they do on the real thing.
        return {"density": 1.0 + 1e-3 * synthetic_field(self._shape, 1, seed=t)}


# --- registering a plugin for one test ----------------------------------------------


def _temporary(registry):
    """Register plugins through ``registry``'s decorator for one test, then remove them.

    Plugins must not be registered at module import: the contract tests parametrize over the
    registry at collection time, so a probe left behind would be silently held to the whole
    contract and would change another file's test IDs.
    """
    decorator = registry.metric if registry is metric_registry else registry.degradation
    added: list[str] = []

    def _register(**kwargs):
        def _decorate(fn):
            added.append(kwargs.get("name") or fn.__name__)
            return decorator(**kwargs)(fn)

        return _decorate

    yield _register
    for name in added:
        registry.REGISTRY.pop(name, None)


@pytest.fixture
def temporary_metric():
    """Register a metric for one test and remove it again."""
    yield from _temporary(metric_registry)


@pytest.fixture
def temporary_degradation():
    """Register a degradation for one test and remove it again."""
    yield from _temporary(deg_registry)


@pytest.fixture
def kinet_file(tmp_path):
    """A small raw-kinet HDF5 file reproducing the format's quirks; see ``fixtures_h5``."""
    return fixtures_h5.write_kinet_raw(tmp_path / "kinet_raw.h5")


# --- result frames with known answers ---------------------------------------------------


def make_frame(
    *,
    metric: str = "m",
    field: str = "f",
    axes: dict[str, list[float]] | None = None,
    n_frames: int = 12,
    noise: float = 0.0,
    seed: int = 0,
    reference: float = 0.0,
) -> pd.DataFrame:
    """A result frame over the full result schema whose values are a known function of level.

    ``axes`` maps a ladder label to the per-level values; level 0 (the reference) is added
    automatically with value ``reference``. Every other column carries what the pipeline
    writes for a deterministic, uncalibrated, pairwise error metric, except that
    ``energy_removed`` and ``energy_changed`` are NaN, unmeasured, for a test to set.
    """
    axes = axes or {"a": [1.0, 2.0, 3.0, 4.0]}
    rng = np.random.default_rng(seed)
    rows = []
    for frame in range(n_frames):
        levels = [("identity", "identity", 0, reference)]
        for label, values in axes.items():
            family = "geometric" if "translate" in label or label == "uncorrelated" \
                else "stochastic"
            levels += [(label, family, level, value + noise * rng.standard_normal())
                       for level, value in enumerate(values, start=1)]
        rows += [{
            "dataset": "d", "dataset_family": "", "complexity_rank": 0,
            "param_reynolds": np.nan, "param_mach": np.nan, "param_resolution": 16,
            "trajectory": "t", "frame_index": frame, "time": float(frame),
            "field": field, "analysis_grid": 16, "remap_op": "block_mean",
            "metric": metric, "arity": "pairwise", "higher_is_better": False,
            "degradation": label, "degradation_op": label, "degradation_family": family,
            "level": level, "severity": float(level), "severity_nominal": float(level),
            "calibration": "", "severity_degenerate": False,
            "energy_removed": np.nan, "energy_changed": np.nan, "severity_name": "s",
            "variant_label": f"{label}_l{level}" if level else "reference",
            "component": "", "value": value, "seed": 0, "wall_time_s": 1e-4,
            "n_members": np.nan, "target_value": np.nan,
        } for label, family, level, value in levels]
    return pd.DataFrame(rows, columns=list(pipeline.RESULT_DTYPES)).astype(pipeline.RESULT_DTYPES)


#: The synthetic ladder every report test renders: an axis of each length the real runs have
#: (four, three and two usable levels), plus the two probes.
SYNTHETIC_LADDER = {
    "gaussian_blur": [1.0, 2.0, 3.0, 4.0],
    "translate_x": [1.0, 3.0, 6.0, 9.0],
    "translate_subpixel": [0.5, 1.0, 2.0],
    "median_blur": [2.0, 3.0],
    "gaussian_impostor": [8.0],
    "uncorrelated": [10.0, 10.0, 10.0],
}
#: The operator behind each ladder label, as the pipeline records it.
SYNTHETIC_OPERATORS = {"translate_x": "translate", "uncorrelated": "random_large_translation"}
SYNTHETIC_FIELDS = ("vorticity", "density", "velocity")


def synthetic_rows(metrics=("mse", "mae", "rmse", "flat")) -> pd.DataFrame:
    """Rows for a four-metric, three-field run.

    ``mae`` is the square root of ``mse`` everywhere, anchor included -- the shape relation of
    the real pair, so the two rank-correlate perfectly while disagreeing in magnitude; ``rmse`` is
    proportional to ``mae``, so their damage is identical; ``flat`` is zero everywhere, a metric
    with no damage scale.
    """
    transform = {"mse": lambda v: v, "mae": np.sqrt, "rmse": lambda v: 0.7 * np.sqrt(v),
                 "flat": lambda v: 0.0 * v}
    frames = []
    for metric in metrics:
        for field in SYNTHETIC_FIELDS:
            axes = {k: [float(transform[metric](v)) for v in vals]
                    for k, vals in SYNTHETIC_LADDER.items()}
            frames.append(make_frame(metric=metric, field=field, n_frames=8,
                                     noise=0.0 if metric == "flat" else 0.05, seed=1, axes=axes))
    df = pd.concat(frames, ignore_index=True)
    df["degradation_op"] = df["degradation_op"].astype(str).replace(SYNTHETIC_OPERATORS)
    df["energy_changed"] = np.where(df["level"] > 0, (0.1 * df["severity"]) ** 2, 0.0)
    return df


# --- configuration ------------------------------------------------------------------------

CONFIGS = str(REPO / "configs")


def build(*overrides: str):
    """Compose the config the way `evaluate.py` does, with CLI-style overrides.

    The HydraConfig singleton has to be installed explicitly. `hydra.main` does that for
    you, and without it `${hydra:runtime.cwd}` -- which `paths.data` depends on -- raises
    "HydraConfig was not set". Composing without it would test a configuration that never
    actually runs.
    """
    with initialize_config_dir(config_dir=CONFIGS, version_base=None):
        cfg = compose(config_name="config", overrides=list(overrides),
                      return_hydra_config=True)
        HydraConfig.instance().set_config(cfg)
        return cfg


# --- bundle-test fields and ensembles (shared by metric bundles' test_metric.py) ----------


def step_field(shape: tuple[int, int] = (4, 4)) -> np.ndarray:
    """Zero on the first row, one on the rest, ``(1, *shape)``: one jump along x, flat along y.

    The increment metrics' worked example: ``increment_flatness`` and ``increment_w1`` each
    derive their card's value on it.
    """
    out = np.ones((1, *shape))
    out[0, 0, :] = 0.0
    return out


def alternating_field(shape: tuple[int, int] = (4, 4)) -> np.ndarray:
    """Zero and one on alternate rows, ``(1, *shape)``: a jump at every step along x."""
    out = np.zeros((1, *shape))
    out[0, 1::2, :] = 1.0
    return out


def exchangeable_ensemble(
    seed: int | np.random.Generator, shape: tuple[int, ...], n_members: int
) -> tuple[np.ndarray, np.ndarray]:
    """A reference and an ensemble drawn from one process: the calibrated case.

    A shared base field plus independent unit noise, drawn once for the reference and once per
    member, so the reference is exchangeable with the members. Calibration and propriety are
    statements about the true predictive distribution, so the reference must be such an
    independent draw: built the other way round (members scattered about the reference), the
    reference is the ensemble mean, and shrinking the members toward it improves every score.

    Args:
        seed: A seed, or a generator to continue drawing from.
        shape: ``(C, *spatial)`` of the reference.
        n_members: Ensemble size.

    Returns:
        ``(reference, members)``, shaped ``(C, *spatial)`` and ``(n_members, C, *spatial)``.
    """
    rng = np.random.default_rng(seed)
    base = rng.standard_normal(shape)
    reference = base + rng.standard_normal(shape)
    return reference, base[None] + rng.standard_normal((n_members, *shape))
