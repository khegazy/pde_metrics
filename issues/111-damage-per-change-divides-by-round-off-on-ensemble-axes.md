# Damage per unit field change divides by round-off on the ensemble-dispersion axes

**Category:** analysis
**Priority:** medium — a generated table on every ensemble card reads the wrong way round
**Status:** open; reproduced, not fixed

## Context

`fmeval/analysis.py` computes, per (metric, field, degradation), `damage_per_change`: the
median damage at the harshest strength over `field_change_max`, the largest change the
degradation made to the field (around line 697, guarded only by `change > 0`). The profile
(`_profile`, around line 1096) ranks the degradations by it to give each card's
**selectivity**, **charges most for** and **charges least for**.

On an ensemble dataset the field change is measured on the prediction's point estimate, the
member mean. `spread_inflate` and `spread_deflate` scale the members about that mean and
preserve it exactly (`degradations/_shared/ensemble.py::scale_spread`, declared
`preserves: [ensemble_mean]`), so their `field_change_max` is round-off and the ratio is about
1e30.

## Evidence

From the committed fingerprints (`metrics/<name>/_generated/fingerprint.json`), run
`python -c "import json; ..."` over each bundle's `axes`:

| metric | degradation | field_change_max | damage_per_change |
|---|---|---|---|
| energy_score | spread_deflate | 1.39e-32 | 9.74e30 |
| energy_score | spread_inflate | 2.29e-31 | 1.36e30 |
| energy_score | bias | 0.380 | 2.60 |
| crps | spread_deflate | 1.39e-32 | 7.93e30 |
| rank_histogram | spread_deflate | 1.39e-32 | 5.75e31 |

The profile row of `energy_score`, `variogram_score`, `crps` and `rank_histogram` therefore
says the metric "charges most for `spread_deflate`" and "least for `bias`", whichever round-off
is smaller deciding the first. On `energy_score` the bias axis has the largest relative change
of the three (2.08 against 0.284 and 0.655 in its reactivity table), and the selectivity number
(0.575) is set by two infinities in effect. Found by the adversarial review of the
`energy_score` branch (October 2026).

## Options

1. Treat a `field_change_max` within round-off of zero (the `_is_round_off` test the analysis
   already uses elsewhere) as undefined, so `damage_per_change` is NaN and the profile ranks
   only the axes that changed the field. The ensemble cards' profile would then rank only
   `bias`, and selectivity would be NaN (fewer than two axes).
2. Measure the field change of an ensemble-only degradation on the member stack (for example
   the change in the members' RMS deviation from their mean), so the dispersion axes get a
   finite ratio with a meaning.

Option 1 is the smaller change and states the truth; option 2 needs a decision on what "field
change" means for a dispersion axis.

## Related

- `metrics/energy_score/card.md`, `metrics/variogram_score/card.md`: their Results say not to
  read the profile row's ranking on these axes.
- `metrics/crps/card.md`, `metrics/rank_histogram/card.md`: affected the same way, not edited.
