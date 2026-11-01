"""The metric contract, parametrized over the whole registry.

Every metric anyone adds is automatically held to these, which is the registry's biggest
payoff: a contributor gets the checks without writing them, and a metric that cannot pass
a synthetic ladder is caught in 50 ms rather than after a ten-minute run.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter
from scipy.stats import spearmanr

from fmeval.context import COMPANION_KEY
from fmeval.data.base import FIELDS
from metrics import registry
from tests.conftest import (
    GRID,
    N_MEMBERS,
    SQUARE_REFERENCE,
    SQUARE_SHIFTED,
    cosine_mode,
    exchangeable_ensemble,
    make_ctx,
    members,
    synthetic_field,
)


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


#: Fields positive by definition: a mass density. A metric that declares only these is given
#: its real domain, the synthetic field moved above zero, rather than a signed field outside it
#: (issues/101). Pressure is not listed: a dataset may store a gauge pressure, which takes both
#: signs (issues/101). The synthetic field stays within about +-2 in two dimensions and +-2.3 in
#: three, so the offset leaves it at least about 0.7.
POSITIVE_FIELDS: frozenset[str] = frozenset({"density"})
POSITIVE_OFFSET: float = 3.0


def _field_for(spec: registry.MetricSpec, shape: tuple[int, ...] = GRID, n_channels: int = 1,
               **kwargs) -> np.ndarray:
    """``synthetic_field`` in this metric's domain: moved above zero for a positive field."""
    x = synthetic_field(shape, n_channels, **kwargs)
    return x + POSITIVE_OFFSET if set(spec.fields) <= POSITIVE_FIELDS else x


def _members(shape: tuple[int, ...], n_channels: int, *, seed: int = 1) -> np.ndarray:
    """An ``(N, C, *spatial)`` ensemble scattered about a common base field."""
    return members(synthetic_field(shape, n_channels, seed=seed, noise=0.0), seed=seed, scale=0.3)


def _args_for(
    spec: registry.MetricSpec,
    *,
    shape: tuple[int, ...] = GRID,
    seed_a: int = 0,
    seed_b: int = 1,
    n_channels: int | None = None,
) -> tuple[np.ndarray, ...]:
    """Positional arguments of the right *shape* for this metric's arity.

    Every generic test below builds its inputs through here, so a metric taking an
    ensemble is handed ``(N, C, *spatial)`` rather than a second field that happens to
    have the same number of dimensions as one. ``n_channels`` overrides the channel count
    :func:`_channels_for` picks.
    """
    c = _channels_for(spec) if n_channels is None else n_channels
    a = _field_for(spec, shape, c, seed=seed_a)
    if spec.arity == "single":
        return (a,)
    if spec.arity == "ensemble":
        return (a, _members(shape, c, seed=seed_b))
    return (a, _field_for(spec, shape, c, seed=seed_b))


def _kwargs_for(spec: registry.MetricSpec, first: np.ndarray) -> dict[str, object]:
    """``{"ctx": ...}`` for a metric that declares one, empty otherwise.

    Mirrors ``fmeval.pipeline``, which builds the context from the *reference* field's
    grid. ``first`` is that reference, so its trailing axes give the spatial shape for
    every arity -- ``(C, *spatial)`` pairwise and single, and the reference rather than
    the stack for ensemble.
    """
    if not spec.takes_ctx:
        return {}
    return {"ctx": make_ctx(first.shape[1:])}


def _call(spec: registry.MetricSpec, *arrays: np.ndarray):
    return spec.fn(*arrays, **_kwargs_for(spec, arrays[0]))


def _call_companion(spec: registry.MetricSpec, *arrays: np.ndarray):
    """The companion, called the way the pipeline calls it: with a context of the same grid."""
    kwargs = {"ctx": make_ctx(arrays[0].shape[1:])} if spec.companion.takes_ctx else {}
    return spec.companion.fn(*arrays, **kwargs)


