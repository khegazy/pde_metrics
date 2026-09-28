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

What the canary cannot yet do is *report* that. Its damage column is normalised by the
unrelated-field anchor, and that anchor is built from translations, which this metric cannot
see either, so the anchor is also ~1e-16 and every damage score is withheld as NaN. The raw
value is the evidence; the normalised column is empty. ``issues/037`` records this for the
whole position-blind family.

The two-point correlation is the Fourier transform of this, so the two carry the
same information and running both is not two independent checks.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import MetricContext
from metrics.registry import metric


def radial_energy_spectrum(
    field: NDArray[np.floating], ctx: MetricContext
) -> NDArray[np.floating]:
    """Fluctuation energy of ``field`` summed into unit-width shells, ``rint(|k|)``.

    The magnitude ``|k|`` is the repository's one definition, from ``fmeval/wavenumbers.py``;
    only the grouping is local. That module exists because the filters and the calibration
    once disagreed about which side of a cutoff the diagonal modes fell on, and a filter
    that was asked to remove 30% of density's energy removed 99.997%. The hazard is two
    operators disagreeing about the *same* cutoff. A metric that groups the shared
    magnitudes into shells does not create it, so the shells here can follow the
    turbulence literature without reintroducing it.

    Shells were first taken as the calibration's exact distinct magnitudes. That gives 5924
    shells of a median 8 modes on 256 x 256, against 182 here, which makes the comparison
    close to a mode-by-mode one: two realisations of the same flow would differ through
    the scatter of individual mode amplitudes rather than through their spectra.
    ``issues/038`` records the measurement and the decision to switch.

    Every mode is kept, including the corners beyond ``|k| = N/2``, whose shells are only
    partly populated by the square grid. Nothing is dropped, so the total energy in the
    spectrum is the field's fluctuation energy exactly.

    The spatial mean is removed before transforming, so the k = 0 shell carries no energy.
    On this data that is not a detail: density is 1.0 +/- 1.8e-4, so its mean is four orders
    of magnitude larger than every fluctuation, and a spectrum including it would compare
    two means and ignore the flow.

    Args:
        field: Array of shape ``(C, *spatial)`` on the analysis grid.
        ctx: Supplies the analysis grid, which sets the shells.

    Returns:
        1-D array of energy per shell, summed over channels, ascending in ``|k|``.
    """
    from fmeval.wavenumbers import wavenumber_magnitude

    shell = np.rint(wavenumber_magnitude(tuple(ctx.grid.shape))).astype(np.int64)
    spatial = tuple(range(1, field.ndim))
    fluct = field - field.mean(axis=spatial, keepdims=True)
    power = sum(np.abs(np.fft.fftn(channel)) ** 2 for channel in fluct)
    return np.bincount(shell.ravel(), power.ravel(), minlength=int(shell.max()) + 1)


@metric(
    name="spectrum_l2",
    arity="pairwise",
    fields=("*",),
    returns="scalar",
    differentiable=True,
    cost="cheap",
    higher_is_better=False,
    symmetric=False,          # the reference sets the scale, so swapping the arguments
                              # changes the value, exactly as for nrmse
    units="dimensionless",
)
def spectrum_l2(
    reference: NDArray[np.floating],
    candidate: NDArray[np.floating],
    *,
    ctx: MetricContext,
) -> float:
    """Relative L2 distance between two radial energy spectra.

    The radial energy spectrum is standard; see Pope (2000), "Turbulent Flows", Cambridge
    University Press, DOI 10.1017/CBO9780511840531, Chapter 6, for the definition and for
    what it does and does not determine about a field. The metrics tracker's energy-spectrum
    entry records the reason it is a baseline rather than a candidate: the spectrum and the
    two-point correlation are Fourier transforms of one another and both discard all phase, so
    matching a spectrum is a weak constraint.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid. Sets
            the normalising scale.
        candidate: The field being scored, same shape and grid.
        ctx: Supplies the analysis grid.

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
    e_ref = radial_energy_spectrum(reference, ctx)
    e_cand = radial_energy_spectrum(candidate, ctx)
    denom = float(np.sqrt((e_ref**2).sum()))
    if denom == 0.0:
        return float("nan")
    return float(np.sqrt(((e_ref - e_cand) ** 2).sum()) / denom)
