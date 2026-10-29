"""TEST_DESCRIPTION.md must document every quantity the suite reports.

Adding a reported column, a degradation, or a renderer without documenting it fails here.
That is the only mechanism that reliably keeps a document like this current: without it the
file describes whatever the code looked like on the day someone last remembered to edit it.
"""

from __future__ import annotations

import ast
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from degradations import registry as deg_registry
from fmeval import REPO
from fmeval import analysis as an
from fmeval.cards.prose import check_math
from fmeval.io import RunFolder, copy_documentation
from fmeval.pipeline import RESULT_DTYPES
from fmeval.report import driver  # noqa: F401  (imports the renderer modules)
from fmeval.report.latex import PACKAGES
from fmeval.report.registry import PLOTS
from metrics.registry import REDUCTIONS, metric
from tests.conftest import make_frame

DOC = REPO / "TEST_DESCRIPTION.md"

#: Columns that are provenance or grouping keys rather than measurements. They are still
#: documented, but grouped into one heading each rather than given a section apiece.
_GROUPED_HEADINGS = {
    "dataset", "dataset_family", "complexity_rank", "param_reynolds", "param_mach",
    "param_resolution", "trajectory", "frame_index", "time", "metric",
    "arity", "field", "seed", "wall_time_s", "degradation",
    "degradation_op", "degradation_family", "level", "severity", "severity_name",
    "variant_label", "analysis_grid", "remap_op", "rho_median", "rho_min",
    "rho_pooled_min", "monotone_fraction_min", "sensitivity_level_median",
    "saturation_level_median", "value_uncorrelated", "n_axes", "n_levels", "n_frames",
}


@pytest.fixture(scope="module")
def doc() -> str:
    assert DOC.exists(), "TEST_DESCRIPTION.md is missing"
    return DOC.read_text()


def documented_names(doc: str) -> set[str]:
    """Every identifier appearing in a `###` heading or in a table's first column."""
    names: set[str] = set()
    for line in doc.splitlines():
        if line.startswith("### "):
            names.update(re.findall(r"`([^`]+)`", line))
        elif line.startswith("| `"):
            names.update(re.findall(r"^\| `([^`]+)`", line))
    return names


def test_every_result_column_is_documented(doc):
    documented = documented_names(doc) | _GROUPED_HEADINGS
    missing = sorted(set(RESULT_DTYPES) - documented)
    assert not missing, f"undocumented result columns: {missing}"


def test_every_analysis_column_is_documented(doc):
    """Columns produced by summarise_axes, probe_summary and report_card."""
    df = make_frame(axes={"a": [1.0, 2.0, 3.0], "gaussian_impostor": [9.0],
                          "uncorrelated": [10.0, 10.0]})
    norm = an.normalisation(df)
    axes = an.summarise_axes(an.add_damage(df, norm), norm=norm, n_bootstrap=0)
    probes = an.probe_summary(df, norm)
    card = an.flag(an.report_card(axes, probes, norm), {"spearman": 0.9})

    produced: set[str] = set()
    for frame in (norm, axes, probes, card):
        produced |= set(frame.columns)
    produced |= {"damage"}
    # Probe columns are named <label>_<quantity>; document the quantity once.
    produced = {re.sub(r"^(gaussian_impostor|uncorrelated)_", r"\1_", c) for c in produced}

    documented = documented_names(doc) | _GROUPED_HEADINGS
    missing = sorted(produced - documented)
    assert not missing, f"undocumented analysis columns: {missing}"


def test_every_degradation_is_documented(doc):
    documented = documented_names(doc)
    missing = sorted(set(deg_registry.available()) - documented)
    assert not missing, f"undocumented degradations: {missing}"


def test_every_renderer_is_documented(doc):
    documented = documented_names(doc)
    # Tables are described by the quantities they contain rather than by name; figures
    # are listed individually, since a reader meets them as pictures.
    missing = sorted(set(PLOTS) - documented)
    assert not missing, f"undocumented figures: {missing}"


