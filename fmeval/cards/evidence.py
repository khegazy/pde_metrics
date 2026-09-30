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

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from fmeval import analysis as an

from .exemplars import load_cards_config, write_block
from .prose import FAMILY_HEADINGS

#: Which generated block each degradation family's results go into.
#:
#: Derived from :data:`FAMILY_HEADINGS` rather than written out again: these were two
#: hand-maintained lists of the same families, and adding a family to one and not the
#: other left its results silently ungenerated -- the card kept its "Not generated yet"
#: placeholder while `cards evidence` reported success.
FAMILY_BLOCKS = {family: f"results_{family}" for family in FAMILY_HEADINGS}

NOT_MEASURED = "No measurements for this test in the recorded run."

#: The degradation families whose per-strength damage a card sets beside the other metrics: the
#: ones where magnitude, not order, is the claim (issues/035).
DAMAGE_BLOCK_FAMILIES: tuple[str, ...] = ("geometric",)

#: The metrics a card's damage table places beside its own: the pointwise controls every
#: candidate has to be read against.
DAMAGE_BLOCK_CONTROLS: tuple[str, ...] = ("mae", "mse", "rmse", "nrmse")


@dataclass(frozen=True)
class Run:
    """One evaluation run, with the statistics derived from it."""

    folder: Path
    rows: pd.DataFrame
    meta: dict
    axes: pd.DataFrame
    probes: pd.DataFrame
    norm: pd.DataFrame
    scored: pd.DataFrame
    """The rows with ``damage`` attached."""
    card: pd.DataFrame
    """One row per metric and field, unflagged: cards never carry flags."""
    anchor_label: str = an.UNCORRELATED_LABEL
    probe_labels: frozenset[str] = an.PROBE_LABELS


def load_run(folder: Path) -> Run:
    """Read a run folder and derive every statistic a card reports.

    Args:
        folder: A ``results/<name>_<stamp>`` directory containing ``data/results.csv``.

    Returns:
        The run and its analysis.

    Raises:
        FileNotFoundError: If the folder holds no results.
        ValueError: If the run is on a dataset cards may not cite -- the dev dataset is
            the first 100 solver steps, before the flow develops, and its numbers would be
            indistinguishable once written into a card from ones that mean something.
    """
    results = folder / "data" / "results.csv"
    if not results.is_file():
        results = folder / "data" / "results.csv.gz"
    if not results.is_file():
        raise FileNotFoundError(f"{folder} has no data/results.csv")

    rows = pd.read_csv(results)
    allowed = list(load_cards_config().evidence_datasets)
    used = sorted(rows["dataset"].unique())
    forbidden = [d for d in used if d not in allowed]
    if forbidden:
        raise ValueError(
            f"{folder} is on {forbidden}, which cards may not cite; allowed: {allowed}.\n"
            "Evidence must come from a developed-flow run, not a smoke test."
        )

    meta_path = folder / "data" / "run_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.is_file() else {}
    analysis = an.analyse(rows, meta=meta)
    return Run(folder=folder, rows=rows, meta=meta, norm=analysis.norm, axes=analysis.axes,
               probes=analysis.probes, scored=analysis.scored, card=analysis.card,
               anchor_label=analysis.anchor_label, probe_labels=analysis.probe_labels)


