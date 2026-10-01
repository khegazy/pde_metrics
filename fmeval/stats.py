"""Estimators on plain arrays, used by :mod:`fmeval.analysis` for the response statistics.

No pandas and no knowledge of the result frame: every function takes numpy arrays and returns
numbers, so each can be checked against a hand-computed answer. Every function returns NaN on
degenerate input rather than raising, because the caller runs several hundred groups and one
degenerate axis must not stop a report.

Production quality. Equations taken from the literature cite author, year and venue beside them.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterator

import numpy as np
from scipy.optimize import OptimizeWarning, curve_fit

#: Politis & White's constant ``c`` in the rule that picks the number of significant lags.
FLAT_TOP_C: float = 2.0

#: Models whose AICc lies within this many units of the best still have substantial support
#: (Burnham & Anderson 2002, *Model Selection and Multimodel Inference*, 2nd ed., Springer), so the
#: shape label goes to the simplest of them rather than to a winner the data cannot distinguish.
AICC_SUPPORT: float = 2.0


def elasticity(x: np.ndarray, y: np.ndarray) -> float:
    """Ordinary least-squares slope of ln y on ln x: the local power-law exponent of a response.

    1 means the response grows in proportion to x, 2 with its square, near 0 that it barely moves.
    Points with a non-positive x or y are dropped, since their logarithm does not exist.

    Returns:
        The slope, or NaN with fewer than three usable points or no spread in x.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    keep = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
    if keep.sum() < 3 or np.ptp(np.log(x[keep])) == 0:
        return float("nan")
    return float(np.polyfit(np.log(x[keep]), np.log(y[keep]), 1)[0])


def severity_at(x: np.ndarray, y: np.ndarray, target: float) -> float:
    """The x at which the ladder-ordered curve ``y`` first reaches ``target``.

    Interpolated between the two bracketing levels, linearly in ln x when both are positive (so a
    ladder of doublings is treated evenly) and linearly in x on a segment that starts at zero. This
    is an interpolation convention, not a fit, and is good to about one ladder step.

    Args:
        x: Severity per level, increasing.
        y: Response per level, same order.
        target: The response to reach.

    Returns:
        The crossing, ``x[0]`` if the first level already reaches it, NaN if no level does.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    keep = np.isfinite(x) & np.isfinite(y)
    x, y = x[keep], y[keep]
    if not np.isfinite(target):
        return float("nan")
    hit = np.flatnonzero(y >= target)
    if hit.size == 0:
        return float("nan")
    i = int(hit[0])
    if i == 0:
        return float(x[0])
    t = (target - y[i - 1]) / (y[i] - y[i - 1])
    if x[i - 1] > 0 and x[i] > 0:
        return float(np.exp(np.log(x[i - 1]) + t * (np.log(x[i]) - np.log(x[i - 1]))))
    return float(x[i - 1] + t * (x[i] - x[i - 1]))


#: Candidate response shapes: (function, initial guess, lower bounds, upper bounds), in units
#: where x and y are both scaled to a maximum of one.
_SHAPES = {
    "linear": (lambda x, a: a * x, [1.0], [0.0], [np.inf]),
    "power": (lambda x, a, b: a * np.power(x, b), [1.0, 1.0], [0.0, 0.0], [np.inf, 10.0]),
    "saturating": (lambda x, a, b: a * (1.0 - np.exp(-x / b)), [1.0, 1.0],
                   [0.0, 1e-3], [np.inf, 1e3]),
}


def fit_response_shape(x: np.ndarray, y: np.ndarray) -> tuple[str, dict[str, float]]:
    """Which of a line, a power law or a saturating exponential describes the curve best.

    Each candidate is fitted by least squares and they are compared by the small-sample corrected
    Akaike criterion, AICc = n ln(RSS/n) + 2k + 2k(k+1)/(n-k-1) (Hurvich & Tsai 1989, *Biometrika*
    76(2):297-307). A candidate is tried only with at least two more points than parameters, and
    the label is "undetermined" unless at least two candidates were fitted: on three levels only
    the line can be fitted, so naming it would report the default rather than the data. Among
    candidates within :data:`AICC_SUPPORT` of the best, the one with fewest parameters wins.

    Every candidate has a free amplitude, so the label is unchanged by rescaling y.

    Returns:
        ``(label, params)`` with the parameters in the caller's units, or ``("undetermined", {})``.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    keep = np.isfinite(x) & np.isfinite(y) & (x > 0)
    x, y = x[keep], y[keep]
    n = len(x)
    if n < 4 or y.max() <= 0:
        return "undetermined", {}
    x_scale, y_scale = x.max(), y.max()
    xs, ys = x / x_scale, y / y_scale
    floor = 1e-20 * float(np.sum(ys**2))             # an exact fit would otherwise give ln 0
    fits: dict[str, tuple[float, np.ndarray]] = {}
    for label, (fn, p0, lower, upper) in _SHAPES.items():
        k = len(p0)
        if n < k + 2:
            continue
        guess = list(p0)
        if label == "power":
            slope = elasticity(xs, ys)
            guess[1] = float(np.clip(slope, 0.0, 10.0)) if np.isfinite(slope) else 1.0
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", OptimizeWarning)
                warnings.simplefilter("ignore", RuntimeWarning)
                params, _ = curve_fit(fn, xs, ys, p0=guess, bounds=(lower, upper), maxfev=20000)
        except (RuntimeError, ValueError):
            continue
        rss = max(float(np.sum((fn(xs, *params) - ys) ** 2)), floor)
        fits[label] = (n * np.log(rss / n) + 2 * k + 2 * k * (k + 1) / (n - k - 1), params)
    if len(fits) < 2:
        return "undetermined", {}
    best = min(value for value, _ in fits.values())
    supported = [label for label, (value, _) in fits.items() if value <= best + AICC_SUPPORT]
    label = min(supported, key=lambda name: (len(_SHAPES[name][1]), fits[name][0]))
    p = fits[label][1]
    physical = {
        "linear": lambda: {"a": p[0] * y_scale / x_scale},
        "power": lambda: {"a": p[0] * y_scale / x_scale ** p[1], "b": p[1]},
        "saturating": lambda: {"a": p[0] * y_scale, "b": p[1] * x_scale},
    }[label]()
    return label, {name: float(value) for name, value in physical.items()}


