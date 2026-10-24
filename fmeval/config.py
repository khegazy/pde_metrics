"""The schemas of the configuration, and the one way to load each part of it.

Every block of ``configs/`` is either the keyword arguments of one callable -- a reader's
constructor (``dataset.reader``), an operator's options (``degradation.ladder.<entry>.options``)
-- or the fields of one dataclass below or imported here. That callable or dataclass owns the
defaults, so a YAML file states a key only to change it. The schema is what lets a YAML leave a
key out without Hydra's struct mode demanding ``+`` to override it, and it names a misspelt or
missing key when the run starts rather than when the value is first read.

The card-generation settings, ``configs/cards/default.yaml``, are not a Hydra group:
generating documentation is not an experiment and must not create a run folder, so
:func:`load_cards_config` reads that file directly, into :class:`CardsConfig`.

Registering the schema, and the ``${repo:}`` resolver that ``paths.data`` uses, is a side
effect of importing this module: ``evaluate.py`` imports it before ``hydra.main`` composes
``configs/config.yaml``, whose defaults list starts with ``_schema``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hydra import compose, initialize_config_dir
from hydra.core.config_store import ConfigStore
from hydra.core.hydra_config import HydraConfig
from omegaconf import MISSING, DictConfig, OmegaConf, open_dict

from fmeval import CONFIGS, REPO
from fmeval.data.base import TimeSelection
from fmeval.ladder import DegradationConfig
from fmeval.pipeline import MapRequest
from fmeval.remap import DEFAULT_METHOD


@dataclass
class Complexity:
    """Where a dataset sits on the ladder of physical complexity, for cross-dataset plots."""

    family: str = MISSING
    rank: int = MISSING
    """Order within the family; negative for a generated dataset, which is not physical."""
    params: dict[str, Any] = field(default_factory=dict)
    label: str = MISSING


@dataclass
class DatasetConfig:
    """A ``configs/dataset/`` option."""

    name: str = MISSING
    format: str = MISSING
    """The reader, by its ``@register_reader`` name."""
    path: str = MISSING
    trajectory: str = MISSING
    fields: list[str] = MISSING
    complexity: Complexity = field(default_factory=Complexity)
    notes: str = MISSING
    time: TimeSelection = field(default_factory=TimeSelection)
    reader: dict[str, Any] = field(default_factory=dict)
    """Keyword arguments of the reader's constructor, which owns their defaults; an unknown
    key raises ``TypeError`` there. A key no YAML states is overridden with ``+``."""
    recompute_derived: bool = True
    """Recompute derived fields with our own operator even at the native resolution, so the
    native grid and every coarse grid use the same discretisation."""


@dataclass
class ReportConfig:
    """The ``report`` group: what a run records for its report."""

    error_map: MapRequest = field(default_factory=MapRequest)
    thresholds: dict[str, float] = MISSING


@dataclass
class Paths:
    data: str = MISSING
    results: str = MISSING
    data_url: str | None = MISSING


@dataclass
class AnalysisGrid:
    """The common grid every field is compared on (IN-2)."""

    resolution: int | None = None
    """None keeps the native resolution; an int coarsens to it, recomputing derived fields."""
    method: str = DEFAULT_METHOD
    """``block_mean`` (conservative) or ``subsample`` (aliasing control). A ``str`` because
    OmegaConf cannot type a ``Literal``; ``fmeval.remap`` refuses any other name."""


@dataclass
class Analysis:
    anchor: str = MISSING


@dataclass
class Config:
    """The whole job config ``evaluate.py`` receives."""

    paths: Paths = field(default_factory=Paths)
    metrics: list[str] = MISSING
    fields: list[str] | None = None
    """Canonical fields to evaluate; None means every field the dataset lists that at least
    one selected metric accepts."""
    analysis_grid: AnalysisGrid = field(default_factory=AnalysisGrid)
    analysis: Analysis = field(default_factory=Analysis)
    seed: int = MISSING
    dataset: DatasetConfig = MISSING
    degradation: DegradationConfig = MISSING
    report: ReportConfig = MISSING


ConfigStore.instance().store(name="_schema", node=Config)
# The repository root, so `paths.data` finds the `datasets` link beside the code from any
# working directory.
OmegaConf.register_new_resolver("repo", lambda: str(REPO))


@dataclass
class EvidenceWindow:
    """The developed-flow window a run cited as evidence follows (``dataset.time.start`` and
    ``reduction``). Nothing selects frames with it; a test checks the exemplar frame lies in it."""

    start: int = MISSING
    reduction: int = MISSING


@dataclass
class ExemplarFrame:
    """The one snapshot every exemplar panel is drawn from."""

    dataset: str = MISSING
    index: int = MISSING
    fields: list[str] = MISSING


@dataclass
class Figures:
    dpi: int = MISSING
    """Exemplar panels are PNG; fixed so regenerating an unchanged panel changes no byte."""


@dataclass
class CardsConfig:
    """``configs/cards/default.yaml``, which is the only source of every value here."""

    evidence_datasets: dict[str, str] = MISSING
    """The datasets a card's measurements may come from, each mapped to the kind of claim a
    run on it supports, as the phrase that completes "n frames of ..." in a card's run summary."""
    evidence_window: EvidenceWindow = field(default_factory=EvidenceWindow)
    exemplar_frame: ExemplarFrame = field(default_factory=ExemplarFrame)
    figures: Figures = field(default_factory=Figures)


def load_cards_config() -> CardsConfig:
    """The card-generation settings, with an unknown, missing or mistyped key refused, named."""
    return OmegaConf.to_object(
        OmegaConf.merge(CardsConfig, OmegaConf.load(CONFIGS / "cards" / "default.yaml")))


def build_job(cfg: DictConfig) -> Config:
    """Build a composed config into the schema dataclasses, before any data is read.

    A ``MISSING`` key, a value a dataclass refuses (``TimeSelection.__post_init__``) or a key
    no dataclass declares raises here, naming the key. The last needs the merge into the bare
    schema: ``+key=value`` adds a key that struct mode would otherwise refuse, and
    ``OmegaConf.to_object`` would keep it as a stray attribute, so ``+dataset.time.max_frame=3``
    would run with ``max_frames`` at its default. Keys inside an untyped mapping
    (``dataset.reader``, a ladder entry's ``options``) are checked by the callable they feed.
    """
    return OmegaConf.to_object(OmegaConf.merge(Config, OmegaConf.to_container(cfg)))


def compose_config(*overrides: str) -> DictConfig:
    """The job config as ``hydra.main`` hands it to ``evaluate.py``, with CLI-style overrides.

    Installs the ``HydraConfig`` singleton, which ``${hydra:runtime.cwd}`` in ``paths`` needs,
    and removes the ``hydra`` node, as ``hydra.main`` does. Creates no run directory. Not for
    use inside a Hydra run: ``initialize_config_dir`` refuses an already initialised Hydra.
    """
    with initialize_config_dir(config_dir=str(CONFIGS), version_base=None):
        cfg = compose(config_name="config", overrides=list(overrides), return_hydra_config=True)
        HydraConfig.instance().set_config(cfg)
        with open_dict(cfg):
            del cfg["hydra"]
        return cfg
