"""The card contract: what every bundle must carry, and what a bad card must say.

Two kinds of test live here. The first checks the schema and the prose rules against
hand-built examples, so a change to the rules shows up as a specific failure rather than
as twenty bundles going red at once. The second is parametrized over every bundle on
disk, so a real bundle that drifts out of contract names itself.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
from argparse import Namespace

import numpy as np
import pandas as pd
import pytest
import yaml
from scipy.ndimage import gaussian_filter

from degradations import registry as deg_registry
from fmeval import CONFIGS, REPO, analysis
from fmeval import config as fmeval_config
from fmeval.cards import catalog, cli, evidence, exemplars, loader, prose, review
from fmeval.cards.figures import Column, _row_limits, exemplar_panel
from fmeval.cards.metric_figures import ALT_TEXT, METRIC_FIGURES, metric_figures
from fmeval.cards.overview import overview_figures, page_markdown
from fmeval.cards.schema import CATEGORIES, SCHEMA_VERSION, STATUSES, CardError, parse_card
from fmeval.report import vocabulary
from fmeval.report.style import OKABE_ITO
from metrics import registry as metric_registry
from tests.conftest import make_frame, synthetic_rows

# --------------------------------------------------------------------------------------
# A minimal valid card, used as the base for the negative tests
# --------------------------------------------------------------------------------------

VALID_METRIC_CARD = {
    "schema_version": SCHEMA_VERSION,
    "name": "example",
    "kind": "metric",
    "category": "pointwise",
    "summary": "An example card used by the tests, long enough to satisfy the floor.",
    "status": "candidate",
    "owners": ["khegazy"],
    "output": {
        "description": "Mean over cells of the squared difference.",
        "bounds": {"lower": 0.0, "upper": None},
    },
    "math": {
        "triangle_inequality": False,
        "scale_dependent": True,
        "resolution_dependent": True,
        "complexity": "O(N)",
    },
}


def card(**overrides):
    """A valid card mapping with the given keys replaced."""
    data = {k: (v.copy() if isinstance(v, dict) else v) for k, v in VALID_METRIC_CARD.items()}
    data.update(overrides)
    return data


def parse(data):
    return parse_card(data, where="test card")


# --------------------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------------------


def test_a_minimal_card_parses():
    parsed = parse(card())
    assert parsed.name == "example"
    assert parsed.status == "candidate"


@pytest.mark.parametrize("missing", ["name", "kind", "category", "summary", "status", "owners"])
def test_every_required_key_is_required(missing):
    data = card()
    del data[missing]
    with pytest.raises(CardError, match=missing):
        parse(data)


@pytest.mark.parametrize("overrides,match", [
    # A key nothing reads is a claim nothing checks, which is the failure mode the card
    # system exists to prevent. A typo -- here a `math` key written at the top level --
    # must not pass silently.
    pytest.param({"triangle_inequality": True}, "unrecognised key", id="unknown-key"),
    # Nothing in a card may state how a metric is expected to behave. A statement about
    # behaviour is either measured -- and then it belongs in the generated evidence -- or
    # it comes from published work, and then it belongs in `## Definition` or
    # `## Assessment` with a citation. An unsourced prediction is an opinion, and an
    # opinion in structured YAML reads like a finding.
    pytest.param({"expectations": [{"axis": "translate_x", "response": "increasing"}]},
                 "unrecognised key", id="prediction"),
    # The category comes from a closed vocabulary, which is what the navigation groups by.
    pytest.param({"category": "fluids"}, "category", id="unknown-category"),
    # Bounds whose lower end is not below the upper describe no range at all.
    pytest.param({"output": {"description": "Something measurable.",
                             "bounds": {"lower": 1.0, "upper": 0.0}}},
                 "not below", id="unordered-bounds"),
    # A card from the future may use fields this code cannot interpret. Refusing is the
    # only safe answer; the error tells the reader to update rather than to edit the card.
    pytest.param({"schema_version": SCHEMA_VERSION + 1}, "newer than this checkout",
                 id="newer-schema"),
    # A review signature records the digest of the prose it stands behind.
    pytest.param({"review": {"prose_sha256": "not-a-hash", "reviewer": "x",
                             "date": "2026-08-18"}}, "sha256", id="signature-not-a-digest"),
])
def test_a_malformed_card_is_refused(overrides, match):
    """A card that breaks the schema is refused with an error naming what is wrong."""
    with pytest.raises(CardError, match=match):
        parse(card(**overrides))


def test_status_vocabulary_is_closed_and_has_no_rejected_value():
    """`rejected` is absent on purpose: nothing here reduces a metric to pass or fail.

    `control` is absent too, and for a different reason. It would answer "what kind of thing
    is this" while the other values answer "how far has the work got", so a metric could not
    be both a familiar baseline and unreviewed -- the field would have to pick one. What kind of
    measurement a metric makes is `category`, which is orthogonal to this and is what the
    navigation groups by.
    """
    assert "rejected" not in STATUSES
    assert "control" not in STATUSES
    assert set(STATUSES) == {"candidate", "validated", "deprecated"}
    with pytest.raises(CardError, match="status"):
        parse(card(status="rejected"))


def test_every_degradation_family_has_one_entry_for_its_label_colour_and_wording():
    """Each registered family is shown with one label, one colour and one phrase.

    All three live in one table, ``vocabulary.FAMILY_INFO``, checked here against the
    registry: a family missing from it would reach the reader as a bare code, in blue, under
    no card heading.
    """
    families = set(deg_registry.FAMILIES) - {"identity"}
    # `identity` labels the reference severity level rather than a kind of damage.
    assert set(vocabulary.FAMILY_INFO) == families, (
        f"fmeval/report/vocabulary.py:FAMILY_INFO covers {sorted(vocabulary.FAMILY_INFO)}, "
        f"the registry defines {sorted(families)}"
    )
    unknown = {k: f.colour for k, f in vocabulary.FAMILY_INFO.items()
               if f.colour not in OKABE_ITO}
    assert not unknown, f"family colours outside the Okabe-Ito palette: {unknown}"


def test_every_metric_type_can_be_said_in_words_on_the_site():
    """A type with no plain-language phrase would reach the reader as a bare code."""
    empty = sorted(code for code, said in CATEGORIES.items() if not said.strip())
    assert not empty, f"categories with no wording for the site: {empty}"


def test_a_degradation_card_category_is_its_registry_family():
    """The card's `category` and the operator's `family` are one fact, stored twice.

    The site labels a degradation page from its card and groups the gallery from the
    registry, so a bundle whose two disagree is filed under one name and described by
    another.
    """
    wrong = []
    for bundle in (b for b in loader.iter_bundles() if b.kind == "degradation"):
        card = loader.load_card(bundle)
        family = deg_registry.get(bundle.name).family
        if card.category != family:
            wrong.append(f"{bundle.name}: card says {card.category!r}, registry says {family!r}")
    assert not wrong, "\n".join(wrong)


def test_a_metric_card_needs_its_math_block():
    data = card()
    del data["math"]
    with pytest.raises(CardError, match="math"):
        parse(data)


def test_an_older_schema_version_without_a_migration_is_refused():
    """No migration exists yet, so an older card is refused with the fix rather than read as
    if it were current."""
    with pytest.raises(CardError, match="no migration"):
        parse(card(schema_version=SCHEMA_VERSION - 1))


def test_the_bounds_order_error_shows_the_bounds_compared():
    """Bounds are converted to floats once; equal bounds are refused, and the message shows
    the two values that were compared."""
    with pytest.raises(CardError, match=r"lower \(1\.0\) is not below upper \(1\.0\)"):
        parse(card(output={"description": "Something measurable.",
                           "bounds": {"lower": 1, "upper": 1}}))


@pytest.mark.parametrize("section, value, key", [
    # `output` holds a description and bounds. A misspelt key here would document a
    # property of the output that no tool ever reads.
    pytest.param("output", {"description": "Something measurable.", "n_draw": 3},
                 "output.n_draw", id="output"),
    # The bounds sit one level deeper; a misspelt `upper` would leave the bound unset
    # while the card appeared to state it.
    pytest.param("output", {"description": "Something measurable.",
                            "bounds": {"lower": 0.0, "uper": 1.0}},
                 "output.bounds.uper", id="output-bounds"),
    # Symmetry is declared on the @metric decorator, so a `symmetric` key in the card
    # would be a second, unchecked answer to the same question.
    pytest.param("math", {**VALID_METRIC_CARD["math"], "symmetric": True},
                 "math.symmetric", id="math"),
    # `levels` is the key the panel reads; `level` would leave the panel without
    # severities while the card appeared to choose them.
    pytest.param("exemplars", {"mode": "none", "level": [1.0]},
                 "exemplars.level", id="exemplars"),
    # The review date is stored under `date`, the key `cards sign` writes; any other
    # spelling is refused rather than read as an alternative.
    pytest.param("review", {"prose_sha256": "0" * 64, "reviewer": "someone",
                            "reviewed_at": "2026-01-01"},
                 "review.reviewed_at", id="review"),
])
def test_an_unknown_key_inside_a_section_is_rejected(section, value, key):
    """Every nested section refuses keys it does not define, as the top level does, and the
    message names the key with its section so the reader can find it."""
    with pytest.raises(CardError, match=rf"unrecognised key\(s\): {re.escape(key)}\."):
        parse(card(**{section: value}))


def test_a_degradation_card_must_illustrate_itself():
    """A degradation whose effect is never shown cannot be understood from prose alone."""
    data = card(kind="degradation", category="smoothing")
    del data["math"]
    with pytest.raises(CardError, match="exemplars"):
        parse(data)


def test_severity_exemplars_need_exactly_three_ordered_levels():
    base = card(kind="degradation", category="smoothing")
    del base["math"]
    rationale = "Weak is at the grid limit, strong removes the inertial range."
    with pytest.raises(CardError, match="three"):
        parse({**base, "exemplars": {"mode": "severity", "levels": [1.0, 4.0],
                                     "rationale": rationale}})
    # Ordering is checked against the operator's declared severity_direction, in
    # fmeval.cards.loader, rather than here: for band_attenuate a smaller number is a
    # stronger degradation, so a numeric sort would call its correct ordering wrong.
    descending = parse({**base, "exemplars": {"mode": "severity", "levels": [16.0, 4.0, 1.0],
                                              "rationale": rationale}})
    assert descending.exemplars.levels == (16.0, 4.0, 1.0)


def test_exemplar_order_is_checked_against_the_declared_direction():
    """A decreasing-severity operator lists its exemplars largest first, and that is right.

    band_attenuate states a *retained* fraction, so 0.8 is milder than 0.0. The check
    lives where the registry spec is in hand, because "weakest" is not a numeric fact.
    """
    card = loader.load_card(loader.find_bundle("band_attenuate"))
    assert card.exemplars.levels == (0.8, 0.5, 0.0)
    spec = deg_registry.get("band_attenuate")
    loader._validate_spec(spec, "degradation")  # must not raise

    inverted = dataclasses.replace(spec, severity_direction="increasing")
    with pytest.raises(CardError, match="weakest to strongest"):
        loader._validate_spec(inverted, "degradation")


def test_every_exemplar_strength_is_one_a_ladder_runs():
    """A degradation's panel shows strengths the evaluation really applies (``schema.py``,
    ``Exemplars.levels``), so a reader can match each column to a row of the results."""
    runs: dict[str, set[float]] = {}
    for option in sorted(f.stem for f in (CONFIGS / "degradation").glob("*.yaml")
                         if not f.name.startswith("_")):
        ladder = fmeval_config.compose_config(f"degradation={option}").degradation.ladder
        for label, entry in ladder.items():
            runs.setdefault(entry.get("op", label), set()).update(entry.severities)
    outside = {}
    for bundle in (b for b in loader.iter_bundles() if b.kind == "degradation"):
        exemplars = loader.load_card(bundle).exemplars
        if exemplars is not None and exemplars.mode == "severity":
            extra = sorted(set(exemplars.levels) - runs.get(bundle.name, set()))
            if extra:
                outside[bundle.name] = extra
    assert not outside, f"card strengths no configs/degradation/ ladder runs: {outside}"


def test_a_degradation_without_an_ordered_severity_uses_draws_instead():
    """The phase-randomised impostor has no severity, and the unrelated-field anchor is
    indexed by draw number. Neither can be shown as weak/medium/strong."""
    base = card(kind="degradation", category="stochastic")
    del base["math"]
    parsed = parse({**base, "exemplars": {
        "mode": "draws", "n_draws": 3,
        "rationale": "Severity is meaningless here; independent draws show the spread.",
    }})
    assert parsed.exemplars is not None
    assert parsed.exemplars.mode == "draws"
    assert parsed.exemplars.levels == ()


def test_a_review_round_trips():
    parsed = parse(card(review={"prose_sha256": "a" * 64, "reviewer": "khegazy",
                                "date": "2026-08-18"}))
    assert parsed.review is not None
    assert parsed.review.date == dt.date(2026, 8, 18)


# --------------------------------------------------------------------------------------
# Prose
# --------------------------------------------------------------------------------------


def build_prose(name="example", **bodies):
    """Assemble a metric card.md with every required section present."""
    defaults = {section: f"Body for {section}. " * 40 for section in prose.METRIC_SECTIONS}
    defaults["Intuition"] = (
        "A physical picture without symbols. " * 30
        + "\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
        + "It ignores where a feature sits."
    )
    defaults["Definition"] = (
        "Body for Definition. " * 20
        + "\n\n### Boundary handling\n\nNone. The operation is local to each cell."
    )
    defaults["Performance"] = "<!-- GENERATED performance: written by `python -m fmeval.cards evidence example`, do not edit -->\n\nplaceholder\n\n<!-- END GENERATED performance -->"
    defaults["Results"] = (
        "### Smoothing\n\n"
        "[gaussian_blur](../../degradations/gaussian_blur/card.md)\n\n"
        "<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence example`, do not edit -->\n\nplaceholder\n\n<!-- END GENERATED results_smoothing -->\n\n"
        + "What the smoothing axes found, stated in enough words to clear the floor. " * 4
    )
    defaults["References"] = "\\bibliography"
    defaults.update(bodies)
    text = f"---\nname: {name}\nkind: metric\n---\n\n"
    for section in prose.METRIC_SECTIONS:
        text += f"## {section}\n\n{defaults[section]}\n\n"
    return text


def problems_for(text, **kwargs):
    kwargs.setdefault("kind", "metric")
    kwargs.setdefault("name", "example")
    return prose.check_prose(text, **kwargs)


def test_a_complete_card_has_no_prose_problems():
    """The defaults include the accepted forms most often doubted: a Performance section that
    is nothing but its generated include, and "None." as the boundary-handling answer."""
    assert problems_for(build_prose()) == []


def test_sections_must_be_in_the_fixed_order():
    text = build_prose()
    first, second, third = prose.METRIC_SECTIONS[:3]
    a, b, c = (text.index(f"## {s}") for s in (first, second, third))
    swapped = text[:a] + text[b:c] + text[a:b] + text[c:]
    assert any("out of order" in p.message for p in problems_for(swapped))


def test_the_declared_order_is_the_one_the_cards_use():
    """The order is a decision, so it is written down once and asserted here.

    Definition first: the equation is the thing being documented, and every later section
    is commentary on it. The account of the metric itself finishes with Limitations, and
    only then does the card turn to what this repository measured -- so a reader adopting
    the metric elsewhere can stop after Limitations and have everything that holds
    independently of our runs.
    """
    assert prose.METRIC_SECTIONS == (
        "Definition",
        "Performance",
        "Intuition",
        "Reading the output",
        "Limitations",
        "Results",
        "References",
    )
    assert prose.DEGRADATION_SECTIONS == (
        "Definition",
        "Intuition",
        "Severity scale",
        "Limitations",
        "What the degradation looks like",
        "References",
    )


@pytest.mark.parametrize("text,fragment", [
    # A section renamed or dropped is named in the problem.
    pytest.param(build_prose().replace("## Limitations", "## Limits"), "Limitations",
                 id="missing-section"),
    # Intuition is the one section a reader from another field is guaranteed to read, so it
    # may not contain notation.
    pytest.param(build_prose(Intuition="The error is $\\sum (a-b)^2$ over cells. " * 30
                             + "\n\n```\n1 2\n```\n"),
                 "mathematical notation", id="notation-in-intuition"),
    # Intuition must also show a worked example; words alone do not.
    pytest.param(build_prose(Intuition="Words about the idea, but no numbers anywhere. " * 30),
                 "worked example", id="no-worked-example"),
    # Boundary handling is the detail most likely to differ silently between two
    # implementations. Periodic wrap, reflection, zero padding and dropping the edge give
    # different numbers from the same formula, and a reader comparing across projects
    # cannot tell which was used. Silence and "none" look identical; only one is a claim.
    pytest.param(build_prose(Definition="An equation and some words about it. " * 10),
                 "Boundary handling", id="no-boundary-handling"),
    # A number typed into the performance summary is a claim about a measurement nothing
    # checks. The section sits near the top so it can be read at a glance and compared
    # across metrics, which is exactly why it must come from the generator rather than
    # from whoever last edited the card.
    pytest.param(build_prose(Performance="Excellent on smoothing, weak on displacement."),
                 "hand-written", id="hand-written-performance"),
    # One kind of test per subsection, so evidence sits beside the claim it supports.
    pytest.param(build_prose(Results="Everything went well across the whole ladder. " * 10),
                 "no '###' subsections", id="results-without-subsections"),
    # A result subsection without its generated numbers is an unsupported claim.
    pytest.param(build_prose(Results="### Smoothing\n\nMSE rose steeply with kernel width. " * 6),
                 "generated block", id="result-without-numbers"),
    # The number is the evidence; the prose reads it. Reversed, the prose leads.
    pytest.param(build_prose(Results=(
        "### Smoothing\n\nMSE rose steeply with kernel width, as the numbers below "
        "show and as anyone would say. \n\n<!-- GENERATED results_smoothing: written by "
        "`python -m fmeval.cards evidence example`, do not edit -->\n\nplaceholder\n\n"
        "<!-- END GENERATED results_smoothing -->\n")),
        "before its generated numbers", id="explanation-before-numbers"),
    # The run summary is stated once, before the first subsection; a second include there
    # is refused.
    pytest.param(build_prose(Results=(
        "<!-- GENERATED run: written by `python -m fmeval.cards evidence example`, do not "
        "edit -->\n\nplaceholder\n\n<!-- END GENERATED run -->\n\n"
        "<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence "
        "example`, do not edit -->\n\nplaceholder\n\n<!-- END GENERATED results_summary "
        "-->\n\n### Smoothing\n\n[gaussian_blur](../../degradations/gaussian_blur/card.md)"
        "\n\n<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence "
        "example`, do not edit -->\n\nplaceholder\n\n<!-- END GENERATED results_smoothing "
        "-->\n\n" + "What the smoothing axes found, at length. " * 5)),
        "before its first subsection", id="second-preamble-include"),
    # The card sends the reader out for what the test is, rather than restating it, so a
    # result subsection links to its degradations.
    pytest.param(build_prose(Results=(
        "### Smoothing\n\n<!-- GENERATED results_smoothing: written by `python -m "
        "fmeval.cards evidence example`, do not edit -->\n\nplaceholder\n\n<!-- END "
        "GENERATED results_smoothing -->\n\n" + "What the smoothing axes found, at length. " * 5)),
        "does not link to the degradations", id="no-degradation-link"),
    # The front matter must agree with the bundle name.
    pytest.param(build_prose(name="other"), "front matter", id="front-matter-name"),
])
def test_a_prose_fault_is_named(text, fragment):
    """Each prose rule, broken on an otherwise complete card, produces a problem naming it."""
    messages = [p.message for p in problems_for(text)]
    assert any(fragment in m for m in messages), messages


def test_an_unexplained_result_subsection_warns_but_does_not_fail():
    """A subsection whose evidence has not been generated has nothing to explain yet."""
    text = build_prose(
        Results=(
            "### Smoothing\n\n"
            "[gaussian_blur](../../degradations/gaussian_blur/card.md)\n\n"
            "<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence example`, do not edit -->\n\nplaceholder\n\n<!-- END GENERATED results_smoothing -->\n"
        )
    )
    problems = problems_for(text)
    unexplained = [p for p in problems if "nothing said about them" in p.message]
    assert unexplained and all(p.severity == "warning" for p in unexplained)


def test_the_contract_sets_no_word_counts():
    """Length is described in the templates and judged by a reader, never counted.

    A count measures length rather than clarity, and an author told to reach a number
    reaches that number -- so the check would manufacture the padding it was meant to
    prevent.
    """
    assert not hasattr(prose, "WORD_FLOORS")
    assert not hasattr(prose, "RESULT_PROSE_FLOOR")
    assert not hasattr(prose, "RESULT_PROSE_CEILING")
    long_enough = build_prose(Limitations="It saturates on shifted shocks.")
    assert not any(
        "words" in p.message and p.section == "Limitations" for p in problems_for(long_enough)
    )


@pytest.mark.parametrize("text,fragment", [
    # One include before the first subsection is the run summary, stated once: which
    # dataset, resolution and frames produced the numbers is the same for every subsection
    # of every card, so it is said there rather than thirty times.
    pytest.param(build_prose(Results=(
        "<!-- GENERATED run: written by `python -m fmeval.cards evidence example`, do not "
        "edit -->\n\nplaceholder\n\n<!-- END GENERATED run -->\n\n### Smoothing\n\n"
        "[gaussian_blur](../../degradations/gaussian_blur/card.md)\n\n"
        "<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence "
        "example`, do not edit -->\n\nplaceholder\n\n<!-- END GENERATED results_smoothing "
        "-->\n\n" + "What the smoothing axes found, at length. " * 5)),
        "before its first subsection", id="run-summary-first"),
    # A cross-cutting subsection, such as damage beside the other metrics, is about every
    # degradation at once and so has no single degradation to link to.
    pytest.param(build_prose(Results=(
        "### Damage beside the other metrics\n\n"
        "<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence "
        "example`, do not edit -->\n\nplaceholder\n\n<!-- END GENERATED "
        "results_damage_by_level -->\n\n"
        + "What the per-strength damage shows beside the other metrics. " * 4)),
        "link", id="cross-cutting-subsection"),
])
def test_an_accepted_form_raises_no_such_problem(text, fragment):
    """A form the rules allow produces no problem of the kind its look-alike fault does."""
    assert not [p for p in problems_for(text) if fragment in p.message]


@pytest.mark.parametrize("text", [
    # The portable subset: inline dollars, and a display block with a tag.
    pytest.param("Inline $f_{c,i}$ and a display equation:\n\n"
                 "$$\n\\mathrm{MSE} = \\frac{1}{N} \\sum_i d_i^2 \\tag{1}\n$$\n\n"
                 "as Equation (1) shows.\n", id="portable-subset"),
    # A card may legitimately show LaTeX source inside a code block, as an example of what
    # not to write.
    pytest.param("```\n\\begin{equation}\nx = 1\n\\end{equation}\n```\n",
                 id="code-block"),
])
def test_math_that_renders_everywhere_is_accepted(text):
    assert prose.check_math(text) == []


@pytest.mark.parametrize("text,fragment", [
    # One missing fence swallows the rest of the section into an equation.
    pytest.param("$$\nx = 1\n\n## Next section\n", "unterminated", id="display-block"),
    # An unpaired dollar turns the rest of the paragraph into maths.
    pytest.param("The value $x is large.\n", "odd number of `$`", id="inline"),
])
def test_an_unterminated_equation_is_caught(text, fragment):
    assert any(fragment in p.message for p in prose.check_math(text))


# --------------------------------------------------------------------------------------
# Review ledger
# --------------------------------------------------------------------------------------


def test_signing_is_insensitive_to_line_endings_and_trailing_space(tmp_path):
    """A colleague opening the file on another platform must not appear to have edited it."""
    bundle = loader.Bundle(name="example", kind="metric", path=tmp_path)
    (tmp_path / "card.md").write_text("## Intuition\n\nSomething.\n")
    first = review.prose_digest(bundle)
    (tmp_path / "card.md").write_text("## Intuition\r\n\r\nSomething.   \r\n")
    assert review.prose_digest(bundle) == first


def test_editing_prose_makes_a_signature_stale(tmp_path):
    bundle = loader.Bundle(name="example", kind="metric", path=tmp_path)
    (tmp_path / "card.md").write_text("## Intuition\n\nOriginal.\n")
    signature = review.sign(bundle, "khegazy")
    assert review.review_state(bundle, signature["prose_sha256"]) == "current"
    (tmp_path / "card.md").write_text("## Intuition\n\nRewritten by something.\n")
    assert review.review_state(bundle, signature["prose_sha256"]) == "stale"


def test_an_unsigned_card_reports_unsigned(tmp_path):
    bundle = loader.Bundle(name="example", kind="metric", path=tmp_path)
    (tmp_path / "card.md").write_text("## Intuition\n\nSomething.\n")
    assert review.review_state(bundle, None) == "unsigned"


# --------------------------------------------------------------------------------------
# Loader
# --------------------------------------------------------------------------------------


def test_a_card_whose_name_disagrees_with_its_directory_is_refused(tmp_path):
    """The name is the metric's identity; two answers to 'what is this called' is a bug."""
    (tmp_path / "card.yaml").write_text(yaml.safe_dump(card(name="something_else")))
    bundle = loader.Bundle(name="example", kind="metric", path=tmp_path)
    with pytest.raises(CardError, match="directory"):
        loader.load_card(bundle)


