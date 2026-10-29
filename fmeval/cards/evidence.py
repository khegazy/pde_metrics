"""Turn one evaluation run into the measured half of every metric card.

Consumes a run folder rather than running the pipeline itself. The evaluation is
expensive and happens where the data lives; generating documentation from its output is
cheap and should not require repeating it. That separation also means a card's numbers
can always be traced to a named run rather than to whenever someone last regenerated.

Nothing here computes a statistic of its own. Every number comes from
:mod:`fmeval.analysis`, which is the same code the LaTeX report uses, so a card and a
report of the same run cannot disagree.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from fmeval import analysis as an
from fmeval.config import load_cards_config
from fmeval.io import COMPANIONS, read_config, read_results, read_run_meta
from fmeval.report.registry import PLOTS
from fmeval.report.vocabulary import FAMILY_INFO, family_label, label

from . import loader
from .loader import write_strict_json
from .metric_figures import FIGURE_BLOCKS, METRIC_FIGURES, CardFigure, metric_figures
from .prose import has_block, write_block

#: Which generated block each degradation family's results go into. Derived from
#: :data:`fmeval.report.vocabulary.FAMILY_INFO` rather than written out again, so a family
#: added there cannot be left with its results silently ungenerated.
FAMILY_BLOCKS = {family: f"results_{family}" for family in FAMILY_INFO}

NOT_MEASURED = "No measurements for this test in the recorded run."


@dataclass(frozen=True, kw_only=True)
class Run(an.Analysis):
    """One evaluation run: where it came from, plus every statistic :func:`an.analyse` derives."""

    folder: Path
    rows: pd.DataFrame
    meta: dict


def load_run(folder: Path) -> Run:
    """Read a run folder and derive every statistic a card reports.

    Args:
        folder: A ``results/<name>_<stamp>`` directory containing ``data/results.csv``.

    Returns:
        The run and its analysis.

    Raises:
        FileNotFoundError: If the folder holds no results.
        ValueError: If the run is on a dataset cards may not cite (not a key of
            ``evidence_datasets`` in ``configs/cards/default.yaml``) -- the dev dataset is
            the first 100 solver steps, before the flow develops, and its numbers would be
            indistinguishable once written into a card from ones that mean something.
    """
    rows = read_results(folder)
    allowed = list(load_cards_config().evidence_datasets)
    used = sorted(rows["dataset"].unique())
    forbidden = [d for d in used if d not in allowed]
    if forbidden:
        raise ValueError(
            f"{folder} is on {forbidden}, which cards may not cite; allowed: {allowed}.\n"
            "Evidence must come from a dataset listed in configs/cards/default.yaml, "
            "not a smoke test."
        )

    meta = read_run_meta(folder)
    analysis = an.analyse(rows, companions=read_results(folder, COMPANIONS, missing_ok=True),
                          meta=meta, config=read_config(folder))
    return Run(folder=folder, rows=rows, meta=meta,
               **{f.name: getattr(analysis, f.name) for f in dataclasses.fields(analysis)})


def _header(*columns: str) -> list[str]:
    """The header and separator rows of a markdown table, with the separator's width matched."""
    return ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]


def _cell(row: Any, column: str) -> Any:
    """A probe column that may be absent from this run's analysis.

    `probe_summary` only emits columns for the probes the ladder actually ran. A run whose
    ladder skipped the impostor -- `degradation.skip=[gaussian_impostor]`, or a custom
    ladder -- legitimately lacks those columns. Absent means not measured, which `_fmt`
    renders as an em dash.
    """
    return row[column] if column in row.index else None


