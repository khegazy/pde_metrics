# 006 — The contract tests give a metric that declares only density a positive field

**Date:** 2026-10-31. **Made by:** the agent that built `wasserstein` (branch `metric/wasserstein`).
**Reverse with:** delete `POSITIVE_FIELDS`, `POSITIVE_OFFSET` and `_field_for` from
`tests/test_metric_contract.py` and call `synthetic_field` directly again. `wasserstein` then
fails the contract tests, so the metric would need a value for signed fields first, which is
`issues/047`'s decision.

## The question that would have been asked

`tests/test_metric_contract.py` runs every registered metric on a signed synthetic field. It
requires a finite number, zero on identical fields and a perfect ranking of a blur ladder.
`wasserstein` is a transport distance between densities and has no value on a field with a
cell at or below zero. Any rule that gave it one would be a signed-field formulation, which
the brief and `issues/047` keep for a person to choose. So either the metric invents a
value outside its domain, or the shared contract tests change how they build their input.
Which?

## The choice

**A metric whose declared fields are all positive by definition, which today means
`fields=("density",)`, is handed the synthetic field moved up by 3.** The synthetic field
stays within about ±2, so the moved field is at least 1 everywhere. The contract tests then
check that metric on its real domain. Every other metric receives exactly the input it
received before. `wasserstein` returns NaN for a field with a non-positive cell, and its own
`test_metric.py` pins that.

- **Issue 101 already proposes it.** It says "the contract tests should exercise such a
  metric on its real domain" and names "a synthetic input with a positive offset, used for
  any metric that declares a positive field". It also names "the second metric that needs a
  positive field" as the moment to decide. `wasserstein` is that second metric, after
  `shock_set_distance`.
- **The alternative was worse.** `shock_set_distance` gave its detector a convention for
  non-positive pressure (`issues/102`). For a transport distance there is no such convention
  that is not a choice between the four formulations of `issues/047`.

## What it changes

- Only the inputs of metrics that declare nothing but density. Today that is `wasserstein`
  alone. `persistence_distance` declares density and vorticity, so it is unaffected.
- Pressure is not in the positive set, although a thermodynamic pressure is positive:
  issue 101 exists because a dataset may store a gauge pressure with both signs, so
  `shock_set_distance` keeps its signed input and its own non-positive convention.
- Issue 101's open choice, a declaration on the decorator or a split of the field vocabulary,
  is not made here. The set of positive fields lives in the test module, where nothing else
  reads it. If issue 101 adds a declaration, the test should read that instead.
