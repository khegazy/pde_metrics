# The pointwise controls accept shapes that numpy can broadcast

**Category:** technical debt
**Priority:** low — the pipeline always passes matching arrays; a direct caller does not
**Status:** open. Reproduced, not fixed.

## Context

`mae`, `mse`, `rmse` and `nrmse` subtract the two fields without comparing their shapes, so a
one-channel field against a two-channel one, or `(X, 1)` against `(X, Y)`, returns a plausible
number. `tests/test_metric_contract.py::test_rejects_mismatched_shapes` cannot catch it: its
mismatch, 16 x 8 against 16 x 10, does not broadcast. `max_error` (pull request 25) now refuses
any shape mismatch, after its adversarial review (2026-10-30) found the same gap there.

## Evidence

Fields of ones `(1, 8, 8)` against zeros `(2, 8, 8)`:

```
mae 1.0    mse 1.0    rmse 1.0    nrmse nan
```

## Options

1. Add a broadcastable mismatch to the contract test and a shape check to each control.
2. Validate shapes once in the pipeline, before any metric is called.
3. Accept it, since the pipeline always feeds matching arrays.
