# Splitting a field into smooth and sharp parts: three open choices

**Category:** method
**Priority:** high, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Splitting a field into smooth and sharp parts](../docs/ideas/norms/mollification_split.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page itself says the gap is mathematical and lists three open choices: how the mollifier width $\varepsilon$ is chosen (fixed, swept, or tied to the grid); whether the split is iterated across scales (which would make it a wavelet decomposition); and whether the remainder $\Delta$ is compared as a signed field or through $|\Delta|$.

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. Each choice changes the number reported, and the page records no standard for any of them. Comparing $|\Delta|$ with a Wasserstein distance also depends on the unbuilt [Wasserstein distance](../docs/ideas/optimal_transport/wasserstein.md).

## What would unblock it

A decision on each of the three choices.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
