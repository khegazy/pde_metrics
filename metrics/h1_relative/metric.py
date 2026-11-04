"""Relative H^1 error as the neural-operator library computes it: the error's value and first
derivatives over the reference's, per channel, summed over channels.

The neural-operator community trains and evaluates with this number. It is inhomogeneous, so a
uniform offset counts through the zeroth-order term, and relative, so it is dimensionless and
reads 1 for a prediction of zero. Its derivatives are centred differences on a domain of unit
length per axis, whatever the physical size of the grid (``judgements/017``).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from metrics.registry import metric

#: Added to the root of the reference's sum before dividing: ``H1Loss(eps=1e-8)``, the
#: library's default (neuraloperator ``neuralop/losses/data_losses.py``, ``H1Loss.__init__``).
#: In the units of the field times the root of a cell count, since the sums are not averaged.
EPSILON: float = 1e-8


@metric(
    name="h1_relative",
    arity="pairwise",
    fields=("*",),
    differentiable=True,
    cost="cheap",
    higher_is_better=False,
    symmetric=False,         # the reference's own H^1 norm is the denominator
    units="dimensionless",
    requires_periodic=True,  # centred differences wrap around every axis (np.roll)
)
def h1_relative(
    reference: NDArray[np.floating],
    candidate: NDArray[np.floating],
) -> float:
    """Sum over channels of ``||e||_{H^1} / (||y||_{H^1} + eps)``, ``e = candidate - reference``.

    Computed exactly as ``H1Loss.rel`` with the library's defaults computes it
    (neuraloperator, ``neuralop/losses/data_losses.py`` at commit 0c10234; the training
    scripts ``scripts/train_navier_stokes.py`` and ``scripts/train_darcy.py`` build it as
    ``H1Loss(d=2)``), with ``y`` the reference:

    1. For each channel, sum over cells the squares of the field and of its first derivative
       along every axis (``compute_terms``; inhomogeneous, the zeroth-order term included).
    2. Derivatives are periodic centred differences ``(f[i+1] - f[i-1]) / (2 h_j)``
       (``neuralop/losses/differentiation.py``, ``FiniteDiff``, periodic branch) with
       ``h_j = measure / N_j`` and the default ``measure = 1.0`` (``uniform_quadrature``): the
       domain is taken as one unit long on every axis.
    3. The ratio is ``sqrt(error sum) / (sqrt(reference sum) + 1e-8)`` per channel
       (``rel``), and the channels are summed (``reduction="sum"``, the default; the
       library's ``Trainer.evaluate`` divides by the number of samples only, so one frame's
       value is this sum).

    Args:
        reference: The trusted field, shape ``(C, *spatial)`` on the analysis grid; the
            library's target ``y``.
        candidate: The field being scored, same shape; the library's ``y_pred``.

    Returns:
        The relative H^1 error summed over channels: zero for identical fields, about one
        per channel for a prediction of zero.

    Raises:
        ValueError: If the shapes differ.
    """
    if reference.shape != candidate.shape:
        raise ValueError(
            f"h1_relative needs matching shapes, got {reference.shape} and {candidate.shape}")
    spatial_axes = tuple(range(1, reference.ndim))

    def h1_squared(x: NDArray[np.floating]) -> NDArray[np.floating]:
        """Per channel: sum over cells of ``x^2`` plus every centred first difference squared,
        with ``h_j = 1 / N_j`` so ``1 / (2 h_j) = N_j / 2``."""
        total = (x**2).sum(axis=spatial_axes)
        for axis in spatial_axes:
            step = np.roll(x, -1, axis=axis) - np.roll(x, 1, axis=axis)
            derivative = step * (x.shape[axis] / 2.0)
            total = total + (derivative**2).sum(axis=spatial_axes)
        return total

    reference = np.asarray(reference, dtype=np.float64)
    error = np.asarray(candidate, dtype=np.float64) - reference
    return float(np.sum(np.sqrt(h1_squared(error)) / (np.sqrt(h1_squared(reference)) + EPSILON)))