def _companion_args(spec: registry.MetricSpec, args: tuple[np.ndarray, ...]):
    """The arguments a companion takes: the candidate alone for a one-field curve."""
    return args[-1:] if spec.companion.one_field else args


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
    unknown = set(spec.fields) - set(FIELDS) - {"*"}
    assert not unknown, f"{spec.name} declares unknown fields {sorted(unknown)}"


def test_pairwise_identity_is_zero(spec):
    """d(x, x) == 0 for a pairwise error metric. Catches normalisation slips."""
    if spec.arity != "pairwise" or spec.higher_is_better:
        pytest.skip("not a pairwise error metric")
    x = _field_for(spec, GRID, _channels_for(spec))
    assert _call(spec, x, x) == pytest.approx(0.0, abs=1e-12)


def test_symmetry(spec):
    if spec.arity != "pairwise" or not spec.symmetric:
        pytest.skip("not declared symmetric")
    a, b = _args_for(spec)
    assert _call(spec, a, b) == pytest.approx(_call(spec, b, a), rel=1e-12)


def test_returns_one_finite_float(spec):
    """One number per comparison: the number the literature reports. Anything with more
    structure is the metric's companion, never its return value."""
    out = _call(spec, *_args_for(spec))
    assert isinstance(out, float), f"{spec.name} returned {type(out)}, expected float"
    assert np.isfinite(out), f"{spec.name} returned {out}"


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
    assert got == pytest.approx(want, rel=1e-5, abs=1e-12)


def test_monotone_on_synthetic_blur_ladder(spec):
    """The CLAUDE.md acceptance criterion (IN-3) as a unit test.

    A metric that cannot rank a synthetic blur ladder will never rank a real degradation
    ladder, and this finds out in milliseconds instead of after a full run.
    """
    c = _channels_for(spec)
    ref = _field_for(spec, GRID, c, seed=0, noise=0.0)
    # A pairwise metric that is undefined (NaN) on the noise-free field, because the quantity it
    # normalises by is zero there, is scored from the default, mildly noisy field instead. The
    # noise-free field is a few Fourier modes, and a statistic that needs more structure than
    # that, such as energy transfer between wavenumber shells, can be exactly zero on it.
    if spec.arity == "pairwise" and np.isnan(_call(spec, ref, ref)):
        ref = _field_for(spec, GRID, c, seed=0)
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
    collapsed = np.repeat(a[None], N_MEMBERS, axis=0)
    assert _call(spec, a, collapsed) == pytest.approx(0.0, abs=1e-12)


def test_declared_target_is_consistent_with_direction(spec):
    """A target-valued metric must not also claim a direction; the registry enforces it."""
    if spec.target is None:
        pytest.skip("no declared target")
    assert not spec.higher_is_better
    assert np.isfinite(spec.target)


# --- companions: the object behind the number ------------------------------------------


def _field_map(spec: registry.MetricSpec) -> None:
    if spec.companion is None or spec.companion.kind != "field":
        pytest.skip("no per-cell map declared")


def _curve(spec: registry.MetricSpec) -> None:
    if spec.companion is None or spec.companion.kind != "curve":
        pytest.skip("no curve declared")


def test_pointwise_map_shape(spec):
    _field_map(spec)
    m = _call_companion(spec, *_args_for(spec))
    assert m.shape == GRID, f"{spec.name}: map is {m.shape}, expected {GRID}"
    assert np.isfinite(m).all()


def test_pointwise_map_reduces_to_metric(spec):
    """R(map(a, b)) == metric(a, b) under the *declared* reduction.

    This is the check that the picture you reason from is really what the number is made
    of. It catches the two easy mistakes: forgetting that channel-summed maps reduce as
    mean/C, and assuming rmse's map averages to rmse when it averages to mse.

    A metric that accepts any field is checked on two channels as well. On one channel a
    map summed over channels and a map maximised over channels are the same array, so only
    two channels show whether the map collapses channels the way its reduction assumes.
    """
    _field_map(spec)
    counts = {_channels_for(spec)} | ({2} if "*" in spec.fields else set())
    for c in sorted(counts):
        args = _args_for(spec, n_channels=c)
        m, want = _call_companion(spec, *args), _call(spec, *args)
        assert spec.reduce(m, c) == pytest.approx(want, rel=1e-12), (
            f"{spec.name}: reduction {spec.reduction!r} of the {c}-channel map gives "
            f"{spec.reduce(m, c)}, but the metric gives {want}"
        )