def test_a_missing_card_names_the_command_that_creates_one(tmp_path):
    bundle = loader.Bundle(name="example", kind="metric", path=tmp_path)
    with pytest.raises(CardError) as caught:
        loader.load_card(bundle)
    assert "python -m fmeval.cards new example" in str(caught.value)


def test_every_card_error_states_where_what_and_the_fix():
    """The error message is the product. An agent given a good one fixes the problem; an
    agent given `False is not True` guesses."""
    with pytest.raises(CardError) as caught:
        parse(card(status="excellent"))
    message = str(caught.value)
    assert "test card" in message and "status" in message and "Fix:" in message


# --------------------------------------------------------------------------------------
# Every bundle on disk
# --------------------------------------------------------------------------------------

BUNDLES = loader.iter_bundles()
IDS = [f"{b.kind}:{b.name}" for b in BUNDLES]


@pytest.mark.parametrize("bundle", BUNDLES, ids=IDS)
def test_bundle_has_every_required_file(bundle):
    missing = loader.check_bundle_files(bundle)
    assert missing == [], f"{bundle.name}: " + "; ".join(missing)


@pytest.mark.parametrize("bundle", BUNDLES, ids=IDS)
def test_bundle_card_is_valid(bundle):
    loader.load_card(bundle)


@pytest.mark.parametrize("bundle", BUNDLES, ids=IDS)
def test_bundle_prose_has_no_errors(bundle):
    """Warnings are allowed while a bundle is in progress; errors are not."""
    card_ = loader.load_card(bundle)
    problems = prose.check_prose(
        bundle.card_md.read_text(), kind=bundle.kind, name=bundle.name
    )
    blocking = [
        p for p in problems if p.severity == "error" or card_.status == "validated"
    ]
    assert not blocking, "\n".join(f"{p.section}: {p.message}" for p in blocking)


