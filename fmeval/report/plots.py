"""Figure renderers.

Each answers one question from the report narrative, and each is registered with the
section it belongs to. Two conventions recur because their absence produces figures that
mislead rather than merely disappoint:

* **Field images share colour limits** across a whole figure. Autoscaling each panel makes
  a heavily smoothed field look identical to the reference.
* **No axes carries twenty series.** Where a ladder has many axes the figure facets by
  axis, with hue for the axis and lightness for the severity level within it.
"""

from __future__ import annotations

import textwrap

import matplotlib
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from matplotlib.ticker import LogLocator, MaxNLocator, NullFormatter

from fmeval.analysis import BLINDNESS_MARGIN, DEGENERATE_SPAN, UNCORRELATED_LABEL

from .context import FigureItem, PlotResult
from .registry import plot
from .style import (
    LINE_STYLES,
    family_colour,
    field_marker,
    okabe,
    show_field,
    symmetric_limits,
)
from .vocabulary import FAMILY_LABELS
from .vocabulary import label as word


def _axis_frame(df: pd.DataFrame, axis: str) -> pd.DataFrame:
    return df[(df["degradation"] == axis) & (df["level"] > 0)]


def _median_by_level(df: pd.DataFrame, column: str = "value") -> pd.DataFrame:
    return (
        df.groupby(["level", "severity"], observed=True)[column]
        .agg(median="median", lo=lambda s: s.quantile(0.25),
             hi=lambda s: s.quantile(0.75))
        .reset_index()
        .sort_values("level")
    )


# --- section 3: does it see damage? ------------------------------------------------------


@plot(
    section=3, order=10, scope="per_metric_field",
    title="Response to each degradation",
    requires_columns=("degradation", "level", "value"),
    defaults={"logy": "auto", "band": True},
)
def ladder_curves(ctx, df, opts) -> PlotResult:
    """Metric value against severity level, one line per ladder axis, with an interquartile band.

    The curve the rank correlation summarises. A flat line means the metric does not see
    that failure mode at all; a curve that jumps to its maximum at severity level 1 has no resolving
    power in the regime that matters.
    """
    metric, field = str(df["metric"].iloc[0]), str(df["field"].iloc[0])
    axes_present = [a for a in ctx.ordinal_axes if a in set(df["degradation"])]
    ctx.require(bool(axes_present), "no ordinal ladder axes")

    fig, grid = ctx.style.figure(1, 1)
    ax = grid[0, 0]
    tidy = []
    for name in axes_present:
        stats = _median_by_level(_axis_frame(df, name))
        if stats.empty:
            continue
        colour = ctx.style.axis_colour(name)
        ax.plot(stats["level"], stats["median"], marker="o", ms=3.5,
                color=colour, ls=ctx.style.axis_style(name), label=ctx.label(name))
        if opts.get("band"):
            ax.fill_between(stats["level"], stats["lo"], stats["hi"],
                            color=colour, alpha=0.15, lw=0)
        stats.insert(0, "degradation", name)
        tidy.append(stats)

    anchor = df[df["degradation"] == ctx.anchor_label]
    if not anchor.empty:
        ax.axhline(float(anchor["value"].median()), color="0.4", ls=":", lw=1)
        text = (" unrelated fields" if ctx.anchor_label == UNCORRELATED_LABEL
                else f" {ctx.label(ctx.anchor_label)} (damage 1)")
        ax.text(0.99, float(anchor["value"].median()), text,
                transform=ax.get_yaxis_transform(), va="bottom", ha="right",
                fontsize="x-small", color="0.4")

    ax.set_xlabel("severity level (0 = reference)")
    ax.set_ylabel(f"{metric} [{_units(ctx, metric)}]")
    ax.set_title(f"{metric} on {field}")
    if _use_log(df["value"], opts.get("logy")):
        ax.set_yscale("log")
    ax.legend(fontsize="x-small", ncol=2)

    return PlotResult(
        [FigureItem(fig, {"metric": metric, "field": field},
                    caption=f"{metric} against severity_level for each ladder axis, on {field}. "
                            "Line is the median over frames, band the interquartile "
                            "range. The dotted line marks the value two statistically "
                            "identical but positionally unrelated fields receive.",
                    data=pd.concat(tidy, ignore_index=True) if tidy else None)]
    )


# --- the response at a glance: the two figures every metric card opens with -----------------
#
# Both are `per_metric`, so the LaTeX report draws one per metric and the card generator
# (fmeval.cards.metric_figures) draws the one its card needs through the same function. The
# subset `df` is one metric's rows; `ctx.axes`, `ctx.card` and `ctx.probes` are the whole
# run's and are filtered here, because `iter_scope` subsets only the tidy frame.


def _metric_rows(ctx, df: pd.DataFrame):
    """The metric a per-metric subset holds, with its ordinal axes, card and probe rows."""
    metric = str(df["metric"].iloc[0])
    axes = ctx.axes[(ctx.axes["metric"].astype(str) == metric) & ~ctx.axes["is_probe"]]
    card = (ctx.card[ctx.card["metric"].astype(str) == metric]
            if "metric" in ctx.card.columns else ctx.card)
    probes = (ctx.probes[ctx.probes["metric"].astype(str) == metric]
              if "metric" in ctx.probes.columns else ctx.probes)
    return metric, axes, card, probes


def _blind_pairs(card: pd.DataFrame) -> set[tuple[str, str]]:
    """``(field, degradation)`` pairs the card lists as a provably small response."""
    pairs: set[tuple[str, str]] = set()
    if "blind_axes" not in card.columns:
        return pairs
    for _, row in card.iterrows():
        listed = row.get("blind_axes")
        if isinstance(listed, str):
            pairs.update((str(row["field"]), axis) for axis in listed.split("; ") if axis)
    return pairs


def _impostor_damage(probes: pd.DataFrame) -> dict[str, float]:
    """Median damage of the fake prediction per field, where the ladder ran it.

    The column itself may be absent: `probe_summary` emits columns only for probes the run
    contained, so a ladder that skipped the impostor has no such column at all.
    """
    if "gaussian_impostor_damage" not in probes.columns:
        return {}
    values = {str(r.field): float(r.gaussian_impostor_damage) for r in probes.itertuples()}
    return {f: v for f, v in values.items() if np.isfinite(v)}


def _family_order(frame: pd.DataFrame) -> list[str]:
    """Families in the card's fixed order, then any the vocabulary does not know, by name."""
    present = set(frame["degradation_family"].astype(str))
    known = [f for f in FAMILY_LABELS if f in present]
    return known + sorted(present - set(FAMILY_LABELS))


def _raw_value_axis(ax, panel: pd.DataFrame) -> None:
    """Scale a panel that shows raw values because the field has no damage scale.

    An axis the metric is invariant to varies only in the last bits -- `np.roll` cannot
    change enstrophy but does change the summation order -- and autoscaling would stretch
    that round-off across the whole panel under an offset label like ``1e-19+3.078e-6``.
    The analysis withholds `rho` on such an axis (``DEGENERATE_SPAN``); the figure says the
    same thing in words and keeps the panel flat.
    """
    values = panel["value_median"].to_numpy(float)
    values = values[np.isfinite(values)]
    ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, 3), useOffset=False)
    if len(values) == 0:
        return
    scale = float(np.max(np.abs(values)))
    if scale > 0 and float(np.ptp(values)) <= DEGENERATE_SPAN * scale:
        centre = float(np.median(values))
        ax.set_ylim(centre - 0.05 * abs(centre), centre + 0.05 * abs(centre))
        ax.text(0.5, 0.85, "unchanged to round-off", transform=ax.transAxes, ha="center",
                va="center", fontsize="x-small", color="0.4")


