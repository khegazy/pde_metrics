"""Normalised root mean squared error: the dimensionless pointwise control.

The one pointwise baseline whose value can be compared across fields, because it is
divided by a scale taken from the reference rather than left in the field's units.
"""

from __future__ import annotations

import numpy as np

from fmeval.context import fluctuation_rms

from ..registry import metric
from ..rmse.metric import rmse


@metric(
    name="nrmse",
    arity="pairwise",
    fields=("*",),
    differentiable=True,
    cost="cheap",
    higher_is_better=False,
    symmetric=False,          # the reference sets the scale, so swapping the arguments changes it
    units="dimensionless",
)
def nrmse(reference: np.ndarray, candidate: np.ndarray) -> float:
    """RMSE normalised by the RMS of the reference *fluctuation*.

    The spatial mean is removed before normalising. The kinet weakly compressible data has
    density fluctuating by a few thousandths of its mean of 1.0, so normalising by the raw RMS
    (~1.0) would hide two to three orders of magnitude of relative error and make density and
    velocity incomparable on the same axis.

    Parameters
    ----------
    reference
        Reference field on the analysis grid, shape ``(C, *spatial)``. Sets the scale.
    candidate
        Candidate field, same shape.

    Returns
    -------
    float
        Dimensionless error, or NaN for a spatially uniform reference, where no
        fluctuation scale exists to divide by.
    """
    denom = fluctuation_rms(reference)
    if denom == 0.0:
        return float("nan")
    return rmse(reference, candidate) / denom
