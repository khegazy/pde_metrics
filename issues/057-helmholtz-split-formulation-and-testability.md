# Helmholtz split: which field is decomposed, what number is reported, and what tests it

**Category:** method
**Priority:** high, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Helmholtz split into rotational and compressive parts](../docs/ideas/physics_invariants/helmholtz_split.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page proposes splitting the velocity into solenoidal and dilatational parts, computing curl-based diagnostics on the solenoidal part, and comparing the spectra of the two parts "computed from density-weighted (Favre) quantities" with the reference's. On a periodic domain the split itself is a standard Fourier projection.

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. Two questions are open and one rule is not met.

1. *Which field is decomposed.* The page asks for density-weighted quantities but does not say whether the split is of $\mathbf{u}$, of $\sqrt{\rho}\,\mathbf{u}$ or of $\rho\mathbf{u}$; compressible-turbulence studies use more than one.
2. *What number is reported.* Two spectra are compared, so the metric is two numbers (one per part), or a vector, or a ratio; the page does not say.
3. *What tests it.* The rule this follows: a metric is built only if an existing experiment changes, in a controlled and known way, the property it is built to detect; a degradation that moves it only incidentally does not count. The current experiments are the 24 degradations (`python -m degradations`) applied to single snapshots of `kinet_re5e4`, `synthetic_ensemble` and `sod_shock_tube`. The property the split detects is the partition of energy between rotation and compression. No degradation changes that partition by design: the smoothing and spectral operators are isotropic and linear, so they damp both parts in the same proportion at each wavenumber. `additive_noise` does move the partition (isotropic white noise in two dimensions puts half its energy into each part in expectation, while `kinet_re5e4` at Mach 0.1 is nearly solenoidal), but only incidentally. This third point is a judgement call made in the screening and is the one most worth re-examining.

## What would unblock it

Decisions on the decomposed field and the reported number, and an experiment that changes the partition in a controlled way (see [the dilatational-scaling proposal](../proposals/EXP-orchestrator-20261023-dilatational-scaling.md)). Related: [024](024-leray-projection.md), the solenoidal projection for the spectral operators.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