def test_the_flags_column_is_documented_as_advisory(doc):
    """A reader meeting a populated ``flags`` cell must not read it as a verdict.

    The rule that the suite measures and does not decide is for the people building this
    repository, and is pinned in AGENTS.md through ``PINNED_PHRASES``. What a reader of the
    numbers needs *here* is the factual half: that a flag is advisory.
    """
    assert "`flags`" in doc
    section = doc.split("### `flags`", 1)[1].split("\n### ", 1)[0]
    assert "advisory" in section.lower()
    assert "not** that the metric is approved" in section


def test_a_copy_is_placed_in_every_run_folder(tmp_path, doc):
    """A results directory must explain its own numbers after being sent to someone else."""
    folder = RunFolder(tmp_path / "m_1").create()
    copied = copy_documentation(folder)
    assert copied == folder.root / DOC.name
    assert copied.read_text() == doc


# --- AGENTS.md ---------------------------------------------------------------------------

AGENTS = REPO / "AGENTS.md"


def test_agents_file_exists_where_other_tools_look():
    """AGENTS.md is the cross-agent convention; the others must only point at it."""
    assert AGENTS.exists()
    for pointer in (REPO / ".github" / "copilot-instructions.md",
                    REPO / ".cursor" / "rules" / "repository.mdc"):
        assert pointer.exists(), f"{pointer} is missing"
        text = pointer.read_text()
        assert "AGENTS.md" in text, f"{pointer.name} does not point at AGENTS.md"
        assert len(text) < 2000, (
            f"{pointer.name} is long enough to have grown its own content; it must stay a "
            "pointer so it cannot drift from AGENTS.md"
        )


def test_agents_api_claims_match_the_code():
    """Signatures quoted in the instructions must still exist.

    An instruction file that describes an API the code no longer has is worse than none,
    because it is followed confidently.
    """
    text = AGENTS.read_text()
    for name in inspect.signature(metric).parameters:
        assert name in text, f"metric() parameter {name!r} is undocumented in AGENTS.md"
    for name in inspect.signature(deg_registry.degradation).parameters:
        assert name in text, f"degradation() parameter {name!r} is undocumented in AGENTS.md"
    for name in REDUCTIONS:
        assert name in text, f"reduction {name!r} is undocumented in AGENTS.md"
    for package in PACKAGES:
        assert package in text, f"LaTeX package {package!r} is undocumented in AGENTS.md"


def test_setup_check_runs_and_reports():
    """`check_setup.py` must work in the environment it is meant to diagnose."""
    result = subprocess.run([sys.executable, str(REPO / "check_setup.py")],
                            capture_output=True, text=True, timeout=180, cwd=REPO)
    assert result.returncode == 0, result.stdout + result.stderr
    for expected in ("numpy", "metrics registry", "degradations registry",
                     "spectral vorticity", "dataset root"):
        assert expected in result.stdout, f"check_setup.py does not report on {expected!r}"


# --------------------------------------------------------------------------------------
# The maths on the site
# --------------------------------------------------------------------------------------


