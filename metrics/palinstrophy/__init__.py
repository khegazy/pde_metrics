"""Palinstrophy: a reference-free diagnostic of how sharp the vorticity field is.

Importing this package registers the metric. See ``card.md`` for what it measures, how to
read it, and where it misleads.
"""

from __future__ import annotations

from .metric import palinstrophy

__all__ = ["palinstrophy"]
