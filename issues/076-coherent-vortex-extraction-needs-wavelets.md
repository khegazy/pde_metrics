# Coherent vortex extraction needs a wavelet library, and its comparison is unspecified

**Category:** deferred functionality
**Priority:** high, the team's priority for the idea
**Status:** open, waiting on a decision on the metric applied to each part. The dependency is resolved on `metric_build`: `pywavelets` 1.10.0 is a core dependency.

## Context

Idea: [Wavelets and coherent vortex extraction](../docs/ideas/basis_decompositions/coherent_vortex_extraction.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The method splits a field into a few large wavelet coefficients (coherent part) and the many small ones (incoherent part) (Farge, Schneider & Kevlahan 1999).

## Why it is not built

The split needs an orthogonal wavelet transform (for example PyWavelets). The page also says only that "each part can then be compared with a metric suited to it", without naming the metrics, so once the library exists the comparison is an open question.

## What would unblock it

A decision on the metric applied to each part. The wavelet library is done on `metric_build`: PyWavelets 1.10.0, smoke-tested with a Haar transform in the repository's environment.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