@pytest.mark.parametrize("bundle", BUNDLES, ids=IDS)
def test_every_equation_in_every_card_actually_typesets(bundle):
    """Run each card through the documentation site's markdown pipeline.

    The rules in ``check_math`` are a proxy: they ban the constructs known to fail. This
    test is the real thing -- it converts the card and asserts that every equation was
    recognised as math and that no LaTeX command survived into the output as literal
    text, which is exactly how an unrenderable equation presents itself to a reader.

    Skipped where the docs toolchain is not installed, so the fast suite stays
    dependency-free; it runs in the docs job, where the toolchain is present by
    definition.
    """
    markdown = pytest.importorskip(
        "markdown", reason="the docs toolchain is not installed in this environment"
    )
    pytest.importorskip("pymdownx", reason="the docs toolchain is not installed")

    text = bundle.card_md.read_text()
    body = text.split("---", 2)[2] if text.startswith("---") else text

    # The strict reader is GitHub, which recognises only dollar delimiters. Restricting
    # arithmatex to those models it: anything GitHub would print as raw source is left as
    # raw source here too. Running the site's own permissive configuration instead would
    # give false assurance, because it happily typesets \begin{equation}, which GitHub
    # does not -- that difference is the whole failure mode this test exists to catch.
    for label, config in (
        ("GitHub", {"generic": True, "block_syntax": ["dollar"],
                    "inline_syntax": ["dollar"]}),
        ("the documentation site", {"generic": True}),
    ):
        html = markdown.markdown(
            body,
            extensions=["pymdownx.arithmatex", "tables", "fenced_code"],
            extension_configs={"pymdownx.arithmatex": config},
        )
        untypeset = re.sub(
            r'<(div|span) class="arithmatex">.*?</\1>', "", html, flags=re.DOTALL
        )
        untypeset = re.sub(r"<code>.*?</code>", "", untypeset, flags=re.DOTALL)

        leaked = sorted(set(re.findall(r"\\(?:begin|end|label|eqref)\{[^}]*\}", untypeset)))
        assert not leaked, (
            f"{bundle.name}: on {label} these commands are not typeset and are shown to "
            f"the reader as raw source: {leaked}"
        )
        assert "$$" not in untypeset, (
            f"{bundle.name}: on {label} a `$$` survives as literal text, so a display "
            "equation was not recognised as math."
        )


