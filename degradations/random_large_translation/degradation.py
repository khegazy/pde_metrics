"""The `random_large_translation` degradation.

See ``card.md`` for what this stands in for, how its severity is scaled, and where it
is not a fair imitation of the failure it models.
"""

from __future__ import annotations

import numpy as np

from ..registry import degradation


@degradation(
    name="random_large_translation",
    family="geometric",
    severity_name="draw",
    severity_units="",
    severity_direction="increasing",
    ordinal=False,   # a probe, not a severity level on a monotone axis
    stochastic=True,
    preserves=("single_point_statistics", "amplitude_spectrum", "spatial_mean", "shape"),
    zero_is_identity=False,
)
def random_large_translation(x: np.ndarray, severity: float, *, ctx) -> np.ndarray:
    """Translate by a large random offset on every axis: the right statistics in the wrong place.

    A probe, scored on the damage scale like the impostor. It keeps every statistic that does not
    depend on position and removes the alignment, so its damage says how a metric scores a field
    that is the right kind of field somewhere else. It is not the damage anchor, for the reason
    below; the anchor is the field's spatial mean (``mean_field``, judgements/001).

    A distant frame of the same trajectory would be the obvious alternative and is wrong:
    the flow decays, so from t=5000 to t=9000 the vorticity variance falls to 0.70 of its
    value and the flatness rises from 17.1 to 27.3. That field is a different physical
    state, not a twin, and it scores *closer* to the reference than a true twin does
    purely because it has weakened.

    Offsets are drawn from the middle half of each axis, and ``severity`` is just the draw
    index so that several independent draws can be taken; the analysis reports their median.

    **It is not an unrelated field.** A translation by d multiplies the mode at wavenumber k by
    the phase k*d, and a field whose energy sits in a few large-scale modes does not average that
    phase away, so the moved copy stays partly correlated or anti-correlated with the reference.
    Measured on kinet_re5e4 (pinned run comparison_1793302178), the median ``energy_changed`` of
    these rows -- 2 for an unrelated field of the same variance -- is 1.64 on density, 3.05 on
    velocity and 2.25 on vorticity, and density's six draws differ by a median factor of 3.2
    within a frame. Its declared ``preserves`` hold on periodic axes only. On an axis with walls
    the harness rolls the mirror-extended field and crops it, so the result is a mirrored window
    rather than a copy: on sod_shock_tube it is anti-correlated with the reference and its
    ``energy_changed`` is 3.46 on density.
    """
    offsets = [
        int(ctx.rng.integers(n // 4, 3 * n // 4 + 1)) for n in x.shape[1:]
    ]
    return np.roll(x, shift=tuple(offsets), axis=ctx.spatial_axes)
