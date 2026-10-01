"""Reporting: LaTeX escaping, the renderer registry, and document assembly.

The escaping tests matter most. Metric and degradation names contain underscores, and an
unescaped underscore is a hard LaTeX error rather than a cosmetic one -- invisible until
compile time, and therefore invisible until someone uploads the folder to Overleaf.
"""

from __future__ import annotations

import re
import shutil

import numpy as np
import pandas as pd
import pytest

from fmeval.io import RunFolder, write_config, write_maps, write_results, write_run_meta
from fmeval.report import latex
from fmeval.report.driver import (
    build_context,
    render,
    write_document,
    write_manifest,
    write_summary_text,
)
from fmeval.report.registry import (
    PLOTS,
    SECTIONS,
    SECTIONS_BY_NUMBER,
    TABLES,
    iter_renderers,
)
from tests.test_analysis import make_frame

# --- escaping -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("a_b", r"a\_b"),
        ("100%", r"100\%"),
        ("x&y", r"x\&y"),
        ("#1", r"\#1"),
        ("$x$", r"\$x\$"),
        ("{a}", r"\{a\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
        ("\\path", r"\textbackslash{}path"),
        ("", ""),
        (None, ""),
    ],
)
def test_escape(raw, expected):
    assert latex.escape(raw) == expected


def test_escape_does_not_double_escape_a_backslash():
    """A single pass, so the backslash introduced by an escape is not escaped again."""
    assert latex.escape("a\\b") == r"a\textbackslash{}b"


def test_code_escapes_then_wraps():
    assert latex.code("gaussian_blur") == r"\texttt{gaussian\_blur}"


def test_number_formatting():
    assert latex.number(0.5) == "0.500"
    assert latex.number(None) == "--"
    assert latex.number(float("nan")) == "--"
    assert latex.number(float("inf")) == "--"
    assert r"\times10^{" in latex.number(1.2e-9)


def test_slug_is_filesystem_and_latex_safe():
    stem = latex.slug("ladder_curves", metric="mse", field="vorticity")
    assert stem == "ladder_curves__metric-mse__field-vorticity"
    assert re.fullmatch(r"[A-Za-z0-9_-]+", stem)
    # graphicx mis-parses paths with more than one dot.
    assert "." not in latex.slug("x", field="a.b c/d")


def test_booktabs_table_escapes_every_cell():
    df = pd.DataFrame({"metric": ["a_b"], "note": ["100% & rising"]})
    tex = latex.booktabs_table(df, caption="c_1", label="t")
    assert r"a\_b" in tex and r"100\% \& rising" in tex and r"c\_1" in tex
    assert _unescaped_underscores(tex) == []


def test_booktabs_table_handles_an_empty_frame():
    tex = latex.booktabs_table(pd.DataFrame(), caption="none", label="e")
    assert "No data" in tex and "\\begin{table}" in tex


#: Commands whose argument is a filename or a key rather than typeset text. LaTeX does not
#: set these, so an underscore in them is both harmless and necessary -- the files really
#: are named e.g. `provenance_table.tex`.
_PATH_COMMANDS = ("input", "includegraphics", "label", "ref", "graphicspath", "lstset")


def _unescaped_underscores(text: str) -> list[str]:
    """Underscores that LaTeX would actually try to typeset.

    Excludes verbatim blocks and the arguments of path- and label-taking commands.
    """
    body = re.sub(r"\\begin\{lstlisting\}.*?\\end\{lstlisting\}", "", text, flags=re.S)
    for command in _PATH_COMMANDS:
        body = re.sub(rf"\\{command}(\[[^\]]*\])?\{{[^}}]*\}}", "", body)
    return [m.group() for m in re.finditer(r"(?<!\\)_", body)]


# --- registry -----------------------------------------------------------------------------


def test_every_renderer_declares_a_known_section():
    for spec in iter_renderers():
        assert spec.section in SECTIONS_BY_NUMBER, spec.name


