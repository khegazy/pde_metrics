# Persistence diagrams need a topology library

**Category:** deferred functionality
**Priority:** high, the team's priority for the idea
**Status:** open, waiting on a dependency

## Context

Idea: [Persistence diagrams](../docs/ideas/topology/persistence_diagrams.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page: "Off-the-shelf software exists, including GUDHI, Ripser.py, giotto-tda and TTK ... so building it is a pure implementation task." It is first under "What to build next".

## Why it is not built

No dependency can be added at present: `uv` is not installed on the login node, and CI installs with `uv sync --locked`, so editing `pyproject.toml` without regenerating `uv.lock` fails every later pull request. Adding the library is a separate change to `pyproject.toml` and `uv.lock`, made once `uv` is available. Writing persistent homology and the bottleneck distance from scratch would replace mature, tested software with new code that would itself need validating. On the doubly periodic `kinet_re5e4` domain the library must support periodic cubical complexes. Once installed the metric is testable: `additive_noise` creates short-lived features near the diagonal, and on a periodic domain `translate` leaves the diagram unchanged.

## What would unblock it

GUDHI (or Ripser.py with a periodic cubical complex) added to `pyproject.toml` and `uv.lock`.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