@pytest.mark.parametrize("bundle", BUNDLES, ids=IDS)
def test_bundle_name_matches_the_registered_name(bundle):
    """The directory, the card and the decorator must agree on what this is called."""
    registry = metric_registry if bundle.kind == "metric" else deg_registry
    assert bundle.name in registry.available(), (
        f"{bundle.path} is a bundle, but nothing registers the name {bundle.name!r}. "
        f"Check the name= argument of its decorator."
    )


@pytest.mark.parametrize("kind", ["metric", "degradation"])
def test_template_is_valid_apart_from_its_sentinels(kind):
    """A template that has drifted out of validity is how systems like this die.

    Every bundle starts as a copy of the template, so if the template itself would fail a
    check, every new bundle inherits that failure and the author learns to ignore the
    checker. The template must therefore pass everything except the ``TODO`` markers,
    which are the one thing it is supposed to fail on.
    """
    template = loader.bundle_root(kind) / "_template"
    bundle = loader.Bundle(name=template.name, kind=kind, path=template)

    assert loader.check_bundle_files(bundle) == []

    text = bundle.card_md.read_text()
    placeholder = f"template_{'metric' if kind == 'metric' else 'degradation'}"
    problems = prose.check_prose(text, kind=kind, name=placeholder)
    unexpected = [
        p
        for p in problems
        if p.severity == "error" and not any(s in p.message for s in prose.SENTINELS)
    ]
    assert not unexpected, "\n".join(f"{p.section}: {p.message}" for p in unexpected)


def test_template_is_not_itself_a_bundle():
    """The underscore keeps it out of discovery, the catalog and the registry."""
    assert all(b.name != "_template" for b in loader.iter_bundles())


def test_bundle_ids_are_unique():
    assert len(IDS) == len(set(IDS))


# --------------------------------------------------------------------------------------
# Evidence: the measured half of a card
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("bundle", [b for b in BUNDLES if b.kind == "metric"],
                         ids=[b.name for b in BUNDLES if b.kind == "metric"])
def test_a_fingerprint_never_cites_the_dev_dataset(bundle):
    """The dev dataset is the first 100 solver steps, before the flow develops.

    Its numbers mean nothing physically, and once written into a card they would be
    indistinguishable from ones that do. The generator refuses such a run; this checks
    nothing already committed slipped through by another route.
    """
    fingerprint = bundle.path / "_generated" / "fingerprint.json"
    if not fingerprint.is_file():
        pytest.skip(f"{bundle.name} has no measurements yet")
    recorded = json.loads(fingerprint.read_text())["dataset"]
    assert not recorded.endswith("_dev"), (
        f"{bundle.name} cites {recorded}, which is a smoke-test dataset"
    )


@pytest.mark.parametrize("bundle", [b for b in BUNDLES if b.kind == "metric"],
                         ids=[b.name for b in BUNDLES if b.kind == "metric"])
def test_a_signed_card_has_measurements_behind_it(bundle):
    """A signature stands behind claims about how the metric behaved.

    Most of a card's claims are measured ones, so there is nothing for a signature to
    stand behind until a run exists. `fmeval.cards sign` refuses in that case; this is the
    check on what is committed.
    """
    card = yaml.safe_load(bundle.card_yaml.read_text())
    if not card.get("review"):
        return
    assert (bundle.path / "_generated" / "fingerprint.json").is_file(), (
        f"{bundle.name} is signed but has no fingerprint.json: the signature stands "
        "behind claims nothing measured"
    )


def _run_folder(path: pathlib.Path, df: pd.DataFrame, dataset: str = "kinet_re5e4"):
    """A results folder at ``path`` holding ``df``, stamped with ``dataset``.

    The default is the canonical dataset, so `load_run` accepts the folder as citable
    evidence.
    """
    (path / "data").mkdir(parents=True)
    df.assign(dataset=dataset).to_csv(path / "data" / "results.csv", index=False)
    return path


def test_evidence_refuses_a_run_on_a_dataset_cards_may_not_cite(tmp_path):
    folder = _run_folder(tmp_path / "comparison_1",
                         pd.DataFrame({"metric": ["mse"], "field": ["vorticity"], "value": [1.0]}),
                         dataset="kinet_re5e4_dev")
    with pytest.raises(ValueError, match="cards may not cite"):
        evidence.load_run(folder)


# --------------------------------------------------------------------------------------
# The catalog: the surface agents read instead of prose
# --------------------------------------------------------------------------------------


def test_the_catalog_covers_every_bundle():
    built = catalog.build()
    names = {e["name"] for e in built["entries"]}
    assert names == {b.name for b in BUNDLES}
    assert built["counts"]["metrics"] + built["counts"]["degradations"] == len(BUNDLES)


def test_the_catalog_reports_the_code_not_the_card():
    """Declared properties come from the registry, so a card cannot overstate them.

    A catalog entry is a contract an agent acts on. If it took `differentiable` from the
    prose half of a card, a metric could claim to be usable as a training loss because
    someone wrote that it was.
    """
    e = catalog.entry(loader.find_bundle("nrmse"))
    spec = metric_registry.get("nrmse")
    assert e["declared"]["symmetric"] is spec.symmetric is False
    assert e["declared"]["units"] == spec.units == "dimensionless"


def test_an_unmeasured_bundle_says_so_rather_than_omitting_the_key():
    """A consumer must tell "not measured" from "measured and unremarkable"."""
    e = catalog.entry(loader.find_bundle("gaussian_blur"))
    assert e["evidence"]["measured"] is False
    assert e["evidence"]["axes"] == []
    assert e["evidence"]["figures"] == [], "the shape is the same whether measured or not"


