"""The `scale_dilatational` degradation: a velocity whose compressive part is too weak or too
strong while its vortical part is exact.

See ``card.md`` for what this stands in for and where it misleads.
"""

from __future__ import annotations

import numpy as np

from fmeval.context import FieldContext
from fmeval.derived import helmholtz_split

from ..registry import degradation


@degradation(
    family="spectral",
    severity_name="fraction of the dilatational part removed or added",
    severity_units="",
    severity_direction="increasing",
    fields=("velocity",),
    preserves=("spatial_mean",),
)
def scale_dilatational(x: np.ndarray, severity: float, *, ctx: FieldContext,
                       amplify: bool = False) -> np.ndarray:
    """Multiply the velocity's dilatational part by ``1 - severity``, or ``1 + severity`` with
    ``amplify``, keeping its solenoidal part and mean exactly.

    The split is the Fourier projection of :func:`fmeval.derived.helmholtz_split`, so the
    result is ``u + delta u_d`` with ``delta = -severity`` or ``+severity``: zero severity
    returns the input bit for bit, and the curl is unchanged.

    Raises:
        ValueError: On a negative severity, or one above 1 when attenuating, which would flip
            the part's sign rather than remove more of it.
    """
    if severity < 0 or (severity > 1 and not amplify):
        raise ValueError(f"scale_dilatational severity must lie in [0, 1], or be >= 0 with "
                         f"amplify; got {severity}")
    _, dilatational = helmholtz_split(x, ctx.grid)
    return x + (severity if amplify else -severity) * dilatational