@plot(
    section=3, order=15, scope="per_metric",
    title="Response to each family of degradation",
    requires_columns=("damage", "degradation", "level"), min_axes=1,
    defaults={"clip": 2.0, "band": False},
)
def response_curves(ctx, df, opts) -> PlotResult:
    """Median damage against severity level, one panel per degradation family and field.

    The question a reader asks first -- where does this metric start to move, how fast, and
    does it level off -- answered by position on one shared 0-to-1 scale rather than by a
    table. Faceted by family (rows) and field (columns) so no panel carries more than a few
    curves: twelve overlaid curves with bands is a spaghetti plot, and small multiples on a
    common scale are what let onset and saturation be compared across panels (Tufte 2006,
    *Beautiful Evidence*; Cleveland & McGill 1984, *J. Am. Stat. Assoc.* 79(387):531-554).

    Conventions, each printed in the caption: the solid grey line is damage 1, an unrelated
    field; the dotted black line is the fake prediction with the right spectrum; the hollow
    black ring is the first level at which the metric has moved a tenth of the way to an
    unrelated field; hollow grey markers are levels excluded for repeating a milder one or
    doing nothing; a field with no damage scale shows the raw value on a grey panel instead.
    """
    from fmeval.analysis import per_level_response

    metric, axes, _card, probes = _metric_rows(ctx, df)
    curve = per_level_response(df, metric=metric, probe_labels=ctx.probe_labels)
    ctx.require(not curve.empty, "no ordinal ladder axes")
    families = _family_order(curve)
    fields = sorted(str(f) for f in curve["field"].unique())
    clip = float(opts["clip"])
    scaled = {f: bool(curve.loc[curve["field"] == f, "damage_median"].notna().any())
              for f in fields}
    onset = {(str(r.field), str(r.degradation)): float(r.sensitivity_level)
             for r in axes.itertuples()} if "sensitivity_level" in axes.columns else {}
    impostor = _impostor_damage(probes)

    # One y-range for every panel that has a damage scale, so a curve's height means the same
    # thing in every panel. Capped at `clip`; points above it are drawn as triangles.
    on_scale = pd.concat([curve.loc[curve["field"] == f, "damage_median"]
                          for f in fields if scaled[f]] or [pd.Series(dtype=float)])
    top = max(1.1, min(clip, float(np.nanmax([*on_scale.to_numpy(float), *impostor.values(),
                                               1.0])) * 1.08))

    fig, grid = ctx.style.figure(
        len(families), len(fields),
        w=min(ctx.style.panel_w * len(fields) + 1.9, ctx.style.max_size),
        h=min(0.72 * ctx.style.panel_h * len(families) + 0.9, ctx.style.max_size),
    )
    tidy = curve.copy()
    tidy["has_scale"] = tidy["field"].map(scaled)
    tidy["impostor_damage"] = tidy["field"].map(impostor).astype(float)
    tidy["onset_level"] = [onset.get((str(f), str(d)), np.nan)
                           for f, d in zip(tidy["field"], tidy["degradation"])]

    for i, family in enumerate(families):
        colour = family_colour(family)
        names = sorted(curve.loc[curve["degradation_family"] == family, "degradation"]
                       .astype(str).unique())
        for j, field in enumerate(fields):
            ax = grid[i, j]
            has_scale = scaled[field]
            column = "damage_median" if has_scale else "value_median"
            if not has_scale:
                ax.set_facecolor("0.93")
            for k, name in enumerate(names):
                block = curve[(curve["field"] == field) & (curve["degradation"] == name)]
                block = block.sort_values("level")
                if block.empty:
                    continue
                usable = block[~block["severity_degenerate"]]
                dropped = block[block["severity_degenerate"]]
                x = usable["level"].to_numpy(int)
                y = usable[column].to_numpy(float)
                shown = np.minimum(y, clip) if has_scale else y
                ax.plot(x, shown, color=colour, marker="o", ms=3,
                        ls=LINE_STYLES[k % len(LINE_STYLES)] if len(x) > 3 else "none",
                        lw=1.1, label=ctx.label(name))
                if has_scale and opts.get("band"):
                    ax.fill_between(x, np.minimum(usable["damage_q25"].to_numpy(float), clip),
                                    np.minimum(usable["damage_q75"].to_numpy(float), clip),
                                    color=colour, alpha=0.15, lw=0)
                if has_scale and (y > clip).any():
                    ax.plot(x[y > clip], shown[y > clip], "^", color=colour, ms=4.5)
                if not dropped.empty:
                    ax.plot(dropped["level"].to_numpy(int),
                            np.minimum(dropped[column].to_numpy(float), clip) if has_scale
                            else dropped[column].to_numpy(float),
                            "o", mfc="none", mec="0.55", ms=3.5, ls="none")
                first = onset.get((field, name), np.nan)
                if has_scale and np.isfinite(first) and int(first) in set(x):
                    ax.plot(first, shown[list(x).index(int(first))], "o", mfc="none",
                            mec="black", mew=1.1, ms=7.5, ls="none", zorder=4)
            if has_scale:
                ax.axhline(1.0, color="0.3", lw=0.9)
                if field in impostor:
                    ax.axhline(min(impostor[field], clip), color="black", ls=":", lw=1.0)
                ax.set_ylim(-0.04 * top, top)
            else:
                _raw_value_axis(ax, curve[(curve["field"] == field)
                                          & (curve["degradation_family"] == family)])
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            if i == 0:
                ax.set_title(field if has_scale else f"{field}\n(no damage scale: raw value)",
                             fontsize="small")
            if i == len(families) - 1:
                ax.set_xlabel(word("level"), fontsize="small")
            ax.tick_params(labelsize="x-small")
        grid[i, 0].set_ylabel(FAMILY_LABELS.get(family, family), fontsize="small")
        grid[i, -1].legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize="x-small",
                           frameon=False, title=None)
    any_scale = any(scaled.values())
    fig.supylabel(word("damage") if any_scale else f"{word('value')} (no damage scale)",
                  fontsize="small")
    fig.suptitle(f"{metric}: median {'damage' if any_scale else 'value'} over frames against "
                 "severity level", fontsize="medium")

    unscaled = [f for f in fields if not scaled[f]]
    caption = (
        f"Median damage over frames against severity level for {metric}, one row per family "
        "of degradation and one column per field, on one shared scale. The solid grey line is "
        "damage 1, an unrelated field; the dotted black line is the damage assigned to the fake "
        "prediction with the right spectrum, where the run included it. The hollow black ring "
        "marks the first level at which the metric has moved a tenth of the way to an unrelated "
        "field. Hollow grey markers are strengths excluded for repeating a milder one or for "
        "doing nothing. Degradations with three or fewer usable levels are drawn as markers "
        f"only; points above {clip:g} are drawn as triangles at the top."
        + (f" No damage scale on {', '.join(unscaled)}: the grey panels show the raw value "
           "instead." if unscaled else "")
    )
    return PlotResult([FigureItem(fig, {"metric": metric}, caption=caption, data=tidy)])


#: The four statistics the profile draws, with the x-range of each panel. ``None`` means the
#: range follows the data; ``"log"`` a logarithmic axis.
_PROFILE_PANELS: tuple[tuple[str, object], ...] = (
    ("rho", (-1.05, 1.05)),
    ("cliffs_delta_min", (-1.05, 1.05)),
    ("damage_per_change", "log"),
    ("damage_max_ucb", None),
)