def test_the_catalog_supports_the_query_it_exists_for():
    """"Which metrics are differentiable, cheap, and measured?" without reading prose."""
    answer = [
        e["name"] for e in catalog.build()["entries"]
        if e["kind"] == "metric"
        and e["declared"]["differentiable"]
        and e["declared"]["cost"] == "cheap"
        and e["evidence"]["measured"]
    ]
    # crps and ensemble_mean_rmse qualify on the same terms as the pointwise family: both
    # are piecewise-differentiable and cheap, and both carry measurements. The two
    # calibration metrics are absent because they declare differentiable=False -- a rank
    # is integer-valued and a ratio of square roots is not a loss.
    assert set(answer) == {
        "mae", "mse", "rmse", "nrmse", "enstrophy", "kinetic_energy",
        "crps", "ensemble_mean_rmse",
        # h_minus_one is one FFT, increment_w1 one sort, increment_flatness one pass, and
        # all three are smooth enough in their inputs to serve as losses.
        "h_minus_one", "increment_flatness", "increment_w1",
        # h1_seminorm and palinstrophy are one spectral derivative per direction and
        # quadratic in the field; spectrum_l2 is one FFT and a bincount, smooth away from
        # identical spectra exactly as rmse is away from identical fields.
        "h1_seminorm", "palinstrophy", "spectrum_l2",
    }


# --------------------------------------------------------------------------------------
# The site
# --------------------------------------------------------------------------------------


def test_the_committed_catalog_matches_the_bundles():
    """`docs/catalog.json` is generated and committed, so it can go stale.

    CI rebuilds and diffs it; this fails locally first, which is where it is cheaper to
    notice.
    """
    committed = json.loads((REPO / "docs" / "catalog.json").read_text())
    assert committed == catalog.build(), (
        "docs/catalog.json is stale; run  python -m fmeval.cards catalog"
    )


@pytest.mark.slow
def test_the_site_builds_without_the_dataset(tmp_path):
    """The site must build on a machine with no CFS mount.

    Everything it needs -- cards, figures, fingerprints -- is committed, and the page
    generator reads those rather than running anything. If that stops being true the site
    becomes unbuildable by anyone without NERSC access, and CI is the first to find out.
    """
    pytest.importorskip("mkdocs", reason="the docs toolchain is not installed")
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(tmp_path)],
        cwd=REPO, capture_output=True, text=True,
        # Material's advisory about a future MkDocs 2 release is not about this site and
        # would otherwise fail --strict.
        env={**os.environ, "DISABLE_MKDOCS_2_WARNING": "true"},
    )
    assert result.returncode == 0, result.stderr[-3000:]
    assert (tmp_path / "catalog.json").is_file(), "the machine surface is missing"
    assert (tmp_path / "llms.txt").is_file()
    assert (tmp_path / "metrics" / "mse" / "index.html").is_file()
    assert (tmp_path / "degradations" / "gallery" / "index.html").is_file()
    assert (tmp_path / "ideas" / "index.html").is_file(), "the ideas overview is missing"


# --------------------------------------------------------------------------------------
# The generators, tested end to end on synthetic data
# --------------------------------------------------------------------------------------
#
# These functions rewrite committed files, and their failure modes -- unstable ordering
# between regenerations, a block swallowing its neighbour, regex escapes corrupting a body,
# silent key drift between writer and reader -- are all quiet: every one of them would put
# wrong content into a card that looks exactly like right content.


def _synthetic_run(tmp_path, with_mae: bool = True):
    """A results folder small enough to analyse in milliseconds, from the analysis fixture."""
    ladder = {
        "gaussian_blur": [1.0, 2.0, 3.0, 4.0],
        "translate_x": [0.5, 1.0, 2.0, 4.0],
        "translate_subpixel": [0.25, 1.0, 4.0],
        "uncorrelated": [10.0, 10.0, 10.0],
        "gaussian_impostor": [8.0],
    }
    frames = [make_frame(metric="mse", axes=ladder)]
    if with_mae:
        # The square root of mse everywhere, anchor included: the real pair's shape relation.
        frames.append(make_frame(metric="mae", axes={k: [float(np.sqrt(v)) for v in vals]
                                                     for k, vals in ladder.items()}))
    df = pd.concat(frames, ignore_index=True)
    df["energy_changed"] = np.where(df["level"] > 0, 0.01 * df["severity"] ** 2, 0.0)
    return _run_folder(tmp_path / "comparison_synthetic", df)


def test_load_run_goes_through_the_one_analysis_entry_point(tmp_path):
    """A card and a report computed from one run carry the same statistics."""
    run = evidence.load_run(_synthetic_run(tmp_path))
    assert set(analysis.RESPONSE_COLUMNS) <= set(run.axes.columns)
    assert "damage" in run.scored.columns
    assert "selectivity" in run.card.columns
    assert run.anchor_label == "uncorrelated"


def _bundle_copy(tmp_path, monkeypatch):
    """A throwaway copy of the mse bundle, so generators never touch tracked files."""
    dst = tmp_path / "mse"
    shutil.copytree(REPO / "metrics" / "mse", dst,
                    ignore=shutil.ignore_patterns("__pycache__"))
    bundle = loader.Bundle(name="mse", kind="metric", path=dst)
    monkeypatch.setattr(loader, "find_bundle", lambda *a, **k: bundle)
    return bundle


def test_evidence_generation_is_idempotent(tmp_path, monkeypatch):
    """Generating twice from the same run must change nothing the second time.

    The card and the fingerprint are committed, so any instability -- a dict whose
    ordering varies, a timestamp sneaking in, a DataFrame serialised in group order --
    shows up as a meaningless diff on every regeneration, and reviewers learn to ignore
    exactly the files where a real change matters most.
    """
    bundle = _bundle_copy(tmp_path, monkeypatch)
    run = evidence.load_run(_synthetic_run(tmp_path))

    def snapshot() -> dict[str, bytes]:
        files = {p.name: p.read_bytes() for p in (bundle.path / "_generated").iterdir()}
        files["card.md"] = bundle.card_md.read_bytes()
        return files

    evidence.generate("mse", run)
    first = snapshot()
    assert {"fingerprint.json", "response_curves.svg", "response_curves.json",
            "sensitivity_profile.svg", "sensitivity_profile.json"} <= set(first)

    evidence.generate("mse", run)
    second = snapshot()
    assert set(second) == set(first)
    changed = sorted(name for name in first if first[name] != second[name])
    assert not changed, f"regenerating from the same run rewrote {changed}"


def test_evidence_fills_every_block_the_card_carries(tmp_path, monkeypatch):
    """Every generated block in the card must be written, not silently skipped.

    The generator only writes blocks whose marker it finds, which is right for family
    blocks a card legitimately lacks -- but it means a typo in a marker name would leave
    that block permanently saying "not generated yet" with no error anywhere. This pins
    the count: after generating, no block in the mse card still carries the placeholder.
    """
    bundle = _bundle_copy(tmp_path, monkeypatch)
    run = evidence.load_run(_synthetic_run(tmp_path))
    evidence.generate("mse", run)

    text = bundle.card_md.read_text()
    assert "Not generated yet" not in text, (
        "a generated block kept its placeholder; its marker name and the generator's "
        "block name disagree"
    )
    # And the numbers written are the synthetic run's, not leftovers.
    assert "comparison_synthetic" in text


def test_the_catalog_reads_what_the_evidence_writes(tmp_path, monkeypatch):
    """The fingerprint's keys are a contract between two modules; pin it.

    `evidence.py` writes `rho`; `catalog.py` reads `row.get("rho")` and publishes it as
    `rank_correlation`. `.get` means a renamed key would not raise -- it would publish
    null for every metric and the catalog would look measured-but-empty, which is worse
    than an error.
    """
    bundle = _bundle_copy(tmp_path, monkeypatch)
    run = evidence.load_run(_synthetic_run(tmp_path))
    evidence.generate("mse", run)

    measured = catalog._measured(bundle)
    assert measured["measured"] is True
    ordinary = [a for a in measured["axes"] if not a["is_probe"]]
    assert ordinary, "no ordinary axes surfaced from the fingerprint"
    assert [f["name"] for f in measured["figures"]] == [
        "damage_beside_controls", "response_curves", "sensitivity_profile"]
    for figure in measured["figures"]:
        assert figure["file"].endswith(".svg") and figure["numbers"].endswith(".json")
    for axis in ordinary:
        assert axis["rank_correlation"] is not None, (
            f"{axis['axis']}: rank_correlation is null -- the key contract between "
            "evidence.py and catalog.py has drifted"
        )
        assert axis["levels"] is not None
    probes = measured["probes"]
    assert probes and probes[0]["unrelated_field_value"] is not None
    for axis in ordinary:
        assert axis["cliffs_delta"] is not None and axis["elasticity_x"], axis["axis"]
    assert measured["profile"] and measured["profile"][0]["selectivity"] is not None


