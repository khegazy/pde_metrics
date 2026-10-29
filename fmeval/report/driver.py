"""Run every renderer and assemble the LaTeX document.

The driver owns everything the renderers deliberately do not: precondition checks, paths,
file formats, rcParams, and the manifest. A renderer that cannot run is logged and
recorded, never fatal -- a failing figure must not destroy an expensive evaluation's
output.

Section prose is generated rather than boilerplate: each chapter quotes the measured
numbers inline and points at its figures, so the document reads as an assessment rather
than a folder of plots.
"""

from __future__ import annotations

import json
import logging
import time
import traceback
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from dataclasses import field as dc_field
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import rc_context

from fmeval import CONFIGS
from fmeval import analysis as an
from fmeval.io import (
    COMPANIONS,
    RunFolder,
    dump_yaml,
    read_config,
    read_results,
    read_run_meta,
    read_yaml,
)

from . import plots as _plots  # noqa: F401  (registers the figure renderers)
from . import tables as _tables  # noqa: F401  (registers the table renderers)
from .context import ReportContext
from .latex import booktabs_table, code, document, escape, figure, preamble, slug, verbatim
from .registry import (
    PLOTS,
    SECTIONS,
    TABLES,
    check_preconditions,
    draw,
    iter_renderers,
    iter_scope,
)
from .style import DEFAULT_THEME

log = logging.getLogger(__name__)


@dataclass
class Rendered:
    """Outcome of one renderer, for the manifest and for the document."""

    name: str
    kind: str
    section: int
    title: str
    status: str
    reason: str = ""
    files: list[str] = dc_field(default_factory=list)
    latex: list[str] = dc_field(default_factory=list)
    notes: list[str] = dc_field(default_factory=list)
    duration_s: float = 0.0

    @classmethod
    def of(cls, spec, status: str, reason: str = "") -> Rendered:
        """The outcome of ``spec``, before anything has been drawn."""
        return cls(spec.name, spec.kind, spec.section, spec.title, status, reason)


#: The repository's report settings, read only for a run folder that did not record its own.
REPORT_DEFAULTS = CONFIGS / "report" / "default.yaml"


def build_context(
    folder: RunFolder,
    *,
    theme: str = DEFAULT_THEME,
    thresholds: Mapping[str, float] | None = None,
    bootstrap: int = an.N_BOOTSTRAP,
) -> ReportContext:
    """Load a run folder and compute everything the renderers need.

    All the statistics happen here, once, so a figure and its table cannot disagree. The
    advisory thresholds are the run's own, ``report.thresholds`` as its config recorded them,
    so a folder re-renders as it was run; a folder that predates the record takes the
    repository's ``configs/report/default.yaml``. ``thresholds`` overrides them key by key,
    so an empty mapping changes nothing; a NaN value switches that one flag off. A folder without
    ``calibration_spectrum.csv`` gets an empty spectrum rather than a failure.
    """
    df = read_results(folder)
    meta = read_run_meta(folder)
    config = read_config(folder)
    recorded = ((config.get("report") or {}).get("thresholds")
                or read_yaml(REPORT_DEFAULTS).get("thresholds", {}))
    thresholds = {**recorded, **(thresholds or {})}
    maps = _read_maps(folder.maps_path)
    spectrum_path = folder.data / "calibration_spectrum.csv"
    spectrum = pd.read_csv(spectrum_path) if spectrum_path.exists() else pd.DataFrame()

    analysis = an.analyse(df, companions=read_results(folder, COMPANIONS, missing_ok=True),
                          meta=meta, config=config, n_bootstrap=bootstrap)

    return ReportContext.from_analysis(
        analysis, meta=meta, theme=theme, card=an.flag(analysis.card, thresholds),
        spectrum=spectrum, maps=maps, config=config, thresholds=thresholds,
    )