def fisher_severity_resolution(x: np.ndarray, Z: np.ndarray) -> np.ndarray:
    """How precisely the metric's value pins down the severity, at each adjacent pair of levels.

    For levels i and i+1 the per-frame step ``d = Z[:, i+1] - Z[:, i]`` has mean m and standard
    deviation s, so the severity resolved by one observation is ``s / |m| * (x[i+1] - x[i])``: the
    Cramér-Rao bound 1/sqrt(I) with Fisher information I = (dD/ds)^2 / sigma^2 (Seung & Sompolinsky
    1993, *PNAS* 90(22):10749-10753). Pairing within a frame cancels anything common to both levels
    in that frame. A lower bound, tight only when the scatter is small.

    Args:
        x: Severity per level, increasing.
        Z: Frames by levels, already on a scale that removes trajectory drift (the caller's job).

    Returns:
        One value per adjacent pair: ``inf`` when the mean step is zero and the scatter is not,
        NaN when both are zero or fewer than two frames are usable.
    """
    x, Z = np.asarray(x, float), np.asarray(Z, float)
    out = np.full(len(x) - 1, np.nan)
    for i in range(len(x) - 1):
        d = Z[:, i + 1] - Z[:, i]
        d = d[np.isfinite(d)]
        dx = x[i + 1] - x[i]
        if len(d) < 2 or not np.isfinite(dx) or dx == 0:
            continue
        spread, mean = float(np.std(d, ddof=1)), float(np.mean(d))
        if mean == 0:
            out[i] = np.inf if spread > 0 else np.nan
        else:
            out[i] = spread / abs(mean) * abs(dx)
    return out


def treves_rolls_sparseness(r: np.ndarray) -> float:
    """Treves-Rolls sparseness a = (mean r)^2 / mean(r^2) of a non-negative response profile.

    1 for a flat profile and 1/n when one entry carries it all (Treves & Rolls 1991, *Network*
    2(4):371-397). Negative entries are clipped to zero.

    Returns:
        a, or NaN with fewer than two finite entries or an all-zero profile.
    """
    r = np.asarray(r, float)
    r = np.clip(r[np.isfinite(r)], 0.0, None)
    if len(r) < 2 or np.mean(r**2) == 0:
        return float("nan")
    return float(np.mean(r) ** 2 / np.mean(r**2))