def test_write_block_replaces_only_its_block(tmp_path):
    """One block's rewrite must not disturb its neighbours or mangle its body.

    The body goes through a regex substitution, where a bare `\\1` or `$` in the
    replacement is interpreted rather than written. Measured tables contain dollar signs
    and backslashes routinely, so corruption here would be routine too.
    """
    card = tmp_path / "card.md"
    card.write_text(
        "prose above\n\n"
        "<!-- GENERATED alpha: written by `cmd`, do not edit -->\n\nold alpha\n\n"
        "<!-- END GENERATED alpha -->\n\nprose between\n\n"
        "<!-- GENERATED beta: written by `cmd`, do not edit -->\n\nold beta\n\n"
        "<!-- END GENERATED beta -->\n\nprose below\n"
    )
    tricky = "a table with $ and \\1 and \\g<0> and $$maths$$"
    prose.write_block(card, "alpha", tricky, command="cmd")

    text = card.read_text()
    assert tricky in text, "regex escapes corrupted the body"
    assert "old beta" in text, "writing alpha disturbed beta"
    assert "old alpha" not in text
    assert text.startswith("prose above") and text.rstrip().endswith("prose below")


def test_write_block_refuses_a_missing_marker_and_leaves_the_file_alone(tmp_path):
    card = tmp_path / "card.md"
    original = "no markers here\n"
    card.write_text(original)
    with pytest.raises(KeyError, match="no 'alpha' generated block"):
        prose.write_block(card, "alpha", "body", command="cmd")
    assert card.read_text() == original


def test_a_marker_not_alone_on_its_line_is_refused_rather_than_skipped():
    """An indented marker would otherwise leave its block silently ungenerated."""
    assert not prose.has_block("no markers here\n", "alpha")
    with pytest.raises(ValueError, match="must start its own line"):
        prose.has_block("  <!-- GENERATED alpha: x -->\n<!-- END GENERATED alpha -->\n", "alpha")


def test_the_review_ledger_through_a_real_regeneration(tmp_path, monkeypatch):
    """The signature's whole point, exercised on files rather than strings.

    Regenerating evidence must not invalidate a human's signature -- they signed the
    prose, not the tables. Editing the prose must invalidate it. The tests above check
    both directions on strings; this drives them through sign, generate and review_state on
    a real bundle copy, which is the path production takes.
    """
    bundle = _bundle_copy(tmp_path, monkeypatch)
    run = evidence.load_run(_synthetic_run(tmp_path))
    evidence.generate("mse", run)                      # the gate: evidence before signing

    assert review.review_state(bundle, None) == "unsigned"
    signature = review.sign(bundle, "someone")["prose_sha256"]
    assert review.review_state(bundle, signature) == "current"

    evidence.generate("mse", run)                      # regeneration: signature survives
    assert review.review_state(bundle, signature) == "current"

    bundle.card_md.write_text(bundle.card_md.read_text() + "\nA new sentence of prose.\n")
    assert review.review_state(bundle, signature) == "stale"  # prose edit: signature dies


def test_evidence_survives_a_run_whose_ladder_skipped_a_probe(tmp_path, monkeypatch):
    """A ladder without the impostor is legitimate; the generator must not crash on it.

    `probe_summary` only emits columns for probes that ran, so a run produced with
    `degradation.skip=[gaussian_impostor]` has no impostor columns at all. Absent probes are
    "not measured", rendered as an em dash, never an error.
    """
    folder = _run_folder(tmp_path / "comparison_noimpostor", make_frame(
        metric="mse", axes={"gaussian_blur": [1.0, 2.0], "uncorrelated": [10.0, 10.0]}))

    bundle = _bundle_copy(tmp_path, monkeypatch)
    evidence.generate("mse", evidence.load_run(folder))

    text = bundle.card_md.read_text()
    assert "comparison_noimpostor" in text
    assert "gaussian_blur" in text


def test_the_cards_cli_takes_all_as_a_flag():
    """`evidence --all` and `exemplars --all` must parse.

    They are the regeneration commands written in `docs/recipes/refresh-the-evidence.md`.
    Recognising `--all` by comparing the positional `name` with the literal string cannot
    work: argparse rejects the option as unknown first, and the command exits with "the
    following arguments are required: name".
    """
    parser = cli.build_parser()
    args = parser.parse_args(["evidence", "--all", "--results", "results/x"])
    assert args.all is True and args.name is None
    args = parser.parse_args(["evidence", "mse", "--results", "results/x"])
    assert args.all is False and args.name == "mse"
    assert parser.parse_args(["exemplars", "--all"]).all is True
    assert parser.parse_args(["overview", "--results", "results/x"]).out is None
    # Neither a name nor --all is a usage error, not a crash.
    assert cli.main(["evidence", "--results", "results/x"]) == 1
    assert cli.main(["exemplars"]) == 1


def test_check_strict_counts_warnings_as_errors(capsys):
    """`check --strict` must fail on what plain `check` only warns about.

    Every bundle is unsigned until a person signs it, so each one carries at least the
    review warning, which is what this test relies on.
    """
    assert cli.main(["check", "mse"]) == 0
    capsys.readouterr()
    assert cli.main(["check", "mse", "--strict"]) == 1
    assert "[error] card.yaml  review" in capsys.readouterr().out


@pytest.mark.parametrize("kind", ["metric", "degradation"])
def test_a_scaffolded_bundle_does_not_call_itself_a_template(kind, tmp_path, monkeypatch, capsys):
    """`cards new` must not copy the template's "not a metric itself" docstring.

    The scaffolder substitutes the placeholder name, replaces the template's own description,
    and names the test file of the bundle's kind in its step list. Runs against a temporary
    bundle root so nothing is written into the repo.
    """
    root = tmp_path / kind
    shutil.copytree(loader.bundle_root(kind) / cli.TEMPLATE_DIR, root / cli.TEMPLATE_DIR)
    monkeypatch.setattr(cli, "bundle_root", lambda _kind: root)
    assert cli.main(["new", "probe_bundle", "--kind", kind]) == 0
    docstring = (root / "probe_bundle" / "__init__.py").read_text()
    assert "Template bundle" not in docstring and f"The `probe_bundle` {kind}." in docstring
    assert f"test_{kind}.py" in capsys.readouterr().out


def test_a_degradation_results_fix_names_the_exemplars_command():
    """A structural fault in a degradation's results section must say `cards exemplars`.

    `cards evidence` refuses degradations, so a fix naming it would send the author to a
    command that cannot help.
    """
    body = ("<!-- GENERATED a: x -->\n<!-- END GENERATED a -->\n"
            "<!-- GENERATED b: y -->\n<!-- END GENERATED b -->\n")
    degradation = prose._check_result_section(prose.DEGRADATION_RESULTS, body, "gain")
    metric = prose._check_result_section("Results", body, "mse")
    assert any("python -m fmeval.cards exemplars gain" in p.fix for p in degradation)
    assert any("python -m fmeval.cards evidence mse" in p.fix for p in metric)


def test_evidence_all_skips_a_metric_the_run_does_not_contain(tmp_path, monkeypatch, capsys):
    """`--all` must leave alone every card whose metric the run never evaluated.

    Twelve cards cite the kinet comparison run and four ensemble cards cite their own
    single-metric runs. Regenerating a card from a run that lacks its metric would write
    "No measurements" into every block and an empty fingerprint -- erasing the evidence
    from the run the card actually cites, with nothing to say that happened.
    """
    folder = _synthetic_run(tmp_path)            # holds mse and mae only
    bundles = [loader.Bundle(name=n, kind="metric", path=tmp_path / n)
               for n in ("enstrophy", "mse")]
    monkeypatch.setattr(cli, "iter_bundles", lambda kind=None: bundles)
    generated: list[str] = []
    monkeypatch.setattr(evidence, "generate", lambda name, run: generated.append(name))

    assert cli.cmd_evidence(Namespace(name=None, all=True, results=str(folder))) == 0
    assert generated == ["mse"]
    out = capsys.readouterr().out
    assert "skipped enstrophy" in out and "its own run" in out


@pytest.mark.parametrize("argv, message", [
    # A results folder holding no results: `evidence` reads the run before anything else,
    # and the reader's fix is to name the right folder.
    pytest.param(["evidence", "mse", "--results", "{missing}"], "no results.csv",
                 id="evidence-no-results"),
    # A run on the dev dataset, which cards may not cite. This message is two lines by
    # design: the refusal, then what evidence must come from.
    pytest.param(["evidence", "mse", "--results", "{dev}"], "cards may not cite",
                 id="evidence-uncitable-run"),
    # A readable run and a metric name with no bundle: the generator, not the loader,
    # refuses it.
    pytest.param(["evidence", "no_such_metric", "--results", "{run}"],
                 "no metric bundle named", id="evidence-unknown-metric"),
    # A degradation name with no bundle, refused before any data is read.
    pytest.param(["exemplars", "no_such_degradation"], "no degradation bundle named",
                 id="exemplars-unknown"),
    # `overview` reads the run the same way `evidence` does.
    pytest.param(["overview", "--results", "{missing}"], "no results.csv",
                 id="overview-no-results"),
])
def test_a_cli_error_the_reader_can_fix_exits_1_with_its_message(argv, message, tmp_path,
                                                                  capsys):
    """`main` turns FileNotFoundError, ValueError and KeyError from any subcommand into exit
    code 1 and the exception's message on stderr, with no traceback."""
    dev = tmp_path / "comparison_dev"
    (dev / "data").mkdir(parents=True)
    (dev / "data" / "results.csv").write_text(
        "dataset,metric,field,value\nkinet_re5e4_dev,mse,vorticity,1.0\n")
    paths = {"missing": tmp_path / "missing", "dev": dev, "run": _synthetic_run(tmp_path)}

    assert cli.main([a.format(**paths) for a in argv]) == 1
    err = capsys.readouterr().err
    assert message in err and "Traceback" not in err
    assert len(err.splitlines()) <= 2, err


