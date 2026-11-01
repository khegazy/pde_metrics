# Transport between signed fields: which of the four formulations to use

**Category:** method
**Priority:** high, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Transport between signed fields](../docs/ideas/optimal_transport/signed_field_transport.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The idea page lists four standard ways to apply optimal transport to a field that takes negative values or does not conserve its total: split into positive and negative parts; add a constant and renormalise; unbalanced (Hellinger–Kantorovich) transport; and graph-space transport (Métivier et al. 2018, *Geophysics* 83(5), R515–R540). It chooses none. Every transport metric applied to velocity or vorticity depends on the choice, including the [Wasserstein distance for velocity and vorticity](../docs/ideas/optimal_transport/wasserstein_signed_fields.md) and the [sliced Wasserstein distance](../docs/ideas/optimal_transport/sliced_wasserstein.md).

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. The four options give different numbers for the same pair of fields: the constant-shift option has a free parameter (the size of the constant) that changes the value, unbalanced transport has a price on mass creation, and the graph-space form needs a scale relating field values to positions.

## What would unblock it

A decision, with its reason, on which formulation (and which free parameters) the repository uses for signed fields. The page's own rationale favours the graph-space form because it stays convex with respect to shifts, but that is a recommendation, not a decision. Graph-space and unbalanced transport also need a transport library (for example POT), which cannot be added yet (see the Wasserstein issue).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