def test_renderers_are_ordered_by_section():
    numbers = [s.section for s in iter_renderers()]
    assert numbers == sorted(numbers)


def test_section_numbers_are_unique_and_contiguous():
    numbers = [s.number for s in SECTIONS]
    assert numbers == sorted(set(numbers)) == list(range(1, len(SECTIONS) + 1))


def test_registries_are_not_empty():
    assert PLOTS and TABLES


def test_duplicate_registration_raises():
    from fmeval.report.registry import plot

    with pytest.raises(ValueError, match="duplicate"):

        @plot(section=3, name="ladder_curves")
        def _dupe(ctx, df, opts):
            return None


def test_unknown_section_raises():
    from fmeval.report.registry import plot

    with pytest.raises(ValueError, match="section"):

        @plot(section=99, name="_bad_section")
        def _bad(ctx, df, opts):
            return None


# --- end to end ------------------------------------------------------------------------------


#: The synthetic ladder every report test renders: an axis of each length the real runs have
#: (four, three and two usable levels), plus the two probes.
LADDER = {
    "gaussian_blur": [1.0, 2.0, 3.0, 4.0],
    "translate_x": [1.0, 3.0, 6.0, 9.0],
    "translate_subpixel": [0.5, 1.0, 2.0],
    "median_blur": [2.0, 3.0],
    "gaussian_impostor": [8.0],
    "uncorrelated": [10.0, 10.0, 10.0],
}
#: The operator behind each ladder label, as the pipeline records it.
OPERATORS = {"translate_x": "translate", "uncorrelated": "random_large_translation"}
FIELDS = ("vorticity", "density", "velocity")


def synthetic_rows(metrics=("mse", "mae", "rmse", "flat")) -> pd.DataFrame:
    """Rows for a four-metric, three-field run.

    ``mae`` is the square root of ``mse`` everywhere, anchor included -- the shape relation of
    the real pair, so the two rank-correlate perfectly while disagreeing in magnitude; ``rmse`` is
    proportional to ``mae``, so their damage is identical; ``flat`` is zero everywhere, a metric
    with no damage scale.
    """
    transform = {"mse": lambda v: v, "mae": np.sqrt, "rmse": lambda v: 0.7 * np.sqrt(v),
                 "flat": lambda v: 0.0 * v}
    frames = []
    for metric in metrics:
        for field in FIELDS:
            axes = {k: [float(transform[metric](v)) for v in vals] for k, vals in LADDER.items()}
            frames.append(make_frame(metric=metric, field=field, n_frames=8,
                                     noise=0.0 if metric == "flat" else 0.05, seed=1, axes=axes))
    df = pd.concat(frames, ignore_index=True)
    df["degradation_op"] = df["degradation_op"].astype(str).replace(OPERATORS)
    df["energy_changed"] = np.where(df["level"] > 0, (0.1 * df["severity"]) ** 2, 0.0)
    return df


def _write_run(folder: RunFolder, df: pd.DataFrame) -> RunFolder:
    write_results(folder, df)
    digest = write_config(folder, {"metrics": sorted(df["metric"].unique()), "seed": 1,
                                   "note": "a_b"}, ["metrics=[mse]"])
    write_maps(folder, {"mse:vorticity__gaussian_blur_l2__t3": np.abs(
        np.random.default_rng(0).standard_normal((16, 8)))})
    write_run_meta(folder, run_id=1, config_hash=digest, metric="mse",
                   dataset="synthetic_d", n_frames=8, fields=list(FIELDS),
                   analysis_grid=16, ladder_axes=sorted(LADDER), n_severity_levels=15, seed=1,
                   command="python evaluate.py metrics=[mse]")
    return folder


@pytest.fixture
def run_folder(tmp_path):
    """A synthetic run folder, complete enough to render."""
    return _write_run(RunFolder(tmp_path / "mse_1").create(), synthetic_rows())


def _degenerate_folder(tmp_path) -> RunFolder:
    """Every metric zero everywhere: no damage scale anywhere."""
    return _write_run(RunFolder(tmp_path / "flat_1").create(),
                      synthetic_rows(metrics=("flat",)))


