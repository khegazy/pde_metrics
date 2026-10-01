"""The cross-metric overview: every metric's response on one page of the site.

A metric card answers "what does this metric see?"; the question a reader choosing between
metrics has is "which of them sees *this*?", and that needs every metric on one figure. The
report already draws two such figures -- the sparkline grid of median damage against
severity level (metrics by degradations, one per field) and the portrait of adjacent-level
discrimination (every field in one grid) -- so this module renders those same registered
renderers from the evidence run into ``docs/figures/<run>/`` with the numbers beside each,
under the same determinism rules as the card figures (:mod:`fmeval.cards.metric_figures`),
and builds the markdown of the page that shows them.

One directory per run, named for it, because the grid can only hold the metrics one run
evaluated: the probabilistic metrics are measured on their own single-metric runs on a
calibrated null and cannot appear beside the kinet metrics. The page says which metrics
are not on the grid and why, rather than leaving a reader to notice the gap.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from matplotlib import pyplot as plt
from matplotlib import rc_context

from fmeval.report.latex import slug
from fmeval.report.registry import PLOTS, RendererUnavailable, check_preconditions, iter_scope

from .exemplars import REPO
from .metric_figures import CardFigure, remove_stale, report_context, svg_rc, write_figure

if TYPE_CHECKING:
    from .evidence import Run

#: Where the overview figures live, one subdirectory per run. Tracked, unlike the pages
#: ``docs/gen_pages.py`` generates, because the figures are committed artifacts.
FIGURES_ROOT: Path = REPO / "docs" / "figures"

#: The renderers the overview page shows, in page order. Both already exist for the report.
OVERVIEW_FIGURES: tuple[str, ...] = ("response_sparklines", "response_portrait")

#: The one-line question each figure answers, used as alt text. No ``]`` or ``)``.
ALT_TEXT: dict[str, str] = {
    "response_sparklines": "median damage against severity level for every metric and every "
                           "degradation, one small curve per cell on one shared scale",
    "response_portrait": "separation of neighbouring strengths for every metric, degradation "
                         "and field, one wedge per field",
}

#: Plain heading for each figure on the page.
HEADINGS: dict[str, str] = {
    "response_sparklines": "The whole ladder in one view",
    "response_portrait": "Which metrics can tell neighbouring strengths apart",
}


def overview_figures(run: Run, out_dir: Path, *,
                     theme: str = "notebook") -> tuple[list[CardFigure], dict[str, str]]:
    """Draw the overview figures of one run into ``out_dir`` and write their numbers.

    Returns the figures written, in page order, and the reason for any that a renderer
    declined to draw. Anything a renderer raises other than
    :class:`RendererUnavailable` propagates: a half-written figure directory would be
    committed as if it were complete.
    """
    ctx = report_context(run, theme=theme)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[CardFigure] = []
    reasons: dict[str, str] = {}
    provenance = {"run": run.folder.name, "dataset": str(run.rows["dataset"].iloc[0]),
                  "metrics": sorted(str(m) for m in run.rows["metric"].unique())}
    for name in OVERVIEW_FIGURES:
        spec = PLOTS[name]
        ok, why = check_preconditions(spec, ctx)
        if not ok:
            reasons[name] = why
            continue
        for keys, subset in iter_scope(spec.scope, ctx.df):
            stem = slug(name, **keys)
            with rc_context(svg_rc(ctx.style)):
                try:
                    result = spec.fn(ctx, subset, dict(spec.defaults))
                except RendererUnavailable as exc:
                    reasons[stem] = str(exc)
                    plt.close("all")
                    continue
                item = result.figures[0]
                item.caption = item.caption or spec.title
                path, numbers = out_dir / f"{stem}.svg", out_dir / f"{stem}.json"
                write_figure(item, path, numbers, panel_key="metric",
                             record={**provenance, "figure": name, "keys": keys})
                plt.close("all")
            written.append(CardFigure(name=stem, path=path, numbers=numbers,
                                      caption=item.caption, alt=ALT_TEXT[name]))
    remove_stale(out_dir, {f.path.name for f in written})
    return written, reasons


_INTRO = """\
# Sensitivity at a glance

