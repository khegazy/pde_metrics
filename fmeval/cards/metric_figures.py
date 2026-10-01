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
from fmeval.report.registry import PLOTS, RendererUnavailable, check_preconditions, iter_scope

from .exemplars import sanitize_json

if TYPE_CHECKING:
    from .evidence import Run

#: The renderers a metric card draws, in the order the card shows them. Each must be a
#: ``scope="per_metric"`` plot in :data:`fmeval.report.registry.PLOTS`.
METRIC_FIGURES: tuple[str, ...] = ("sensitivity_profile", "response_curves")

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
}

#: The column whose values key ``panels`` in the figure's JSON, per figure.
_PANEL_KEY: dict[str, str] = {"response_curves": "field", "sensitivity_profile": "field"}


@dataclass(frozen=True)
class CardFigure:
    """One figure written beside a card, and the numbers written beside it."""

    name: str
    path: Path
    numbers: Path
    caption: str
    alt: str


def report_context(run: Run, *, theme: str = "notebook") -> ReportContext:
    """The renderers' view of an evidence run.

    The same frames :func:`fmeval.report.driver.build_context` would build from the folder,
    taken from the :class:`Run` the card generator already analysed, so the numbers a figure
    draws are the numbers the tables beside it print. The card frame is unflagged: cards
    carry no flags.
    """
    scored = run.scored
    return ReportContext(
        df=scored, norm=run.norm, axes=run.axes, probes=run.probes, card=run.card,
        meta=run.meta,
        style=report_style.Style.build(theme, metrics=scored["metric"].unique(),
                                       axes=scored["degradation"].unique()),
        anchor_label=run.anchor_label, probe_labels=run.probe_labels,
    )


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


def metric_figures(run: Run, metric: str, out_dir: Path, *,
                   theme: str = "notebook") -> tuple[list[CardFigure], dict[str, str]]:
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
    ctx = report_context(run, theme=theme)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[CardFigure] = []
    reasons: dict[str, str] = {}
    rc = {**ctx.style.rc, "svg.hashsalt": SVG_HASHSALT}

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
        path = out_dir / f"{name}.svg"
        numbers = out_dir / f"{name}.json"
        # Drawing and saving share one rc_context: the hashsalt is read when the SVG is
        # written, so a save outside the context would get a fresh uuid every time.
        with rc_context(rc):
            try:
                result = spec.fn(ctx, subset, dict(spec.defaults))
            except RendererUnavailable as exc:
                reasons[name] = str(exc)
                plt.close("all")
                continue
            item = result.figures[0]
            item.fig.savefig(path, format="svg", metadata={"Date": None, "Creator": None})
            plt.close("all")
        record = {
            "metric": metric,
            "run": run.folder.name,
            "dataset": str(run.rows["dataset"].iloc[0]),
            "figure": name,
            "caption": item.caption or spec.title,
            "panels": _panels(item.data, _PANEL_KEY.get(name, "field")),
        }
        numbers.write_text(
            json.dumps(sanitize_json(record), indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
        written.append(CardFigure(name=name, path=path, numbers=numbers,
                                  caption=item.caption or spec.title, alt=ALT_TEXT[name]))

    # Rule 3: nothing this generation did not write survives beside the card.
    keep = {f.path.name for f in written} | {f.numbers.name for f in written}
    for stale in sorted(out_dir.glob("*.svg")):
        if stale.name not in keep:
            stale.unlink()
            stale.with_suffix(".json").unlink(missing_ok=True)
    return written, reasons
