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

The other metrics of detected shock sets import what they share from here: the checks, the
cached reference masks and the channel mean (:func:`shock_set_score`), the scores of empty sets
(:func:`set_distance`), and the point set and line-out their cards draw
(:func:`shock_positions`, :func:`pressure_profile`).
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import partial

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import distance_transform_edt

from fmeval.context import FieldContext
from fmeval.data.analytic import SodShockTube
from fmeval.data.base import GridSpec
from metrics.registry import companion, metric

#: The weakest shock the detector reports, as a Mach number. Schaal & Springel (2015), MNRAS
#: 446, 3992, Sect. 2.3.2, criterion (iii).
MACH_MIN: float = 1.3
#: The ratio of specific heats the Mach threshold is converted with. The metric is handed one
#: field and no equation of state, so it is fixed, and read from the one compressible dataset
#: that stores a pressure, the Sod reader's default, rather than restated here.
GAMMA: float = inspect.signature(SodShockTube).parameters["gamma"].default
#: ``ctx.cache`` key of the reference's shock masks, one per channel, computed once per frame.
REFERENCE_MASKS = "shock_set/reference_masks"


def shock_mask(pressure: NDArray[np.floating], *, mach_min: float = MACH_MIN,
               gamma: float = GAMMA) -> NDArray[np.bool_]:
    """The cells of one pressure field that a shock of at least ``mach_min`` passes through.

    The pressure half of the shock-zone criterion (iii) of Schaal & Springel (2015), MNRAS
    446, 3992-4007, Sect. 2.3.2: a cell is shocked when the jump in log pressure between
    its two neighbours reaches that of a normal shock at ``mach_min``, whose pressure ratio
    is their Eq. (2), the Rankine-Hugoniot relation
    ``p2/p1 = 2 gamma M^2/(gamma + 1) - (gamma - 1)/(gamma + 1)``. They take the neighbours
    along the shock direction, which needs the temperature gradient this metric is not given,
    so the test is applied along every grid axis and a cell is shocked if any axis flags it
    (choice mine). Their criteria (i) and (ii), on the velocity divergence and the temperature
    and density gradients, need fields a single-field metric does not receive, and they warn
    that the pressure part alone "may not be sufficient"; only it is applied here.

    The jump is tested as ``max(p_-, p_+) >= R min(p_-, p_+)`` with ``min(p_-, p_+) > 0``, in
    double precision. A pressure ratio, and so a Mach number, exists only between two positive
    pressures, so a cell beside a zero or negative pressure is never flagged (convention mine,
    ``issues/102``): a field that is not a thermodynamic pressure has no shock, and cannot score
    better than a missed shock by being flagged everywhere. The two neighbours of an edge cell
    are the cell itself and its one inner neighbour: the field is extended by repeating the
    edge value, a zero-gradient wall, never wrapped.

    Args:
        pressure: One channel, shape ``(*spatial)``.
        mach_min: The weakest Mach number reported as a shock.
        gamma: Ratio of specific heats used to convert ``mach_min`` to a pressure ratio.

    Returns:
        Boolean array of ``pressure``'s shape, True on shocked cells.
    """
    # Schaal & Springel (2015) Eq. (2): the pressure ratio across a Mach mach_min shock.
    ratio = 2.0 * gamma * mach_min**2 / (gamma + 1.0) - (gamma - 1.0) / (gamma + 1.0)
    # Zero-gradient wall, never wrapped (the tube has walls); double precision, so a float32
    # field is flagged exactly as its float64 copy is.
    padded = np.pad(np.asarray(pressure, dtype=np.float64), 1, mode="edge")
    shocked = np.zeros(pressure.shape, dtype=bool)
    for axis in range(pressure.ndim):
        inner = [slice(1, -1)] * pressure.ndim
        ahead, behind = list(inner), list(inner)
        ahead[axis], behind[axis] = slice(2, None), slice(None, -2)
        pair = (padded[tuple(ahead)], padded[tuple(behind)])
        low = np.minimum(*pair)
        # Schaal & Springel (2015) Sect. 2.3.2 criterion (iii), pressure half:
        # Delta log p >= log(p2/p1) at M_min, written without the logarithm, between two
        # positive pressures only (convention mine, issues/102).
        shocked |= (low > 0) & (np.maximum(*pair) >= ratio * low)
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



def shock_set_score(reference: NDArray[np.floating], candidate: NDArray[np.floating], *,
                    ctx: FieldContext,
                    score: Callable[[NDArray[np.bool_], NDArray[np.bool_], GridSpec], float],
                    ) -> float:
    """Compare the shock sets of two pressure fields channel by channel with ``score``.

    The step every metric of a detected shock set shares: the shapes are checked against each
    other and the grid, a field that is NaN or infinite anywhere scores NaN (it has no readable
    pressure ratio there, and a pointwise error returns NaN too), the reference's masks
    (:func:`shock_mask`) are computed once per frame and kept in ``ctx.cache``, and the
    channels' scores are averaged; pressure has one channel.

    Args:
        reference: The trusted pressure, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The pressure being scored, same shape and grid.
        ctx: Supplies the grid, and caches the reference's masks per frame.
        score: Scores the reference's mask against the candidate's on the grid.

    Returns:
        The channel mean of ``score``, or NaN on a non-finite field.

    Raises:
        ValueError: If the shapes differ, or do not match the grid in ``ctx``: a field without
            its channel axis would otherwise be read as channels of single cells, none flagged.
    """
    if reference.shape != candidate.shape or reference.shape[1:] != ctx.grid.shape:
        raise ValueError(f"a shock-set metric needs matching shapes on the grid "
                         f"{ctx.grid.shape}, got {reference.shape} and {candidate.shape}")
    if not (np.isfinite(reference).all() and np.isfinite(candidate).all()):
        return float("nan")
    if REFERENCE_MASKS not in ctx.cache:
        ctx.cache[REFERENCE_MASKS] = [shock_mask(channel) for channel in reference]
    return float(np.mean([score(a, shock_mask(channel), ctx.grid)
                          for a, channel in zip(ctx.cache[REFERENCE_MASKS], candidate)]))