@plot(
    section=2, order=20, scope="per_metric",
    title="Sensitivity profile",
    requires_columns=("damage", "degradation", "level"), min_axes=1,
)
def sensitivity_profile(ctx, df, opts) -> PlotResult:
    """Four per-degradation statistics on aligned rows: ordering, separation, charge, blindness.

    A Cleveland dot plot (Cleveland 1985, *The Elements of Graphing Data*): one row per
    degradation, grouped by family, and one marker per field, so every statistic is read by
    position on a common scale. Panels: the rank correlation with its resampling interval; the
    separation of neighbouring strengths as Cliff's delta, with Vargha and Delaney's anchors
    as faint ticks for scale and not as grades; the damage charged per unit of field change,
    on a log axis because it spans decades; and the upper confidence bound on the largest
    damage beside the fixed margin below which a response counts as provably small.

    A hollow marker, in every panel, is a field and degradation the card lists under
    "response provably below the margin". That is a measured equivalence-test outcome the
    Profile table already prints, drawn rather than graded. Sits in the headline section
    because it is the one figure that summarises every axis of one metric.
    """
    ctx.require("cliffs_delta_min" in ctx.axes.columns,
                "this run's analysis has no response statistics")
    metric, axes, card, _probes = _metric_rows(ctx, df)
    ordinal = set(df.loc[(df["level"] > 0) & ~df["degradation"].isin(ctx.probe_labels),
                         "degradation"].astype(str))
    rows = axes[axes["degradation"].astype(str).isin(ordinal)]
    ctx.require(not rows.empty, f"no ordinal axes for {metric}")

    families = _family_order(rows)
    order = [d for family in families
             for d in sorted(rows.loc[rows["degradation_family"] == family, "degradation"]
                             .astype(str).unique())]
    position = {d: len(order) - 1 - i for i, d in enumerate(order)}
    fields = sorted(str(f) for f in rows["field"].unique())
    blind = _blind_pairs(card)

    fig, grid = ctx.style.figure(1, len(_PROFILE_PANELS), sharey=True,
                                 w=min(2.3 * len(_PROFILE_PANELS) + 1.8, ctx.style.max_size),
                                 h=min(0.34 * len(order) + 1.9, ctx.style.max_size))
    tidy = []
    for p, (column, span) in enumerate(_PROFILE_PANELS):
        ax = grid[0, p]
        values = rows[column].to_numpy(float) if column in rows.columns else np.array([])
        if span == "log":
            positive = values[np.isfinite(values) & (values > 0)]
            # A log axis only earns its place over a decade or more; under that, matplotlib's
            # minor labels pile up ("4x10^-1 5x10^-1 ...") and a linear axis reads better.
            if len(positive) and positive.max() / positive.min() >= 10:
                ax.set_xscale("log")
                ax.xaxis.set_major_locator(LogLocator(numticks=5))
                ax.xaxis.set_minor_formatter(NullFormatter())
        for r in rows.itertuples():
            x = float(getattr(r, column, np.nan)) if column in rows.columns else np.nan
            y = position[str(r.degradation)]
            colour = family_colour(str(r.degradation_family))
            hollow = (str(r.field), str(r.degradation)) in blind
            if not np.isfinite(x) or (span == "log" and x <= 0 and ax.get_xscale() == "log"):
                continue
            if column == "rho":
                lo = float(getattr(r, "rho_ci_lo", np.nan))
                hi = float(getattr(r, "rho_ci_hi", np.nan))
                if np.isfinite(lo) and np.isfinite(hi):
                    ax.hlines(y, lo, hi, color=colour, lw=0.9, alpha=0.6, zorder=1)
            ax.plot(x, y, marker=field_marker(fields.index(str(r.field))), ms=5.5, ls="none",
                    color=colour, mfc="none" if hollow else colour, mew=1.1, zorder=3)
        if isinstance(span, tuple):
            ax.set_xlim(*span)
        if not np.isfinite(values).any():
            # An empty panel reads as a missing figure; a sentence reads as a measurement.
            ax.text(0.5, 0.5, "not defined\nfor this metric", transform=ax.transAxes,
                    ha="center", va="center", fontsize="x-small", color="0.45")
        if column in ("rho", "cliffs_delta_min"):
            ax.axvline(0.0, color="0.3", lw=0.8)
        if column == "cliffs_delta_min":
            for anchor in _DELTA_ANCHORS:
                ax.axvline(anchor, color="0.8", lw=0.6, ls=":")
                ax.axvline(-anchor, color="0.8", lw=0.6, ls=":")
        if column == "damage_max_ucb":
            ax.axvline(BLINDNESS_MARGIN, color="0.3", lw=0.9, ls="--")
            ax.text(BLINDNESS_MARGIN, len(order) - 0.45, f" margin {BLINDNESS_MARGIN:g}",
                    fontsize="xx-small", color="0.3", va="bottom", ha="left")
            ax.set_xlim(left=0.0)
        ax.set_title(textwrap.fill(word(column), 30), fontsize="x-small")
        ax.tick_params(labelsize="x-small")
    grid[0, 0].set_yticks([position[d] for d in order], [ctx.label(d) for d in order],
                          fontsize="x-small")
    grid[0, 0].set_ylim(-0.7, len(order) - 0.3)
    for r in rows.itertuples():
        tidy.append({
            "metric": metric, "field": str(r.field), "degradation": str(r.degradation),
            "degradation_family": str(r.degradation_family),
            **{c: float(getattr(r, c, np.nan)) for c in
               ("rho", "rho_ci_lo", "rho_ci_hi", "cliffs_delta_min", "damage_per_change",
                "damage_max_ucb", "blindness_q", "n_levels")},
            "blind": (str(r.field), str(r.degradation)) in blind,
        })

    handles = [Line2D([], [], marker=field_marker(i), ls="none", color="0.3", ms=5.5, label=f)
               for i, f in enumerate(fields)]
    handles.append(Line2D([], [], marker="o", ls="none", color="0.3", mfc="none", ms=5.5,
                          label=word("blind_axes")))
    fig.legend(handles=handles, loc="outside lower center", ncol=len(handles),
               fontsize="x-small", frameon=False)
    fig.suptitle(f"{metric}: how it responded to each degradation, by field", fontsize="medium")

    caption = (
        f"Four measured statistics for {metric}, one row per degradation grouped by family and "
        "one marker per field. From left: the rank correlation between the metric and the "
        "applied strength within a frame, with the line showing the resampling interval; the "
        "separation of neighbouring strengths as Cliff's delta, where 0 means the metric "
        "cannot tell one strength from the next and the faint ticks at 0.12, 0.28 and 0.42 are "
        "Vargha and Delaney's small, medium and large anchors, for scale and not as grades; the "
        "damage charged per unit of field change at the harshest strength; and the upper "
        f"confidence bound on the largest damage, beside the fixed margin of {BLINDNESS_MARGIN:g}. "
        "A hollow marker is a field and degradation on which that bound lies below the margin, "
        "so the response is provably small. A missing marker is a statistic the analysis "
        "withheld, as the rank correlation is on an axis the metric is invariant to."
    )
    return PlotResult([FigureItem(fig, {"metric": metric}, caption=caption,
                                  data=pd.DataFrame(tidy))])


# --- section 4: is the response reliable? --------------------------------------------------