def _fmt(value: Any, digits: int = 3) -> str:
    """A number for a table cell, or an em dash where there is none."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}g}"
    return str(value)


def run_block(run: Run) -> str:
    """The provenance every number below it inherits, and the kind of claim it supports.

    What the frames are is read from ``evidence_datasets``, so a card on a calibrated null or
    an analytic check says so in the same sentence that names the dataset.
    """
    meta, rows = run.meta, run.rows
    dataset = str(rows["dataset"].iloc[0])
    frames = sorted(rows["frame_index"].unique())
    git = meta.get("git", {})
    sha = str(git.get("sha") or "not recorded")[:12]
    dirty = " (working tree dirty)" if git.get("dirty") else ""
    return (
        f"Measured on `{dataset}`, frames {frames[0]} to {frames[-1]} "
        f"({len(frames)} frames of {load_cards_config().evidence_datasets[dataset]}), on the "
        f"{meta.get('analysis_grid') or 'native'} analysis grid, seed "
        f"{meta.get('seed', '—')}, at commit `{sha}`{dirty}. Run `{run.folder.name}`.\n\n"
        f"Every number in this section comes from that one run. Regenerate with "
        f"`python -m fmeval.cards evidence <name> --results {run.folder}`."
    )


def figure_lines(figures: Sequence[CardFigure] | None, reasons: Mapping[str, str] | None,
                 block: str = "performance") -> list[str]:
    """The image and caption for each figure of one block, or one sentence saying why it is absent.

    Images sit inside the generated block, never outside it: the card checker strips
    generated blocks before counting hand-written words, and an image outside one would be
    read as prose (`fmeval.cards.prose`). The alt text is the figure's question and the
    caption its reading, both from the renderer, so a reader of the repository on GitHub and
    a reader of the site see the same figure with the same words.
    """
    if not (figures or reasons):
        return []      # drawn without figures, e.g. from a test: no figure lines at all
    reasons = reasons or {}
    lines: list[str] = []
    by_name = {f.name: f for f in figures or ()}
    for name in METRIC_FIGURES:
        if FIGURE_BLOCKS[name] != block:
            continue
        figure = by_name.get(name)
        if figure is None:
            title = PLOTS[name].title.lower()
            lines += [f"No {title} figure: {reasons.get(name, 'not drawn')}.", ""]
            continue
        lines += [f"![{figure.alt}](_generated/{figure.path.name})", "", figure.caption, ""]
    return lines


def _span(values: pd.Series) -> str:
    """The range of a column over the rows of one table cell, or its one value, or a dash."""
    finite = values.dropna()
    if finite.empty:
        return "—"
    low, high = _fmt(float(finite.min())), _fmt(float(finite.max()))
    return low if low == high else f"{low} to {high}"


def performance_block(run: Run, metric: str, figures: Sequence[CardFigure] = (),
                      reasons: Mapping[str, str] | None = None) -> str:
    """The summary, at a glance: the figures first, then one table per measurement.

    Three measurements per degradation, none of them a grade: whether the response follows the
    degradation (trend), how far it moves (reactivity), and how much it varies from snapshot to
    snapshot (consistency). Only the first compares exactly across metrics.
    """
    axes = run.axes[run.axes["metric"] == metric]
    if axes.empty:
        return NOT_MEASURED
    ordinal = axes[~axes["is_probe"]]
    groups = [(family_label(family), field, sub)
              for family, group in ordinal.groupby("degradation_family")
              for field, sub in group.groupby("field")]
    # A run analysed before a column existed lacks it, and its cells read as a dash.
    absent = pd.Series(dtype=float)

    lines = figure_lines(figures, reasons, "performance")
    lines += ["**Trend: does the response follow the degradation?**", "",
              *_header("test family", "field", "degradations", "rank correlation",
                       "fraction of frames in order",
                       "weakest gap between neighbouring strengths")]
    for named, field, sub in groups:
        lines.append(f"| {named} | {field} | {len(sub)} | {_span(sub['rho'])} | "
                     f"{_span(sub['monotone_fraction'])} | "
                     f"{_span(sub['separability_auc_min'])} |")
    lines += ["", "**Reactivity: how far does it move?**", "",
              *_header("test family", "field", "change from clean at the harshest strength",
                       "elasticity", "first strength detected")]
    for named, field, sub in groups:
        lines.append(f"| {named} | {field} | {_span(sub.get('relative_change_max', absent))} | "
                     f"{_span(sub.get('elasticity', absent))} | "
                     f"level {_fmt(sub['sensitivity_level'].min())} |")
    probes = run.probes[run.probes["metric"] == metric]
    for _, row in probes.iterrows():
        lines.append(
            f"| trap test: fake prediction, right spectrum | {row['field']} | — | — | "
            f"damage {_fmt(_cell(row, 'gaussian_impostor_damage'))} |"
        )
    lines += ["", "**Consistency: how much does it vary from snapshot to snapshot?**", "",
              *_header("test family", "field", "consistency, in the strength's units",
                       "snapshots per independent block")]
    for named, field, sub in groups:
        lines.append(f"| {named} | {field} | {_span(sub.get('severity_resolution', absent))} | "
                     f"{_span(sub.get('blindness_block_length', absent))} |")
    no_relative = not ordinal["relative_change_max"].notna().any() \
        if "relative_change_max" in ordinal.columns else True
    lines += [
        "",
        "One row per family of degradation and physical field; a cell gives the range over "
        "the degradations in that family. **Trend.** The rank correlation is the Spearman "
        "correlation between the strength and how far the metric has moved from its value on "
        "the undegraded field of the same frame, in the one direction it moves under that "
        "degradation, computed inside a single frame. A value of 1 means every strength moved "
        "it further than the last in every frame, whichever way it moves; a response that "
        "scatters to both sides scores near 0. The fraction of frames in order counts the "
        "frames with no exception. The weakest gap is the smallest Mann-Whitney overlap between "
        "two neighbouring strengths across frames: 1 means they never overlap, 0.5 that they "
        "cannot be told apart. **Reactivity.** The change from clean is the median, at the "
        "harshest strength, of the departure from the undegraded value of the same frame over "
        "the size of that value: 0.3 means 30%. "
        + ("It does not exist for this metric, whose undegraded value is exactly zero; the "
           "damage below is its relative reading. " if no_relative else "")
        + "The elasticity is the percentage change of that departure per percentage change in "
        "strength over the mildest strengths. First strength detected is the mildest at which "
        "the metric has moved a tenth of the way to the anchor; "
        "**damage** reads that 0-to-1 scale as a number. A dash means the measurement is not "
        "defined there. A metric's reactivity scales with the power it is expressed in: mean "
        "squared error's elasticity is twice root-mean-square error's, though the two carry "
        "the same information, so compare magnitudes across metrics with that in mind. "
        "**Consistency** is how much the response varies from snapshot to snapshot relative to "
        "its size, in the strength's units; the snapshots of one trajectory are correlated, "
        "and the last column is how many consecutive snapshots one independent block spans.",
        "",
        "These tables report what was measured and grade none of the measurements. What the "
        "numbers mean for this metric is written in the subsections below, beside the test "
        "that produced each number.",
    ]
    lines += _profile_lines(run, metric, axes)
    return "\n".join(lines)


def companion_block(run: Run, metric: str) -> str:
    """The metric's curve read coordinate by coordinate, beside the panel, never inside it."""
    stats = run.companion_axes
    stats = stats[(stats["metric"].astype(str) == metric) & ~stats["is_probe"]] \
        if not stats.empty else stats
    if stats.empty:
        return NOT_MEASURED
    dominance = run.dominance[run.dominance["metric"].astype(str) == metric]
    coordinates = sorted(stats["coordinate"].unique())
    heads = [an.coordinate_label(c) for c in coordinates]
    lines = []
    for field, sub in stats.groupby("field"):
        for column, title in (("rho", "rank correlation"),
                              ("relative_change_max", "change from clean at the harshest "
                                                      "strength")):
            if not sub[column].notna().any():
                reason = (" The curve's value on the undegraded field is zero, as a comparison "
                          "curve's is, so there is no clean value to divide by."
                          if column == "relative_change_max" else "")
                lines += [f"**{field}, {title}:** not defined at any coordinate.{reason}", ""]
                continue
            wide = sub.pivot_table(index="degradation", columns="coordinate", values=column,
                                   aggfunc="first", observed=True,
                                   dropna=False).reindex(columns=coordinates)
            extra = ("dominance",) if column == "rho" else ()
            lines += [f"**{field}, {title}, at each coordinate.**", "",
                      *_header("degradation", *heads, *extra)]
            for degradation, values in wide.iterrows():
                cells = [_fmt(float(v)) for v in values]
                if extra:
                    hit = dominance[(dominance["field"].astype(str) == field)
                                    & (dominance["degradation"].astype(str) == degradation)]
                    cells.append(_fmt(float(hit["dominance_min"].iloc[0])) if len(hit) else "—")
                lines.append(f"| `{degradation}` | " + " | ".join(cells) + " |")
            lines.append("")
    lines.append(
        "Each coordinate of the curve read as a metric of its own, with the same statistics as "
        "the tables above and no resampling interval. Neighbouring coordinates are strongly "
        "correlated, so a row localises the evidence and does not multiply it. **Dominance** "
        "is the fraction of frames in which, for the weakest pair of neighbouring strengths, the "
        "harsher strength's curve has moved at least as far as the milder one's at every "
        "coordinate, each in its own direction: near 1, any summary that grows with every "
        "coordinate's departure orders those strengths the same way, so the choice of summary "
        "cannot change the trend. None of these numbers enters the tables above."
    )
    return "\n".join(lines)


