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

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import rc_context

from fmeval.io import read_config, read_maps
from fmeval.pipeline import parse_map_key
from fmeval.report import style as report_style
from fmeval.report.context import FigureItem, ReportContext
from fmeval.report.latex import slug
from fmeval.report.plots import companion_records  # importing registers the renderers
from fmeval.report.registry import PLOTS, RendererSpec, check_preconditions, draw, iter_scope

from .loader import json_records, write_strict_json
from .prose import EXPERIMENT_BLOCK

if TYPE_CHECKING:
    from .evidence import Run

#: The slot of the figure the metric's own field draws, the renderer :func:`standard_figure`
#: names. It is the first figure on the card, ahead of the harness's own.
STANDARD = "standard"

#: The slot of a real forecast's error against its lead time, drawn from each further run of
#: real forecasts the card cites and shown in that run's subsection
#: (:func:`fmeval.cards.evidence.experiment_block`).
LEAD = "lead_time"

#: The renderer that draws :data:`LEAD`, and the field's figure of a pairwise metric whose card
#: cites a run of real forecasts.
ALONG_TIME = "response_along_time"

#: The figures a metric card draws, in the order the card shows them: the field's figure, then
#: the harness's, then the lead-time figure of each run of real forecasts. Every renderer drawn
#: must be a ``per_metric`` or ``per_metric_field`` plot in
#: :data:`fmeval.report.registry.PLOTS`; a ``per_metric_field`` one is drawn once per field.
METRIC_FIGURES: tuple[str, ...] = (STANDARD, "sensitivity_profile", "response_curves",
                                   "damage_beside_controls", LEAD)

#: Which generated block of the card each figure opens. The field's figure and the two response
#: figures head the Performance summary; the magnitude comparison sits above the table of the
#: same numbers; a lead-time figure opens the subsection of the run it was drawn from, the block
#: whose name starts with :data:`EXPERIMENT_BLOCK`.
FIGURE_BLOCKS: dict[str, str] = {
    STANDARD: "performance",
    "sensitivity_profile": "performance",
    "response_curves": "performance",
    "damage_beside_controls": "results_damage_by_level",
    LEAD: EXPERIMENT_BLOCK,
}

#: The words a card uses for a figure where it names the slot rather than a renderer.
SLOT_TITLES: dict[str, str] = {STANDARD: "field-standard", LEAD: "lead-time"}

#: Renderer options a card overrides. A card shows at most four point-set panels: twelve
#: persistence diagrams of vorticity, about 7000 points each on the pinned kinet run, wrote
#: 10.6 MB of numbers beside one figure, a large share of the size budget for every committed
#: generated file (``tests/test_cards.py``). The report keeps every panel.
CARD_OPTIONS: dict[str, dict] = {"companion_points": {"max_panels": 4}}

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
    "companion_curves": "the curve behind the number against its coordinate, as its field "
                        "draws it, at every strength of each degradation, the clean curve in "
                        "black",
    "companion_points": "the point sets behind the number, each degraded set over the "
                        "reference's, as its field draws them",
    ALONG_TIME: "the metric against time: the clean field's own history in black and each "
                "strength of the operator applied at each time, or a real forecast's error "
                "against its lead time, one panel per start and one line per run",
}


@dataclass(frozen=True)
class CardFigure:
    """One figure written beside a card, and the numbers written beside it."""

    name: str
    path: Path
    numbers: Path
    caption: str
    alt: str
    slot: str = ""
    """The entry of :data:`METRIC_FIGURES` it fills; one file may fill two, and the field's
    figure of a per-field renderer fills one slot with a file per field."""
    source: str = ""
    """The further run it was drawn from, empty when it was drawn from the primary run."""


def _panels(data: pd.DataFrame | None, key: str) -> dict[str, list[dict]]:
    """The renderer's data split into panels, as exact JSON-ready records."""
    if data is None or data.empty:
        return {}
    records = json_records(data)
    if key not in data.columns:
        return {"all": records}
    panels: dict[str, list[dict]] = {}
    for record in records:
        panels.setdefault(str(record[key]), []).append(record)
    return dict(sorted(panels.items()))


