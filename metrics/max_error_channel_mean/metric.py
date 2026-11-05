"""Maximum absolute error of each channel, averaged over channels: the max error of PDEBench.

The sibling of ``max_error``, which takes one maximum over every channel and cell. On a
one-channel field (density, vorticity) the two are the same number; on velocity they differ.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from ..max_error.metric import absolute_error
from ..registry import metric


@metric(
    name="max_error_channel_mean",
    arity="pairwise",
    fields=("*",),
    differentiable=True,      # piecewise linear, as max_error: a (sub)gradient at the one cell
                              # of each channel that attains its maximum
    cost="cheap",
    higher_is_better=False,
    symmetric=True,
    units="field",
)
def max_error_channel_mean(
    reference: NDArray[np.floating], candidate: NDArray[np.floating]
) -> float:
    """The largest absolute error of each channel over its cells, averaged over channels.

    PDEBench's max error: its ``metric_func`` takes the maximum of the absolute error over
    space for each sample, channel and time step, the maximum over the samples, and then the
    mean over channels and time steps (Takamoto et al. 2022, NeurIPS 35 Datasets and
    Benchmarks, Sect. 3.3 and App. B; code ``pdebench/models/metrics.py``, ``metric_func``,
    ``err_Max``). The harness scores one frame at a time, so the mean over channels is the
    reduction left. The Well's L-infinity error averaged over its fields is the same number
    (Ohana et al. 2024, App. E.3; ``LInfinity.eval``).

    No per-cell map is stored: a mean of per-channel maxima cannot be recovered from a map
    reduced over channels. ``max_error``'s map shows where the error lies.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.

    Returns:
        The mean over channels of each channel's largest ``|reference - candidate|``, in the
        field's units. Zero for identical fields, unbounded above.

    Raises:
        ValueError: If the shapes differ.
    """
    error = absolute_error(reference, candidate)
    return float(np.mean(error.reshape(error.shape[0], -1).max(axis=1)))