@plot(
    section=4, order=10, scope="per_field",
    title="Rank correlation per axis",
    requires_columns=("degradation", "level", "value"), min_axes=1,
)
def monotonicity_heatmap(ctx, df, opts) -> PlotResult:
    """Spearman correlation for every metric against every ladder axis.

    Read down a column for whether one metric is monotone; read across a row for the
    selectivity profile -- what that metric actually detects. Hatched cells fall below the
    configured reference value.
    """
    field = str(df["field"].iloc[0])
    rows = ctx.axes[(ctx.axes["field"] == field) & (~ctx.axes["is_probe"])]
    ctx.require(not rows.empty, f"no ordinal axes for {field}")
    grid_df = rows.pivot_table(index="metric", columns="degradation", values="rho",
                               observed=True)
    ctx.require(grid_df.size > 0, "empty correlation grid")

    fig, axgrid = ctx.style.figure(
        1, 1,
        w=max(3.5, 0.9 * grid_df.shape[1] + 1.6),
        h=max(2.0, 0.42 * len(grid_df) + 1.4),
    )
    ax = axgrid[0, 0]
    image = ax.imshow(grid_df.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(grid_df.shape[1]))
    ax.set_xticklabels([ctx.label(c) for c in grid_df.columns], rotation=40, ha="right")
    ax.set_yticks(range(len(grid_df)))
    ax.set_yticklabels(list(grid_df.index))
    ax.grid(False)

    limit = float(ctx.thresholds.get("spearman", np.nan))
    for i, metric in enumerate(grid_df.index):
        for j, axis in enumerate(grid_df.columns):
            value = grid_df.iloc[i, j]
            if not np.isfinite(value):
                continue
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize="xx-small",
                    color="white" if abs(value) > 0.6 else "black")
            if np.isfinite(limit) and value < limit:
                ax.add_patch(
                    __import__("matplotlib").patches.Rectangle(
                        (j - 0.5, i - 0.5), 1, 1, fill=False, hatch="///",
                        edgecolor="black", lw=1.2)
                )
    fig.colorbar(image, ax=ax, label="Spearman correlation", shrink=0.85)
    ax.set_title(f"Rank correlation with severity — {field}")

    return PlotResult(
        [FigureItem(fig, {"field": field},
                    caption=f"Spearman correlation between severity_level and metric value on "
                            f"{field}, computed within each ladder axis. Hatched cells "
                            f"fall below the reference value of {limit:g}.",
                    data=grid_df.reset_index())]
    )


# --- section 5: separability ---------------------------------------------------------------


@plot(
    section=5, order=10, scope="per_metric_field",
    title="Distribution of each severity level over time",
    requires_columns=("degradation", "level", "value"), min_frames=4,
)
def severity_level_separation(ctx, df, opts) -> PlotResult:
    """Spread of each severity level's values across frames, as violins grouped by axis.

    Where adjacent violins overlap, the metric cannot distinguish two models one severity level
    apart however clean its median curve looks.
    """
    metric, field = str(df["metric"].iloc[0]), str(df["field"].iloc[0])
    axes_present = [a for a in ctx.ordinal_axes if a in set(df["degradation"])]
    ctx.require(bool(axes_present), "no ordinal ladder axes")

    # Wrap into a grid rather than one long row: a dozen panels side by side collapse to
    # zero width once axis decorations are accounted for.
    ncols = min(4, len(axes_present))
    nrows = int(np.ceil(len(axes_present) / ncols))
    fig, grid = ctx.style.figure(nrows, ncols, sharey=True)
    flat = [grid[r, c] for r in range(nrows) for c in range(ncols)]
    for ax in flat[len(axes_present):]:
        ax.set_axis_off()

    tidy = []
    for column, name in enumerate(axes_present):
        ax = flat[column]
        sub = _axis_frame(df, name)
        levels = sorted(sub["level"].unique())
        data = [sub.loc[sub["level"] == lv, "value"].to_numpy() for lv in levels]
        if not any(len(d) > 1 for d in data):
            ax.set_axis_off()
            continue
        parts = ax.violinplot(data, positions=levels, showextrema=False, widths=0.8)
        for body, colour in zip(parts["bodies"],
                                ctx.style.level_colours(ctx.style.axis_colour(name),
                                                        len(levels))):
            body.set_facecolor(colour)
            body.set_alpha(0.85)
        auc = ctx.axis_rows(metric=metric, field=field, degradation=name)
        if not auc.empty and np.isfinite(auc["separability_auc_min"].iloc[0]):
            ax.set_title(f"{ctx.label(name)}\nmin AUC {auc['separability_auc_min'].iloc[0]:.2f}",
                         fontsize="x-small")
        else:
            ax.set_title(ctx.label(name), fontsize="x-small")
        ax.set_xlabel("severity level")
        for lv, values in zip(levels, data):
            tidy.append({"degradation": name, "level": lv,
                         "median": float(np.median(values)), "n": len(values)})
    for r in range(nrows):
        grid[r, 0].set_ylabel(metric)
    fig.suptitle(f"{metric} on {field}: severity_level distributions over frames", fontsize="small")

    return PlotResult(
        [FigureItem(fig, {"metric": metric, "field": field},
                    caption="Distribution of each severity level's values across frames. Adjacent "
                            "violins that overlap cannot be told apart by this metric; "
                            "the annotated AUC is the smallest adjacent-severity level separation.",
                    data=pd.DataFrame(tidy))]
    )


# --- section 6: when and where does it fire? --------------------------------------------------


@plot(
    section=6, order=10, scope="per_field",
    title="Reference field and its degraded variants",
    requires_maps=True,
    defaults={"cmap": "RdBu_r"},
)
def field_gallery(ctx, df, opts) -> PlotResult:
    """The reference field beside each degraded variant, on shared colour limits.

    Shared limits are not a stylistic choice: autoscaling each panel would make a heavily
    smoothed field look identical to the reference, which is the opposite of what the
    figure is for.
    """
    field = str(df["field"].iloc[0])
    stored = {k: v for k, v in ctx.maps.items() if f":{field}__" in k}
    ctx.require(bool(stored), f"no stored maps for {field}")

    reference = ctx.maps.get(f"__field__{field}")
    panels = sorted(stored)[:12]
    n = len(panels) + (1 if reference is not None else 0)
    ncols = min(4, n)
    nrows = int(np.ceil(n / ncols))
    fig, grid = ctx.style.figure(nrows, ncols)
    flat = [grid[r, c] for r in range(nrows) for c in range(ncols)]

    limits = symmetric_limits(np.concatenate([v.ravel() for v in stored.values()]), 0.995)
    i = 0
    if reference is not None:
        show_field(flat[0], reference, cmap=opts.get("cmap"), vmin=limits[0], vmax=limits[1])
        flat[0].set_title("reference", fontsize="x-small")
        i = 1
    for key in panels:
        ax = flat[i]
        show_field(ax, stored[key], cmap="magma")
        ax.set_title(key.split("__", 1)[1].rsplit("__", 1)[0], fontsize="xx-small")
        ax.set_xticks([])
        ax.set_yticks([])
        i += 1
    for ax in flat[i:]:
        ax.set_axis_off()
    fig.suptitle(f"Pointwise metric density — {field}", fontsize="small")

    return PlotResult(
        [FigureItem(fig, {"field": field},
                    caption="Per-cell contribution to the metric for each stored variant. "
                            "A displaced feature shows as two lobes: one where it should "
                            "be and is not, one where it is and should not be.")]
    )


# --- section 7: what does it detect? --------------------------------------------------------


def _cell_wedges(n: int) -> list[list[tuple[float, float]]]:
    """Polygons tiling the unit square, one per field, in the layout of Gleckler et al. (2008).

    One field fills the cell; two split it on the diagonal; three take the top triangle and the
    two lower quadrilaterals; four take the four triangles about the centre.
    """
    tl, tr, br, bl, centre, bottom = (0, 1), (1, 1), (1, 0), (0, 0), (0.5, 0.5), (0.5, 0)
    return {
        1: [[bl, br, tr, tl]],
        2: [[bl, br, tr], [bl, tr, tl]],
        3: [[tl, tr, centre], [tl, centre, bottom, bl], [tr, br, bottom, centre]],
        4: [[tl, tr, centre], [tr, br, centre], [br, bl, centre], [bl, tl, centre]],
    }[n]