def test_full_render(run_folder):
    ctx = build_context(run_folder, thresholds={"spearman": 0.9, "impostor_damage": 0.5},
                        bootstrap=0)
    rendered = render(run_folder, ctx, formats=("png",))
    write_document(run_folder, ctx, rendered)
    write_manifest(run_folder, rendered)
    write_summary_text(run_folder, ctx)

    assert any(r.status == "ok" for r in rendered)
    assert not [r for r in rendered if r.status == "error"], \
        [(r.name, r.reason) for r in rendered if r.status == "error"]
    assert (run_folder.root / "main.tex").exists()
    assert (run_folder.root / "preamble.tex").exists()
    assert (run_folder.root / "summary.txt").exists()
    assert list(run_folder.plots.glob("*.png"))
    assert list(run_folder.tables.glob("*.tex"))


def test_sections_are_written_in_ascending_order_with_none_empty(run_folder):
    ctx = build_context(run_folder, bootstrap=0)
    rendered = render(run_folder, ctx, formats=("png",))
    write_document(run_folder, ctx, rendered)

    names = sorted(p.name for p in run_folder.sections.glob("*.tex"))
    numbers = [int(n.split("_")[0]) for n in names]
    assert numbers == sorted(numbers)
    for path in run_folder.sections.glob("*.tex"):
        text = path.read_text()
        assert text.strip(), f"{path.name} is empty"
        assert "\\section{" in text


def test_no_unescaped_underscore_survives_into_any_generated_tex(run_folder):
    """The bug that would otherwise be found on Overleaf, not here."""
    ctx = build_context(run_folder, bootstrap=0)
    rendered = render(run_folder, ctx, formats=("png",))
    write_document(run_folder, ctx, rendered)

    for path in [*run_folder.sections.glob("*.tex"),
                 *run_folder.tables.glob("*.tex"),
                 run_folder.root / "main.tex"]:
        offenders = _unescaped_underscores(path.read_text())
        assert not offenders, f"{path.name} has {len(offenders)} unescaped underscore(s)"


def test_renderer_failures_are_recorded_but_not_fatal(run_folder, monkeypatch):
    """A bad figure must not destroy an expensive evaluation's output."""
    from fmeval.report import registry as rr

    def boom(ctx, df, opts):
        raise RuntimeError("deliberate")

    monkeypatch.setitem(rr.PLOTS, "ladder_curves",
                        rr.PLOTS["ladder_curves"].__class__(
                            **{**rr.PLOTS["ladder_curves"].__dict__, "fn": boom}))
    ctx = build_context(run_folder, bootstrap=0)
    rendered = render(run_folder, ctx, formats=("png",))
    failed = [r for r in rendered if r.name == "ladder_curves"]
    assert failed and failed[0].status == "error"
    assert any(r.status == "ok" for r in rendered), "other renderers must still run"


def test_single_metric_run_skips_cross_metric_renderers(run_folder):
    ctx = build_context(run_folder, bootstrap=0)
    ctx.df = ctx.df[ctx.df["metric"] == "mse"]
    ctx.card = ctx.card[ctx.card["metric"] == "mse"]
    ctx.axes = ctx.axes[ctx.axes["metric"] == "mse"]
    rendered = render(run_folder, ctx, formats=("png",))
    skipped = {r.name: r.reason for r in rendered if r.status == "skipped"}
    assert "cost_frontier" in skipped
    assert "metrics" in skipped["cost_frontier"]


def test_config_appears_verbatim_in_the_report(run_folder):
    ctx = build_context(run_folder, bootstrap=0)
    rendered = render(run_folder, ctx, formats=("png",))
    write_document(run_folder, ctx, rendered)
    text = (run_folder.sections / "11_reproducibility.tex").read_text()
    assert "lstlisting" in text
    assert "metrics" in text, "the resolved config must be reproduced in the document"


# --- the compile check ------------------------------------------------------------------------


