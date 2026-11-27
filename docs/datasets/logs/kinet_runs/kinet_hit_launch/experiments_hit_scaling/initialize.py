"""
Initial conditions for hit_scaling cases.

These are homogeneous isotropic turbulence cases, decaying and linearly forced. They
start from the same divergence-free Passot-Pouquet field as the forced cases of
``homogeneous_isotropic_turbulence``, on the equilibrium (no non-equilibrium
correction), so they reuse that experiment's ``init_hit_forced`` rather than a copy.
"""

from experiments.homogeneous_isotropic_turbulence import initialize as hit

init_hit_scaling = hit.init_hit_forced.for_cases(
    "Re-12p5k_Ma-1en1_2d",
    "Re-25k_Ma-1en1_2d",
    "Re-50k_Ma-1en1_2d",
    "Re-12p5k_Ma-1en1_linear_forced_2d",
    "Re-25k_Ma-1en1_linear_forced_2d",
    "Re-50k_Ma-1en1_linear_forced_2d",
)