def _profile_lines(run: Run, metric: str, axes: pd.DataFrame) -> list[str]:
    """The measured profile of one metric, one row per field, read from the analysis frames."""
    card = run.card[run.card["metric"] == metric].sort_values("field")
    if card.empty or "selectivity" not in card.columns:
        return []
    translation = axes[axes["degradation"] == an.DISPLACEMENT_AXIS]
    against = ", ".join(sorted(str(x) for x in translation["elasticity_x"].dropna().unique()))
    margin, confidence = an.BLINDNESS_MARGIN, an.BLINDNESS_CONFIDENCE
    lines = ["", "**Profile.**", "", *_header(
        "field", "selectivity", label("most_sensitive_axis"), label("least_sensitive_axis"),
        f"response provably below {margin:g} at {confidence:.0%} on",
        f"{label('elasticity_displacement')}{f', against {against}' if against else ''}",
        "compute cost (x cheapest in this run)")]
    for _, row in card.iterrows():
        blind = " ".join(f"`{a}`" for a in an.split_blind(row.get("blind_axes")))
        most, least = row.get("most_sensitive_axis"), row.get("least_sensitive_axis")
        lines.append(
            f"| {row['field']} | {_fmt(row.get('selectivity'))} | "
            f"{f'`{most}`' if isinstance(most, str) else '—'} | "
            f"{f'`{least}`' if isinstance(least, str) else '—'} | {blind or '—'} | "
            f"{_fmt(row.get('elasticity_displacement'))} | {_fmt(row.get('cost_relative'))} |"
        )
    lines += [
        "",
        "One row per physical field. **Selectivity** is how concentrated the metric's response "
        "is on a few degradations, measured per unit of field change: 0 means it charges every "
        "degradation the same, as mean squared error does by construction, and values toward 1 "
        "that one degradation carries most of it. **Charges most and least for** name the two "
        "ends of that profile. **Response provably below** lists degradations on which the upper "
        "confidence bound of the largest damage lies below the margin -- an equivalence test, so "
        "an entry says the response is provably small, not merely not significant; a dash means "
        "no degradation met the bound. **Elasticity** is the slope of log damage against log "
        "shift over the smallest shifts: 1 means damage grows in proportion to the shift, 2 with "
        "its square. **Compute cost** is wall-clock per evaluation over the cheapest metric and "
        "field in the same run.",
    ]
    return lines