@pytest.mark.slow
def test_report_compiles_with_latex(run_folder):
    """Escaping bugs are invisible until compile time. Catch them here, not on Overleaf.

    Skipped when pdflatex is absent. On NERSC: ``module load texlive/2024``.
    """
    import subprocess

    if shutil.which("latexmk") is None:
        pytest.skip("latexmk not available")
    ctx = build_context(run_folder, bootstrap=0)
    rendered = render(run_folder, ctx, formats=("pdf", "png"))
    main = write_document(run_folder, ctx, rendered)
    result = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", main.name],
        cwd=main.parent, capture_output=True, text=True, timeout=600,
    )
    pdf = main.with_suffix(".pdf")
    assert result.returncode == 0, result.stdout[-4000:]
    assert pdf.exists() and pdf.stat().st_size > 1000


# --- the imshow lint --------------------------------------------------------------------------


def test_imshow_is_confined_to_the_style_helper():
    """Data is (X, Y); a raw imshow silently transposes every field picture.

    On square data the result looks entirely plausible, so this is the only thing that
    keeps the convention. ``monotonicity_heatmap`` is exempt: it draws a matrix of
    correlations, not a spatial field.
    """
    from pathlib import Path

    report_dir = Path(__file__).resolve().parent.parent / "fmeval" / "report"
    allowed = {"style.py"}
    for path in report_dir.glob("*.py"):
        if path.name in allowed:
            continue
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if ".imshow(" in line and "grid_df" not in line:
                raise AssertionError(
                    f"{path.name}:{number} calls imshow directly; spatial fields must go "
                    "through style.show_field, which applies the (X, Y) transpose"
                )


def test_context_reads_the_declared_anchor(tmp_path):
    """A run that declares another anchor is analysed against it, and the plots follow."""
    df = pd.concat([make_frame(metric=m, field="vorticity", n_frames=8, noise=0.05, seed=1,
                               axes={"gaussian_blur": [1.0, 2.0, 3.0, 4.0],
                                     "gaussian_impostor": [8.0], "flat": [10.0, 10.0]})
                    for m in ("mse", "mae")], ignore_index=True)
    folder = RunFolder(tmp_path / "mse_2").create()
    write_results(folder, df)
    digest = write_config(folder, {"metrics": ["mse"], "analysis": {"anchor": "flat"}}, [])
    write_run_meta(folder, run_id=2, config_hash=digest, metric="mse", dataset="synthetic_d",
                   n_frames=8, fields=["vorticity"], analysis_grid=16,
                   ladder_axes=["gaussian_blur"], n_severity_levels=8, seed=1,
                   anchor_label="flat", probe_labels=["flat", "gaussian_impostor"])
    ctx = build_context(folder, bootstrap=0)
    assert ctx.anchor_label == "flat"
    assert ctx.norm["anchor_source"].eq("flat").all()
    assert "flat" not in ctx.ordinal_axes
    rendered = render(folder, ctx, formats=("png",))
    assert not [r for r in rendered if r.status == "error"], \
        [(r.name, r.reason) for r in rendered if r.status == "error"]


def test_displacement_prose_names_what_each_geometric_axis_leaves_unchanged(tmp_path):
    """The report states, beside a measured response, what that degradation provably preserved.

    The rows name the operator as the pipeline does -- translate_x is an entry of the operator
    translate -- because that is what the accessor looks up in the run's registry snapshot.
    """
    df = pd.concat([make_frame(metric=m, field="vorticity", n_frames=8,
                               axes={"translate_x": [1.0, 3.0, 6.0], "uncorrelated": [10.0] * 2})
                    for m in ("mse", "mae")], ignore_index=True)
    df["degradation_op"] = df["degradation_op"].astype(str).replace({
        "translate_x": "translate", "uncorrelated": "random_large_translation"})
    folder = RunFolder(tmp_path / "mse_3").create()
    write_results(folder, df)
    digest = write_config(folder, {"metrics": ["mse"]}, [])
    write_run_meta(folder, run_id=3, config_hash=digest, metric="mse", dataset="synthetic_d",
                   n_frames=8, fields=["vorticity"], analysis_grid=16,
                   ladder_axes=["translate_x"], n_severity_levels=6, seed=1)
    ctx = build_context(folder, bootstrap=0)
    assert ctx.preserved_by("translate_x") == ("single_point_statistics", "amplitude_spectrum",
                                               "spatial_mean", "shape")
    assert ctx.preserved_by("no_such_axis") == ()
    write_document(folder, ctx, render(folder, ctx, formats=("png",)))
    text = (folder.sections / "09_displacement.tex").read_text()
    assert "amplitude spectrum" in text and "test-verified" in text



