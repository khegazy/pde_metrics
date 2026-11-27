"""The `member_shape` degradation: heavy-tailed or skewed members with the right mean and
variance.

See ``card.md`` for what this stands in for and where it misleads.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

from ..registry import degradation


@degradation(
    family="ensemble",
    severity_name="departure from the normal",
    severity_units="1/nu, or the two-piece scale split",
    severity_direction="increasing",
    ensemble=True,
    preserves=("ensemble_mean",),
)
def member_shape(members: np.ndarray, severity: float, *,
                 family: str = "student_t") -> np.ndarray:
    """Map each cell's members onto a heavier-tailed or skewed family, keeping their first two
    sample moments.

    Per cell, with x_bar and s_hat the members' sample mean and standard deviation:

    1. standardise, z = (x - x_bar) / s_hat;
    2. map through a quantile function, u = Q(Phi(z)): the Student-t quantile at
       nu = 1 / severity, or the two-piece normal quantile with scales 1 - severity (left)
       and 1 + severity (right), the distribution of Jordan, Krueger & Lerch (2019, J. Stat.
       Softw. 90(12), App. A.2.7);
    3. re-standardise u over the members and return x_bar + s_hat u.

    The map is monotone, so every member keeps its rank, and each cell's sample mean and
    sample variance are unchanged; the identity at severity 0.

    Raises:
        ValueError: On an unknown family, a severity outside its range (``student_t``:
            >= 0; ``two_piece``: [0, 1)), or a cell whose members all agree.
    """
    if family not in ("student_t", "two_piece"):
        raise ValueError(f"family must be student_t or two_piece, got {family!r}")
    if severity < 0 or (family == "two_piece" and severity >= 1):
        raise ValueError(f"member_shape severity for {family} must lie in "
                         f"{'[0, 1)' if family == 'two_piece' else '[0, inf)'}, got {severity}")
    if severity == 0:
        return members
    mean = members.mean(axis=0)
    spread = members.std(axis=0, ddof=1)
    if spread.min() == 0:
        raise ValueError("member_shape: a cell whose members all agree has no shape to change")
    p = stats.norm.cdf((members - mean) / spread)
    if family == "student_t":
        u = stats.t.ppf(p, df=1.0 / severity)
    else:
        # Two-piece normal quantile, inverting its CDF F(x) = 2 s1/(s1+s2) Phi(x/s1) for
        # x <= 0 and (s1 - s2 + 2 s2 Phi(x/s2))/(s1 + s2) above (Jordan et al. 2019, App. A.2.7).
        s1, s2 = 1.0 - severity, 1.0 + severity
        u = np.where(p <= s1 / (s1 + s2),
                     s1 * stats.norm.ppf(np.minimum(p * (s1 + s2) / (2 * s1), 1.0)),
                     s2 * stats.norm.ppf(np.maximum((p * (s1 + s2) - s1 + s2) / (2 * s2), 0.0)))
    u = (u - u.mean(axis=0)) / u.std(axis=0, ddof=1)
    return mean + spread * u
