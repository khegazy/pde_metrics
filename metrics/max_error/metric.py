"""Maximum absolute error: the pointwise L-infinity control, the worst single cell.

The pointwise controls ``mae``, ``mse``, ``rmse`` and ``nrmse`` average the error over the
domain, so one badly wrong cell counts only in proportion to its share of the cells. The
maximum error reports that cell alone: a spurious spike, an overshoot beside a front, or the
first cell of a growing instability cannot be diluted out of it.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from metrics.registry import companion, metric


def _absolute_error(
    reference: NDArray[np.floating], candidate: NDArray[np.floating]
) -> NDArray[np.floating]:
    """``|reference - candidate|`` cell by cell, refusing shapes that differ.

    Both the metric and its map take their maximum from this array. Numpy would broadcast a
    one-channel field against a two-channel one, or a ``(X, 1)`` field against ``(X, Y)``, and
    return a plausible number; a maximum over such an array is meaningless, so it raises.

    Raises:
        ValueError: If the two shapes differ.
    """
    if reference.shape != candidate.shape:
        raise ValueError(
            f"max_error needs matching shapes, got {reference.shape} and {candidate.shape}"
        )
    return np.abs(reference - candidate)


@metric(
    name="max_error",
    arity="pairwise",
    fields=("*",),
    differentiable=True,      # piecewise linear: a gradient wherever one entry attains the
                              # maximum with nonzero error, a subgradient at ties and at zero
    cost="cheap",
    higher_is_better=False,
    symmetric=True,
    units="field",
    reduction="max",
)
def max_error(reference: NDArray[np.floating], candidate: NDArray[np.floating]) -> float:
    """Largest absolute difference over all channels and cells: the discrete L-infinity error.

    The discrete L-infinity norm of the error, the maximum over all mesh nodes of the
    absolute difference from the reference (Roy 2005, J. Comput. Phys. 205(1), 131-156,
    Sect. 2.5, Eq. 7). PDEBench reports this "max error" beside RMSE and nRMSE as the local
    worst case and a proxy for the stability of time-stepping (Takamoto et al. 2022,
    NeurIPS 35 Datasets and Benchmarks, 1596-1611, Sect. 3.3).

    Channels are pooled: the maximum runs over every (channel, cell) entry, as ``mae`` and
    ``mse`` pool channels into their means. This choice is the bundle's, not a source's;
    PDEBench's code instead averages the per-channel maxima, which differs only on a
    multi-channel field such as velocity.

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The field being scored, same shape and grid.

    Returns:
        The largest ``|reference - candidate|`` over every channel and cell, in the field's
        own units. Zero for identical fields, unbounded above. NaN if either field holds a NaN.

    Raises:
        ValueError: If the shapes differ, or if the fields have no cells.
    """
    # Roy (2005) Eq. 7: L_inf = max_n |f_n - f_exact,n|, here over channels and cells pooled.
    return float(_absolute_error(reference, candidate).max())


@companion(of="max_error")
def max_error_map(
    reference: NDArray[np.floating], candidate: NDArray[np.floating]
) -> NDArray[np.floating]:
    """Per-cell absolute error, the largest over channels. Reduces to :func:`max_error` by max.

    The map shows where the worst cell sits and how isolated it is: one bright cell is a
    local excursion, a ridge along a front is a displaced sharp feature.

    Args:
        reference: The trusted field, shape ``(C, *spatial)``.
        candidate: The field being scored, same shape.

    Returns:
        An array of shape ``(*spatial)``: the channel axis is reduced by its maximum, so that
        the maximum of the map is the metric (Roy 2005, Eq. 7, as in :func:`max_error`).
    """
    return _absolute_error(reference, candidate).max(axis=0)