#: Vargha & Delaney's descriptive anchors on |A - 0.5| (small, medium, large), as Cliff's delta.
#: Colour-bar ticks for scale only; never labels on a cell.
_DELTA_ANCHORS = (0.12, 0.28, 0.42)


@plot(
    section=7, order=5, scope="global",
    title="Portrait of adjacent-level discrimination",
    requires_columns=("degradation", "level", "value"), min_axes=1,
    defaults={"cmap": "RdBu_r"},
)
def response_portrait(ctx, df, opts) -> PlotResult:
    """Cliff's delta for every metric, degradation and field, in one portrait diagram.

    The climate-model portrait (Gleckler, Taylor & Doutriaux 2008, *J. Geophys. Res.* 113,
    D06104): a metric-by-degradation grid with each cell split into one wedge per field, so all
    three fields are read in one view. RdBu rather than a perceptually uniform diverging map: the
    ones matplotlib ships are dark at their centre, which would make "no discrimination" the
    darkest cell and hard to tell from the grey used for a missing value.
    """
    ctx.require("cliffs_delta_min" in ctx.axes.columns, "this run's analysis has no Cliff's delta")
    metrics = sorted(str(m) for m in df["metric"].unique())
    rows = ctx.axes[~ctx.axes["is_probe"] & ctx.axes["metric"].isin(metrics)
                    & ctx.axes["field"].isin(df["field"].unique())]
    fields = sorted(str(f) for f in rows["field"].unique())
    ctx.require(1 <= len(fields) <= 4, f"the portrait holds one to four fields, not {len(fields)}")
    axes_present = [a for a in ctx.ordinal_axes if a in set(rows["degradation"].astype(str))]
    ctx.require(bool(axes_present) and rows["cliffs_delta_min"].notna().any(),
                "no finite Cliff's delta")
    lookup = {(str(r.metric), str(r.degradation), str(r.field)): float(r.cliffs_delta_min)
              for r in rows.itertuples()}

    n_m, n_a = len(metrics), len(axes_present)
    fig, grid = ctx.style.figure(1, 2, w=0.7 * n_a + 3.6, h=0.5 * n_m + 1.8,
                                 gridspec_kw={"width_ratios": [max(n_a, 3), 1.2]})
    ax, key = grid[0, 0], grid[0, 1]
    cmap, norm = matplotlib.colormaps[opts["cmap"]], Normalize(-1.0, 1.0)
    wedges = _cell_wedges(len(fields))
    tidy = []
    for i, metric in enumerate(metrics):
        for j, axis in enumerate(axes_present):
            for wedge, field in zip(wedges, fields, strict=True):
                value = lookup.get((metric, axis, field), np.nan)
                points = [(j + x, n_m - 1 - i + y) for x, y in wedge]
                ax.add_patch(Polygon(points, closed=True, lw=0.6, edgecolor="white",
                                     facecolor=cmap(norm(value)) if np.isfinite(value) else "0.9"))
                tidy.append({"metric": metric, "degradation": axis, "field": field,
                             "cliffs_delta_min": value})
    ax.set_xlim(0, n_a)
    ax.set_ylim(0, n_m)
    ax.set_aspect("equal")
    ax.grid(False)
    ax.set_xticks(np.arange(n_a) + 0.5, [ctx.label(a) for a in axes_present], rotation=40,
                  ha="right", fontsize="x-small")
    ax.set_yticks(np.arange(n_m) + 0.5, list(reversed(metrics)), fontsize="x-small")
    bar = fig.colorbar(ScalarMappable(norm, cmap), ax=ax, shrink=0.8)
    bar.set_label("Cliff's delta, weakest adjacent pair", fontsize="x-small")
    bar.set_ticks([-1, *(-a for a in reversed(_DELTA_ANCHORS)), 0, *_DELTA_ANCHORS, 1])
    bar.ax.tick_params(labelsize="xx-small")
    key.set_xlim(-0.1, 1.1)
    key.set_ylim(-0.1, 1.1)
    key.set_aspect("equal")
    key.set_axis_off()
    for wedge, field in zip(wedges, fields, strict=True):
        key.add_patch(Polygon(wedge, closed=True, facecolor="0.85", edgecolor="0.3", lw=0.6))
        cx, cy = np.mean(np.array(wedge), axis=0)
        key.text(cx, cy, field, ha="center", va="center", fontsize="xx-small")
    key.set_title("one wedge per field", fontsize="xx-small")
    caption = (
        "Cliff's delta between adjacent severity levels, the weakest pair on each degradation, "
        "for every metric and degradation, with each cell split into one wedge per field (key "
        "at right). 0 means the metric cannot tell neighbouring levels apart, 1 that a frame at "
        "the worse level always scores worse, and a negative value that the order is reliably "
        "reversed. Grey wedges have no defined value. The colour-bar ticks at 0.12, 0.28 and "
        "0.42 are Vargha and Delaney's small, medium and large anchors, given for scale and "
        "not as grades."
    )
    return PlotResult([FigureItem(fig, {}, caption=caption, data=pd.DataFrame(tidy))])


def _matrix_panel(ax, matrix: pd.DataFrame, cmap, title: str):
    """One annotated metric-by-metric coefficient matrix, grey where undefined."""
    values = matrix.to_numpy(float)
    mesh = ax.pcolormesh(np.ma.masked_invalid(values), cmap=cmap, vmin=-1.0, vmax=1.0,
                         edgecolors="white", linewidth=0.5)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.grid(False)
    ticks = np.arange(len(matrix)) + 0.5
    ax.set_xticks(ticks, list(matrix.columns), rotation=60, ha="right", fontsize="xx-small")
    ax.set_yticks(ticks, list(matrix.index), fontsize="xx-small")
    for (i, j), v in np.ndenumerate(values):
        if np.isfinite(v):
            ax.text(j + 0.5, i + 0.5, f"{v:.2f}", ha="center", va="center", fontsize=5,
                    color="white" if abs(v) > 0.6 else "black")
    ax.set_title(title, fontsize="small")
    return mesh


@plot(
    section=7, order=30, scope="global", min_metrics=2,
    title="Rank agreement beside magnitude agreement",
    requires_columns=("damage", "value"),
    defaults={"cmap": "RdBu_r"},
)
def concordance_matrix(ctx, df, opts) -> PlotResult:
    """Spearman correlation of the metrics (left) beside Lin's concordance of their damage (right).

    Two metrics can order every degradation identically and still charge very different amounts
    for the same one; the left panel sees only the first, the right the second (Lin 1989,
    *Biometrics* 45(1):255-268).
    """
    from fmeval.analysis import concordance_matrix as lins_concordance
    from fmeval.analysis import cross_metric_correlation

    rho = cross_metric_correlation(df)
    rc = lins_concordance(df, probe_labels=ctx.probe_labels)
    ctx.require(not rho.empty and not rc.empty,
                "needs two metrics with common ladder levels and a damage scale")
    names = sorted(set(rho.index) | set(rc.index))
    rho, rc = rho.reindex(index=names, columns=names), rc.reindex(index=names, columns=names)
    side = 0.42 * len(names) + 1.6
    fig, grid = ctx.style.figure(1, 2, w=2 * side + 1.0, h=side)
    cmap = matplotlib.colormaps[opts["cmap"]].with_extremes(bad="0.9")
    mesh = _matrix_panel(grid[0, 0], rho, cmap, "Spearman, on median values")
    _matrix_panel(grid[0, 1], rc, cmap, "Lin's concordance, on damage")
    fig.colorbar(mesh, ax=list(grid.ravel()), shrink=0.7, label="coefficient")
    unscaled = [m for m in names if rc.loc[m].isna().all()]
    data = pd.DataFrame([
        {"metric_a": a, "metric_b": b, "spearman": float(rho.loc[a, b]),
         "concordance": float(rc.loc[a, b])}
        for a in names for b in names
    ])
    caption = (
        "Left: rank correlation between metrics over the median value at every strength of "
        "every degradation, the existing redundancy statistic. Right: Lin's concordance "
        "coefficient on damage, which also penalises departure from the identity line, so two "
        "metrics that order every degradation alike but charge different amounts score high on "
        "the left and lower on the right. Grey cells are undefined."
        + (f" No damage scale, so undefined on the right: {', '.join(unscaled)}."
           if unscaled else "")
    )
    return PlotResult([FigureItem(fig, {}, caption=caption, data=data)])