def test_mathjax_is_configured_for_the_delimiters_arithmatex_emits():
    """MathJax must be told to look for what arithmatex wrote, not for what an author typed.

    Authors write ``$...$`` and ``$$...$$`` in ``card.md``, and ``prose.py`` enforces that
    subset because it is what GitHub also renders. But ``pymdownx.arithmatex`` in
    ``generic`` mode consumes those dollars at build time and re-emits every equation as
    ``\\(...\\)`` or ``\\[...\\]`` inside an element of class ``arithmatex``. MathJax 3
    treats ``inlineMath``/``displayMath`` as a *replacement* for its defaults, so a
    configuration naming the dollar forms silently drops the backslash forms, matches
    nothing, and leaves the raw LaTeX on the page.

    Nothing else catches that: the build succeeds, ``--strict`` is satisfied, no console
    error appears, and every equation on the site renders as its own source. This test asks
    arithmatex what it actually emits for the configuration in ``mkdocs.yml``, then checks
    the MathJax config declares those same delimiters.

    Skipped where the docs toolchain is not installed, so the fast suite stays
    dependency-free; it runs in the docs job, where the toolchain is present by
    definition.
    """
    markdown = pytest.importorskip(
        "markdown", reason="the docs toolchain is not installed in this environment"
    )
    pytest.importorskip("pymdownx", reason="the docs toolchain is not installed")

    config = yaml.safe_load((REPO / "mkdocs.yml").read_text())
    options = next(
        entry["pymdownx.arithmatex"]
        for entry in config["markdown_extensions"]
        if isinstance(entry, dict) and "pymdownx.arithmatex" in entry
    )
    html = markdown.markdown(
        "Inline $a$ and a display equation:\n\n$$\nb = c \\tag{1}\n$$\n",
        extensions=["pymdownx.arithmatex"],
        extension_configs={"pymdownx.arithmatex": options},
    )
    assert 'class="arithmatex"' in html, (
        "arithmatex produced no wrapper element; the extension configuration in "
        "mkdocs.yml is not what this test assumes"
    )

    # As written in the JavaScript source, where each backslash is escaped.
    emitted = {opening: rf"\\{opening[-1]}"
               for opening in (r"\(", r"\[") if opening in html}
    assert emitted, f"arithmatex emitted no recognised delimiter; got: {html!r}"

    js = (REPO / "docs" / "javascripts" / "mathjax.js").read_text()
    missing = sorted(rendered for rendered in emitted.values() if rendered not in js)
    assert not missing, (
        f"docs/javascripts/mathjax.js does not declare {missing}, which is what "
        "arithmatex emits. Every equation on the site will render as raw LaTeX, and "
        "nothing else will report a problem. Set tex.inlineMath and tex.displayMath to "
        "the delimiters listed above."
    )


# --------------------------------------------------------------------------------------
# The human file guide
# --------------------------------------------------------------------------------------

GUIDE = REPO / "docs" / "working-with-the-repo.md"


def test_the_file_guide_starts_with_a_summary_table():
    """A reader looking up one file should not have to read the whole document."""
    head = GUIDE.read_text().split("## The bundle files in detail")[0]
    assert "| File | What it is | Who edits it | When |" in head


# --------------------------------------------------------------------------------------
# The instruction files, each pinned by the phrases it must keep
# --------------------------------------------------------------------------------------

