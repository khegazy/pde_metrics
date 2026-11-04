"""Root mean squared error of each channel, averaged over channels: RMSE as PDEBench reports it.

The sibling of ``rmse``, which pools the channels before the square root. On a one-channel
field (density, vorticity) the two are the same number; on velocity they differ.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from ..mse.metric import channel_mse
from ..registry import metric


@metric(
    name="rmse_channel_mean",
    arity="pairwise",
    fields=("*",),
    differentiable=True,
    cost="cheap",
    higher_is_better=False,
    symmetric=True,
    units="field",
)
def rmse_channel_mean(
    reference: NDArray[np.floating], candidate: NDArray[np.floating]
) -> float:
    """The root mean squared error of each channel over its cells, averaged over channels.

    PDEBench's RMSE: its ``metric_func`` takes the square root of the spatial mean of the
    squared error for each sample, channel and time step, averages over the samples, then over
    channels and time steps (Takamoto et al. 2022, NeurIPS 35 Datasets and Benchmarks, Sect. 3.3;
    code ``pdebench/models/metrics.py``, ``metric_func``, ``err_mean`` and ``err_RMSE``). The
    harness scores one frame at a time, so the average over channels is the reduction left.
    The Well's RMSE averaged over its fields is the same number (Ohana et al. 2024, App. E.3).

    No per-cell map is stored: a mean of per-channel square roots cannot be recovered from a
    map summed over channels. ``rmse``'s map is the squared error behind both.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.

    Returns:
        The mean over channels of each channel's RMSE, in the field's units. Zero for
        identical fields, unbounded above.

    Raises:
        ValueError: If the shapes differ.
    """
    return float(np.mean(np.sqrt(channel_mse(reference, candidate))))