# --- plumbing --------------------------------------------------------------------------------


def test_items_within_a_section_follow_their_declared_order(run_folder, monkeypatch):
    """Registration order is what places a renderer; without it, the name did."""
    import dataclasses

    from fmeval.report import registry as rr
    from fmeval.report.context import TableResult

    def one_row(ctx, df, opts):
        return TableResult(frame=pd.DataFrame({"x": [1]}), caption="t")

    base = rr.TABLES["report_card"]
    monkeypatch.setitem(rr.TABLES, "zz_first", dataclasses.replace(
        base, name="zz_first", fn=one_row, section=7, order=5))
    monkeypatch.setitem(rr.TABLES, "aa_second", dataclasses.replace(
        base, name="aa_second", fn=one_row, section=7, order=50))
    ctx = build_context(run_folder, bootstrap=0)
    rendered = render(run_folder, ctx, only=["zz_first", "aa_second"], formats=("png",))
    write_document(run_folder, ctx, rendered)
    text = (run_folder.sections / "07_selectivity.tex").read_text()
    assert text.index("zz_first") < text.index("aa_second")


def test_long_tables_use_longtable():
    frame = pd.DataFrame({"metric": ["a_b"] * 3, "value": [1.0, 2.0, 3.0]})
    tex = latex.booktabs_table(frame, caption="c", label="l", long=True)
    assert "\\begin{longtable}" in tex and "\\endhead" in tex
    assert "\\begin{table}" not in tex, "a longtable cannot sit inside a float"
    short = latex.booktabs_table(frame, caption="c", label="l")
    assert "\\begin{table}" in short


def test_wide_tables_are_set_small():
    wide = pd.DataFrame({f"c{i}": [1.0] for i in range(13)})
    assert "\\footnotesize" in latex.booktabs_table(wide, caption="c", label="l")


def test_metric_styles_differ_when_colours_repeat():
    from fmeval.report.style import Style

    names = [f"m{i}" for i in range(9)]
    style = Style.build(metrics=names)
    assert style.metric_colour("m0") == style.metric_colour("m8"), "eight colours, nine metrics"
    assert style.metric_style("m0") != style.metric_style("m8")


# --- the response figures --------------------------------------------------------------------


def _rendered(folder, name, **filters):
    ctx = build_context(folder, bootstrap=0)
    for column, value in filters.items():
        ctx.df = ctx.df[ctx.df[column] == value]
        ctx.axes = ctx.axes[ctx.axes[column] == value]
        ctx.card = ctx.card[ctx.card[column] == value]
    rendered = {r.name: r for r in render(folder, ctx, only=[name], formats=("png",))}
    return rendered[name]


def _figure_data(folder, stem: str) -> pd.DataFrame:
    return pd.read_csv(folder.figure_data / f"{stem}.csv")


def test_response_sparklines_render_and_grey_the_metric_without_a_scale(run_folder):
    outcome = _rendered(run_folder, "response_sparklines")
    assert outcome.status == "ok", outcome.reason
    data = _figure_data(run_folder, "response_sparklines__field-vorticity")
    assert not data.loc[data["metric"] == "flat", "has_scale"].any()
    assert data.loc[data["metric"] == "mse", "has_scale"].all()
    assert set(data.loc[data["degradation"] == "median_blur", "n_levels"]) == {2}
    assert "uncorrelated" not in set(data["degradation"]), "probes are not ladder axes"