def set_distance(a: NDArray[np.bool_], b: NDArray[np.bool_], grid: GridSpec, *,
                 summary: Callable[[NDArray[np.bool_], NDArray[np.bool_], tuple[float, ...]],
                                   float]) -> float:
    """A distance between two shock sets, with the empty sets scored by convention.

    Two empty sets score 0: both fields agree there is no shock. One empty set scores the
    length of the domain's diagonal, the worst-possible value Maier-Hein et al. (2024), Nature
    Methods 21, 195-212, Suppl. Note 2.3, recommend for a distance that is undefined, naming the
    image diagonal; it exceeds every distance two cell centres can have. Both are conventions of
    this repository (``issues/102``), shared by every distance between shock sets so that they
    treat a missing shock alike. Two non-empty sets are scored by ``summary``.

    Args:
        a, b: The reference's and the candidate's shocked cells.
        grid: The analysis grid, for its spacing and extent.
        summary: The distance between two non-empty sets at the grid's spacing.

    Returns:
        The distance, in the units of the grid spacing.
    """
    if not (a.any() or b.any()):
        return 0.0
    if not (a.any() and b.any()):
        # Maier-Hein et al. (2024) Suppl. Note 2.3: the worst value, the diagonal.
        return float(np.sqrt(sum((n * dx) ** 2 for n, dx in zip(grid.shape, grid.spacing))))
    return float(summary(a, b, grid.spacing))


def average_symmetric_surface_distance(a: NDArray[np.bool_], b: NDArray[np.bool_],
                                       spacing: tuple[float, ...]) -> float:
    """The pooled mean of the distances from each set to the other, Equation (2) of the card.

    Yeghiazaryan & Voiculescu (2018), J. Med. Imaging 5(1), 015006, Sect. 2.3.2, unnumbered in
    the copy read::

        ASSD(A, B) = (sum_{a in A} d(a, B) + sum_{b in B} d(b, A)) / (|A| + |B|)
    """
    d_ab, d_ba = surface_distances(a, b, spacing)
    return float((d_ab.sum() + d_ba.sum()) / (d_ab.size + d_ba.size))


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
    (:func:`shock_mask`), :func:`average_symmetric_surface_distance`, with the empty sets
    scored by the conventions of :func:`set_distance` (``issues/102``). Channels are averaged
    and a non-finite field scores NaN (:func:`shock_set_score`).

    Args:
        reference: The trusted pressure, shape ``(C, *spatial)`` on the analysis grid.
        candidate: The pressure being scored, same shape and grid.
        ctx: Supplies the grid spacing, and caches the reference's shock set per frame.

    Returns:
        The distance in the units of the grid spacing: zero when the two shock sets
        coincide, at most the domain's diagonal, and NaN on a non-finite field.

    Raises:
        ValueError: If the shapes differ, or do not match the grid in ``ctx``.
    """
    return shock_set_score(reference, candidate, ctx=ctx, score=partial(
        set_distance, summary=average_symmetric_surface_distance))


@companion(of="shock_set_distance", kind="points",
           coordinate=(("x", "cells"), ("pressure", "field")))
def shock_positions(pressure: NDArray[np.floating]) -> NDArray[np.float64]:
    """The cells :func:`shock_mask` flags in one pressure field, as (cell index, pressure) rows.

    The point set behind every shock-set metric, drawn by the card figure over the pressure's
    line-out (:func:`pressure_profile`), the reference's and each degraded field's, so the
    detected positions are read off the profile. The index is along the first grid axis, the
    axis of a one-dimensional grid; on a grid of more dimensions the rows keep only that
    coordinate. A non-finite field has no readable pressure ratio and gives no rows.

    Args:
        pressure: One pressure field, shape ``(C, *spatial)``.

    Returns:
        An ``(N, 2)`` array of (cell index along the first axis, pressure) of the flagged cells
        of every channel.
    """
    if not np.isfinite(pressure).all():
        return np.zeros((0, 2))
    masks = [shock_mask(channel) for channel in pressure]
    return np.concatenate([np.column_stack([np.nonzero(mask)[0], channel[mask]])
                           for channel, mask in zip(pressure, masks)]).astype(np.float64)


@companion(of="shock_set_distance", name="profile")
def pressure_profile(pressure: NDArray[np.floating]) -> NDArray[np.float64]:
    """The pressure itself, the line-out the detected shocks are drawn on; one channel."""
    return np.asarray(pressure[0], dtype=np.float64)
