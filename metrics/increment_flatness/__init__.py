"""Increment flatness: a one-number alarm for lost intermittency.

Importing this package registers the metric. See ``card.md`` for what it measures, how to
read it, and where it misleads.
"""

from __future__ import annotations

from .metric import SEPARATION_CELLS, axis_flatness, increment_flatness, increments

__all__ = ["SEPARATION_CELLS", "axis_flatness", "increment_flatness", "increments"]
