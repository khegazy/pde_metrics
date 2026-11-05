# `multiplicative_noise` at its harshest severity makes density negative in some cells, where `wasserstein` is undefined

**Category:** method
**Priority:** unset
**Status:** open. Nothing is changed; the harshest level of the axis scores NaN for
`wasserstein` on density.

## Context

`multiplicative_noise` multiplies each cell by `1 + s * N(0, 1)`
(`degradations/multiplicative_noise/degradation.py`), and the evidence ladder runs it up to
`s = 0.5` (`configs/degradation/default.yaml`). At `s = 0.5` the factor is negative wherever the
draw is below -2, which a standard normal does with probability 0.0228, about 1500 of the 65536
cells of a 256^2 field (the agent's arithmetic). Density is positive everywhere, so the degraded
density has negative cells in every frame. At `s = 0.1` the factor is negative only below -10,
which does not happen on a field of this size in practice.

`wasserstein` is a distance between measures and returns NaN when either field has a cell that
is not positive (`metrics/wasserstein/metric.py`; the signed-field question is `issues/047`).
Measured on the smoke run `comparison_1793796393` (`kinet_re5e4_dev`, all 100 frames, 2026-11-04,
not evidence): `wasserstein` is NaN on exactly the 100 rows of `multiplicative_noise` level 5
(`s = 0.5`) and on no other row, with no convergence warning, so the NaN is the input-domain one.
Every other metric scores that level as a number, so on that level `wasserstein` drops out of
every cross-metric statistic. Its own trend on the axis is not read on the four other levels:
on the final evidence pass (`comparison_1793829127`, kinet_re5e4) the `wasserstein` card's
fingerprint has `n_levels` 5 for `multiplicative_noise`, every ordering statistic null and
`damage_max` 0.639, and the card shows the axis as a dash, the mark it also uses for a metric that
does not respond (found by the `readings-physics-norms` agent from `_per_frame_rho`; not re-run).
Either the analysis drops a NaN row per frame and reads the remaining levels, or this text and
the card say the axis is unread.

## What would settle it

One of: a positivity-preserving form of the operator for fields that are positive by nature
(a log-normal factor `exp(s N - s^2 / 2)` has mean one and never changes sign, the agent's
suggestion, not taken from a source), declared per field; a harshest severity below the point
where the factor can change sign; or a statement that a negative density is a legitimate failure
to probe and that a metric undefined on it reports NaN, as now. The choice changes every
metric's numbers on that level, so it is the harness's, not this metric's.

## Related

`issues/047` (signed fields for a transport distance), `metrics/wasserstein/card.md`
(Limitations), written with the transport norms' evaluation by their field's standard,
2026-11-04.
