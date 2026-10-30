---
type: MTR
kind: variant of metrics/shock_set_distance
related: ["metrics/shock_set_distance", "issues/096"]
seen_in: "Schaal & Springel 2015, MNRAS 446, 3992-4007"
doi: "10.1093/mnras/stu2386"
found_by: "shock_set_distance, 2026-10-30; revised 2026-10-31"
---

# MTR: The full Schaal-Springel shock finder, with a compression gate and a single-layer surface

## What it measures

The same shock-set distance, with the shock finder Schaal and Springel actually use rather than
the pressure half of one criterion: a cell is in the shock zone only if the flow is compressing
there and temperature and density rise together, and the zone is then thinned to a shock surface
one cell thick before any distance is taken.

## Definition

Schaal & Springel (2015), Sect. 2.3.2: (i) $\nabla\cdot\mathbf{v} < 0$; (ii)
$\nabla T \cdot \nabla \rho > 0$; (iii) $\Delta\log T \ge \log(T_2/T_1)|_{M_{\min}}$ and
$\Delta\log p \ge \log(p_2/p_1)|_{M_{\min}}$ with $M_{\min} = 1.3$, the ratios from their
Eqs. (2) and (3), with $\Delta$ taken between "neighbouring cells along the shock direction".
Sect. 2.3.3 then reduces the zone, "typically 3–4 cells thick", to a shock surface of "a single
layer of cells" and estimates each surface cell's Mach number from the states of the cells just
outside the zone. A Ducros-type dilatation-vorticity ratio (Ducros et al. 1999) is the
alternative compression gate used in shock capturing.

## Relation to existing work

`shock_set_distance` applies only the pressure half of (iii), across a three-cell stencil along
each grid axis, because a metric receives one field, and it does not thin the flagged cells to a
surface, so a sharp step flags two cells and a step moved $s$ cells scores $s - 1/2$ cells. The
full finder would add the compression gate (rejecting noise and non-compressive steep pressure
changes) and the single-layer surface (a step moved $s$ cells would score $s$). It would not by
itself detect a shock smeared wider than about four cells: criterion (iii) is local in the paper
too: the whole-zone states serve the Mach-number estimate (Sect. 2.3.3, and Sect. 5's "variable
jump range"), not detection.

## How it could be tested

On `sod_shock_tube`: `translate_x` (with the single-layer surface the value should be the shift
itself), and `additive_noise`, whose false positives the compression gate would cut.

## Why it is helpful

It is the detector the shocklet case needs, where turbulence produces steep pressure changes
that are not shocks. It needs the harness to hand one metric several fields (issue 096).

## References

- Schaal, K. & Springel, V. (2015). *MNRAS* 446, 3992-4007, Sect. 2.3.2-2.3.3, Eqs. 2-3.
  <https://doi.org/10.1093/mnras/stu2386> (arXiv HTML read).
- Ducros, F. et al. (1999). *J. Comput. Phys.* 152(2), 517-549.
  <https://doi.org/10.1006/jcph.1999.6238> (read only through a search summary of its abstract).
