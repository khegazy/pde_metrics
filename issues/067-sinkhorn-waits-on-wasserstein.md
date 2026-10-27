# Sinkhorn divergences wait on the Wasserstein distance

**Category:** deferred functionality
**Priority:** medium, the team's priority for the idea
**Status:** open, waiting on another metric

## Context

Idea: [Entropic relaxation and Sinkhorn divergences](../docs/ideas/optimal_transport/sinkhorn.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page: "this becomes relevant only after the Wasserstein distance has shown that it is useful. The open question is whether Wasserstein helps at all, and that should be answered before its cost is optimised."

## Why it is not built

The rule this follows: an idea that builds on a metric not yet on `main` is not implemented; it waits until that metric is merged. The [Wasserstein distance](../docs/ideas/optimal_transport/wasserstein.md) is not built. A Sinkhorn implementation would also normally use a transport library, which cannot be added now. No dependency can be added at present: `uv` is not installed on the login node, and CI installs with `uv sync --locked`, so editing `pyproject.toml` without regenerating `uv.lock` fails every later pull request. Adding the library is a separate change to `pyproject.toml` and `uv.lock`, made once `uv` is available.

## What would unblock it

The Wasserstein distance built and shown useful, and the library added.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
