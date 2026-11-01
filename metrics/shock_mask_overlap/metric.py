"""Dice coefficient of the shocks found in the reference and in the candidate pressure.

The detector is shared code: :func:`metrics.shock_set_distance.metric.shock_mask` flags a
cell when the pressure ratio across it reaches that of a Mach 1.3 shock (Schaal & Springel
2015), at the thresholds fixed there. This metric asks how many of the flagged cells the two
fields share, the overlap score of image segmentation, where ``shock_set_distance`` asks how
far apart the flagged cells lie. A shock moved by at least its own detected width shares no
cell and scores 0, however far it moved.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fmeval.context import FieldContext
from metrics.registry import metric
from metrics.shock_set_distance.metric import shock_mask

#: ``ctx.cache`` key of the reference's shock masks, one per channel, computed once per frame.
REFERENCE_MASKS = "shock_mask_overlap/reference_masks"


@metric(
    name="shock_mask_overlap",
    arity="pairwise",
    fields=("pressure",),
    differentiable=False,           # a thresholded detector: the masks change in jumps
    cost="cheap",
    higher_is_better=True,
    symmetric=True,
    monotone_under_smoothing=False,  # a thresholded set changes in jumps, with ties
    units="dimensionless",
    requires_periodic=False,
)
def shock_mask_overlap(reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
                       ctx: FieldContext) -> float:
    """Dice coefficient between the shocked cells of two pressure fields.

    With ``A`` and ``B`` the cells :func:`shock_mask` flags in the reference and in the
    candidate, the Dice coefficient of Taha & Hanbury (2015), BMC Med. Imaging 15, 29,
    Eq. (6)::

        DICE(A, B) = 2 |A n B| / (|A| + |B|)

    the number of shared cells over the mean size of the two sets, from 0 (no shared cell)
    to 1 (identical sets). It equals the F1 score of the candidate's flags against the
    reference's (Taha & Hanbury 2015, Table 1) and is a monotone function of the Jaccard
    index, ``JAC = DICE / (2 - DICE)`` (their Eq. 8), so the two rank any set of candidates
    alike. One empty set gives 0 from the formula. Two empty sets leave it 0/0; they score 1,
    because both fields agree there is no shock (convention mine, ``issues/120``). Channels,
    of which pressure has one, are averaged. A field that is NaN or infinite anywhere has no
    readable pressure ratio there, so NaN is returned, as ``shock_set_distance`` does.

    Args:
        reference: The trusted pressure, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The pressure being scored, same shape and grid.
        ctx: Caches the reference's shock masks for the frame.

    Returns:
        The Dice coefficient, dimensionless, in [0, 1]; NaN on a non-finite field.

    Raises:
        ValueError: If the shapes differ.
    """
    if reference.shape != candidate.shape:
        raise ValueError(f"shock_mask_overlap needs matching shapes, got {reference.shape} "
                         f"and {candidate.shape}")
    if not (np.isfinite(reference).all() and np.isfinite(candidate).all()):
        return float("nan")
    if REFERENCE_MASKS not in ctx.cache:
        ctx.cache[REFERENCE_MASKS] = [shock_mask(channel) for channel in reference]
    values = []
    for a, channel in zip(ctx.cache[REFERENCE_MASKS], candidate):
        b = shock_mask(channel)
        flagged = int(a.sum() + b.sum())
        # Taha & Hanbury (2015) Eq. (6): 2 |A n B| / (|A| + |B|); 1 when both sets are empty
        # (convention mine, issues/120).
        values.append(2.0 * int((a & b).sum()) / flagged if flagged else 1.0)
    return float(np.mean(values))
