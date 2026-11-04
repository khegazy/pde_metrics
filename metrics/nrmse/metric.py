"""Normalised root mean squared error as PDEBench defines it: each channel's RMSE over the RMS of
the reference channel, averaged over channels.

The denominator is the raw root-mean-square of the reference, with no mean removed. On a field
whose mean is much larger than its fluctuation the value is therefore small whatever the error
in the fluctuation; ``vrmse`` divides by the fluctuation instead.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from ..mse.metric import channel_mse
from ..registry import metric


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
def nrmse(reference: NDArray[np.floating], candidate: NDArray[np.floating]) -> float:
    """Each channel's RMSE divided by the RMS of that channel of the reference, averaged.

    PDEBench's nRMSE, ``||u_pred - u_true||_2 / ||u_true||_2`` (Takamoto et al. 2022, NeurIPS 35
    Datasets and Benchmarks, App. B, the unnumbered display equation), computed as its code
    computes it: for each sample, channel and time step the RMSE over space divided by
    ``sqrt(mean(target ** 2))`` over space, with no small constant added, then the mean over
    samples, channels and time steps (``pdebench/models/metrics.py``, ``metric_func``,
    ``err_nRMSE``). The harness scores one frame at a time, so the mean over channels is the
    reduction left.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid. Sets the
            scale of each channel.
        candidate: The field being scored, same shape and grid.

    Returns:
        The mean over channels of RMSE over the reference's RMS, dimensionless. NaN if any
        channel of the reference is zero in every cell, where PDEBench's division has no value.

    Raises:
        ValueError: If the shapes differ.
    """
    norm = np.sqrt(np.mean(reference.reshape(reference.shape[0], -1) ** 2, axis=1))
    if np.any(norm == 0.0):
        return float("nan")
    return float(np.mean(np.sqrt(channel_mse(reference, candidate)) / norm))
