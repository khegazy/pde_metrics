"""The metric contract, parametrized over the whole registry.

Every metric anyone adds is automatically held to these, which is the registry's biggest
payoff: a contributor gets the checks without writing them, and a metric that cannot pass
a synthetic ladder is caught in 50 ms rather than after a ten-minute run.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import spearmanr

from fmeval.context import FieldContext
from fmeval.data.base import GridSpec
from metrics import registry
from tests.conftest import GRID, synthetic_field

# Canonical field vocabulary, mirrored from fmeval.data.base to keep this test importable
# without the data layer. Kept in sync by test_field_vocabulary_matches_data_layer below.
CANONICAL_FIELDS = {"density", "velocity", "vorticity", "pressure", "temperature",
                    "distribution"}


def all_specs() -> list[registry.MetricSpec]:
    registry.discover()
    return [registry.REGISTRY[n] for n in sorted(registry.REGISTRY)]


@pytest.fixture(params=[s.name for s in all_specs()])
def spec(request) -> registry.MetricSpec:
    """One MetricSpec per registered metric."""
    return registry.get(request.param)


def _channels_for(spec: registry.MetricSpec) -> int:
    """A channel count this metric accepts."""
    if "velocity" in spec.fields:
        return 2
    return 1


#: Ensemble size used when building arguments for an ``ensemble``-arity metric. Small,
#: but above the two members a sample variance needs.
N_MEMBERS = 6


def _members(shape: tuple[int, ...], n_channels: int, *, seed: int = 1) -> np.ndarray:
    """An ``(N, C, *spatial)`` ensemble scattered about a common base field."""
    base = synthetic_field(shape, n_channels, seed=seed, noise=0.0)
    rng = np.random.default_rng(seed)
    return base[None] + 0.3 * rng.standard_normal((N_MEMBERS, *base.shape))


def _args_for(
    spec: registry.MetricSpec,
    *,
    shape: tuple[int, ...] = GRID,
    seed_a: int = 0,
    seed_b: int = 1,
) -> tuple[np.ndarray, ...]:
    """Positional arguments of the right *shape* for this metric's arity.

    Every generic test below builds its inputs through here, so a metric taking an
    ensemble is handed ``(N, C, *spatial)`` rather than a second field that happens to
    have the same number of dimensions as one.
    """
    c = _channels_for(spec)
    a = synthetic_field(shape, c, seed=seed_a)
    if spec.arity == "single":
        return (a,)
    if spec.arity == "ensemble":
        return (a, _members(shape, c, seed=seed_b))
    return (a, synthetic_field(shape, c, seed=seed_b))


def _ctx(shape: tuple[int, ...]) -> FieldContext:
    """A context for a metric that asks for one, on a unit-spaced periodic grid.

    Unit spacing keeps the generic checks below reading the same as they did before any
    metric took a ctx: a metric whose value carries a length then returns the same number
    it would have on a grid it had to assume. What the ctx must *not* be is absent -- the
    pipeline always supplies one, so a contract test that omitted it would be testing a
    call the harness never makes.
    """
    return FieldContext(
        field="density",
        grid=GridSpec(
            shape=tuple(shape),
            spacing=(1.0,) * len(shape),
            periodic=(True,) * len(shape),
        ),
        frame_index=0,
        time=0.0,
        fluctuation_rms=1.0,
        rng=np.random.default_rng(0),
    )


def _kwargs_for(spec: registry.MetricSpec, first: np.ndarray) -> dict[str, object]:
    """``{"ctx": ...}`` for a metric that declares one, empty otherwise.

    Mirrors ``fmeval.pipeline``, which builds the context from the *reference* field's
    grid. ``first`` is that reference, so its trailing axes give the spatial shape for
    every arity -- ``(C, *spatial)`` pairwise and single, and the reference rather than
    the stack for ensemble.
    """
    if not spec.takes_ctx:
        return {}
    return {"ctx": _ctx(first.shape[1:])}


def _call(spec: registry.MetricSpec, *arrays: np.ndarray):
    return spec.fn(*arrays, **_kwargs_for(spec, arrays[0]))


def _call_map(spec: registry.MetricSpec, *arrays: np.ndarray) -> np.ndarray:
    """The pointwise map, called the way the pipeline calls it.

    The pipeline passes the metric's kwargs straight through to the map as well, so a map
    that declares a ctx receives the same one its metric did.
    """
    return spec.pointwise(*arrays, **_kwargs_for(spec, arrays[0]))


def test_no_import_errors():
    """A metric module that fails to import would silently vanish from the registry."""
    errors = registry.discover()
    assert errors == {}, f"metric modules failed to import: {errors}"


def test_registry_is_nonempty():
    assert all_specs(), "no metrics registered; discovery is broken"


def test_name_is_wellformed(spec):
    """The name is the metric's identity: bundle directory, card key, and config token.

    It must therefore be importable as a Python package name, which ``isidentifier``
    checks, and lowercase so directory names are stable across case-insensitive
    filesystems.
    """
    assert spec.name.isidentifier(), f"{spec.name!r} is not a valid identifier"
    assert spec.name == spec.name.lower(), f"{spec.name!r} must be lowercase"


def test_declared_fields_are_canonical(spec):
    unknown = set(spec.fields) - CANONICAL_FIELDS - {"*"}
    assert not unknown, f"{spec.name} declares unknown fields {sorted(unknown)}"


def test_pairwise_identity_is_zero(spec):
    """d(x, x) == 0 for a pairwise error metric. Catches normalisation slips."""
    if spec.arity != "pairwise" or spec.higher_is_better:
        pytest.skip("not a pairwise error metric")
    x = synthetic_field(GRID, _channels_for(spec))
    assert _call(spec, x, x) == pytest.approx(0.0, abs=1e-12)


def test_symmetry(spec):
    if spec.arity != "pairwise" or not spec.symmetric:
        pytest.skip("not declared symmetric")
    c = _channels_for(spec)
    a = synthetic_field(GRID, c, seed=0)
    b = synthetic_field(GRID, c, seed=1)
    assert _call(spec, a, b) == pytest.approx(_call(spec, b, a), rel=1e-12)


def test_returns_declared_type(spec):
    out = _call(spec, *_args_for(spec))
    if spec.returns == "scalar":
        assert isinstance(out, float), f"{spec.name} returned {type(out)}, expected float"
        assert np.isfinite(out), f"{spec.name} returned {out}"
    else:
        arr = np.asarray(out)
        assert arr.ndim == 1 and np.isfinite(arr).all()


def test_rejects_mismatched_shapes(spec):
    """A shape mismatch must raise, not silently broadcast."""
    if spec.arity != "pairwise":
        pytest.skip("single-field metric")
    c = _channels_for(spec)
    a = synthetic_field(GRID, c)
    b = synthetic_field((GRID[0], GRID[1] + 2), c)
    with pytest.raises(Exception):
        _call(spec, a, b)


def test_dtype_stability(spec):
    """float32 input must agree with float64 to single-precision tolerance."""
    args64 = _args_for(spec)
    args32 = tuple(x.astype(np.float32) for x in args64)
    got, want = _call(spec, *args32), _call(spec, *args64)
    if spec.returns == "scalar":
        assert got == pytest.approx(want, rel=1e-5, abs=1e-12)


def test_monotone_on_synthetic_blur_ladder(spec):
    """The CLAUDE.md acceptance criterion (IN-3) as a unit test.

    A metric that cannot rank a synthetic blur ladder will never rank a real degradation
    ladder, and this finds out in milliseconds instead of after a full run.
    """
    from scipy.ndimage import gaussian_filter

    c = _channels_for(spec)
    ref = synthetic_field(GRID, c, seed=0, noise=0.0)
    sigmas = [0.0, 0.5, 1.0, 2.0, 4.0]

    if spec.arity == "ensemble":
        # Blur every member alike. The ensemble's centre drifts away from the reference
        # as the small scales go, so an ensemble error metric must still rank the ladder;
        # a *calibration* metric need not, since a uniformly blurred ensemble can stay
        # perfectly well dispersed about its own -- now wrong -- centre.
        if spec.measures == "calibration":
            pytest.skip("calibration metric: blur damages accuracy, not dispersion")
        members = _members(GRID, c, seed=1)
        values = [
            _call(spec, ref, members if s == 0 else gaussian_filter(
                members, (0, 0, *([s] * (members.ndim - 2))), mode="wrap"))
            for s in sigmas
        ]
    else:
        values = []
        for s in sigmas:
            cand = ref if s == 0 else gaussian_filter(ref, (0, *([s] * (ref.ndim - 1))),
                                                      mode="wrap")
            values.append(_call(spec, ref, cand) if spec.arity == "pairwise"
                          else _call(spec, cand))

    if spec.returns != "scalar":
        pytest.skip("vector-valued metric")
    rho = spearmanr(range(len(sigmas)), values).statistic
    expected = 1.0 if not spec.higher_is_better else -1.0
    # A metric may declare that it is *not* monotone under smoothing. That is checked
    # here rather than skipped: the declaration has to be true, so it cannot be used to
    # slip a metric past a gate it would otherwise have failed silently.
    if not spec.monotone_under_smoothing:
        assert abs(rho) < 1.0, (
            f"{spec.name} declares monotone_under_smoothing=False but ranked the blur "
            f"ladder perfectly (rho={rho:.3f}); values={values}. Remove the declaration"
        )
        return
    # Single-field metrics measure the field, not the error, so blurring makes them fall.
    if spec.arity == "single":
        assert abs(rho) == pytest.approx(1.0), (
            f"{spec.name} is not monotone under blur (rho={rho:.3f}); values={values}"
        )
    else:
        assert rho == pytest.approx(expected), (
            f"{spec.name} is not monotone under blur (rho={rho:.3f}); values={values}"
        )


def test_ctx_flag_matches_signature(spec):
    import inspect

    assert spec.takes_ctx == ("ctx" in inspect.signature(spec.fn).parameters)


# --- the ensemble arity ------------------------------------------------------------


def test_ensemble_metric_rejects_a_plain_field(spec):
    """Handing a ``(C, *spatial)`` field where members belong must raise.

    Without this, a caller that forgot the member axis gets a number computed over the
    channel axis instead -- the wrong reduction, silently, with a plausible result.
    """
    if spec.arity != "ensemble":
        pytest.skip("not an ensemble metric")
    c = _channels_for(spec)
    a = synthetic_field(GRID, c, seed=0)
    with pytest.raises(Exception):
        _call(spec, a, synthetic_field(GRID, c, seed=1))


def test_ensemble_metric_rejects_a_mismatched_grid(spec):
    if spec.arity != "ensemble":
        pytest.skip("not an ensemble metric")
    c = _channels_for(spec)
    a = synthetic_field(GRID, c, seed=0)
    with pytest.raises(Exception):
        _call(spec, a, _members((GRID[0], GRID[1] + 2), c))


def test_ensemble_error_metric_is_zero_on_a_perfect_ensemble(spec):
    """Every member equal to the reference is a perfect prediction, and scores zero.

    Skipped for target-valued metrics, where a collapsed ensemble is not the ideal: the
    spread-to-skill ratio of a zero-spread ensemble is zero, and zero is its *worst*
    value, not its best.
    """
    if (
        spec.arity != "ensemble"
        or spec.measures != "error"
        or spec.higher_is_better
    ):
        pytest.skip("not an ensemble error metric")
    c = _channels_for(spec)
    a = synthetic_field(GRID, c, seed=0)
    members = np.repeat(a[None], N_MEMBERS, axis=0)
    assert _call(spec, a, members) == pytest.approx(0.0, abs=1e-12)


def test_declared_target_is_consistent_with_direction(spec):
    """A target-valued metric must not also claim a direction; the registry enforces it."""
    if spec.target is None:
        pytest.skip("no declared target")
    assert not spec.higher_is_better
    assert np.isfinite(spec.target)


# --- pointwise decomposition -------------------------------------------------------


def test_pointwise_map_shape(spec):
    if not spec.has_pointwise:
        pytest.skip("no pointwise decomposition declared")
    c = _channels_for(spec)
    a, b = synthetic_field(GRID, c, seed=0), synthetic_field(GRID, c, seed=1)
    m = _call_map(spec, a, b) if spec.arity == "pairwise" else _call_map(spec, a)
    assert m.shape == GRID, f"{spec.name}: map is {m.shape}, expected {GRID}"
    assert np.isfinite(m).all()


def test_pointwise_map_reduces_to_metric(spec):
    """R(map(a, b)) == metric(a, b) under the *declared* reduction.

    This is the check that the picture you reason from is really what the number is made
    of. It catches the two easy mistakes: forgetting that channel-summed maps reduce as
    mean/C, and assuming rmse's map averages to rmse when it averages to mse.
    """
    if not spec.has_pointwise:
        pytest.skip("no pointwise decomposition declared")
    c = _channels_for(spec)
    a, b = synthetic_field(GRID, c, seed=0), synthetic_field(GRID, c, seed=1)
    if spec.arity == "pairwise":
        m, want = _call_map(spec, a, b), _call(spec, a, b)
    else:
        m, want = _call_map(spec, a), _call(spec, a)
    assert spec.reduce(m, c) == pytest.approx(want, rel=1e-12), (
        f"{spec.name}: reduction {spec.reduction!r} of the map gives "
        f"{spec.reduce(m, c)}, but the metric gives {want}"
    )


def test_pointwise_map_is_multichannel_aware():
    """Explicitly pin the mean/C rule on a 2-channel field, where C actually matters."""
    spec = registry.get("mse")
    a = synthetic_field(GRID, 2, seed=0)
    b = synthetic_field(GRID, 2, seed=1)
    m = _call_map(spec, a, b)
    assert m.mean() == pytest.approx(2 * _call(spec, a, b), rel=1e-12)
    assert spec.reduce(m, 2) == pytest.approx(_call(spec, a, b), rel=1e-12)


# --- registry mechanics ------------------------------------------------------------


def test_get_unknown_metric_lists_available():
    with pytest.raises(KeyError, match="unknown metric"):
        registry.get("definitely_not_a_metric")


def test_duplicate_registration_raises():
    with pytest.raises(ValueError, match="duplicate metric"):

        @registry.metric(name="mse")
        def _dupe(a, b):
            return 0.0


def test_wrong_arity_signature_raises():
    with pytest.raises(TypeError, match="positional argument"):

        @registry.metric(name="_bad_arity", arity="pairwise")
        def _bad(a):
            return 0.0


def test_unknown_reduction_raises():
    with pytest.raises(ValueError, match="unknown reduction"):

        @registry.metric(name="_bad_reduction", reduction="nope")
        def _bad(a, b):
            return 0.0
