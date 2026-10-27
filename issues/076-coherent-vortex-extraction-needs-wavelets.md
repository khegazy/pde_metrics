# Coherent vortex extraction needs a wavelet library, and its comparison is unspecified

**Category:** deferred functionality
**Priority:** high, the team's priority for the idea
**Status:** open, waiting on a dependency

## Context

Idea: [Wavelets and coherent vortex extraction](../docs/ideas/basis_decompositions/coherent_vortex_extraction.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The method splits a field into a few large wavelet coefficients (coherent part) and the many small ones (incoherent part) (Farge, Schneider & Kevlahan 1999).

## Why it is not built

No dependency can be added at present: `uv` is not installed on the login node, and CI installs with `uv sync --locked`, so editing `pyproject.toml` without regenerating `uv.lock` fails every later pull request. Adding the library is a separate change to `pyproject.toml` and `uv.lock`, made once `uv` is available. The split needs an orthogonal wavelet transform (for example PyWavelets). The page also says only that "each part can then be compared with a metric suited to it", without naming the metrics, so once the library exists the comparison is an open question.

## What would unblock it

A wavelet library added, and a decision on the metric applied to each part.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
