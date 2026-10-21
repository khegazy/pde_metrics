"""The degradation contract, parametrized over the whole registry, plus ladder mechanics.

The highest-value check here is ``test_declared_direction_is_true``: it *verifies* the
declared ``severity_direction`` by measuring that damage actually rises with level. A
reversed severity list would otherwise silently invert every Spearman computed from that
axis, and nothing else in the pipeline would notice.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from degradations import registry as deg
from degradations._shared.filters import _apply_filter
from fmeval.calibration import calibrate, calibrate_field
from fmeval.context import FieldContext, derive_rng, fluctuation_rms
from fmeval.data.base import Frame, GridSpec
from fmeval.ladder import (
    REFERENCE_LEVEL,
    DegradationConfig,
    SeverityLevel,
    apply_severity_level,
    build_ladder,
    ladder_axes,
    ordinal_axes,
)
from fmeval.wavenumbers import wavenumber_magnitude
from tests.conftest import make_ctx, members, synthetic_field, unit_grid

#: Grid for the calibrated operators. Larger and with a red spectrum, because a calibrated
#: severity is a fraction of a measured property: on a small broadband field the characteristic
#: scale is a couple of cells, every scale fraction rounds to a no-op, and the direction test
#: would pass vacuously while checking nothing.
CALIBRATION_SHAPE = (64, 48)

SHAPE = (32, 16)  # non-square, and divisible by the coarsening factors under test


def smooth_field(shape: tuple[int, ...] = CALIBRATION_SHAPE) -> np.ndarray:
    """A field with a decaying spectrum, so it has a characteristic scale to calibrate against."""
    rng = np.random.default_rng(7)
    noise = rng.standard_normal((1, *shape))
    transfer = 1.0 / (1.0 + wavenumber_magnitude(shape) ** 2)
    return np.real(np.fft.ifftn(np.fft.fftn(noise[0]) * transfer))[None]


def resolve_for(spec: deg.DegradationSpec, x: np.ndarray, severity: float) -> float:
    """Turn a config-facing severity into the value the operator actually receives.

    Calibrated operators take an absolute cutoff or width while their config severity is a
    fraction, so a test that passes the config number straight to the function is testing a
    different quantity than the one whose direction is declared.
    """
    if spec.calibration is None:
        return severity
    measured = calibrate_field([x], unit_grid(x.shape[1:]), "vorticity")
    if spec.calibration == "scale":
        return measured.length_for_scale_fraction(severity)
    side = "above" if spec.calibration == "energy_above" else "below"
    return measured.cutoff_removing_energy(severity, side)


def call(spec: deg.DegradationSpec, x: np.ndarray, severity: float, **kw) -> np.ndarray:
    """Apply an operator to ``x`` at a config-facing severity, resolving it if calibrated."""
    return call_absolute(spec, x, resolve_for(spec, x, severity), **kw)


def call_absolute(spec: deg.DegradationSpec, x: np.ndarray, severity: float,
                  **kw) -> np.ndarray:
    """Apply an operator at a severity already in its own units.

    Used by the tests that are about a filter's spectral behaviour rather than about the
    ladder, where a wavenumber is the meaningful thing to state.

    An operator declaring ``ensemble=True`` is handed a member stack built from ``x`` and
    returns one; the caller sees the same shape it passed in, so the generic contract
    tests below need no special case. Where a *field* is the meaningful thing to compare
    -- shape, dtype, damage -- the ensemble mean stands in for it.
    """
    kwargs = dict(spec.defaults)
    kwargs.update(kw)
    if spec.takes_ctx:
        kwargs["ctx"] = make_ctx(x)
    if spec.ensemble:
        out = spec.fn(members(x), severity, **kwargs)
        # The member stack itself: dispersion changes leave the mean fixed, so the shared
        # assertions compare stacks, and damage is measured against the ensemble's spread.
        return np.asarray(out, dtype=np.float64)
    return spec.fn(x, severity, **kwargs)


#: Severities that meaningfully exercise each operator, in increasing-damage order.
LADDERS: dict[str, list[float]] = {
    "identity": [0],
    # The calibrated operators take their severities in config units -- a fraction of the
    # characteristic scale, or of the energy to remove -- and `call` resolves them.
    "gaussian_blur": [0.02, 0.06, 0.15, 0.30],
    "box_blur": [0.06, 0.15, 0.30],
    "median_blur": [0.06, 0.15, 0.30],
    "disk_blur": [0.06, 0.15, 0.30],
    "epanechnikov_blur": [0.06, 0.15, 0.30],
    "lowpass_ideal": [0.05, 0.20, 0.45],
    "lowpass_butterworth": [0.05, 0.20, 0.45],
    "highpass_ideal": [0.45, 0.70, 0.90],
    "highpass_butterworth": [0.45, 0.70, 0.90],
    "band_attenuate": [0.8, 0.4, 0.0],
    "translate": [1, 2, 4],
    "translate_subpixel": [0.25, 0.5, 1.0],
    "coarsen": [2, 4, 8],
    "coarsen_bandlimited": [2, 4, 8],
    "subsample": [2, 4, 8],
    "additive_noise": [0.01, 0.1, 0.5],
    "multiplicative_noise": [0.01, 0.1, 0.5],
    "gaussian_impostor": [0],
    "random_large_translation": [0, 1, 2],   # draw indices, not damage levels
    "gain": [0.05, 0.2, 0.5],
    "bias": [0.05, 0.2, 0.5],
    # Ensemble dispersion. Severities are fractions of the calibrated spread: excess for
    # inflate, removed for deflate, so zero is a no-op on both and neither exceeds one.
    "spread_inflate": [0.25, 1.0, 3.0],
    "spread_deflate": [0.25, 0.5, 0.9],
}


@pytest.fixture(params=sorted(deg.available()))
def spec(request) -> deg.DegradationSpec:
    return deg.get(request.param)


def test_no_import_errors():
    assert deg.discover() == {}


def test_every_operator_has_a_test_ladder(spec):
    """A new operator must be added to LADDERS, or it escapes every check below."""
    assert spec.name in LADDERS, f"add {spec.name!r} to LADDERS in this file"


def test_preserves_shape_and_dtype(spec):
    x = synthetic_field(SHAPE, 2, seed=0)
    want = members(x).shape if spec.ensemble else x.shape
    out = call(spec, x, LADDERS[spec.name][-1])
    assert out.shape == want
    assert np.asarray(out).dtype == np.float64
    assert np.isfinite(out).all(), f"{spec.name} produced non-finite values"


def test_zero_severity_matches_its_declaration(spec):
    """Severity 0 is a no-op exactly when the operator declares ``zero_is_identity``.

    A no-op at 0 is what makes pairwise metrics return 0 on the clean level. 0 is the
    config-facing severity, so a calibrated operator is judged after resolution: removing no
    energy keeps every mode of a sharp low-pass, while a Butterworth high-pass still attenuates
    the lowest shells a little. Checked both ways, so an operator that is the identity at 0
    without declaring it is caught as surely as one that declares it falsely.
    """
    x = synthetic_field(SHAPE, 1, seed=0)
    want = members(x) if spec.ensemble else x
    unchanged = np.allclose(call(spec, x, 0), want, rtol=0, atol=1e-15)
    assert unchanged == spec.zero_is_identity, (
        f"{spec.name} declares zero_is_identity={spec.zero_is_identity} but severity 0 "
        f"{'left the field unchanged' if unchanged else 'changed the field'}"
    )


def test_declared_direction_is_true(spec):
    """Verify severity_direction by measuring that damage rises with level.

    A reversed list inverts the Spearman for that axis, silently.
    """
    if not spec.ordinal or spec.name == "identity":
        pytest.skip("not on a monotone axis")
    x = (smooth_field() if spec.calibration
         else synthetic_field(SHAPE, 1, seed=0, noise=0.02))
    severities = spec.sort_severities(LADDERS[spec.name])
    if spec.ensemble:
        # An ensemble operator is judged by how far it moves the *members* from the
        # calibrated ensemble, not by how far it moves a field: dispersion scaling
        # leaves the ensemble mean exactly where it was, so a mean-based damage measure
        # would read zero at every severity and the direction test would prove nothing.
        clean = members(x)
        damage = [float(((clean - call(spec, x, s)) ** 2).mean()) for s in severities]
    else:
        damage = [float(((x - call(spec, x, s)) ** 2).mean()) for s in severities]
    assert damage[-1] > 0, (
        f"{spec.name}: the harshest test severity does nothing, so this test proves nothing; "
        "the entry in LADDERS is too mild for the field it is applied to"
    )
    assert damage == sorted(damage), (
        f"{spec.name}: damage {damage} is not increasing across sorted severities "
        f"{severities}; severity_direction={spec.severity_direction!r} may be wrong"
    )


def test_sort_severities_orders_by_damage(spec):
    """Config order must not matter: the builder sorts into increasing-damage order."""
    given = LADDERS[spec.name]
    assert spec.sort_severities(list(reversed(given))) == spec.sort_severities(given)


def test_deterministic_operators_are_reproducible(spec):
    if spec.stochastic:
        pytest.skip("stochastic")
    x = synthetic_field(SHAPE, 1, seed=0)
    s = LADDERS[spec.name][-1]
    assert np.array_equal(call(spec, x, s), call(spec, x, s))


def test_stochastic_operators_are_seed_reproducible(spec):
    if not spec.stochastic:
        pytest.skip("deterministic")
    x = synthetic_field(SHAPE, 1, seed=0)
    s = LADDERS[spec.name][-1]
    kw = dict(spec.defaults)

    def run(seed, frame_index, field):
        c = FieldContext("vorticity", unit_grid(SHAPE), frame_index, 0.0, fluctuation_rms(x),
                         derive_rng(seed, "lbl", frame_index, field))
        return spec.fn(x, s, **{**kw, "ctx": c})

    assert np.array_equal(run(7, 0, "vorticity"), run(7, 0, "vorticity"))
    assert not np.array_equal(run(7, 0, "vorticity"), run(7, 1, "vorticity"))
    assert not np.array_equal(run(7, 0, "vorticity"), run(7, 0, "density"))
    assert not np.array_equal(run(7, 0, "vorticity"), run(8, 0, "vorticity"))


#: Absolute severities for the boundary test, which bypasses calibration: a calibrated cutoff
#: is in cycles across the domain, and the extended domain is twice as long, so resolving the
#: same fraction on both grids would compare two different experiments.
BOUNDARY_SEVERITY = {"scale": 6.0, "energy_above": 16.0, "energy_below": 4.0}

#: Operators that act within a few cells, so across a Neumann boundary they must not see the far
#: end of the domain at all. Measured: each moves the left end by 0.2-0.5 on a periodic grid.
LOCAL_OPERATORS = ("gaussian_blur", "box_blur", "disk_blur", "epanechnikov_blur", "translate",
                   "translate_subpixel")


def _absolute_level(spec: deg.DegradationSpec) -> SeverityLevel:
    """The operator's harshest test severity as a ladder level, in absolute units."""
    severity = (BOUNDARY_SEVERITY[spec.calibration] if spec.calibration
                else LADDERS[spec.name][-1])
    return dataclasses.replace(
        SeverityLevel.from_spec(spec, label=spec.name, level=1, severity=severity, options={}),
        calibration=None)


