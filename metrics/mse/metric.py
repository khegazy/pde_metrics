"""Mean squared error over all channels and cells.

The pointwise L2 control: the metric that the position-tolerant candidates in this
repository exist to be compared against. It is here because a suite in which L2 looks good
everywhere is a broken suite, not because it is a good metric for displaced sharp features.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from metrics.registry import companion, metric


@metric(
    name="mse",
    arity="pairwise",
    fields=("*",),
    differentiable=True,
    cost="cheap",
    higher_is_better=False,
    symmetric=True,
    units="field^2",
    reduction="mean",
)
def mse(reference: NDArray[np.floating], candidate: NDArray[np.floating]) -> float:
    """Mean squared error over all channels and cells: the squared L2 norm divided by N.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.

    Returns:
        The mean of the squared difference. Zero for identical fields, unbounded above,
        in the square of the field's units.
    """
    d = reference - candidate
    return float(np.mean(d * d))


def channel_mse(
    reference: NDArray[np.floating], candidate: NDArray[np.floating]
) -> NDArray[np.floating]:
    """Mean squared error of each channel over its cells, one value per channel.

    This is The Well's MSE, which reduces over the spatial axes only and keeps one value per
    field (Ohana et al. 2024, NeurIPS 37 Datasets and Benchmarks, App. E.3; code
    ``the_well/benchmark/metrics/spatial.py``, ``MSE.eval``). Every channel has the same cells,
    so its mean over channels is :func:`mse`. The bundles that apply a nonlinearity per channel
    before averaging over channels -- ``rmse_channel_mean``, ``nrmse`` and ``vrmse`` -- start
    from it.

    Args:
        reference: The trusted field, shape ``(C, *spatial)``.
        candidate: The field being scored, same shape.

    Returns:
        An array of shape ``(C,)``.

    Raises:
        ValueError: If the shapes differ. Numpy would broadcast a one-channel field against a
            two-channel one and return a plausible value per channel.
    """
    if reference.shape != candidate.shape:
        raise ValueError(
            f"channel_mse needs matching shapes, got {reference.shape} and {candidate.shape}"
        )
    d = (reference - candidate).reshape(reference.shape[0], -1)
    return np.mean(d * d, axis=1)


@companion(of="mse")
def mse_map(
    reference: NDArray[np.floating], candidate: NDArray[np.floating]
) -> NDArray[np.floating]:
    """Per-cell squared error, summed over channels. Reduces to :func:`mse` by mean / C.

    Worth looking at rather than only reducing: for a sharp feature that is displaced
    rather than wrong, this map shows two separated lobes -- one where the feature should
    be and is not, one where it is and should not be. That picture is the double penalty,
    and it is the reason the rest of this repository exists.

    Args:
        reference: The trusted field, shape ``(C, *spatial)``.
        candidate: The field being scored, same shape.

    Returns:
        An array of shape ``(*spatial)``: the channel axis is summed away.
    """
    return ((reference - candidate) ** 2).sum(axis=0)