#: Phrases each instruction file must still contain, keyed by its path in the repository.
PINNED_PHRASES = {
    # AGENTS.md is what an agent follows, so it must carry:
    #   - a section for each registry a contributor might extend, and for tests and LaTeX;
    #   - the rules whose violation silently corrupts results: check the exit status before
    #     claiming success (RC=$?), never hand-edit generated LaTeX, never slice the time
    #     axis (the multi-gigabyte read), non-square fixtures (the transpose trap),
    #     severity_direction (the inverted ladder), no verdicts, one source of truth, a
    #     config file stating a key only to change it, reuse before writing, imports at the
    #     top, rules stated without their history, and shared test helpers;
    #   - the bundle workflow and no other: a metric outside a bundle does not import, and
    #     an agent would have no way to learn why from this file;
    #   - the card prohibitions, which exist because breaking them produces plausible, wrong
    #     documentation;
    #   - a pointer to the recipes, so an agent reading only the summary is sent onward.
    "AGENTS.md": (
        "Adding a metric", "Adding a degradation", "Adding a data source",
        "Adding a figure or table", "Writing tests", "How to treat the LaTeX output",
        "RC=$?", "Never hand-edit", "Never slice the time axis", "non-square",
        "severity_direction", "does not decide", "Define every value once",
        "Grep before you write", "states a key only to change it", "never writes `cfg",
        "Imports at the top of the file",
        "State the rule, not its history", "never import from another `test_*.py` module",
        "python -m fmeval.cards new", "python -m fmeval.cards check",
        "python -m fmeval.cards evidence", "python -m fmeval.cards exemplars",
        "card.yaml", "card.md", "docs/catalog.json", "<!-- GENERATED",
        "Never invent a number", "Never state expected behaviour",
        "never edit `_generated/`", "never sign a card",
        "docs/recipes/", "Delete an issue once it is fully resolved",
        # A built metric left in the plan reads as work still to do.
        "docs/ideas/README.md",
    ),
    # Every agent profile, and the issues index itself, says that `issues/` holds only open
    # items: an issue left in place after it is fully resolved reads as work still to do.
    "CLAUDE.md": ("Delete an issue once it is fully resolved",),
    ".github/copilot-instructions.md": ("Delete an issue once it is fully resolved",),
    ".cursor/rules/repository.mdc": ("Delete an issue once it is fully resolved",),
    "issues/README.md": ("Delete an issue once it is fully resolved", "there is no resolved list"),
    # docs/decisions.md stops an agent from "fixing" a deliberate absence. Each entry
    # corresponds to an enforced decision; if one is removed here it will be rediscovered
    # as a mysterious test failure by whoever trips over it next.
    "docs/decisions.md": (
        "no predictions", "no pass or fail", "no word counts", "no metric IDs",
        "<!-- GENERATED", "never sign", "at `get()`, not at import", "stops the run",
        "docs/recipes/",
    ),
    # The human file guide. A guide that has fallen behind the bundle contract sends a
    # reader to a file that is gone, so every file a contributor is expected to create or
    # to leave alone is named in it (coverage, not quality); and its job is to make the
    # workflow runnable without a second document, so it names the card commands.
    "docs/working-with-the-repo.md": (
        "metric.py", "degradation.py", "card.yaml", "card.md", "refs.bib",
        "test_metric.py", "_generated/", "AGENTS.md", "TEST_DESCRIPTION.md",
        "configs/", "issues/",
        "fmeval.cards new", "fmeval.cards check", "fmeval.cards sign",
    ),
    # The recipes in docs/recipes/ are the canonical instructions for extending the
    # repository; AGENTS.md summarises and points at them. They are separate files, each
    # asserted here by name, precisely so that no single careless edit can destroy the
    # instructions: an agent that overwrites AGENTS.md loses a summary, and an edit that
    # guts a recipe fails CI naming that recipe. Destroying the instructions would require
    # deliberately editing several named files and this test together.
    "docs/recipes/index.md": (
        "Never invent a number",
        "Never invent a citation",
        "Never state expected behaviour",
        "never sign a card",
        "report it rather than writing around it",
        "Reuse before you write",
        "Prove that a refactor changes no number",
    ),
    "docs/recipes/add-a-metric.md": (
        "python -m fmeval.cards new <name>",
        "python -m fmeval.cards check",
        "test_metric.py",
        "### Boundary handling",
        "python -m fmeval.cards evidence",
        "python -m fmeval.cards catalog",
        "equation number",
        "worked example",
        "docs/ideas/README.md",
    ),
    "docs/recipes/add-a-degradation.md": (
        "--kind degradation",
        "severity_direction",
        "configs/degradation/default.yaml",
        "FAMILY_BLOCKS",
        "FAMILY_INFO",
        "exemplars",
        "python -m fmeval.cards exemplars <name>",
        "mode: draws",
    ),
    "docs/recipes/add-a-dataset.md": (
        "configs/dataset/",
        "_re5e4_simulation",
        "names the key an option forgot",
        "fmeval/data/base.py",
        "Never slice the time axis",
        "calibration.csv",
        "severity_degenerate",
        "evidence_datasets",
        "configs/cards/default.yaml",
        "developed",
    ),
    "docs/recipes/add-a-diagnostic.md": (
        "fmeval/cards/diagnostics.py",
        "@diagnostic",
        "ctx.limits",
        "show_field",
        "numbers behind the picture",
        "exemplar_panel",
    ),
    "docs/recipes/verify-a-refactor.md": (
        "any difference beyond the stated tolerance is a bug you introduced",
        "every column is compared except",
        "docs/recipes/compare_runs.py",
        "variant_label",
        "_IMPORT_ERRORS",
        "dataset=kinet_re5e4_dev",
        "Rows are missing",
        "Values differ",
    ),
    "docs/recipes/refresh-the-evidence.md": (
        "evidence --all",
        "python -m fmeval.cards catalog",
        "typed into sentences do not",
        "issues/032",
        "does **not** invalidate a signature",
    ),
}