def render(
    folder: RunFolder,
    ctx: ReportContext,
    *,
    only: Sequence[str] = (),
    skip: Sequence[str] = (),
    formats: Sequence[str] = ("pdf", "png"),
) -> list[Rendered]:
    """Run every registered renderer whose preconditions are met."""
    folder.create()
    results: list[Rendered] = []

    for spec in iter_renderers():
        if only and spec.name not in only:
            results.append(Rendered.of(spec, "disabled", "not selected"))
            continue
        if spec.name in skip or "*" in skip:
            results.append(Rendered.of(spec, "disabled", "skipped by config"))
            continue

        ok, why = check_preconditions(spec, ctx)
        if not ok:
            log.info("skip %s: %s", spec.name, why)
            results.append(Rendered.of(spec, "skipped", why))
            continue

        outcome = Rendered.of(spec, "ok")
        started = time.perf_counter()
        unavailable: list[str] = []
        rendered_any = False
        try:
            for keys, subset in iter_scope(spec.scope, ctx.df):
                # Unavailability is declared per scope subset: a renderer that cannot draw
                # one metric -- a single-field quantity with no damage scale -- must not
                # silence the figure for every other metric in the run.
                with rc_context(ctx.style.rc):
                    result, why = draw(spec, ctx, subset)
                if result is None:
                    where = ", ".join(f"{k}={v}" for k, v in keys.items()) or "all"
                    unavailable.append(f"{where}: {why}")
                    log.info("skip %s (%s): %s", spec.name, where, why)
                    continue
                rendered_any = True
                if spec.kind == "plot":
                    _emit_plot(folder, spec, result, formats, outcome)
                else:
                    _emit_table(folder, spec, result, outcome)
                outcome.notes.extend(getattr(result, "notes", []))
            if unavailable and not rendered_any:
                outcome.status, outcome.reason = "skipped", "; ".join(unavailable)
            elif unavailable:
                outcome.notes.append("not drawn for " + "; ".join(unavailable))
        except Exception:  # deliberately broad - a bad figure must not lose the evaluation
            outcome.status = "error"
            outcome.reason = traceback.format_exc(limit=3)
            log.exception("renderer %s failed", spec.name)
        finally:
            plt.close("all")
            outcome.duration_s = time.perf_counter() - started
        results.append(outcome)

    return results


def _emit_plot(folder, spec, result, formats, outcome) -> None:
    for item in result.figures:
        stem = slug(spec.name, **item.keys)
        for suffix in formats:
            path = folder.plots / f"{stem}.{suffix}"
            item.fig.savefig(path)
            outcome.files.append(str(path.relative_to(folder.root)))
        if item.data is not None and not item.data.empty:
            item.data.to_csv(folder.figure_data / f"{stem}.csv", index=False)
        outcome.latex.append(
            figure(stem, caption=item.caption or spec.title, label=stem)
        )


def _emit_table(folder, spec, result, outcome) -> None:
    stem = slug(spec.name, **result.keys)
    csv_path = folder.data / f"{stem}.csv"
    result.frame.to_csv(csv_path, index=False)
    tex = booktabs_table(
        result.frame,
        caption=result.caption or spec.title,
        label=stem,
        formats=result.formats,
        headers=result.headers,
        note=result.note,
        landscape=result.frame.shape[1] > 8,
        long=result.long,
    )
    (folder.tables / f"{stem}.tex").write_text(tex)
    outcome.files.extend([
        str(csv_path.relative_to(folder.root)),
        f"tables/{stem}.tex",
    ])
    outcome.latex.append(f"\\input{{tables/{stem}}}\n")


# --- document assembly -------------------------------------------------------------------


def write_document(folder: RunFolder, ctx: ReportContext,
                   rendered: Sequence[Rendered]) -> Path:
    """Write ``preamble.tex``, ``sections/*.tex`` and ``main.tex``."""
    by_section: dict[int, list[Rendered]] = {}
    for item in rendered:
        by_section.setdefault(item.section, []).append(item)

    metric = ctx.meta.get("metric") or ", ".join(ctx.metrics)
    dataset = ctx.meta.get("dataset", "")
    (folder.root / "preamble.tex").write_text(
        preamble(f"Metric report: {metric}", f"dataset: {dataset}")
    )

    written: list[str] = []
    for section in SECTIONS:
        items = [i for i in by_section.get(section.number, []) if i.status == "ok"]
        prose = _section_prose(section.key, ctx)
        if not items and not prose:
            continue
        body = [f"\\section{{{escape(section.title)}}}", ""]
        if section.intro:
            body += [escape(section.intro), ""]
        if prose:
            body += [prose, ""]
        for item in sorted(items, key=lambda i: (_declared_order(i), i.name)):
            body.extend(item.latex)
        name = f"{section.number:02d}_{section.key}"
        (folder.sections / f"{name}.tex").write_text("\n".join(body) + "\n")
        written.append(name)

    (folder.root / "main.tex").write_text(document(written))
    return folder.root / "main.tex"


