"""Average distance between the shocks found in the reference and in the candidate pressure.

A pointwise norm charges a shock that is right in strength but one cell out of place twice,
once where it should be and once where it is. This metric instead finds the shocks in each
field and measures how far apart the two sets of shocked cells lie, in units of length.

It is two steps, and the first is shared code. :func:`shock_mask` is the detector: a cell is
shocked when the pressure ratio across it reaches that of a Mach 1.3 shock (Schaal & Springel
2015). :func:`surface_distances` is the comparison: every shocked cell's distance to the
nearest shocked cell of the other field, from a Euclidean distance transform that never wraps
around the domain. The registered number pools those distances into one mean, the average
symmetric surface distance of image segmentation (Yeghiazaryan & Voiculescu 2018).
"""

from __future__ import annotations

import inspect

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import distance_transform_edt

from fmeval.context import FieldContext
from fmeval.data.analytic import SodShockTube
from metrics.registry import metric

#: The weakest shock the detector reports, as a Mach number. Schaal & Springel (2015), MNRAS
#: 446, 3992, Sect. 2.3.2, criterion (iii).
MACH_MIN: float = 1.3
#: The ratio of specific heats the Mach threshold is converted with. The metric is handed one
#: field and no equation of state, so it is fixed, and read from the one compressible dataset
#: that stores a pressure, the Sod reader's default, rather than restated here.
GAMMA: float = inspect.signature(SodShockTube).parameters["gamma"].default


def shock_mask(pressure: NDArray[np.floating], *, mach_min: float = MACH_MIN,
               gamma: float = GAMMA) -> NDArray[np.bool_]:
    """The cells of one pressure field that a shock of at least ``mach_min`` passes through.

    The pressure half of the shock-zone criterion (iii) of Schaal & Springel (2015), MNRAS
    446, 3992-4007, Sect. 2.3.2: a cell is shocked when the jump in log pressure between
    its two neighbours reaches that of a normal shock at ``mach_min``, whose pressure ratio
    is their Eq. (2), the Rankine-Hugoniot relation
    ``p2/p1 = 2 gamma M^2/(gamma + 1) - (gamma - 1)/(gamma + 1)``. The test is applied along
    every axis and a cell is shocked if any axis flags it; Schaal and Springel measure the
    jump along the shock direction instead, which needs the temperature gradient this
    metric is not given (choice mine). The velocity-divergence and temperature criteria (i)
    and (ii) need fields a single-field metric does not receive, so only (iii) is applied.

    The jump is tested as ``max(p_-, p_+) >= R min(p_-, p_+)``. Where a neighbour's pressure
    is zero or negative this always holds, so a non-positive pressure, across which the
    ratio is unbounded, is flagged as shocked (convention mine, ``issues/102``). The two
    neighbours of an edge cell are the cell itself and its one inner neighbour: the field
    is extended by repeating the edge value, a zero-gradient wall, never wrapped.

    Args:
        pressure: One channel, shape ``(*spatial)``.
        mach_min: The weakest Mach number reported as a shock.
        gamma: Ratio of specific heats used to convert ``mach_min`` to a pressure ratio.

    Returns:
        Boolean array of ``pressure``'s shape, True on shocked cells.
    """
    # Schaal & Springel (2015) Eq. (2): the pressure ratio across a Mach mach_min shock.
    ratio = 2.0 * gamma * mach_min**2 / (gamma + 1.0) - (gamma - 1.0) / (gamma + 1.0)
    padded = np.pad(pressure, 1, mode="edge")  # zero-gradient wall; the tube has walls
    shocked = np.zeros(pressure.shape, dtype=bool)
    for axis in range(pressure.ndim):
        inner = [slice(1, -1)] * pressure.ndim
        ahead, behind = list(inner), list(inner)
        ahead[axis], behind[axis] = slice(2, None), slice(None, -2)
        pair = (padded[tuple(ahead)], padded[tuple(behind)])
        # Schaal & Springel (2015) Sect. 2.3.2 criterion (iii), pressure half:
        # Delta log p >= log(p2/p1) at M_min, written without the logarithm.
        shocked |= np.maximum(*pair) >= ratio * np.minimum(*pair)
    return shocked