@pytest.mark.parametrize("name", sorted(PINNED_PHRASES))
def test_each_instruction_file_still_carries_its_pinned_phrases(name):
    """Each instruction file still says what ``PINNED_PHRASES`` records for it.

    Prose wraps at the margin, so a pinned phrase may be split across lines; comparing with
    whitespace collapsed and case folded keeps the pins about content, not layout. Each
    phrase is chosen to stay specific under that folding.
    """
    path = REPO / name
    assert path.is_file(), f"{name} is missing"
    text = " ".join(path.read_text().split()).lower()
    for required in PINNED_PHRASES[name]:
        assert " ".join(required.split()).lower() in text, (
            f"{name} no longer says {required!r}. These files are the canonical "
            "instructions; if this changed deliberately, update this test in the same "
            "commit and say why in its message."
        )


# --------------------------------------------------------------------------------------
# The ideas section: hand-written plans for metrics that are not built yet
# --------------------------------------------------------------------------------------

IDEAS = REPO / "docs" / "ideas"
#: The tracker's two-letter identifiers (OT-1, NM-3, ...). Retired: an idea is named by its
#: page, and a reader who was never told the scheme cannot decode a prefix.
_RETIRED_ID = re.compile(r"\b(?:OT|SH|NM|CG|PH|PD|TD|BD|PS|IN)-\d")


DATASETS = REPO / "docs" / "datasets"


@pytest.mark.parametrize("page", sorted(p.relative_to(REPO / "docs").as_posix()
                                        for d in (IDEAS, DATASETS) for p in d.rglob("*.md")))
def test_an_idea_or_dataset_page_follows_the_site_conventions(page):
    """Idea and dataset pages obey the rules the cards obey, since all render on GitHub and
    the site.

    Equations use only the dollar forms both readers render; the retired tracker IDs and the
    word "rung" (say "severity level") stay out.
    """
    text = (REPO / "docs" / page).read_text()
    assert check_math(text) == [], f"docs/{page}: {check_math(text)}"
    assert not _RETIRED_ID.search(text), (
        f"docs/{page} uses a retired tracker ID "
        f"{_RETIRED_ID.search(text).group(0)!r}; name the idea instead"
    )
    assert not re.search(r"\brungs?\b", text, re.IGNORECASE), (
        f"docs/{page} says 'rung'; say 'severity level'"
    )


@pytest.mark.parametrize("config", sorted(p.name for p in (REPO / "configs" / "dataset").glob(
    "*.yaml") if not p.name.startswith("_")))
def test_every_dataset_is_on_the_page_of_its_problem(config):
    """One page per physical problem, holding every configuration of it.

    The page is named by the config's ``complexity.family``, which a fragment may supply, so
    the family is read through the defaults chain. Both the page and the index link must
    exist, and the page must name the configuration.
    """
    chain, family = [config], None
    while family is None and chain:
        data = yaml.safe_load((REPO / "configs" / "dataset" / chain.pop()).read_text())
        family = (data.get("complexity") or {}).get("family")
        chain += [f"{d}.yaml" for d in data.get("defaults", []) if d != "_self_"]
    assert family, f"configs/dataset/{config} has no complexity.family"
    page = DATASETS / f"{family}.md"
    assert page.is_file(), (
        f"configs/dataset/{config} belongs to problem {family!r}, which has no page "
        f"docs/datasets/{family}.md; see docs/recipes/add-a-dataset.md step 6"
    )
    name = config.removesuffix(".yaml")
    assert f"`{name}`" in page.read_text(), f"docs/datasets/{family}.md does not name {name}"
    assert f"({family}.md)" in (DATASETS / "README.md").read_text(), (
        f"docs/datasets/README.md does not link {family}.md"
    )


