---
type: EXP
kind: degradation
related: ["issues/070"]
seen_in: "orchestrator's own"
doi: "none"
found_by: "orchestrator, 2026-10-23"
---

# EXP: Controlled violations of admissibility conditions

## What the experiment is

Degradations whose damage is a known violation of a physical constraint:

1. **Negative excursions.** Subtract a known amount from density (or pressure) in a known fraction
   of cells, chosen at random with the run's generator, so that a known number of cells becomes
   negative by a known amount.
2. **Non-finite values.** Replace a known number of cells with NaN or infinity.

## What it tests

It changes the number of inadmissible cells and the most negative value by known amounts. No
current degradation produces a negative density on `kinet_re5e4`, and none produces a non-finite
value.

## Metrics it would test

The positivity and finite-value parts of the admissibility checks (issue 070).

## Why it is helpful

Without it the admissibility checks can never be validated, although they are among the cheapest
and most decisive physical checks on a prediction.

## Cost and requirements

Two small degradation bundles. The non-finite form needs a decision first: the harness validates
that frames are finite (`Trajectory.frame()`), so a deliberately non-finite prediction must be
allowed past that check for this degradation only.

## References

None; the proposal is the orchestrator's own.
