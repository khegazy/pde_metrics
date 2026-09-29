"""Flatness (kurtosis) of one-cell increments: a one-number Gaussianity alarm.

A single-field metric. It characterises one field rather than comparing two, so the
pipeline evaluates it on the reference and on every degraded variant and the drift between
them is what is read -- the same shape as ``enstrophy``.

Flatness is exactly 3 for a Gaussian field and grows without bound as a distribution's
weight moves into its tails. Fully developed turbulence has increment flatness well above 3
and rising toward the small scales, which is the quantitative statement of intermittency:
the sharp, rare, spatially isolated structures that carry the tail. An over-smoothed
surrogate destroys those first, and its flatness falls toward 3 while a pointwise error
norm may barely move. That is the failure this metric exists to expose.

Granero-Belinchon and Cabeza Gallucci (2024) train and score a generative turbulence model
on exactly this family of statistics -- "the variance, skewness and flatness of the
increments of the generated field that retrieve respectively the turbulent energy
distribution, energy cascade and intermittency across scales".
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from metrics.registry import metric

#: Increment separation, in cells. Fixed here and never exposed as an option.
#:
#: One cell is the smallest separation the analysis grid resolves and therefore the
#: scale at which intermittency is strongest, which is where an over-smoothed prediction
#: separates most clearly from the reference. It is a constant rather than a configurable
#: severity for the same reason detector thresholds in this repository are fixed once: a
#: separation chosen per model would let a model be tuned to the scale that flatters it.
#: It also means the value is tied to the analysis-grid resolution, which the card says.
SEPARATION_CELLS = 1


def increments(x: NDArray[np.floating], axis: int) -> NDArray[np.floating]:
    """One-cell increments of ``x`` along one spatial ``axis``, with periodic wrap.

    The single definition of an increment in this repository. ``increment_w1`` imports it
    rather than restating it, so the two metrics cannot come to disagree about what a
    separation of one cell means or about how the domain edge is handled.

    Args:
        x: Array whose ``axis`` is spatial and periodic.
        axis: Which axis to difference along, as a negative index.

    Returns:
        An array the same shape as ``x``: entry ``n`` is ``x[n + 1] - x[n]`` along
        ``axis``, and the last entry wraps around to the first.
    """
    return np.roll(x, -SEPARATION_CELLS, axis=axis) - x


def axis_flatness(x: NDArray[np.floating], axis: int) -> float:
    """Flatness of the one-cell increments of ``x`` along one spatial ``axis``.

    Args:
        x: One channel of a field, shape ``(*spatial)``, periodic along ``axis``.
        axis: Which spatial axis to take the increment along, as a negative index.

    Returns:
        ``<d^4> / <d^2>^2`` for the increment ``d``, or NaN when the increments vanish
        identically -- a field constant along this axis has no increment distribution to
        have a shape, and returning 3 or 0 there would both be inventions.
    """
    d = increments(x, axis)
    second = float(np.mean(d**2))
    if second == 0.0:
        return float("nan")
    return float(np.mean(d**4) / second**2)


@metric(
    name="increment_flatness",
    arity="single",
    fields=("*",),
    returns="scalar",
    differentiable=True,
    cost="cheap",
    higher_is_better=False,   # no direction of its own: the drift from the reference is
                              # what is read, in either direction
    symmetric=False,
    units="dimensionless",
    # Flatness is a statistic of distribution *shape*, and shape has no reason to move
    # one way under smoothing. Measured on frame 5000 of kinet_re5e4, blurring at
    # sigma = 0, 0.5, 1, 2, 4 gives density 16.47 / 16.55 / 16.38 / 15.53 / 12.99,
    # velocity 8.34 / 8.21 / 8.10 / 8.48 / 8.36 and vorticity 12.71 / 12.34 / 10.14 /
    # 7.59 / 16.15 -- none of them monotone, and vorticity turns sharply back up at the
    # heaviest blur. CLAUDE.md's acceptance protocol treats non-monotone metrics as
    # dangerous for model selection, so this is a property a reader has to be told about
    # rather than one to engineer away; issues/036 carries the argument.
    monotone_under_smoothing=False,
)
def increment_flatness(x: NDArray[np.floating]) -> float:
    """Flatness of one-cell increments, averaged over spatial axes and channels.

    Granero-Belinchon and Cabeza Gallucci (2024), Mach. Learn.: Sci. Technol. 5(2),
    025032, DOI 10.1088/2632-2153/ad43b3: the model there is trained against "the
    variance, skewness and flatness of the increments of the generated field that retrieve
    respectively the turbulent energy distribution, energy cascade and intermittency
    across scales". Flatness is the third of those and the one that measures
    intermittency; this metric is that criterion used as a diagnostic rather than a loss.

    The average is taken over *flatness values*, one per (channel, axis), rather than by
    pooling every increment into one sample. Pooling would be wrong in a way that is easy
    to miss: increments along different axes of an anisotropic field have different
    variances, and a mixture of Gaussians with unequal variances is leptokurtic, so a
    perfectly Gaussian anisotropic field would score above 3 and the one number this
    metric promises to mean something at -- exactly 3 for a Gaussian -- would stop being
    true. Averaging the per-axis flatnesses keeps that anchor exact.

    Args:
        x: The field to characterise, shape ``(C, *spatial)`` on the analysis grid.

    Returns:
        The mean flatness. 3 for a Gaussian field, below 3 for a field whose increments
        are more uniformly spread than a Gaussian's, above 3 for an intermittent one.
        Dimensionless and unbounded above. NaN if no axis of any channel has a non-zero
        increment, that is if the field is constant.
    """
    n_spatial = x.ndim - 1
    values = [
        axis_flatness(channel, axis=axis)
        for channel in x
        for axis in range(-n_spatial, 0)
    ]
    finite = [v for v in values if np.isfinite(v)]
    if not finite:
        return float("nan")
    return float(np.mean(finite))
