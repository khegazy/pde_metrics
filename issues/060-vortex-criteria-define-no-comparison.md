# Vortex criteria define a detector, not a comparison

**Category:** method
**Priority:** medium, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Vortex criteria: Q, λ₂ and Okubo–Weiss](../docs/ideas/pattern_detection/vortex_criteria.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page defines the Q, λ₂, Okubo–Weiss and swirling-strength criteria, each of which marks points as inside a vortex. It does not say how the marked sets of a prediction and a reference are compared. The plan for agent-built metrics treats a vortex mask as shared code built inside the first metric that uses it, not as a metric.

In planar incompressible flow the four criteria coincide: the page states $W = -4Q$; with $S$ traceless and $\Omega$ antisymmetric, $S^2 + \Omega^2 = -Q\,I$ in the plane, so the middle eigenvalue of the three-dimensional tensor is $\lambda_2 = -Q$; and the eigenvalues of $A$ are $\pm\sqrt{-Q}$, so $\lambda_{ci} = \sqrt{Q}$ where $Q > 0$ (the last two derived in the screening). On `kinet_re5e4`, weakly compressible at Mach 0.1, the identities hold up to the dilatational part.

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. Possible comparisons (overlap of the vortex masks, vortex area fraction, a distance between Q distributions, a vortex count) measure different things, and the page records no standard. Whether any of them is testable also depends on the choice: a count or area fraction is not changed in a controlled way by any degradation (see [the known-vortex proposal](../proposals/EXP-orchestrator-20261023-known-vortex-field.md)).

## What would unblock it

A decision on the comparison. The 2-D identity means one bundle covers all four criteria, with the three-dimensional differences stated on its card.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
