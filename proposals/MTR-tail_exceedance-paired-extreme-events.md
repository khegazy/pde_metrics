---
type: "MTR"
kind: "new metric"
related: ["metrics/tail_exceedance", "metrics/max_error", "docs/ideas/distributional/tail_index_estimators.md"]
seen_in: "Ferro & Stephenson 2011, Weather and Forecasting 26(5), 699-713"
doi: "10.1175/WAF-D-10-05030.1"
found_by: "tail_exceedance, 2026-10-31"
---

# MTR: Where the extreme increments are: a paired score for rare events

## What it measures

Whether the prediction's extreme one-cell increments sit in the same cells as the reference's.
`tail_exceedance` counts events without pairing them, so it is blind to position: a prediction
whose extreme jumps are all in the wrong place scores 1. Pairing cell by cell gives a 2 by 2
contingency table of hits, misses, false alarms and correct negatives for the event "increment at
least the reference's $k$-th largest", and a rare-event verification score summarises it.

## Definition

With the event defined as in `tail_exceedance`, count hits $a$, false alarms $b$, misses $c$ and
correct negatives $d$ cell by cell. Ferro and Stephenson (2011) propose the extremal dependence
index and its symmetric form, scores that stay informative as the base rate of the event goes to
zero. I could not open the paper (the publisher and the Exeter repository refused the fetch), so
no equation is given here; the formula must be taken from the paper itself before anything is
built. Search summaries describe the symmetric index as built from logarithms of the hit rate and
false-alarm rate, ranging from -1 to 1 with 1 perfect.

## Relation to existing work

`tail_exceedance` (built) is the frequency bias, $(a+b)/(a+c)$, which needs no pairing. `max_error`
is pointwise but reads one cell. Nothing in `docs/catalog.json` or `docs/ideas/` scores the
co-location of extreme events. Because it pairs cells, it has the double penalty: a sharp front
displaced by one cell turns every hit into a miss and a false alarm.

## How it could be tested

`translate_x` moves every extreme event off its cell, so a paired score falls from perfect at
the first displacement; blur and noise act as on `tail_exceedance`. A neighbourhood version
(counting a hit within a window, as spatial verification methods do) would be the natural fix for
the double penalty, and `translate_x`'s ladder would show the window width.

## Why it is helpful

It is the position-sensitive companion of a position-blind count, built from the same events, and
it is the standard family of scores for rare binary events in weather verification.

## References

- Ferro, C. A. T. & Stephenson, D. B. (2011). Extremal dependence indices: improved verification
  measures for deterministic forecasts of rare binary events. *Weather and Forecasting* 26(5),
  699–713. doi:10.1175/WAF-D-10-05030.1 (not read; see Definition).