def lins_ccc(x: np.ndarray, y: np.ndarray) -> float:
    """Lin's concordance correlation coefficient: agreement with the identity line, not just a line.

    rho_c = 2 s_xy / (s_x^2 + s_y^2 + (mu_x - mu_y)^2) with population moments, over the pairs where
    both are finite (Lin 1989, *Biometrics* 45(1):255-268).

    Returns:
        rho_c, or NaN with fewer than two pairs or a zero denominator.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    keep = np.isfinite(x) & np.isfinite(y)
    x, y = x[keep], y[keep]
    if len(x) < 2:
        return float("nan")
    denominator = x.var() + y.var() + (x.mean() - y.mean()) ** 2
    if denominator == 0:
        return float("nan")
    return float(2 * np.mean((x - x.mean()) * (y - y.mean())) / denominator)


def _flat_top(t: np.ndarray) -> np.ndarray:
    """The trapezoidal flat-top lag window: 1 up to |t| = 1/2, falling linearly to 0 at |t| = 1."""
    t = np.abs(t)
    return np.where(t <= 0.5, 1.0, np.where(t <= 1.0, 2.0 * (1.0 - t), 0.0))


def politis_white_block_length(x: np.ndarray) -> int:
    """Automatic block length for the moving-block bootstrap of a dependent series.

    The selector of Politis & White (2004, *Econometric Reviews* 23(1):53-70), with the correction
    of Patton, Politis & White (2009, *Econometric Reviews* 28(4):372-375): count the lags whose
    autocorrelation is significant, estimate the long-run variance and its first moment with a
    flat-top lag window, and return b = (2 G^2 / D)^(1/3) N^(1/3) with D = (4/3) g(0)^2 for the
    moving-block bootstrap. Clipped to at most a quarter of the series.

    It is derived for the mean of a stationary series. A trending series has no decaying
    autocorrelation and drives it to long blocks, so callers remove any trend first. Applied here to
    the per-frame trace of a median, which is a heuristic transfer rather than the case it was
    derived for.

    Returns:
        A block length of at least 1; 1 for a constant series or one too short to estimate.
    """
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 2:
        return 1
    k_n = max(5, int(np.ceil(np.sqrt(np.log10(n)))))
    if n < 2 * k_n + 2 or np.ptp(x) == 0:
        return 1
    x = x - x.mean()
    m_max = min(int(np.ceil(np.sqrt(n))) + k_n, n - 1)
    R = np.array([np.dot(x[: n - k], x[k:]) / n for k in range(m_max + 1)])
    if R[0] <= 0:
        return 1
    insignificant = np.abs(R[1:] / R[0]) < FLAT_TOP_C * np.sqrt(np.log10(n) / n)   # lags 1..m_max
    m_hat = next((m for m in range(m_max - k_n + 1) if insignificant[m: m + k_n].all()), None)
    if m_hat is None:
        significant = np.flatnonzero(~insignificant)
        m_hat = int(significant[-1]) + 2 if significant.size else 1
    M = int(np.clip(2 * m_hat, 1, m_max))
    lags = np.arange(-M, M + 1)
    weights = _flat_top(lags / M) * R[np.abs(lags)]
    G = float(np.sum(weights * np.abs(lags)))
    D = 4.0 / 3.0 * float(np.sum(weights)) ** 2
    if not (np.isfinite(G) and np.isfinite(D) and G > 0 and D > 0):
        return 1
    b = (2.0 * G**2 / D) ** (1.0 / 3.0) * n ** (1.0 / 3.0)
    return int(np.clip(round(b), 1, max(1, n // 4)))


def block_bootstrap(n_frames: int, block_length: int, n_draws: int,
                    rng: np.random.Generator) -> Iterator[np.ndarray]:
    """Positional index arrays for a moving-block bootstrap (Künsch 1989, *Ann. Stat.* 17(3)).

    Each draw concatenates ``ceil(n_frames / L)`` blocks of ``L`` consecutive indices whose starts
    are drawn uniformly with replacement. Overlapping blocks, no wrap, no truncation: the same
    construction the rank-correlation interval in :mod:`fmeval.analysis` uses.
    """
    L = max(1, min(int(block_length), int(n_frames)))
    starts = np.arange(n_frames - L + 1)
    n_blocks = int(np.ceil(n_frames / L))
    for _ in range(n_draws):
        chosen = rng.choice(starts, size=n_blocks)
        yield np.concatenate([np.arange(s, s + L) for s in chosen])
