"""Relative L2 distance between the radial energy spectra of two fields.

A deliberately *phase-blind* metric, included as a baseline rather than as a candidate. The
radial energy spectrum is a function of the amplitude of the Fourier coefficients alone, so
it says how a field's energy is distributed across scales and nothing whatsoever about where
that energy sits or how it is organised. Two fields with identical spectra can look nothing
alike.

That blindness is the reason to have it. ``AGENTS.md`` records that the Gaussian
impostor -- a field with the reference's exact amplitude spectrum and randomised phase --
"does not catch the L^p family ... The check is aimed at quantities that are functions of
|F(f)| alone -- an energy spectrum, a two-point correlation -- which score it *perfectly*. A
report where everything passes is not reassuring; it means nothing in the panel can be
caught by it yet." This metric is exactly such a quantity: on ``comparison_1790633480`` it
scored the impostor at about 1e-15, the same as the undegraded reference.

The damage column reports it: the anchor, the field's spatial mean, has no fluctuation
spectrum at all, so this metric's span is well defined and the impostor scores damage 0.000
on every field of ``comparison_1793657627``. The large-translation probe scores 0 too,
because a translation leaves the amplitude spectrum unchanged.

The two-point correlation is the Fourier transform of this, so the two carry the
same information and running both is not two independent checks.

The spectrum E(k) itself, at every shell, is the metric's curve companion, drawn on log-log
axes over the reference's as the turbulence literature draws it; the analysis reads it at the
octave shells (:data:`OCTAVES`).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import COMPANION_KEY, FieldContext, fluctuation
from fmeval.wavenumbers import wavenumber_magnitude
from metrics.registry import companion, metric

#: ``ctx.cache`` key of the reference's spectrum, computed once per frame.
REFERENCE_SPECTRUM = "spectrum_l2/reference_spectrum"

#: The octave shells the analysis reads the spectrum and the flux at, each as a metric of its own:
#: a handful, because each costs 2.3 to 3.0 s per field in the analysis (AGENTS.md section 3.3).
#: Those beyond a coarse grid's last shell are absent there (``Companion.unmatched_analysed``).
OCTAVES = (1, 2, 4, 8, 16, 32, 64, 128)


def radial_shells(shape: tuple[int, ...]) -> NDArray[np.int64]:
    """The unit-width shell ``rint(|k|)`` of every mode of a grid of ``shape``.

    The grouping `radial_energy_spectrum` bins with, and `spectral_energy_flux` filters with, so
    the two agree about which shell a diagonal mode belongs to. ``|k|`` is
    ``fmeval/wavenumbers.py``'s.
    """
    return np.rint(wavenumber_magnitude(shape)).astype(np.int64)


def radial_energy_spectrum(
    field: NDArray[np.floating], ctx: FieldContext,
    other: NDArray[np.floating] | None = None,
) -> NDArray[np.floating]:
    """Fluctuation energy of ``field`` summed into unit-width shells, ``rint(|k|)``.

    With ``other``, the same shells hold the real part of the cross-spectrum instead,
    ``Re[conj(F field) * F other]`` summed over channels: the co-spectrum of two fields of
    the same shape, which ``spectral_energy_flux`` bins its energy transfer with. Without
    it, the energy spectrum ``|F field|^2``.

    The magnitude ``|k|`` is the repository's one definition, from ``fmeval/wavenumbers.py``;
    only the grouping is local. One definition matters where two operators must agree about
    which side of the *same* cutoff a mode falls, as the filters and the calibration must. A
    metric that groups the shared magnitudes into shells does not create that hazard, so the
    shells here can follow the turbulence literature.

    The shells are unit-width rather than the calibration's exact distinct magnitudes. Those
    give 5924 shells of a median 8 modes on 256 x 256, against 182 here, which would make the
    comparison close to a mode-by-mode one: two realisations of the same flow would differ
    through the scatter of individual mode amplitudes rather than through their spectra.

    Every mode is kept, including the corners beyond ``|k| = N/2``, whose shells are only
    partly populated by the square grid. Nothing is dropped, so the total energy in the
    spectrum is the field's fluctuation energy exactly.

    The spatial mean is removed before transforming, so the k = 0 shell carries no energy.
    On this data that is not a detail: density fluctuates by a few thousandths of its mean of
    1.0, so its mean is two to three orders of magnitude larger than every fluctuation, and a
    spectrum including it would compare two means and ignore the flow.

    Args:
        field: Array of shape ``(C, *spatial)`` on the analysis grid.
        ctx: Supplies the analysis grid, which sets the shells.
        other: Optional second field of ``field``'s shape; its mean is removed too.

    Returns:
        1-D array of energy per shell, summed over channels, ascending in ``|k|``; the
        co-spectrum per shell when ``other`` is given.

    Raises:
        ValueError: If ``other`` does not have ``field``'s shape.
    """
    shell = radial_shells(tuple(ctx.grid.shape))
    if other is None:
        power = sum(np.abs(np.fft.fftn(channel)) ** 2 for channel in fluctuation(field))
    elif other.shape != field.shape:
        raise ValueError(f"a co-spectrum needs two fields of one shape, got {field.shape} "
                         f"and {other.shape}")
    else:
        power = sum(np.real(np.conj(np.fft.fftn(a)) * np.fft.fftn(b))
                    for a, b in zip(fluctuation(field), fluctuation(other), strict=True))
    return np.bincount(shell.ravel(), power.ravel(), minlength=int(shell.max()) + 1)


@metric(
    name="spectrum_l2",
    arity="pairwise",
    fields=("*",),
    differentiable=True,
    cost="cheap",
    higher_is_better=False,
    symmetric=False,          # the reference sets the scale, so swapping the arguments
                              # changes the value, exactly as for nrmse
    units="dimensionless",
    requires_periodic=True,  # an FFT energy spectrum
)
def spectrum_l2(
    reference: NDArray[np.floating],
    candidate: NDArray[np.floating],
    *,
    ctx: FieldContext,
) -> float:
    """Relative L2 distance between two radial energy spectra, over every shell from k = 1.

    The radial energy spectrum is standard (Pope 2000, "Turbulent Flows", Cambridge University
    Press, DOI 10.1017/CBO9780511840531, Chapter 6; Boffetta & Ecke 2012, Eq. (3)); the
    spectrum and the two-point correlation are Fourier transforms of one another and both
    discard all phase, so matching a spectrum is a weak constraint. The relative L2 over shells
    on linear values is this repository's summary, not a source's, and is dominated by the few
    most energetic shells (``issues/136``). The spectra are those of :func:`energy_spectrum`,
    the metric's companion: the candidate's arrives in ``ctx.cache[COMPANION_KEY]`` and the
    reference's is computed once per frame.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid. Sets
            the normalising scale.
        candidate: The field being scored, same shape and grid.
        ctx: Supplies the analysis grid and the cache.

    Returns:
        Dimensionless. Zero when the two spectra coincide, 1 when the candidate has no
        fluctuation energy at all, and unbounded above when it has more energy than the
        reference. NaN for a spatially uniform reference, which has no spectrum to divide
        by.
    """
    if reference.shape != candidate.shape:
        raise ValueError(
            f"spectrum_l2 needs matching shapes, got {reference.shape} and "
            f"{candidate.shape}"
        )
    _, e_cand = (ctx.cache[COMPANION_KEY] if COMPANION_KEY in ctx.cache
                 else energy_spectrum(candidate, ctx=ctx))
    if REFERENCE_SPECTRUM not in ctx.cache:
        ctx.cache[REFERENCE_SPECTRUM] = energy_spectrum(reference, ctx=ctx)[1]
    e_ref = ctx.cache[REFERENCE_SPECTRUM]
    denom = float(np.sqrt((e_ref**2).sum()))
    if denom == 0.0:
        return float("nan")
    return float(np.sqrt(((e_ref - e_cand) ** 2).sum()) / denom)


# Drawn as its field draws it: E(k) on log-log axes with the reference's overlaid (Boffetta &
# Ecke 2012, Annu. Rev. Fluid Mech. 44, Fig. 11a; Kochkov et al. 2021, PNAS 118, Fig. 2c).
@companion(of="spectrum_l2", kind="curve", coordinate=("wavenumber", "cycles per domain"),
           analysed=OCTAVES, scales=("log", "log"))
def energy_spectrum(x: NDArray[np.floating], *,
                    ctx: FieldContext) -> tuple[NDArray[np.int64], NDArray[np.floating]]:
    """(k, E(k)) of one field at every shell k = 1, 2, ... up to the grid's corner mode.

    ``E(k) = 1/2 sum_c sum_{rint|m| = k} |f_hat_m|^2`` with ``f_hat`` the transform divided by the
    number of cells ``M``, so that ``sum_k E(k) = <|f'|^2> / 2``, half the mean square of the
    fluctuation: for velocity the kinetic energy per unit mass, ``E = <u^2>/2 = int E(k) dk``
    of Boffetta & Ecke (2012), Annu. Rev. Fluid Mech. 44, Eq. (3), p. 430; for vorticity the
    enstrophy, ``int k^2 E(k) dk`` there. It is :func:`radial_energy_spectrum` divided by
    ``2 M^2``, a constant that cancels in the metric's ratio. Shell 0 is left out: the mean is
    removed, so it holds round-off only and cannot be drawn on a logarithmic axis.

    The shells beyond ``N/2`` lie in the corners of the grid, only partly inside it, so the
    curve falls there because the shells are incomplete, not because the field has less
    energy at those scales. They are kept because the metric sums every shell.

    Args:
        x: Array of shape ``(C, *spatial)`` on the analysis grid.
        ctx: Supplies the analysis grid, which sets the shells.

    Returns:
        The shells 1 to the largest ``rint(|k|)`` of the grid, in cycles across the domain, and
        ``E`` at each, in the field's units squared.
    """
    spectrum = radial_energy_spectrum(x, ctx) / (2.0 * x[0].size ** 2)
    return np.arange(1, spectrum.size), spectrum[1:]
