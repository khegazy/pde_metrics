---
type: MTR
kind: variant of metrics/shock_set_distance
related: ["metrics/shock_set_distance", "issues/096"]
seen_in: "Schaal & Springel 2015, MNRAS 446, 3992-4007"
doi: "10.1093/mnras/stu2386"
found_by: "shock_set_distance, 2026-10-30"
---

# MTR: The full shock-zone detector, with a compression gate and the jump across the zone

## What it measures

The same shock-set distance, with the detector Schaal and Springel actually use rather than
its pressure half: a cell is in a shock zone only if the flow is compressing there and the
temperature and density rise together, and the jump is measured across the whole zone rather
than across one cell's two neighbours.

## Definition

Schaal & Springel (2015), Sect. 2.3.2: (i) $\nabla\cdot\mathbf{v} < 0$; (ii)
$\nabla T \cdot \nabla \rho > 0$; (iii) $\Delta\log T \ge \log(T_2/T_1)|_{M_{\min}}$ and
$\Delta\log p \ge \log(p_2/p_1)|_{M_{\min}}$ with $M_{\min} = 1.3$, the ratios from their
Eqs. (2) and (3), and $\Delta$ taken between the first cells outside the zone along the
temperature gradient (Sect. 2.3.3). A Ducros-type dilatation-vorticity ratio (Ducros et al.
1999) is the alternative compression gate used in shock capturing.

## Relation to existing work

`shock_set_distance` applies (iii) for pressure only, across a three-cell stencil, because a
metric receives one field. Its card records the consequences: a shock wider than about four
cells is missed, and noise and any steep non-compressive pressure change are flagged.

## How it could be tested

On `sod_shock_tube` with the same ladder: `gaussian_blur` and `coarsen_bandlimited`, which
remove the shock from the three-cell detector at every strength, would instead give a
distance; `additive_noise` false positives would be cut by the compression gate.

## Why it is helpful

It is the detector the shocklet case needs, where turbulence produces steep pressure changes
that are not shocks. It needs the harness to hand one metric several fields (issue 096).

## References

- Schaal, K. & Springel, V. (2015). *MNRAS* 446, 3992-4007, Sect. 2.3.2-2.3.3, Eqs. 2-3.
  <https://doi.org/10.1093/mnras/stu2386> (arXiv HTML read).
- Ducros, F. et al. (1999). *J. Comput. Phys.* 152(2), 517-549.
  <https://doi.org/10.1006/jcph.1999.6238> (abstract read).
