"""Increment-PDF 1-Wasserstein distance: compares increment statistics, ignores position.

Importing this package registers the metric. See ``card.md`` for what it measures, how to
read it, and where it misleads.
"""

from __future__ import annotations

from .metric import axis_w1, increment_w1

__all__ = ["axis_w1", "increment_w1"]
