"""The machine surface: every bundle's typed facts in one file.

`docs/catalog.json` is what an agent reads to answer a structural question -- what metrics
exist, what they return, what properties they have, how they behaved -- without parsing
prose. Prose is written for people and changes wording freely; a catalog entry is a
contract.

Nothing here is a new source of truth. Each entry merges three that already exist: the
registry spec, which the code declares; the card, which the author writes; and the
fingerprint, which the evidence generator measures. Where they disagree the merge does not
pick a winner -- disagreement means something is wrong and the card checks catch it. Which
experiments a metric is not run on, and why, is derived from the same three plus what each
evidence dataset offers (``configs/cards/default.yaml``, ``configs/dataset/``).
"""

from __future__ import annotations

import dataclasses
import functools
import json
from pathlib import Path
from typing import Any

from fmeval import analysis as an
from fmeval.config import compose_config, load_cards_config

from .loader import GENERATED_DIR, Bundle, iter_bundles, load_card, write_strict_json

CATALOG_SCHEMA_VERSION = 6
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


def recorded_runs(bundle: Bundle) -> list[dict[str, Any]]:
    """The fingerprint record of every run the card cites, its primary run first; empty if none.

    The primary run's record is the fingerprint's top level and each further run's is an entry
    of its ``other_runs`` (:func:`fmeval.cards.evidence.generate`). This is the one record of
    which runs a card cites: ``cards evidence --all`` regenerates each card from it.
    """
    if not bundle.fingerprint.is_file():
        return []
    data = json.loads(bundle.fingerprint.read_text())
    return [data, *data.get("other_runs", [])]


def _summary(data: dict[str, Any]) -> dict[str, Any]:
    """One run's measurements as the catalog publishes them, from its fingerprint record."""
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
            "translation_probe_value": row.get("uncorrelated_value"),
        }
        for row in data.get("probes", [])
    ]
    return {
        "measured": True,
        "run": data.get("run"),
        "dataset": data.get("dataset"),
        "frames": len(data.get("frames", [])),
        "axes": axes,
        "probes": probes,
        "profile": profile,
    }


def _measured(bundle: Bundle) -> dict[str, Any]:
    """What the card's primary run measured, or an explicit statement that nothing has.

    A consumer must be able to tell "no measurements yet" from "measured and unremarkable"
    without inferring it from a missing key, so the shape is the same either way.
    """
    runs = recorded_runs(bundle)
    if not runs:
        return {"measured": False, "run": None, "dataset": None, "axes": [], "probes": [],
                "profile": [], "figures": []}
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
    return {**_summary(runs[0]), "figures": figures}


@functools.cache
def _dataset_fields(dataset: str) -> tuple[str, ...]:
    """The fields a dataset provides, read from its own config, ``configs/dataset/<name>.yaml``."""
    return tuple(compose_config(f"dataset={dataset}").dataset.fields)


def experiments(bundle: Bundle) -> list[dict[str, Any]]:
    """Whether a metric's card cites a run on each evidence dataset, and if not, why.

    One record per dataset of ``evidence_datasets`` (``configs/cards/default.yaml``), in that
    order. ``state`` is ``measured`` (the card cites ``run``, and ``primary`` says whether its
    numbers are the card's main ones), ``not applicable`` (``reason`` says why) or ``not yet
    run``. The reasons the code can know are derived from what the metric declares and what the
    dataset offers: a periodic-only metric on a dataset that is not periodic, an ensemble metric
    on one realisation per frame, a metric of fields the dataset does not provide. A reason only
    a person can give is the card's ``not_run`` entry. ``note`` records that a pairwise or
    single-field metric on an ensemble dataset scores the member mean (``fmeval.ladder``).

    Raises:
        ValueError: If ``not_run`` names a dataset that is not evidence, one the card cites a
            run on, or one whose reason the code already knows; if the card cites a run on a
            dataset the metric cannot run on; or if an evidence dataset has no entry in
            ``evidence_dataset_properties``.
    """
    cards = load_cards_config()
    card = load_card(bundle)
    declared = _spec_fields(bundle)
    runs = recorded_runs(bundle)
    cited = {r["dataset"]: r["run"] for r in runs}
    where = f"{bundle.path.parent.name}/{bundle.name}/card.yaml, not_run"
    unknown = sorted(set(card.not_run) - set(cards.evidence_datasets))
    if unknown:
        raise ValueError(f"{where}: {unknown} are not evidence datasets; allowed: "
                         f"{list(cards.evidence_datasets)}")
    wanted = [f for f in declared["fields"] if f != "*"]
    rows = []
    for dataset, claim in cards.evidence_datasets.items():
        offers = cards.evidence_dataset_properties.get(dataset)
        if offers is None:
            raise ValueError(f"{dataset} has no entry in evidence_dataset_properties; add its "
                             "periodic and ensemble properties to configs/cards/default.yaml")
        reasons = []
        if declared["requires_periodic"] and not offers.periodic:
            reasons.append("needs a periodic domain, and this dataset is not periodic")
        if declared["arity"] == "ensemble" and not offers.ensemble:
            reasons.append("needs an ensemble, and this dataset has one realisation per frame")
        if wanted and not set(wanted) & set(_dataset_fields(dataset)):
            reasons.append(f"needs {' or '.join(wanted)}, which this dataset does not provide")
        person = card.not_run.get(dataset)
        if person and reasons:
            raise ValueError(f"{where}: the reason for {dataset} is already known from the "
                             f"metric's declaration ({'; '.join(reasons)}); remove the entry")
        if dataset in cited and (reasons or person):
            raise ValueError(f"{bundle.name} cites run {cited[dataset]} on {dataset}, where it "
                             f"is not applicable: {'; '.join(reasons) or person}")
        rows.append({
            "dataset": dataset,
            "claim": claim,
            "state": ("measured" if dataset in cited
                      else "not applicable" if reasons or person else "not yet run"),
            "run": cited.get(dataset),
            "primary": bool(runs) and runs[0]["dataset"] == dataset,
            "reason": "; ".join(reasons) or person,
            "note": ("scores the member mean" if offers.ensemble and not (reasons or person)
                     and declared["arity"] != "ensemble" else None),
        })
    return rows


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
        # One record per further run the card cites, each on another evidence dataset; the
        # primary run is `evidence`. Additive, like `experiments`.
        "other_evidence": [_summary(r) for r in recorded_runs(bundle)[1:]],
        **({"experiments": experiments(bundle)} if bundle.kind == "metric" else {}),
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
