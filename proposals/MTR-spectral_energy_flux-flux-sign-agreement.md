---
type: "MTR"
kind: "variant of spectral_energy_flux"
related: ["spectral_energy_flux", "docs/ideas/turbulence_statistics/energy_transfer_checks.md"]
seen_in: "agent's own"
doi: "none"
found_by: "spectral_energy_flux, 2026-10-30"
---

# MTR: Direction-of-transfer disagreement, a dimension-neutral backscatter fraction

## What it measures

The fraction of octaves at which the prediction moves energy the other way from the reference:
the flux curves have opposite signs. It generalises the idea page's backscatter sign fraction,
which counts only octaves where the prediction has a negative flux and the reference a positive
one, and so presumes a forward cascade.

## Definition

My own: S = (1 / n_K) * #{K : sign(Pi_cand(K)) != sign(Pi_ref(K)) and |Pi_ref(K)| > t}, over
the octave wavenumbers of `spectral_energy_flux`'s companion, with Pi from Alexakis & Biferale
(2018, Eq. 18 of arXiv:1808.06186). The threshold t excludes octaves where the reference's flux is
round-off; it would have to be fixed once in terms of the reference's own curve (for example a
fraction of its largest magnitude), never tuned. A second variant: compare the shell-by-shell
transfer T(k) (the differences of Pi) rather than the cumulative Pi, which localises where a
prediction gains or loses energy instead of where it moves it across.

## Relation to existing work

The built `spectral_energy_flux` measures the size of the gap between the curves; this measures
only its direction, and is the reading the idea page's backscatter fraction was after. The
narrowed idea page (energy-transfer checks) keeps the original, forward-cascade form.

## How it could be tested

From the companion curves already stored in `companions.csv` by any `spectral_energy_flux` run:
no new computation of the flux. Blurs and low-pass filters should leave the low octaves' sign
intact and flip or zero the high ones; the graded phase randomisation EXP would drive it toward
one half.

## Why it is helpful

In two dimensions the sign of the flux is the physics (Kraichnan 1967, via Alexakis & Biferale
2018, Sect. 3.2.1); a surrogate that reverses the cascade at some scale is wrong in a way a
magnitude can understate.

## References

- Alexakis, A. & Biferale, L. (2018). Cascades and transitions in turbulent flows. *Physics
  Reports* 767-769, 1-101. doi:10.1016/j.physrep.2018.08.001
