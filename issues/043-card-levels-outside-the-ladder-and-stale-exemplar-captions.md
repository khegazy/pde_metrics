# Four degradation cards illustrate strengths no ladder runs, and twenty exemplar captions are stale

**Category:** technical debt
**Priority:** low — no number in any table or figure is wrong; two documented rules are not enforced
**Status:** open, needs an owner decision

## Context

Found while consolidating duplicated definitions (October 2026). Neither finding comes from that
work; both were present at commit `12b0701`.

## 1. Card exemplar levels that no ladder uses

`fmeval/cards/schema.py` documents that a card's `exemplars.levels` "must be severities this
degradation's ladder actually uses", so that the panel on a degradation's page shows strengths
the evaluation really applies. Nothing enforces it, and four cards break it. Measured against every
file in `configs/degradation/`:

| degradation | card `exemplars.levels` | ladder severities | levels in no ladder |
|---|---|---|---|
| `bias` | 0.05, 0.2, 0.5 | 0.05, 0.15, 0.3, 0.6 (`ensemble_miscalibration`) | 0.2, 0.5 |
| `spread_deflate` | 0.25, 0.5, 0.9 | 0.25, 0.5, 0.7, 0.8 (`ensemble_miscalibration`) | 0.9 |
| `spread_inflate` | 0.25, 1.0, 3.0 | 0.25, 0.75, 1.5, 3.0 (`ensemble_miscalibration`) | 1.0 |
| `multiplicative_noise` | 0.01, 0.1, 0.5 | none: the operator is in no ladder | all three |

The other operators' cards each pick three of their four configured strengths, as intended.

**Decision needed:** either change these cards' levels (and regenerate their panels, which needs
the canonical frame on CFS), or amend the rule in `schema.py`. Once decided, a subset test in
`tests/test_cards.py` can enforce it; it was not added because it would fail today.

The contract test's `LADDERS` in `tests/test_degradation_contract.py` is a third, deliberately
separate list: it needs severities that give strictly increasing damage on the 32 x 16 contract
grid, where a 16-cell translation is half the period.

## 2. Twenty degradation cards carry exemplar captions older than their generator

Running `python -m fmeval.cards exemplars --all` at `12b0701` rewrites the generated `exemplars`
block of 20 degradation cards. The panels (`exemplars.png`) and their numbers (`exemplars.json`)
regenerate byte-identically; only two lines of caption text in each `card.md` change: the image's
alt text (`bias exemplar panel` becomes `bias: the same snapshot, undegraded and then
degraded`) and the table header (`configured | applied | ...` becomes `strength requested in the
config | ...`). The generator was reworded after the cards were last regenerated.

**Fix:** run `python -m fmeval.cards exemplars --all` where the data lives and commit the 20 cards.
It was not done in the consolidation work, so that change stayed free of content changes.
