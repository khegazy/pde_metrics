"""H^-1: a dual norm of the error, weaker than L2 and close to the Wasserstein distance.

Importing this package registers the metric. See ``card.md`` for what it measures, how to
read it, and where it misleads.
"""

from __future__ import annotations

from .metric import h_minus_one, h_minus_one_map, riesz_potential

__all__ = ["h_minus_one", "h_minus_one_map", "riesz_potential"]
