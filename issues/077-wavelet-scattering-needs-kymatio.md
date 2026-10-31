# Wavelet scattering needs a scattering-transform library

**Category:** deferred functionality
**Priority:** high, the team's priority for the idea
**Status:** open, waiting on a dependency that works with the repository's SciPy. `kymatio` 0.3.0, the latest release, was tried in the dependency change of the metric-building plan (2026-10-31) and fails to import (Evidence below), so it was not added.

## Context

Idea: [Wavelet scattering and phase harmonics](../docs/ideas/basis_decompositions/wavelet_scattering.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The scattering transform (Mallat 2012; Bruna and Mallat 2013) cascades wavelet transforms and moduli; the astrophysics applications the page cites use dedicated packages.

## Why it is not built

A from-scratch scattering transform would be a large body of new numerical code. The distance between scattering coefficient vectors is also not fixed on the page.

## Evidence

Tried 2026-10-31 in a throwaway environment matching the lock (Python 3.12.13, numpy 2.5.1,
scipy 1.18.0): `from kymatio.numpy import Scattering2D` raises

    ImportError: cannot import name 'sph_harm' from 'scipy.special'

from `kymatio/scattering3d/filter_bank.py`, line 4. SciPy has removed `sph_harm` (its suggested
replacement is `sph_harm_y`), and kymatio 0.3.0 (released 2022-09-05) is the latest release on
PyPI. Importing the 2-D frontend alone does not avoid it, because `kymatio.numpy` imports the
3-D frontend too.

## What would unblock it

One of: a kymatio release that imports under SciPy 1.18; pinning SciPy below the release that
removed `sph_harm`, which would hold back every other dependency and is not recommended; or a
scattering transform built on the wavelet library now available (PyWavelets 1.10.0 on
`metric_build`), which is a large body of new numerical code needing its own validation.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
