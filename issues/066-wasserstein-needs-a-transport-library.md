# Wasserstein distance for horizontal displacement needs a transport library

**Category:** deferred functionality
**Priority:** high, the team's priority for the idea
**Status:** open, waiting on a dependency and on the signed-field decision

## Context

Idea: [Wasserstein distance for horizontal displacement](../docs/ideas/optimal_transport/wasserstein.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The quadratic Wasserstein distance between two fields on the 256 × 256 grid of `kinet_re5e4` is a transport problem between 65 536-point distributions.

## Why it is not built

No dependency can be added at present: `uv` is not installed on the login node, and CI installs with `uv sync --locked`, so editing `pyproject.toml` without regenerating `uv.lock` fails every later pull request. Adding the library is a separate change to `pyproject.toml` and `uv.lock`, made once `uv` is available. Solving that problem exactly needs a dedicated solver (for example POT); a general linear-programming solution is far too slow at this size. For velocity and vorticity, which take both signs, the metric also needs the signed-field formulation, which is an open question (issue on transport between signed fields). Density is positive and would not need it.

## What would unblock it

A transport library added (`pyproject.toml` and `uv.lock`), and the signed-field decision for the signed fields.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
