"""Variance-scaled root mean squared error as The Well defines it: each channel's RMSE over the
standard deviation of the reference channel, averaged over channels.

The denominator is the fluctuation of the reference about its own spatial mean, so predicting
that mean scores about one on every field, and a field whose mean is much larger than its
fluctuation, as density's is here, is compared on its fluctuation.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from ..mse.metric import channel_mse
from ..registry import metric

#: The Well's constant added to the reference's variance, in the square of the field's units
#: (Ohana et al. 2024, App. E.3, "epsilon = 10^-7"; ``spatial.py``, ``eps: float = 1e-7``).
EPSILON = 1e-7


@metric(
    name="vrmse",
    arity="pairwise",
    fields=("*",),
    differentiable=True,
    cost="cheap",
    higher_is_better=False,
    symmetric=False,          # the reference sets the scale, so swapping the arguments changes it
    units="dimensionless",
)
def vrmse(reference: NDArray[np.floating], candidate: NDArray[np.floating]) -> float:
    """Each channel's RMSE over the reference channel's standard deviation, averaged.

    The Well's VRMSE, ``(<|u - v|^2> / (<|u - u_bar|^2> + eps))^(1/2)`` with ``u`` the truth
    (Ohana et al. 2024, NeurIPS 37 Datasets and Benchmarks, App. E.3, the unnumbered display
    equation), computed as its code computes it: the spatial mean of the squared error over
    ``torch.std(y) ** 2 + eps`` for each channel, where ``torch.std`` divides by the cell count
    less one, then the square root (``the_well/benchmark/metrics/spatial.py``, ``VRMSE`` through
    ``NMSE`` with ``norm_mode="std"``). The Well reports one value per field and their mean over
    fields (``the_well/benchmark/trainer/training.py``, ``split_up_losses``, the ``full``
    entry); the mean over channels is that mean.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid. Sets the
            scale of each channel.
        candidate: The field being scored, same shape and grid.

    Returns:
        The mean over channels of the variance-scaled RMSE, dimensionless. Finite on every
        input: a uniform reference channel is divided by ``sqrt(EPSILON)``.

    Raises:
        ValueError: If the shapes differ.
    """
    variance = np.var(reference.reshape(reference.shape[0], -1), axis=1, ddof=1)
    return float(np.mean(np.sqrt(channel_mse(reference, candidate) / (variance + EPSILON))))
