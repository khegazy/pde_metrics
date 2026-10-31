"""The `highpass_ideal` degradation.

See ``card.md`` for what this stands in for, how its severity is scaled, and where it
is not a fair imitation of the failure it models.
"""

from __future__ import annotations

import numpy as np

from fmeval.wavenumbers import wavenumber_magnitude

from .._shared.filters import _apply_filter
from ..registry import degradation


@degradation(
    family="spectral",
    severity_name="energy removed",
    severity_units="fraction",
    severity_direction="increasing",
    calibration="energy_below",
    preserves=("spatial_mean",),
)
def highpass_ideal(x: np.ndarray, severity: float, *, ctx) -> np.ndarray:
    """Sharp high-pass: zero every mode with |k| < cutoff, keeping the spatial mean.

    Removes the energy-containing large scales. Not a realistic surrogate failure, but a
    direct test of whether a metric registers large-scale structure at all.

    **The k=0 mode is preserved deliberately.** Deleting it removes the spatial mean, which
    for a field like density (1.0, fluctuating by a few thousandths of it) is a change two to
    three orders of magnitude larger than the whole fluctuation the cutoff acts on. Measured
    with k=0 deleted: every severity level gives an identical damage of 2.7e7 (against the
    translation anchor), so the axis carries no ordering at all and its rank correlation
    collapses to 0.10. Keeping the mean makes the operator measure what it is named for --
    removal of large-scale structure -- and gives a monotone ladder on every field.
    """
    k = wavenumber_magnitude(ctx.grid.shape)
    return _apply_filter(x, (k >= severity).astype(float), keep_mean=True)