def test_response_sparklines_skip_when_no_metric_has_a_scale(tmp_path):
    outcome = _rendered(_degenerate_folder(tmp_path), "response_sparklines")
    assert outcome.status == "skipped" and "damage scale" in outcome.reason


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_portrait_wedges_tile_the_unit_square(n):
    from fmeval.report.plots import _cell_wedges

    def area(polygon):
        x, y = np.array(polygon).T
        return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

    wedges = _cell_wedges(n)
    assert len(wedges) == n
    assert sum(area(w) for w in wedges) == pytest.approx(1.0, abs=1e-12)
    assert all(0.0 <= c <= 1.0 for w in wedges for point in w for c in point)


def test_response_portrait_holds_every_field_in_one_grid(run_folder):
    outcome = _rendered(run_folder, "response_portrait")
    assert outcome.status == "ok", outcome.reason
    data = _figure_data(run_folder, "response_portrait")
    assert len(data) == 4 * 4 * 3, "one row per metric, ordinal degradation and field"
    assert data.loc[data["metric"] == "mse", "cliffs_delta_min"].notna().all()


def test_response_portrait_handles_a_single_field(run_folder):
    outcome = _rendered(run_folder, "response_portrait", field="density")
    assert outcome.status == "ok", outcome.reason
    assert set(_figure_data(run_folder, "response_portrait")["field"]) == {"density"}


def test_displacement_companion_panel_reads_damage_against_field_change(run_folder):
    outcome = _rendered(run_folder, "displacement_response")
    assert outcome.status == "ok", outcome.reason
    data = _figure_data(run_folder, "displacement_response__field-vorticity")
    assert data.loc[data["metric"] == "mse", "energy_changed"].notna().all()


def test_displacement_response_still_renders_without_energy_changed(run_folder):
    ctx = build_context(run_folder, bootstrap=0)
    ctx.df = ctx.df.drop(columns="energy_changed")
    rendered = {r.name: r for r in render(run_folder, ctx, only=["displacement_response"],
                                          formats=("png",))}
    assert rendered["displacement_response"].status == "ok"
    data = _figure_data(run_folder, "displacement_response__field-vorticity")
    assert "energy_changed" not in data.columns or data["energy_changed"].isna().all()


def test_deception_panel_says_which_metrics_have_no_damage_scale(run_folder):
    outcome = _rendered(run_folder, "deception_panel")
    assert outcome.status == "ok", outcome.reason
    data = _figure_data(run_folder, "deception_panel__field-vorticity").set_index("metric")
    assert not bool(data.loc["flat", "has_scale"])
    assert bool(data.loc["mse", "has_scale"])


# --- agreement in magnitude --------------------------------------------------------------------


def test_concordance_is_below_spearman_for_a_shape_twin(run_folder):
    outcome = _rendered(run_folder, "concordance_matrix")
    assert outcome.status == "ok", outcome.reason
    data = _figure_data(run_folder, "concordance_matrix")
    pair = data[(data["metric_a"] == "mae") & (data["metric_b"] == "mse")].iloc[0]
    assert pair["spearman"] == pytest.approx(1.0), "a monotone twin orders the ladder alike"
    assert pair["concordance"] < 0.99, "but charges different amounts"


def test_redundancy_dendrogram_leaves_out_the_metric_without_a_scale(run_folder):
    outcome = _rendered(run_folder, "redundancy_dendrogram")
    assert outcome.status == "ok", outcome.reason
    leaves = set(_figure_data(run_folder, "redundancy_dendrogram")["leaves"].iloc[0].split(";"))
    assert leaves == {"mae", "mse", "rmse"}


def test_section_seven_prose_quotes_the_participation_ratio(run_folder):
    ctx = build_context(run_folder, bootstrap=0)
    write_document(run_folder, ctx, render(run_folder, ctx, only=["response_portrait"],
                                           formats=("png",)))
    text = (run_folder.sections / "07_selectivity.tex").read_text()
    assert "independent directions" in text
    assert "\\texttt{flat}" in text, "the metric left out for lacking a scale is named"


