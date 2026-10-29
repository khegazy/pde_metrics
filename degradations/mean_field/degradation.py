"""The `mean_field` degradation.

See ``card.md`` for what this stands in for, what it means as the damage anchor, and where it
is not a fair imitation of anything.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from degradations.registry import degradation
from fmeval.context import FieldContext


@degradation(
    name="mean_field",
    family="smoothing",
    severity_name="n/a",
    severity_units="",
    severity_direction="increasing",
    ordinal=False,   # a reference measurement, not a severity level on a monotone axis
    preserves=("spatial_mean",),
    zero_is_identity=False,
)
def mean_field(
    field: NDArray[np.floating],
    severity: float,
    *,
    ctx: FieldContext,
) -> NDArray[np.floating]:
    """Replace every cell with the field's spatial mean, channel by channel.

    The climatological reference forecast of forecast verification (Murphy 1988, Mon. Wea.
    Rev. 116(12), 2417-2424): the prediction that knows the field's mean and nothing else. It
    is the default damage anchor (``analysis.anchor``), so damage 1 reads "as far from the
    truth as the field's own mean". For the mean squared error that anchor is exactly the
    reference's spatial variance.

    The mean is taken over this frame's own cells. For a statistically homogeneous flow that
    is its climatology; it needs no other frame and no knowledge of the boundaries, because a
    mean over the domain does not depend on what lies outside it.

    Args:
        field: The field, shape ``(C, *spatial)``.
        severity: Ignored: there is one level.
        ctx: Supplies the spatial axes.

    Returns:
        A new array of the input's shape and dtype, constant over space in each channel.
    """
    return np.broadcast_to(field.mean(axis=ctx.spatial_axes, keepdims=True), field.shape).copy()