def _cell(row: Any, column: str) -> Any:
    """A probe column that may be absent from this run's analysis.

    `probe_summary` only emits columns for the probes the ladder actually ran. A run whose
    ladder skipped the impostor -- `degradation.skip=[gaussian_impostor]`, or a custom
    ladder -- legitimately lacks those columns, and indexing them raised a bare KeyError
    that named a column instead of the situation. Absent means not measured, which
    `_fmt` renders as an em dash.
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
    """The provenance every number below it inherits."""
    meta, rows = run.meta, run.rows
    frames = sorted(rows["frame_index"].unique())
    git = meta.get("git", {})
    sha = str(git.get("sha") or git.get("commit") or "not recorded")[:12]
    dirty = " (working tree dirty)" if git.get("dirty") else ""
    return (
        f"Measured on `{rows['dataset'].iloc[0]}`, frames {frames[0]} to {frames[-1]} "
        f"({len(frames)} frames of developed flow), on the "
        f"{meta.get('analysis_grid') or 'native'} analysis grid, seed "
        f"{meta.get('seed', '—')}, at commit `{sha}`{dirty}. Run `{run.folder.name}`.\n\n"
        f"Every number in this section comes from that one run. Regenerate with "
        f"`python -m fmeval.cards evidence <name> --results {run.folder}`."
    )


def performance_block(run: Run, metric: str) -> str:
    """The summary table: how this metric behaved on every test, at a glance."""
    axes = run.axes[run.axes["metric"] == metric]
    if axes.empty:
        return NOT_MEASURED

    lines = ["| test family | field | degradations | rank correlation | weakest gap "
             "between neighbouring strengths | first strength detected |",
             "|---|---|---|---|---|---|"]
    for family, group in axes[~axes["is_probe"]].groupby("degradation_family"):
        # The same readable name the matching '### ' subsection uses, so a reader moving
        # between the summary and the detail is not asked to learn two vocabularies.
        named = FAMILY_HEADINGS.get(family, family)
        for field, sub in group.groupby("field"):
            lines.append(
                f"| {named} | {field} | {len(sub)} | "
                f"{_fmt(sub['rho'].min())} to {_fmt(sub['rho'].max())} | "
                f"{_fmt(sub['separability_auc_min'].min())} | "
                f"level {_fmt(sub['sensitivity_level'].min())} |"
            )
    probes = run.probes[run.probes["metric"] == metric]
    for _, row in probes.iterrows():
        lines.append(
            f"| trap test: fake prediction, right spectrum | {row['field']} | 1 | — | — | "
            f"damage {_fmt(_cell(row, 'gaussian_impostor_damage'))} |"
        )
    lines += [
        "",
        "One row per family of degradation and physical field. **Rank correlation** asks "
        "whether the metric put the strengths of one degradation in the right order: it "
        "is the Spearman correlation between the metric and the applied strength, "
        "computed inside a single frame, and the column gives the range over the "
        "degradations in that family. A value of 1 means every strength was ordered "
        "correctly in every frame. **Weakest gap between neighbouring strengths** asks "
        "whether the metric can tell one strength from the next: it is the smallest "
        "Mann-Whitney overlap between any two neighbouring strengths, where 1 means the "
        "two never overlap and 0.5 means the metric cannot separate them at all. "
        "**First strength detected** is the mildest strength at which the metric has "
        "moved a tenth of the way from the undegraded reference toward a field with no "
        "relation to the truth; a dash means the metric never reached that tenth. "
        "**Damage** is that same 0-to-1 scale read as a number: 0 is the undegraded "
        "reference and 1 is an unrelated field.",
        "",
        "This table reports what was measured and grades none of the measurements. What "
        "the numbers mean for this metric is written in the subsections below, beside the "
        "test that produced each number.",
    ]
    lines += _profile_lines(run, metric, axes)
    return "\n".join(lines)


def _profile_lines(run: Run, metric: str, axes: pd.DataFrame) -> list[str]:
    """The measured profile of one metric, one row per field, read from the analysis frames."""
    card = run.card[run.card["metric"] == metric].sort_values("field")
    if card.empty or "selectivity" not in card.columns:
        return []
    translation = axes[axes["degradation"] == "translate_subpixel"]
    against = ", ".join(sorted(str(x) for x in translation["elasticity_x"].dropna().unique()))
    margin, confidence = an.BLINDNESS_MARGIN, an.BLINDNESS_CONFIDENCE
    lines = [
        "", "**Profile.**", "",
        "| field | selectivity | charges most for | charges least for | response provably below "
        f"{margin:g} at {confidence:.0%} on | elasticity to a sub-pixel shift"
        f"{f' (against {against})' if against else ''} | compute cost (x cheapest in this run) |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, row in card.iterrows():
        blind = " ".join(f"`{a}`" for a in str(row.get("blind_axes") or "").split("; ") if a)
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


def damage_by_level_block(run: Run, metric: str) -> str:
    """Per-strength damage for this metric beside the pointwise controls (issues/035).

    One table per field and translation degradation, one row per metric -- this one first -- and
    one column per strength, so the magnitude claims a card makes have a generated source.
    """
    present = set(run.rows["metric"].astype(str).unique())
    others = [m for m in DAMAGE_BLOCK_CONTROLS if m in present and m != metric]
    if not others:
        return "Only one metric in the recorded run; there is nothing to place this one beside."
    lines: list[str] = []
    for family in DAMAGE_BLOCK_FAMILIES:
        for field in sorted(run.scored["field"].astype(str).unique()):
            wide = an.damage_by_level(run.scored, field=field, family=family,
                                      probe_labels=run.probe_labels)
            for degradation, block in wide.groupby("degradation", observed=True):
                block = block.sort_values("level")
                strengths = [f"{s:g}" for s in block["severity"]]
                name = str(run.rows.loc[run.rows["degradation"] == degradation,
                                        "severity_name"].iloc[0])
                lines += [f"**{FAMILY_HEADINGS.get(family, family)}, {field}, "
                          f"`{degradation}`** (strength: {name}).", "",
                          "| metric | " + " | ".join(strengths) + " |",
                          "|---" * (len(strengths) + 1) + "|"]
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
        "reference and 1 an unrelated field; a dash means no damage scale on that field. The "
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
    lines = ["| degradation | field | strengths | rank correlation | "
             "fraction of frames in the right order | weakest gap between neighbouring "
             "strengths |",
             "|---|---|---|---|---|---|"]
    for _, row in axes.sort_values(["degradation", "field"]).iterrows():
        lines.append(
            f"| `{row['degradation']}` | {row['field']} | {int(row['n_levels'])} | "
            f"{_fmt(row['rho'])} | {_fmt(row['monotone_fraction'])} | "
            f"{_fmt(row['separability_auc_min'])} |"
        )
    return "\n".join(lines)


def canaries_block(run: Run, metric: str) -> str:
    """What the metric assigns to the fake prediction and to an unrelated field."""
    probes = run.probes[run.probes["metric"] == metric]
    if probes.empty:
        return NOT_MEASURED
    lines = ["| field | damage assigned to the fake prediction | closest real degradation "
             "| value on an unrelated field |",
             "|---|---|---|---|"]
    for _, row in probes.sort_values("field").iterrows():
        nearest = _cell(row, "gaussian_impostor_nearest_level")
        lines.append(
            f"| {row['field']} | {_fmt(_cell(row, 'gaussian_impostor_damage'))} | "
            f"{'`' + str(nearest) + '`' if nearest is not None else '—'} | "
            f"{_fmt(_cell(row, f'{run.anchor_label}_value'))} |"
        )
    lines += [
        "",
        "The fake prediction here has exactly the reference field's amplitude spectrum "
        "and completely scrambled structure. Damage of 1 is what a field with no relation "
        "to the truth scores, so the damage column says how close to useless this metric "
        "considers that fake prediction: a low number means the metric was fooled. The "
        "third column translates the same number into an ordinary degradation whose "
        "damage the fake prediction matches, which is easier to picture.",
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
    lines = ["| compared with | rank correlation over every degradation |", "|---|---|"]
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
    from .loader import find_bundle

    bundle = find_bundle(metric)
    if bundle is None:
        raise KeyError(f"no metric bundle named {metric!r}")

    command = f"python -m fmeval.cards evidence {metric} --results {run.folder}"
    blocks = {
        "run": run_block(run),
        "performance": performance_block(run, metric),
        "results_canaries": canaries_block(run, metric),
        "results_summary": summary_block(run, metric),
        "results_damage_by_level": damage_by_level_block(run, metric),
    }
    for family, block in FAMILY_BLOCKS.items():
        blocks[block] = family_block(run, metric, family)

    text = bundle.card_md.read_text()
    for name, body in blocks.items():
        if f"<!-- GENERATED {name}:" in text:
            write_block(bundle.card_md, name, body, command=command)

    axes = run.axes[run.axes["metric"] == metric]
    probes = run.probes[run.probes["metric"] == metric]
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
    }
    out = bundle.path / "_generated" / "fingerprint.json"
    from .exemplars import sanitize_json

    out.write_text(
        json.dumps(sanitize_json(fingerprint), indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    )
    for stale in bundle.path.glob("_generated/results_*.md"):
        stale.unlink()
    for stale in (bundle.path / "_generated" / "performance.md",
                  bundle.path / "_generated" / "run.md"):
        stale.unlink(missing_ok=True)
    return out