@pytest.mark.parametrize("name", ["concordance_matrix", "redundancy_dendrogram"])
def test_magnitude_figures_skip_on_a_single_metric(run_folder, name):
    outcome = _rendered(run_folder, name, metric="mse")
    assert outcome.status == "skipped"


# --- the tables --------------------------------------------------------------------------------


def test_report_card_headers_are_plain_language_but_csv_columns_keep_their_names(run_folder):
    assert _rendered(run_folder, "report_card").status == "ok"
    tex = (run_folder.tables / "report_card.tex").read_text()
    assert "severity tracking (rank)" in tex and "selectivity" in tex
    header = (run_folder.data / "report_card.csv").read_text().splitlines()[0]
    assert "rho_min" in header and "blind_axes" in header, "the machine-readable names stay"


def test_axis_response_table_renders_or_skips_cleanly(run_folder):
    outcome = _rendered(run_folder, "axis_response")
    assert outcome.status == "ok", outcome.reason
    tex = (run_folder.tables / "axis_response__field-vorticity.tex").read_text()
    assert "\\begin{longtable}" in tex, "one row per metric and degradation needs page breaks"
    ctx = build_context(run_folder, bootstrap=0)
    ctx.axes = ctx.axes.drop(columns=["elasticity", "severity_10"])
    rendered = {r.name: r for r in render(run_folder, ctx, only=["axis_response"],
                                          formats=("png",))}
    assert rendered["axis_response"].status == "skipped"


def test_damage_by_level_table_names_the_metric_without_a_scale(run_folder):
    outcome = _rendered(run_folder, "damage_by_level_table")
    assert outcome.status == "ok", outcome.reason
    data = pd.read_csv(run_folder.data / "damage_by_level_table__field-vorticity.csv")
    assert {"mse", "mae", "rmse"} <= set(data.columns) and "flat" not in data.columns
    assert set(data["degradation"]) == {"translate_x", "translate_subpixel"}, "geometric only"
    tex = (run_folder.tables / "damage_by_level_table__field-vorticity.tex").read_text()
    assert "flat" in tex, "the note names the metric left out"


def test_damage_by_level_table_skips_on_a_single_metric(run_folder):
    assert _rendered(run_folder, "damage_by_level_table", metric="mse").status == "skipped"


# --- the headline ------------------------------------------------------------------------------


def test_summary_text_names_the_metric_in_a_comparison_folder(run_folder):
    """Four metrics on three fields: without the metric column the rows cannot be told apart."""
    ctx = build_context(run_folder, bootstrap=0)
    text = write_summary_text(run_folder, ctx).read_text()
    table = text.split("\n\n", 1)[1]
    assert table.splitlines()[0].split()[0] == "metric"
    assert "selectivity" in table.splitlines()[0]
    assert "independent directions" in text


def test_headline_prose_states_the_blindness_margin_from_the_analysis(run_folder):
    from fmeval import analysis

    ctx = build_context(run_folder, bootstrap=50)
    write_document(run_folder, ctx, render(run_folder, ctx, only=["report_card"],
                                           formats=("png",)))
    text = (run_folder.sections / "02_headline.tex").read_text()
    assert f"below {analysis.BLINDNESS_MARGIN:g}" in text
    assert "selectivity" in text and "elasticity" in text


def test_profile_table_is_the_source_of_the_headline_profile(run_folder):
    outcome = _rendered(run_folder, "profile_table")
    assert outcome.status == "ok", outcome.reason
    header = (run_folder.data / "profile_table.csv").read_text().splitlines()[0]
    for column in ("most_sensitive_axis", "least_sensitive_axis", "elasticity_displacement"):
        assert column in header



