"""The figures a metric card opens with, drawn from the run its evidence cites.

A card shows its numbers as tables, and a table does not answer the first question a reader
has -- where does this metric start to move, how fast, what is it blind to -- at a glance. The
figures here answer it, and they are produced by the same registered renderers the LaTeX
report uses (:mod:`fmeval.report.plots`), called through the registry so a card and a report
of the same run cannot draw different pictures. Renderers still write nothing: this module
owns the paths, the rcParams and the file format (``context.py``).

Three rules, each enforced by a test in ``tests/test_cards.py``:

1. **Every figure is byte-stable within one matplotlib version.** The files are committed,
   so a regeneration of an unchanged figure must be a no-op diff. SVG needs two things for
   that, both measured here: a fixed ``svg.hashsalt`` (without it matplotlib salts element
   ids with a fresh uuid and two renders differ) and no creation date in the metadata. Both
   are only honoured when ``savefig`` runs inside the same ``rc_context`` as the drawing.
2. **Every figure has its numbers beside it.** An agent reading the site cannot open an SVG;
   the ``.json`` next to each figure carries the renderer's data, keyed under ``panels``.
   Schema: ``{metric, run, dataset, figure, caption, panels}`` where ``panels`` maps a field
   (curves) or a statistic (profile) to a list of records -- the shape an interactive view
   could be fed from later without re-deriving anything.
3. **What this generation did not write is removed.** A figure renamed or dropped from
   :data:`METRIC_FIGURES` must not linger in ``_generated/`` beside a card that no longer
   references it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import rc_context

from fmeval.report import plots as _plots  # noqa: F401  (importing registers the renderers)
from fmeval.report import style as report_style
from fmeval.report.context import ReportContext
from fmeval.report.registry import PLOTS, RendererSpec, check_preconditions, draw, iter_scope

from .loader import write_strict_json

if TYPE_CHECKING:
    from .evidence import Run

#: The renderers a metric card draws, in the order the card shows them. Each must be a
#: ``scope="per_metric"`` plot in :data:`fmeval.report.registry.PLOTS`.
METRIC_FIGURES: tuple[str, ...] = ("sensitivity_profile", "response_curves",
                                   "damage_beside_controls")

#: Which generated block of the card each figure opens. The two response figures head the
#: Performance summary; the magnitude comparison sits above the table of the same numbers.
FIGURE_BLOCKS: dict[str, str] = {
    "sensitivity_profile": "performance",
    "response_curves": "performance",
    "damage_beside_controls": "results_damage_by_level",
}

#: Fixed salt for SVG element ids. Any string works; what matters is that it never changes,
#: because a changed salt rewrites every committed SVG at once.
SVG_HASHSALT = "pde_metrics"

#: The one-line question each figure answers, used as the image's alt text. Free of ``]``
#: and ``)``: the card checker's link pattern and the site's asset rewrite both stop at
#: those characters, so either would truncate the alt text or the path.
ALT_TEXT: dict[str, str] = {
    "sensitivity_profile": "how the metric responded to each degradation, by field: rank "
                           "correlation, separation of neighbouring strengths, damage per "
                           "unit of field change, and the bound on its largest response",
    "response_curves": "median damage against severity level, one panel per degradation "
                       "family and field, on one shared scale",
    "damage_beside_controls": "damage against applied strength for this metric beside the "
                              "pointwise controls, log-log, one panel per displacement "
                              "degradation and field",
}


@dataclass(frozen=True)
class CardFigure:
    """One figure written beside a card, and the numbers written beside it."""

    name: str
    path: Path
    numbers: Path
    caption: str
    alt: str


def _panels(data: pd.DataFrame | None, key: str) -> dict[str, list[dict]]:
    """The renderer's data split into panels, through ``to_json`` so numpy scalars serialise."""
    if data is None or data.empty:
        return {}
    records = json.loads(data.to_json(orient="records"))
    if key not in data.columns:
        return {"all": records}
    panels: dict[str, list[dict]] = {}
    for record in records:
        panels.setdefault(str(record[key]), []).append(record)
    return dict(sorted(panels.items()))