def render_figure(spec: RendererSpec, ctx: ReportContext, subset: pd.DataFrame, out_dir: Path,
                  stem: str, *, alt: str, record: dict, panel_key: str,
                  keep: Callable[[FigureItem], bool] | None = None,
                  options: dict | None = None) -> tuple[list[CardFigure], str]:
    """Draw one renderer, save its figures as byte-stable SVGs and their numbers as strict JSON.

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
        keep: Which of the renderer's figures to write, each under ``stem`` extended by the
            keys that tell it apart (:func:`fmeval.report.latex.slug`, the metric left out).
            None writes the first figure alone, under ``stem``.
        options: Renderer options overriding its defaults (:func:`draw`).

    Returns:
        The figures written, empty with the renderer's reason when it declined.
    """
    written = []
    with rc_context({**ctx.style.rc, "svg.hashsalt": SVG_HASHSALT}):
        result, why = draw(spec, ctx, subset, options)
        items = ([] if result is None else result.figures[:1] if keep is None
                 else [item for item in result.figures if keep(item)])
        for item in items:
            name = stem if keep is None else slug(
                stem, **{k: v for k, v in item.keys.items() if k != "metric"})
            caption = item.caption or spec.title
            path, numbers = out_dir / f"{name}.svg", out_dir / f"{name}.json"
            item.fig.savefig(path, format="svg", metadata={"Date": None, "Creator": None})
            write_strict_json(numbers, {**record, "caption": caption,
                                        "panels": _panels(item.data, panel_key)})
            written.append(CardFigure(name=name, path=path, numbers=numbers, caption=caption,
                                      alt=alt))
        plt.close("all")
    return written, why


def remove_stale(out_dir: Path, keep: set[str]) -> None:
    """Delete every ``.svg`` in ``out_dir`` not in ``keep``, with the ``.json`` beside it."""
    for stale in sorted(out_dir.glob("*.svg")):
        if stale.name not in keep:
            stale.unlink()
            stale.with_suffix(".json").unlink(missing_ok=True)


def _forecasts(ctx: ReportContext, metric: str) -> bool:
    """Whether a run holds real forecasts of ``metric``: rows that carry a prediction step."""
    rows = ctx.df[ctx.df["metric"].astype(str) == metric]
    return "lead_step" in rows.columns and bool(rows["lead_step"].notna().any())


def standard_figure(contexts: Sequence[ReportContext],
                    metric: str) -> tuple[str | None, str, int]:
    """The renderer that draws the figure this metric's own field draws, the run it is drawn
    from, or None and why.

    One rule, read from what the metric declares and what the cited runs hold, so a metric names
    its figure by declaring its companions and nothing else. ``contexts`` are the card's runs,
    the primary run first; the returned index says which one the figure is drawn from.

    1. **A curve or a point set behind the number**: ``companion_curves`` or
       ``companion_points``, the object the field plots (a spectrum, a structure function, a
       Hill plot, a rank histogram; persistence diagrams, shock positions). The metric's own
       companion decides when it is one of these, else the first declared that is.
    2. **A single-field quantity**: ``response_along_time``, its value against time with the
       clean field's history in black, as an energy or enstrophy decay curve is drawn.
    3. **A two-field metric whose card cites a run of real forecasts**: ``response_along_time``
       on the first such run, its error against lead time, as the forecasting benchmarks score a
       rollout step by step. The primary run keeps every other figure and table.
    4. **Any other two-field metric**: ``damage_beside_controls``, its misfit against an
       applied shift beside the pointwise errors, the comparison by which an error that
       tolerates displacement is told apart from the pointwise ones.
    5. **An ensemble score with none of the above**: no figure here. Its field draws scores
       against lead time, and the synthetic ensemble's time is a phase advance with one spread
       at every frame, on which such a figure is flat by construction.
    """
    ctx = contexts[0]
    companions = [c for c in companion_records(ctx, metric) if c["kind"] in ("curve", "points")]
    if companions:
        own = next((c for c in companions if c["name"] == metric), companions[0])
        return f"companion_{'curves' if own['kind'] == 'curve' else 'points'}", "", 0
    rows = ctx.df[ctx.df["metric"].astype(str) == metric]
    if "arity" not in rows.columns or rows.empty:
        return None, "the run records no arity for this metric", 0
    arity = str(rows["arity"].iloc[0])
    if arity == "single":
        return ALONG_TIME, "", 0
    if arity == "pairwise":
        forecast = next((i for i, c in enumerate(contexts) if _forecasts(c, metric)), None)
        return ((ALONG_TIME, "", forecast) if forecast is not None
                else ("damage_beside_controls", "", 0))
    return None, ("an ensemble score with no curve or point set behind it; its field draws it "
                  "against lead time, which the synthetic ensemble, one spread at every frame, "
                  "cannot show"), 0


