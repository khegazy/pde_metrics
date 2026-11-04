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
distribution, energy cascade and intermittency across scales" -- and, as turbulence does,
report the flatness of the longitudinal velocity increments against separation. So for velocity
the increments read are the longitudinal ones (:func:`increment_samples`), and the curve over
octave separations is stored beside the number, with the transverse curve as a second companion.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import FieldContext
from fmeval.data.base import FIELDS
from metrics.registry import companion, metric

#: Increment separation, in cells, of the registered number. Fixed here and never exposed as
#: an option.
#:
#: One cell is the smallest separation the analysis grid resolves and therefore the
#: scale at which intermittency is strongest, which is where an over-smoothed prediction
#: separates most clearly from the reference. It is a constant rather than a configurable
#: severity for the same reason detector thresholds in this repository are fixed once: a
#: separation chosen per model would let a model be tuned to the scale that flatters it.
#: It also means the value is tied to the analysis-grid resolution, which the card says.
#: The other separations are read on the curve companions, at the octaves of
#: :func:`octave_separations`, whose first entry is this one.
SEPARATION_CELLS = 1


def increments(x: NDArray[np.floating], axis: int,
               separation: int = SEPARATION_CELLS) -> NDArray[np.floating]:
    """Increments of ``x`` along one spatial ``axis`` at ``separation`` cells, with periodic wrap.

    The single definition of an increment in this repository. ``increment_w1`` imports it
    rather than restating it, so the two metrics cannot come to disagree about what a
    separation of one cell means or about how the domain edge is handled.

    Args:
        x: Array whose ``axis`` is spatial and periodic.
        axis: Which axis to difference along, as a negative index.
        separation: The separation in cells; one cell, this metric's, by default.

    Returns:
        An array the same shape as ``x``: entry ``n`` is ``x[n + separation] - x[n]`` along
        ``axis``, wrapping around at the end.
    """
    return np.roll(x, -separation, axis=axis) - x


def vector_field(field: str) -> bool:
    """Whether ``field`` is a vector whose channel ``i`` is its component along spatial axis
    ``i`` (``channels == "n_spatial"`` in :data:`fmeval.data.base.FIELDS`: velocity), so that its
    increments have an orientation, longitudinal or transverse, relative to their separation.

    Raises:
        KeyError: If ``field`` is not a canonical field name.
    """
    return FIELDS[field].channels == "n_spatial"


def increment_samples(x: NDArray[np.floating], field: str,
                      separation: int = SEPARATION_CELLS, *,
                      transverse: bool = False) -> list[NDArray[np.floating]]:
    """The increments every increment metric reads, one array per (channel, axis) pair.

    For a vector field (:func:`vector_field`) the longitudinal increments, the component
    parallel to the separation (channel ``i`` along axis ``i``): the standard object of
    structure-function theory (Boffetta & Ecke 2012, Annu. Rev. Fluid Mech. 44, 427, Eq. (4),
    p. 430, which splits the structure function into longitudinal and transverse parts; the
    increment of Granero-Belinchon & Cabeza Gallucci 2024, Eq. (1), is of the longitudinal
    velocity). With ``transverse=True``, the component perpendicular to it (channel ``i`` along
    every axis ``j != i``), channel by channel. For any other field every channel along every
    axis, in channel-then-axis order; such a field has no transverse increments.

    Args:
        x: The field, shape ``(C, *spatial)`` on a periodic grid.
        field: Its canonical name, which says whether it is a vector.
        separation: The separation in cells.
        transverse: Read the transverse increments of a vector field instead of the longitudinal.

    Returns:
        The increment arrays, each of shape ``(*spatial)``; an empty list for the transverse
        increments of a one-dimensional vector field.

    Raises:
        ValueError: If a vector field's channels do not match its spatial axes, or the
            transverse increments of a field that is not a vector are asked for.
    """
    n_spatial = x.ndim - 1
    vector = vector_field(field)
    if vector and x.shape[0] != n_spatial:
        raise ValueError(f"{field} on {n_spatial} spatial axes needs {n_spatial} channels, one "
                         f"per axis; got shape {x.shape}")
    if transverse and not vector:
        raise ValueError(f"{field} is not a vector field, so it has no transverse increments")
    pairs = ([(c, a) for c in range(x.shape[0]) for a in range(-n_spatial, 0)] if not vector
             else [(c, a) for c in range(n_spatial) for a in range(-n_spatial, 0)
                   if (a + n_spatial != c) == transverse])
    return [increments(x[c], a, separation) for c, a in pairs]


def octave_separations(spatial_shape: tuple[int, ...]) -> NDArray[np.int64]:
    """The separations the curve companions read: 1, 2, 4, ... cells up to half the smallest
    side of the grid, the largest at which a periodic increment is not its own mirror image.

    Raises:
        ValueError: If an axis has fewer than two cells: there is no separation to read, and a
            mean over none would be NaN rather than a number.
    """
    largest = min(spatial_shape) // 2
    if largest < 1:
        raise ValueError(f"increment separations need at least two cells along every spatial "
                         f"axis; the spatial shape is {tuple(spatial_shape)}")
    return 2 ** np.arange(int(np.log2(largest)) + 1)


