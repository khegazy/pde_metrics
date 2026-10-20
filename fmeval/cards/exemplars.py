"""Generate a degradation's exemplar panel from the one canonical frame.

Reads the frame named in ``configs/cards/default.yaml``, applies the operator at the three
severities the card declares, and renders the panel plus the numbers behind it. Every
panel in the repository comes from that one frame: two degradations illustrated on
different snapshots cannot be compared, which would defeat the gallery that puts all of
them on one page.

This reads the dataset directly and never a run folder. An exemplar shows what a
degradation does to a field, which is a property of the operator rather than of any
metric, so it needs no evaluation to have been performed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from omegaconf import OmegaConf

from degradations import registry as deg_registry
from fmeval.calibration import calibrate
from fmeval.config import CardsConfig, compose_config, load_cards_config
from fmeval.context import FieldContext, derive_rng, fluctuation_rms
from fmeval.data import kinet_raw, locate, well  # noqa: F401  (importing registers the formats)
from fmeval.data.base import READERS
from fmeval.ladder import SeverityLevel, resolve_severity

from . import loader
from .figures import Column, exemplar_panel
from .loader import load_card, write_strict_json
from .prose import write_block


@dataclass(frozen=True)
class CanonicalFrame:
    """The one snapshot every exemplar panel in the repository is drawn from."""

    index: int
    dataset: str
    fields: dict[str, np.ndarray]
    grid: Any
    time: float


def load_canonical_frame(cfg: CardsConfig | None = None, *,
                         allow_remote: bool = False) -> CanonicalFrame:
    """Read the canonical exemplar frame from the dataset it names.

    Args:
        cfg: Card settings; loaded from ``configs/cards/default.yaml`` if omitted.
        allow_remote: Permit reading the published copy over HTTP when there is no local
            one. Off by default; see the comment on the resolver call below.

    Returns:
        The frame, with every field the config asks to illustrate.

    Raises:
        FileNotFoundError: If the dataset is not reachable, which on a machine without the
            CFS mount is the expected outcome and the reason exemplars are generated where
            the data lives rather than in CI.
    """
    cfg = cfg or load_cards_config()
    # The dataset as `evaluate.py` would compose it, so a dataset config that inherits a
    # fragment, and the data root, are read the same way here. Composing creates no run
    # directory.
    composed = compose_config(f"dataset={cfg.exemplar_frame.dataset}")
    dataset = composed.dataset

    # The same resolver `evaluate.py` uses: two rules for where a dataset lives would
    # diverge the moment either one grows a case.
    #
    # `allow_url=False` on purpose. Exemplar panels are committed artifacts generated
    # where the data lives, and the documentation build must keep working on a runner with
    # no data at all; silently fetching 166 GiB worth of ranges during a docs build is not
    # an improvement. Pass allow_remote=True to opt in deliberately.
    try:
        location = locate.resolve_dataset_path(
            dataset.path, composed.paths.data, data_url=composed.paths.data_url,
            allow_url=allow_remote,
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"the canonical exemplar frame is not readable here.\n{exc}\n"
            "Exemplar panels are generated where the data lives (NERSC) and committed, "
            "rather than in CI."
        ) from None
    reader_kwargs = OmegaConf.to_container(dataset.reader, resolve=True)
    trajectory = READERS[dataset.format](location.target, **reader_kwargs)

    wanted = [f for f in cfg.exemplar_frame.fields if f in trajectory.fields]
    frame = trajectory.frame(cfg.exemplar_frame.index, wanted)
    return CanonicalFrame(index=cfg.exemplar_frame.index,
                          dataset=cfg.exemplar_frame.dataset,
                          fields=dict(frame.fields), grid=frame.grid, time=float(frame.time))


def build_columns(name: str, card: Any, frame: CanonicalFrame, *, seed: int) -> tuple[list, dict]:
    """Apply the operator at each declared severity and label the columns.

    Severities are resolved through the same path the ladder uses, so a calibrated axis
    shows the number that was actually applied to this field rather than the fraction that
    was configured. Titles carry that resolved value and its units, because "medium" does
    not describe a picture.

    Returns:
        The columns, and a record of what was applied for the fingerprint.
    """
    spec = deg_registry.get(name)
    field_name = card.exemplars.field_name
    data = frame.fields[field_name]

    calibration = calibrate({field_name: [data]}, frame.grid, [field_name])
    columns = [Column(title="original", data=data)]
    applied: dict[str, Any] = {"severities": [], "resolved": [], "mode": card.exemplars.mode}

    if card.exemplars.mode == "draws":
        for draw in range(card.exemplars.n_draws):
            ctx = _context(field_name, frame, data, seed=seed, label=f"{name}_draw{draw}")
            columns.append(
                Column(title=f"draw {draw + 1}", data=spec.fn(data, float(draw), ctx=ctx))
            )
            applied["severities"].append(draw)
        return columns, applied

    for severity in card.exemplars.levels:
        level = SeverityLevel.from_spec(spec, label=name, level=1, severity=severity, options={})
        resolved = resolve_severity(level, field_name, calibration)
        ctx = _context(field_name, frame, data, seed=seed, label=f"{name}_{severity}")
        if spec.ensemble:
            shown = _ensemble_member(spec, data, resolved, seed=seed)
        else:
            shown = spec.fn(data, resolved, ctx=ctx)
        # The title is the severity that was applied, with its units.
        units = f" {spec.severity_units}" if spec.severity_units else ""
        columns.append(Column(title=f"{spec.severity_name} = {resolved:.3g}{units}", data=shown))
        applied["severities"].append(float(severity))
        applied["resolved"].append(float(resolved))
    return columns, applied


#: Ensemble size for the exemplar panel of an operator that acts on a member stack.
EXEMPLAR_MEMBERS = 8


def _ensemble_member(spec: Any, data: np.ndarray, severity: float, *, seed: int
                     ) -> np.ndarray:
    """One member of a synthetic ensemble, before and after a dispersion operator.

    An ensemble operator has nothing to show on a single field: the canonical frame is one
    realization, and these operators change how a *set* of them is scattered. A small
    ensemble is therefore built around the canonical field -- members are it plus noise at
    a fixed fraction of its fluctuation -- the operator is applied to the whole stack, and
    the panel shows one member of the result.

    That is an honest picture of what a reader would see: the ensemble mean is unchanged
    by construction, so what visibly moves between the columns is how far an individual
    member strays from it, which is exactly the quantity these operators scale.
    """
    rng = np.random.default_rng(seed)
    scale = 0.3 * fluctuation_rms(data)
    members = data[None] + scale * rng.standard_normal((EXEMPLAR_MEMBERS, *data.shape))
    return np.asarray(spec.fn(members, severity))[0]


def _context(field_name: str, frame: CanonicalFrame, data: np.ndarray, *,
             seed: int, label: str) -> FieldContext:
    """A field context matching the one the pipeline builds, so panels match runs."""
    return FieldContext(
        field=field_name, grid=frame.grid, frame_index=frame.index, time=frame.time,
        fluctuation_rms=fluctuation_rms(data),
        rng=derive_rng(seed, label, frame.index, field_name),
    )


def generate(name: str, *, seed: int | None = None) -> Path | None:
    """Render one degradation's exemplar panel and write its caption and numbers.

    Args:
        name: The degradation bundle to illustrate.
        seed: Run seed, so a stochastic operator's draws reproduce. Defaults to ``seed`` in
            ``configs/config.yaml``, the one place the run seed is set.

    Returns:
        The path to the written panel, or ``None`` if the card declares ``mode: none``.
    """
    # Looked up through the module, so a test that substitutes `loader.find_bundle` with a
    # throwaway copy keeps the generator away from the tracked bundle.
    bundle = loader.find_bundle(name)
    if bundle is None:
        raise KeyError(f"no degradation bundle named {name!r}")
    card = load_card(bundle)
    if card.exemplars is None or card.exemplars.mode == "none":
        return None

    cfg = load_cards_config()
    frame = load_canonical_frame(cfg)
    if seed is None:
        seed = int(compose_config().seed)
    columns, applied = build_columns(name, card, frame, seed=seed)

    out = bundle.generated
    panel = exemplar_panel(
        columns, list(card.exemplars.diagnostics), path=out / "exemplars.png",
        title=f"{name} on {card.exemplars.field_name}, frame {frame.index}",
        grid=frame.grid, dpi=cfg.figures.dpi,
    )

    fingerprint = {
        "degradation": name,
        "field": card.exemplars.field_name,
        "dataset": frame.dataset,
        "frame_index": frame.index,
        "time": frame.time,
        "seed": seed,
        "applied": applied,
        "panels": panel.statistics,
    }
    write_strict_json(out / "exemplars.json", fingerprint)
    write_block(bundle.card_md, "exemplars",
                _caption(name, card, frame, applied, panel.statistics),
                command=f"python -m fmeval.cards exemplars {name}")
    return panel.path


def _caption(name: str, card: Any, frame: CanonicalFrame, applied: dict,
             statistics: dict) -> str:
    """The caption, stating what actually happened rather than what was expected.

    The card's rationale says why these severities were chosen; the measured numbers say
    what they did. Both belong under the figure, and only one can be written in advance.
    """
    lines = [
        f"![{name}: the same snapshot, undegraded and then degraded]"
        "(_generated/exemplars.png)",
        "",
        f"**{name}** on {card.exemplars.field_name}, frame {frame.index} of "
        f"`{frame.dataset}`. {card.exemplars.rationale}",
        "",
    ]
    columns = [c for c in statistics.get("field", {}) if c != "original"]
    if applied["mode"] == "severity" and applied.get("resolved"):
        lines += ["| strength requested in the config | strength actually applied to "
                  "this field | RMS size of the change | fraction of the field's power "
                  "kept |",
                  "|---|---|---|---|"]
        difference = statistics.get("difference", {})
        spectrum = statistics.get("radial_spectrum", {})
        for i, (configured, resolved) in enumerate(
            zip(applied["severities"], applied["resolved"])
        ):
            column = columns[i] if i < len(columns) else None
            rms = f"{difference[column]['rms']:.4g}" if column in difference else "--"
            retained = (f"{spectrum[column]['power_retained']:.4g}"
                        if column in spectrum else "--")
            lines.append(f"| {configured:g} | {resolved:.4g} | {rms} | {retained} |")
    else:
        lines.append(f"{len(columns)} independent random draws, seeded from the run seed "
                     "so that every draw reproduces exactly.")
    return "\n".join(lines) + "\n"
