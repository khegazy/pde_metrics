# On sod_shock_tube the unrelated-field anchor is poorly determined, so Sod damage numbers are too

**Category:** method
**Priority:** medium — every damage number on a card evidenced on `sod_shock_tube` depends on it
**Status:** open, needs an owner decision

## Context

The damage scale runs from the undegraded reference (0) to the unrelated field (1), measured by
`random_large_translation`: a roll by a random offset from the middle half of each axis, averaged
over six draws (`uncorrelated` in `configs/degradation/default.yaml`). That operator's own
docstring says it decorrelates only a broadband field, that a field dominated by its largest scale
keeps a residual correlation no offset makes reliably small, and that the spread across draws is
the diagnostic: if it is wide, the anchor is not trustworthy for that field. On `kinet_re5e4`
vorticity the six draws agree within 0.96–1.03 (same docstring).

`sod_shock_tube` is the opposite case. Its calibration (`data/calibration.csv` of the run below)
puts 50% and 90% of the density and pressure fluctuation energy at the first wavenumber
(`k_energy_50` = `k_energy_90` = 1; `k_energy_99` = 5.8 for density and 6.0 for pressure), and
the characteristic scale of both, about 3000 cells, exceeds the 2048-cell tube.

Found by the agent that admitted `sod_shock_tube` as card evidence (branch
`metric/sod_evidence`, 2026-10-24); the numbers below were re-measured from the same run folder
before this issue was filed.

## Evidence

`python evaluate.py metrics=[mse] dataset=sod_shock_tube paths.data_url=null` at commit
`44e2077` with a clean tree, run `mse_1792825406` (default ladder, the reader's own 10 frames,
2048 cells). Per frame, the ratio of the largest to the smallest `mse` over the six anchor draws:

| field | median over frames | largest |
|---|---|---|
| density | 1.62 | 1.99 |
| pressure | 1.73 | 2.21 |
| velocity | 6.47 | 21.0 |

So the denominator of every Sod damage number (the impostor's damage, the first severity
detected, the damage-by-level tables, the blindness bound) moves by a factor of about 1.6–2 on
density and pressure, and up to 21 on velocity, depending on where the draws land.

## Decision needed

One of:

1. Keep the anchor and report its draw spread beside every Sod damage number.
2. An anchor built from the closed form: the exact solution with the same states at a distant
   time, or with the diaphragm elsewhere; statistically related, positionally unrelated, and
   deterministic. (The agent's own idea; no source.)
3. `analysis.anchor` set to a mean-field anchor once [040](040-mean-field-anchor.md) is built.

Which one changes what damage 1 means on Sod, so it is a person's decision. Until then the Sod
page (`docs/datasets/sod_shock_tube.md`) records the spread.