def damage_by_level_block(run: Run, metric: str, figures: Sequence[CardFigure] = (),
                          reasons: Mapping[str, str] | None = None) -> str:
    """Per-strength damage for this metric beside the pointwise controls.

    The figure of those numbers first, then one table per field and translation degradation,
    one row per metric -- this one first -- and one column per strength, so the magnitude
    claims a card makes have a generated source.
    """
    present = set(run.rows["metric"].astype(str).unique())
    others = [m for m in an.DAMAGE_BLOCK_CONTROLS if m in present and m != metric]
    if not others:
        return "Only one metric in the recorded run; there is nothing to place this one beside."
    lines = figure_lines(figures, reasons, "results_damage_by_level")
    for family in an.DAMAGE_BLOCK_FAMILIES:
        for field in sorted(run.scored["field"].astype(str).unique()):
            wide = an.damage_by_level(run.scored, field=field, family=family,
                                      probe_labels=run.probe_labels)
            for degradation, block in wide.groupby("degradation", observed=True):
                block = block.sort_values("level")
                strengths = [f"{s:g}" for s in block["severity"]]
                name = str(run.rows.loc[run.rows["degradation"] == degradation,
                                        "severity_name"].iloc[0])
                lines += [f"**{family_label(family)}, {field}, "
                          f"`{degradation}`** (strength: {name}).", "",
                          *_header("metric", *strengths)]
                for m in (metric, *others):
                    cells = (block[m].to_numpy(float) if m in block.columns
                             else [float("nan")] * len(strengths))
                    lines.append(f"| `{m}` | " + " | ".join(_fmt(float(v)) for v in cells) + " |")
                lines.append("")
    if not lines:
        return NOT_MEASURED
    lines.append(
        "Median damage over frames at every strength, this metric in the first row and the "
        "pointwise controls beneath it, all on the same 0-to-1 scale where 0 is the undegraded "
        "reference and 1 the anchor (by default the field's own mean); a dash means no damage "
        "scale on that field. The "
        "rank correlations under *Compared with the other metrics* say whether two metrics put "
        "the strengths in the same order; this table says how much each one charges for the same "
        "strength, which decides whether two metrics are interchangeable as training losses."
    )
    return "\n".join(lines)


