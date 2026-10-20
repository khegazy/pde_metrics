"""The machine surface: every bundle's typed facts in one file.

`docs/catalog.json` is what an agent reads to answer a structural question -- what metrics
exist, what they return, what properties they have, how they behaved -- without parsing
prose. Prose is written for people and changes wording freely; a catalog entry is a
contract.

Nothing here is a new source of truth. Each entry merges three that already exist: the
registry spec, which the code declares; the card, which the author writes; and the
fingerprint, which the evidence generator measures. Where they disagree the merge does not
pick a winner -- disagreement means something is wrong and the card checks catch it.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from fmeval import analysis as an

from .loader import GENERATED_DIR, Bundle, iter_bundles, load_card, write_strict_json

CATALOG_SCHEMA_VERSION = 2
"""Bump when an entry's shape changes in a way a consumer could not ignore. Not the card
schema's version (:data:`fmeval.cards.schema.SCHEMA_VERSION`), which versions ``card.yaml``."""


def _spec_fields(bundle: Bundle) -> dict[str, Any]:
    """What the code declares about this metric or degradation.

    Read from the registry rather than the card, so a catalog entry cannot claim a metric
    is differentiable when its decorator says otherwise.
    """
    if bundle.kind == "metric":
        from metrics import registry
    else:
        from degradations import registry
    return registry.get(bundle.name).describe()


def _measured(bundle: Bundle) -> dict[str, Any]:
    """What the recorded run measured, or an explicit statement that nothing has.

    A consumer must be able to tell "no measurements yet" from "measured and unremarkable"
    without inferring it from a missing key, so the shape is the same either way.
    """
    fingerprint = bundle.fingerprint
    if not fingerprint.is_file():
        return {"measured": False, "run": None, "dataset": None, "axes": [], "probes": [],
                "profile": [], "figures": []}

    data = json.loads(fingerprint.read_text())
    axes = [
        {
            "axis": row["degradation"],
            "field": row["field"],
            "family": row.get("degradation_family"),
            "is_probe": bool(row.get("is_probe")),
            "levels": row.get("n_levels"),
            "rank_correlation": row.get("rho"),
            "monotone_fraction": row.get("monotone_fraction"),
            "weakest_separation": row.get("separability_auc_min"),
            "first_detected_level": row.get("sensitivity_level"),
            "cliffs_delta": row.get("cliffs_delta_min"),
            "elasticity": row.get("elasticity"),
            "elasticity_x": row.get("elasticity_x"),
            "response_shape": row.get("response_shape"),
            "detection_onset_severity": row.get("severity_10"),
            "half_damage_severity": row.get("severity_50"),
            "severity_resolution": row.get("severity_resolution"),
            "largest_response_upper_bound": row.get("damage_max_ucb"),
            "blindness_q": row.get("blindness_q"),
        }
        for row in data.get("axes", [])
    ]
    profile = [
        {
            "field": row["field"],
            "selectivity": row.get("selectivity"),
            "most_sensitive_axis": row.get("most_sensitive_axis"),
            "least_sensitive_axis": row.get("least_sensitive_axis"),
            "blind_axes": an.split_blind(row.get("blind_axes")),
            "elasticity_displacement": row.get("elasticity_displacement"),
        }
        for row in data.get("profile", [])
    ]
    probes = [
        {
            "field": row["field"],
            "impostor_damage": row.get("gaussian_impostor_damage"),
            "impostor_nearest_level": row.get("gaussian_impostor_nearest_level"),
            "unrelated_field_value": row.get("uncorrelated_value"),
        }
        for row in data.get("probes", [])
    ]
    # The figures beside the card, each with the JSON of the numbers it draws. Listed from
    # the files rather than from the fingerprint so the catalog cannot name a figure that is
    # not there. Additive, so CATALOG_SCHEMA_VERSION is unchanged: a consumer that ignores the key
    # reads the entry exactly as before.
    relative = bundle.path.relative_to(bundle.path.parent.parent)
    figures = [
        {"name": svg.stem, "file": str(relative / GENERATED_DIR / svg.name),
         "numbers": str(relative / GENERATED_DIR / svg.with_suffix(".json").name)}
        for svg in sorted(bundle.generated.glob("*.svg"))
    ]
    return {
        "measured": True,
        "run": data.get("run"),
        "dataset": data.get("dataset"),
        "frames": len(data.get("frames", [])),
        "axes": axes,
        "probes": probes,
        "profile": profile,
        "figures": figures,
    }


def entry(bundle: Bundle) -> dict[str, Any]:
    """One catalog entry: the code's declaration, the card, and the measurements."""
    card = load_card(bundle)
    review = card.review
    return {
        "name": card.name,
        "kind": card.kind,
        "category": card.category,
        "summary": card.summary,
        "status": card.status,
        "owners": list(card.owners),
        "path": f"{bundle.path.parent.name}/{bundle.path.name}",
        "card": f"{bundle.path.parent.name}/{bundle.path.name}/card.md",
        "declared": _spec_fields(bundle),
        "math": dataclasses.asdict(card.math) if card.math is not None else None,
        "output": {"description": card.output.description,
                   "lower_bound": card.output.lower,
                   "upper_bound": card.output.upper},
        "evidence": _measured(bundle),
        "reviewed": review is not None,
        "reviewed_by": review.reviewer if review else None,
        "reviewed_at": review.date.isoformat() if review else None,
    }


def build() -> dict[str, Any]:
    """The whole catalog, metrics and degradations together, sorted by name."""
    entries = sorted((entry(b) for b in iter_bundles()), key=lambda e: (e["kind"], e["name"]))
    return {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "counts": {
            "metrics": sum(1 for e in entries if e["kind"] == "metric"),
            "degradations": sum(1 for e in entries if e["kind"] == "degradation"),
            "with_measurements": sum(1 for e in entries if e["evidence"]["measured"]),
            "reviewed": sum(1 for e in entries if e["reviewed"]),
        },
        "entries": entries,
    }


def write(path: Path) -> Path:
    """Write the catalog as strict, sorted JSON with a trailing newline, so diffs stay readable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    write_strict_json(path, build())
    return path