def test_pointwise_map_is_multichannel_aware():
    """Explicitly pin the mean/C rule on a 2-channel field, where C actually matters."""
    spec = registry.get("mse")
    a = synthetic_field(GRID, 2, seed=0)
    b = synthetic_field(GRID, 2, seed=1)
    m = _call_companion(spec, a, b)
    assert m.mean() == pytest.approx(2 * _call(spec, a, b), rel=1e-12)
    assert spec.reduce(m, 2) == pytest.approx(_call(spec, a, b), rel=1e-12)


def test_a_curve_has_one_value_per_fixed_coordinate(spec):
    """Equal lengths, unique coordinates that do not depend on the fields, finite values."""
    _curve(spec)
    first = _call_companion(spec, *_companion_args(spec, _args_for(spec)))
    second = _call_companion(spec, *_companion_args(spec, _args_for(spec, seed_a=3, seed_b=4)))
    for coordinates, values in (first, second):
        coordinates, values = np.asarray(coordinates), np.asarray(values, dtype=float)
        assert coordinates.ndim == values.ndim == 1 and len(coordinates) == len(values), (
            f"{spec.name}: curve of {coordinates.shape} coordinates and {values.shape} values")
        assert len(set(coordinates.tolist())) == len(coordinates), (
            f"{spec.name}: repeated coordinates {coordinates.tolist()}")
        assert np.isfinite(values).all(), f"{spec.name}: non-finite curve values {values}"
    assert np.array_equal(np.asarray(first[0]), np.asarray(second[0])), (
        f"{spec.name}: the coordinates moved with the fields, {first[0]} vs {second[0]}; a "
        "coordinate is the same at every row or the rows cannot be compared")


def test_a_comparison_curve_is_zero_on_identical_fields(spec):
    """A comparison curve of an error metric takes the metric's identity value, zero, at every
    coordinate when the two fields are the same."""
    _curve(spec)
    if spec.companion.one_field or spec.arity != "pairwise" or spec.higher_is_better:
        pytest.skip("not a comparison curve of a pairwise error metric")
    x = _field_for(spec, GRID, _channels_for(spec))
    _, values = _call_companion(spec, x, x)
    assert np.allclose(values, 0.0, atol=1e-12), f"{spec.name}: curve on (x, x) is {values}"


def test_a_point_set_has_one_column_per_declared_coordinate(spec):
    """An ``(N, D)`` array with ``D`` the number of declared coordinates, on two inputs; ``N`` may
    change with the fields, ``D`` may not, or the stored sets cannot be drawn on one set of axes."""
    if spec.companion is None or spec.companion.kind != "points":
        pytest.skip("no point set declared")
    for args in (_args_for(spec), _args_for(spec, seed_a=3, seed_b=4)):
        points = np.asarray(_call_companion(spec, *_companion_args(spec, args)))
        assert points.ndim == 2 and points.shape[1] == len(spec.companion.coordinate), (
            f"{spec.name}: point set of shape {points.shape} for the declared coordinates "
            f"{spec.companion.coordinate}")


def test_the_metric_reads_its_companion_from_the_cache(spec):
    """The pipeline computes a curve or a point set once per row and hands it to the metric in
    the context; the metric must give the same number from that as when it computes it itself."""
    if spec.companion is None or spec.companion.kind == "field":
        pytest.skip("no curve or point set declared")
    if not spec.takes_ctx:
        pytest.skip("the metric takes no context, so it always computes the companion itself")
    args = _args_for(spec)
    ctx = make_ctx(args[0].shape[1:])
    ctx.cache[COMPANION_KEY] = _call_companion(spec, *_companion_args(spec, args))
    direct = spec.fn(*args, ctx=make_ctx(args[0].shape[1:]))
    assert spec.fn(*args, ctx=ctx) == pytest.approx(direct, rel=1e-12), (
        f"{spec.name}: the number from the cached companion differs from the direct one")


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


