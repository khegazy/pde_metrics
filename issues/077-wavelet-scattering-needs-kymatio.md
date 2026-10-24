# Wavelet scattering needs a scattering-transform library

**Category:** deferred functionality
**Priority:** high, the team's priority for the idea
**Status:** open, waiting on a dependency

## Context

Idea: [Wavelet scattering and phase harmonics](../docs/ideas/basis_decompositions/wavelet_scattering.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The scattering transform (Mallat 2012; Bruna and Mallat 2013) cascades wavelet transforms and moduli; the astrophysics applications the page cites use dedicated packages.

## Why it is not built

No dependency can be added at present: `uv` is not installed on the login node, and CI installs with `uv sync --locked`, so editing `pyproject.toml` without regenerating `uv.lock` fails every later pull request. Adding the library is a separate change to `pyproject.toml` and `uv.lock`, made once `uv` is available. A from-scratch scattering transform would be a large body of new numerical code. The distance between scattering coefficient vectors is also not fixed on the page.

## What would unblock it

A scattering library (for example kymatio) added.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
