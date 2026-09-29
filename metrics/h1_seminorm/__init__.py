"""H^1 seminorm: the positive-order mirror of h_minus_one, recorded as tested.

Importing this package registers the metric. See ``card.md`` for what it measures, how to
read it, and where it misleads.
"""

from __future__ import annotations

from .metric import h1_seminorm, h1_seminorm_map

__all__ = ["h1_seminorm", "h1_seminorm_map"]