def test_an_idea_is_removed_once_it_is_built():
    """No idea page is named after a metric that exists.

    Once a metric is built its card is the only record of it, and the idea's row and page
    are deleted in the same change (docs/recipes/add-a-metric.md). This catches an idea built
    under its own name; one built under a different name is caught only by that recipe step.
    """
    catalog = json.loads((REPO / "docs" / "catalog.json").read_text())
    built = {e["name"] for e in catalog["entries"] if e["kind"] == "metric"}
    idea_stems = {p.stem for p in IDEAS.rglob("*.md")}
    # Either set coming back empty would make the intersection below pass for no reason.
    assert built, "docs/catalog.json lists no metrics; the catalog format has changed"
    assert idea_stems, f"no idea pages under {IDEAS}; the ideas section has moved"
    stale = sorted(idea_stems & built)
    assert not stale, (
        f"{stale} are built metrics but still have idea pages; delete each page, its row in "
        "docs/ideas/README.md and its link on the theme page"
    )


def test_every_idea_has_a_row_and_every_row_a_page():
    """The overview table and the idea pages correspond one to one."""
    overview = (IDEAS / "README.md").read_text()
    # A row's page is the first link to a page inside a theme directory, wherever it sits in
    # the row's first cell, so a title containing brackets or a cell not starting with the
    # link is still read. Theme links point at a README and are excluded by the pattern.
    linked = [
        m.group(1)
        for line in overview.splitlines() if line.startswith("|")
        for m in [re.search(r"\]\(([a-z0-9_]+/(?!README)[a-z0-9_]+\.md)\)", line.split("|")[1])]
        if m
    ]
    rows = set(linked)
    pages = {p.relative_to(IDEAS).as_posix() for p in IDEAS.glob("*/*.md")
             if p.name != "README.md"}
    assert pages, f"no idea pages under {IDEAS}; the ideas section has moved"
    assert len(linked) == len(rows), (
        f"pages with more than one row: {sorted(r for r in rows if linked.count(r) > 1)}"
    )
    assert rows == pages, (
        f"rows without a page: {sorted(rows - pages)}; "
        f"pages without a row in docs/ideas/README.md: {sorted(pages - rows)}"
    )


# --------------------------------------------------------------------------------------
# One source of truth, checked mechanically where a check is cheap and exact
# --------------------------------------------------------------------------------------


def _python_sources(*roots: str) -> list[Path]:
    return [p for root in roots for p in sorted((REPO / root).rglob("*.py"))
            if "_template" not in p.parts and "__pycache__" not in p.parts]


def test_the_issues_folder_holds_only_open_items():
    """A fully resolved issue is deleted, so no status may begin by calling it resolved, and the
    index and the files must list the same issues."""
    issues = sorted((REPO / "issues").glob("[0-9]*.md"))
    resolved = [p.name for p in issues
                if re.search(r"^\*\*Status:\*\*\s*resolved", p.read_text(), re.I | re.M)]
    assert not resolved, f"delete these resolved issues (issues/README.md): {resolved}"
    index = (REPO / "issues" / "README.md").read_text()
    indexed = set(re.findall(r"\]\((\d{3}-[^)]+\.md)\)", index))
    on_disk = {p.name for p in issues}
    assert indexed == on_disk, (
        f"issues/README.md and issues/ disagree: indexed only {sorted(indexed - on_disk)}, "
        f"on disk only {sorted(on_disk - indexed)}")


