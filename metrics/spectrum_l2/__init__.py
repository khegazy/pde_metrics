"""Radial energy spectrum distance: a phase-blind baseline.

Importing this package registers the metric. See ``card.md`` for what it measures, how to
read it, and where it misleads.
"""

from __future__ import annotations

from .metric import radial_energy_spectrum, spectrum_l2

__all__ = ["radial_energy_spectrum", "spectrum_l2"]
