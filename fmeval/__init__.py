"""The evaluation harness: data readers, the degradation ladder, analysis and reporting.

Importing this package installs one thing: the card validator, which makes the metric and
degradation registries refuse to hand back something whose documentation is missing or
disagrees with the code. It is installed here, rather than inside the registries, so that
``import metrics`` on its own stays free of this package's dependencies, and so that a
half-written card in one bundle cannot break a run of an unrelated metric. See
``fmeval/cards/loader.py`` for the reasoning in full.

It also defines the two paths every module that reads a repository file starts from,
``REPO`` and ``CONFIGS``. Nothing else is re-exported. Modules are imported by their full
path, so that a reader following an import knows exactly which file to open.
"""

from __future__ import annotations

import logging
from pathlib import Path

#: The repository root, found from this file rather than the working directory: nothing here
#: requires being run from the root. Defined before the card validator below is imported, so
#: the modules it loads can already use it.
REPO = Path(__file__).resolve().parent.parent
#: The Hydra configuration directory.
CONFIGS = REPO / "configs"

# Wire up card enforcement, tolerating an incomplete checkout. A failure here must not stop the
# harness importing: the validator is a guard rail, and a broken guard rail should be visible
# without also making the tool unusable. Hence the guarded import.
try:
    from .cards.loader import install

    install()
except Exception:  # deliberately broad, see the comment above
    logging.getLogger(__name__).debug("card validation unavailable", exc_info=True)