def surface_distances(a: NDArray[np.bool_], b: NDArray[np.bool_],
                      spacing: tuple[float, ...]) -> tuple[NDArray, NDArray]:
    """Distance from every point of ``a`` to the nearest point of ``b``, and the reverse.

    The point-to-set distance ``d(x, B) = min_{y in B} |x - y|`` with the Euclidean distance
    at the grid's own spacing, Yeghiazaryan & Voiculescu (2018), J. Med. Imaging 5(1),
    015006, Sect. 2.3 (unnumbered in the copy read). It is the minimum inside Taha &
    Hanbury's (2015) directed distances, BMC Med. Imaging 15, 29, Eqs. (49) and (51). Every
    flagged cell is a point of the set: a shock is already thin, so no boundary is
    extracted from the mask (choice mine). The exact Euclidean distance transform measures
    across the domain, never around it, so on a periodic grid it overstates the distance
    of two points on either side of the seam.

    Args:
        a, b: Boolean masks of one shape, each with at least one True cell.
        spacing: Cell size along each axis.

    Returns:
        ``(d_ab, d_ba)``: one distance per True cell of ``a``, then of ``b``.
    """
    if not (a.any() and b.any()):
        raise ValueError("surface_distances needs two non-empty sets; the caller scores "
                         "an empty set")
    return (distance_transform_edt(~b, sampling=spacing)[a],
            distance_transform_edt(~a, sampling=spacing)[b])


@metric(
    name="shock_set_distance",
    arity="pairwise",
    fields=("pressure",),
    differentiable=False,           # a thresholded detector: the sets change in jumps
    cost="cheap",
    higher_is_better=False,
    symmetric=True,
    monotone_under_smoothing=False,  # a thresholded set changes in jumps, with ties
    units="length",
    requires_periodic=False,
)
def shock_set_distance(reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
                       ctx: FieldContext) -> float:
    """Average symmetric surface distance between the shock sets of two pressure fields.

    With ``A`` and ``B`` the shocked cells of the reference and the candidate
    (:func:`shock_mask`), the average of all distances from points of one set to the other
    set and back, Yeghiazaryan & Voiculescu (2018), J. Med. Imaging 5(1), 015006,
    Sect. 2.3.2, unnumbered in the copy read::

        ASSD(A, B) = (sum_{a in A} d(a, B) + sum_{b in B} d(b, A)) / (|A| + |B|)

    Two empty sets score 0: both fields agree there is no shock (convention mine). One
    empty set scores the length of the domain's diagonal, the worst-possible value
    Maier-Hein et al. (2024), Nature Methods 21, 195-212, Suppl. Note 2.3, recommend for a
    distance that is undefined, naming the image diagonal; it exceeds every distance two
    cell centres can have. Both are conventions, ``issues/102``. Channels are averaged.

    Args:
        reference: The trusted pressure, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The pressure being scored, same shape and grid.
        ctx: Supplies the grid spacing, and caches the reference's shock set per frame.

    Returns:
        The distance in the units of the grid spacing: zero when the two shock sets
        coincide, and at most the domain's diagonal.

    Raises:
        ValueError: If the shapes differ, or do not match the grid in ``ctx``.
    """
    if reference.shape != candidate.shape or reference.shape[1:] != ctx.grid.shape:
        raise ValueError(f"shock_set_distance needs matching shapes on the grid "
                         f"{ctx.grid.shape}, got {reference.shape} and {candidate.shape}")
    spacing = ctx.grid.spacing
    diagonal = float(np.sqrt(sum((n * dx) ** 2 for n, dx in zip(ctx.grid.shape, spacing))))
    key = "shock_set_distance/reference_masks"
    if key not in ctx.cache:
        ctx.cache[key] = [shock_mask(channel) for channel in reference]
    values = []
    for a, channel in zip(ctx.cache[key], candidate):
        b = shock_mask(channel)
        if not (a.any() or b.any()):
            values.append(0.0)
        elif not (a.any() and b.any()):
            # Maier-Hein et al. (2024) Suppl. Note 2.3: the worst value, the diagonal.
            values.append(diagonal)
        else:
            d_ab, d_ba = surface_distances(a, b, spacing)
            # Yeghiazaryan & Voiculescu (2018) Sect. 2.3.2: the pooled mean of both directions.
            values.append(float((d_ab.sum() + d_ba.sum()) / (d_ab.size + d_ba.size)))
    return float(np.mean(values))