def test_response_curves_draw_one_record_per_metric_and_keep_the_unscaled_field_as_values(
        run_folder):
    """The per-metric curve figure: every family and field of one metric in one frame."""
    outcome = _rendered(run_folder, "response_curves")
    assert outcome.status == "ok", outcome.reason
    data = _figure_data(run_folder, "response_curves__metric-mse")
    assert set(data["degradation"]) == {"gaussian_blur", "translate_x", "translate_subpixel",
                                        "median_blur"}, "probes are not ladder levels"
    assert set(data["degradation_family"]) == {"stochastic", "geometric"}
    assert set(data["field"]) == set(FIELDS)
    assert data["has_scale"].all()
    assert np.isfinite(data["impostor_damage"]).all(), "the run has the impostor on every field"
    assert (data.loc[data["degradation"] == "median_blur", "n_frames"] == 8).all()
    flat = _figure_data(run_folder, "response_curves__metric-flat")
    assert not flat["has_scale"].any()
    assert flat["damage_median"].isna().all() and np.isfinite(flat["value_median"]).all()


def test_response_curves_survive_a_ladder_without_the_impostor(tmp_path):
    df = synthetic_rows(metrics=("mse", "mae"))
    df = df[df["degradation"] != "gaussian_impostor"]
    folder = _write_run(RunFolder(tmp_path / "noimp_1").create(), df)
    outcome = _rendered(folder, "response_curves")
    assert outcome.status == "ok", outcome.reason
    data = _figure_data(folder, "response_curves__metric-mse")
    assert data["impostor_damage"].isna().all()


def test_sensitivity_profile_rows_are_the_metric_s_ordinal_axes(run_folder):
    outcome = _rendered(run_folder, "sensitivity_profile")
    assert outcome.status == "ok", outcome.reason
    data = _figure_data(run_folder, "sensitivity_profile__metric-mae")
    assert set(data["degradation"]) == {"gaussian_blur", "translate_x", "translate_subpixel",
                                        "median_blur"}
    assert set(data["field"]) == set(FIELDS)
    assert (data["metric"] == "mae").all()
    assert data["blind"].dtype == bool
    assert {"rho", "rho_ci_lo", "cliffs_delta_min", "damage_per_change",
            "damage_max_ucb"} <= set(data.columns)


def test_sensitivity_profile_skips_without_the_response_statistics(run_folder, monkeypatch):
    """A folder analysed before the response columns existed declares itself unavailable."""
    ctx = build_context(run_folder, bootstrap=0)
    ctx.axes = ctx.axes.drop(columns=["cliffs_delta_min"])
    rendered = {r.name: r for r in render(run_folder, ctx, only=["sensitivity_profile"],
                                          formats=("png",))}
    outcome = rendered["sensitivity_profile"]
    assert outcome.status == "skipped" and "response statistics" in outcome.reason


def test_a_folder_from_before_these_columns_still_renders(tmp_path):
    """Every newer input missing at once: no energy_changed, calibration, severity_nominal or
    severity_name in the rows, and no anchor_label, probe_labels or preserves in run_meta.json."""
    import json

    df = synthetic_rows(metrics=("mse", "mae")).drop(columns=["energy_changed", "severity_name"])
    folder = _write_run(RunFolder(tmp_path / "old_1").create(), df)
    meta_path = folder.data / "run_meta.json"
    meta = json.loads(meta_path.read_text())
    for entry in meta.get("registries", {}).get("degradations", {}).values():
        for key in ("preserves", "calibration", "ensemble", "defaults", "fields"):
            entry.pop(key, None)
    meta.pop("anchor_label", None)
    meta.pop("probe_labels", None)
    meta_path.write_text(json.dumps(meta))
    assert not {"calibration", "severity_nominal"} & set(df.columns)

    ctx = build_context(folder, bootstrap=20)
    rendered = render(folder, ctx, formats=("png",))
    write_document(folder, ctx, rendered)
    assert not [r for r in rendered if r.status == "error"], \
        [(r.name, r.reason) for r in rendered if r.status == "error"]
    assert ctx.anchor_label == "uncorrelated"