def family_block(run: Run, metric: str, family: str) -> str:
    """One family's numbers, one row per degradation and physical field."""
    axes = run.axes[(run.axes["metric"] == metric)
                    & (run.axes["degradation_family"] == family)
                    & (~run.axes["is_probe"])]
    if axes.empty:
        return NOT_MEASURED
    lines = _header("degradation", "field", "strengths", "rank correlation",
                    "fraction of frames in the right order",
                    "weakest gap between neighbouring strengths")
    for _, row in axes.sort_values(["degradation", "field"]).iterrows():
        lines.append(
            f"| `{row['degradation']}` | {row['field']} | {int(row['n_levels'])} | "
            f"{_fmt(row['rho'])} | {_fmt(row['monotone_fraction'])} | "
            f"{_fmt(row['separability_auc_min'])} |"
        )
    return "\n".join(lines)


def canaries_block(run: Run, metric: str) -> str:
    """What the metric assigns to the fake prediction, to the reference moved far away, and to
    the anchor."""
    probes = run.probes[run.probes["metric"] == metric]
    if probes.empty:
        return NOT_MEASURED
    lines = _header("field", "damage assigned to the fake prediction",
                    "closest real degradation", "damage of the reference moved far away",
                    "value on the anchor")
    for _, row in probes.sort_values("field").iterrows():
        nearest = _cell(row, "gaussian_impostor_nearest_level")
        lines.append(
            f"| {row['field']} | {_fmt(_cell(row, 'gaussian_impostor_damage'))} | "
            f"{'`' + nearest + '`' if isinstance(nearest, str) and nearest else '—'} | "
            f"{_fmt(_cell(row, f'{an.UNCORRELATED_LABEL}_damage'))} | "
            f"{_fmt(_cell(row, f'{run.anchor_label}_value'))} |"
        )
    lines += [
        "",
        "The fake prediction here has exactly the reference field's amplitude spectrum "
        "and completely scrambled structure. Damage 1 is what the anchor scores, by default "
        "the reference's own spatial mean, a prediction that knows the mean and nothing else. "
        "The damage column therefore says how close to useless this metric considers that "
        "fake prediction: a low number means the metric was fooled. The third column "
        "translates the same number into an ordinary degradation whose damage the fake "
        "prediction matches, which is easier to picture. The fourth is the reference moved by "
        "a large random offset, the right statistics in the wrong place; where a field's "
        "energy sits in its largest scales that copy stays partly correlated with the "
        "reference, so it is not the score of an unrelated field.",
    ]
    return "\n".join(lines)


