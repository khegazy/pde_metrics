# A false "not monotone under smoothing" declaration passes the contract test on round-off

**Category:** technical debt
**Priority:** low — it lets one wrong declaration through; no number moves
**Status:** open. Reproduced, not fixed.

## Context

`tests/test_metric_contract.py::test_monotone_on_synthetic_blur_ladder` checks a metric that
declares `monotone_under_smoothing=False` by requiring `abs(rho) < 1.0`, so that the declaration
cannot hide a metric that is in fact monotone. SciPy's Spearman coefficient for a perfectly
monotone five-point ladder can be 0.9999999999999999, which passes.

Found by the agent that built `variogram_score` (finding 022, adversarial review 2026-10-30):
after its fix the score was monotone on the ladder, yet its stale False declaration still passed.

## Evidence

```
python -c 'from scipy.stats import spearmanr; print(repr(spearmanr([0,1,2,3,4],[0.1,0.2,0.3,0.4,0.5])[0]))'
np.float64(0.9999999999999999)
```

## What would settle it

Compare with a tolerance (for example `abs(rho) < 1 - 1e-9`), or test the ranks directly: a ladder
whose values are strictly ordered is monotone whatever the coefficient's last bit.