def flatness(samples: list[NDArray[np.floating]]) -> float:
    """Mean over ``samples`` of each one's flatness, ``<d^4> / <d^2>^2``: Granero-Belinchon &
    Cabeza Gallucci (2024), Eq. (5).

    A sample whose increments vanish identically has no distribution to have a shape, and
    scoring it 3 or 0 would both be inventions: it is skipped, as is any non-finite flatness.
    NaN if nothing is left, that is if the field is constant along every axis read.
    """
    values = []
    for d in samples:
        second = float(np.mean(d**2))
        if second != 0.0:
            values.append(float(np.mean(d**4) / second**2))
    finite = [v for v in values if np.isfinite(v)]
    if not finite:
        return float("nan")
    return float(np.mean(finite))


@metric(
    name="increment_flatness",
    arity="single",
    fields=("*",),
    differentiable=True,
    cost="cheap",
    higher_is_better=False,   # no direction of its own: the drift from the reference is
                              # what is read, in either direction
    symmetric=False,
    units="dimensionless",
    # Flatness is a statistic of distribution *shape*, and shape has no reason to move
    # one way under smoothing. Measured on frame 5000 of kinet_re5e4 (gaussian_filter, wrap),
    # blurring at sigma = 0, 0.5, 1, 2, 4 gives density 16.47 / 16.55 / 16.38 / 15.53 / 12.99
    # and vorticity 12.71 / 12.34 / 10.14 / 7.59 / 16.15, neither monotone, vorticity turning
    # sharply back up at the heaviest blur. Velocity's longitudinal value falls steadily,
    # 7.72 / 7.40 / 6.83 / 6.41 / 5.51, while its transverse value rises, 8.96 / 9.02 / 9.38 /
    # 10.55 / 11.20, so the two orientations pooled wander (8.34 / 8.21 / 8.10 / 8.48 / 8.36).
    # CLAUDE.md's acceptance protocol treats non-monotone metrics as dangerous for model
    # selection, so this is a property a reader has to be told about rather than one to
    # engineer away; issues/036 carries the argument.
    monotone_under_smoothing=False,
    requires_periodic=True,  # increments taken with np.roll
)
def increment_flatness(x: NDArray[np.floating], *, ctx: FieldContext) -> float:
    """Flatness of one-cell increments, longitudinal for velocity, averaged over the
    (channel, axis) pairs read: the first point of :func:`increment_flatness_curve`.

    Granero-Belinchon and Cabeza Gallucci (2024), Mach. Learn.: Sci. Technol. 5(2),
    025032, DOI 10.1088/2632-2153/ad43b3, Sect. 2.1, Eq. (5): the flatness of the
    longitudinal velocity increments, which they report against separation (Fig. 6c) and
    train their model against as "the variance, skewness and flatness of the increments of
    the generated field that retrieve respectively the turbulent energy distribution, energy
    cascade and intermittency across scales". Flatness is the third of those and the one that
    measures intermittency; this metric is that criterion used as a diagnostic rather than a
    loss, at the smallest separation.

    The average is taken over *flatness values*, one per (channel, axis) pair of
    :func:`increment_samples`, rather than by pooling every increment into one sample.
    Pooling would be wrong in a way that is easy to miss: increments along different axes of
    an anisotropic field have different variances, and a mixture of Gaussians with unequal
    variances is leptokurtic, so a perfectly Gaussian anisotropic field would score above 3
    and the one number this metric promises to mean something at -- exactly 3 for a Gaussian
    -- would stop being true. Averaging the per-axis flatnesses keeps that anchor exact.

    Args:
        x: The field to characterise, shape ``(C, *spatial)`` on the analysis grid.
        ctx: The pipeline's context: its field name says whether the increments are
            longitudinal.

    Returns:
        The mean flatness. 3 for a Gaussian field, below 3 for a field whose increments
        are more uniformly spread than a Gaussian's, above 3 for an intermittent one.
        Dimensionless and unbounded above. NaN if no pair read has a non-zero increment,
        that is if the field is constant.
    """
    return flatness(increment_samples(x, ctx.field))


@companion(of="increment_flatness", name="by_separation", kind="curve",
           coordinate=("separation", "cells"))
def increment_flatness_curve(x: NDArray[np.floating], *,
                             ctx: FieldContext) -> tuple[NDArray, NDArray]:
    """(separations, F(l)): the flatness at each octave separation, longitudinal for velocity,
    the curve its field draws against separation on logarithmic axes (Granero-Belinchon &
    Cabeza Gallucci 2024, Fig. 6c). Its first point is the registered number, which is
    computed on its own, so that the metric's cost is that of the one separation it reports."""
    separations = octave_separations(x.shape[1:])
    return separations, np.array([flatness(increment_samples(x, ctx.field, int(l)))
                                  for l in separations])


@companion(of="increment_flatness", name="transverse", kind="curve",
           coordinate=("separation", "cells"))
def increment_flatness_transverse(x: NDArray[np.floating], *,
                                  ctx: FieldContext) -> tuple[NDArray, NDArray]:
    """(separations, F_T(l)): the flatness of the transverse increments of a vector field at
    each octave separation, the second half of Boffetta & Ecke (2012), Eq. (4). Empty for a
    field with no transverse increments (a scalar, or a one-dimensional vector)."""
    if not vector_field(ctx.field) or x.ndim < 3:
        return np.array([], dtype=np.int64), np.array([])
    separations = octave_separations(x.shape[1:])
    return separations, np.array([flatness(increment_samples(x, ctx.field, int(l),
                                                             transverse=True))
                                  for l in separations])