def summary_block(run: Run, metric: str) -> str:
    """What holds across every degradation: how this metric relates to the others.

    ``cross_metric_correlation`` returns a square matrix indexed by metric, so the row
    for this metric is read and the self-correlation dropped.
    """
    matrix = an.cross_metric_correlation(run.rows)
    if matrix.empty or metric not in matrix.columns:
        return NOT_MEASURED

    row = matrix.loc[metric].drop(labels=[metric], errors="ignore").sort_values(ascending=False)
    lines = _header("compared with", "rank correlation over every degradation")
    for other, value in row.items():
        lines.append(f"| `{other}` | {_fmt(float(value))} |")
    lines += [
        "",
        "Computed on the median value at each combination of degradation and strength, "
        "over every degradation and physical field in the run, with the undegraded "
        "reference excluded. Two metrics correlating near 1 put the degradations in the "
        "same order, but the two may still weight those degradations very differently. "
        "A correlation near 1 therefore means the two metrics are redundant for ranking "
        "models, not that the two are interchangeable as training losses.",
    ]
    return "\n".join(lines)


def generate(metric: str, run: Run) -> Path:
    """Write every generated block of one metric's card, and its fingerprint.

    Args:
        metric: The metric bundle to fill in.
        run: The run to take every number from.

    Returns:
        The path to the written fingerprint.

    Raises:
        KeyError: If the bundle does not exist, or its card lacks a block the generator
            writes -- which means the card and the generator disagree about what is
            generated.
    """
    # Looked up through the module, so a test that substitutes `loader.find_bundle` with a
    # throwaway copy keeps the generator away from the tracked bundle.
    bundle = loader.find_bundle(metric)
    if bundle is None:
        raise KeyError(f"no metric bundle named {metric!r}")

    command = f"python -m fmeval.cards evidence {metric} --results {run.folder}"
    # Figures first, so a figure that cannot be drawn is reported inside the block that
    # would have shown it rather than discovered as a missing file.
    figures, reasons = metric_figures(run, metric, bundle.generated)
    blocks = {
        "run": run_block(run),
        "performance": performance_block(run, metric, figures, reasons),
        "results_canaries": canaries_block(run, metric),
        "results_summary": summary_block(run, metric),
        "results_damage_by_level": damage_by_level_block(run, metric, figures, reasons),
        "results_companion": companion_block(run, metric),
    }
    for family, block in FAMILY_BLOCKS.items():
        blocks[block] = family_block(run, metric, family)

    text = bundle.card_md.read_text()
    for name, body in blocks.items():
        if has_block(text, name):
            write_block(bundle.card_md, name, body, command=command)

    axes = run.axes[run.axes["metric"] == metric]
    probes = run.probes[run.probes["metric"] == metric]
    curve = (run.companion_axes[run.companion_axes["metric"].astype(str) == metric]
             if not run.companion_axes.empty else run.companion_axes)
    dominance = (run.dominance[run.dominance["metric"].astype(str) == metric]
                 if not run.dominance.empty else run.dominance)
    fingerprint = {
        "metric": metric,
        "dataset": str(run.rows["dataset"].iloc[0]),
        "run": run.folder.name,
        "frames": sorted(int(f) for f in run.rows["frame_index"].unique()),
        "seed": run.meta.get("seed"),
        "analysis_grid": run.meta.get("analysis_grid"),
        "git": run.meta.get("git", {}),
        "axes": json.loads(axes.to_json(orient="records")),
        "probes": json.loads(probes.to_json(orient="records")),
        "profile": json.loads(run.card[run.card["metric"] == metric].to_json(orient="records")),
        **({"companion": json.loads(curve.to_json(orient="records")),
            "dominance": json.loads(dominance.to_json(orient="records"))}
           if not curve.empty else {}),
    }
    write_strict_json(bundle.fingerprint, fingerprint)
    return bundle.fingerprint