def metric_figures(
    run: Run, metric: str, out_dir: Path, others: Sequence[Run] = (),
) -> tuple[list[CardFigure], dict[str, str]]:
    """Draw every card figure for one metric and write each with its numbers.

    The field's figure (:data:`STANDARD`) comes first. A renderer that fills two slots, as
    ``damage_beside_controls`` does for a pairwise metric with nothing else to draw, or a
    forecast run's lead-time figure that is also a pairwise metric's field figure, is drawn once
    and its file shown in both. The stored maps the field's figures read are those of this metric
    alone, read lazily from the primary run's ``error_maps.npz``; a further run's figure is named
    after its dataset and records its run in :attr:`CardFigure.source`.

    Args:
        run: The primary evidence run, already analysed.
        metric: The metric whose card is being generated.
        out_dir: The bundle's ``_generated/`` directory.
        others: The card's further runs, already analysed. Only a run of real forecasts is
            drawn from: its lead-time figure (:data:`LEAD`), and the field's figure of a
            pairwise metric (:func:`standard_figure`).

    Returns:
        The figures written, in card order, and the reason for each slot of
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
    maps = read_maps(run.folder, keep=lambda key: parse_map_key(key)[0].partition(".")[0]
                     == metric)
    runs = [run, *others]
    contexts = [ReportContext.from_analysis(r, meta=r.meta, theme=report_style.DEFAULT_THEME,
                                            maps=maps if r is run else {},
                                            config=read_config(r.folder)) for r in runs]
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[CardFigure] = []
    reasons: dict[str, str] = {}
    drawn: dict[tuple[str, int], list[CardFigure]] = {}
    standard, why_none, standard_run = standard_figure(contexts, metric)
    forecasts = [i for i in range(1, len(runs)) if _forecasts(contexts[i], metric)]

    for slot in METRIC_FIGURES:
        # (renderer, index of the run it is drawn from) for each figure the slot shows.
        wanted = ([(standard, standard_run)] if slot == STANDARD
                  else [(ALONG_TIME, i) for i in forecasts] if slot == LEAD
                  else [(slot, 0)])
        for name, index in wanted:
            if name is None:
                reasons[slot] = why_none
                continue
            if (name, index) in drawn:
                written += [replace(f, slot=slot) for f in drawn[name, index]]
                continue
            spec, ctx, source = PLOTS[name], contexts[index], runs[index]
            if spec.scope not in ("per_metric", "per_metric_field"):
                raise ValueError(f"{name} is {spec.scope!r}; a card figure must be per_metric "
                                 "or per_metric_field")
            ok, why = check_preconditions(spec, ctx)
            if not ok:
                reasons[slot] = why
                continue
            subsets = [sub for keys, sub in iter_scope(spec.scope, ctx.df)
                       if keys.get("metric") == metric]
            if not subsets:
                reasons[slot] = f"{metric} is not in the run"
                continue
            dataset = str(source.rows["dataset"].iloc[0])
            stem = name if index == 0 else slug(name, dataset=dataset)
            figures, why = [], []
            for subset in subsets:
                # The field's figure keeps every figure the renderer draws but a per-coordinate
                # view, whose numbers the card prints as tables in its companion block.
                out, declined = render_figure(
                    spec, ctx, subset, out_dir, stem, alt=ALT_TEXT[name], panel_key="field",
                    record={"metric": metric, "run": source.folder.name, "dataset": dataset,
                            "figure": name},
                    keep=None if spec.scope == "per_metric" else (lambda i: "view" not in i.keys),
                    options=CARD_OPTIONS.get(name))
                figures += [replace(f, slot=slot, source="" if index == 0
                                    else source.folder.name) for f in out]
                why += [declined] if declined else []
            if figures:
                drawn[name, index] = figures
                written += figures
            else:
                reasons[slot] = "; ".join(dict.fromkeys(why)) or "the renderer drew nothing"

    # Rule 3: nothing this generation did not write survives beside the card.
    remove_stale(out_dir, {f.path.name for f in written})
    return written, reasons