def test_a_companion_is_refused_when_its_declaration_contradicts_itself(temporary_metric):
    """One companion per metric; a curve names its coordinate, a point set names at least two
    and a field map none; and the signature takes the metric's arguments, or one field where a
    pairwise metric takes two."""
    temporary_metric(name="_has_curve", arity="pairwise")(lambda a, b: 0.0)
    with pytest.raises(ValueError, match="names its coordinate"):
        registry.companion(of="_has_curve", kind="curve")(lambda a, b: ([0], [0.0]))
    with pytest.raises(ValueError, match="names its coordinate"):
        registry.companion(of="_has_curve", coordinate=("l", "cells"))(lambda a, b: a)
    with pytest.raises(TypeError, match="positional"):
        registry.companion(of="_has_curve", kind="field")(lambda a: a)
    registry.companion(of="_has_curve", kind="curve", coordinate=("l", "cells"))(
        lambda x: ([1], [0.0]))
    assert registry.REGISTRY["_has_curve"].companion.one_field
    with pytest.raises(ValueError, match="already has a companion"):
        registry.companion(of="_has_curve", kind="curve", coordinate=("l", "cells"))(
            lambda a, b: ([1], [0.0]))
    with pytest.raises(ValueError, match="not registered"):
        registry.companion(of="_no_such_metric")(lambda a, b: a)
    temporary_metric(name="_has_points", arity="pairwise")(lambda a, b: 0.0)
    with pytest.raises(ValueError, match="names its coordinate"):
        registry.companion(of="_has_points", kind="points")(lambda x: np.zeros((0, 2)))
    with pytest.raises(ValueError, match="at least two"):
        registry.companion(of="_has_points", kind="points", coordinate=(("x", "cells"),))(
            lambda x: np.zeros((0, 1)))
    registry.companion(of="_has_points", kind="points",
                       coordinate=(("x", "cells"), ("y", "cells")))(lambda x: np.zeros((0, 2)))
    assert registry.REGISTRY["_has_points"].companion.one_field


def test_unknown_reduction_raises():
    with pytest.raises(ValueError, match="unknown reduction"):

        @registry.metric(name="_bad_reduction", reduction="nope")
        def _bad(a, b):
            return 0.0


# --- properties shared by named metrics --------------------------------------------
#
# Each test below states one property that several bundles claim in their cards, with one
# case per metric. They are not registry-wide: each holds for the metrics listed and is not
# expected of the others.


@pytest.mark.parametrize("name", [
    # MAE's map is |difference|: 1 in each lobe and 0 where the two squares overlap.
    pytest.param("mae", id="mae"),
    # MSE's map is the squared difference, and squaring 1 and 0 changes neither, so the
    # picture is the same: the double penalty is a property of pointwise error, not of the
    # power it is raised to.
    pytest.param("mse", id="mse"),
])
def test_the_error_map_shows_two_lobes_for_a_displaced_feature(name: str):
    """The double penalty as a picture: error where the feature is not, and where it is."""
    error = registry.get(name).companion.fn(SQUARE_REFERENCE, SQUARE_SHIFTED)
    assert np.all(error[1:3, 1] == 1.0), "where the feature should be and is not"
    assert np.all(error[1:3, 3] == 1.0), "where it is and should not be"
    assert np.all(error[1:3, 2] == 0.0), "the overlapping column should carry no error at all"


@pytest.mark.parametrize("name", [
    # The sentence in MAE's card about what it ignores.
    pytest.param("mae", id="mae"),
    # The sentence in MSE's card about what it ignores: the metric sees a bag of per-cell
    # differences and nothing about their arrangement, which is exactly the information a
    # displaced shock lives in.
    pytest.param("mse", id="mse"),
])
def test_a_pointwise_metric_is_blind_to_where_the_error_sits(name: str):
    """Two candidates wrong by the same amount in different places score identically."""
    reference = np.zeros((1, 4, 4))
    corner = reference.copy()
    corner[0, 0, 0] = 1.0
    middle = reference.copy()
    middle[0, 2, 2] = 1.0
    fn = registry.get(name).fn
    assert fn(reference, corner) == fn(reference, middle)