def test_a_cli_error_in_a_subcommand_without_its_own_handler_exits_1(tmp_path, monkeypatch,
                                                                     capsys):
    """`sign` has no handler of its own: a bundle with measurements but no card.yaml reaches
    the one in `main`, which prints the one-line message and exits 1."""
    bundle = loader.Bundle(name="probe", kind="metric", path=tmp_path / "probe")
    bundle.fingerprint.parent.mkdir(parents=True)
    bundle.fingerprint.write_text("{}")
    monkeypatch.setattr(cli, "find_bundle", lambda name: bundle)

    assert cli.main(["sign", "probe", "--by", "someone"]) == 1
    err = capsys.readouterr().err
    assert "card.yaml" in err and len(err.splitlines()) == 1, err


# --- the figures on a metric card ---------------------------------------------------------------


def _figure_run(tmp_path, metrics=("mse", "mae", "flat"), *, impostor: bool = True):
    """A results folder from the report suite's rows, stamped citable: three fields, a metric
    with no damage scale, and optionally no impostor."""
    df = synthetic_rows(metrics=metrics)
    if not impostor:
        df = df[df["degradation"] != "gaussian_impostor"]
    return _run_folder(tmp_path / "comparison_figures", df)


def test_metric_figures_are_byte_identical_within_one_environment(tmp_path):
    """Two renders of the same figure must be the same bytes, SVG included.

    SVG needs a fixed `svg.hashsalt` -- without it matplotlib salts element ids with a fresh
    uuid, and two renders differ (measured) -- and no creation date in the metadata. Byte
    identity is promised within one matplotlib version only, which is what one test run is.
    """
    run = evidence.load_run(_figure_run(tmp_path))
    first, _ = metric_figures(run, "mse", tmp_path / "a")
    second, _ = metric_figures(run, "mse", tmp_path / "b")
    assert [f.name for f in first] == list(METRIC_FIGURES)
    for one, two in zip(first, second, strict=True):
        assert one.path.read_bytes() == two.path.read_bytes(), f"{one.name} is not stable"
        assert one.numbers.read_bytes() == two.numbers.read_bytes()
        text = one.path.read_text()
        assert "dc:date" not in text and "<dc:creator>" not in text


def test_the_performance_block_opens_with_the_figures(tmp_path, monkeypatch):
    """Picture first, table second; and every figure beside the card is one the card shows."""
    bundle = _bundle_copy(tmp_path, monkeypatch)
    evidence.generate("mse", evidence.load_run(_synthetic_run(tmp_path)))

    block = prose.generated_blocks(bundle.card_md.read_text())["performance"]
    body = [line for line in block.splitlines()[1:] if line.strip()]
    assert body[0] == f"![{ALT_TEXT['sensitivity_profile']}](_generated/sensitivity_profile.svg)"
    assert body[2] == f"![{ALT_TEXT['response_curves']}](_generated/response_curves.svg)"
    assert body[4].startswith("| test family |"), "the table follows the figures"
    for alt in ALT_TEXT.values():
        assert "]" not in alt and ")" not in alt, "alt text would truncate the link pattern"
    referenced = set(re.findall(r"\]\(_generated/([^)]+\.svg)\)", block))
    assert referenced == {"response_curves.svg", "sensitivity_profile.svg"}
    damage = prose.generated_blocks(bundle.card_md.read_text())["results_damage_by_level"]
    first = next(line for line in damage.splitlines()[1:] if line.strip())
    assert first == (f"![{ALT_TEXT['damage_beside_controls']}]"
                     "(_generated/damage_beside_controls.svg)"), "the figure heads its table"
    shown = set(re.findall(r"\]\(_generated/([^)]+\.svg)\)", bundle.card_md.read_text()))
    present = {p.name for p in (bundle.path / "_generated").glob("*.svg")}
    assert shown == present == {"response_curves.svg", "sensitivity_profile.svg",
                                "damage_beside_controls.svg"}


def test_a_single_metric_run_gets_no_damage_figure_and_the_block_says_only_that(tmp_path):
    """The ensemble cards are pinned to single-metric runs: no controls, so no figure and no
    extra sentence -- the block's existing one already says there is nothing to place beside."""
    run = evidence.load_run(_synthetic_run(tmp_path, with_mae=False))
    figures, reasons = metric_figures(run, "mse", tmp_path / "one")
    assert [f.name for f in figures] == ["sensitivity_profile", "response_curves"]
    assert "2 metrics" in reasons["damage_beside_controls"]
    block = evidence.damage_by_level_block(run, "mse", figures, reasons)
    assert block.startswith("Only one metric in the recorded run")
    assert "figure" not in block


def test_a_metric_without_a_damage_scale_still_gets_its_figures(tmp_path):
    run = evidence.load_run(_figure_run(tmp_path))
    _figures, reasons = metric_figures(run, "flat", tmp_path / "flat")
    assert set(reasons) == {"damage_beside_controls"}, reasons
    assert "no damage scale" in reasons["damage_beside_controls"]
    curves = json.loads((tmp_path / "flat" / "response_curves.json").read_text())
    assert set(curves["panels"]) == {"density", "velocity", "vorticity"}
    rows = [r for rows in curves["panels"].values() for r in rows]
    assert not any(r["has_scale"] for r in rows)
    assert all(r["damage_median"] is None and r["value_median"] is not None for r in rows)
    assert curves["metric"] == "flat" and curves["run"] == "comparison_figures"


def test_card_figures_survive_a_run_without_the_impostor(tmp_path):
    run = evidence.load_run(_figure_run(tmp_path, impostor=False))
    _figures, reasons = metric_figures(run, "mse", tmp_path / "noimp")
    assert not reasons, reasons
    curves = json.loads((tmp_path / "noimp" / "response_curves.json").read_text())
    assert all(r["impostor_damage"] is None
               for rows in curves["panels"].values() for r in rows)


def test_a_figure_this_generation_did_not_write_is_removed(tmp_path):
    """A renamed or dropped figure must not linger beside a card that no longer shows it."""
    out = tmp_path / "gen"
    out.mkdir()
    (out / "old_view.svg").write_text("<svg/>")
    (out / "old_view.json").write_text("{}")
    (out / "exemplars.png").write_bytes(b"png")      # not a card figure; left alone
    metric_figures(evidence.load_run(_figure_run(tmp_path)), "mse", out)
    assert not (out / "old_view.svg").exists() and not (out / "old_view.json").exists()
    assert (out / "exemplars.png").exists()


def test_an_unavailable_figure_is_said_in_the_block_not_dropped_silently(tmp_path):
    run = evidence.load_run(_synthetic_run(tmp_path))
    block = evidence.performance_block(run, "mse", [], {"response_curves": "no ordinal axes",
                                                        "sensitivity_profile": "no axes"})
    assert "No response to each family of degradation figure: no ordinal axes." in block
    assert "No sensitivity profile figure: no axes." in block


def test_the_figure_vocabulary_covers_what_the_figures_draw_and_grades_nothing():
    """Every statistic a card figure labels has plain words, and none of the words is a verdict."""
    drawn = {"rho", "rho_ci_lo", "rho_ci_hi", "cliffs_delta_min", "damage_per_change",
             "damage_max_ucb", "blind_axes", "sensitivity_level", "damage", "value", "level",
             "gaussian_impostor_damage", "severity_degenerate"}
    missing = sorted(drawn - set(vocabulary.LABELS))
    assert not missing, f"statistics a figure draws with no plain label: {missing}"
    graded = re.compile(r"\b(" + "|".join(vocabulary.GRADING_WORDS) + r")\b", re.IGNORECASE)
    for text in [*vocabulary.LABELS.values(),
                 *(f.label for f in vocabulary.FAMILY_INFO.values()),
                 *(f.description for f in vocabulary.FAMILY_INFO.values()),
                 *ALT_TEXT.values()]:
        assert not graded.search(text), f"a label grades a measurement: {text!r}"


