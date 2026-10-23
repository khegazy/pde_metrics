# The synthetic ensemble is generated from its own seed, not the run's

**Category:** method
**Priority:** low — no number is wrong; a recorded seed does not say what it appears to say
**Status:** open, needs an owner decision

## Context

`configs/dataset/synthetic_ensemble.yaml` feeds `SyntheticEnsembleTrajectory`
(`fmeval/data/synthetic_ensemble.py`), whose constructor takes `seed: int = 0` and derives every
draw of the reference and of each member from it. `evaluate.py` passes the reader only
`dataset.reader`, which does not state `seed`, so the generated data always come from seed 0.
The run seed (`seed` in `configs/config.yaml`, 20260807) reaches only the degradation operators,
and the three operators of `configs/degradation/ensemble_miscalibration.yaml` (`spread_inflate`,
`spread_deflate`, `bias`) draw nothing.

Found while reviewing the move of every default into the code that owns it (October 2026). It
was left alone there on purpose, because changing it changes every number of a
`synthetic_ensemble` run, and with them the evidence of four metric cards.

## Evidence

The third run of `docs/recipes/verify-a-refactor.md` (`dataset=synthetic_ensemble
degradation=ensemble_miscalibration metrics=[crps,spread_skill,ensemble_mean_rmse,rank_histogram]`)
repeated with `seed=1`: all 624 result rows have bitwise identical `value`s to the run with the
default seed; only the `seed` column, `run_meta.json`'s `seed` and the command differ.

What the record says: the four ensemble cards (`crps`, `spread_skill`, `ensemble_mean_rmse`,
`rank_histogram`) state "seed 20260807" in their evidence line, and their `fingerprint.json`
records `"seed": 20260807`. The seed that generated their data is 0, which `run_meta.json` now
records under `reader_options.seed`.

## Consequence

- `seed=<n>` on a synthetic run produces the same numbers, so it cannot be used to draw another
  realization of the calibrated null and see how much a metric's value moves between draws.
- A reader of a card is told the run seed, which had no effect on the measurement.

## Decision needed

One of:

1. Pass the run seed to a reader that takes one (`fmeval/data/readers.py::open_trajectory`), so `seed`
   means "every random draw of the run". This changes every number of a synthetic run; the four
   ensemble cards must be regenerated from a new pinned run.
2. Keep the generator's seed separate and state it on the card's evidence line beside the run
   seed, taking it from `run_meta.json`'s `reader_options`.

Either way, `docs/recipes/verify-a-refactor.md` needs no change: its third run compares two runs
with the same seed.
