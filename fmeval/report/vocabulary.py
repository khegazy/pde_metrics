"""One set of plain words for every quantity a figure or a card labels.

The site's reader is an early graduate student in any field. The cards already say "weakest
gap between neighbouring strengths" rather than ``separability_auc_min``; a figure that
printed the column name beside that table would teach the same reader two vocabularies for
one number. Figures, their captions and the card text that introduces them read their words
from here, and a test asserts that every column the figures draw has an entry and that no
entry grades anything.

The labels describe what was measured. They never say good or bad: this repository measures
and does not decide (``docs/decisions.md``, "There is no pass or fail").
"""

from __future__ import annotations

#: Plain name for each degradation family, used as a figure row label and as the ``###``
#: heading of the matching card subsection. The two are one mapping so a reader moving
#: between a figure and the table beneath it is never asked to translate.
FAMILY_LABELS: dict[str, str] = {
    "smoothing": "Smoothing",
    "spectral": "Spectral filtering",
    "geometric": "Displacement",
    "resolution": "Resolution loss",
    "stochastic": "Noise",
    "pointwise": "Cell-value distortion",
    "ensemble": "Ensemble dispersion",
}

#: Plain label for each statistic a figure draws, keyed by its column name. The label says
#: what the number is and which way it runs, in words the card tables already use.
LABELS: dict[str, str] = {
    "damage": "damage (0 = undegraded reference, 1 = unrelated field)",
    "value": "metric value",
    "level": "severity level (1 = mildest)",
    "rho": "rank correlation with strength (1 = ordered correctly in every frame)",
    "rho_ci_lo": "rank correlation, lower end of the resampling interval",
    "rho_ci_hi": "rank correlation, upper end of the resampling interval",
    "cliffs_delta_min": "separation of neighbouring strengths "
                        "(0 = indistinguishable, 1 = never overlap)",
    "damage_per_change": "damage charged per unit of field change",
    "damage_max_ucb": "largest damage, upper confidence bound",
    "blind_axes": "response provably below the margin",
    "sensitivity_level": "first strength at which the metric has moved a tenth of the way",
    "gaussian_impostor_damage": "fake prediction with the right spectrum",
    "severity_degenerate": "strength that repeated a milder one or did nothing (excluded)",
    "energy_changed": "field change (normalised mean squared error)",
}

#: Words a label or caption may not contain. A label that calls a measurement good, bad,
#: passing or failing has turned a measurement into a verdict.
GRADING_WORDS: tuple[str, ...] = ("good", "bad", "pass", "fail", "best", "worst", "verdict")


def label(column: str) -> str:
    """The plain label for a column, or the column name itself if none is recorded.

    Falling back to the name rather than raising keeps a figure drawable while the vocabulary
    is extended; the coverage test is what makes a missing entry a failure.
    """
    return LABELS.get(column, column)