@pytest.mark.parametrize(("name", "ratio"), [
    # MAE ~ delta <|df/dx|>: linear, so halving the displacement halves the error.
    pytest.param("mae", 2.0, id="mae-linear"),
    # MSE ~ delta^2 <(df/dx)^2>: quadratic, so halving the displacement quarters it. This is
    # the expansion in MSE's Definition, and what makes MSE tolerant of small shifts and
    # severe about larger ones.
    pytest.param("mse", 4.0, id="mse-quadratic"),
])
def test_response_to_a_small_displacement_has_the_declared_power(name: str, ratio: float):
    """Halving a displacement below the scale of variation divides the error by ``ratio``.

    Checked on a smooth sinusoid, where the sub-cell displacement is exact rather than
    approximated by a shift, and where the derivative is bounded so the small-displacement
    expansion in each card's Definition holds.
    """
    x = np.linspace(0.0, 2.0 * np.pi, 256, endpoint=False)
    reference = np.sin(x)[None, :]
    fn = registry.get(name).fn
    errors = [fn(reference, np.sin(x + d)[None, :]) for d in (0.02, 0.01, 0.005)]
    ratios = [errors[i] / errors[i + 1] for i in range(len(errors) - 1)]
    assert all(abs(r - ratio) < 0.05 for r in ratios), ratios


@pytest.mark.parametrize(("name", "factor"), [
    # The H^-1 seminorm carries a length: same field, same mode index, twice the spacing
    # means twice the domain and half the wavenumber, so 1 / |k| doubles.
    pytest.param("h_minus_one", 2.0, id="h_minus_one-length"),
    # The H^1 seminorm carries an inverse length, the opposite power: doubling the cell
    # size halves the wavenumber and so halves the value.
    pytest.param("h1_seminorm", 0.5, id="h1_seminorm-inverse-length"),
    # Palinstrophy carries an inverse length squared: doubling the cell size halves every
    # wavenumber, so it falls by four. On a grid coarsened by a factor, using the native
    # spacing would inflate the result by exactly the square of that factor.
    pytest.param("palinstrophy", 0.25, id="palinstrophy-inverse-length-squared"),
    # The variogram score weights each pair by its inverse distance, so doubling the cell
    # size halves every weight and the score.
    pytest.param("variogram_score", 0.5, id="variogram_score-inverse-length"),
    # The distance between shock sets is a length: the detector reads only pressure ratios,
    # so the same cells are flagged at any spacing and every distance between them doubles.
    pytest.param("shock_set_distance", 2.0, id="shock_set_distance-length"),
    # The Wasserstein distance is a length of transport: the same mode on a grid twice as
    # coarse moves the same fraction of the mass twice as far. Given on its positive domain.
    pytest.param("wasserstein", 2.0, id="wasserstein-length"),
])
def test_doubling_the_spacing_scales_the_value_by_its_power_of_length(name: str, factor: float):
    """A metric carrying a length to some power scales by ``2^power`` when the spacing doubles.

    This is why these metrics must read the *analysis* grid's spacing rather than assume unit
    cells. Each is evaluated on a mode-1 cosine along x on an 8x8 grid: a pairwise metric as
    the error against a zero field, an ensemble one as a one-member ensemble of the cosine
    against a zero field, a single-field one on the cosine itself.
    """
    spec = registry.get(name)
    shape = (8, 8)
    fields = (cosine_mode(shape, mode=1),)
    if spec.arity == "pairwise":
        fields = (np.zeros((1, *shape)), *fields)
    elif spec.arity == "ensemble":
        fields = (np.zeros((1, *shape)), fields[0][None])
    if set(spec.fields) <= POSITIVE_FIELDS:
        fields = tuple(x + POSITIVE_OFFSET for x in fields)
    unit = spec.fn(*fields, ctx=make_ctx(shape, spacing=1.0))
    doubled = spec.fn(*fields, ctx=make_ctx(shape, spacing=2.0))
    assert doubled == pytest.approx(factor * unit)


