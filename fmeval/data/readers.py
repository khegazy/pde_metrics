"""The one place a dataset config becomes an open reader.

Readers are a deliberately closed set with explicit imports, unlike metrics and degradations
(``AGENTS.md`` §5): importing this module registers every format, and nothing else needs its
own import line. :func:`open_trajectory` is shared by ``evaluate.py``, the exemplar panels and
the dataset figures, so a reader is constructed the same way, and found in the same place,
whichever of them asks.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from . import analytic, kinet_raw, synthetic_ensemble, well  # noqa: F401  (register the formats)
from .base import READERS, Trajectory
from .locate import resolve_dataset_path

if TYPE_CHECKING:
    from fmeval.config import DatasetConfig, Paths

log = logging.getLogger(__name__)


def open_trajectory(dataset: DatasetConfig, paths: Paths, *,
                    allow_url: bool = True) -> Trajectory:
    """Construct the reader a dataset config names, on its local copy or its published one.

    Args:
        dataset: The dataset config, built into its schema.
        paths: ``paths.data`` and ``paths.data_url`` of the same config.
        allow_url: Whether a dataset with no local copy may be read over HTTP. The exemplar
            panels refuse, because they are committed artifacts generated where the data lives.

    Raises:
        KeyError: If the format is not a registered reader.
        FileNotFoundError: If a file-backed dataset has no reachable copy.
    """
    fmt = dataset.format
    if fmt not in READERS:
        raise KeyError(f"unknown dataset format {fmt!r}; available: {sorted(READERS)}")

    if not READERS[fmt].reads_from_disk:
        return READERS[fmt](Path(dataset.path), **dataset.reader)

    location = resolve_dataset_path(dataset.path, paths.data, data_url=paths.data_url,
                                    allow_url=allow_url)
    if location.source == "url":
        log.info("dataset %s is not on this filesystem; reading the published copy at %s",
                 dataset.name, location.url)
    return READERS[fmt](location.target, **dataset.reader)