def _response_headline(row: pd.Series, ctx: ReportContext) -> list[str]:
    """The response statistics of one metric and field, as clauses for the headline."""
    axes = ctx.ordinal_rows(metric=row["metric"], field=row["field"])
    bits = []
    if np.isfinite(row.get("selectivity", np.nan)):
        bits.append(
            f"its selectivity is {_fmt(row['selectivity'])}, charging most per unit of field "
            f"change for {code(row['most_sensitive_axis'])} and least for "
            f"{code(row['least_sensitive_axis'])}"
        )
    if "blindness_q" in axes.columns and axes["blindness_q"].notna().any():
        blind = an.split_blind(row.get("blind_axes"))
        bits.append(
            f"its largest response is provably below {an.BLINDNESS_MARGIN:g} at "
            f"{an.BLINDNESS_CONFIDENCE:.0%} confidence on "
            + (", ".join(code(a) for a in blind) if blind else "no degradation")
        )
    if np.isfinite(row.get("elasticity_displacement", np.nan)):
        against = axes.loc[axes["degradation"] == an.DISPLACEMENT_AXIS, "elasticity_x"]
        bits.append(
            f"its elasticity to a sub-pixel displacement is {_fmt(row['elasticity_displacement'])}"
            + (f" against {escape(str(against.iloc[0]))}" if len(against) else "")
        )
    return bits


def _declared_order(item: Rendered) -> int:
    """The ``order`` a renderer was registered with, which places it within its section."""
    spec = (PLOTS if item.kind == "plot" else TABLES).get(item.name)
    return spec.order if spec is not None else 100