def test_committed_figures_fit_the_size_budget():
    """A ceiling with headroom, not a target: docs/decisions.md names 50 MB as the line past
    which Git LFS is the answer. Fails naming the three largest files."""
    files = [p for b in BUNDLES for p in (b.path / "_generated").iterdir()
             if p.is_file() and p.name != ".gitkeep"]
    files += [p for p in (REPO / "docs" / "figures").rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    largest = sorted(files, key=lambda p: p.stat().st_size, reverse=True)[:3]
    assert total < 25_000_000, (
        f"committed generated files total {total / 1e6:.1f} MB; largest: "
        + ", ".join(f"{p.parent.parent.name}/{p.name} {p.stat().st_size // 1024} KB"
                    for p in largest)
    )


# --- the cross-metric overview --------------------------------------------------------------


def test_overview_figures_are_byte_identical_and_cover_every_field(tmp_path):
    run = evidence.load_run(_figure_run(tmp_path))
    first, reasons = overview_figures(run, tmp_path / "a")
    second, _ = overview_figures(run, tmp_path / "b")
    assert not reasons, reasons
    assert [f.name for f in first] == ["response_sparklines__field-density",
                                       "response_sparklines__field-velocity",
                                       "response_sparklines__field-vorticity",
                                       "response_portrait"]
    for one, two in zip(first, second, strict=True):
        assert one.path.read_bytes() == two.path.read_bytes(), f"{one.name} is not stable"
        assert one.numbers.read_bytes() == two.numbers.read_bytes()
    record = json.loads(first[0].numbers.read_text())
    assert record["metrics"] == ["flat", "mae", "mse"] and record["keys"] == {"field": "density"}
    assert set(record["panels"]) == {"flat", "mae", "mse"}, "numbers are keyed by metric"


def test_the_sensitivity_page_shows_every_figure_and_names_what_is_not_on_it(tmp_path):
    root = tmp_path / "figures"
    run = evidence.load_run(_figure_run(tmp_path))
    figures, _ = overview_figures(run, root / "comparison_figures")
    catalog_json = {"entries": [
        {"name": "mse", "kind": "metric",
         "evidence": {"measured": True, "run": "comparison_figures", "dataset": "kinet_re5e4"}},
        {"name": "crps", "kind": "metric",
         "evidence": {"measured": True, "run": "crps_1", "dataset": "synthetic_ensemble"}},
        {"name": "gaussian_blur", "kind": "degradation", "evidence": {"measured": False}},
    ]}
    page = page_markdown(root, catalog_json)
    for figure in figures:
        assert f"](figures/comparison_figures/{figure.name}.svg)" in page
        assert f"[{figure.name}.json](figures/comparison_figures/{figure.name}.json)" in page
        assert figure.caption in page
    assert "## Run `comparison_figures`" in page
    assert "[crps](metrics/crps.md) (run `crps_1` on `synthetic_ensemble`)" in page
    assert "[mse](metrics/mse.md) (run" not in page, "mse is on the grid"
    assert "ranking" in page and "No overview figures" not in page
    assert "No overview figures have been generated yet" in page_markdown(tmp_path / "none")


def test_every_committed_overview_figure_has_its_numbers_beside_it():
    root = REPO / "docs" / "figures"
    svgs = sorted(root.rglob("*.svg")) if root.is_dir() else []
    def refuse(token):
        raise AssertionError(f"non-standard JSON token {token!r} in an overview figure's numbers")

    for svg in svgs:
        numbers = svg.with_suffix(".json")
        assert numbers.is_file(), f"{svg.relative_to(REPO)} has no {numbers.name} beside it"
        record = json.loads(numbers.read_text(), parse_constant=refuse)
        assert record.get("panels"), f"{numbers.relative_to(REPO)} records no panels"
        assert record["run"] == svg.parent.name, "a figure sits in the directory of its run"


def test_the_exemplar_loader_accepts_any_checkout_path(tmp_path, monkeypatch):
    """A checkout under `fluid_metrics (copy)` must reach the data check, not a parse error."""
    monkeypatch.setattr(fmeval_config, "REPO", tmp_path / "fluid_metrics (copy), v=2")
    with pytest.raises(FileNotFoundError, match="not readable here"):
        exemplars.load_canonical_frame()


def test_exemplar_panels_are_byte_identical_within_one_environment(tmp_path):
    """Rendering the same panel twice must produce the same bytes.

    The panels are committed, so nondeterminism here -- a timestamp in the PNG metadata,
    an unseeded jitter, an unordered iteration -- turns every regeneration into a diff on
    unchanged figures, and reviewers learn to skim exactly the files where a real change
    matters. Byte identity is only promised within one matplotlib version, which is what
    a single test run is.
    """
    base = np.random.default_rng(0).normal(size=(48, 48))
    columns = [Column("original", base)] + [
        Column(f"sigma = {s} cells", gaussian_filter(base, s, mode="wrap"))
        for s in (1.0, 2.0, 4.0)
    ]
    rows = ["difference", "radial_spectrum", "pdf"]

    dpi = fmeval_config.load_cards_config().figures.dpi
    first = exemplar_panel(columns, rows, path=tmp_path / "a.png", title="determinism", dpi=dpi)
    second = exemplar_panel(columns, rows, path=tmp_path / "b.png", title="determinism", dpi=dpi)

    assert (tmp_path / "a.png").read_bytes() == (tmp_path / "b.png").read_bytes()
    # Compared through the sanitiser, because a NaN statistic -- "not measured" -- is
    # never equal to itself, and comparing raw dicts would fail on unchanged output.
    assert loader.sanitize_json(first.statistics) == loader.sanitize_json(second.statistics)


def test_every_panel_row_shares_one_set_of_limits(tmp_path):
    """The rule that keeps a strong degradation from looking like the original.

    Per-panel autoscaling is the single most effective way to make a severe degradation
    invisible, and it fails silently -- the figure looks fine. The difference row's limits
    must come from the strongest column, so the weak column reads as faint; a weak
    difference drawn on its own scale would look as severe as the strong one.
    """
    base = np.zeros((16, 16))
    weak, strong = base.copy(), base.copy()
    weak[8, 8] = 0.1
    strong[8, 8] = 10.0
    columns = [Column("original", base), Column("weak", weak), Column("strong", strong)]

    low, high = _row_limits("difference", columns, base)
    assert high == 10.0 and low == -10.0, (
        "difference limits must span the strongest severity, not each panel's own range"
    )


@pytest.mark.parametrize("bundle", BUNDLES, ids=IDS)
def test_every_generated_json_is_strict_json(bundle):
    """A committed fingerprint must be readable by an ordinary JSON parser.

    These files exist for machine readers. `json.dumps` writes float('nan') as a bare
    `NaN` token, which is not JSON and which a strict parser refuses -- so a single
    unmeasured statistic would make a whole fingerprint unreadable. "Not a number" means
    "not measured", and null is how JSON says that.
    """
    def refuse(token):
        raise AssertionError(
            f"{bundle.name}: non-standard JSON token {token!r}. Regenerate it: the writers "
            "sanitise NaN to null."
        )

    for path in sorted((bundle.path / "_generated").glob("*.json")):
        json.loads(path.read_text(), parse_constant=refuse)


@pytest.mark.parametrize("bundle", BUNDLES, ids=IDS)
def test_a_committed_figure_has_its_numbers_beside_it(bundle):
    """Every panel must ship the statistics behind it.

    An agent reading the site cannot open a PNG. A figure with no numeric counterpart is
    unreadable to half this repository's intended audience, and the rule is easy to break
    by adding a figure without extending the generator that records its numbers.
    """
    figures = [*(bundle.path / "_generated").glob("*.png"),
               *(bundle.path / "_generated").glob("*.svg")]
    for panel in sorted(figures):
        numbers = panel.with_suffix(".json")
        assert numbers.is_file(), (
            f"{bundle.name}: {panel.name} has no {numbers.name} beside it"
        )
        recorded = json.loads(numbers.read_text())
        assert recorded.get("panels"), f"{bundle.name}: {numbers.name} records no panels"


# --- the response blocks -----------------------------------------------------------------------


def test_damage_by_level_block_puts_this_metric_first_beside_the_controls(tmp_path):
    run = evidence.load_run(_synthetic_run(tmp_path))
    block = evidence.damage_by_level_block(run, "mae")
    assert "`translate_x`" in block
    rows = [line for line in block.splitlines() if line.startswith("| `")]
    assert rows[0].startswith("| `mae`") and rows[1].startswith("| `mse`"), (
        "one row per metric, this metric first, then the pointwise controls")
    alone = evidence.load_run(_synthetic_run(tmp_path / "alone", with_mae=False))
    assert "Only one metric" in evidence.damage_by_level_block(alone, "mse")


def test_performance_block_carries_the_measured_profile(tmp_path):
    block = evidence.performance_block(evidence.load_run(_synthetic_run(tmp_path)), "mse")
    assert "**Profile.**" in block and "selectivity" in block.lower()
    assert f"{analysis.BLINDNESS_MARGIN:g}" in block, "the margin is read from the analysis"


def test_profile_header_nests_no_parentheses(tmp_path):
    """The strength an elasticity is taken against already carries its name in parentheses."""
    block = evidence.performance_block(evidence.load_run(_synthetic_run(tmp_path)), "mse")
    header = next(line for line in block.splitlines() if line.startswith("| field | selectivity"))
    depth = deepest = 0
    for character in header:
        depth += {"(": 1, ")": -1}.get(character, 0)
        deepest = max(deepest, depth)
    assert "against" in header and deepest <= 1, header