def _left_end_response(spec: deg.DegradationSpec, boundary: str) -> float:
    """How far the first 16 cells of the output move when only the last 32 of the input do."""
    n = 256
    step = np.where(np.arange(n) < n // 2, 1.0, 0.125)[None]
    bumped = step.copy()
    bumped[0, -32:] += 0.5
    level = _absolute_level(spec)
    grid = GridSpec((n,), (1.0,), (boundary,), ("x",), (0.0,))
    left = [apply_severity_level(level, Frame(0, 0.0, {"density": f}, grid), ["density"],
                                 seed=0).fields["density"][0, :16] for f in (step, bumped)]
    return float(np.abs(left[0] - left[1]).max())


def test_the_far_end_does_not_reach_across_a_neumann_boundary(spec):
    """Every operator wraps, so on a non-periodic axis the driver extends the field across the
    boundary by its rule before applying it (``fmeval.ladder._call``).

    Measured as the response of the left end to a change confined to the right end. On a
    periodic grid the two ends are neighbours; across a Neumann wall the even extension puts
    them half the extended domain apart. So no operator may respond more there than on the
    periodic grid, and a local one -- a blur or a translation -- must not respond at all.
    Pointwise operators still respond a little on both, because their amplitude is relative to
    the field's fluctuation RMS, which the bump changes; that is not a leak, and it is equal on
    both grids. (Extension of a zero-gradient wall: LeVeque (2002), Finite Volume Methods for
    Hyperbolic Problems, Cambridge, Sect. 7.3.3, ghost cells eq. (7.17) for the even fields.)
    """
    if spec.ensemble:
        pytest.skip("acts on a member stack, not across space")
    periodic, neumann = (_left_end_response(spec, b) for b in ("periodic", "neumann"))
    assert neumann <= periodic + 1e-12, (
        f"{spec.name}: the left end moves by {neumann:.3g} across a Neumann boundary but only "
        f"{periodic:.3g} across a periodic one; the extension is not reaching this operator"
    )
    if spec.name in LOCAL_OPERATORS:
        assert periodic > 0.1, f"{spec.name}: no wrap-around on a periodic grid, test is vacuous"
        assert neumann < 1e-12, (
            f"{spec.name}: a local operator moved the left end by {neumann:.3g} when only the "
            "right end changed, so it still sees across the boundary"
        )


def test_a_walled_ensemble_is_degraded_member_by_member(spec):
    """An ensemble frame on a grid with a Neumann x-axis and a periodic y-axis goes through the
    same extension and crop (``fmeval.ladder._call``) with the member axis leading.

    A deterministic per-member operator gives each member exactly what it gives that member
    alone on the same grid, so the member axis survives the extension and the crop and the
    periodic axis is not extended. An ensemble operator returns the stack's shape, and keeps
    the member mean where it declares so. A stochastic operator draws per member, so only its
    shape is checked.
    """
    grid = GridSpec(SHAPE, (1.0, 1.0), ("neumann", "periodic"), ("x", "y"), (0.0, 0.0))
    x = synthetic_field(SHAPE, 2, seed=3)
    stack = members(x)
    rms = {"velocity": fluctuation_rms(x)}
    level = _absolute_level(spec)
    out = apply_severity_level(level, Frame(0, 0.0, {"velocity": x}, grid,
                                            members={"velocity": stack}),
                               ["velocity"], seed=0, reference_rms=rms).members["velocity"]
    assert out.shape == stack.shape, f"{spec.name}: {stack.shape} -> {out.shape}"
    if spec.ensemble:
        if "ensemble_mean" in spec.preserves:
            np.testing.assert_allclose(out.mean(axis=0), stack.mean(axis=0), atol=1e-12)
    elif not spec.stochastic:
        alone = [apply_severity_level(level, Frame(0, 0.0, {"velocity": m}, grid), ["velocity"],
                                      seed=0, reference_rms=rms).fields["velocity"]
                 for m in stack]
        np.testing.assert_array_equal(out, np.stack(alone), err_msg=spec.name)


@pytest.mark.xfail(strict=True, reason="issues/046: |k| counts cycles across each axis's own "
                   "length, and the extension doubles only the walled axis")
def test_a_low_pass_treats_both_axes_of_a_walled_square_grid_alike():
    """A wave of one wavelength is filtered alike along x and y on a square grid, whichever
    axis has the wall. Measured: with a Neumann x-axis and an absolute cutoff of 6, the
    16-cell wave along x is removed and the same wave along y is kept."""
    n = 64
    grid = GridSpec((n, n), (1.0, 1.0), ("neumann", "periodic"), ("x", "y"), (0.0, 0.0))
    wave = np.cos(2 * np.pi * (np.arange(n) + 0.5) / 16)
    level = dataclasses.replace(
        SeverityLevel.from_spec(deg.get("lowpass_ideal"), label="lowpass_ideal", level=1,
                                severity=6.0, options={}),
        calibration=None)
    kept = [float(apply_severity_level(level, Frame(0, 0.0, {"density": f[None]}, grid),
                                       ["density"], seed=0).fields["density"].std() / f.std())
            for f in (np.broadcast_to(wave[:, None], (n, n)), np.broadcast_to(wave, (n, n)))]
    assert kept[0] == pytest.approx(kept[1], abs=1e-6), f"kept along x, y: {kept}"


# --- operator-specific properties ---------------------------------------------------


def test_translate_is_periodic():
    x = synthetic_field(SHAPE, 1, seed=0)
    s = deg.get("translate")
    assert np.array_equal(call(s, x, SHAPE[0], axis="x"), x)


def test_translate_moves_the_declared_axis():
    """axis='x' must move axis -2 on a 2D grid, not axis -1."""
    x = synthetic_field(SHAPE, 1, seed=0)
    s = deg.get("translate")
    assert np.array_equal(call(s, x, 3, axis="x"), np.roll(x, 3, axis=-2))
    assert np.array_equal(call(s, x, 3, axis="y"), np.roll(x, 3, axis=-1))


def test_subpixel_translate_matches_roll_at_integer_distance():
    """The sub-pixel operator must agree with the exact one where both are defined."""
    x = synthetic_field(SHAPE, 1, seed=0)
    s = deg.get("translate_subpixel")
    for d in (1, 2, 5):
        assert np.allclose(call(s, x, d, axis="x"), np.roll(x, d, axis=-2), atol=1e-10)


def test_subpixel_translate_resolves_below_one_cell():
    """The whole point: sub-cell displacement must be distinguishable from 0 and from 1."""
    x = synthetic_field(SHAPE, 1, seed=0)
    s = deg.get("translate_subpixel")
    half = call(s, x, 0.5, axis="x")
    assert not np.allclose(half, x)
    assert not np.allclose(half, np.roll(x, 1, axis=-2))


@pytest.mark.parametrize("match_moments", [
    # The default, and the form the ladder runs. The moment restoration rescales the field
    # after the phases are randomised, so it could in principle disturb exactly what the
    # construction is for.
    pytest.param(True, id="moments-matched"),
    # The bare phase randomisation, before any rescaling.
    pytest.param(False, id="bare"),
])
def test_impostor_preserves_the_spectrum_exactly(match_moments):
    """IN-4's defining property: identical |X_k|, hence identical E(k), with or without the
    moment restoration.

    On the real 256^2 vorticity field at t = 5000 the radial spectra agree to a relative L1
    error of 1.6e-16 with the moments matched and 1.5e-16 without.
    """
    x = synthetic_field((32, 32), 1, seed=0, noise=0.3)
    y = call(deg.get("gaussian_impostor"), x, 0, match_moments=match_moments)
    assert np.allclose(np.abs(np.fft.fftn(x[0])), np.abs(np.fft.fftn(y[0])), rtol=1e-8)


def _flatness(a: np.ndarray) -> float:
    f = a - a.mean()
    return float((f**4).mean() / (f**2).mean() ** 2)


def test_impostor_is_real_and_gaussian():
    """Hermitian symmetry must hold, and the result must actually be Gaussian.

    A hand-drawn-phase implementation fails both: ``irfftn`` silently discards imaginary
    parts and the flatness lands far from 3 (47.9 measured).

    Flatness is a fourth moment and noisy on one realisation -- measured spread on a 64^2
    grid is 2.9 +/- 0.2 across seeds -- so the tight assertion is on the mean over several
    seeds, with a loose per-seed bound that still separates 3 from a broken 48.
    """
    spec = deg.get("gaussian_impostor")
    # Strongly intermittent: sparse spikes on a smooth background.
    x = synthetic_field((64, 64), 1, seed=0, noise=0.0)
    x[0, ::16, ::16] += 20.0
    assert _flatness(x[0]) > 50, "test field is not intermittent enough to discriminate"

    values = []
    for seed in range(8):
        y = spec.fn(x, 0, ctx=make_ctx(x, field="v", seed=seed, label="impostor"),
                    **spec.defaults)
        assert np.isrealobj(y) and np.isfinite(y).all()
        f = _flatness(y[0])
        assert f < 10, (
            f"impostor flatness {f:.2f} is nowhere near Gaussian; the phase construction "
            "is probably violating Hermitian symmetry"
        )
        values.append(f)
    assert float(np.mean(values)) == pytest.approx(3.0, abs=0.3)


def test_impostor_matches_moments():
    x = synthetic_field((32, 32), 1, seed=0, noise=0.3)
    y = call(deg.get("gaussian_impostor"), x, 0)
    assert y.mean() == pytest.approx(x.mean(), rel=1e-9)
    assert y.std() == pytest.approx(x.std(), rel=1e-9)


def _draws(x, n=8):
    """``n`` draws of the unrelated-field anchor, each from its own seed."""
    spec = deg.get("random_large_translation")
    return [spec.fn(x, 0, ctx=make_ctx(x, field="v", seed=seed, label="unc"))
            for seed in range(n)]


def test_random_large_translation_always_moves_by_at_least_a_quarter_domain():
    """The guarantee the operator makes: offsets come from the middle half of each axis."""
    x = np.arange(64 * 64, dtype=float).reshape(1, 64, 64)  # every cell distinguishable
    for y in _draws(x):
        # Recover the offset from where the original first element ended up.
        idx = int(np.argwhere(y[0] == 0.0)[0][0])
        assert 16 <= idx <= 48, f"offset {idx} is outside the middle half"


def test_random_large_translation_decorrelates_a_broadband_field():
    """Averaged over draws it reaches the uncorrelated limit on a realistic field.

    Deliberately broadband. A field dominated by one large-scale mode is a known bad case
    -- see the caveat in the operator docstring -- and the median over draws, not any
    single draw, is what the anchor uses.
    """
    rng = np.random.default_rng(0)
    x = synthetic_field((64, 64), 1, seed=0, noise=1.0)
    x += 0.5 * rng.standard_normal(x.shape)
    corrs = [abs(float(np.corrcoef(x.ravel(), y.ravel())[0, 1])) for y in _draws(x)]
    assert float(np.median(corrs)) < 0.2, f"median |corr| over draws is {corrs}"


def test_random_large_translation_is_not_ordinal():
    """It is a reference measurement defining D = 1, not a severity level on a monotone axis."""
    assert deg.get("random_large_translation").ordinal is False


def test_lowpass_then_highpass_reconstructs():
    """Ideal filters at a shared cutoff partition the spectrum, up to two shared modes.

    Both keep the cutoff band |k| == c, and the high-pass additionally keeps k = 0 on
    purpose (see highpass_ideal), so each is counted twice and subtracted once.
    """
    x = synthetic_field((32, 32), 1, seed=0, noise=0.3)
    lo = call_absolute(deg.get("lowpass_ideal"), x, 8)
    hi = call_absolute(deg.get("highpass_ideal"), x, 8)
    k = wavenumber_magnitude((32, 32))
    overlap = _apply_filter(x, (k == 8).astype(float))
    mean = np.full_like(x, x.mean())
    assert np.allclose(lo + hi - overlap - mean, x, atol=1e-10)


def test_gain_preserves_the_mean_and_moves_only_amplitude():
    x = synthetic_field(SHAPE, 1, seed=0)
    y = call(deg.get("gain"), x, 0.5)
    assert y.mean() == pytest.approx(x.mean(), rel=1e-12)
    fluct_x, fluct_y = x - x.mean(), y - y.mean()
    assert np.allclose(fluct_y, 1.5 * fluct_x)


def test_bias_shifts_the_mean_only():
    x = synthetic_field(SHAPE, 1, seed=0)
    y = call(deg.get("bias"), x, 0.25)
    assert np.allclose(y - x, 0.25 * fluctuation_rms(x))


# --- ladder construction --------------------------------------------------------------


def test_build_ladder_expands_entries():
    severity_levels = build_ladder({"gaussian_blur": {"severities": [1.0, 2.0]}})
    assert [r.variant_label for r in severity_levels] == [
        "reference", "gaussian_blur_l1", "gaussian_blur_l2"
    ]
    assert [r.level for r in severity_levels] == [0, 1, 2]
    assert [r.severity for r in severity_levels] == [0.0, 1.0, 2.0]


def test_build_ladder_applies_its_keywords_to_a_config_block_too():
    """A keyword means the same whether the ladder comes as a mapping or as the config block."""
    entries = {"gaussian_blur": {"severities": [1.0]}, "translate_x": {"op": "translate",
                                                                      "severities": [1]}}
    block = DegradationConfig(ladder=entries)
    for ladder in (entries, block):
        levels = build_ladder(ladder, include_reference=False, skip=["translate_x"])
        assert [r.variant_label for r in levels] == ["gaussian_blur_l1"]
        with pytest.raises(TypeError, match="bogus"):
            build_ladder(ladder, bogus=1)
    assert block.include_reference and not block.skip, "the caller's block was modified"


def test_build_ladder_refuses_an_option_its_operator_does_not_take():
    """A misspelt option is refused when the ladder is built, before any data is read, rather
    than when the operator is first called."""
    with pytest.raises(ValueError, match=r"\['ordr'\].*it takes \['order'\]"):
        build_ladder({"lowpass_butterworth": {"severities": [0.3], "options": {"ordr": 2}}})
    (level,) = build_ladder({"lowpass_butterworth": {"severities": [0.3], "options": {"order": 2}}},
                            include_reference=False)
    assert level.options == {"order": 2}


def test_build_ladder_sorts_decreasing_direction_correctly():
    """A decreasing-direction list is worst-last after sorting, however it was written.

    ``band_attenuate`` is the example because its severity is the fraction *retained*, so
    smaller is worse; the spectral filters' severity is the fraction of energy removed, which
    rises with damage like everything else.
    """
    assert deg.get("band_attenuate").severity_direction == "decreasing"
    for given in ([0.8, 0.5, 0.2, 0.0], [0.0, 0.2, 0.5, 0.8]):
        severity_levels = build_ladder({"band_attenuate": {"severities": given}},
                             include_reference=False)
        assert [r.severity for r in severity_levels] == [0.8, 0.5, 0.2, 0.0]
        assert [r.level for r in severity_levels] == [1, 2, 3, 4]


def test_build_ladder_supports_two_instances_of_one_operator():
    cfg = {
        "translate_x": {"op": "translate", "severities": [1, 2], "options": {"axis": "x"}},
        "translate_y": {"op": "translate", "severities": [1, 2], "options": {"axis": "y"}},
    }
    severity_levels = build_ladder(cfg, include_reference=False)
    assert ladder_axes(severity_levels) == ["translate_x", "translate_y"]
    assert {r.op for r in severity_levels} == {"translate"}


def test_build_ladder_honours_enabled_only_and_skip():
    cfg = {
        "gaussian_blur": {"severities": [1]},
        "median_blur": {"severities": [3], "enabled": False},
        "coarsen": {"severities": [2]},
    }
    assert ladder_axes(build_ladder(cfg)) == ["gaussian_blur", "coarsen"]
    assert ladder_axes(build_ladder(cfg, only=["coarsen"])) == ["coarsen"]
    assert ladder_axes(build_ladder(cfg, skip=["coarsen"])) == ["gaussian_blur"]


def test_ordinal_axes_excludes_the_canary():
    cfg = {
        "gaussian_blur": {"severities": [1, 2]},
        "gaussian_impostor": {"severities": [0]},
    }
    severity_levels = build_ladder(cfg)
    assert ladder_axes(severity_levels) == ["gaussian_blur", "gaussian_impostor"]
    assert ordinal_axes(severity_levels) == ["gaussian_blur"]


def test_build_ladder_rejects_malformed_entries():
    with pytest.raises(ValueError, match="no 'severities'"):
        build_ladder({"gaussian_blur": {}})
    with pytest.raises(ValueError, match="unexpected keys"):
        build_ladder({"gaussian_blur": {"severities": [1], "typo": 3}})
    with pytest.raises(KeyError, match="unknown degradation"):
        build_ladder({"nope": {"severities": [1]}})


# --- applying severity levels to frames ---------------------------------------------------------


def _frame() -> Frame:
    g = unit_grid(SHAPE)
    return Frame(
        index=3,
        time=1.5,
        fields={
            "density": 1.0 + 1e-3 * synthetic_field(SHAPE, 1, seed=1),
            "velocity": 0.04 * synthetic_field(SHAPE, 2, seed=2),
        },
        grid=g,
    )


def test_apply_reference_level_returns_the_originals():
    frame = _frame()
    out = apply_severity_level(REFERENCE_LEVEL, frame, ["density", "velocity"], seed=0).fields
    for name, arr in out.items():
        assert arr is frame.fields[name]


def test_apply_severity_level_degrades_every_requested_field():
    frame = _frame()
    severity_level = build_ladder({"gaussian_blur": {"severities": [0.3]}},
                        include_reference=False)[0]
    applied = apply_severity_level(
        severity_level, frame, ["density", "velocity"], seed=0,
        calibration=calibrate({name: [frame[name]] for name in frame.fields}, frame.grid,
                              ["density", "velocity"]),
    )
    out = applied.fields
    assert set(out) == {"density", "velocity"}
    assert set(applied.resolved) == {"density", "velocity"}
    assert set(applied.energy_removed) == {"density", "velocity"}
    for name, arr in out.items():
        assert arr.shape == frame.fields[name].shape
        assert not np.allclose(arr, frame.fields[name])


def test_apply_severity_level_is_invariant_to_frame_iteration_order():
    """Seeding from content, not call order, is what makes parallelisation safe later."""
    frame = _frame()
    severity_level = build_ladder({"additive_noise": {"severities": [0.1]}},
                        include_reference=False)[0]
    first = apply_severity_level(severity_level, frame, ["density"], seed=11).fields["density"]
    _ = apply_severity_level(severity_level, frame, ["velocity"], seed=11)  # advance nothing
    again = apply_severity_level(severity_level, frame, ["density"], seed=11).fields["density"]
    assert np.array_equal(first, again)


def test_noise_scales_with_the_reference_rms_not_the_raw_rms():
    """Density is 1.0 +/- 1e-3: scaling by the raw RMS would be pure destruction."""
    frame = _frame()
    severity_level = build_ladder({"additive_noise": {"severities": [0.1]}},
                        include_reference=False)[0]
    rms = fluctuation_rms(frame["density"])
    out = apply_severity_level(severity_level, frame, ["density"], seed=0,
                     reference_rms={"density": rms}).fields["density"]
    perturbation = np.abs(out - frame["density"]).mean()
    assert perturbation < 0.5 * frame["density"].mean(), "noise swamped the signal"
    assert perturbation == pytest.approx(0.1 * rms * np.sqrt(2 / np.pi), rel=0.25)


def test_highpass_ladder_is_monotone_on_a_field_with_a_large_mean():
    """Monotone, and on the scale of the fluctuation rather than of the mean.

    Density is 1.0 with fluctuations of order 1e-4, so a high-pass that removed k=0 would give
    every severity level the same damage, set by the mean, and the axis would carry no
    ordering. The declared ``spatial_mean`` preservation is checked by the contract below.
    """
    x = 1.0 + 1e-3 * synthetic_field((32, 32), 1, seed=0, noise=0.3)
    spec = deg.get("highpass_ideal")
    damage = [float(((x - call_absolute(spec, x, c)) ** 2).mean())
              for c in (2, 4, 8, 16)]
    assert damage == sorted(damage), f"high-pass ladder is not monotone: {damage}"
    assert damage[-1] > 1.5 * damage[0], f"ladder has little dynamic range: {damage}"
    # The decisive check: deleting the mean would put every severity level ~1e7 times above
    # the fluctuation variance.
    variance = float(np.var(x))
    assert damage[-1] < variance, (
        f"damage {damage[-1]:.3e} exceeds the fluctuation variance {variance:.3e}; "
        "the filter is probably removing the spatial mean"
    )


# --- declared preservation ---------------------------------------------------------------------

#: Relative change below which a declared property counts as preserved. An FFT round trip on this
#: grid moves values by ~1e-15; the smallest genuine change any operator here makes to the test
#: field is ~1e-3 of its range (median blur's mean, measured). Fixed once, never per operator.
PRESERVATION_TOLERANCE = 1e-9


def _fluctuation_amplitudes(x: np.ndarray) -> np.ndarray:
    spatial = tuple(range(1, x.ndim))
    return np.abs(np.fft.fftn(x - x.mean(axis=spatial, keepdims=True), axes=spatial))


def _standardised(x: np.ndarray) -> np.ndarray | None:
    spatial = tuple(range(1, x.ndim))
    centred = x - x.mean(axis=spatial, keepdims=True)
    spread = centred.std(axis=spatial, keepdims=True)
    return None if np.any(spread == 0) else centred / spread


def _rigid_shift_residual(x: np.ndarray, y: np.ndarray) -> float:
    """How far ``y`` is from ``x`` moved rigidly by any shift, up to an increasing affine map.

    The displacement along each axis is read off the phase of the lowest mode along it and removed;
    what remains is compared with the standardised original.
    """
    xs, ys = _standardised(x), _standardised(y)
    if xs is None or ys is None:
        return float("inf")
    X, Y = np.fft.fftn(xs[0]), np.fft.fftn(ys[0])
    for axis, n in enumerate(x.shape[1:]):
        unit = tuple(1 if a == axis else 0 for a in range(X.ndim))
        assert abs(X[unit]) > 1e-6 * abs(X).max(), "test field has no energy in a unit mode"
        delta = -np.angle(Y[unit] * np.conj(X[unit])) * n / (2 * np.pi)
        freq = np.fft.fftfreq(n).reshape([-1 if a == axis else 1 for a in range(X.ndim)])
        Y = Y * np.exp(2j * np.pi * freq * delta)
    return float(np.max(np.abs(np.fft.ifftn(Y).real - xs[0])) / np.max(np.abs(xs[0])))


#: One residual per word of degradations.registry.PRESERVED, each relative to the original.
PRESERVATION_CHECKS = {
    "single_point_statistics": lambda x, y: float(
        np.max(np.abs(np.sort(y.ravel()) - np.sort(x.ravel()))) / np.max(np.abs(x))),
    "amplitude_spectrum": lambda x, y: float(
        np.max(np.abs(_fluctuation_amplitudes(y) - _fluctuation_amplitudes(x)))
        / np.max(_fluctuation_amplitudes(x))),
    "spatial_mean": lambda x, y: float(
        np.max(np.abs(y.mean(axis=(1, 2)) - x.mean(axis=(1, 2)))) / np.max(np.abs(x))),
    "shape": _rigid_shift_residual,
    # Over a member stack (N, C, *spatial): the member mean, cell by cell.
    "ensemble_mean": lambda x, y: float(
        np.max(np.abs(y.mean(axis=0) - x.mean(axis=0))) / np.max(np.abs(x))),
}


def test_every_preserved_word_has_a_check():
    assert set(PRESERVATION_CHECKS) == set(deg.PRESERVED)


def test_declared_preservation_is_true(spec):
    """Every declared word is measured at every test severity, as severity_direction is.

    One-way by design: an operator may preserve a property on this field without guaranteeing it,
    so only a declaration is checked, never an absence.
    """
    if not spec.preserves:
        pytest.skip("declares nothing")
    x = synthetic_field(SHAPE, 1, seed=0)
    before = members(x) if spec.ensemble else x
    for severity in LADDERS[spec.name]:
        y = call(spec, x, severity)
        for word in spec.preserves:
            residual = PRESERVATION_CHECKS[word](before, y)
            assert residual < PRESERVATION_TOLERANCE, (
                f"{spec.name} declares preserves={word!r} but severity {severity} changed it by a "
                f"relative {residual:.2e}; the declaration is false -- remove the word, do not "
                "loosen the tolerance"
            )


def test_an_ensemble_word_needs_an_ensemble_operator(temporary_degradation):
    """``ensemble_mean`` describes a member stack, the other words a field; they cannot mix."""
    with pytest.raises(ValueError, match="describes a member stack"):
        @temporary_degradation(name="_probe_field_claims_ensemble", preserves=("ensemble_mean",))
        def _field(x, severity):
            return x
    with pytest.raises(ValueError, match="a field"):
        @temporary_degradation(name="_probe_ensemble_claims_field", ensemble=True,
                               preserves=("spatial_mean",))
        def _ensemble(members, severity):
            return members


def test_preservation_vocabulary_is_closed():
    with pytest.raises(ValueError, match=r"PRESERVED|vocabulary"):
        deg.degradation(name="_unregistered_colour", preserves=("colour",))(lambda x, s: x)


def test_preservation_checks_have_teeth():
    """A check that passes for everything verifies nothing."""
    x = synthetic_field(SHAPE, 1, seed=0)
    subpixel, blur = deg.get("translate_subpixel"), deg.get("gaussian_blur")
    assert PRESERVATION_CHECKS["single_point_statistics"](x, call(subpixel, x, 0.5)) > 1e-3
    assert PRESERVATION_CHECKS["shape"](x, call(deg.get("gaussian_impostor"), x, 0)) > 1e-1
    assert PRESERVATION_CHECKS["amplitude_spectrum"](x, call(blur, x, 0.3)) > 1e-3
    median = call_absolute(deg.get("median_blur"), x, 3)
    assert PRESERVATION_CHECKS["spatial_mean"](x, median) > 1e-6
    # A field with nothing at the grid scale is shifted exactly by a fraction of a cell, and the
    # shape check recognises a fractional rigid shift as one.
    band_limited = np.fft.fftn(x[0])
    band_limited[SHAPE[0] // 2, :] = 0
    band_limited[:, SHAPE[1] // 2] = 0
    smooth = np.fft.ifftn(band_limited).real[None]
    assert PRESERVATION_CHECKS["shape"](smooth, call(subpixel, smooth, 0.5)) < 1e-9


def test_a_fractional_shift_loses_the_nyquist_mode_of_an_even_grid():
    """Why translate_subpixel declares only the mean: the phase ramp makes the Nyquist component
    imaginary and the real part discards it. 1.7e-2 of the amplitude on this white-noise field;
    at most 8.2e-11 of the fluctuation energy on frame 5000 of kinet_re5e4 (issues/041)."""
    x = synthetic_field(SHAPE, 1, seed=0)
    y = call(deg.get("translate_subpixel"), x, 0.5)
    assert PRESERVATION_CHECKS["amplitude_spectrum"](x, y) > 1e-3