def _section_prose(key: str, ctx: ReportContext) -> str:
    """Generated commentary quoting the measured numbers, per section."""
    card = ctx.card
    if key == "overview":
        meta = ctx.meta
        snapshot = meta.get("registries", {}).get("metrics", {})
        metric = meta.get("metric", "")
        entry = snapshot.get(metric, {})
        lines = []
        if entry.get("doc"):
            lines.append(escape(entry["doc"]))
        lines.append(
            f"Evaluated on {escape(meta.get('dataset', 'the dataset'))} over "
            f"{meta.get('n_frames', '?')} frames and "
            f"{len(meta.get('ladder_axes', []) or [])} ladder axes, on an analysis grid of "
            f"{meta.get('analysis_grid', '?')}. Configuration hash "
            f"{code(meta.get('config_hash', ''))}."
        )
        if entry:
            lines.append(
                f"Arity {escape(entry.get('arity', ''))}; units "
                f"{escape(entry.get('units', ''))}; "
                + ("differentiable" if entry.get("differentiable") else
                   "not differentiable")
                + ", so it "
                + ("could" if entry.get("differentiable") else "could not")
                + " serve as a training loss."
            )
        return "\n\n".join(lines)

    if key == "headline" and not card.empty:
        parts = []
        several = card["metric"].nunique() > 1
        for _, row in card.iterrows():
            subject = (f"For {code(str(row['metric']))} on "
                       f"{escape(str(row['field']))}" if several
                       else f"On {escape(str(row['field']))}")
            bits = [f"{subject}, the weakest axis is "
                    f"{code(str(row.get('worst_axis', '')))} with a rank "
                    f"correlation of {_fmt(row.get('rho_min'))}"]
            if np.isfinite(row.get("gaussian_impostor_damage", np.nan)):
                bits.append(
                    "the spectrum-matched Gaussian field is assigned a damage of "
                    f"{_fmt(row['gaussian_impostor_damage'])}, where 1 is the value two "
                    "unrelated fields receive"
                )
            elif np.isfinite(row.get("gaussian_impostor_relative", np.nan)):
                bits.append(
                    "this metric has no damage scale here, and the spectrum-matched Gaussian "
                    f"field moves it by {row['gaussian_impostor_relative']:.1e} of its largest "
                    "response to any ordinary degradation"
                )
            bits.extend(_response_headline(row, ctx))
            flags = str(row.get("flags", ""))
            bits.append(
                f"flagged: {escape(flags)}" if flags else
                "no configured reference value was missed"
            )
            parts.append("; ".join(bits) + ".")
        return "\n\n".join(parts)

    if key == "reliability" and not ctx.axes.empty:
        ordinal = ctx.ordinal_rows()
        ordinal = ordinal[ordinal["rho"].notna()]
        if ordinal.empty:
            # Every ordinal axis has an undefined correlation. That is what a metric invariant
            # to the whole ladder produces, and it is a documented-correct configuration rather
            # than an error, so the section says so instead of taking down the report.
            return (
                "Rank correlation is undefined on every ladder axis: the metric's value does "
                "not vary across the severity levels by more than floating-point round-off. For a "
                "single-field invariant measured against operators that preserve it, that is "
                "the correct result rather than a defect."
            )
        best = ordinal.loc[ordinal["rho"].idxmax()]
        worst = ordinal.loc[ordinal["rho"].idxmin()]
        return (
            f"Rank correlation ranges from {_fmt(worst['rho'])} on "
            f"{code(worst['degradation'])} to {_fmt(best['rho'])} on "
            f"{code(best['degradation'])}. Each is computed within a single "
            "ladder axis; correlating across axes would be meaningless, since severities "
            "on different axes have no order relative to one another. Each is also "
            "computed within a single frame and then aggregated: pooling every frame "
            "together would conflate the response to severity with the evolution of the "
            "field along the trajectory, which on this data spans several orders of "
            "magnitude."
        )

    if key == "selectivity" and ctx.df["metric"].nunique() >= 2:
        parts = []
        ratio, scaled = _independent_directions(ctx)
        missing = sorted(set(ctx.metrics) - set(scaled))
        if np.isfinite(ratio):
            parts.append(
                f"The {len(scaled)} metrics with a damage scale span {_fmt(ratio)} independent "
                "directions: the participation ratio of the eigenvalues of the covariance of "
                "their damage over every strength of every degradation, which would read "
                f"{len(scaled)} if each measured something different and 1 if they all measured "
                "the same thing."
            )
        if missing:
            parts.append("Left out, having no damage scale on this run: "
                         + ", ".join(f"{code(m)}" for m in missing) + ".")
        if "selectivity" in card.columns and card["selectivity"].notna().any():
            low = card.loc[card["selectivity"].idxmin()]
            high = card.loc[card["selectivity"].idxmax()]
            parts.append(
                f"Selectivity runs from {_fmt(low['selectivity'])} "
                f"({code(str(low['metric']))} on {escape(str(low['field']))}) to "
                f"{_fmt(high['selectivity'])} ({code(str(high['metric']))} on "
                f"{escape(str(high['field']))}), where 0 is a metric that charges every "
                "degradation the same per unit of field change."
            )
        return " ".join(parts)

    walls = ", ".join(ctx.meta.get("boundary", ()))
    if key == "displacement":
        text = (
            "A translation leaves every statistic of the field unchanged and alters only "
            "position. " if ctx.periodic else
            f"This dataset's boundaries are {escape(walls)}. Across a non-periodic boundary a "
            "translation brings in the field's extension by that boundary's rule rather than "
            "the far end of the domain, so it changes the field's values as well as their "
            "position, and no operator's declared invariants are quoted here. "
        ) + (
            "A metric that approaches the unrelated-field level after a "
            "displacement much smaller than the structures in the flow is exhibiting the "
            "double penalty: it is reporting a large error for a field that is correct in "
            "shape and amplitude."
        )
        geometric = sorted(
            str(a) for a in ctx.df.loc[ctx.df["degradation_family"] == "geometric",
                                       "degradation"].unique()
            if str(a) in ctx.ordinal_axes
        ) if "degradation_family" in ctx.df.columns else []
        for axis in geometric:
            words = ctx.preserved_by(axis)
            if words:
                text += (
                    f" {code(axis)} is declared, and test-verified, to leave "
                    "unchanged: " + ", ".join(w.replace("_", " ") for w in words) + "."
                )
        return text

    if key == "robustness":
        text = (
            "Two constructions are used. The spectrum-matched Gaussian field retains every "
            "Fourier amplitude and replaces every phase, so its energy spectrum and "
            "two-point correlation are identical to the reference to machine precision "
            "while its flatness collapses to the Gaussian value of three. A metric built "
            "only on second-order statistics cannot distinguish it from the reference. "
            "The positionally unrelated field is the reference translated by a large "
            "random offset, which preserves every statistic exactly while removing "
            "alignment, and therefore defines a damage of one."
        )
        if not ctx.periodic:
            text += (
                " Both statements hold on a periodic domain. This dataset's boundaries are "
                f"{escape(walls)}, and both fields are built on its extension across them and "
                "cropped back to the domain, so neither keeps the reference's statistics "
                "exactly: the Gaussian field keeps the Fourier amplitudes of the extension, "
                "and the unrelated field is a window onto the displaced extension, so part of "
                "what it shows is the extension rather than the reference."
            )
        if ctx.anchor_label != an.UNCORRELATED_LABEL:
            text += (
                " In this run the damage scale is anchored instead on the ladder entry "
                f"{code(ctx.anchor_label)} (set by \\texttt{{analysis.anchor}}), "
                "so a damage of one is the value that entry receives rather than the value of "
                "an unrelated field."
            )
        return text

    if key == "reproducibility":
        config = dump_yaml(dict(ctx.config))
        command = ctx.meta.get("command", "")
        body = []
        if command:
            body.append(verbatim(command, caption="Command"))
        body.append(verbatim(config, caption="Resolved configuration"))
        return "\n".join(body)

    return ""