@plot(
    section=7, order=35, scope="global", min_metrics=3,
    title="Which metrics agree in magnitude",
    requires_columns=("damage",),
)
def redundancy_dendrogram(ctx, df, opts) -> PlotResult:
    """Average-linkage clustering of the metrics on one minus the absolute concordance of damage.

    Metrics joined near zero assign nearly the same damage everywhere. Drawn in one colour: the
    tree shows structure, not a set of groups to adopt.
    """
    from scipy.cluster.hierarchy import dendrogram, linkage
    from scipy.spatial.distance import squareform

    from fmeval.analysis import concordance_matrix as lins_concordance

    rc = lins_concordance(df, probe_labels=ctx.probe_labels)
    keep = [m for m in rc.index if np.isfinite(rc.loc[m].to_numpy(float)).all()]
    ctx.require(len(keep) >= 3, "needs three metrics with a damage scale")
    distance = 1.0 - np.abs(rc.loc[keep, keep].to_numpy(float))
    distance = np.clip((distance + distance.T) / 2, 0.0, None)
    np.fill_diagonal(distance, 0.0)
    tree = linkage(squareform(distance, checks=False), method="average")
    fig, grid = ctx.style.figure(1, 1, h=0.35 * len(keep) + 1.2)
    ax = grid[0, 0]
    dendrogram(tree, labels=keep, orientation="right", ax=ax, color_threshold=0,
               above_threshold_color="black")
    ax.set_xlabel("1 - |Lin's concordance|")
    ax.grid(False)
    data = pd.DataFrame(tree, columns=["left", "right", "distance", "size"])
    data["leaves"] = ";".join(keep)
    caption = (
        "Average-linkage clustering of the metrics that have a damage scale, on one minus the "
        "absolute value of Lin's concordance of their damage. Metrics joined near zero assign "
        "nearly the same damage to every strength of every degradation; the height of a join "
        "is how far apart the two groups are."
    )
    return PlotResult([FigureItem(fig, {}, caption=caption, data=data)])


@plot(
    section=6, order=20, scope="per_field",
    title="Damage against severity, every metric on every degradation",
    requires_columns=("damage", "degradation", "level"), min_axes=1,
    defaults={"clip": 1.25},
)
def response_sparklines(ctx, df, opts) -> PlotResult:
    """Every metric's median-damage curve on every degradation, on one shared 0-1 scale.

    A sparkline table (Tufte 2006, *Beautiful Evidence*): small multiples aligned on a common
    scale, so onset, slope, saturation and blindness are read by position rather than by colour,
    the encoding people read most accurately (Cleveland & McGill 1984, *J. Am. Stat. Assoc.*
    79(387):531-554). A flat line is a result, not a failure to draw.
    """
    from fmeval.analysis import damage_by_level

    field = str(df["field"].iloc[0])
    metrics = sorted(str(m) for m in df["metric"].unique())
    wide = damage_by_level(df, field=field, probe_labels=ctx.probe_labels)
    ctx.require(any(m in wide.columns for m in metrics),
                f"no metric has a damage scale on {field}")
    present = set(wide["degradation"].astype(str))
    axes_present = [a for a in ctx.ordinal_axes if a in present]
    ctx.require(bool(axes_present), f"no ordinal degradation on {field}")
    info = {
        (str(r.metric), str(r.degradation)): r
        for r in ctx.axes[(ctx.axes["field"] == field) & ~ctx.axes["is_probe"]].itertuples()
    }

    clip = float(opts["clip"])
    fig, grid = ctx.style.figure(len(metrics), len(axes_present), sharey=True,
                                 w=0.85 * len(axes_present) + 1.8, h=0.5 * len(metrics) + 1.2)
    tidy = []
    for j, axis in enumerate(axes_present):
        block = wide[wide["degradation"] == axis].sort_values("level")
        levels = block["level"].to_numpy(int)
        for i, metric in enumerate(metrics):
            ax = grid[i, j]
            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(False)
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.set_ylim(-0.08, clip)
            y = (block[metric].to_numpy(float) if metric in block.columns
                 else np.full(len(levels), np.nan))
            row = info.get((metric, axis))
            onset = float(getattr(row, "sensitivity_level", np.nan)) if row else np.nan
            elasticity = float(getattr(row, "elasticity", np.nan)) if row else np.nan
            has_scale = bool(np.isfinite(y).any())
            if not has_scale:
                ax.set_facecolor("0.93")
                ax.text(0.5, 0.5, "no scale", transform=ax.transAxes, ha="center",
                        va="center", fontsize="xx-small", color="0.45")
            else:
                ax.axhline(1.0, color="0.75", lw=0.6, ls=":")
                shown = np.minimum(y, clip)
                ax.plot(np.r_[0, levels], np.r_[0.0, shown], color="0.15", marker="o", ms=2.2,
                        lw=0.9, ls="-" if len(levels) > 3 else "none")
                clipped = y > clip
                if clipped.any():
                    ax.plot(levels[clipped], shown[clipped], "^", color="0.15", ms=3)
                if np.isfinite(onset) and onset in levels:
                    ax.plot(onset, shown[list(levels).index(onset)], "o", ms=3.5, zorder=3,
                            color=okabe("vermillion"))
                if np.isfinite(elasticity):
                    ax.text(0.03, 0.97, f"{elasticity:.1f}", transform=ax.transAxes,
                            ha="left", va="top", fontsize="xx-small", color="0.3")
            for level, severity, value in zip(levels, block["severity"], y, strict=True):
                tidy.append({
                    "field": field, "metric": metric, "degradation": axis,
                    "level": int(level), "severity": float(severity),
                    "damage_median": float(value), "n_levels": len(levels),
                    "has_scale": has_scale, "sensitivity_level": onset,
                    "elasticity": elasticity,
                    "elasticity_x": getattr(row, "elasticity_x", "") if row else "",
                })
        grid[0, j].set_title(ctx.label(axis), fontsize="xx-small", loc="left", rotation=20)
        grid[-1, j].set_xlabel(
            f"{block['severity'].min():.3g} to {block['severity'].max():.3g}",
            fontsize="xx-small")
    for i, metric in enumerate(metrics):
        grid[i, 0].set_ylabel(metric, rotation=0, ha="right", va="center", fontsize="x-small")
    fig.suptitle(f"Median damage against severity level -- {field}", fontsize="small")
    caption = (
        f"Median damage over frames against severity level for every metric (rows) and "
        f"degradation (columns) on {field}, all on one 0-1 scale, starting from the undamaged "
        "reference at the left of every curve. The dotted line is damage 1, an unrelated "
        "field. Degradations with three or fewer usable levels are drawn as dots. The red dot "
        "is the first level at which the metric has moved a tenth of the way to an unrelated "
        "field. The number is the elasticity over the mildest levels, against the severity each "
        "degradation names: near 0 blind, 1 linear, 2 quadratic. Grey cells are metrics with "
        f"no damage scale on this field. Points above {clip:g} are clipped and drawn as "
        "triangles. Below each column is the range of the severity actually applied."
    )
    return PlotResult([FigureItem(fig, {"field": field}, caption=caption,
                                  data=pd.DataFrame(tidy))])


