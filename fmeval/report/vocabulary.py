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

from dataclasses import dataclass


@dataclass(frozen=True)
class Family:
    """How one degradation family is shown, everywhere it is shown."""

    label: str
    """Figure row label, and the ``###`` heading of the matching card subsection: one set of
    words, so a reader moving between a figure and the table beneath it never translates."""
    colour: str
    """Okabe-Ito colour name (``style.OKABE_ITO``), fixed per family rather than assigned from
    whatever families a run contains, so smoothing is the same colour on every page."""
    description: str
    """What a degradation of this family does, for the site's header table."""


#: Every degradation family a figure, card or page shows. The keys are
#: ``degradations.registry.FAMILIES`` less ``identity``, which is the reference and is never
#: drawn; a test holds the two equal. One table, so the label, colour and wording of a family
#: cannot fall out of step.
FAMILY_INFO: dict[str, Family] = {
    "smoothing": Family("Smoothing", "blue", "smoothing away fine detail"),
    "spectral": Family("Spectral filtering", "purple", "filtering out chosen scales"),
    "geometric": Family("Displacement", "vermillion", "moving features to the wrong place"),
    "resolution": Family("Resolution loss", "green", "losing grid resolution"),
    "stochastic": Family("Noise", "orange", "adding noise"),
    "pointwise": Family("Cell-value distortion", "sky", "distorting each cell's value"),
    "ensemble": Family("Ensemble dispersion", "black", "making the ensemble the wrong width"),
}


def family_label(family: str) -> str:
    """The plain name of a degradation family, or the family code if it has none."""
    return FAMILY_INFO[family].label if family in FAMILY_INFO else str(family)

#: Plain label for each statistic a figure draws, keyed by its column name. The label says
#: what the number is and which way it runs, in words the card tables already use.
LABELS: dict[str, str] = {
    "damage": "damage (0 = undegraded reference, 1 = the anchor)",
    "value": "metric value",
    "level": "severity level (1 = mildest)",
    "rho": "rank correlation with strength (1 = follows the degradation in every frame)",
    "relative_change_max": "change from the clean value at the harshest strength "
                           "(fraction of clean)",
    "relative_change_median": "change from the clean value (fraction of clean)",
    "severity_resolution": "variation from snapshot to snapshot relative to the response, "
                           "in the strength's units",
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
    # The profile, worded identically in the LaTeX report and on the cards.
    "most_sensitive_axis": "charges most for",
    "least_sensitive_axis": "charges least for",
    "elasticity_displacement": "elasticity to a sub-pixel shift",
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
