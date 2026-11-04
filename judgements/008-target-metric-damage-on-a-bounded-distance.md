# 008 — A target-valued metric's damage is a bounded distance from the target, zero at the target

**Date:** 2026-11-04. **Made by:** the agent resolving issue 123 (task
`harness-target-anchor-correlation`, branch from `update_metric_eval_principles`).
**Reverse with:** `fmeval/analysis.py::_oriented` (return `|ln(v / target)|` with zero mapped to a
large constant), `normalisation` and `add_damage` (drop the target branch); then regenerate the
`spread_skill` and `tail_exceedance` cards and every "Compared with the other metrics" table that
lists `tail_exceedance`, delete this file and its row in `README.md`.

## The question that would have been asked

`spread_skill` and `tail_exceedance` are calibrated at 1 and wrong on both sides of it. Their
ordering statistics already read the log ratio |ln(v / 1)|. What should their **damage** be, so
that it reads 0 when calibrated and rises toward the anchor in both directions, and what should a
value of 0 be, which both metrics reach (an ensemble collapsed onto its mean; a smoothed field
with no extreme increments) and which the log ratio puts infinitely far away?

## The choice

**The distance from the target is q(v) = |v - t| / (v + t), and the damage is
D = q(v) / q(anchor).** Derivation: with x = v / t = e^u, (x - 1) / (x + 1) = (e^u - 1) / (e^u + 1)
= tanh(u / 2), so q = tanh(|ln(v / t)| / 2). It is an increasing function of the log ratio, so it
orders every value exactly as the log ratio does and no rank statistic changes in kind; it is
symmetric in the same way (q(t x) = q(t / x), half and twice the target both read 1/3); and it is
bounded by 1, which zero and infinity both reach. The log ratio is the symmetric measure of
relative change (Törnqvist, Vartia and Vartia 1985, *The American Statistician* 39(1), 43–46,
from the abstract); the bounded transform of it is this agent's construction, chosen for the
reasons below, not a convention found in the verification literature.

The damage is measured from the target, not from the clean value, so the clean prediction's own
miscalibration (the synthetic ensemble's sampling error, 0.990 against 1) is its damage, and the
anchor never flips the sign: the mean-field anchor sits on the collapsed side of the ratio
(0.0040 for `spread_skill`, exactly 0 for `tail_exceedance`) and inflation still reads positive
damage.

## Why not the log ratio itself

Measured on the runs this change regenerates:

- `tail_exceedance` scores exactly 0 on the mean-field anchor on all three fields
  (`comparison_1793657627`). On the log scale the anchor is infinitely far away, so
  D = |ln v| / inf is 0 for every finite value and NaN at zero: no damage scale at all.
- Its blurs and low-pass filters reach 0 at the harsher strengths. With 0 at +inf, two such
  strengths cannot be compared (inf - inf is NaN), and the round-off guard, which keeps only finite
  values, withheld the rank correlation of `gaussian_blur`, `box_blur`, `lowpass_ideal` and
  `lowpass_butterworth` on density and velocity, the axes the metric responds to most (issue 123).
- Mapping 0 to a large finite constant instead would make the damage of every other value depend
  on an arbitrary number.

## What it changes

Every damage-derived number of the two metrics: `damage`, `damage_max`, the blindness bound and
`blind_axes`, `damage_per_change` and the selectivity profile (these were withheld before), the
response columns (elasticity, response shape, severity at 10% and 50%, severity resolution) and
the sensitivity and saturation levels, and `span`, which for such a metric is q(anchor).
Two neighbouring strengths both at q = 1 count as in order in `monotone_fraction`; they remain a
tie to the rank correlation. The reported `value` is unchanged: the raw ratio, as the literature
reports it.