@plot(
    section=7, order=10, scope="per_field", min_metrics=2,
    title="Selectivity profile",
    requires_columns=("degradation", "level", "value"), min_axes=2,
)
def selectivity_profile(ctx, df, opts) -> PlotResult:
    """Each metric's response across every ladder axis, as grouped bars.

    Two metrics with near-identical profiles are redundant even when their magnitudes
    differ. A profile that is uniform across every axis indicates a metric responding to
    damage in general rather than to a specific failure mode.
    """
    field = str(df["field"].iloc[0])
    rows = ctx.axes[(ctx.axes["field"] == field) & (~ctx.axes["is_probe"])]
    ctx.require(rows["metric"].nunique() >= 2, "needs at least two metrics")
    grid_df = rows.pivot_table(index="degradation", columns="metric", values="rho",
                               observed=True)

    fig, axgrid = ctx.style.figure(1, 1)
    ax = axgrid[0, 0]
    positions = np.arange(len(grid_df))
    width = 0.8 / max(1, grid_df.shape[1])
    for i, metric in enumerate(grid_df.columns):
        ax.bar(positions + i * width, grid_df[metric].to_numpy(), width,
               label=metric, color=ctx.style.metric_colour(metric))
    ax.set_xticks(positions + 0.4 - width / 2)
    ax.set_xticklabels([ctx.label(a) for a in grid_df.index], rotation=40, ha="right")
    ax.set_ylabel("Spearman correlation")
    ax.set_title(f"What each metric detects — {field}")
    ax.legend(fontsize="x-small")

    return PlotResult(
        [FigureItem(fig, {"field": field},
                    caption="Rank correlation of each metric against each ladder axis.",
                    data=grid_df.reset_index())]
    )


# --- section 8: can it be fooled? ---------------------------------------------------------


@plot(
    section=8, order=10, scope="per_field",
    title="Response to deliberately misleading fields",
    requires_columns=("damage",),
    requires_degradations=("gaussian_impostor",),
)
def deception_panel(ctx, df, opts) -> PlotResult:
    """Damage assigned to the misleading fields, against the ordinary ladder.

    The spectrum-matched Gaussian field preserves the energy spectrum and the two-point
    correlation exactly while destroying all phase information, so a metric built only on
    second-order statistics scores it as perfect. The positionally unrelated field
    preserves every statistic while destroying alignment, so it defines a damage of 1.
    """
    field = str(df["field"].iloc[0])
    metrics = sorted(df["metric"].unique())
    ladder = df[(df["level"] > 0) & (~df["degradation"].isin(ctx.probe_labels))]

    fig, grid = ctx.style.figure(1, 1, w=1.7 * ctx.style.panel_w,
                                 h=max(2.0, 0.42 * len(metrics) + 1.4))
    ax = grid[0, 0]
    tidy = []
    labelled = False
    for row, metric in enumerate(metrics):
        severity_levels = ladder[ladder["metric"] == metric]["damage"].dropna()
        if len(severity_levels):
            ax.plot(severity_levels, [row] * len(severity_levels), "o",
                    mfc="none", mec="0.65", ms=4, zorder=2)
        impostor = df[(df["metric"] == metric)
                      & (df["degradation"] == "gaussian_impostor")]["damage"].median()
        has_scale = bool(len(severity_levels)) or bool(np.isfinite(impostor))
        if np.isfinite(impostor):
            ax.hlines(row, 0, impostor, color="0.85", lw=1, zorder=1)
            ax.plot(impostor, row, marker="*", ms=13, zorder=3, color=okabe("vermillion"),
                    label=None if labelled else "spectrum-matched Gaussian")
            labelled = True
        if not has_scale:
            ax.text(0.02, row, "no damage scale", fontsize="xx-small", color="0.5",
                    va="center")
        tidy.append({"metric": metric, "impostor_damage": float(impostor),
                     "has_scale": has_scale})

    ax.axvline(1.0, color="0.3", lw=1)
    ax.text(1.0, -0.7, " unrelated fields", fontsize="x-small", color="0.3", va="top")
    limit = float(ctx.thresholds.get("impostor_damage", np.nan))
    if np.isfinite(limit):
        ax.axvline(limit, color="0.5", ls="--", lw=1)
    ax.set_yticks(range(len(metrics)))
    ax.set_yticklabels(metrics)
    ax.set_xlabel("damage (0 = clean, 1 = unrelated fields)")
    ax.set_title(f"Misleading fields — {field}")
    ax.set_ylim(-1.0, len(metrics) - 0.4)
    if labelled:
        ax.legend(fontsize="x-small", loc="upper right")

    return PlotResult(
        [FigureItem(fig, {"field": field},
                    caption="Damage assigned to the spectrum-matched Gaussian field "
                            "(star) against the ordinary ladder severity levels (open circles), "
                            "one row per metric. A metric that places the star near zero is "
                            "responding only to second-order statistics. Rows marked 'no damage "
                            "scale' are metrics whose clean and unrelated values coincide, so no "
                            "damage can be defined for them.",
                    data=pd.DataFrame(tidy))],
        notes=["A metric near the origin here sees only the energy spectrum."],
    )


# --- section 9: displacement ------------------------------------------------------------------


@plot(
    section=9, order=10, scope="per_field",
    title="Response to pure displacement",
    requires_columns=("damage",),
    defaults={"axes": ("translate_subpixel", "translate_x", "translate_y")},
)
def displacement_response(ctx, df, opts) -> PlotResult:
    """Damage against displacement distance, one line per metric.

    A pure translation leaves shape and amplitude exactly correct and changes only
    position, so this isolates position sensitivity from every other kind. A metric that
    reaches the unrelated-field level after a displacement much smaller than the structures
    in the field is exhibiting the double penalty.
    """
    field = str(df["field"].iloc[0])
    wanted = [a for a in opts.get("axes", ()) if a in set(df["degradation"])]
    ctx.require(bool(wanted), "no translation axis in the ladder")

    # The companion panel puts the same points against energy_changed, the mean squared
    # difference over the reference variance: mean squared error on a fixed scale. It is itself a
    # metric, so that axis is not metric-independent and every curve on it reads relative to MSE.
    translated = df[df["degradation"].isin(wanted) & (df["level"] > 0)]
    companion = ("energy_changed" in df.columns
                 and bool(translated["energy_changed"].notna().any()))
    fig, grid = ctx.style.figure(1, 2 if companion else 1,
                                 w=(2 if companion else 1) * ctx.style.panel_w + 1.4)
    ax = grid[0, 0]
    tidy = []
    for metric in sorted(df["metric"].unique()):
        sub = translated[translated["metric"] == metric]
        columns = ["damage", "energy_changed"] if companion else ["damage"]
        stats = sub.groupby("severity", observed=True)[columns].median().sort_index()
        if stats.empty or not np.isfinite(stats["damage"]).any():
            continue                      # no damage scale: nothing to draw, nothing to list
        # With the companion panel, MSE is its x-axis, so it is drawn as the reference in both.
        reference = companion and metric == "mse"
        look = ({"color": "black", "ls": "--", "lw": 1.6} if reference else
                {"color": ctx.style.metric_colour(metric), "ls": ctx.style.metric_style(metric)})
        label = f"{metric} (the right panel's x-axis)" if reference else metric
        ax.plot(stats.index, stats["damage"], marker="o", ms=3.5, label=label, **look)
        if companion:
            grid[0, 1].plot(stats["energy_changed"], stats["damage"], marker="o", ms=3.5,
                            label=label, **look)
        tidy.extend(
            {"metric": metric, "distance": float(d), "damage": float(r["damage"]),
             "energy_changed": float(r["energy_changed"]) if companion else np.nan}
            for d, r in stats.iterrows()
        )

    # Declared before the log scale is set, not after. A metric with no dynamic range has an
    # all-NaN damage column -- which AGENTS.md section 3 explicitly calls correct for a
    # single-field invariant rather than a bug -- and matplotlib then raises "Data cannot be
    # log-scaled because all values are <= 0" from inside the renderer. The contract is that
    # unavailability is declared with ctx.require, so this is a skip, not an error.
    ctx.require(
        any(np.isfinite(row["damage"]) for row in tidy),
        "no finite damage on the displacement axis: the metric has no dynamic range between "
        "clean and the unrelated-field anchor, so there is nothing to plot against distance",
    )

    for panel in grid[0]:
        panel.axhline(1.0, color="0.3", lw=1)
        panel.set_xscale("log")
        panel.set_ylabel("damage")
    ax.text(0.01, 1.0, "unrelated fields", fontsize="x-small", color="0.3",
            va="bottom", transform=ax.get_yaxis_transform())
    ax.set_xlabel("displacement [cells]")
    ax.set_title(f"Pure displacement — {field}")
    fig.legend(*ax.get_legend_handles_labels(), fontsize="xx-small", loc="outside right upper")
    caption = ("Damage against displacement distance. Shape and amplitude are exactly correct "
               "at every point on this curve; only position changes.")
    if companion:
        right = grid[0, 1]
        right.set_xlabel("field change (normalised MSE)")
        right.set_title("The same points against normalised MSE", fontsize="small")
        caption += (" The right panel plots the same medians against energy_changed, the mean "
                    "squared difference divided by the reference variance. That is mean squared "
                    "error on a fixed scale, so this axis is not metric-independent: every curve "
                    "on it reads as that metric relative to MSE, and MSE itself, dashed black "
                    "when present, is proportional to it by construction.")

    return PlotResult(
        [FigureItem(fig, {"field": field}, caption=caption, data=pd.DataFrame(tidy))]
    )