def write_manifest(folder: RunFolder, rendered: Sequence[Rendered]) -> Path:
    """Record every renderer's outcome, including why anything was skipped."""
    path = folder.data / "manifest.json"
    path.write_text(json.dumps([asdict(r) for r in rendered], indent=2) + "\n")
    return path


def write_summary_text(folder: RunFolder, ctx: ReportContext) -> Path:
    """The headline block alone, for a glance in a terminal."""
    lines = [f"metric      : {ctx.meta.get('metric', '')}",
             f"dataset     : {ctx.meta.get('dataset', '')}",
             f"frames      : {ctx.meta.get('n_frames', '')}",
             f"config hash : {ctx.meta.get('config_hash', '')}", ""]
    if not ctx.card.empty:
        columns = [c for c in ("metric", "field", "rho_min", "worst_axis",
                               "separability_auc_min", "selectivity", "blind_axes",
                               "gaussian_impostor_damage", "gaussian_impostor_relative",
                               "cost_relative", "flags") if c in ctx.card.columns]
        lines.append(ctx.card[columns].to_string(index=False))
    if ctx.df["metric"].nunique() > 1:
        ratio, scaled = _independent_directions(ctx)
        lines += ["", f"independent directions : {_fmt(ratio)} across the {len(scaled)} "
                      "metrics with a damage scale (participation ratio)"]
    path = folder.root / "summary.txt"
    path.write_text("\n".join(lines) + "\n")
    return path


def status_line(rendered: Sequence[Rendered]) -> str:
    """How many renderers ended in each status, e.g. ``ok 30 · skipped 4``."""
    counts = Counter(item.status for item in rendered)
    return " · ".join(f"{k} {v}" for k, v in sorted(counts.items()))


# --- small helpers --------------------------------------------------------------------------


def _independent_directions(ctx: ReportContext) -> tuple[float, list[str]]:
    """The participation ratio of the metrics' damage, and the metrics with a damage scale on
    this run (any non-degenerate normalisation), which is what the ratio is quoted over."""
    ratio = an.participation_ratio_of_metrics(ctx.df, probe_labels=ctx.probe_labels)
    scaled = sorted(str(m) for m in ctx.norm.loc[~ctx.norm["degenerate"].astype(bool),
                                                  "metric"].unique())
    return ratio, scaled


def _fmt(value: object, digits: int = 2) -> str:
    try:
        v = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "--"
    return f"{v:.{digits}f}" if np.isfinite(v) else "--"


def _read_maps(path: Path) -> dict[str, np.ndarray]:
    if not path.exists():
        return {}
    with np.load(path) as archive:
        return {k: archive[k] for k in archive.files}
