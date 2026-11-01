# Sliced Wasserstein distance: what measure is sliced, on a periodic domain

**Category:** method
**Priority:** high, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Sliced Wasserstein distance](../docs/ideas/optimal_transport/sliced_wasserstein.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page defines the sliced distance as the average of one-dimensional Wasserstein distances along many projections, and says the distributions compared "need not be the raw field values" but could be increments, gradients or fluxes. It does not say which.

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. Three questions have no answer on the page:

1. If the field itself is treated as a mass distribution, it must be nonnegative with a fixed total, so velocity and vorticity need the signed-field formulation, which is itself open (issue on transport between signed fields).
2. On the doubly periodic `kinet_re5e4` domain, a projection onto a line at a non-axis angle does not close on the torus, and the transport cost along a projection must use a periodic distance; the page does not say how either is handled.
3. The page's pitfall says to "validate it against the exact Wasserstein distance on small cases", and the exact distance is built only for positive fields ([wasserstein](../metrics/wasserstein/card.md), on density).

If instead the sliced distance is applied to samples of a feature (increments, gradients), the choice of feature is the open question, and for one-dimensional features slicing is unnecessary.

## What would unblock it

A decision on which measure is sliced and how periodicity is treated, and, if validation against the full distance is required on a signed field, the [Wasserstein distance for velocity and vorticity](../docs/ideas/optimal_transport/wasserstein_signed_fields.md) built first; on density it can be validated against [wasserstein](../metrics/wasserstein/card.md).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