def test_no_test_module_imports_from_another_test_module():
    """Shared test helpers live in ``tests/conftest.py``, never in a ``test_*`` module.

    A test module is collected by pytest, not a library: a helper imported out of one gets
    copied into the next file whenever the import feels awkward, and the copies drift.
    """
    # Any module path with a `test_` component: `tests.test_x`, or another bundle's
    # `..mse.test_metric`. A bundle test importing its own `.metric` does not match.
    pattern = re.compile(r"^\s*(from|import)\s+[\w.]*\btest_\w+(\s+import|\s*$)", re.M)
    offenders = [str(p.relative_to(REPO)) for p in _python_sources("tests", "metrics",
                                                                    "degradations")
                 if p.name != Path(__file__).name and pattern.search(p.read_text())]
    assert not offenders, (
        f"{offenders} import from another test module; move the helper to tests/conftest.py"
    )


def test_no_module_level_alias():
    """A module-level ``NAME = other_name`` is a second name for one thing; import the original.

    An alias is a copy a reader has to resolve, whatever reason is written beside it. Only an
    assignment whose value is a bare name or attribute chain counts, so a value computed by a
    call is untouched.
    """
    aliases = []
    for path in _python_sources("fmeval", "metrics", "degradations", "tests", "docs"):
        for node in ast.parse(path.read_text()).body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            value = node.value
            if (isinstance(value, (ast.Name, ast.Attribute))
                    and not any(isinstance(n, ast.Call) for n in ast.walk(value))):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                names = [t.id for t in targets if isinstance(t, ast.Name)]
                if names and names != ["pytestmark"]:
                    aliases.append(f"{path.relative_to(REPO)}:{node.lineno} {names[0]} = "
                                   f"{ast.unparse(value)}")
    assert not aliases, f"module-level aliases; import the original instead: {aliases}"


def test_imports_sit_at_the_top_of_the_file():
    """An import inside a function hides a dependency from the reader of the module's head.

    Only an import guarded by ``if``/``else`` or ``try``/``except`` (an optional dependency) may
    sit elsewhere. The vendored ``fmeval/external`` code is left as it was published.
    """
    sources = [p for p in _python_sources("fmeval", "metrics", "degradations", "tests", "docs")
               if "external" not in p.parts] + sorted(REPO.glob("*.py"))
    local = []
    for path in sources:
        tree = ast.parse(path.read_text())
        guarded = {id(n) for g in ast.walk(tree) if isinstance(g, (ast.If, ast.Try))
                   for n in ast.walk(g)}
        local += [f"{path.relative_to(REPO)}:{n.lineno}"
                  for f in ast.walk(tree) if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
                  for n in ast.walk(f)
                  if isinstance(n, (ast.Import, ast.ImportFrom)) and id(n) not in guarded]
    assert not local, f"imports inside a function; move them to the top of the file: {local}"


def test_the_degradation_families_are_listed_once():
    """Only the registry enumerates the families, and only the vocabulary describes them.

    A literal holding five or more family names anywhere else is a second list of them, which
    would have to be kept in step with the registry by hand.
    """
    allowed = {REPO / "degradations" / "registry.py", REPO / "fmeval" / "report" / "vocabulary.py",
               Path(__file__)}
    copies = []
    for path in _python_sources("fmeval", "metrics", "degradations", "tests", "docs"):
        if path in allowed:
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            items = (node.keys if isinstance(node, ast.Dict)
                     else node.elts if isinstance(node, (ast.List, ast.Tuple, ast.Set)) else [])
            named = ({i.value for i in items if isinstance(i, ast.Constant)}
                     & set(deg_registry.FAMILIES))
            if len(named) >= 5:
                copies.append(f"{path.relative_to(REPO)}:{node.lineno}")
    assert not copies, f"a second list of the degradation families at {copies}"
