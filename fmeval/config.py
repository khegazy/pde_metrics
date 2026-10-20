"""The schema of the Hydra configuration, and the one way to compose it outside ``hydra.main``.

Every block of ``configs/`` is either the keyword arguments of one callable -- a reader's
constructor (``dataset.reader``), an operator's options (``degradation.ladder.<entry>.options``)
-- or the fields of one dataclass below or imported here. That callable or dataclass owns the
defaults, so a YAML file states a key only to change it. The schema is what lets a YAML leave a
key out without Hydra's struct mode demanding ``+`` to override it, and it names a misspelt or
missing key when the run starts rather than when the value is first read.

Registering the schema is a side effect of importing this module: ``evaluate.py`` imports it
before ``hydra.main`` composes ``configs/config.yaml``, whose defaults list starts with
``_schema``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hydra import compose, initialize_config_dir
from hydra.core.config_store import ConfigStore
from hydra.core.hydra_config import HydraConfig
from omegaconf import MISSING, DictConfig, open_dict

from fmeval import CONFIGS
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