@pytest.mark.parametrize("name", [
    # CRPS's skill term E|X - y| grows as the members move away from the reference, and the
    # spread term does not move, so the score rises.
    pytest.param("crps", id="crps"),
    # The energy score is the same two terms over the whole field: the distance term grows
    # with the shift and the pair term does not move.
    pytest.param("energy_score", id="energy_score"),
    # The error of the ensemble mean is the bias itself once it dominates the noise.
    pytest.param("ensemble_mean_rmse", id="ensemble_mean_rmse"),
    # A biased ensemble pushes the reference toward one end of the member ranks: the
    # histogram slopes, and the reliability index rises with the slope.
    pytest.param("rank_histogram", id="rank_histogram"),
])
def test_an_ensemble_metric_rises_with_bias(name: str):
    """Shifting every member by a growing constant never improves the score.

    The ensemble starts calibrated -- the reference is exchangeable with the members -- so
    every shift moves it away from the truth.
    """
    spec = registry.get(name)
    reference, ensemble = exchangeable_ensemble(3, (1, 48, 48), 8)
    values = [_call(spec, reference, ensemble + b) for b in (0.0, 0.25, 0.5, 1.0, 2.0)]
    assert values == sorted(values), values
    assert values[-1] > values[0], values


#: What in a metric's source makes it assume every axis wraps: a Fourier transform however it
#: is imported, an FFT convolution (circular unless padded), a rolled difference, the shared
#: wavenumbers, or wrap-mode padding or filtering (``np.pad``, ``scipy.ndimage``).
_WRAPS = re.compile(r"np\.fft|numpy\.fft|from numpy import fft|scipy\.fft|fftconvolve|np\.roll"
                    r"|fmeval\.wavenumbers|kinet_spectral|mode=\"wrap\"|mode='wrap'")
#: Another bundle's module imported by this one, e.g. ``from ..h1_seminorm.metric import``.
_BUNDLE_IMPORT = re.compile(r"from (?:\.\.|metrics\.)(\w+)\.metric import")


def test_a_metric_that_wraps_declares_requires_periodic(spec):
    """``requires_periodic`` is declared, so it is checked against the source.

    A metric whose module takes a Fourier transform, a spectral derivative or a rolled
    difference -- or imports a bundle that is itself periodic-only -- reads a domain edge as a
    jump, and must declare it so the pipeline does not run it on a bounded dataset. A hand-made
    wrap written some other way escapes this check; the declaration then rests on review.
    """
    source = Path(sys.modules[spec.module].__file__).read_text()
    inherited = [b for b in _BUNDLE_IMPORT.findall(source)
                 if b in registry.REGISTRY and registry.REGISTRY[b].requires_periodic]
    if _WRAPS.search(source) or inherited:
        assert spec.requires_periodic, (
            f"{spec.name} uses {_WRAPS.search(source).group(0) if _WRAPS.search(source) else ''}"
            f"{' and ' if _WRAPS.search(source) and inherited else ''}"
            f"{'periodic-only ' + ', '.join(inherited) if inherited else ''}, so it assumes a "
            "periodic domain; declare requires_periodic=True in its @metric decorator"
        )


@pytest.mark.parametrize("line", [
    "F = np.fft.rfftn(x)", "import numpy.fft as nf", "from numpy import fft",
    "from scipy.fft import rfftn", "from scipy.signal import fftconvolve", "np.roll(x, 1, 0)",
    "from fmeval.wavenumbers import k_magnitude", "from fmeval.external.kinet_spectral import d",
    'np.pad(x, 2, mode="wrap")', "ndimage.uniform_filter(x, 3, mode='wrap')",
])
def test_every_way_of_wrapping_the_domain_is_recognised(line):
    """Each form here wraps a bounded tube's ends together; a metric written with any of them
    and without ``requires_periodic`` would run on ``sod_shock_tube`` and read its walls as a
    jump, so the source check must see every one."""
    assert _WRAPS.search(line), f"{line!r} wraps the domain but escapes the periodicity check"
