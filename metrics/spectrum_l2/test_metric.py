"""Tests for the radial-spectrum distance.

The registry-wide contract lives in ``tests/test_metric_contract.py``. What is tested here
is the worked example in the card, the closed-form values for a field scaled or emptied,
and the invariance that is the whole reason this metric is in the repository as a baseline
rather than a candidate: it cannot see phase.

Every expected value is derived in the docstring beside it rather than copied from a run.
"""

from __future__ import annotations

import numpy as np
import pytest

from fmeval.context import FieldContext
from fmeval.data.base import GridSpec

from .metric import radial_energy_spectrum, spectrum_l2


def _ctx(shape: tuple[int, ...]) -> FieldContext:
    return FieldContext(
        field="density",
        grid=GridSpec(shape=shape, spacing=(1.0,) * len(shape),
                      periodic=(True,) * len(shape)),
        frame_index=0,
        time=0.0,
        fluctuation_rms=1.0,
        rng=np.random.default_rng(0),
    )


def _wave(shape: tuple[int, int], mode: int, phase: float = 0.0) -> np.ndarray:
    """``cos(2 pi m x / L + phase)`` along x, constant along y."""
    x = np.arange(shape[0])
    profile = np.cos(2.0 * np.pi * mode * x / shape[0] + phase)
    return np.broadcast_to(profile[:, None], shape).copy()[np.newaxis, ...]


def test_a_shifted_wave_is_at_distance_zero():
    """The defining blindness: changing phase alone leaves the spectrum untouched.

    A cosine and a sine of the same wavenumber have identical amplitude at every mode and
    differ only in phase, so this metric reports them as indistinguishable while any
    pointwise norm reports a large error. This is the property that lets the Gaussian
    impostor catch metrics of this kind.
    """
    ctx = _ctx((8, 8))
    cosine = _wave((8, 8), mode=1)
    sine = _wave((8, 8), mode=1, phase=np.pi / 2)

    assert spectrum_l2(cosine, sine, ctx=ctx) == pytest.approx(0.0, abs=1e-12)
    # ... and the two are genuinely different fields, so the blindness is real.
    assert not np.allclose(cosine, sine)


def test_worked_example_from_the_card():
    """A wave against a flat field scores exactly 1.

    With no fluctuation the candidate's spectrum is identically zero, so the numerator and
    the denominator of the relative distance are the same quantity and the ratio is 1.
    """
    ctx = _ctx((4, 4))
    assert spectrum_l2(_wave((4, 4), mode=1), np.zeros((1, 4, 4)), ctx=ctx) == pytest.approx(1.0)


def test_worked_example_one_cell_shift():
    """The card's second example: the same 4x4 wave moved by one cell.

    The profile along x goes from (1, 0, -1, 0) to (0, 1, 0, -1), so the two disagree in
    every cell, by 1 in each, and the root-mean-square error is exactly 1 -- larger than the
    wave's own rms of 1/sqrt(2). It is not the largest error a field of this amplitude can
    have: the negated wave differs by 2 wherever the wave is nonzero, an rms of sqrt(2).
    The spectrum distance is 0, because a shift changes only phase.
    """
    ctx = _ctx((4, 4))
    reference = _wave((4, 4), mode=1)
    shifted = np.roll(reference, 1, axis=1)

    assert spectrum_l2(reference, shifted, ctx=ctx) == pytest.approx(0.0, abs=1e-12)
    assert np.sqrt(np.mean((reference - shifted) ** 2)) == pytest.approx(1.0)
    assert np.sqrt(np.mean((reference + reference) ** 2)) == pytest.approx(np.sqrt(2.0))


def test_scrambling_the_cells_is_not_a_phase_change():
    """Permuting cells destroys the spectrum, so the metric sees it.

    Only operations that keep every Fourier amplitude -- a translation, a phase
    randomisation -- are invisible here. A random permutation of the cells whitens the
    spectrum instead: a smooth field's energy is spread evenly over every mode, so almost
    none of it stays in the shells the reference occupied. An earlier draft of the card said
    a scrambled field scores perfectly; it scores about 1 on this field.
    """
    shape = (64, 64)
    ctx = _ctx(shape)
    field = _wave(shape, mode=1) + 0.3 * _wave(shape, mode=3)
    order = np.random.default_rng(1).permutation(field.size)
    scrambled = field.reshape(-1)[order].reshape(field.shape)

    assert spectrum_l2(field, scrambled, ctx=ctx) > 0.9


def test_doubling_the_amplitude_scores_three():
    """Energy goes as amplitude squared, so a candidate at twice the amplitude has four
    times the energy in every shell. The spectra then differ by 3 times the reference
    everywhere, and the relative L2 distance is exactly 3 whatever the field is.
    """
    ctx = _ctx((8, 8))
    field = _wave((8, 8), mode=1) + 0.4 * _wave((8, 8), mode=3)
    assert spectrum_l2(field, 2.0 * field, ctx=ctx) == pytest.approx(3.0)


def test_a_constant_offset_is_invisible():
    """The spatial mean is removed before transforming, so k = 0 carries no energy.

    Stated in the card's Definition, and load-bearing on this data: density is 1.0 +/-
    1.8e-4, so a spectrum that kept the mean would be comparing two means.
    """
    ctx = _ctx((8, 8))
    field = _wave((8, 8), mode=2)
    assert spectrum_l2(field, field + 1000.0, ctx=ctx) == pytest.approx(0.0, abs=1e-12)


def test_energy_lands_in_the_shell_the_mode_belongs_to():
    """A single mode puts all of its energy in exactly one shell.

    A mode-2 wave along x has |k| = 2 in integer wavenumber units, so every other shell
    must be empty. This pins the binning, which is imported from the calibration rather
    than defined here, and would catch that import silently changing meaning.
    """
    ctx = _ctx((8, 8))
    spectrum = radial_energy_spectrum(_wave((8, 8), mode=2), ctx)
    nonzero = np.flatnonzero(spectrum > 1e-9 * spectrum.max())
    assert len(nonzero) == 1, f"expected one populated shell, got {nonzero}"


def test_a_uniform_reference_is_nan_rather_than_a_number():
    """No fluctuation energy means no scale to divide by, so the metric declines to answer."""
    ctx = _ctx((8, 8))
    assert np.isnan(spectrum_l2(np.full((1, 8, 8), 3.0), _wave((8, 8), mode=1), ctx=ctx))