def render_figure(spec: RendererSpec, ctx: ReportContext, subset: pd.DataFrame, out_dir: Path,
                  stem: str, *, alt: str, record: dict,
                  panel_key: str) -> tuple[CardFigure | None, str]:
    """Draw one renderer, save it as a byte-stable SVG and its numbers as strict JSON.

    Drawing and saving share one ``rc_context`` holding the theme and the fixed
    :data:`SVG_HASHSALT`: the salt is read when the SVG is written, so a save outside the
    context would get a fresh uuid every time (rule 1).

    Args:
        spec: The registered renderer.
        ctx: The renderers' view of the run.
        subset: The rows of ``ctx.df`` this figure draws.
        out_dir: Where ``<stem>.svg`` and ``<stem>.json`` are written.
        stem: The file stem, and the returned figure's name.
        alt: The image's alt text.
        record: The provenance the JSON carries beside ``caption`` and ``panels``.
        panel_key: The column of the renderer's data the JSON's panels are split by.

    Returns:
        The figure written, or ``None`` and the renderer's reason for declining.
    """
    with rc_context({**ctx.style.rc, "svg.hashsalt": SVG_HASHSALT}):
        result, why = draw(spec, ctx, subset)
        if result is None:
            plt.close("all")
            return None, why
        item = result.figures[0]
        caption = item.caption or spec.title
        path, numbers = out_dir / f"{stem}.svg", out_dir / f"{stem}.json"
        item.fig.savefig(path, format="svg", metadata={"Date": None, "Creator": None})
        plt.close("all")
    write_strict_json(numbers, {**record, "caption": caption,
                                "panels": _panels(item.data, panel_key)})
    return CardFigure(name=stem, path=path, numbers=numbers, caption=caption, alt=alt), why


def remove_stale(out_dir: Path, keep: set[str]) -> None:
    """Delete every ``.svg`` in ``out_dir`` not in ``keep``, with the ``.json`` beside it."""
    for stale in sorted(out_dir.glob("*.svg")):
        if stale.name not in keep:
            stale.unlink()
            stale.with_suffix(".json").unlink(missing_ok=True)


def metric_figures(
    run: Run, metric: str, out_dir: Path, *, theme: str = report_style.DEFAULT_THEME,
) -> tuple[list[CardFigure], dict[str, str]]:
    """Draw every card figure for one metric and write each with its numbers.

    Args:
        run: The evidence run, already analysed.
        metric: The metric whose card is being generated.
        out_dir: The bundle's ``_generated/`` directory.
        theme: A theme from :mod:`fmeval.report.style`, shared with the LaTeX report.

    Returns:
        The figures written, in card order, and the reason for each figure in
        :data:`METRIC_FIGURES` that could not be drawn -- a renderer declaring itself
        unavailable is a statement about the run, not an error, and the card prints it.

    Raises:
        Anything a renderer raises other than :class:`RendererUnavailable`. The report
        driver swallows those so a bad figure cannot lose an expensive evaluation; a
        generator of committed files must instead stop, because a half-written
        ``_generated/`` directory would be committed as if it were complete.
    """
    # The same frames the report builds from the folder, taken from the run the card
    # generator already analysed, so a figure draws the numbers the tables beside it print.
    ctx = ReportContext.from_analysis(run, meta=run.meta, theme=theme)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[CardFigure] = []
    reasons: dict[str, str] = {}

    for name in METRIC_FIGURES:
        spec = PLOTS[name]
        if spec.scope != "per_metric":
            raise ValueError(f"{name} is {spec.scope!r}; a card figure must be per_metric")
        ok, why = check_preconditions(spec, ctx)
        if not ok:
            reasons[name] = why
            continue
        subset = next((sub for keys, sub in iter_scope(spec.scope, ctx.df)
                       if keys.get("metric") == metric), None)
        if subset is None:
            reasons[name] = f"{metric} is not in the run"
            continue
        figure, why = render_figure(
            spec, ctx, subset, out_dir, name, alt=ALT_TEXT[name], panel_key="field",
            record={"metric": metric, "run": run.folder.name,
                    "dataset": str(run.rows["dataset"].iloc[0]), "figure": name})
        if figure is None:
            reasons[name] = why
        else:
            written.append(figure)

    # Rule 3: nothing this generation did not write survives beside the card.
    remove_stale(out_dir, {f.path.name for f in written})
    return written, reasons
