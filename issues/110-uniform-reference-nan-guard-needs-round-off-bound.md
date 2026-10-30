# A uniform reference gives NaN only when its floating-point mean is exact

**Category:** technical debt
**Priority:** unset
**Status:** open. `spectral_energy_flux` is fixed on its own branch; `spectrum_l2` and `nrmse` are not.

## Context

Several metrics promise NaN for a spatially uniform reference, which has no scale to divide by,
and guard with an exact comparison: `nrmse` tests `fluctuation_rms(reference) == 0.0`, and
`spectrum_l2` tests that the norm of the reference's spectrum is `0.0`. Both quantities are taken
about the spatial mean (`fmeval/context.py::fluctuation`). The floating-point mean of a constant
equals the constant only for some values and grid sizes, so a uniform reference usually leaves a
round-off fluctuation, and the metric divides by it.

## Measured

On a uniform reference of 0.7 against a standard normal candidate (seed 0), with commands run
from the worktree of `metric/spectral_energy_flux`, 2026-10-30:

| metric | grid | value | promised |
|---|---|---|---|
| `spectrum_l2` | 32 x 32 | 1.92e31 | NaN |
| `spectrum_l2` | 30 x 34 | 2.21e31 | NaN |
| `nrmse` | 30 x 34 | 1.10e16 | NaN |

The adversarial review of `spectral_energy_flux` (pull request #26) found the same pattern
there (3.6e48 on 30 x 34). That bundle now treats a reference curve no larger than a
round-off bound as zero.

## Why it matters

A uniform reference is rare on real data, but the `mean_field` anchor makes a uniform field the
*candidate* on every run, not the reference, so the anchor itself is unaffected. The risk is a
derived or masked reference that is constant, or a test that uses a non-dyadic constant: the
metric returns a huge finite number where its docstring promises NaN, and the harness's
degeneracy handling (issues/037) never sees it.

## What would settle it

A shared round-off guard used by every metric that divides by a reference scale: compare the
scale with machine epsilon times the reference's own magnitude (its largest absolute value,
raised to the power the scale carries), and return NaN below it. Changing `spectrum_l2` and
`nrmse` changes no number on real data, so the refactor gate (`docs/recipes/verify-a-refactor.md`)
would confirm it.

## Related

Found in the adversarial review of `spectral_energy_flux` (pull request #26), 2026-10-30.