Every metric page reports how that one metric responded to each way of damaging a field.
This page puts every metric on the same figures, drawn from one recorded evaluation run by
the same code that draws the report, so that the question a reader choosing a metric
actually has -- *which of these sees the failure I care about?* -- can be answered by eye.

Nothing here is a ranking. Damage is on one 0-to-1 scale throughout, where 0 is the
undegraded reference and 1 is a field with the right statistics and no relation to the
truth; the figures show what each metric sees and what each metric misses, and a metric
that is flat on one degradation and steep on another is exactly the information a reader
needs. The numbers behind each figure are linked beside it. For how to read a single
metric's page, see [How to read a metric page](reading-guide.md).
"""


def page_markdown(figures_root: Path = FIGURES_ROOT, catalog: dict | None = None) -> str:
    """The markdown of the overview page, built from the committed figures and their JSON.

    One section per run directory, newest first by name; each figure under its own heading
    with the caption its renderer wrote and a link to its numbers. If the catalog is given,
    the page ends by naming every measured metric that is not on the grid and why.
    """
    import json

    lines = [_INTRO]
    runs = sorted((d for d in figures_root.iterdir() if d.is_dir()), reverse=True) \
        if figures_root.is_dir() else []
    if not runs:
        lines.append("\n*No overview figures have been generated yet. Run "
                     "`python -m fmeval.cards overview --results results/<run>`.*\n")
        return "\n".join(lines)
    on_grid: set[str] = set()
    for run_dir in runs:
        records = {p.stem: json.loads(p.read_text()) for p in sorted(run_dir.glob("*.json"))}
        if not records:
            continue
        first = next(iter(records.values()))
        metrics = first.get("metrics", [])
        on_grid.update(metrics)
        lines += [f"\n## Run `{run_dir.name}`\n",
                  f"Measured on `{first.get('dataset')}`, for {len(metrics)} metrics: "
                  + ", ".join(f"[{m}](metrics/{m}.md)" for m in metrics) + ".\n"]
        ordered = sorted(records, key=lambda stem: (OVERVIEW_FIGURES.index(records[stem]["figure"]),
                                                    stem))
        for stem in ordered:
            record = records[stem]
            keys = record.get("keys", {})
            heading = HEADINGS[record["figure"]]
            if keys:
                heading += " -- " + ", ".join(f"{v}" for v in keys.values())
            lines += [f"### {heading}\n",
                      f"![{ALT_TEXT[record['figure']]}](figures/{run_dir.name}/{stem}.svg)\n",
                      record["caption"] + "\n",
                      f"*Numbers behind this figure: "
                      f"[{stem}.json](figures/{run_dir.name}/{stem}.json).*\n"]
    if catalog is not None:
        absent = [e for e in catalog["entries"]
                  if e["kind"] == "metric" and e["evidence"]["measured"]
                  and e["name"] not in on_grid]
        if absent:
            lines += ["\n## Not on these figures\n",
                      "A cross-metric figure can hold only the metrics one run evaluated "
                      "together. These metrics are measured, but on runs of their own, so "
                      "their figures are on their pages: "
                      + ", ".join(f"[{e['name']}](metrics/{e['name']}.md) "
                                  f"(run `{e['evidence']['run']}` on `{e['evidence']['dataset']}`)"
                                  for e in absent)
                      + ". The probabilistic metrics are evaluated on a calibrated null, a "
                        "synthetic ensemble whose statistics are known in closed form; it is "
                        "not a flow, and placing those numbers beside measurements on turbulence "
                        "would invite a comparison that means nothing.\n"]
    return "\n".join(lines)