# --- section 10: cost -----------------------------------------------------------------------


@plot(
    section=10, order=10, scope="global", min_metrics=2,
    title="Cost against worst-axis correlation",
    requires_columns=("wall_time_s",),
)
def cost_frontier(ctx, df, opts) -> PlotResult:
    """Worst-axis rank correlation against wall-clock cost, one point per metric.

    Upper left is the useful region. A metric in the upper right gives the right answer at
    a price that may rule it out as a training loss while leaving it usable as a
    diagnostic.
    """
    card = ctx.card
    ctx.require("rho_min" in card.columns and len(card) >= 2, "needs at least two metrics")
    fig, grid = ctx.style.figure(1, 1)
    ax = grid[0, 0]
    for _, row in card.iterrows():
        ax.scatter(row["cost_s"], row["rho_min"], s=45,
                   color=ctx.style.metric_colour(row["metric"]), zorder=3)
        ax.annotate(f"{row['metric']} ({row['field']})",
                    (row["cost_s"], row["rho_min"]),
                    textcoords="offset points", xytext=(6, 3), fontsize="xx-small")
    ax.set_xscale("log")
    ax.set_xlabel("wall clock per evaluation [s]")
    ax.set_ylabel("worst-axis Spearman correlation")
    ax.set_title("Cost against reliability")
    return PlotResult([FigureItem(fig, {}, caption="Each point is one metric and field.",
                                  data=card[["metric", "field", "cost_s", "rho_min"]])])


# --- helpers -------------------------------------------------------------------------------


def _units(ctx, metric: str) -> str:
    snapshot = ctx.meta.get("registries", {}).get("metrics", {})
    return snapshot.get(metric, {}).get("units", "")


def _use_log(values: pd.Series, setting) -> bool:
    if setting is not True and setting != "auto":
        return False
    positive = values[values > 0]
    if len(positive) < 3:
        return False
    return bool(positive.max() / positive.min() > 100)


@plot(
    section=3, order=5, scope="per_field",
    title="Where the field keeps its energy",
    requires_columns=("field", "severity", "calibration"),
)
def energy_spectrum(ctx, df, opts) -> PlotResult:
    """Cumulative fluctuation energy against wavenumber, with the applied cutoffs marked.

    This is the figure that explains the resolution of every filter ladder in the report. A
    severity on a spectral axis is a fraction of energy to remove, and the harness converts it to
    a cutoff using exactly this curve -- so where the curve is steep, neighbouring severity levels
    land on the same wavenumber shell and cannot be separated, and where it is shallow they spread
    out.

    Read the steepness first. Measured on this data the density curve is almost a step: 3e-5 of its
    fluctuation energy lies at or below |k| = 1 and 69% at |k| = sqrt(2), so two consecutive
    available cutoffs differ by most of the field and a sharp filter has only a couple of usable
    severity levels there however the ladder is configured. Vorticity rises gradually --
    50% by |k| = 3.2,
    90% by 23, 99% by 51 -- and its cutoffs spread over more than a factor of ten as a result.
    """
    ctx.require(not ctx.spectrum.empty,
                "no measured spectrum in this run (it predates severity calibration)")
    field = str(df["field"].iloc[0])
    curve = ctx.spectrum[ctx.spectrum["field"] == field].sort_values("wavenumber")
    ctx.require(not curve.empty, f"no measured spectrum for {field}")

    cuts = df[df["calibration"].astype(str).str.startswith("energy") & (df["level"] > 0)]

    fig, axgrid = ctx.style.figure(1, 1)
    ax = axgrid[0, 0]
    k = curve["wavenumber"].to_numpy()
    cumulative = curve["cumulative_energy_below"].to_numpy()
    ax.plot(k, cumulative, marker="o", markersize=2.5, lw=1.4, color="black",
            label="cumulative energy below $k$")
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlim(0, max(k.max(), 2))
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("wavenumber $k$")
    ax.set_ylabel("fraction of fluctuation energy below $k$")

    # The applied cutoffs, so a reader can see which severity levels share a shell.
    rows = []
    for axis, g in cuts.groupby("degradation", observed=True):
        colour = ctx.style.axis_colour(str(axis))
        for level, h in g.groupby("level", observed=True):
            cutoff = float(h["severity"].iloc[0])
            removed = float(h["energy_removed"].median())
            degenerate = bool(h["severity_degenerate"].iloc[0])
            ax.axvline(cutoff, color=colour, lw=1.0,
                       ls=":" if degenerate else "--", alpha=0.85)
            rows.append({"axis": str(axis), "level": int(level), "cutoff": cutoff,
                         "energy_removed": removed, "excluded": degenerate})
        ax.plot([], [], color=colour, ls="--", label=f"{ctx.label(str(axis))} cutoffs")

    ax.legend(fontsize="xx-small", loc="lower right")
    ax.set_title(f"Fluctuation energy distribution — {field}")

    note = (
        "Dashed lines are the cutoffs the configured severities resolved to; dotted lines are "
        "severity levels excluded because they landed on the same shell as a milder "
        "severity level or on a no-op."
    )
    return PlotResult(
        figures=[FigureItem(
            fig=fig, keys={"field": field},
            caption=f"Cumulative fluctuation energy for {field}, with the applied spectral "
                    "cutoffs. The steeper the curve, the fewer distinct severity levels "
                    "a sharp filter "
                    "can produce.",
            data=pd.concat([curve.assign(kind="spectrum"),
                            pd.DataFrame(rows).assign(kind="cutoff")], ignore_index=True),
        )],
        notes=[note],
    )
